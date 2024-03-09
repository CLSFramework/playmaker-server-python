import gymnasium as gym
from queue import Queue
import numpy as np
from service_pb2 import GameModeType, ServerParam, PlayerType, PlayerParam, Side, State, TrainerAction, TrainerActions, Vector2D, WorldModel
import service_pb2 as pb2
from service_pb2 import Body_KickOneStep
from pyrusgeom.vector_2d import Vector2D as V2D
class CustomGymEnv(gym.Env):
    def __init__(self) -> None:
        super().__init__()
        self.player_action_queue = Queue(1)
        self.trainer_action_queue = Queue(10)
        self.observation_queue = Queue(1)
        self.episode_reward = 0
        self.intermittent_rewards=[]
        self.previous_intermittent_wm: WorldModel = None
        self.old_observation = None
        self.ANGLE_DIVS = 4
        self.POWER_DIVS = 4
        self.server_param: ServerParam = None
        self.player_param: PlayerParam = None
        self.player_type: PlayerType = None
        self.ANGLE_STEP = 360/self.ANGLE_DIVS
        
        # observation: normalized self pos, normalized ball pos
        self.observation_space = gym.spaces.Box(low=np.array([-1,-1,-1,-1]),high=np.array([1,1,1,1])
                                                ,shape=(4,),dtype=np.float64)
        # action space: kick, 18 angles, 4 power levels
        # use multidescrete
        self.action_space = gym.spaces.MultiDiscrete([self.ANGLE_DIVS,self.POWER_DIVS])
    
    def append_intermittent_rewards(self, wm:WorldModel):
        if self.previous_intermittent_wm is None:
            self.previous_intermittent_wm = wm
            return
        ball_pos = wm.ball.position
        old_ball_pos = self.previous_intermittent_wm.ball.position
        self.intermittent_rewards.append(ball_pos.x - old_ball_pos.x)
        self.previous_intermittent_wm = wm
    
        



    def observation_to_ndarray(self, observation: State) -> np.ndarray:
        wm = observation.world_model
        self_pos = wm.self.position
        ball_pos = wm.ball.position
        hl = self.server_param.pitch_half_length
        hw = self.server_param.pitch_half_width
        normalized_self_pos = [self_pos.x/hl, self_pos.y/hw]
        normalized_ball_pos = [ball_pos.x/hl, ball_pos.y/hw]
        return np.array(normalized_self_pos + normalized_ball_pos)
    
    def calculate_reward(self, observation:State, old_observation:State) -> float:
        if observation.world_model.game_mode_type == GameModeType.KickOff_:
            last_ball_x = old_observation.world_model.ball.position.x
            if last_ball_x > 0:
                actual_ball = Vector2D(x=52.5,y=0)
            else:
                actual_ball = Vector2D(x=-52.5,y=0)
            ball_pos = actual_ball
        else:
            ball_pos = observation.world_model.ball.position
        old_ball_pos = old_observation.world_model.ball.position
        # print(f'Ball Pos:({ball_pos.x},{ball_pos.y}), old ball pos : ({old_ball_pos.x},{old_ball_pos.y})')
        return ball_pos.x - old_ball_pos.x
    
    def wait_for_observation_and_return(self):
        # print("Awaiting observation")
        observation = self.observation_queue.get(block=True)
        # print("RECEIVED OBSERVATION")
        self.old_observation = observation
        # if self.old_observation is None:
        #     print("OLD OBS IS NONE!!!!!!!!")
        return self.observation_to_ndarray(observation), {}
    
    def clear_actions_queue(self):
        with self.player_action_queue.mutex:
            self.player_action_queue.queue.clear()

    def clear_observation_queue(self):
        with self.observation_queue.mutex:
            self.observation_queue.queue.clear()

    def do_action(self, action, clear_actions: bool = False):
        if clear_actions:
            self.clear_actions_queue()
        self.player_action_queue.put(action,block=False)

    def gym_action_to_soccer_action(self, action, wm:WorldModel):
        # angle = -np.pi + action[0] * self.ANGLE_STEP
        absolute_angle = -180 + action[0] * self.ANGLE_STEP
        power_step = self.server_param.ball_speed_max / self.POWER_DIVS 
        power = (action[1] +1) * power_step
        # print(f"Body Dir: {wm.self.body_direction}")
        pos = wm.self.position
        target = V2D.polar2vector(10,absolute_angle)+ V2D(x=pos.x,y=pos.y)
        
        # print(f"Absolute Angle: {absolute_angle}, Power: {power}")
        
        return Body_KickOneStep(first_speed=power,target_point=Vector2D(x=target.x(),y=target.y()),force_mode=True)


    def step(self, action):
        # print("STEP START")
        self.clear_observation_queue()
        self.do_action(action)
        # print("await observation")
        observation:State = self.observation_queue.get()
        # print("###############")
        game_mode = observation.world_model.game_mode_type
        # print(f"Game Cycle: {observation.world_model.cycle}, Game Mode : {game_mode}")
        # todo: hack to find which goal was scored in since goal_l or goal_r dont send observations.
        
        reward = 0
    
        if self.old_observation is not None:
            reward = self.calculate_reward(observation, self.old_observation)
        self.episode_reward += reward
        
        done = observation.world_model.game_mode_type != GameModeType.PlayOn
        # print(f"Done = {done}")
        self.old_observation = observation
        return self.observation_to_ndarray(observation), reward, done, False, {}
    
    def get_trainer_reset_commands(self) -> TrainerActions:
        actions = TrainerActions()
        zero_vec = Vector2D(x=0.,y=0.)
        player_vec =Vector2D(x=-5.,y=0.)
        actions.actions.append(TrainerAction(do_change_mode=pb2.DoChangeMode(game_mode_type=GameModeType.PlayOn,side=Side.LEFT)))
        actions.actions.append(TrainerAction(do_move_ball=pb2.DoMoveBall(position=zero_vec,velocity=zero_vec)))
        actions.actions.append(TrainerAction(do_recover=pb2.DoRecover()))
        actions.actions.append(TrainerAction(do_move_player=pb2.DoMovePlayer(our_side=True, uniform_number= 1, position= player_vec,body_direction=0)))
        return actions

    
    def reset(self, seed = -1):
        # print("RESETING ENV!")
        print(f"Episode reward:{self.episode_reward}")
        self.episode_reward = 0
        self.old_observation = None
        self.clear_actions_queue()
        self.clear_observation_queue()
        if self.trainer_action_queue.empty:
            self.trainer_action_queue.put(0)
        # todo add reset action
        # reset action sent, to unblock player action
        self.do_action([-1,-1], clear_actions=True)
        return self.wait_for_observation_and_return()
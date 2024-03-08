import gymnasium as gym
from queue import Queue
import numpy as np
from service_pb2 import ServerParam, PlayerType, PlayerParam, State, Vector2D
from service_pb2 import Body_KickOneStep
from pyrusgeom.vector_2d import Vector2D as V2D
class CustomGymEnv(gym.Env):
    def __init__(self) -> None:
        super().__init__()
        self.player_action_queue = Queue(1)
        self.observation_queue = Queue(1)
        self.episode_reward = 0
        self.old_observation = None
        self.ANGLE_DIVS = 4
        self.POWER_DIVS = 4
        self.server_param: ServerParam = None
        self.player_param: PlayerParam = None
        self.player_type: PlayerType = None
        self.ANGLE_STEP = 360/self.ANGLE_DIVS
        
        # observation: normalized self pos, normalized ball pos
        self.observation_space = gym.spaces.Box(low=np.array([-1,-1,-1,-1]),high=np.array([1,1,1,1])
                                                ,shape=(4,),dtype=np.float32)
        # action space: kick, 18 angles, 4 power levels
        # use multidescrete
        self.action_space = gym.spaces.MultiDiscrete([self.ANGLE_DIVS,self.POWER_DIVS])
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
        wm = observation.world_model
        old_wm = old_observation.world_model
        ball_pos = wm.ball.position
        old_ball_pos = old_wm.ball.position
        return ball_pos.x - old_ball_pos.x
    
    def wait_for_observation_and_return(self):
        observation = self.observation_queue.get(block=True)
        self.old_observation = observation
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
        self.player_action_queue.put(self.gym_action_to_soccer_action(action),block=False)

    def gym_action_to_soccer_action(self, action):
        # angle = -np.pi + action[0] * self.ANGLE_STEP
        absolute_angle = -180 + action[0] * self.ANGLE_STEP
        power_step = self.server_param.ball_speed_max / self.POWER_DIVS 
        power = (action[1] +1) * power_step
        print(f"Body Dir: {self.old_observation.world_model.self.body_direction}")
        pos = self.old_observation.world_model.self.position
        target = V2D.polar2vector(10,absolute_angle)+ V2D(x=pos.x,y=pos.y)
        
        print(f"Absolute Angle: {absolute_angle}, Power: {power}")
        
        return Body_KickOneStep(first_speed=power,target_point=Vector2D(x=target.x(),y=target.y()),force_mode=True)


    def step(self, action):
        self.clear_observation_queue()
        self.do_action(action)
        observation:State = self.observation_queue.get()
        print("###############")
        print(f"Game Cycle: {observation.world_model.cycle}, Game Mode : {observation.world_model.game_mode_type}")
        reward = 0
        if self.old_observation is not None:
            reward = self.calculate_reward(observation, self.old_observation)
        self.episode_reward += reward
        done = False
        
        self.old_observation = observation
        return self.observation_to_ndarray(observation), reward, done, False, {}
    
    def reset(self):
        self.episode_reward = 0
        self.old_observation = None
        # todo add reset action
        return self.wait_for_observation_and_return()
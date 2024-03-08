import time
from grpc_server import Game
import threading
from concurrent import futures
import grpc
from gym_env import CustomGymEnv
import service_pb2_grpc as pb2_grpc
import service_pb2 as pb2
class GymGame(Game):
    def __init__(self, gym_env:CustomGymEnv):
        super().__init__()
        self.gym_env: CustomGymEnv = gym_env
    
    def SendServerParams(self, request: pb2.ServerParam, context):
        self.gym_env.server_param = request
        return super().SendServerParams(request, context)
    
    def SendPlayerParams(self, request: pb2.PlayerParam, context):
        self.gym_env.player_param = request
        return super().SendPlayerParams(request, context)
    
    def SendPlayerType(self, request: pb2.PlayerType, context):
        self.gym_env.player_type = request
        return super().SendPlayerType(request, context)
    
    def GetPlayerActions(self, request, context):
        # append neck action first to the action list
        actions = pb2.PlayerActions()
        wm = request.world_model
        actions.actions.append(pb2.PlayerAction(neck_turn_to_ball=pb2.Neck_TurnToBall()))
        if wm.game_mode_type != pb2.GameModeType.PlayOn:
            self.gym_env.old_observation = None
            return actions
        if not request.world_model.self.is_kickable:
            # if the ball is not kickable, return Intercept
            intercept_action = pb2.Body_Intercept(save_recovery=False, face_point=wm.ball.position)
            actions.actions.append(pb2.PlayerAction(body_intercept=intercept_action))
            return actions
        # if the ball is kickable, send observation to the gym env
        self.gym_env.clear_actions_queue()
        self.gym_env.observation_queue.put(request,block=True)
        selected_kick_action: pb2.Body_KickOneStep = self.gym_env.player_action_queue.get(block = True)
        # convert the action to the grpc action
        actions.actions.append(pb2.PlayerAction(body_kick_one_step=selected_kick_action))
        return actions

def serve(gym_env:CustomGymEnv):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=22))
    pb2_grpc.add_GameServicer_to_server(GymGame(gym_env), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Decision Server started. Listening on port 50051...")
    try:
        while True:
            time.sleep(60 * 60 * 24)  # Sleep for a day or any desired interval
    except KeyboardInterrupt:
        print("Shutting down the server...")
        server.stop(0)

if __name__ == "__main__":
    gym_env = CustomGymEnv()
    server_thread = threading.Thread(target=serve, args=(gym_env,))
    server_thread.start()
    gym_env.close()
    observation, _ = gym_env.wait_for_observation_and_return()
    while server_thread.is_alive():
        action = gym_env.action_space.sample()
        print(f"Action: {action}")
        # get observation from the environment
        observation, reward, done,truncated, info = gym_env.step(action)
        print(f"Observation: {observation}, Reward: {reward}, Done: {done}, Info: {info}")
        if done:
            observation, info = gym_env.reset()
            print("Environment reset")
        else:
            print("Environment not reset")


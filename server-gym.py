from thrift.protocol import TBinaryProtocol
from thrift.transport import TSocket, TTransport
from soccer import Game
import sys
import os
from utils.PFProcessServer import PFProcessServer
from thrift.server.TServer import TThreadedServer
import logging
import multiprocessing
import gym
from gym import spaces
import numpy as np
from typing import Union
from soccer.ttypes import State, Empty, PlayerActions, CoachActions, TrainerActions, WorldModel, Self, ThriftVector2D, Dash, PlayerAction
from soccer.ttypes import ServerParam, PlayerParam, PlayerType, InitMessage, RegisterRequest, RegisterResponse, AgentType, TrainerAction, DoMoveBall, DoMovePlayer
from src.SamplePlayerAgent import SamplePlayerAgent
from src.SampleCoachAgent import SampleCoachAgent
from src.SampleTrainerAgent import SampleTrainerAgent
from threading import Semaphore
from multiprocessing import Manager, Lock
import logging
import random

logging.basicConfig(level=logging.DEBUG)

manager = Manager()
shared_lock = Lock()  # Create a Lock for synchronization
shared_number_of_connections = manager.Value('i', 0)

class SoccerEnv(gym.Env):
    def __init__(self, action_queue, observation_queue, reward_done_queue, request_to_trainer):
        super(SoccerEnv, self).__init__()
        self.action_queue = action_queue
        self.observation_queue = observation_queue
        self.reward_done_queue = reward_done_queue
        self.request_to_trainer = request_to_trainer

        self.action_space = spaces.Space()

    def reset(self):
        return observation_queue.get()

    def step(self, action):
        self.action_queue.put(action)
        reward_done = self.reward_done_queue.get()
        # reward_done = RewardDone(0, False)
        obs = self.observation_queue.get()
        return obs, reward_done.reward, reward_done.done, {}

    def render(self):
        # Clear the screen
        print("Rendering")

    def distruct(self):
        pass

class RewardDone:
    def __init__(self, reward, done):
        self.reward = reward
        self.done = done

    def __str__(self):
        return f"Reward: {self.reward}, Done: {self.done}"

class GameHandler:
    def __init__(self, action_queue, observation_queue, reward_done_queue, request_to_trainer):
        self.agents: dict[int, Union[SamplePlayerAgent, SampleTrainerAgent, SampleCoachAgent]] = {}
        self.running = Semaphore()
        self.action_queue = action_queue
        self.observation_queue = observation_queue
        self.reward_done_queue = reward_done_queue
        self.request_to_trainer = request_to_trainer

    def GetPlayerActions(self, register_response: RegisterResponse, state: State):
        logging.debug(f"GetPlayerActions {state.world_model.cycle}")
        wm: WorldModel = state.world_model
        myself: Self = wm.myself
        self.observation_queue.put([myself.position.x, myself.position.y, myself.body_direction])
        act = self.action_queue.get()
        dash = Dash(power=100, relative_direction=act)

        actions: list[PlayerAction] = [PlayerAction(dash=dash)]
        res = PlayerActions(actions=actions)
        logging.debug(f"Player actions: {res}")
        return res

    def GetCoachActions(self, register_response: RegisterResponse, state):
        logging.debug(f"GetCoachActions {state.world_model.cycle}")
        actions = self.agents[register_response.client_id].get_actions(state.world_model)
        return CoachActions(actions=actions)

    def GetTrainerActions(self, register_response: RegisterResponse, state: State):

        if len(state.world_model.teammates) == 0:
            return TrainerActions(actions=[])
        logging.debug(f"GetTrainerActions {state.world_model.cycle}")
        player_pos = state.world_model.teammates[0].position
        logging.debug(f"Player position: {player_pos.x} {player_pos.y}")
        if player_pos.x > 10:
            action = TrainerAction(
                do_move_player=DoMovePlayer(
                    our_side=True,
                    uniform_number=1,
                    body_direction=0,
                    position=ThriftVector2D(x=-10, y=0)
                )
            )
            self.reward_done_queue.put(RewardDone(10, True))
            return TrainerActions(actions=[action])
        else:
            self.reward_done_queue.put(RewardDone(0, False))
            return TrainerActions(actions=[])

    def SendServerParams(self, register_response: RegisterResponse, serverParam):
        # logging.debug(f"Server params received {serverParam}")
        self.agents[register_response.client_id].set_params(serverParam)
        res = Empty()
        return res

    def SendPlayerParams(self, register_response: RegisterResponse, playerParam):
        # logging.debug(f"Player params received {playerParam}")
        self.agents[register_response.client_id].set_params(playerParam)
        res = Empty()
        return res

    def SendPlayerType(self, register_response: RegisterResponse, playerType):
        # logging.debug(f"Player type received {playerType}")
        self.agents[register_response.client_id].set_params(playerType)
        res = Empty()
        return res

    def SendInitMessage(self, register_response: RegisterResponse, initMessage):
        logging.debug(f"Init message received {initMessage}")
        self.agents[register_response.client_id].set_debug_mode(initMessage.debug_mode)
        res = Empty()
        return res

    def Register(self, register_request: RegisterRequest):
        logging.debug("New connection")
        with shared_lock:
            shared_number_of_connections.value += 1
            logging.debug(f"Number of connections {shared_number_of_connections.value}")
            if register_request.agent_type == AgentType.PlayerT:
                self.agents[shared_number_of_connections.value] = SamplePlayerAgent()
            elif register_request.agent_type == AgentType.CoachT:
                self.agents[shared_number_of_connections.value] = SampleCoachAgent()
            elif register_request.agent_type == AgentType.TrainerT:
                self.agents[shared_number_of_connections.value] = SampleTrainerAgent()
            res = RegisterResponse(client_id=shared_number_of_connections.value)
            return res

    def SendByeCommand(self, register_response: RegisterResponse):
        with shared_lock:
            self.agents.pop(register_response.client_id)
        res = Empty()
        return res

def serve(port, action_queue, observation_queue, reward_done_queue, request_to_trainer):
    handler = GameHandler(action_queue, observation_queue, reward_done_queue, request_to_trainer)
    processor = Game.Processor(handler)
    transport = TSocket.TServerSocket(host='0.0.0.0', port=port)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()

    server = PFProcessServer(processor, transport, tfactory, pfactory)
    # server = TThreadedServer(processor, transport, tfactory, pfactory)

    logging.info(f"Starting server on port {port}")
    try:
        handler.running.acquire()
        server.serve()
    except KeyboardInterrupt:
        print("Stopping server")
        handler.running.release()
        os._exit(0)


def rl(action_queue, observation_queue, reward_done_queue, request_to_trainer):
    logging.info("RL Process started")
    env = SoccerEnv(action_queue, observation_queue, reward_done_queue, request_to_trainer)
    logging.info("Environment created")
    while True:
        logging.info("Resetting environment")
        obs = env.reset()
        logging.info(f"Environment reset with observation: {obs}")
        done = False
        while not done:
            action = random.randint(0, 360)
            logging.info(f"Taking action: {action}")
            obs, reward, done, _ = env.step(action)
            logging.info(f"Observation: {obs} Reward: {reward} Done: {done}")
        env.distruct()

if __name__ == '__main__':
    manager = multiprocessing.Manager()
    action_queue = manager.Queue()
    observation_queue = manager.Queue()
    reward_done_queue = manager.Queue()
    request_to_trainer = manager.Queue()
    serve_process = multiprocessing.Process(target=serve, args=(50051, action_queue, observation_queue, reward_done_queue, request_to_trainer))
    serve_process.start()
    rl_process = multiprocessing.Process(target=rl, args=(action_queue, observation_queue, reward_done_queue, request_to_trainer))
    rl_process.start()

    serve_process.join()
    rl_process.join()

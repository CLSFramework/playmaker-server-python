from typing import Union
from soccer.ttypes import State, Empty, PlayerActions, CoachActions, TrainerActions
from soccer.ttypes import ServerParam, PlayerParam, PlayerType, InitMessage, RegisterRequest, RegisterResponse, AgentType
from src.SamplePlayerAgent import SamplePlayerAgent
from src.SampleCoachAgent import SampleCoachAgent
from src.SampleTrainerAgent import SampleTrainerAgent
from threading import Semaphore
from multiprocessing import Manager, Lock
import logging

logging.basicConfig(level=logging.INFO)

manager = Manager()
shared_lock = Lock()  # Create a Lock for synchronization
shared_number_of_connections = manager.Value('i', 0)


class GameHandler:
    def __init__(self):
        self.agents: dict[int, Union[SamplePlayerAgent, SampleTrainerAgent, SampleCoachAgent]] = {}
        self.running = Semaphore()

    def GetPlayerActions(self, register_response: RegisterResponse, state: State):
        logging.debug(f"GetPlayerActions {state.world_model.cycle}")
        actions = self.agents[register_response.client_id].get_actions(state.world_model)
        res = PlayerActions(actions=actions)
        return res

    def GetCoachActions(self, register_response: RegisterResponse, state):
        logging.debug(f"GetCoachActions {state.world_model.cycle}")
        actions = self.agents[register_response.client_id].get_actions(state.world_model)
        return CoachActions(actions=actions)

    def GetTrainerActions(self, register_response: RegisterResponse, state):
        logging.debug(f"GetTrainerActions {state.world_model.cycle}")
        actions = self.agents[register_response.client_id].get_actions(state.world_model)
        return TrainerActions(actions=actions)

    def SendServerParams(self, register_response: RegisterResponse, serverParam):
        logging.debug(f"Server params received {serverParam}")
        self.agents[register_response.client_id].set_params(serverParam)
        res = Empty()
        return res

    def SendPlayerParams(self, register_response: RegisterResponse, playerParam):
        logging.debug(f"Player params received {playerParam}")
        self.agents[register_response.client_id].set_params(playerParam)
        res = Empty()
        return res

    def SendPlayerType(self, register_response: RegisterResponse, playerType):
        logging.debug(f"Player type received {playerType}")
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
from typing import Union
from thrift import Thrift
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
from thrift.transport import TSocket, TTransport
from soccer import Game
from soccer.ttypes import State, Empty, PlayerActions, CoachActions, TrainerActions
from soccer.ttypes import ServerParam, PlayerParam, PlayerType, InitMessage, RegisterRequest, RegisterResponse, AgentType
from src.SamplePlayerAgent import SamplePlayerAgent
from src.SampleCoachAgent import SampleCoachAgent
from src.SampleTrainerAgent import SampleTrainerAgent
from threading import Semaphore
import os
import sys

class GameHandler:
    def __init__(self):
        self.agents: dict[int, Union[SamplePlayerAgent, SampleTrainerAgent, SampleCoachAgent]] = {}

        self.number_of_connections = 0
        self.lock = Semaphore()
        self.running = Semaphore()
    
    def GetPlayerActions(self, register_response: RegisterResponse, state: State):
        # print("GetPlayerActions", state.world_model.cycle)
        actions = self.agents[register_response.client_id].get_actions(state.world_model)
        res = PlayerActions(actions=actions)
        return res

    def GetCoachActions(self, register_response: RegisterResponse, state):
        # print("GetCoachActions", state.world_model.cycle)
        actions = self.agents[register_response.client_id].get_actions(state.world_model)
        return CoachActions(actions=actions)

    def GetTrainerActions(self, register_response: RegisterResponse, state):
        # print("GetTrainerActions", state.world_model.cycle)
        actions = self.agents[register_response.client_id].get_actions(state.world_model)
        return TrainerActions(actions=actions)

    def SendServerParams(self, register_response: RegisterResponse, serverParam):
        print("Server params received", serverParam)
        self.agents[register_response.client_id].set_params(serverParam)
        res = Empty()
        return res

    def SendPlayerParams(self, register_response: RegisterResponse, playerParam):
        print("Player params received", playerParam)
        self.agents[register_response.client_id].set_params(playerParam)
        res = Empty()
        return res

    def SendPlayerType(self, register_response: RegisterResponse, playerType):
        print("Player type received", playerType)
        self.agents[register_response.client_id].set_params(playerType)
        res = Empty()
        return res

    def SendInitMessage(self, register_response: RegisterResponse, initMessage):
        print("Init message received", initMessage)
        self.agents[register_response.client_id].set_debug_mode(initMessage.debug_mode)
        res = Empty()
        return res

    def Register(self, register_request: RegisterRequest):
        print("New connection")
        with self.lock:
            self.number_of_connections += 1
            if register_request.agent_type == AgentType.PlayerT:
                self.agents[self.number_of_connections] = SamplePlayerAgent()
            elif register_request.agent_type == AgentType.CoachT:
                self.agents[self.number_of_connections] = SampleCoachAgent()
            elif register_request.agent_type == AgentType.TrainerT:
                self.agents[self.number_of_connections] = SampleTrainerAgent()
            res = RegisterResponse(client_id=self.number_of_connections)
            return res

    def SendByeCommand(self, register_response: RegisterResponse):
        with self.lock:
            self.agents.pop(register_response.client_id)
        res = Empty()
        return res


def serve(port):
    handler = GameHandler()
    processor = Game.Processor(handler)
    transport = TSocket.TServerSocket(host='0.0.0.0', port=port)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()

    # server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
    server = TServer.TThreadPoolServer(processor, transport, tfactory, pfactory)
    server.setNumThreads(50)
    print("Thrift server started at port 50051")
    try:
        handler.running.acquire()
        server.serve()
    except KeyboardInterrupt:
        print("Stopping server")
        handler.running.release()
        os._exit(0)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        port = 50051
    else:
        port = sys.argv[1]
    serve(port)

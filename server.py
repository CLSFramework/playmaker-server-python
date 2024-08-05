from thrift import Thrift
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
from thrift.transport import TSocket, TTransport
from soccer import Game
from soccer.ttypes import State, Empty, PlayerActions, CoachActions, TrainerActions, ServerParam, PlayerParam, PlayerType, InitMessage, InitMessageFromServer

from time import sleep
from concurrent import futures
from src.SamplePlayerAgent import SamplePlayerAgent
from src.SampleCoachAgent import SampleCoachAgent
from src.SampleTrainerAgent import SampleTrainerAgent
from threading import Semaphore
import os


class GameHandler:
    def __init__(self):
        self.player_agent = SamplePlayerAgent()
        self.coach_agent = SampleCoachAgent()
        self.trainer_agent = SampleTrainerAgent()
        self.number_of_connections = 0
        self.lock = Semaphore()
        self.running = Semaphore()
    
    def GetPlayerActions(self, state):
        print("GetPlayerActions", state.world_model.cycle)
        actions = self.player_agent.get_actions(state.world_model)
        return PlayerActions(actions=actions)

    def GetCoachActions(self, state):
        print("GetCoachActions", state.world_model.cycle)
        actions = self.coach_agent.get_actions(state.world_model)
        return CoachActions(actions=actions)

    def GetTrainerActions(self, state):
        print("GetTrainerActions", state.world_model.cycle)
        actions = self.trainer_agent.get_actions(state.world_model)
        return TrainerActions(actions=actions)

    def SendServerParams(self, serverParam):
        print("Server params received", serverParam)
        self.player_agent.set_params(serverParam)
        self.coach_agent.set_params(serverParam)
        self.trainer_agent.set_params(serverParam)
        return

    def SendPlayerParams(self, playerParam):
        print("Player params received", playerParam)
        self.player_agent.set_params(playerParam)
        self.coach_agent.set_params(playerParam)
        self.trainer_agent.set_params(playerParam)
        return

    def SendPlayerType(self, playerType):
        print("Player type received", playerType)
        self.player_agent.set_params(playerType)
        self.coach_agent.set_params(playerType)
        self.trainer_agent.set_params(playerType)
        return

    def SendInitMessage(self, initMessage):
        print("Init message received", initMessage)
        self.player_agent.set_debug_mode(initMessage.debug_mode)
        return

    def GetInitMessage(self, empty):
        print("New connection")
        # with self.lock:
        #     self.number_of_connections += 1
        res = InitMessageFromServer()
        print(res)
        return res

    def SendByeCommand(self, empty):
        with self.lock:
            self.number_of_connections -= 1
        if self.number_of_connections <= 0:
            self.running.release()
        return


def serve():
    handler = GameHandler()
    processor = Game.Processor(handler)
    transport = TSocket.TServerSocket(host='0.0.0.0', port=50051)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()

    server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
    print("Thrift server started at port 50051")
    try:
        handler.running.acquire()
        server.serve()
    except KeyboardInterrupt:
        print("Stopping server")
        handler.running.release()
        os._exit(0)

if __name__ == '__main__':
    serve()

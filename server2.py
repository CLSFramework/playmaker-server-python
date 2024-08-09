import threading
from typing import Union
from thrift import Thrift
from thrift.protocol import TBinaryProtocol
from thrift.protocol.THeaderProtocol import THeaderProtocolFactory
from thrift.server.TServer import TServer, TSimpleServer
from thrift.transport import TSocket, TTransport, THeaderTransport
from soccer import Game
from soccer.ttypes import State, Empty, PlayerActions, CoachActions, TrainerActions
from soccer.ttypes import ServerParam, PlayerParam, PlayerType, InitMessage, RegisterRequest, RegisterResponse, AgentType
from src.SamplePlayerAgent import SamplePlayerAgent
from src.SampleCoachAgent import SampleCoachAgent
from src.SampleTrainerAgent import SampleTrainerAgent
from threading import Semaphore
import sys
import logging
import time
import asyncio
import multiprocessing
import os


class PFThreadedServer(TServer):
    """Threaded server that spawns a new thread and processor per each connection."""
    # # def __init__(self, processorFactory, serverTransport, transportFactory, protocolFactory):
    def __init__(self, *args):
        TServer.__init__(self, *args)
        # self.processorFactory = processorFactory
        self.processorFactory = args[0]
        self.daemon = False

    def serve(self):
        self.serverTransport.listen()
        while True:
            try:
                client = self.serverTransport.accept()
                if not client:
                    continue
                t = threading.Thread(target=self.handle, args=(client,))
                t.daemon = self.daemon
                t.start()

            except KeyboardInterrupt:
                raise

            except Exception as x:
                print(x)

    def handle(self, client):
        print(f"Starting thread {threading.get_ident()} for client {client}")
        start_time = time.time()

        processor = self.processorFactory.getProcessor(client)
        itrans = self.inputTransportFactory.getTransport(client)
        iprot = self.inputProtocolFactory.getProtocol(itrans)

        if isinstance(self.inputProtocolFactory, THeaderProtocolFactory):
            otrans = None
            oprot = iprot
        else:
            otrans = self.outputTransportFactory.getTransport(client)
            oprot = self.outputProtocolFactory.getProtocol(otrans)

        try:
            while True:
                processor.process(iprot, oprot)
        except TTransport.TTransportException:
            pass
        except Exception as x:
            print(x)
        finally:
            itrans.close()
            if otrans:
                otrans.close()
            end_time = time.time()
            print(f"Thread {threading.get_ident()} for client {client} completed in {end_time - start_time} seconds.")


class PFProcessServer(TServer):
    """Process-based server that spawns a new process per each connection."""

    def __init__(self, *args):
        TServer.__init__(self, *args)
        self.processorFactory = args[0]

    def serve(self):
        self.serverTransport.listen()
        while True:
            try:
                client = self.serverTransport.accept()
                if not client:
                    continue
                p = multiprocessing.Process(target=self.handle, args=(client,))
                p.start()

            except KeyboardInterrupt:
                raise

            except Exception as x:
                print(x)

    def handle(self, client):
        processor = self.processorFactory.getProcessor(client)
        itrans = self.inputTransportFactory.getTransport(client)
        iprot = self.inputProtocolFactory.getProtocol(itrans)

        if isinstance(self.inputProtocolFactory, THeaderProtocolFactory):
            otrans = None
            oprot = iprot
        else:
            otrans = self.outputTransportFactory.getTransport(client)
            oprot = self.outputProtocolFactory.getProtocol(otrans)

        try:
            while True:
                processor.process(iprot, oprot)
        except TTransport.TTransportException:
            pass
        except Exception as x:
            print(x)
        finally:
            itrans.close()
            if otrans:
                otrans.close()

from multiprocessing import Manager
manager = Manager()
shared_int = manager.Value('i', 0)


class GameHandler:
    number_of_connections = 0
    lock = threading.Lock()
    agents: dict[int, Union[SamplePlayerAgent, SampleTrainerAgent, SampleCoachAgent]] = {}

    def __init__(self):
        self.running = Semaphore()

    def GetPlayerActions(self, register_response: RegisterResponse, state: State):
        print("GetPlayerActions", state.world_model.cycle)
        print("number of connections", self.number_of_connections)
        print(f"Starting thread {threading.get_ident()}")
        print(f"shared_int {shared_int.value}")
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
            shared_int.value += 1
            self.number_of_connections += 1
            print("Number of connections", self.number_of_connections, shared_int.value)
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



class GameProcessorFactory:
    def __init__(self, ):
        pass

    def getProcessor(self, client):
        return Game.Processor(GameHandler())  # could optionally pass client to GameHandler if desired

def serve(port):
    handler = GameHandler()
    transport = TSocket.TServerSocket(host='0.0.0.0', port=port)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()

    # server = PFThreadedServer(GameProcessorFactory(), transport, tfactory, pfactory)
    server = PFProcessServer(GameProcessorFactory(), transport, tfactory, pfactory)
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

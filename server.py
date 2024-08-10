from typing import Union
from thrift import Thrift
from thrift.protocol import TBinaryProtocol
from thrift.protocol.THeaderProtocol import THeaderProtocolFactory
from thrift.server.TServer import TServer
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
import threading
import queue
import logging as logger

import asyncio

def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

def run_async_func_in_new_thread(target, *args):
    new_loop = asyncio.new_event_loop()
    t = threading.Thread(target=start_loop, args=(new_loop,))
    t.start()

    asyncio.run_coroutine_threadsafe(target(*args), new_loop)
class TThreadedServer2(TServer):
    """Threaded server that spawns a new thread per each connection."""

    def __init__(self, *args, **kwargs):
        TServer.__init__(self, *args)
        self.daemon = kwargs.get("daemon", False)

    def serve(self):
        self.serverTransport.listen()
        while True:
            try:
                client = self.serverTransport.accept()
                if not client:
                    continue
                t = threading.Thread(target=self.start_event_loop, args=(client,))
                # run_async_func_in_new_thread(self.handle, client)

                # t = threading.Thread(target=self.handle, args=(client,))
                t.setDaemon(self.daemon)
                t.start()
            except KeyboardInterrupt:
                raise
            except Exception as x:
                logger.exception(x)

    def start_event_loop(self, client):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.handle(client))
        loop.close()

    async def handle(self, client):
        itrans = self.inputTransportFactory.getTransport(client)
        iprot = self.inputProtocolFactory.getProtocol(itrans)

        # for THeaderProtocol, we must use the same protocol instance for input
        # and output so that the response is in the same dialect that the
        # server detected the request was in.
        if isinstance(self.inputProtocolFactory, THeaderProtocolFactory):
            otrans = None
            oprot = iprot
        else:
            otrans = self.outputTransportFactory.getTransport(client)
            oprot = self.outputProtocolFactory.getProtocol(otrans)

        try:
            while True:
                await self.processor.process(iprot, oprot)
        except TTransport.TTransportException:
            pass
        except Exception as x:
            logger.exception(x)

        itrans.close()
        if otrans:
            otrans.close()

class TThreadPoolServer2(TServer):
    """Server with a fixed size pool of threads which service requests."""

    def __init__(self, *args, **kwargs):
        TServer.__init__(self, *args)
        self.clients = queue.Queue()
        self.threads = 10
        self.daemon = kwargs.get("daemon", False)

    def setNumThreads(self, num):
        """Set the number of worker threads that should be created"""
        self.threads = num

    def serveThread(self):
        """Loop around getting clients from the shared queue and process them."""
        while True:
            try:
                client = self.clients.get()
                self.serveClient(client)
            except Exception as x:
                logger.exception(x)

    def serveClient(self, client):
        """Process input/output from a client for as long as possible"""
        itrans = self.inputTransportFactory.getTransport(client)
        iprot = self.inputProtocolFactory.getProtocol(itrans)

        # for THeaderProtocol, we must use the same protocol instance for input
        # and output so that the response is in the same dialect that the
        # server detected the request was in.
        if isinstance(self.inputProtocolFactory, THeaderProtocolFactory):
            otrans = None
            oprot = iprot
        else:
            otrans = self.outputTransportFactory.getTransport(client)
            oprot = self.outputProtocolFactory.getProtocol(otrans)

        try:
            while True:
                self.processor.process(iprot, oprot)
        except TTransport.TTransportException:
            pass
        except Exception as x:
            logger.exception(x)

        itrans.close()
        if otrans:
            otrans.close()

    def serve(self):
        """Start a fixed number of worker threads and put client into a queue"""
        for i in range(self.threads):
            try:
                t = threading.Thread(target=self.serveThread)
                t.setDaemon(self.daemon)
                t.start()
            except Exception as x:
                logger.exception(x)

        # Pump the socket for clients
        self.serverTransport.listen()
        while True:
            try:
                client = self.serverTransport.accept()
                if not client:
                    continue
                self.clients.put(client)
            except Exception as x:
                logger.exception(x)


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
        print("GetTrainerActions", state.world_model.cycle)
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
    server = TThreadedServer2(processor, transport, tfactory, pfactory)
    # server.setNumThreads(50)
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

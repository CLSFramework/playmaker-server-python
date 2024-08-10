from thrift.protocol import TBinaryProtocol
from thrift.transport import TSocket, TTransport
from soccer import Game
import sys
import os
from utils.PFProcessServer import PFProcessServer
from thrift.server.TServer import TThreadedServer
from utils.GameHandler import GameHandler
import logging

logging.basicConfig(level=logging.INFO)

def serve(port):
    handler = GameHandler()
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


if __name__ == '__main__':
    if len(sys.argv) < 2:
        port = 50051
    else:
        port = sys.argv[1]
    serve(port)

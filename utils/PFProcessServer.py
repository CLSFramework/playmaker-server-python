from thrift.protocol.THeaderProtocol import THeaderProtocolFactory
from thrift.server.TServer import TServer
from thrift.transport import TTransport
import multiprocessing


class PFProcessServer(TServer):
    """Process-based server that spawns a new process per each connection."""

    def __init__(self, *args):
        TServer.__init__(self, *args)
        # self.processorFactory = args[0]

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
        # processor = self.processorFactory.getProcessor(client)
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
                self.processor.process(iprot, oprot)
        except TTransport.TTransportException:
            pass
        except Exception as x:
            print(x)
        finally:
            itrans.close()
            if otrans:
                otrans.close()
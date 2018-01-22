import grpc
from concurrent import futures
import hydro_serving_grpc as hs
from PythonRuntimeService import PythonRuntimeService


class PythonRuntime:

    def __init__(self, model_path, contract_path):
        self.port = None
        self.server = None
        self.servicer = PythonRuntimeService(model_path, contract_path)

    def start(self, port="9090", max_workers=10):
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
        hs.add_PredictionServiceServicer_to_server(self.servicer, self.server)
        addr = "[::]:{}".format(port)
        print("Starting server on {}".format(addr))
        self.server.add_insecure_port(addr)
        self.server.start()

    def stop(self, code=0):
        self.server.stop(code)

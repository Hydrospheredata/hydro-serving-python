import grpc
from concurrent import futures
import hydro_serving_grpc as hs
from grpc._cython import cygrpc

from PythonRuntimeService import PythonRuntimeService
import sys
import os
import logging

class PythonRuntime:
    def __init__(self, model_path):
        self.port = None
        self.server = None
        self.contract_path = os.path.join(model_path, "contract.protobin")
        self.files_path = os.path.join(model_path, "files")
        self.model_path = os.path.join(self.files_path, "src")
        self.lib_path = os.path.join(model_path, "lib")

        if os.path.exists(self.lib_path):
            print("Added `{}` to PYTHON_PATH".format(self.lib_path))
            sys.path.append(self.lib_path)

        self.servicer = PythonRuntimeService(self.model_path, self.contract_path)
        self.logger = logging.getLogger("main")

    def start(self, port="9090", max_workers=10, max_message_size=256*1024*1024):
        options = [(cygrpc.ChannelArgKey.max_send_message_length, max_message_size),
                   (cygrpc.ChannelArgKey.max_receive_message_length, max_message_size)]
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers), options=options)
        hs.add_PredictionServiceServicer_to_server(self.servicer, self.server)
        addr = "[::]:{}".format(port)
        self.logger.info("Starting server on {}".format(addr))
        self.server.add_insecure_port(addr)
        self.server.start()

    def stop(self, code=0):
        self.server.stop(code)

import grpc
from concurrent import futures
from grpc._cython import cygrpc

from src.grpc_service import load_model
from hydro_serving_grpc.serving.runtime.api_pb2_grpc import add_PredictionServiceServicer_to_server
from grpc_health.v1.health_pb2_grpc import add_HealthServicer_to_server

import logging

class GRPCServer:
    def __init__(self, model_path):
        self.port = None
        self.server = None
        self.servicer = load_model(model_path)
        self.logger = logging.getLogger("GRPCServer")

    def start(self, port="9090", max_workers=10, max_message_size=256*1024*1024):
        options = [(cygrpc.ChannelArgKey.max_send_message_length, max_message_size),
                   (cygrpc.ChannelArgKey.max_receive_message_length, max_message_size)]
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers), options=options)
        add_PredictionServiceServicer_to_server(self.servicer, self.server)
        add_HealthServicer_to_server(self.servicer, self.server)
        addr = "[::]:{}".format(port)
        self.logger.info("Starting server on {}".format(addr))
        assigned_port = self.server.add_insecure_port(addr)
        self.logger.info("GRPC assigned port {}".format(assigned_port))
        self.server.start()

    def stop(self, code=0):
        self.server.stop(code)
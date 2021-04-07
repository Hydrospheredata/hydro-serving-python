import unittest
import time
import grpc
import sys
import os

from google.protobuf.empty_pb2 import Empty

from src.PythonRuntime import PythonRuntime
import hydro_serving_grpc as hs

from hydro_serving_grpc.serving.contract.signature_pb2 import ModelSignature
from hydro_serving_grpc.serving.contract.field_pb2 import ModelField
from hydro_serving_grpc.serving.contract.types_pb2 import DT_INT8
from hydro_serving_grpc.serving.contract.tensor_pb2 import Tensor
from hydro_serving_grpc.serving.runtime.api_pb2_grpc import PredictionServiceStub
from hydro_serving_grpc.serving.runtime.api_pb2 import PredictRequest


class RuntimeTests(unittest.TestCase):
    @staticmethod
    def generate_signature():
        signature = ModelSignature(
            signature_name="crash_add",
            inputs=[
                ModelField(
                    name="a",
                    dtype=DT_INT8
                ),
                ModelField(
                    name="b",
                    dtype=DT_INT8
                )
            ],
            outputs=[
                ModelField(
                    name="sum",
                    dtype=DT_INT8
                )
            ]
        )
        with open("test/models/crashing_calculator/contract.protobin", "wb") as file:
            file.write(signature.SerializeToString())
 
    def test_crashing_model(self):
        self.generate_signature()
        path = os.path.abspath("test/models/crashing_calculator")
        runtime = PythonRuntime(path)
        runtime.start(port="9091")

        try:
            time.sleep(1)
            channel = grpc.insecure_channel('localhost:9091')
            client = PredictionServiceStub(channel=channel)
            a, b = Tensor(), Tensor()
            a.ParseFromString(Tensor(dtype=DT_INT8, int_val=[3]).SerializeToString())
            b.ParseFromString(Tensor(dtype=DT_INT8, int_val=[2]).SerializeToString())
            request = PredictRequest(inputs={"a": a, "b": b})
            try:
                _ = client.Predict(request)
                self.fail("This case must fail on client.Predict")
            except grpc._channel._InactiveRpcError as e:
                self.assertEquals(e.details(), 'RuntimeError("I can\'t calculate anything :(")')
            except Exception as e:
                raise e
        finally:
            sys.path.remove(os.path.join(path, "files", "src"))
            del sys.modules['func_main']
            runtime.stop() 

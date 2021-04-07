import unittest
import time
import grpc
import sys
import os

from google.protobuf.empty_pb2 import Empty

from src.PythonRuntime import PythonRuntime
from hydro_serving_grpc.serving.contract.signature_pb2 import ModelSignature
from hydro_serving_grpc.serving.contract.field_pb2 import ModelField
from hydro_serving_grpc.serving.contract.tensor_pb2 import Tensor, TensorShape
from hydro_serving_grpc.serving.contract.types_pb2 import DT_INT8
from hydro_serving_grpc.serving.runtime.api_pb2_grpc import PredictionServiceStub
from hydro_serving_grpc.serving.runtime.api_pb2 import PredictRequest, PredictResponse


class RuntimeTests(unittest.TestCase):
    @staticmethod
    def generate_signature():
        signature = ModelSignature(
            signature_name="add",
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
        with open("test/models/calculator/contract.protobin", "wb") as file:
            file.write(signature.SerializeToString())

    def test_correct_signature(self):
        self.generate_signature()
        path = os.path.abspath("test/models/calculator")
        runtime = PythonRuntime(path)
        runtime.start(port="9090")

        try:
            time.sleep(1)
            channel = grpc.insecure_channel('localhost:9090')
            client = PredictionServiceStub(channel=channel)

            a, b = Tensor(), Tensor()
            a.ParseFromString(Tensor(dtype=DT_INT8, int_val=[3]).SerializeToString())
            b.ParseFromString(Tensor(dtype=DT_INT8, int_val=[2]).SerializeToString())
            request = PredictRequest(inputs={"a": a, "b": b})

            result = client.Predict(request)
            expected = PredictResponse(outputs={
                "sum": Tensor(dtype=DT_INT8, tensor_shape=TensorShape(), int_val=[5])
            })
            self.assertEqual(result, expected)
        finally:
            sys.path.remove(os.path.join(path, "files", "src"))
            del sys.modules['func_main']
            runtime.stop()

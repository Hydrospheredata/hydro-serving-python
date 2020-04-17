import unittest
import time
import grpc
import sys
import os

from google.protobuf.empty_pb2 import Empty

from src.runtime import PythonRuntime
import hydro_serving_grpc as hs


class RuntimeTests(unittest.TestCase):
    @staticmethod
    def generate_contract():
        contract = hs.ModelContract(
            model_name="calculator",
            signatures=[
                hs.ModelSignature(
                    signature_name="add",
                    inputs=[
                        hs.ModelField(
                            field_name="a",
                            info=hs.TensorInfo(
                                dtype=hs.DT_INT8
                            )
                        ),
                        hs.ModelField(
                            field_name="b",
                            info=hs.TensorInfo(
                                dtype=hs.DT_INT8
                            )
                        )
                    ],
                    outputs=[
                        hs.ModelField(
                            field_name="sum",
                            info=hs.TensorInfo(
                                dtype=hs.DT_INT8
                            )
                        )
                    ]
                )
            ]
        )
        with open("models/calculator/contract.protobin", "wb") as file:
            file.write(contract.SerializeToString())

    @staticmethod
    def delete_contract():
        os.remove("models/calculator/contract.protobin")

    def test_correct_signature(self):
        path = os.path.abspath("test/models/calculator")
        runtime = PythonRuntime(path)
        runtime.start(port="9090")

        try:
            time.sleep(1)

            channel = grpc.insecure_channel('localhost:9090')
            client = hs.PredictionServiceStub(channel=channel)
            a = hs.TensorProto()
            a.ParseFromString(
                hs.TensorProto(
                    dtype=hs.DT_INT8,
                    int_val=[3]
                ).SerializeToString()
            )
            b = hs.TensorProto()
            b.ParseFromString(
                hs.TensorProto(
                    dtype=hs.DT_INT8,
                    int_val=[2]
                ).SerializeToString()
            )
            request = hs.PredictRequest(
                inputs={
                    "a": a,
                    "b": b
                }
            )

            result = client.Predict(request)
            expected = hs.PredictResponse(
                outputs={
                    "sum": hs.TensorProto(
                        dtype=hs.DT_INT8,
                        tensor_shape=hs.TensorShapeProto(),
                        int_val=[5]
                    )
                }
            )
            print(result)
            self.assertEqual(result, expected)

            status = client.Status(Empty())
            print(status)
            self.assertEqual(status.status, 1)
            self.assertEqual(status.message, "ok")
        finally:
            sys.path.remove(os.path.join(path, "files", "src"))
            del sys.modules['func_main']
            runtime.stop()

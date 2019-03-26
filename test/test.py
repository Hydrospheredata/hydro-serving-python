import unittest
import time
import grpc
import sys
import os

from google.protobuf.empty_pb2 import Empty

sys.path.append("../src")
from PythonRuntime import PythonRuntime
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
        path = os.path.abspath("models/calculator")
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
                model_spec=hs.ModelSpec(signature_name="add"),
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
            self.assertEqual(status.status, 2)
            self.assertEqual(status.message, "ok")
        finally:
            runtime.stop()

    # def test_incorrect_signature(self):
    #     runtime = PythonRuntime("models/tf_summator")
    #     runtime.start(port="9090")
    #
    #     try:
    #         time.sleep(1)
    #         channel = grpc.insecure_channel('localhost:9090')
    #         client = hs.PredictionServiceStub(channel=channel)
    #         a = hs.TensorProto()
    #         a.ParseFromString(make_tensor_proto(3, dtype=hs.DT_INT8).SerializeToString())
    #         b = hs.TensorProto()
    #         b.ParseFromString(make_tensor_proto(2, dtype=hs.DT_INT8).SerializeToString())
    #         request = hs.PredictRequest(
    #             model_spec=hs.ModelSpec(signature_name="missing_sig"),
    #             inputs={
    #                 "a": a,
    #                 "b": b
    #             }
    #         )
    #         client.Predict(request)
    #     except grpc.RpcError as ex:
    #         self.assertEqual(ex.code(), grpc.StatusCode.INVALID_ARGUMENT)
    #         self.assertEqual(ex.details(), "missing_sig signature is not present in the model")
    #     except Exception as ex:
    #         self.fail("Unexpected exception: {}".format(ex))
    #     finally:
    #         runtime.stop(0)


if __name__ == "__main__":
    unittest.main()

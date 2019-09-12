import unittest
import time
import grpc
import sys
import os

from google.protobuf.empty_pb2 import Empty

from src.PythonRuntime import PythonRuntime
import hydro_serving_grpc as hs


class RuntimeTests(unittest.TestCase):
    @staticmethod
    def generate_contract():
        contract = hs.contract.ModelContract(
            model_name="crashing_calculator",
            predict=hs.contract.ModelSignature(
                    signature_name="crash_add",
                    inputs=[
                        hs.contract.ModelField(
                            name="a",
                            dtype=hs.DT_INT8
                        ),
                        hs.contract.ModelField(
                            name="b",
                            dtype=hs.DT_INT8
                        )
                    ],
                    outputs=[
                        hs.contract.ModelField(
                            name="sum",
                            dtype=hs.DT_INT8
                        )
                    ]
                )
        )
        with open("test/models/crashing_calculator/contract.protobin", "wb") as file:
            file.write(contract.SerializeToString())
 
    def test_crashing_model(self):
        self.generate_contract()
        path = os.path.abspath("test/models/crashing_calculator")
        runtime = PythonRuntime(path)
        runtime.start(port="9091")

        try:
            time.sleep(1)
            channel = grpc.insecure_channel('localhost:9091')
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
            
            try:
                result = client.Predict(request)
                print(result)
                self.fail("This case must fail on client.Predict")
            except grpc._channel._Rendezvous as e:
                print("Received expected exception", type(e))
            except Exception as e:
                raise e

        finally:
            sys.path.remove(os.path.join(path, "files", "src"))
            del sys.modules['func_main']
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

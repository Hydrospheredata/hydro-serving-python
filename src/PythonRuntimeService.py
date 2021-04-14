import importlib
import logging
import os
import sys
from typing import Dict

import grpc
import google
from hydro_serving_grpc.serving.runtime.api_pb2_grpc import PredictionServiceServicer
from hydro_serving_grpc.serving.contract.tensor_pb2 import Tensor
from hydro_serving_grpc.serving.contract.signature_pb2 import ModelSignature
from hydro_serving_grpc.serving.runtime.api_pb2 import PredictResponse
from hydrosdk.data.conversions import tensor_proto_to_np, np_to_tensor_proto

class PythonRuntimeService(PredictionServiceServicer):
    def __init__(self, model_path, signature_path):
        self.logger = logging.getLogger("PythonRuntimeService")
        self.model_path = "{}/func_main.py".format(model_path)
        self.module_path = self.model_path.replace('.py', '')
        self.module_path = self.module_path.replace('/', '.')[1:]
        sys.path.append(model_path)

        signature = ModelSignature()
        if not os.path.exists(signature_path):
            raise FileNotFoundError(f"Couldn't find serialized signature at {signature_path}")
        with open(signature_path, "rb") as file:
            try: 
                signature.ParseFromString(file.read())
            except google.protobuf.message.DecodeError as e:
                raise ValueError(f"Couldn't parse serialized signature at {signature_path}: {e}") from e
            self.signature = signature

        self.status = "UNKNOWN"
        self.status_message = "Preparing to import func_main"
        self.error = None
        try:
            self.module = importlib.import_module("func_main")
            self.executable = getattr(self.module, self.signature.signature_name)
            self.status = "SERVING"
            self.status_message = "ok"
        except Exception as ex:
            logging.exception("Error during func_main import. Runtime is in invalid state.")
            self.error = ex
            self.status = "NOT_SERVING"
            self.status_message = "'func_main' import error: {}".format(ex)

    def Predict(self, request, context):
        if self.error:
            context.abort(
                grpc.StatusCode.INTERNAL,
                "func_main is not imported due to error: {}".format(str(self.error))
            )
        else:
            self.logger.info("Received inference request: {}".format(request)[:256])
            try:

                numpy_request_inputs: Dict[str] = {k: tensor_proto_to_np(t) for k, t in request.inputs.items()}
                numpy_outputs: Dict[str] = self.executable(**numpy_request_inputs)

                try:
                    # If TensorProto is returned, than pass it. If Numpy is returned, cast it to TensorProto
                    tensor_proto_outputs: Dict[str, Tensor] = {k: (v if isinstance(v, Tensor) else np_to_tensor_proto(v))
                                                                    for k, v in numpy_outputs.items()}

                    result = PredictResponse(outputs=tensor_proto_outputs)
                    self.logger.info("Answer: {}".format(result)[:256])
                    return result
                except ValueError as e:
                    self.logger.exception("Could not convert numpy output ({}) to tensor proto. {}".format(numpy_outputs, e))
                    context.abort(grpc.StatusCode.OUT_OF_RANGE, repr(e))

            except Exception as ex:
                self.logger.exception("Function {} failed to handle request".format(self.signature.signature_name))
                context.abort(grpc.StatusCode.INTERNAL, repr(ex))

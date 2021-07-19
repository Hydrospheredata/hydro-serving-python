import importlib
import logging
import sys
import os
from typing import Dict
import grpc
from hydro_serving_grpc.serving.runtime.api_pb2_grpc import PredictionServiceServicer
from hydro_serving_grpc.serving.contract.tensor_pb2 import Tensor
from hydro_serving_grpc.serving.runtime.api_pb2 import PredictResponse
from hydro_serving_grpc.serving.contract.signature_pb2 import ModelSignature
from hydrosdk.data.conversions import tensor_proto_to_np, np_to_tensor_proto

from grpc_health.v1.health_pb2 import HealthCheckResponse
from grpc_health.v1.health_pb2_grpc import HealthServicer


def load_model(model_path):
    signature_path = os.path.join(model_path, "contract.protobin")
    files_path = os.path.join(model_path, "files")
    src_path = os.path.join(files_path, "src")
    lib_path = os.path.join(src_path, "lib")
    
    with open(signature_path, "rb") as file:
        try: 
            signature = ModelSignature()
            signature.ParseFromString(file.read())
        except Exception as e:
            raise ValueError(f"Couldn't parse serialized signature at {signature_path}: {e}") from e

    logging.info("Added model `{}` to PYTHON_PATH".format(model_path))
    sys.path.append(model_path)

    logging.info("Added src `{}` to PYTHON_PATH".format(src_path))
    sys.path.append(src_path)

    if os.path.exists(lib_path):
        logging.info("Added lib `{}` to PYTHON_PATH".format(lib_path))
        sys.path.append(lib_path)

    module = importlib.import_module("func_main")
    executable = getattr(module, signature.signature_name)
    logging.info(f"Got {signature.signature_name} function from the module")

    return PythonGRPCService(executable, signature)

class PythonGRPCService(PredictionServiceServicer, HealthServicer):
    def __init__(self, executable, signature):
        self.logger = logging.getLogger("PythonGRPCService")
        self.executable = executable
        self.signature  = signature

    def Predict(self, request, context):
        self.logger.info("Received inference request: {}".format(request)[:256])
        numpy_outputs = {}
        try:
            numpy_request_inputs: Dict[str] = {k: tensor_proto_to_np(t) for k, t in request.inputs.items()}
            numpy_outputs: Dict[str] = self.executable(**numpy_request_inputs)
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

    def Check(self, request, context):
        return HealthCheckResponse(status="SERVING")

import importlib
import logging
import sys
from typing import Dict

from grpc_health.v1.health_pb2 import HealthCheckRequest, HealthCheckResponse
from grpc_health.v1.health_pb2_grpc import HealthServicer

import grpc
import hydro_serving_grpc as hs
import numpy as np
from hydro_serving_grpc.tf.api import PredictionServiceServicer
from hydrosdk.data.conversions import tensor_proto_to_nparray, nparray_to_tensor_proto


class PythonRuntimeService(PredictionServiceServicer, HealthServicer):
    def __init__(self, model_path, contract_path):
        self.logger = logging.getLogger("PythonRuntimeService")
        self.model_path = "{}/func_main.py".format(model_path)
        self.module_path = self.model_path.replace('.py', '')
        self.module_path = self.module_path.replace('/', '.')[1:]
        sys.path.append(model_path)

        contract = hs.contract.ModelContract()
        with open(contract_path, "rb") as file:
            contract.ParseFromString(file.read())
            self.contract = contract

        self.status = "NOT_SERVING"
        self.status_message = "Preparing to import func_main"
        self.error = None
        try:
            self.module = importlib.import_module("func_main")
            self.executable = getattr(self.module, self.contract.predict.signature_name)
            self.status = "SERVING"
            self.status_message = "OK"
            logging.info("Initialization ok")
        except Exception as ex:
            logging.exception("Error during func_main import. Runtime is in invalid state.")
            self.error = ex
            self.status = "NOT_SERVING"
            self.status_message = "'func_main' import error: {}".format(ex)
            raise ex

    def Predict(self, request, context):
        if self.error:
            context.abort(
                grpc.StatusCode.INTERNAL,
                "func_main is not imported due to error: {}".format(str(self.error))
            )
        else:
            self.logger.info("Received inference request: {}".format(request)[:256])
            try:
                numpy_request_inputs: Dict[str, np.array] = {k: tensor_proto_to_nparray(t) for k, t in request.inputs.items()}
                numpy_outputs: Dict[str, np.array] = self.executable(**numpy_request_inputs)

                try:
                    tensor_proto_outputs = {k: nparray_to_tensor_proto(v) for k, v in numpy_outputs.items()}
                    result = hs.PredictResponse(outputs=tensor_proto_outputs)
                    self.logger.info("Answer: {}".format(result)[:256])
                    return result
                except ValueError as e:
                    error_message = "Could not convert numpy output ({}) to tensor proto. {}".format(numpy_outputs, e)
                    self.logger.warning(error_message)
                    context.set_code(grpc.StatusCode.OUT_OF_RANGE)
                    context.set_details(error_message)
                    return hs.PredictResponse()

            except Exception as ex:
                self.logger.exception("Function {} failed to handle request".format(self.contract.predict.signature_name))
                context.abort(grpc.StatusCode.INTERNAL, repr(ex))

    def Status(self, request, context):
        return hs.tf.api.StatusResponse(
            status=self.status,
            message=self.status_message
        )

    def Check(self, request, context):
        return HealthCheckResponse(status=self.status)

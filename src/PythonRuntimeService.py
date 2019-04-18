import hydro_serving_grpc as hs
import grpc
import importlib
import sys
import logging

from hydro_serving_grpc.tf.api import PredictionServiceServicer


class PythonRuntimeService(PredictionServiceServicer):
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

        self.status = "UNKNOWN"
        self.status_message = "Preparing to import func_main"
        try:
            self.module = importlib.import_module("func_main")
            self.executable = getattr(self.module, self.contract.predict.signature_name)
            self.status = "SERVING"
            self.status_message = "ok"
        except Exception as ex:
            logging.exception("Error during func_main import. Runtime is in invalid state.")
            self.status = "NOT_SERVING"
            self.status_message = "'func_main' import error: {}".format(ex)

    def Predict(self, request, context):
        self.logger.info("Received inference request: {}".format(request)[:256])
        try:
            result = self.executable(**request.inputs)
            if not isinstance(result, hs.PredictResponse):
                self.logger.warning("Type of a result ({}) is not `PredictResponse`".format(result))
                context.set_code(grpc.StatusCode.OUT_OF_RANGE)
                context.set_details("Type of a result ({}) is not `PredictResponse`".format(result))
                return hs.PredictResponse()

            self.logger.info("Answer: {}".format(result)[:256])
            return result
        except Exception as ex:
            context.abort(grpc.StatusCode.INTERNAL, repr(ex))

    def Status(self, request, context):
        return hs.tf.api.StatusResponse(
            status=self.status,
            message=self.status_message
        )
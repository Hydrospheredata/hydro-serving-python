import hydro_serving_grpc as hs
import grpc
import importlib
import sys
import logging


class PythonRuntimeService(hs.PredictionServiceServicer):
    def __init__(self, model_path, contract_path):
        self.logger = logging.getLogger("PythonRuntimeService")
        self.model_path = "{}/func_main.py".format(model_path)
        self.module_path = self.model_path.replace('.py', '')
        self.module_path = self.module_path.replace('/', '.')[1:]
        sys.path.append(model_path)

        contract = hs.ModelContract()
        with open(contract_path, "rb") as file:
            contract.ParseFromString(file.read())
            self.contract = contract

    def Predict(self, request, context):
        model_spec = request.model_spec
        self.logger.info("Received inference request: {}".format(request))

        selected_signature = None

        for signature in self.contract.signatures:
            if signature.signature_name == model_spec.signature_name:
                selected_signature = signature

        if selected_signature is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("{} signature is not present in the model".format(model_spec.signature_name))
            return hs.PredictResponse()

        module = importlib.import_module("func_main")
        executable = getattr(module, selected_signature.signature_name)
        result = executable(**request.inputs)
        if not isinstance(result, hs.PredictResponse):
            self.logger.warning("Type of a result ({}) is not `PredictResponse`".format(result))
            context.set_code(grpc.StatusCode.OUT_OF_RANGE)
            context.set_details("Type of a result ({}) is not `PredictResponse`".format(result))
            return hs.PredictResponse()

        self.logger.info("Answer: {}".format(result))
        return result

import os
from urllib.parse import urljoin

import mlflow
import onnxruntime as ort
import requests
import triton_python_backend_utils as pb_utils

MLFLOW_MODEL_NAME = os.getenv("MLFLOW_MODEL_NAME", "onnx-model")
MLFLOW_MODEL_VERSION = os.getenv("MLFLOW_MODEL_VERSION", "1")
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")


class TritonPythonModel:
    def initialize(self, args):
        self.logger = pb_utils.Logger
        self.logger.log_info("Initializing model...")

        health_url = urljoin(MLFLOW_TRACKING_URI, "health")
        response = requests.get(health_url, timeout=5)
        if response.status_code != 200:
            raise Exception("MLflow server is not healthy")

        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        client = mlflow.tracking.MlflowClient()

        registered_model = client.get_model_version(MLFLOW_MODEL_NAME, MLFLOW_MODEL_VERSION)
        local_path = mlflow.artifacts.download_artifacts(artifact_uri=registered_model.source)
        self.session = ort.InferenceSession(local_path)

        # Get input and output names
        self.input_name = self.session.get_inputs()[0].name
        self.output_names = [output.name for output in self.session.get_outputs()]

        self.logger.log_info(f"MLflow model loaded at {local_path}")

    def execute(self, requests):
        responses = []
        self.logger.log_info("Executing model...")
        for request in requests:
            input_tensor = pb_utils.get_input_tensor_by_name(request, "images").as_numpy()

            # Run ONNX inference
            results = self.session.run(self.output_names, {self.input_name: input_tensor})

            # Create output tensor
            output_tensor = pb_utils.Tensor("detections", results[0])
            responses.append(pb_utils.InferenceResponse([output_tensor]))

        self.logger.log_info("Inference completed successfully.")
        return responses

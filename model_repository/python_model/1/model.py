import os

import mlflow
import onnxruntime as ort
import triton_python_backend_utils as pb_utils

MLFLOW_MODEL_NAME = os.getenv("MLFLOW_MODEL_NAME", "YOLOv11n")
MLFLOW_MODEL_VERSION = os.getenv("MLFLOW_MODEL_VERSION", "1")
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")


class TritonPythonModel:
    def initialize(self, args):
        self.logger = pb_utils.Logger
        self.logger.log_info("Initializing model...")
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        client = mlflow.tracking.MlflowClient()
        registered_model = client.get_registered_model(MLFLOW_MODEL_NAME)

        # Download the ONNX model file from MLflow to a local path
        local_path = mlflow.artifacts.download_artifacts(artifact_uri=registered_model.latest_versions[0].source)

        # Initialize ONNX Runtime session
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

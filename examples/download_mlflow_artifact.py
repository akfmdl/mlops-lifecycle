import argparse
import os
from urllib.parse import urljoin

import mlflow
import requests

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")


def download_mlflow_artifact(model_name, model_version, output_dir):
    health_url = urljoin(MLFLOW_TRACKING_URI, "health")
    response = requests.get(health_url, timeout=5)
    if response.status_code != 200:
        raise Exception("MLflow server is not healthy")

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = mlflow.tracking.MlflowClient()

    # Get the specific model version instead of using the latest
    registered_model = client.get_model_version(model_name, model_version)

    # Download the model file from MLflow to a local path
    mlflow.artifacts.download_artifacts(artifact_uri=registered_model.source, dst_path=output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default="onnx-model")
    parser.add_argument("--model_version", type=str, default="1")
    parser.add_argument("--output_dir", type=str, default=".")
    args = parser.parse_args()

    download_mlflow_artifact(args.model_name, args.model_version, args.output_dir)

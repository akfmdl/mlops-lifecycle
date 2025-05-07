import os

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    APP_NAME: str = os.getenv("APP_NAME", "fastapi-app")
    MODEL_NAMESPACE: str = os.getenv("MODEL_NAMESPACE", "mlops-platform")
    SERVICE_HOST: str = os.getenv("SERVICE_HOST", "localhost")
    SERVICE_PORT: int = int(os.getenv("SERVICE_PORT", "8888"))
    ONNX_MODEL_TRITON_URL: str = os.getenv("ONNX_MODEL_TRITON_URL", "localhost:30401")
    OTLP_GRPC_ENDPOINT: str = os.environ.get("OTLP_GRPC_ENDPOINT", "http://localhost:31834")


settings = Config(_env_file=None)

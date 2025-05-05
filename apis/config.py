import os

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    MODEL_NAMESPACE: str = os.getenv("MODEL_NAMESPACE", "mlops-platform")
    SERVICE_HOST: str = os.getenv("SERVICE_HOST", "localhost")
    SERVICE_PORT: int = int(os.getenv("SERVICE_PORT", "8888"))
    TRITON_URL: str = os.getenv("TRITON_URL", "")


settings = Config(_env_file=None)

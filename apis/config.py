import os

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    MODEL_NAMESPACE: str = os.getenv("MODEL_NAMESPACE", "mlops-platform")
    UVICORN_HOST: str = os.getenv("UVICORN_HOST", "localhost")
    UVICORN_PORT: int = int(os.getenv("UVICORN_PORT", "8888"))
    TRITON_URL: str = os.getenv("TRITON_URL", "")


settings = Config(_env_file=None)

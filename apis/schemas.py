from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    model_name: str = Field(
        title="model_name",
        description="model_name",
        default="onnx-model",
    )
    model_version: str = Field(
        title="model_version",
        description="model_version",
        default="1",
    )
    image_url: str = Field(
        title="image_url",
        description="image_url",
        default="https://djl.ai/examples/src/test/resources/dog_bike_car.jpg",
    )


class PredictResponse(BaseModel):
    result_image_url: str = Field(
        title="result_image_url",
        description="result_image_url",
        default="",
    )
    prediction: str = Field(
        title="prediction",
        description="prediction",
        default="",
    )

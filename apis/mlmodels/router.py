import os
import uuid

import cv2
import requests
import tritonclient.http as httpclient
from config import settings
from fastapi import APIRouter, HTTPException
from kubernetes import client, config
from schemas import PredictRequest, PredictResponse
from tritonclient.utils import InferenceServerException

from . import utils

router = APIRouter()


@router.get(
    "/",
    description="모델 리스트 조회",
    tags=["Models"],
)
def get_models():
    try:
        # Load the kube config
        config.load_incluster_config()  # For running inside a Kubernetes cluster
    except config.config_exception.ConfigException:
        # Fallback to local kube config if not running in a cluster
        try:
            config.load_kube_config()
        except config.config_exception.ConfigException as inner_exc:
            raise HTTPException(status_code=500, detail="Could not configure kubernetes client") from inner_exc

    apps_v1 = client.AppsV1Api()
    deployments = apps_v1.list_deployment_for_all_namespaces(label_selector="release=triton")
    deployment_names = [deployment.metadata.name for deployment in deployments.items]

    return deployment_names


@router.post(
    "/predict",
    description="모델 추론",
    response_model=PredictResponse,
    tags=["Models"],
)
def predict(request: PredictRequest):
    try:
        # 이미지 URL에서 이미지 다운로드
        try:
            image = utils.get_image_from_url(request.image_url)
            if image is None:
                raise HTTPException(status_code=400, detail="Invalid image format")

        except requests.RequestException as e:
            raise HTTPException(status_code=400, detail=f"Failed to download image: {str(e)}") from e

        # 이미지 원본 크기 저장
        original_shape = image.shape[:2]  # (height, width)

        # 이미지 전처리
        input_size = (640, 640)  # 기본 YOLO 입력 크기
        input_data = utils.preprocess_image(image, input_size)

        # Triton 서버 URL 설정 (model_name이 triton 서버 호스트와 포트를 포함할 수 있음)
        triton_url = (
            settings.TRITON_URL
            if settings.TRITON_URL
            else f"{request.model_name}.{settings.MODEL_NAMESPACE}.svc.cluster.local:8000"
        )

        # Triton 클라이언트 초기화
        triton_client = httpclient.InferenceServerClient(url=triton_url)

        # 서버 상태 확인
        if not triton_client.is_server_live():
            raise HTTPException(status_code=503, detail=f"Triton server {triton_url} is not running")

        # 입력 텐서 생성
        inputs = [httpclient.InferInput("images", input_data.shape, "FP32")]
        inputs[0].set_data_from_numpy(input_data)

        # 추론 요청
        response = triton_client.infer(
            model_name=request.model_name, inputs=inputs, model_version=request.model_version
        )

        # 출력 결과 가져오기
        output = response.as_numpy("output0")

        # 후처리 및 바운딩 박스 추출
        boxes, scores, class_ids = utils.postprocess_output(
            output,
            original_shape,
            input_size=input_size,
            conf_threshold=0.5,
            iou_threshold=0.5,
        )

        # 감지 결과 그리기
        result_image = utils.draw_detections(image.copy(), boxes, scores, class_ids, 0.5)

        # 결과 이미지 저장
        os.makedirs("static", exist_ok=True)
        result_filename = f"{uuid.uuid4()}.jpg"
        result_path = f"static/{result_filename}"
        cv2.imwrite(result_path, result_image)

        # 결과 URL 생성
        result_url = f"http://{settings.SERVICE_HOST}:{settings.SERVICE_PORT}/static/{result_filename}"
        return PredictResponse(result_image_url=result_url)

    except InferenceServerException as e:
        raise HTTPException(status_code=500, detail=f"Triton inference error: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}") from e

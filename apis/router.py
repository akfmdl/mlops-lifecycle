import json
import os
import uuid
from io import BytesIO

import cv2
import numpy as np
import requests
import tritonclient.http as httpclient
from config import settings
from fastapi import APIRouter, HTTPException
from kubernetes import client, config
from schemas import PredictRequest, PredictResponse
from tritonclient.utils import InferenceServerException

router = APIRouter()

# 색상 팔레트 캐싱
_color_palette_cache: dict[int, np.ndarray] = {}


def create_default_class_file():
    """기본 COCO 클래스 파일 생성"""
    os.makedirs("static", exist_ok=True)
    class_file_path = "static/coco_classes.json"

    # 이미 파일이 존재하면 생성하지 않음
    if os.path.exists(class_file_path):
        return

    # 기본 COCO 클래스 목록
    default_classes = [
        "person",
        "bicycle",
        "car",
        "motorcycle",
        "airplane",
        "bus",
        "train",
        "truck",
        "boat",
        "traffic light",
        "fire hydrant",
        "stop sign",
        "parking meter",
        "bench",
        "bird",
        "cat",
        "dog",
        "horse",
        "sheep",
        "cow",
        "elephant",
        "bear",
        "zebra",
        "giraffe",
        "backpack",
        "umbrella",
        "handbag",
        "tie",
        "suitcase",
        "frisbee",
        "skis",
        "snowboard",
        "sports ball",
        "kite",
        "baseball bat",
        "baseball glove",
        "skateboard",
        "surfboard",
        "tennis racket",
        "bottle",
        "wine glass",
        "cup",
        "fork",
        "knife",
        "spoon",
        "bowl",
        "banana",
        "apple",
        "sandwich",
        "orange",
        "broccoli",
        "carrot",
        "hot dog",
        "pizza",
        "donut",
        "cake",
        "chair",
        "couch",
        "potted plant",
        "bed",
        "dining table",
        "toilet",
        "tv",
        "laptop",
        "mouse",
        "remote",
        "keyboard",
        "cell phone",
        "microwave",
        "oven",
        "toaster",
        "sink",
        "refrigerator",
        "book",
        "clock",
        "vase",
        "scissors",
        "teddy bear",
        "hair drier",
        "toothbrush",
    ]

    # 파일 생성
    try:
        with open(class_file_path, "w") as f:
            json.dump(default_classes, f, indent=2)
    except Exception:
        pass  # 파일 생성 실패 시 무시


def get_coco_classes():
    """
    COCO 클래스 이름을 반환하는 함수
    1. 클래스 파일이 있으면 로드
    2. 없으면 기본 COCO 클래스 목록 사용
    """
    # 클래스 파일 경로
    class_file_path = "static/coco_classes.json"

    # 파일이 존재하면 로드
    if os.path.exists(class_file_path):
        try:
            with open(class_file_path, "r") as f:
                return json.load(f)
        except Exception:
            pass  # 파일 로드 실패 시 기본값 사용

    # 기본 COCO 클래스 목록
    return [
        "person",
        "bicycle",
        "car",
        "motorcycle",
        "airplane",
        "bus",
        "train",
        "truck",
        "boat",
        "traffic light",
        "fire hydrant",
        "stop sign",
        "parking meter",
        "bench",
        "bird",
        "cat",
        "dog",
        "horse",
        "sheep",
        "cow",
        "elephant",
        "bear",
        "zebra",
        "giraffe",
        "backpack",
        "umbrella",
        "handbag",
        "tie",
        "suitcase",
        "frisbee",
        "skis",
        "snowboard",
        "sports ball",
        "kite",
        "baseball bat",
        "baseball glove",
        "skateboard",
        "surfboard",
        "tennis racket",
        "bottle",
        "wine glass",
        "cup",
        "fork",
        "knife",
        "spoon",
        "bowl",
        "banana",
        "apple",
        "sandwich",
        "orange",
        "broccoli",
        "carrot",
        "hot dog",
        "pizza",
        "donut",
        "cake",
        "chair",
        "couch",
        "potted plant",
        "bed",
        "dining table",
        "toilet",
        "tv",
        "laptop",
        "mouse",
        "remote",
        "keyboard",
        "cell phone",
        "microwave",
        "oven",
        "toaster",
        "sink",
        "refrigerator",
        "book",
        "clock",
        "vase",
        "scissors",
        "teddy bear",
        "hair drier",
        "toothbrush",
    ]


def get_color_palette(num_classes):
    """클래스 수에 맞는 색상 팔레트 생성 (캐싱)"""
    if num_classes not in _color_palette_cache:
        _color_palette_cache[num_classes] = np.random.uniform(0, 255, size=(num_classes, 3))
    return _color_palette_cache[num_classes]


@router.get(
    "/",
    description="모델 리스트 조회",
    tags=["Models"],
)
def get_models():
    try:
        # 시작 시 기본 클래스 파일 생성
        create_default_class_file()

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


def preprocess_image(image, input_size=(640, 640)):
    """이미지 전처리 함수"""
    resized_image = cv2.resize(image, (input_size[0], input_size[1]))
    rgb_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB) / 255.0
    transposed_image = np.transpose(rgb_image, (2, 0, 1))
    input_data = np.expand_dims(transposed_image, axis=0).astype(np.float32)
    return input_data


def postprocess_output(output, img_shape, input_size=(640, 640), conf_threshold=0.5, iou_threshold=0.5):
    """모델 출력 후처리 함수"""
    outputs = np.transpose(np.squeeze(output))

    boxes = []
    scores = []
    class_ids = []

    rows = outputs.shape[0]
    img_height, img_width = img_shape

    scale_x = img_width / input_size[0]
    scale_y = img_height / input_size[1]

    for i in range(rows):
        classes_scores = outputs[i][4:]
        max_score = np.amax(classes_scores)

        if max_score >= conf_threshold:
            class_id = np.argmax(classes_scores)

            x, y, w, h = outputs[i][:4]

            left = int((x - w / 2) * scale_x)
            top = int((y - h / 2) * scale_y)
            width = int(w * scale_x)
            height = int(h * scale_y)

            left = max(0, left)
            top = max(0, top)
            width = min(width, img_width - left)
            height = min(height, img_height - top)

            boxes.append([left, top, width, height])
            scores.append(max_score)
            class_ids.append(class_id)

    filtered_boxes = []
    filtered_scores = []
    filtered_class_ids = []

    if boxes:
        try:
            indices = cv2.dnn.NMSBoxes(boxes, scores, conf_threshold, iou_threshold)

            if isinstance(indices, tuple):
                indices = list(indices)
            elif len(indices.shape) == 2:
                indices = indices.flatten()

            for idx in indices:
                filtered_boxes.append(boxes[idx])
                filtered_scores.append(scores[idx])
                filtered_class_ids.append(class_ids[idx])
        except Exception as e:
            filtered_boxes = boxes
            filtered_scores = scores
            filtered_class_ids = class_ids

    return filtered_boxes, filtered_scores, filtered_class_ids


def draw_detections(image, boxes, scores, class_ids, conf_threshold=0.5):
    """감지된 객체를 이미지에 그리는 함수"""
    # 필요할 때 클래스 이름과 색상 팔레트 생성
    class_names = get_coco_classes()
    color_palette = get_color_palette(len(class_names))

    for box, score, class_id in zip(boxes, scores, class_ids):
        if score < conf_threshold:
            continue

        x, y, w, h = box
        x, y, w, h = int(x), int(y), int(w), int(h)

        if 0 <= class_id < len(color_palette):
            color = color_palette[class_id]

            cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)

            class_name = class_names[class_id] if class_id < len(class_names) else f"class_{class_id}"
            label = f"{class_name}: {score:.2f}"

            (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)

            cv2.rectangle(image, (x, y - label_height - 5), (x + label_width, y), color, cv2.FILLED)
            cv2.putText(image, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

    return image


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
            response = requests.get(request.image_url, timeout=10)
            response.raise_for_status()

            # 이미지 바이트를 numpy 배열로 변환
            image_array = np.frombuffer(response.content, np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            if image is None:
                raise HTTPException(status_code=400, detail="Invalid image format")

        except requests.RequestException as e:
            raise HTTPException(status_code=400, detail=f"Failed to download image: {str(e)}") from e

        # 이미지 원본 크기 저장
        original_shape = image.shape[:2]  # (height, width)

        # 이미지 전처리
        input_size = (640, 640)  # 기본 YOLO 입력 크기
        input_data = preprocess_image(image, input_size)

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
        boxes, scores, class_ids = postprocess_output(
            output,
            original_shape,
            input_size=input_size,
            conf_threshold=0.5,
            iou_threshold=0.5,
        )

        # 감지 결과 그리기
        result_image = draw_detections(image.copy(), boxes, scores, class_ids, 0.5)

        # 결과 이미지 저장
        os.makedirs("static", exist_ok=True)
        result_filename = f"{uuid.uuid4()}.jpg"
        result_path = f"static/{result_filename}"
        cv2.imwrite(result_path, result_image)

        # 결과 URL 생성
        result_url = f"http://{settings.UVICORN_HOST}:{settings.UVICORN_PORT}/static/{result_filename}"

        # 결과 반환 - 여기서도 클래스 이름 동적으로 가져옴
        class_names = get_coco_classes()
        prediction_text = ", ".join(
            [
                f"{class_names[class_id] if class_id < len(class_names) else f'class_{class_id}'} ({score:.2f})"
                for class_id, score in zip(class_ids, scores)
                if score >= 0.5 and class_id < len(class_names)
            ]
        )

        return PredictResponse(result_image_url=result_url, prediction=prediction_text)

    except InferenceServerException as e:
        raise HTTPException(status_code=500, detail=f"Triton inference error: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}") from e

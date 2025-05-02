# pip install "tritonclient[all]"
import argparse
import sys

import cv2
import numpy as np
import tritonclient.http as httpclient
from tritonclient.utils import InferenceServerException

CLASS_NAMES = [
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

COLOR_PALETTE = np.random.uniform(0, 255, size=(len(CLASS_NAMES), 3))


def preprocess_image(image, input_size=(640, 640)):
    resized_image = cv2.resize(image, (input_size[0], input_size[1]))  # 모델 입력 크기에 맞게 조정
    rgb_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB) / 255.0  # RGB로 변환 및 정규화
    transposed_image = np.transpose(rgb_image, (2, 0, 1))  # 채널 순서 변경 (HWC → CHW)
    input_data = np.expand_dims(transposed_image, axis=0).astype(np.float32)  # 배치 차원 추가

    return input_data


def draw_detections(image, boxes, scores, class_ids, conf_threshold=0.5):
    """
    이미지에 감지된 객체의 경계 상자(bounding box)를 그립니다.

    Args:
        image (np.ndarray): 원본 이미지
        boxes (np.ndarray): 경계 상자 좌표 [x, y, width, height]
        scores (np.ndarray): 각 감지에 대한 신뢰도 점수
        class_ids (np.ndarray): 각 감지에 대한 클래스 ID
        conf_threshold (float): 표시할 감지에 대한 최소 신뢰도 임계값

    Returns:
        np.ndarray: 경계 상자가 그려진 이미지
    """
    for box, score, class_id in zip(boxes, scores, class_ids):
        if score < conf_threshold:
            continue

        # 경계 상자 좌표 추출
        x, y, w, h = box

        # 정수로 변환
        x, y, w, h = int(x), int(y), int(w), int(h)

        # 클래스 ID가 유효한 범위 내에 있는지 확인
        if 0 <= class_id < len(COLOR_PALETTE):
            # 색상 가져오기
            color = COLOR_PALETTE[class_id]

            # 경계 상자 그리기
            cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)

            # 클래스 이름과 신뢰도 점수
            class_name = CLASS_NAMES[class_id] if class_id < len(CLASS_NAMES) else f"class_{class_id}"
            label = f"{class_name}: {score:.2f}"

            # 텍스트 크기 계산
            (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)

            # 텍스트 배경 그리기
            cv2.rectangle(image, (x, y - label_height - 5), (x + label_width, y), color, cv2.FILLED)

            # 텍스트 그리기
            cv2.putText(image, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

    return image


def postprocess_output(output, img_shape, input_size=(640, 640), conf_threshold=0.5, iou_threshold=0.5):
    """
    모델 출력을 후처리하여 경계 상자, 점수 및 클래스 ID를 추출합니다.

    Args:
        output (np.ndarray): 모델의 출력 텐서
        img_shape (tuple): 원본 이미지의 높이와 너비 (height, width)
        conf_threshold (float): 감지에 대한 최소 신뢰도 임계값
        iou_threshold (float): 비최대 억제(NMS)에 대한 IoU 임계값

    Returns:
        tuple: (boxes, scores, class_ids) - 경계 상자, 점수, 클래스 ID
    """
    # 출력 텐서 변환
    outputs = np.transpose(np.squeeze(output))

    # 모든 감지에 대한 목록
    boxes = []
    scores = []
    class_ids = []

    # 출력 해석
    rows = outputs.shape[0]

    # 원본 이미지 높이와 너비
    img_height, img_width = img_shape

    # 입력 크기에서 원본 크기로의 스케일 계산
    # YOLO 모델이 보통 정사각형 입력을 사용하므로, 스케일 조정이 필요합니다
    scale_x = img_width / input_size[0]  # 모델 입력 너비 기준으로 조정
    scale_y = img_height / input_size[1]  # 모델 입력 높이 기준으로 조정

    for i in range(rows):
        # 클래스 점수 가져오기
        classes_scores = outputs[i][4:]

        # 최대 점수 찾기
        max_score = np.amax(classes_scores)

        # 임계값 이상인 경우에만 처리
        if max_score >= conf_threshold:
            class_id = np.argmax(classes_scores)

            # 상자 좌표 가져오기 (모델 출력은 일반적으로 정규화된 좌표임)
            x, y, w, h = outputs[i][:4]

            # 원본 이미지 크기에 맞게 좌표 조정
            left = int((x - w / 2) * scale_x)
            top = int((y - h / 2) * scale_y)
            width = int(w * scale_x)
            height = int(h * scale_y)

            # 좌표가 이미지 범위를 벗어나지 않도록 조정
            left = max(0, left)
            top = max(0, top)
            width = min(width, img_width - left)
            height = min(height, img_height - top)

            # 목록에 추가
            boxes.append([left, top, width, height])
            scores.append(max_score)
            class_ids.append(class_id)

    # 결과 필터링을 위한 변수 초기화
    filtered_boxes = []
    filtered_scores = []
    filtered_class_ids = []

    # 비최대 억제(NMS) 적용
    if boxes:  # 박스가 존재할 경우에만 NMS 적용
        try:
            indices = cv2.dnn.NMSBoxes(boxes, scores, conf_threshold, iou_threshold)

            # OpenCV 버전에 따라 인덱스가 다른 형식으로 반환될 수 있음
            if isinstance(indices, tuple):
                # OpenCV 3
                indices = list(indices)
            elif len(indices.shape) == 2:
                # OpenCV 4.2 이하 - 2D 배열
                indices = indices.flatten()

            # 결과 필터링
            for idx in indices:
                filtered_boxes.append(boxes[idx])
                filtered_scores.append(scores[idx])
                filtered_class_ids.append(class_ids[idx])
        except Exception as e:
            print(f"NMS 처리 중 오류 발생: {e}")
            # 오류 발생 시 원본 목록 반환
            filtered_boxes = boxes
            filtered_scores = scores
            filtered_class_ids = class_ids

    return filtered_boxes, filtered_scores, filtered_class_ids


def main(args):
    # 이미지 로드 및 전처리
    image = cv2.imread(args.image_path)
    if image is None:
        raise ValueError(f"Failed to load image from {args.image_path}")

    # 이미지 원본 크기 저장
    original_shape = image.shape[:2]  # (height, width)

    # 이미지 전처리: 모델 입력 크기에 맞게 조정
    input_data = preprocess_image(image, args.input_size)

    try:
        # Triton 클라이언트 초기화
        triton_client = httpclient.InferenceServerClient(url=args.triton_url)

        # 서버 상태 확인
        if not triton_client.is_server_live():
            print(f"Triton 서버({args.triton_url})가 실행 중이지 않습니다.")
            sys.exit(1)

        # 입력 텐서 생성
        inputs = [httpclient.InferInput("images", input_data.shape, "FP32")]
        inputs[0].set_data_from_numpy(input_data)

        # 추론 요청
        response = triton_client.infer(model_name=args.model_name, inputs=inputs, model_version=args.model_version)

        # 출력 결과 가져오기
        output = response.as_numpy(args.output_name)

        # 후처리 및 바운딩 박스 추출
        boxes, scores, class_ids = postprocess_output(
            output,
            original_shape,
            input_size=args.input_size,
            conf_threshold=args.conf_thres,
            iou_threshold=args.iou_thres,
        )

        # 감지 결과 그리기
        result_image = draw_detections(image.copy(), boxes, scores, class_ids, args.conf_thres)

        # 결과 이미지 저장 (저장 경로가 지정된 경우)
        if args.output_image:
            cv2.imwrite(args.output_image, result_image)
            print(f"결과 이미지가 {args.output_image}에 저장되었습니다.")

        # 결과 출력
        print(f"감지된 객체 수: {len(boxes)}")
        for i, (box, score, class_id) in enumerate(zip(boxes, scores, class_ids)):
            class_name = CLASS_NAMES[class_id] if class_id < len(CLASS_NAMES) else f"class_{class_id}"
            print(f"객체 {i + 1}: {class_name}, 신뢰도: {score:.4f}, 위치: {box}")

    except InferenceServerException as e:
        print(f"Triton 서버 오류: {e}")
        sys.exit(1)
    except ConnectionError:
        print(f"Triton 서버({args.triton_url})에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        sys.exit(1)
    except Exception as e:
        print(f"예기치 않은 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Triton Inference Client")
    parser.add_argument("--triton-url", type=str, default="localhost:8000", help="Triton server URL")
    parser.add_argument("--model-name", type=str, default="onnx-model", help="Model name registered in Triton")
    parser.add_argument("--model-version", type=str, default="1", help="Model version (empty string means latest version)")
    parser.add_argument("--image-path", type=str, default="examples/dog.jpg", help="Path to the input image")
    parser.add_argument("--input-size", type=int, nargs=2, default=[640, 640], help="Input image size (width, height)")
    parser.add_argument("--output-name", type=str, default="output0", help="Name of the output tensor")
    parser.add_argument("--conf-thres", type=float, default=0.5, help="Confidence threshold for detections")
    parser.add_argument("--iou-thres", type=float, default=0.5, help="IoU threshold for NMS")
    parser.add_argument("--output-image", type=str, default="dog_detection.jpg", help="Path to save the output image")
    args = parser.parse_args()

    main(args)

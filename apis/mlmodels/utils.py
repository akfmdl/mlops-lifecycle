import cv2
import numpy as np
import requests

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


def get_image_from_url(url: str):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    image = cv2.imdecode(np.frombuffer(response.content, np.uint8), cv2.IMREAD_COLOR)
    return image


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
        except Exception:
            filtered_boxes = boxes
            filtered_scores = scores
            filtered_class_ids = class_ids

    return filtered_boxes, filtered_scores, filtered_class_ids


def draw_detections(image, boxes, scores, class_ids, conf_threshold=0.5):
    """감지된 객체를 이미지에 그리는 함수"""
    for box, score, class_id in zip(boxes, scores, class_ids):
        if score < conf_threshold:
            continue

        x, y, w, h = box
        x, y, w, h = int(x), int(y), int(w), int(h)

        if 0 <= class_id < len(COLOR_PALETTE):
            color = COLOR_PALETTE[class_id]

            cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)

            class_name = CLASS_NAMES[class_id] if class_id < len(CLASS_NAMES) else f"class_{class_id}"
            label = f"{class_name}: {score:.2f}"

            (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)

            cv2.rectangle(image, (x, y - label_height - 5), (x + label_width, y), color, cv2.FILLED)
            cv2.putText(image, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

    return image

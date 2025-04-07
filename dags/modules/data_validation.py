from pathlib import Path

import cv2


def validate_image(image_path: str) -> bool:
    """이미지 파일이 손상되지 않았는지 검증합니다."""
    try:
        img = cv2.imread(str(image_path))
        if img is None:
            return False
        return True
    except Exception:
        return False


def validate_yolo_format(label_path: str, image_path: str) -> bool:
    """YOLO 형식의 라벨 파일이 올바른지 검증합니다."""
    try:
        # 이미지 크기 확인
        img = cv2.imread(str(image_path))
        if img is None:
            return False
        height, width = img.shape[:2]
        print(f"이미지 크기: {height}x{width}")

        # 라벨 파일 읽기
        with open(label_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for line in lines:
            parts = line.strip().split()
            if len(parts) != 5:  # YOLO format: class x_center y_center width height
                return False

            # 값들이 0-1 범위 내에 있는지 확인
            x_center = float(parts[1])
            y_center = float(parts[2])
            w = float(parts[3])
            h = float(parts[4])

            if not (0 <= x_center <= 1 and 0 <= y_center <= 1 and 0 <= w <= 1 and 0 <= h <= 1):
                return False

        return True
    except Exception:
        return False


def validate_dataset(data_path: str) -> list:
    """데이터셋의 모든 파일을 검증합니다."""
    images_path = Path(data_path) / "images"
    labels_path = Path(data_path) / "labels"

    invalid_files = []

    # 이미지와 라벨 파일 검증
    for img_path in images_path.glob("*.jpg"):
        label_path = labels_path / f"{img_path.stem}.txt"

        # 이미지 파일 검증
        if not validate_image(img_path):
            invalid_files.append(f"손상된 이미지: {img_path}")
            continue

        # 라벨 파일 존재 여부 확인
        if not label_path.exists():
            invalid_files.append(f"라벨 파일 없음: {img_path}")
            continue

        # YOLO 형식 검증 및 클래스 정보 수집
        try:
            if not validate_yolo_format(label_path, img_path):
                invalid_files.append(f"잘못된 YOLO 형식: {img_path}")
        except Exception as e:
            invalid_files.append(f"라벨 파일 처리 오류: {img_path}, 오류: {str(e)}")

    # 검증 결과 저장
    if invalid_files:
        result_path = Path(data_path) / "validation_results.txt"
        with open(result_path, "w", encoding="utf-8") as f:
            f.write("\n".join(invalid_files))
        raise ValueError(f"검증 실패: {len(invalid_files)}개의 문제가 발견되었습니다.")

    print("모든 파일이 검증을 통과했습니다.")
    return True

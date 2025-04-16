#!/usr/bin/env python3
import argparse
import sys
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


def validate_dataset(data_path):
    """데이터셋 검증"""
    data_path = Path(data_path)
    print(f"데이터셋 검증 중: {data_path}")

    invalid_files = []

    # 이미지와 라벨 파일 검증
    for img_path in data_path.rglob("*.jpg"):
        label_path = next(data_path.rglob(f"{img_path.stem}.txt"), None)

        # 이미지 파일 검증
        if not validate_image(img_path):
            invalid_files.append(f"손상된 이미지: {img_path}")
            continue

        # 라벨 파일 존재 여부 확인
        if not label_path:
            invalid_files.append(img_path)

    if invalid_files:
        print("검증 실패: 다음 파일의 label 파일이 존재하지 않습니다.")
        for file in invalid_files:
            print(f"- {file}")
        return False

    print("검증 성공: 모든 이미지와 라벨 파일이 존재합니다.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="데이터셋 검증")
    parser.add_argument("--data_path", type=str, help="데이터셋 경로", default="./data/raw")

    args = parser.parse_args()

    try:
        is_valid = validate_dataset(args.data_path)
        print(f"XCOM_RETURN:{is_valid}")
    except Exception as e:
        print(f"검증 실패: {e}")
        sys.exit(1)

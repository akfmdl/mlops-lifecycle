#!/usr/bin/env python3
import argparse
import shutil
import sys
from pathlib import Path

from sklearn.model_selection import train_test_split


def split_dataset(data_path, target_path, train_ratio=0.7, val_ratio=0.2, test_ratio=0.1):
    """데이터셋을 학습/검증/테스트 세트로 분할"""
    data_path = Path(data_path)
    target_path = Path(target_path)
    print(f"데이터셋 분할 중: {data_path} -> {target_path}")

    # 이미지와 라벨 디렉토리 찾기
    images_path = None
    labels_path = None

    # 여러 이미지 포맷 찾기
    image_files = []
    for ext in ["*.jpg", "*.jpeg", "*.png"]:
        found_files = list(data_path.rglob(ext))
        if found_files:
            image_files.extend(found_files)
            # 첫 번째 발견된 이미지 파일의 디렉토리를 이미지 경로로 설정
            if images_path is None:
                images_path = found_files[0].parent

    # 라벨 파일이 있는 디렉토리 찾기
    for label_path in data_path.rglob("*.txt"):
        # README.txt와 LICENSE 파일 제외
        if label_path.name in ["README.txt", "LICENSE"]:
            continue
        labels_path = label_path.parent
        break

    # 경로 존재 확인
    if not images_path or not images_path.exists():
        raise ValueError(f"이미지 경로가 존재하지 않습니다: {images_path}")
    if not labels_path or not labels_path.exists():
        raise ValueError(f"라벨 경로가 존재하지 않습니다: {labels_path}")

    # 디렉토리 생성
    for split in ["train", "val", "test"]:
        for subdir in ["images", "labels"]:
            (target_path / split / subdir).mkdir(parents=True, exist_ok=True)

    # 이미지 파일 목록 및 해당 확장자 저장
    if not image_files:
        raise ValueError("이미지 파일이 없습니다")

    # 파일 이름과 확장자 추출
    image_infos = [(f.stem, f.suffix) for f in image_files]

    # 중복 제거 (같은 파일명, 다른 확장자)
    unique_names = {}
    for stem, suffix in image_infos:
        # 동일 파일명에서는 첫 번째 발견된 파일 사용
        if stem not in unique_names:
            unique_names[stem] = suffix

    # 고유한 파일 이름 목록
    image_names = list(unique_names.keys())
    print(f"총 이미지 파일: {len(image_files)}개, 고유 파일명: {len(image_names)}개")

    # train/val/test 분할
    if train_ratio + val_ratio + test_ratio >= 1.0:
        raise ValueError("train_ratio + val_ratio + test_ratio 합은 1.0 미만이어야 합니다.")

    train_val, test_names = train_test_split(image_names, test_size=test_ratio)
    train_names, val_names = train_test_split(train_val, test_size=val_ratio / (train_ratio + val_ratio))

    print(f"학습: {len(train_names)}개, 검증: {len(val_names)}개, 테스트: {len(test_names)}개")

    # 파일 복사 함수
    def copy_files(names, split_name):
        for name in names:
            # 파일 확장자 가져오기
            suffix = unique_names[name]

            # 이미지 복사
            src_img = images_path / f"{name}{suffix}"
            # 저장시에는 원본 확장자 유지
            dst_img = target_path / split_name / "images" / f"{name}{suffix}"
            shutil.copy2(src_img, dst_img)

            # 라벨 복사 (있는 경우)
            src_label = labels_path / f"{name}.txt"
            if src_label.exists():
                dst_label = target_path / split_name / "labels" / f"{name}.txt"
                shutil.copy2(src_label, dst_label)

    # 각 세트 복사
    copy_files(train_names, "train")
    copy_files(val_names, "val")
    copy_files(test_names, "test")

    print("데이터셋 분할 완료")
    return str(target_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="데이터셋 학습/검증/테스트 분할")
    parser.add_argument("--data_path", type=str, help="원본 데이터셋 경로", default="./data/raw/extracted")
    parser.add_argument("--target_path", type=str, help="분할된 데이터셋 저장 경로", default="./data/splits")
    parser.add_argument("--train_ratio", type=float, default=0.7, help="학습 데이터 비율 (기본값: 0.7)")
    parser.add_argument("--val_ratio", type=float, default=0.2, help="검증 데이터 비율 (기본값: 0.2)")
    parser.add_argument("--test_ratio", type=float, default=0.1, help="테스트 데이터 비율 (기본값: 0.1)")

    args = parser.parse_args()

    try:
        result_path = split_dataset(args.data_path, args.target_path, args.train_ratio, args.val_ratio, args.test_ratio)
        print(f"XCOM_RETURN:{result_path}")
    except Exception as e:
        print(f"분할 실패: {e}")
        sys.exit(1)

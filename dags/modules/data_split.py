import random
import shutil
from pathlib import Path


def split_dataset(data_path: str, target_path: str, train_ratio: float = 0.8, val_ratio: float = 0.2) -> bool:
    """데이터셋을 학습, 검증, 테스트 세트로 분할합니다.

    Args:
        data_path: 이미지와 라벨이 있는 디렉토리 경로
        train_ratio: 학습 세트 비율 (기본값: 0.7)
        val_ratio: 검증 세트 비율 (기본값: 0.15)
    """
    # 경로를 Path 객체로 변환
    data_path = Path(data_path)
    print(f"데이터 경로: {data_path}")

    # 이미지와 라벨 디렉토리 찾기
    images_path = None
    labels_path = None

    # 이미지 파일이 있는 디렉토리 찾기
    for img_path in data_path.rglob("*.jpg"):
        images_path = img_path.parent
        break

    # 라벨 파일이 있는 디렉토리 찾기
    for label_path in data_path.rglob("*.txt"):
        # README.txt와 LICENSE 파일 제외
        if label_path.name in ["README.txt", "LICENSE"]:
            continue
        labels_path = label_path.parent
        break

    # 경로 확인
    if not images_path:
        raise ValueError(f"이미지 디렉토리를 찾을 수 없습니다: {data_path}")
    if not labels_path:
        raise ValueError(f"라벨 디렉토리를 찾을 수 없습니다: {data_path}")

    print(f"이미지 경로: {images_path}")
    print(f"라벨 경로: {labels_path}")

    # 출력 디렉토리 생성
    output_base = Path(target_path)
    for split in ["train", "val", "test"]:
        for subdir in ["images", "labels"]:
            (output_base / split / subdir).mkdir(parents=True, exist_ok=True)

    # 모든 이미지 파일 목록 가져오기
    image_files = list(images_path.glob("*.jpg"))
    print(f"총 이미지 파일 수: {len(image_files)}")

    if not image_files:
        raise ValueError(f"이미지 파일이 없습니다: {images_path}")

    random.shuffle(image_files)  # 데이터 무작위 섞기

    # 분할 비율 계산
    n_total = len(image_files)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)

    # 데이터 분할
    train_files = image_files[:n_train]
    val_files = image_files[n_train : n_train + n_val]
    test_files = image_files[n_train + n_val :]

    # 파일 복사 함수
    def copy_files(files, split_name):
        for img_path in files:
            # 이미지 파일 복사
            dest_img_path = output_base / split_name / "images" / img_path.name
            shutil.copy2(img_path, dest_img_path)
            print(f"이미지 복사: {img_path} -> {dest_img_path}")

            # 라벨 파일 복사
            label_path = labels_path / f"{img_path.stem}.txt"
            if label_path.exists():
                dest_label_path = output_base / split_name / "labels" / label_path.name
                shutil.copy2(label_path, dest_label_path)
                print(f"라벨 복사: {label_path} -> {dest_label_path}")
            else:
                print(f"경고: 라벨 파일이 없습니다: {label_path}")

    # 각 세트에 파일 복사
    copy_files(train_files, "train")
    copy_files(val_files, "val")
    copy_files(test_files, "test")

    # 분할 결과 출력
    print("데이터셋 분할 완료:")
    print(f"학습 세트: {len(train_files)}개")
    print(f"검증 세트: {len(val_files)}개")
    print(f"테스트 세트: {len(test_files)}개")

    return True


if __name__ == "__main__":
    split_dataset(
        data_path="./data/raw/extracted",
        target_path="./data/splits",
    )

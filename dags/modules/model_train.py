import json
from pathlib import Path

import requests
import yaml
from ultralytics import YOLO


def train_yolo(
    data_yaml_path: str,
    output_dir: str,
    epochs: int = 10,
    batch_size: int = 16,
    img_size: int = 640,
) -> bool:
    """YOLO 모델을 학습시킵니다.

    Args:
        data_yaml_path: 데이터셋 설정 YAML 파일 경로
        output_dir: 학습 결과를 저장할 디렉토리
        epochs: 학습 에포크 수
        batch_size: 배치 크기
        img_size: 입력 이미지 크기

    Returns:
        bool: 학습 성공 여부
    """
    # 출력 디렉토리 생성
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        # YOLO 모델 로드
        print("YOLO 모델 로드 중...")
        model = YOLO("yolo11n.pt")

        # YOLO 학습 실행
        print("YOLO 학습 시작...")
        train_results = model.train(
            data=data_yaml_path,
            epochs=epochs,
            batch=batch_size,
            imgsz=img_size,
            project=output_dir,
            name="train",
        )
        print("YOLO 학습 완료!")
        print(f"학습 경로: {train_results.save_dir}")

        print("검증 시작...")
        valid_results = model.val(name="valid")
        print("검증 완료!")

        # 검증 메트릭을 JSON 파일로 저장
        print("검증 메트릭 저장 중...")
        metrics_path = valid_results.save_dir / "validation_metrics.json"

        # 메트릭 데이터를 JSON으로 변환 가능한 형태로 변환
        metrics_dict = {
            "box": {
                "mAP50": float(valid_results.box.map50),
                "mAP50-95": float(valid_results.box.map),
            },
            "speed": {
                "preprocess": float(valid_results.speed["preprocess"]),
                "inference": float(valid_results.speed["inference"]),
                "loss": float(valid_results.speed["loss"]),
            },
        }

        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics_dict, f, indent=4)

        print(f"검증 메트릭이 {metrics_path}에 저장되었습니다.")

        print("모델 저장 시작...")
        model.save(valid_results.save_dir / "model.pt")
        print("모델 저장 완료!")

        return str(valid_results.save_dir)
    except Exception as e:
        raise e


def create_data_yaml(train_path: str, val_path: str, test_path: str, dataset_cfg_url: str, output_path: str) -> str:
    """YOLO 학습에 필요한 data.yaml 파일을 생성합니다.

    Args:
        train_path: 학습 데이터 경로
        val_path: 검증 데이터 경로
        test_path: 테스트 데이터 경로
        num_classes: 클래스 수
        output_path: data.yaml 파일을 저장할 경로

    Returns:
        str: 생성된 data.yaml 파일 경로
    """
    # 절대 경로로 변경
    train_path = Path(train_path).absolute()
    val_path = Path(val_path).absolute()
    test_path = Path(test_path).absolute()

    # 데이터셋 설정 YAML 파일 다운로드
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(dataset_cfg_url, stream=True, timeout=10)
    response.raise_for_status()
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response.text)

    data = yaml.safe_load(open(output_path, "r", encoding="utf-8"))
    data["path"] = str(Path(train_path).parent)
    data["train"] = str(Path(train_path).relative_to(Path(train_path).parent))
    data["val"] = str(Path(val_path).relative_to(Path(train_path).parent))
    data["test"] = str(Path(test_path).relative_to(Path(train_path).parent))

    # data.yaml 파일 저장
    yaml_path = Path(output_path)
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False)

    return str(yaml_path)


if __name__ == "__main__":
    create_data_yaml(
        train_path="./data/splits/train",
        val_path="./data/splits/val",
        test_path="./data/splits/test",
        dataset_cfg_url="https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/cfg/datasets/coco128.yaml",
        output_path="./data/splits/data.yaml",
    )

    train_yolo(
        data_yaml_path="./data/splits/data.yaml",
        output_dir="./runs",
        epochs=1,
    )

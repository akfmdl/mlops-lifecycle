#!/usr/bin/env python3
import argparse
import json
import shutil
import sys
from pathlib import Path

from ultralytics import YOLO


def train_yolo(data_yaml_path, output_dir, metrics_file_path, best_model_path, epochs=10, batch_size=16, img_size=640):
    """YOLO 모델 학습"""
    print(f"YOLO 학습 시작: {data_yaml_path}")

    data_yaml_path = Path(data_yaml_path)
    output_dir = Path(output_dir)

    # 경로 존재 확인
    if not data_yaml_path.exists():
        raise ValueError(f"YAML 파일이 존재하지 않습니다: {data_yaml_path}")

    # 출력 디렉토리 생성
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 모델 로드
        print("YOLO 모델 로드 중...")
        model = YOLO("yolo11n.pt")

        # 학습 실행
        print(f"학습 시작 (에포크: {epochs}, 배치 크기: {batch_size}, 이미지 크기: {img_size})...")
        train_results = model.train(
            data=str(data_yaml_path),
            epochs=epochs,
            batch=batch_size,
            imgsz=img_size,
            project=str(output_dir),
            name="train",
            exist_ok=True,
        )

        # 학습 결과 저장 경로
        save_dir = Path(train_results.save_dir)
        print(f"학습 완료: {save_dir}")

        # 모델 검증
        print("모델 검증 중...")
        val_results = model.val(name="valid", exist_ok=True)

        metrics = {
            "mAP50": round(float(val_results.box.map50), 4),
            "mAP50-95": round(float(val_results.box.map), 4),
        }

        with open(metrics_file_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)

        print(f"검증 완료: {metrics}")

        # 모델 저장
        if best_model_path.exists():
            print(f"모델 저장 완료: {best_model_path}")
        else:
            model_files = list(save_dir.glob("best.pt"))
            if model_files:
                shutil.copy(model_files[0], best_model_path)
                print(f"모델 저장 완료: {model_files[0]}")
            else:
                print("모델 파일을 찾을 수 없습니다.")

        return str(save_dir)

    except Exception as e:
        print(f"학습 중 오류 발생: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YOLO 모델 학습")
    parser.add_argument(
        "--data_yaml_path", type=str, help="데이터 YAML 파일 경로", default="/tmp/airflow/data/splits/data.yaml"
    )
    parser.add_argument("--output_dir", type=str, help="출력 디렉토리 경로", default="/tmp/airflow/data/runs")
    parser.add_argument(
        "--metrics_file_path",
        type=str,
        help="검증 결과 저장 파일 경로",
        default="/tmp/airflow/data/runs/valid/metrics.json",
    )
    parser.add_argument(
        "--best_model_path",
        type=str,
        help="Best 모델 저장 파일 경로",
        default="/tmp/airflow/data/runs/weights/best.pt",
    )
    parser.add_argument("--epochs", type=int, default=1, help="학습 에포크 수")
    parser.add_argument("--batch_size", type=int, default=16, help="배치 크기")
    parser.add_argument("--img_size", type=int, default=640, help="이미지 크기")

    args = parser.parse_args()

    try:
        result_dir = train_yolo(args.data_yaml_path, args.output_dir, args.epochs, args.batch_size, args.img_size)
        print(f"XCOM_RETURN:{result_dir}")
    except Exception as e:
        print(f"학습 실패: {e}")
        sys.exit(1)

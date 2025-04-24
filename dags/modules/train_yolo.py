#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urljoin

import mlflow
import requests
import yaml
from ultralytics import YOLO, settings

MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
os.environ["MLFLOW_KEEP_RUN_ACTIVE"] = "true"


class YOLOModel:
    def __init__(self, experiment_name="yolo", run_name="yolo11n", model_path="yolo11n.pt"):
        print("YOLO 모델 로드 중...")
        self.model = YOLO(model_path)
        self.run_name = run_name
        self.experiment_name = experiment_name
        self.model_path = model_path
        self.mlflow_enabled = True

        try:
            # 서버 상태 확인 (health check)
            health_url = urljoin(MLFLOW_TRACKING_URI, "health")
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
                print(f"mlflow artifact uri: {mlflow.get_artifact_uri()}")
                mlflow.set_experiment(experiment_name)
                mlflow.start_run(run_name=self.run_name, nested=True)
                settings.update({"mlflow": True})
            else:
                raise ConnectionError(f"MLflow 서버 응답 오류: {response.status_code}")
        except (requests.RequestException, ConnectionError) as e:
            print(f"[경고] MLflow 연결 실패: {e}\nMLflow 기능 비활성화 상태로 진행합니다.")
            self.mlflow_enabled = False
            settings.update({"mlflow": False})

    def log_dataset_info(self, data_yaml_path):
        if not self.mlflow_enabled:
            print("MLflow 기능이 비활성화되어 데이터셋 정보를 로깅할 수 없습니다.")
            return

        with open(data_yaml_path, "r", encoding="utf-8") as f:
            data_config = yaml.safe_load(f)

        dataset_info = {
            "dataset_path": data_config.get("path", "unknown"),
            "train_path": data_config.get("train", "unknown"),
            "val_path": data_config.get("val", "unknown"),
            "test_path": data_config.get("test", "unknown"),
            "num_classes": len(data_config.get("names", {})),
            "class_names": list(data_config.get("names", {}).values()),
        }

        mlflow.log_param("dataset_path", dataset_info["dataset_path"])
        mlflow.log_param("train_path", dataset_info["train_path"])
        mlflow.log_param("val_path", dataset_info["val_path"])
        mlflow.log_param("test_path", dataset_info["test_path"])
        mlflow.log_param("num_classes", dataset_info["num_classes"])
        mlflow.log_param("class_names", json.dumps(dataset_info["class_names"]))

    def train(self, data_yaml_path, epochs=10, batch_size=16, img_size=640):
        print(f"학습 시작 (Epochs: {epochs}, Batch Size: {batch_size}, Img Size: {img_size})...")

        if not Path(data_yaml_path).exists():
            raise ValueError(f"YAML 파일이 존재하지 않습니다: {data_yaml_path}")

        self.log_dataset_info(data_yaml_path)

        train_results = self.model.train(
            data=data_yaml_path,
            epochs=epochs,
            batch=batch_size,
            imgsz=img_size,
            exist_ok=True,
            project=self.experiment_name,
            name=self.run_name,
        )
        return train_results

    def validate(self):
        if not self.mlflow_enabled:
            print("MLflow 기능이 비활성화되어 모델 검증을 건너뜁니다.")
            return

        valid_results = self.model.val(exist_ok=True, name=self.run_name)

        # 모델 성능 메트릭 로깅
        mlflow.log_metric("mAP50-95", valid_results.box.map)
        mlflow.log_metric("inference_speed", valid_results.speed["inference"])

        return valid_results

    def register_model(self, valid_results, force_register):
        if not self.mlflow_enabled:
            print("MLflow 기능이 비활성화되어 모델 등록을 건너뜁니다.")
            return False

        # 현재 모델의 성능 메트릭 가져오기
        current_map = valid_results.box.map
        current_inference_speed = valid_results.speed["inference"]

        client = mlflow.tracking.MlflowClient()

        try:
            registered_model = client.get_registered_model(self.run_name)
            latest_run = client.get_run(registered_model.latest_versions[0].run_id)
            previous_map = latest_run.data.metrics.get("mAP50-95", 0)
            previous_inference_speed = latest_run.data.metrics.get("inference_speed", 0)
        except mlflow.exceptions.RestException:
            # 모델이 레지스트리에 없는 경우
            previous_map = 0
            previous_inference_speed = 0

        # 성능이 향상된 경우에만 모델 등록
        if force_register.lower() == "true":
            print("force_register 옵션이 활성화되어 모델을 강제 등록합니다.")
        elif current_map > previous_map and current_inference_speed > previous_inference_speed:
            print(
                f"모델 성능 향상 확인 - mAP50-95: {previous_map:.3f} -> {current_map:.3f}, "
                f"추론 속도: {previous_inference_speed:.3f} -> {current_inference_speed:.3f}"
            )
        else:
            print("현재 모델의 성능이 이전 모델보다 낮아 등록을 건너뜁니다.")
            return False

        # ONNX 형식으로 모델 내보내기
        onnx_path = self.model.export(format="onnx", dynamic=True)

        # 현재 실행 중인 MLflow run에 아티팩트로 모델 저장
        mlflow.log_artifact(local_path=onnx_path)

        # Model Registry에 모델 등록 또는 업데이트
        mlflow.register_model(f"runs:/{mlflow.active_run().info.run_id}/{os.path.basename(onnx_path)}", self.run_name)
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YOLO 모델 학습")
    parser.add_argument(
        "--data_yaml_path", type=str, help="데이터 YAML 파일 경로", default="/tmp/airflow/data/splits/data.yaml"
    )
    parser.add_argument("--epochs", type=int, default=1, help="학습 에포크 수")
    parser.add_argument("--batch_size", type=int, default=16, help="배치 크기")
    parser.add_argument("--img_size", type=int, default=640, help="이미지 크기")
    parser.add_argument("--run_name", type=str, default="yolo11n", help="mlflow run name & model name")
    parser.add_argument("--force_register", type=str, default="False", help="모델 강제 등록 여부")

    args = parser.parse_args()

    try:
        yolo_model = YOLOModel()
        train_results = yolo_model.train(
            data_yaml_path=args.data_yaml_path,
            epochs=args.epochs,
            batch_size=args.batch_size,
            img_size=args.img_size,
        )
        valid_results = yolo_model.validate()
        is_registered = yolo_model.register_model(valid_results, args.force_register)
        mlflow.end_run()
        print(f"XCOM_RETURN:{is_registered}")
    except Exception as e:
        print(f"학습 실패: {e}")
        sys.exit(1)

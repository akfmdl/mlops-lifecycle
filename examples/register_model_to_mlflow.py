#!/usr/bin/env python
import argparse
import os
import time
from pathlib import Path

import mlflow


def register_model(model_path, model_name, run_name=None, description=None):
    """
    모델을 MLflow 레지스트리에 등록합니다.

    Args:
        model_path: 모델 파일 경로
        model_name: 레지스트리에 등록할 모델 이름
        run_name: MLflow 실행 이름 (기본값: 모델 이름 + 타임스탬프)
        description: 모델 설명

    Returns:
        등록된 모델의 버전 정보
    """
    model_path = Path(model_path)

    # MLflow 서버 URI 설정
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    mlflow.set_tracking_uri(tracking_uri)
    print(f"MLflow 트래킹 서버: {tracking_uri}")

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    default_run_name = f"{model_name}-{timestamp}"

    # 모델 정보 추출
    model_size = model_path.stat().st_size / (1024 * 1024)  # MB 단위

    # 추가 메타데이터
    tags = {
        "model_size_mb": f"{model_size:.2f}",
        "registered_by": os.getenv("USER", "unknown"),
    }

    # MLflow에 모델 로깅
    with mlflow.start_run(run_name=run_name or default_run_name) as run:
        run_id = run.info.run_id
        print(f"MLflow 실행 ID: {run_id}")

        # 파라미터 로깅
        mlflow.log_params(
            {"model_name": model_name, "model_path": str(model_path), "model_size_mb": f"{model_size:.2f}"}
        )

        # 태그 설정
        for key, value in tags.items():
            mlflow.set_tag(key, value)

        # 모델 파일 로깅
        mlflow.log_artifact(model_path)

        # 모델 등록
        model_uri = f"runs:/{run_id}/{model_path.name}"
        model_details = mlflow.register_model(model_uri, model_name)

        print(f"✅ 모델이 성공적으로 등록되었습니다: {model_name} (버전 {model_details.version})")

        # 모델 설명 추가
        if description:
            client = mlflow.tracking.MlflowClient()
            client.update_registered_model(model_name, description=description)

        return model_details


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="모델을 MLflow 레지스트리에 등록합니다")
    parser.add_argument("--model-path", type=str, default="yolo11n.onnx", help="모델 파일 경로")
    parser.add_argument("--model-name", type=str, default="onnx-model", help="레지스트리에 등록할 모델 이름")
    parser.add_argument("--run-name", type=str, help="MLflow 실행 이름. 빈 문자열이면 모델 이름 + 타임스탬프로 설정됨")
    parser.add_argument("--description", type=str, help="모델 설명")

    args = parser.parse_args()

    register_model(args.model_path, args.model_name, args.run_name, args.description)

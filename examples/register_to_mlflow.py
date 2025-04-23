#!/usr/bin/env python
import argparse
import os
import time
from pathlib import Path

import mlflow
import onnx


def validate_onnx_model(onnx_model_path):
    """ONNX 모델이 유효한지 검증합니다."""
    try:
        model = onnx.load(onnx_model_path)
        onnx.checker.check_model(model)
        print(f"✅ ONNX 모델 검증 성공: {onnx_model_path}")

        # 모델 정보 출력
        inputs = [input.name for input in model.graph.input]
        outputs = [output.name for output in model.graph.output]
        print(f"모델 입력: {inputs}")
        print(f"모델 출력: {outputs}")

        return model
    except Exception as e:
        print(f"❌ ONNX 모델 검증 실패: {str(e)}")
        return None


def register_model(onnx_model_path, model_name, run_name=None, description=None):
    """
    ONNX 모델을 MLflow 레지스트리에 등록합니다.

    Args:
        onnx_model_path: ONNX 모델 파일 경로
        model_name: 레지스트리에 등록할 모델 이름
        run_name: MLflow 실행 이름 (기본값: 모델 이름 + 타임스탬프)
        description: 모델 설명

    Returns:
        등록된 모델의 버전 정보
    """
    onnx_model_path = Path(onnx_model_path)

    # ONNX 모델 검증
    model = validate_onnx_model(onnx_model_path)
    if model is None:
        return None

    # MLflow 서버 URI 설정
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    mlflow.set_tracking_uri(tracking_uri)
    print(f"MLflow 트래킹 서버: {tracking_uri}")

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    default_run_name = f"{model_name}-{timestamp}"

    # 모델 정보 추출
    model_size = onnx_model_path.stat().st_size / (1024 * 1024)  # MB 단위
    input_shapes = {
        i.name: [d.dim_value if d.dim_value else -1 for d in i.type.tensor_type.shape.dim] for i in model.graph.input
    }
    output_shapes = {
        o.name: [d.dim_value if d.dim_value else -1 for d in o.type.tensor_type.shape.dim] for o in model.graph.output
    }

    # 추가 메타데이터
    tags = {
        "model_type": "onnx",
        "model_size_mb": f"{model_size:.2f}",
        "framework": "ONNX",
        "inputs": str(input_shapes),
        "outputs": str(output_shapes),
        "registered_by": os.getenv("USER", "unknown"),
    }

    # MLflow에 모델 로깅
    with mlflow.start_run(run_name=run_name or default_run_name) as run:
        run_id = run.info.run_id
        print(f"MLflow 실행 ID: {run_id}")

        # 파라미터 로깅
        mlflow.log_params(
            {"model_name": model_name, "model_path": str(onnx_model_path), "model_size_mb": f"{model_size:.2f}"}
        )

        # 태그 설정
        for key, value in tags.items():
            mlflow.set_tag(key, value)

        # 모델 파일 로깅
        mlflow.log_artifact(onnx_model_path)

        # 모델 등록
        model_uri = f"runs:/{run_id}/{onnx_model_path.name}"
        model_details = mlflow.register_model(model_uri, model_name)

        print(f"✅ 모델이 성공적으로 등록되었습니다: {model_name} (버전 {model_details.version})")

        # 모델 설명 추가
        if description:
            client = mlflow.tracking.MlflowClient()
            client.update_registered_model(model_name, description=description)

        return model_details


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ONNX 모델을 MLflow 레지스트리에 등록합니다")
    parser.add_argument("--onnx-model", type=str, default="yolo11n.onnx", help="ONNX 모델 파일 경로")
    parser.add_argument("--model-name", type=str, default="yolo11n", help="레지스트리에 등록할 모델 이름")
    parser.add_argument("--run-name", type=str, help="MLflow 실행 이름")
    parser.add_argument("--description", type=str, help="모델 설명")

    args = parser.parse_args()

    register_model(args.onnx_model, args.model_name, args.run_name, args.description)

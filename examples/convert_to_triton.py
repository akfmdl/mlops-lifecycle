#!/usr/bin/env python
import argparse
import shutil
from pathlib import Path


def create_triton_model_repo(onnx_path, output_dir, model_name="yolov11n", model_version="1"):
    onnx_path = Path(onnx_path)
    model_repo_path = Path(output_dir) / model_name
    version_path = model_repo_path / model_version

    # 디렉토리 생성
    version_path.mkdir(parents=True, exist_ok=True)

    # ONNX 모델 복사
    shutil.copy(onnx_path, version_path / "model.onnx")

    # config.pbtxt 생성
    config_text = f"""
name: "{model_name}"
backend: "onnxruntime"
max_batch_size: 1

input [
  {{
    name: "images"
    data_type: TYPE_FP32
    dims: [3, -1, -1]
  }}
]

output [
  {{
    name: "output0"
    data_type: TYPE_FP32
    dims: [84, -1]
  }}
]
"""
    with open(model_repo_path / "config.pbtxt", "w", encoding="utf-8") as f:
        f.write(config_text.strip())

    print(f"Triton model repository created at: {model_repo_path.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert ONNX model to Triton Inference Server format")
    parser.add_argument("--onnx_model", type=str, default="yolo11n.onnx", help="Path to the ONNX model file")
    parser.add_argument("--output_dir", type=str, default="./model_repository", help="Path to the output directory")
    parser.add_argument("--model_name", type=str, default="yolo11n", help="Name of the model in Triton")
    parser.add_argument("--model_version", type=str, default="1", help="Version of the model")

    args = parser.parse_args()

    create_triton_model_repo(args.onnx_model, args.output_dir, args.model_name, args.model_version)

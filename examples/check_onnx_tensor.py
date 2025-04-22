import argparse

import onnxruntime


def check_onnx_tensor(model_path):
    # 세션 생성
    session = onnxruntime.InferenceSession(model_path, providers=["CPUExecutionProvider"])

    # 입력 정보 확인
    print("🔹 Inputs:")
    for input_tensor in session.get_inputs():
        print(f"  name: {input_tensor.name}")
        print(f"  shape: {input_tensor.shape}")
        print(f"  type: {input_tensor.type}")

    # 출력 정보 확인
    print("\n🔹 Outputs:")
    for output_tensor in session.get_outputs():
        print(f"  name: {output_tensor.name}")
        print(f"  shape: {output_tensor.shape}")
        print(f"  type: {output_tensor.type}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ONNX 모델의 입력/출력 텐서 정보 확인")
    parser.add_argument("--model_path", type=str, default="yolo11n.onnx", help="ONNX 모델 파일 경로")
    args = parser.parse_args()
    check_onnx_tensor(args.model_path)

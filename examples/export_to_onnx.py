# pip install ultralytics
import argparse

from ultralytics import YOLO


def main(args):
    model = YOLO(args.model_path)
    model_path = model.export(format="onnx", dynamic=True)
    print(f"✅ ONNX 모델이 ./{model_path}에 저장되었습니다.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=str, default="yolo11n.pt")
    args = parser.parse_args()

    main(args)

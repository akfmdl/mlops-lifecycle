# pip install ultralytics
import argparse

from ultralytics import YOLO


def main(args):
    model = YOLO(args.model_path)
    model_path = model.export(format=args.format, dynamic=True, int8=args.int8)
    print(f"✅ {args.format} 모델이 ./{model_path}에 저장되었습니다.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=str, default="yolo11n.pt")
    parser.add_argument("--format", type=str, default="onnx", choices=["onnx", "engine"])
    parser.add_argument(
        "--int8",
        action="store_true",
        help="INT8 양자화 활성화. 모델을 더욱 압축하고 정확도 손실을 최소화하면서 추론 속도를 높임",
    )
    args = parser.parse_args()

    main(args)

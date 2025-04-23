# Triton Inference Server 사용 예제

## 1. Triton Inference Server 실행

임시 model_repository 폴더 생성
```bash
mkdir tmp_model_repository
```

컨테이너 실행
* goranidocker/tritonserver:python-v1: model_repository/Dockerfile을 빌드한 커스텀 이미지
* 기본 nvidia에서 제공하는 이미지는 https://catalog.ngc.nvidia.com/orgs/nvidia/containers/tritonserver/tags 참고

```bash
sudo docker run --gpus=all -it --shm-size=256m --network="host" --rm -p 8000:8000 -p 8001:8001 -p 8002:8002 -v $(pwd)/tmp_model_repository:/models goranidocker/tritonserver:python-v1
```

프로세스 실행
* --model-control-mode=poll: 모델 변경 시 자동으로 모델 로드
* --repository-poll-secs=3: 모델 변경 시 3초마다 모델 로드

```bash
tritonserver --model-repository=/models --model-control-mode=poll --repository-poll-secs=3
```

## 2. ONNX 백엔드 모델 배포 방법

ONNX 모델 파일 얻기
```bash
python3 examples/export_to_onnx.py --model-path yolo11n.pt
```

Triton 모델 레포지토리 생성. 정상적으로 완료되면 model_repository 폴더 내에 yolo11n 폴더가 생성됨. 그리고 Triton 컨테이너 내에서 자동으로 모델을 로드함
```bash
python3 examples/convert_to_triton.py --onnx-model yolo11n.onnx --output-dir tmp_model_repository --model-name yolo11n --model-version 1
```

모델 추론
```bash
python3 examples/triton_yolo_inference.py --model-name yolo11n --output-name output0 --output-image dog_detection.jpg
```

추론 결과 확인: dog_detection.jpg

## 3. Python 백엔드 모델 배포 방법

ONNX Runtime 백엔드를 사용할 경우, 전처리나 후처리 코드를 커스터마이징 할 수 없기 때문에 Python 백엔드를 사용해야 함.
기본 구조
* initialize: 모델 초기화(로드시 한번만 실행)
* execute: 모델 추론

mlflow 서버 실행
```bash
mlflow server --host 127.0.0.1 --port 5000
```

mlflow 모델 등록
```bash
export MLFLOW_TRACKING_URI=http://127.0.0.1:5000
python3 examples/register_to_mlflow.py --onnx-model yolo11n.onnx --model-name yolo11n
```

python 백엔드 모델 폴더 복사
```bash
cp -r model_repository/basic tmp_model_repository
```

모델 추론
```bash
python3 examples/triton_yolo_inference.py --model-name basic --output-name detections --output-image dog_detection.jpg
```

추론 결과 확인: dog_detection.jpg



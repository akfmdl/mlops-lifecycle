# Triton Inference Server Helm Chart
이 Helm Chart는 Triton Inference Server를 배포하기 위한 차트입니다.

## Prerequisites
- k3s 클러스터 설치
- helm 설치
- kubectl 설치
- docker 설치

## Repository Clone 및 Helm Chart 설치
이 레포의 charts/tritoninferenceserver 폴더에 있는 helm chart를 설치합니다.

```bash
git clone https://github.com/akfmdl/mlops-lifecycle.git
cd mlops-lifecycle
helm upgrade --install tritoninferenceserver charts/tritoninferenceserver --namespace mlops-platform --create-namespace
```

## 로컬에서 모델 추론해보기

### local에 mlflow 서버를 띄우기

mlops-lifecycle/model_repository/onnx-model 모델을 triton inference server로 배포하려면 먼저, mlflow 서버를 실행해야 합니다. 기본 포트는 5000입니다. 포트를 변경하고 싶으시면 아래 명령어에서 포트를 변경해주세요.
포트가 변경될 경우, 모든 명령어를 실행하는 터미널에 export MLFLOW_TRACKING_URI="http://localhost:<변경될 포트>" 명령어를 추가하신 후 실행해주세요.

```bash
export MLFLOW_TRACKING_URI="http://localhost:5000"
mlflow server --host 0.0.0.0 --port 5000
```

### mlflow 서버에 모델 등록

모델이 로컬에 없다면 다음 명령어로 모델을 다운받을 수 있습니다.

```bash
python examples/export_yolo.py --model-path yolo11n.pt --format onnx
```

모델을 mlflow 서버에 등록합니다.

```bash
python examples/register_model_to_mlflow.py --model-path yolo11n.onnx --model-name yolo11n-onnx
```

### triton 컨테이너 띄우기

* --network="host": 로컬에서 실행되고 있는 mlflow에 접근할 수 있도록 호스트 네트워크 사용   
* -v $(pwd)/model_repository:/models: 모델 레포지토리 마운트 -> model_repository 폴더는 이 레포지토리에 있습니다.
* -e MLFLOW_TRACKING_URI=$MLFLOW_TRACKING_URI: mlflow 서버의 주소를 환경변수로 전달
```bash
sudo docker run -it --network="host" --rm -v $(pwd)/model_repository:/models -e MLFLOW_TRACKING_URI=$MLFLOW_TRACKING_URI goranidocker/tritonserver:python-v1
```

### triton 컨테이너 내에서 서버 실행

triton 컨테이너 내에 들어왔으면 /models 폴더에 위에서 마운트한 model_repository 폴더 내에 있는 모델 폴더가 있는지 확인합니다.

```bash
ls /models
```

MLFLOW_TRACKING_URI 환경 변수가 제대로 주입되었는지 확인합니다.

```bash
echo $MLFLOW_TRACKING_URI
```

triton 서버를 실행합니다.

* TRITON_PORT: 30000-32767 범위 내에서 사용 가능한 포트 중 하나를 선택합니다. 이 포트는 k8s nodeport 포트 포함 모든 사용 중인 포트를 제외한 포트입니다.
* --model-repository=/models: 모델 레포지토리 경로
* --model-control-mode=poll: 모델 추론 서버가 모델 레포지토리를 주기적으로 폴링하도록 설정
* --repository-poll-secs=3: 3초마다 모델 레포지토리를 폴링
* --http-port=$TRITON_PORT: HTTP 포트 지정

```bash
TRITON_PORT=$(comm -23 <(seq 30000 32767 | sort) <(ss -Htan | awk '{print $4}' | cut -d':' -f2 | sort -u; kubectl get svc -A -o jsonpath='{.items[*].spec.ports[*].nodePort}' 2>/dev/null | tr ' ' '\n' | sort -u) | head -n 1)
tritonserver --model-repository=/models --model-control-mode=poll --repository-poll-secs=3 --http-port=$TRITON_PORT
```

위 명령어를 통해 triton server를 실행하면 [model.py](../../model_repository/onnx-model/1/model.py) 파일에서 initialize 함수에 명시한 것처럼 mlflow로부터 모델을 다운받고 컨테이너 내에 배포합니다.

```bash
0521 04:40:49.798415 327 model.py:17] "Initializing model..."
Downloading artifacts: 100%|█████████████████████████████████████████████████| 1/1 [00:00<00:00,  1.21it/s]
I0521 04:40:50.772720 327 model.py:35] "MLflow model loaded at /tmp/tmpzjugf7mi/best.onnx"
```

http service에 어떤 포트가 할당되었는지는 마지막 줄에 표시됩니다. 이 포트를 사용하여 추론합니다.

```bash
I0521 05:04:06.346963 552 http_server.cc:4755] "Started HTTPService at 0.0.0.0:<할당된 포트>"
```

### 추론해보기

가상환경 만들기

```bash
python3.12 -m venv venv
source venv/bin/activate
```

추론을 위한 패키지 설치

```bash
pip install -r examples/requirements.txt
```

위에서 확인한 http service의 포트를 사용하여 추론해봅니다. 새로운 터미널을 열고 다음 명령어를 입력합니다.

```bash
python3 examples/triton_yolo_inference.py --triton-url localhost:<할당된 포트> --model-name onnx-model --image-path examples/dog.jpg
```

### 추론 결과 확인

dog_detection.jpg 파일이 생성되었는지 확인합니다. 추론 후 Box 형태로 결과가 표시됩니다.

### model_repository 폴더에 있는 모델의 이름을 바꾸고 추론해보기

```bash
mv model_repository/onnx-model model_repository/python-model
```

triton 서버는 config.pbtxt 파일에 명시적으로 name을 지정해주지 않으면 폴더명을 모델명으로 인식합니다. 또한, 컨테이너 내에서 모델 레포지토리를 폴링하고 있기 때문에 기존 모델을 unload하고 자동으로 새로운 모델을 load합니다.

변경된 모델 이름으로 추론해보기

```bash
python examples/triton_yolo_inference.py --triton-url localhost:<할당된 포트> --model-name python-model --image-path examples/dog.jpg
```

복구하기

```bash
mv model_repository/python-model model_repository/onnx-model
```

mlflow 모델명을 바꾸고 추론해보기

동일한 모델 파일을 새로운 모델로 등록

```bash
python examples/register_model_to_mlflow.py --model-path yolo11n.onnx --model-name mymodel-onnx
```

model_repository/onnx-model/1/model.py 파일에서 모델 이름을 바꾸기

```python
MLFLOW_MODEL_NAME = os.getenv("MLFLOW_MODEL_NAME", "mymodel-onnx")
MLFLOW_MODEL_VERSION = os.getenv("MLFLOW_MODEL_VERSION", "1")
```

역시 triton 서버가 자동으로 모델을 unload하고 load합니다.

변경된 모델 이름으로 추론해보기

```bash
python examples/triton_yolo_inference.py --triton-url localhost:<할당된 포트> --model-name onnx-model --image-path examples/dog.jpg
```

## Kubernetes에서 모델 추론해보기

### triton 서버 배포

```bash
TRITON_SERVER_NAME="your_triton_server_name"
NAMESPACE="your_namespace"
helm upgrade --install $TRITON_SERVER_NAME charts/tritoninferenceserver --namespace $NAMESPACE --create-namespace
```

triton 서버는 NodePort 타입의 서비스로 생성되었습니다.

```bash
NODE_PORT=$(kubectl get svc -l release=$TRITON_SERVER_NAME -n $NAMESPACE -o jsonpath='{.items[0].spec.ports[0].nodePort}')
echo $NODE_PORT
echo "localhost:$NODE_PORT"
ENDPOINT="localhost:$NODE_PORT"
```
이제 triton 서버의 endpoint는 $ENDPOINT입니다.

### 추론해보기

```bash
python examples/triton_yolo_inference.py --triton-url $ENDPOINT --model-name onnx-model --image-path examples/dog.jpg
```

### 정리하기

```bash
helm uninstall $TRITON_SERVER_NAME -n $NAMESPACE
kubectl delete namespace $NAMESPACE
```

## Airflow를 통해 모델 배포 자동화 경험하기

dags폴더에 있는 k8s_dag는 모델을 학습 -> 새로운 모델을 mlflow에 등록 -> values.yaml에 등록 -> ArgoCD를 통해 triton 서버에 새로운 mlflow 모델 등록 까지 자동화 하는 파이프라인입니다. 직접 실행해보고 확인해보세요.

[Go to Airflow tutorial page](../../dags/README.md)

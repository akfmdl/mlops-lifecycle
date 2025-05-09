# Triton Inference Server Helm Chart
이 Helm Chart는 Triton Inference Server를 배포하기 위한 차트입니다.

## Prerequisites
- k3s 클러스터 설치
- helm 설치
- kubectl 설치
- docker 설치

## 튜토리얼

### 로컬에서 모델 추론해보기

local에 mlflow 서버를 띄워보고, 모델을 등록해보자.

1. mlflow 서버 띄우기

```bash
mlflow server --host 127.0.0.1 --port 5000
```

2. mlflow 서버에 모델 등록

모델이 로컬에 없다면 다음 명령어로 모델을 다운받을 수 있습니다.

```bash
python examples/export_yolo.py --model-path yolo11n.pt --format onnx
```

모델을 mlflow 서버에 등록합니다.

```bash
python examples/register_model_to_mlflow.py --model-path yolo11n.onnx --model-name yolo11n-onnx
```

3. triton 컨테이너 띄우기
* --network="host": 로컬에서 실행되고 있는 mlflow에 접근할 수 있도록 호스트 네트워크 사용   
* -v $(pwd)/model_repository:/models: 모델 레포지토리 마운트 -> model_repository 폴더는 이 레포지토리에 있습니다.

```bash
sudo docker run -it --network="host" --rm -p 8000:8000 -p 8001:8001 -p 8002:8002 -v $(pwd)/model_repository:/models goranidocker/tritonserver:python-v1
```

4. triton 컨테이너 내에서 서버 실행

* --model-control-mode=poll: 모델 추론 서버가 모델 레포지토리를 주기적으로 폴링하도록 설정
* --repository-poll-secs=3: 3초마다 모델 레포지토리를 폴링

```bash
tritonserver --model-repository=/models --model-control-mode=poll --repository-poll-secs=3
```

5. 추론해보기

```bash
python examples/triton_yolo_inference.py --triton-url localhost:8000 --model-name onnx-model --image-path examples/dog.jpg
```

6. 추론 결과 확인

dog_detection.jpg 파일이 생성되었는지 확인합니다.


7. model_repository 폴더에 있는 모델의 이름을 바꾸고 추론해보기

```bash
mv model_repository/onnx-model model_repository/python-model
```

triton 서버는 config.pbtxt 파일에 명시적으로 name을 지정해주지 않으면 폴더명을 모델명으로 인식합니다. 또한, 컨테이너 내에서 모델 레포지토리를 폴링하고 있기 때문에 기존 모델을 unload하고 자동으로 새로운 모델을 load합니다.

변경된 모델 이름으로 추론해보기

```bash
python examples/triton_yolo_inference.py --triton-url localhost:8000 --model-name python-model --image-path examples/dog.jpg
```

복구하기

```bash
mv model_repository/python-model model_repository/onnx-model
```

8. mlflow 모델명을 바꾸고 추론해보기

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
python examples/triton_yolo_inference.py --triton-url localhost:8000 --model-name onnx-model --image-path examples/dog.jpg
```

### Kubernetes에서 모델 추론해보기

1. Triton Inference Server 배포

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

추론해보기

```bash
python examples/triton_yolo_inference.py --triton-url $ENDPOINT --model-name onnx-model --image-path examples/dog.jpg
```

정리하기

```bash
helm uninstall $TRITON_SERVER_NAME -n $NAMESPACE
kubectl delete namespace $NAMESPACE
```

### Airflow를 통해 모델 배포 자동화 경험하기

dags폴더에 있는 k8s_dag는 모델을 학습 -> 새로운 모델을 mlflow에 등록 -> values.yaml에 등록 -> ArgoCD를 통해 triton 서버에 새로운 mlflow 모델 등록 까지 자동화 하는 파이프라인입니다. 직접 실행해보고 확인해보세요.

[Go to Airflow tutorial page](https://github.com/akfmdl/mlops-lifecycle/blob/main/charts/airflow/README.md)

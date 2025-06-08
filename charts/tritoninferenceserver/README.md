# Triton Inference Server Helm Chart
이 Helm Chart는 Triton Inference Server를 배포하기 위한 차트입니다.

## Prerequisites
- k3s 클러스터 설치
- helm 설치
- kubectl 설치
- docker 설치

## Repository Clone 및 Helm Chart 설치
이 레포의 charts/tritoninferenceserver 폴더에 있는 helm chart를 설치합니다.
이미 [argocd-apps/applicationset.yaml](../../argocd-apps/applicationset.yaml) 파일을 ArgoCD에 등록했다면 넘어가셔도 됩니다.

```bash
helm upgrade --install tritoninferenceserver charts/tritoninferenceserver --namespace mlops-platform --create-namespace
```

## 이 레포의 model_repository 설명

* onnx-model 모델: MLFlow로부터 모델을 다운받아 로드하고 추론합니다.
  * config.pbtxt 파일 설명
    ```
    backend: "python"  # Python backend를 사용하여 Python 코드로 유연하게 모델 서빙

    max_batch_size: 8  # 한 번에 처리할 수 있는 최대 배치 크기 (동시 추론 요청 최적화)

    input [
    {
        name: "images"             # 입력 텐서 이름 (추론 요청 시 사용할 키)
        data_type: TYPE_FP32       # 입력 데이터 타입 (32-bit float)
        dims: [3, 640, 640]        # 입력 텐서의 차원: (채널, 높이, 너비)
    }
    ]

    output [
    {
        name: "output0"            # 출력 텐서 이름
        data_type: TYPE_FP32       # 출력 데이터 타입 (32-bit float)
        dims: [-1, 6]              # 출력 차원: (N, 6), N은 가변 길이 (디텍션 결과 수)
                                # 각 row는 [x1, y1, x2, y2, confidence, class]
    }
    ]
    ```

## 로컬에서 모델 추론해보기

### mlflow 서버 실행

mlops-lifecycle/model_repository/onnx-model 모델은 MLFlow로부터 모델을 다운받아 저장합니다. [models.py](../../model_repository/onnx-model/1/model.py) 파일에서 initialize 함수에 명시한 것처럼 mlflow로부터 모델을 다운받고 컨테이너 내에 배포합니다. 그리고 MLFLOW_TRACKING_URI 환경변수를 통해 mlflow 서버에 접근합니다. 기본 값은 http://localhost:5000 입니다.

```python
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
```

따라서 triton inference server로 배포하려면 먼저, mlflow 서버를 실행해야 합니다.

만약 Host에서 mlflow cli를 이용하여 프로세스로 실행하려면 다음 명령어를 실행합니다.
```bash
mlflow server --host 0.0.0.0 --port 5000
```

포트가 변경될 경우, 모든 명령어를 실행하는 터미널에 export MLFLOW_TRACKING_URI="http://localhost:<변경될 포트>" 명령어를 추가하신 후 실행해주세요.

```bash
export MLFLOW_TRACKING_URI="http://localhost:<변경될 포트>"
```

### mlflow 서버에 모델 등록

모델이 로컬에 없다면 다음 명령어로 모델을 다운받을 수 있습니다.
(examples 폴더 내에 있는 스크립트들은 mlflow 서버에 http://localhost:5000 주소로 접근합니다. 만약 다른 주소로 접근하고 싶다면 MLFLOW_TRACKING_URI 환경 변수를 변경해주세요.)

```bash
python examples/export_yolo.py --model-path yolo11n.pt --format onnx
```

모델을 mlflow 서버에 등록합니다.

```bash
python examples/register_model_to_mlflow.py --model-path yolo11n.onnx --model-name yolo11n-onnx
```

### triton 컨테이너 띄우기

* --network="host": 외부에서 실행되고 있는 mlflow에 접근할 수 있도록 호스트 네트워크 사용
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

triton server 실행
* --model-repository=/models: 모델 레포지토리 경로
* --model-control-mode=poll: 모델 추론 서버가 모델 레포지토리를 주기적으로 폴링하도록 설정
* --repository-poll-secs=3: 3초마다 모델 레포지토리를 폴링
* --http-port=8000: HTTP 포트 지정
* --allow-grpc=false: GRPC 서비스 비활성화
* --allow-metrics=false: Metrics 서비스 비활성화
```bash
tritonserver --model-repository=/models --model-control-mode=poll --repository-poll-secs=3 --http-port=8000 --allow-grpc=false --allow-metrics=false
```

위 명령어를 통해 triton server를 실행하면 [model.py](../../model_repository/onnx-model/1/model.py) 파일에서 initialize 함수에 명시한 것처럼 mlflow로부터 모델을 다운받고 컨테이너 내에 배포합니다.

```bash
0521 04:40:49.798415 327 model.py:17] "Initializing model..."
Downloading artifacts: 100%|█████████████████████████████████████████████████| 1/1 [00:00<00:00,  1.21it/s]
I0521 04:40:50.772720 327 model.py:35] "MLflow model loaded at /tmp/tmpzjugf7mi/best.onnx"
```

http service에 어떤 포트가 할당되었는지는 마지막 줄에 표시됩니다. 이 포트를 사용하여 추론합니다.

```bash
I0521 05:04:06.346963 552 http_server.cc:4755] "Started HTTPService at 0.0.0.0:8000"
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

--model-control-mode=poll 설정을 통해 triton 서버가 모델 레포지토리를 주기적으로 폴링하고 있기 때문에 모델 이름을 바꾸면 자동으로 모델을 unload하고 load합니다.
실제로도 그러한지 확인해봅니다.

```bash
mv model_repository/onnx-model model_repository/python-model
```

기존 onnx-model이 unload되고 python-model이 load됩니다.

```bash
I0522 01:36:44.378783 148 model_lifecycle.cc:636] "successfully unloaded 'onnx-model' version 1"
I0522 01:39:05.862312 148 model_lifecycle.cc:849] "successfully loaded 'python-model'"
```

triton 서버는 config.pbtxt 파일에 명시적으로 name을 지정해주지 않으면 `폴더명을 모델명으로 인식`합니다. 또한, 컨테이너 내에서 모델 레포지토리를 폴링하고 있기 때문에 기존 모델을 unload하고 자동으로 새로운 모델을 load합니다.

변경된 모델 이름으로 추론해보기: --model-name 인자를 onnx-model 대신 python-model로 지정합니다.

```bash
python examples/triton_yolo_inference.py --triton-url localhost:8000 --model-name python-model --image-path examples/dog.jpg
```

복구하기

```bash
mv model_repository/python-model model_repository/onnx-model
```

mlflow 모델명을 바꾸고 추론해보기

동일한 모델 파일을 새로운 모델로 등록하고 mlflow에서 모델이 잘 등록되었는 지 확인합니다.

```bash
python examples/register_model_to_mlflow.py --model-path yolo11n.onnx --model-name mymodel-onnx
```

model_repository/onnx-model/1/model.py 파일에서 모델 이름을 직접 바꾸거나

```python
MLFLOW_MODEL_NAME = os.getenv("MLFLOW_MODEL_NAME", "mymodel-onnx")
MLFLOW_MODEL_VERSION = os.getenv("MLFLOW_MODEL_VERSION", "1")
```

triton 컨테이너 내에서 MLFLOW_MODEL_NAME 환경 변수를 통해 모델 이름을 바꿀 수 있습니다.

```bash
export MLFLOW_MODEL_NAME="mymodel-onnx"
```

역시 triton 서버가 자동으로 모델을 unload하고 load합니다.

```bash
I0521 05:14:15.013902 1106 model.py:17] "Initializing model mymodel-onnx version 1..."
```

변경된 모델 이름으로 추론해봅니다. --model-name 인자는 mlflow의 모델 이름이 아니라 triton 서버에 등록된 모델 이름(디렉토리명)이니 헷갈리지 않도록 주의합니다.

```bash
python examples/triton_yolo_inference.py --triton-url localhost:8000 --model-name onnx-model --image-path examples/dog.jpg
```

### 정리하기
triton 컨테이너 내에서 `ctrl + C` 키를 눌러 triton 서버를 종료한 뒤, `ctrl + D` 키를 눌러 컨테이너를 종료합니다.
mlflow 프로세스를 종료한 뒤 관련 폴더를 삭제해주세요.
```bash
rm -rf mlruns mlartifacts
```

## Kubernetes에서 모델 추론해보기

### triton 서버 배포

triton helm chart를 배포하기 전 변수들을 지정합니다.
* TRITON_SERVER_NAME: triton 서버의 이름
* NAMESPACE: triton 서버의 namespace
```bash
TRITON_SERVER_NAME="your_triton_server_name"
NAMESPACE="your_namespace"
```

triton 서버를 helm chart로 직접 배포합니다.
* charts/tritoninferenceserver: [charts/tritoninferenceserver/values.yaml](../../charts/tritoninferenceserver/values.yaml) 파일을 통해 이 레포의 [model_repository/onnx-model](../../model_repository/onnx-model) 폴더에 있는 모델을 배포합니다. gitSync를 사용해서 model_repository 폴더를 triton 서버에 동기화 합니다.
```bash
helm upgrade --install $TRITON_SERVER_NAME charts/tritoninferenceserver --namespace $NAMESPACE --create-namespace
```

triton 서버는 NodePort 타입의 서비스로 생성되었습니다. 어떤 포트로 할당되었는지 확인합니다.
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

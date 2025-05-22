# api-server Helm Chart
이 Helm Chart는 mlops-platform에 배포될 api server를 제공합니다.

## Prerequisites
- mlops-platform helm chart 설치
- triton inference server helm chart 설치
- api server helm chart 설치(kubectl apply -f argocd-apps/applicationset.yaml 를 실행하면 ArgoCD에서 자동으로 설치됨)

## Repository Clone 및 Helm Chart 설치
이 레포의 charts/api-server 폴더에 있는 helm chart를 설치합니다.

```bash
git clone https://github.com/akfmdl/mlops-lifecycle.git
cd mlops-lifecycle
helm upgrade --install api-server charts/api-server --namespace mlops-platform --create-namespace
```

## 튜토리얼

### 로컬에서 API 서버 실행해보기

필수 패키지 설치

```bash
pip install -r apis/requirements.txt
```

로컬에서 FastAPI를 실행하고 /predict 라우터를 Test해보려면 로컬에 triton inference server를 실행해야 합니다.

[triton inference server 실행](../tritoninferenceserver/README.md) 을 참고해서 로컬에서 mlflow 실행 및 onnx-model 모델을 서빙해주시기 바랍니다.

apis/config.py 파일에는 ONNX_MODEL_TRITON_URL의 기본 주소가 localhost:8000 으로 설정되어 있습니다. 그리고 apis/mlmodels/router.py 파일에서 이 주소를 사용하여 triton inference server에 접근합니다. onnx model이 8000 포트로 실행되고 있지 않을 경우 변경해야 합니다.

```bash
class Config(BaseSettings):
    ONNX_MODEL_TRITON_URL: str = os.getenv("ONNX_MODEL_TRITON_URL", "localhost:<TRITON_PORT>")
```

혹은 ONNX_MODEL_TRITON_URL 환경변수를 지정합니다.

```bash
export ONNX_MODEL_TRITON_URL="localhost:<TRITON_PORT>"
```

FastAPI를 실행하기 전에 PORT를 지정해줍니다.
* SERVICE_PORT: 30000-32767 범위 내에서 사용 가능한 포트 중 하나를 선택합니다. 이 포트는 k8s nodeport 포트 포함 모든 사용 중인 포트를 제외한 포트입니다.

```bash
export SERVICE_PORT=30000
while [ $SERVICE_PORT -le 32767 ]; do
    if ! timeout 1 bash -c ">/dev/tcp/localhost/$SERVICE_PORT" 2>/dev/null && ! kubectl get svc -A -o jsonpath='{.items[*].spec.ports[*].nodePort}' 2>/dev/null | grep -q "$SERVICE_PORT"; then
        break
    fi
    SERVICE_PORT=$((SERVICE_PORT + 1))
done
export SERVICE_PORT=$SERVICE_PORT
```

어떤 포트로 할당될지 확인합니다.
```bash
echo $SERVICE_PORT
```

Cloud VM에서 실행할경우, host name을 localhost대신 public ip로 지정해주어야 합니다.
```bash
export SERVICE_HOST=$(curl -s ifconfig.me)
```

FastAPI를 실행합니다.

```bash
cd apis
uvicorn main:app --host $SERVICE_HOST --port $SERVICE_PORT
```

http://$SERVICE_HOST:$SERVICE_PORT/docs 에 접속하시면 Swagger UI를 확인할 수 있습니다.

/onnx-model/predict 라우터는 image_url 파라미터를 받아서 이미지를 다운로드 받고, triton inference server에 추론 요청을 보냅니다. 추론 결과는 이미지 파일로 저장된 후, FastAPI 서버의 static url로 접근할 수 있도록 반환합니다.

예시: result_image_url를 클릭해서 결과 이미지를 확인할 수 있습니다.
```bash
{
  "result_image_url": "http://$SERVICE_HOST:$SERVICE_PORT/static/6b7b8d8e-cbd7-4a87-bcb4-0c946d17baea.jpg"
}
```

### Kubernetes에서 API 서버 실행해보기

[charts/api-server](../api-server/README.md) 및 [charts/tritoninferenceserver](../tritoninferenceserver/README.md) helm chart를 설치합니다.

api server의 NodePort를 확인합니다.

```bash
NODE_PORT=$(kubectl get svc -n mlops-platform api-server -o jsonpath='{.spec.ports[0].nodePort}')
echo $NODE_PORT
echo "http://$SERVICE_HOST:$NODE_PORT"
```

http://$SERVICE_HOST:$NODE_PORT/docs 에 접속합니다.

동일하게 /onnx-model/predict 라우터를 테스트합니다. Kubernetes에서 api-server와 onnx-model pod의 로그를 확인해보며 진행 동작을 확인합니다.

### 심화

새로운 triton model을 배포하고 이를 사용하는 라우터를 추가해보세요.
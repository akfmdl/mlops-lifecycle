# mlops-platform Helm Chart
이 Helm Chart는 Triton Inference Server를 배포하기 위한 차트입니다.

## Prerequisites
- k3s 클러스터 설치
- helm 설치
- kubectl 설치

## Repository Clone 및 Helm Chart 설치
이 레포의 charts/tritoninferenceserver 폴더에 있는 helm chart를 설치합니다.
triton 서버를 kubernetes에 배포합니다.

```bash
git clone https://github.com/akfmdl/mlops-lifecycle.git
cd mlops-lifecycle
helm upgrade --install tritoninferenceserver charts/tritoninferenceserver --namespace mlops-platform --create-namespace
```

## Helm Chart 삭제
```bash
helm uninstall tritoninferenceserver -n mlops-platform
kubectl delete namespace mlops-platform
```
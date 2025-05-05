# api-server Helm Chart
이 Helm Chart는 mlops-platform에 배포될 api server를 제공합니다.

## Prerequisites
- mlops-platform helm chart 설치

## Repository Clone 및 Helm Chart 설치
이 레포의 charts/api-server 폴더에 있는 helm chart를 설치합니다.

```bash
git clone https://github.com/akfmdl/mlops-lifecycle.git
cd mlops-lifecycle
helm upgrade --install api-server charts/api-server --namespace mlops-platform --create-namespace
```

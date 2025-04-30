# mlops-platform Helm Chart
이 Helm Chart는 머신러닝 프로젝트의 전 과정을 자동화하기 위한 플랫폼을 제공합니다.

## Prerequisites
- k3s 클러스터 설치
- helm 설치
- kubectl 설치

## Repository Clone 및 Helm Chart 설치
이 레포의 charts/mlops-platform 폴더에 있는 helm chart를 설치합니다.
airflow, mlflow, prometheus, grafana, triton 등의 서비스를 kubernetes에 배포합니다.

```bash
git clone https://github.com/akfmdl/mlops-lifecycle.git
cd mlops-lifecycle
helm upgrade --install mlops-platform charts/mlops-platform --namespace mlops-platform --create-namespace
```

## Git config 관련 설정

### Github 토큰 생성
Airflow 및 Github actions에서 사용할 토큰을 생성합니다.
https://github.com/settings/tokens 에 접속하여 Personal access tokens (classic)을 생성합니다.

필요 권한:
- repo: 권한 전체

### k8s 시크릿 생성
- username: github 사용자 이름
- email: github 사용자 이메일
- token: 위에서 생성한 토큰

```bash
kubectl create secret generic github-credential \
  --from-literal=github_username=<github_username> \
  --from-literal=github_email=<github_email> \
  --from-literal=github_token=<github_token> \
  -n mlops-platform
```

## Helm Chart 삭제
```bash
helm uninstall mlops-platform -n mlops-platform
kubectl delete namespace mlops-platform
```

## airflow, mlflow, prometheus, grafana, triton 등의 서비스를 브라우저에서 접근해보기
mlops-platform 차트의 values.yaml 파일에서 일부 서비스들의 서비스 타입을 아래와 같이 NodePort로 설정해두었습니다.

```bash
    service:
      type: NodePort
```
참고로 이 NodePort는 쿠버네티스 클러스터 외부에서 접근할 수 있도록 하기 위한 서비스 타입인데, 사용 가능한 포트 번호를 자동으로 할당합니다.
또한, k3s의 경우 기본적으로 localhost:<NodePort>로 접근할 수 있도록 설정되어 있습니다.
k9s에서 각 서비스의 포트 번호를 확인하거나 kubectl get svc -n mlops-platform 명령어로 확인할 수 있습니다.
브라우저에서 http://localhost:<NodePort>로 접근해보면 각 서비스의 페이지를 확인할 수 있습니다.

## Airflow admin 비밀번호
초기 비밀번호는 admin입니다.
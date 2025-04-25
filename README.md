# mlops-lifecycle

이 레포지토리는 MLOps의 전체 라이프사이클을 자동화된 파이프라인으로 경험해볼 수 있도록 설계되어 있습니다. 
단순히 모델을 학습시키는 것에서 끝나는 것이 아니라, 실험 추적, 모델 배포, 모니터링까지 실제 현업에서 사용하는 MLOps 흐름을 직접 따라해볼 수 있도록 구성되어 있습니다.
MLOps가 왜 필요한지, 그리고 어떤 방식으로 머신러닝 프로젝트의 품질과 효율을 끌어올릴 수 있는지를 이 레포를 통해 직접 체험해볼 수 있습니다.
각 단계는 실제로 실무에서 필요한 작업들입니다.

1. 데이터 수집 및 전처리 자동화
2. 모델 학습 및 실험 관리
3. 모델 레지스트리에 등록
4. 배포 자동화
5. 운영 중 모델 모니터링 및 재학습

이 레포지토리는 다음과 같은 패키지를 사용합니다:

- [Airflow](https://airflow.apache.org/): 워크플로우 관리
- [MLFlow](https://mlflow.org/): 실험 관리
- [Prometheus](https://prometheus.io/): 모니터링
- [Grafana](https://grafana.com/): 모니터링 UI
- [Triton Inference Server](https://github.com/triton-inference-server/server): 실시간 추론을 위한 모델 배포

## Prerequisites
- Python 3.10+
- Kubernetes

## 아키텍처 확인 방법
Kubernetes는 주로 Linux 환경에서 사용되기 때문에, 이 튜토리얼은 Linux 환경(amd64)을 기준으로 작성되었습니다.
Windows 환경에서는 WSL2를 사용하여 Linux 환경을 구축할 수 있습니다.
for linux and mac
```bash
uname -m
```
* x86_64일 경우: amd64 -> 정상적으로 동작함
* arm64일 경우: aarch64 -> 정상적으로 동작하지 않을 수 있음
* 그 외 i686 또는 i386: 32비트이므로 동작하지 않을 수 있음

for windows
```bash
echo %PROCESSOR_ARCHITECTURE%
```
* AMD64일 경우: amd64 -> 정상적으로 동작함
* ARM64일 경우: aarch64 -> 정상적으로 동작하지 않을 수 있음
* 그 외: 32비트이므로 동작하지 않을 수 있음

## 한번에 설치하기
이 레포에는 k3s, kubectl, k9s, helm을 한번에 설치할 수 있는 스크립트가 있습니다.
```bash
./install.sh
```

## 각각 설치하기
### [k3s](https://k3s.io/): Lightweight Kubernetes
k3s는 가볍고 쉽게 설치할 수 있는 Kubernetes 클러스터입니다. 가볍지만 이 튜토리얼에서 사용하는 모든 기능을 지원합니다. 또한, 튜토리얼만 진행하기 때문에 단일 노드로만 구성합니다.

#### for linux
* --write-kubeconfig-mode 644: kubeconfig 파일의 권한을 644로 설정
* --default-runtime nvidia: GPU 사용 설정(GPU가 없는 경우 무시)
```bash
curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644 --default-runtime nvidia
```
확인
```bash
systemctl status k3s
```

KUBECONFIG 환경변수 설정
```bash
echo 'export KUBECONFIG=/etc/rancher/k3s/k3s.yaml' >> ~/.bashrc
source ~/.bashrc
```

#### for mac
https://coding-groot.tistory.com/236 참고


### [kubectl](https://kubernetes.io/docs/reference/kubectl/): Kubernetes CLI
kubectl은 쿠버네티스 클러스터에 리소스들을 배포/관리하기 위한 CLI 도구입니다.
k3s만 설치해도 kubectl을 사용할 수 있기 때문에 별도로 설치할 필요는 없습니다. 하지만 k3s가 아닌 다른 클러스터를 사용하는 경우 별도로 설치해야 합니다.

#### for linux
```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x ./kubectl
sudo mv ./kubectl /usr/local/bin/kubectl
```

#### for mac
```bash
brew install kubectl
```

확인
```bash
kubectl get nodes
```

### [k9s](https://k9scli.io/): Kubernetes CLI
k9s는 kubectl와 비슷한 도구이지만 더 편리한 인터페이스(UI)를 제공합니다.

#### for linux
```bash
K9S_VERSION=$(curl -s https://api.github.com/repos/derailed/k9s/releases/latest | grep -Po '"tag_name": "\K.*?(?=")')
curl -LO https://github.com/derailed/k9s/releases/download/$K9S_VERSION/k9s_Linux_amd64.tar.gz
tar -zxvf k9s_Linux_amd64.tar.gz
sudo mv k9s /usr/local/bin/
rm k9s_Linux_amd64.tar.gz
```
#### for mac
```bash
brew install k9s
```

### [helm](https://helm.sh/): Kubernetes Package Manager
helm은 Kubernetes 클러스터에 애플리케이션을 배포하기 위한 패키지 매니저입니다.

#### for linux
```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

#### for mac
```bash
brew install helm
```

### [옵션] Helm Chart 삭제
```bash
helm uninstall mlops-platform
kubectl delete namespace mlops-platform
```

### [옵션] Cluster 제거
cluster를 제거하면 설치된 모든 리소스들을 한번에 제거할 수 있습니다.

k3s-uninstall.sh 파일 위치 찾기
```bash
which k3s
```

k3s-uninstall.sh 파일은 위에서 찾은 경로와 같은 디렉토리에 있습니다.
```bash
sudo /usr/local/bin/k3s-uninstall.sh
```

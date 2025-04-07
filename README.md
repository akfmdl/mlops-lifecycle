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

- [DVC](https://dvc.org/): 데이터 버전 관리
- [Airflow](https://airflow.apache.org/): 워크플로우 관리
- [MLFlow](https://mlflow.org/): 실험 관리
- [Prometheus](https://prometheus.io/): 모니터링
- [Grafana](https://grafana.com/): 모니터링 UI
- [Triton Inference Server](https://github.com/triton-inference-server/server): 실시간 추론을 위한 모델 배포

## Prerequisites
- Python 3.10+
- Kubernetes

## Installation
이 튜토리얼은 k3s 클러스터를 사용합니다. 그 이유는 k8s보다 가볍고 쉽게 설치할 수 있기 때문입니다.
가볍지만 이 튜토리얼에서 사용하는 모든 기능을 지원합니다.
Kubernetes는 주로 Linux 환경에서 사용되기 때문에, 이 튜토리얼은 Linux 환경을 기준으로 작성되었습니다.

### [k3s](https://k3s.io/): Lightweight Kubernetes
* --write-kubeconfig-mode 644: kubeconfig 파일의 권한을 644로 설정
```bash
curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644
```

check k3s
```bash
k3s kubectl get nodes
```

### [kubectl](https://kubernetes.io/docs/reference/kubectl/): Kubernetes CLI
k3s만 설치해도 kubectl을 사용할 수 있기 때문에 별도로 설치할 필요는 없습니다. 하지만 k3s가 아닌 다른 클러스터를 사용하는 경우 별도로 설치해야 합니다.

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x ./kubectl
sudo mv ./kubectl /usr/local/bin/kubectl
```

### [k9s](https://k9scli.io/): Kubernetes CLI
```bash
K9S_VERSION=$(curl -s https://api.github.com/repos/derailed/k9s/releases/latest | grep -Po '"tag_name": "\K.*?(?=")')
curl -LO https://github.com/derailed/k9s/releases/download/$K9S_VERSION/k9s_Linux_amd64.tar.gz
tar -zxvf k9s_Linux_amd64.tar.gz
sudo mv k9s /usr/local/bin/
rm k9s_Linux_amd64.tar.gz
```
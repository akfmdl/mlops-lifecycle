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
https://github.com/settings/personal-access-tokens 에 접속하여 토큰을 생성합니다.

필요 권한:
- Read access to actions variables, metadata, and secrets
- Read and Write access to actions and code

### k8s 시크릿 생성
- username: github 사용자 이름
- email: github 사용자 이메일
- token: 위에서 생성한 토큰

```bash
kubectl create secret generic github-credential \
  --from-literal=username=<github_username> \
  --from-literal=email=<github_email> \
  --from-literal=token=<github_token> \
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

## GPU 사용 설정
이 차트는 GPU 사용 설정을 위한 nvidia-device-plugin을 포함하고 있습니다.
nvidia-device-plugin은 쿠버네티스 클러스터에 GPU를 사용할 수 있도록 하는 플러그인입니다.
PC에 GPU가 있고 학습을 더 빠르게 실행하고 싶으시면 이 차트의 values.yaml 파일에서 nvidia.enabled를 true로 설정해주세요.

```bash
nvidia:
  enabled: true
```

단, 아래와 같은 작업이 수행되어야 합니다.
1. 노드에 NVIDIA 드라이버가 설치되어 있어야 합니다.
2. nvidia-smi를 실행해봤을 때 GPU 정보가 잘 뜨는지 확인이 되어야 합니다.
3. Container runtime이 nvidia-container-runtime인지 확인해야 합니다.

    ```bash
    grep nvidia /var/lib/rancher/k3s/agent/etc/containerd/config.toml
    ```

    출력 결과
    ```bash
      default_runtime_name = "nvidia"
    [plugins.'io.containerd.cri.v1.runtime'.containerd.runtimes.'nvidia']
    [plugins.'io.containerd.cri.v1.runtime'.containerd.runtimes.'nvidia'.options]
      BinaryName = "/usr/bin/nvidia-container-runtime"
    ```

3번이 안되어있을 경우, nvidia 관련 패키지를 설치해주세요.

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit nvidia-container-runtime
```

k3s를 재시작 한 후 3번을 재확인합니다.
k3s는 자동으로 NVIDIA runtime을 containerd 설정에 추가합니다.
참고: https://docs.k3s.io/advanced#alternative-container-runtime-support

```bash
sudo systemctl restart k3s
```

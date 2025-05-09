# Airflow DAGs Setup Guide

## Prerequisites
- mlops-platform helm chart 설치
- airflow, tritoninferenceserver helm chart 설치(kubectl apply -f argocd-apps/applicationset.yaml 를 실행하면 ArgoCD에서 자동으로 설치됨)

## Local에서 DAG 실행해보기

DAG를 실행하기 위한 패키지 설치

```bash
pip install -r dags/requirements.txt
```

AIRFLOW_HOME 설정하기

AIRFLOW_HOME을 설정하지 않으면 기본적으로 ~/airflow 디렉토리에 설치됩니다.

각종 airflow 설정 파일들이 저장될 디렉토리를 생성합니다.
```bash
export AIRFLOW_HOME="$(pwd)/airflow"
mkdir -p $AIRFLOW_HOME
```

DAG 폴더 설정하기

Airflow에서 이 프로젝트의 DAG들을 인식하기 위해서는 심볼릭 링크(symbolic link)를 생성해야 합니다.
```bash
ln -s $(pwd)/dags $AIRFLOW_HOME/dags
```

심볼릭 링크가 제대로 생성되었는지 확인:
```bash
ls -la $AIRFLOW_HOME/dags
```

아래와 같이 출력되면 정상입니다.
```bash
./airflow/dags -> ../mlops-lifecycle/dags
```

Airflow 시작:
```bash
airflow standalone
```
위 명령어를 실행하면 다음과 같은 메시지가 출력됩니다.
초기 admin 비밀번호는 복사해놓으시고 web server에 접속시 사용합니다.
```bash
standalone | Airflow is ready
standalone | Login with username: admin  password: 초기 admin 비밀번호 <—— 복사해놓기!!
standalone | Airflow Standalone is for development purposes only. Do not use this in production!
```

- airflow standalone은 다음과 같은 작업을 포함합니다.
   - sqlite 기반의 메타데이터 DB 초기화
   - 유저 생성
   - 웹 서버 시작
   - 스케줄러 시작

- admin 비밀번호를 까먹었을 경우, $AIRFLOW_HOME/standalone_admin_password.txt 에서 확인 가능

airflow CLI를 사용하는 터미널에도 AIRFLOW_HOME 설정이 필요합니다.
```bash
export AIRFLOW_HOME="$(pwd)/airflow"
```

DAG 활성화(Airflow Web UI에서도 가능):
```bash
airflow dags unpause local_dag
```

DAG가 Airflow에 인식되는지 확인:
```bash
airflow dags list | grep local_dag
```

혹은 Airflow Web UI에서 DAG 목록 확인:
   - Airflow Web UI에 접속(Local 환경에서는 http://localhost:8080)
   - DAG 목록에서 `local_dag` 확인

mlfow 실행

이 프로젝트의 DAG 실행 시 mlflow 서버를 실행해야 합니다.

```bash
mlflow server --host 0.0.0.0 --port 5000
```

DAG 실행(Pause 상태인 경우, Queue에 넣어놓고 실행 안함)

- [방법 1] CLI를 이용한 방법
   ```bash
   airflow dags trigger local_dag
   ```

- [방법 2] Web UI를 이용한 방법
   - Airflow Web UI에 접속(Local 환경에서는 http://localhost:8080)
   - DAG 목록에서 `local_dag` 클릭
   - 실행할 태스크 클릭
   - 태스크 실행 버튼 클릭

- [방법 3] Python 파일을 이용한 방법
   ```bash
   python dags/local_dag.py
   ```

Airflow Web UI에서 태스크 실행과정을 확인해보시기 바랍니다.

MLFlow 서버에서 등록된 모델을 확인하시기 바랍니다.

## Kubernetes에서 DAG 실행해보기

Kubernetes에 배포된 Airflow 서비스의 NodePort를 확인합니다.

```bash
NODE_PORT=$(kubectl get svc -n mlops-platform airflow-webserver -o jsonpath='{.spec.ports[0].nodePort}')
echo $NODE_PORT
echo "http://localhost:$NODE_PORT"
```

Airflow Web UI에 접속하여 DAGs 목록에서 k8s_dag 확인 및 Trigger 버튼 클릭, 태스크 실행 확인
- id: admin, password: admin

k9s를 이용하여 Kubernetes cluster에서 실행되는 k8s_dag의 각 Task pod들이 어떻게 동작하는지 확인해보시기 바랍니다.

airflow helm chart는 아래와 같은 설정을 통해 mlops-platform helm chart를 통해 배포된 mlflow와 연동되어있습니다. (같은 namespace에 있어야 함)

```yaml
env:
  - name: MLFLOW_TRACKING_URI
    value: "http://mlflow-tracking:80"
```

이 mlflow 서버에서 등록된 모델을 확인해보시기 바랍니다.

```bash
NODE_PORT=$(kubectl get svc -n mlops-platform mlflow-tracking -o jsonpath='{.spec.ports[0].nodePort}')
echo $NODE_PORT
echo "http://localhost:$NODE_PORT"
```

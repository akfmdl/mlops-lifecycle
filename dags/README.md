# Airflow DAGs Setup Guide

## DAG를 실행하기 위한 패키지 설치

```bash
pip install -r dags/requirements.txt
```

## DAG 폴더 설정하기

Airflow에서 이 프로젝트의 DAG들을 인식하기 위해서는 심볼릭 링크(symbolic link)를 생성해야 합니다.
AIRFLOW_HOME을 설정하지 않았다면 기본적으로 ~/airflow 디렉토리에 설치됩니다.
```bash
ln -s $(pwd)/dags ~/airflow/dags
```

심볼릭 링크가 제대로 생성되었는지 확인:
```bash
ls -la ~/airflow/dags
```

## Airflow 시작하기

1. Airflow 시작:
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

2. DAG 활성화:
```bash
airflow dags unpause local_dag
```

3. DAG가 Airflow에 인식되는지 확인:
```bash
airflow dags list | grep local_dag
```

4. 혹은 Airflow Web UI에서 DAG 목록 확인:
   - http://localhost:8080 접속 (기본 포트 사용 시)
   - DAG 목록에서 `local_dag` 확인

## DAG 실행

### Local DAG 실행해보기

1. [방법 1] CLI를 이용한 방법
```bash
airflow dags trigger local_dag
```

2. [방법 2] Web UI를 이용한 방법
   - http://localhost:8080 접속 (기본 포트 사용 시)
   - DAG 목록에서 `local_dag` 클릭
   - 실행할 태스크 클릭
   - 태스크 실행 버튼 클릭

3. [방법 3] Python 파일을 이용한 방법
```bash
python dags/local_dag.py
```

### 태스크 실행 확인

```bash
airflow tasks list | grep local_dag
```
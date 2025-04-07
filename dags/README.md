# Airflow DAGs Setup Guide

## DAG를 실행하기 위한 패키지 설치

```bash
pip install -r dags/requirements.txt
```

## DAG 폴더 설정하기

Airflow에서 이 프로젝트의 DAG들을 인식하기 위해서는 심볼릭 링크(symbolic link)를 생성해야 합니다.

### 설정 방법

1. 프로젝트 루트 디렉토리에서 다음 명령어를 실행합니다:
AIRFLOW_HOME을 설정하지 않았다면 기본적으로 ~/airflow 디렉토리에 설치됩니다.
```bash
ln -s $(pwd)/dags ~/airflow/dags
```

### 설정 확인

1. 심볼릭 링크가 제대로 생성되었는지 확인:
```bash
ls -la ~/airflow/dags
```

2. DAG가 Airflow에 인식되는지 확인:
```bash
airflow dags list | grep local_dag
```

3. Airflow Web UI에서 DAG 목록 확인:
   - http://localhost:8080 접속 (기본 포트 사용 시)
   - DAG 목록에서 `local_dag` 확인

## Airflow 시작하기

1. Airflow 시작:
```bash
airflow standalone
```

2. DAG 활성화:
```bash
airflow dags unpause local_dag
```
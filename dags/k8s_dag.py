import os
from datetime import datetime

from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from kubernetes.client import models as k8s

DAGS_DIR = os.environ.get("DAGS_DIR", "/app/dags")
WORK_DIR = os.environ.get("WORK_DIR", "/work_dir")

with DAG(
    "k8s_dag",
    description="YOLO 데이터셋 Collection, Split, Validation, Train in Kubernetes",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["yolo", "kubernetes"],
    params={
        # 데이터셋 다운로드에 필요한 파라미터
        "dataset_url": "https://github.com/ultralytics/assets/releases/download/v0.0.0/coco128.zip",
        "dataset_cfg_url": "https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/cfg/datasets/coco128.yaml",
        "dataset_path": os.path.join(WORK_DIR, "raw"),
        # 데이터셋 Split에 필요한 파라미터
        "splits_path": os.path.join(WORK_DIR, "splits"),
        "train_ratio": 0.7,
        "val_ratio": 0.2,
        "test_ratio": 0.1,
        # YOLO 학습 DAG에 필요한 파라미터
        "output_dir": os.path.join(WORK_DIR, "runs"),
        "epochs": 10,
        "batch_size": 16,
        "img_size": 640,
        # Kubernetes 파라미터
        "work_dir_pvc_name": "data-volume",
        "dags_dir_pvc_name": "mlops-platform-dags",
        "namespace": "mlops-platform",
        "image": "goranidocker/mlops:v3",
        # modules 디렉토리 경로
        "modules_dir": os.path.join(DAGS_DIR, "repo/dags/modules"),
    },
) as dag:
    # 공통 볼륨 마운트 설정
    work_dir_volume = k8s.V1Volume(
        name="work-dir",
        persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name="{{ params.work_dir_pvc_name }}"),
    )
    dags_dir_volume = k8s.V1Volume(
        name="dags-dir",
        persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name="{{ params.dags_dir_pvc_name }}"),
    )

    work_dir_volume_mount = k8s.V1VolumeMount(name=work_dir_volume.name, mount_path=WORK_DIR)
    dags_dir_volume_mount = k8s.V1VolumeMount(name=dags_dir_volume.name, mount_path=DAGS_DIR)

    # 데이터 다운로드 태스크
    download_task = KubernetesPodOperator(
        task_id="download_dataset",
        name="download-dataset",
        namespace="{{ params.namespace }}",
        image="{{ params.image }}",
        cmds=["python"],
        arguments=[
            "{{ params.modules_dir }}/download_dataset.py",
            "--dataset_url",
            "{{ params.dataset_url }}",
            "--target_path",
            "{{ params.dataset_path }}",
        ],
        volumes=[work_dir_volume, dags_dir_volume],
        volume_mounts=[work_dir_volume_mount, dags_dir_volume_mount],
        is_delete_operator_pod=True,
        in_cluster=True,
        get_logs=True,
    )

    # 데이터 검증 태스크
    validate_task = KubernetesPodOperator(
        task_id="validate_dataset",
        name="validate-dataset",
        namespace="{{ params.namespace }}",
        image="{{ params.image }}",
        cmds=["python"],
        arguments=[
            "{{ params.modules_dir }}/validate_dataset.py",
            "--data_path",
            "{{ params.dataset_path }}",
        ],
        volumes=[work_dir_volume, dags_dir_volume],
        volume_mounts=[work_dir_volume_mount, dags_dir_volume_mount],
        is_delete_operator_pod=True,
        in_cluster=True,
        get_logs=True,
    )

    # 데이터 분할 태스크
    split_task = KubernetesPodOperator(
        task_id="split_dataset",
        name="split-dataset",
        namespace="{{ params.namespace }}",
        image="{{ params.image }}",
        cmds=["python"],
        arguments=[
            "{{ params.modules_dir }}/split_dataset.py",
            "--data_path",
            "{{ params.dataset_path }}",
            "--target_path",
            "{{ params.splits_path }}",
            "--train_ratio",
            "{{ params.train_ratio }}",
            "--val_ratio",
            "{{ params.val_ratio }}",
            "--test_ratio",
            "{{ params.test_ratio }}",
        ],
        volumes=[work_dir_volume, dags_dir_volume],
        volume_mounts=[work_dir_volume_mount, dags_dir_volume_mount],
        is_delete_operator_pod=True,
        in_cluster=True,
        get_logs=True,
    )

    # 데이터 YAML 생성 태스크
    create_data_yaml_task = KubernetesPodOperator(
        task_id="create_data_yaml",
        name="create-data-yaml",
        namespace="{{ params.namespace }}",
        image="{{ params.image }}",
        cmds=["python"],
        arguments=[
            "{{ params.modules_dir }}/create_data_yaml.py",
            "--train_path",
            "{{ params.splits_path }}/train",
            "--val_path",
            "{{ params.splits_path }}/val",
            "--test_path",
            "{{ params.splits_path }}/test",
            "--dataset_cfg_url",
            "{{ params.dataset_cfg_url }}",
            "--output_path",
            "{{ params.splits_path }}/data.yaml",
        ],
        volumes=[work_dir_volume, dags_dir_volume],
        volume_mounts=[work_dir_volume_mount, dags_dir_volume_mount],
        is_delete_operator_pod=True,
        in_cluster=True,
        get_logs=True,
    )

    # YOLO 모델 학습 태스크
    train_yolo_task = KubernetesPodOperator(
        task_id="train_yolo",
        name="train-yolo",
        namespace="{{ params.namespace }}",
        image="{{ params.image }}",
        cmds=["python"],
        arguments=[
            "{{ params.modules_dir }}/train_yolo.py",
            "--data_yaml_path",
            "{{ params.splits_path }}/data.yaml",
            "--epochs",
            "{{ params.epochs }}",
            "--batch_size",
            "{{ params.batch_size }}",
            "--img_size",
            "{{ params.img_size }}",
        ],
        volumes=[work_dir_volume, dags_dir_volume],
        volume_mounts=[work_dir_volume_mount, dags_dir_volume_mount],
        container_resources=k8s.V1ResourceRequirements(
            requests={"cpu": "1", "memory": "4Gi"}, limits={"cpu": "2", "memory": "8Gi"}
        ),
        is_delete_operator_pod=True,
        in_cluster=True,
        get_logs=True,
    )

    download_task >> validate_task >> split_task >> create_data_yaml_task >> train_yolo_task


if __name__ == "__main__":
    dag.test()

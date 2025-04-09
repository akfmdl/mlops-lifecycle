from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from modules.create_data_yaml import create_data_yaml
from modules.download_dataset import download_dataset
from modules.extract_dataset import extract_dataset
from modules.split_dataset import split_dataset
from modules.train_yolo import train_yolo
from modules.validate_dataset import validate_dataset

with DAG(
    "local_dag",
    description="YOLO 데이터셋 Collection, Split, Validation, Train",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["yolo", "local"],
    params={
        # 데이터셋 다운로드에 필요한 파라미터
        "dataset_url": "https://github.com/ultralytics/assets/releases/download/v0.0.0/coco128.zip",
        "dataset_cfg_url": "https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/cfg/datasets/coco128.yaml",
        "dataset_path": "./data/raw/extracted",
        # 데이터셋 Split에 필요한 파라미터
        "splits_path": "./data/splits",
        "train_ratio": 0.7,
        "val_ratio": 0.2,
        "test_ratio": 0.1,
        # YOLO 학습 DAG에 필요한 파라미터
        "output_dir": "./runs",
        "epochs": 10,
        "batch_size": 16,
        "img_size": 640,
    },
    render_template_as_native_obj=True,
) as dag:
    download_task = PythonOperator(
        task_id="download_dataset",
        python_callable=download_dataset,
        op_kwargs={"dataset_url": "{{ params.dataset_url }}"},
    )

    extract_task = PythonOperator(
        task_id="extract_dataset",
        python_callable=extract_dataset,
        op_kwargs={
            "source_path": "{{ task_instance.xcom_pull(task_ids='download_dataset') }}",
            "target_path": "{{ params.dataset_path }}",
        },
    )

    validate_task = PythonOperator(
        task_id="validate_dataset",
        python_callable=validate_dataset,
        op_kwargs={"data_path": "{{ params.dataset_path }}"},
    )

    split_task = PythonOperator(
        task_id="split_dataset",
        python_callable=split_dataset,
        op_kwargs={
            "data_path": "{{ params.dataset_path }}",
            "target_path": "{{ params.splits_path }}",
            "train_ratio": "{{ params.train_ratio }}",
            "val_ratio": "{{ params.val_ratio }}",
            "test_ratio": "{{ params.test_ratio }}",
        },
    )

    create_data_yaml_task = PythonOperator(
        task_id="create_data_yaml",
        python_callable=create_data_yaml,
        op_kwargs={
            "train_path": "{{ params.splits_path }}/train",
            "val_path": "{{ params.splits_path }}/val",
            "test_path": "{{ params.splits_path }}/test",
            "dataset_cfg_url": "{{ params.dataset_cfg_url }}",
            "output_path": "{{ params.splits_path }}/data.yaml",
        },
    )

    train_yolo_task = PythonOperator(
        task_id="train_yolo",
        python_callable=train_yolo,
        op_kwargs={
            "data_yaml_path": "{{ task_instance.xcom_pull(task_ids='create_data_yaml') }}",
            "output_dir": "{{ params.output_dir }}",
            "epochs": "{{ params.epochs }}",
            "batch_size": "{{ params.batch_size }}",
            "img_size": "{{ params.img_size }}",
        },
    )

    download_task >> extract_task >> validate_task >> split_task >> create_data_yaml_task >> train_yolo_task


if __name__ == "__main__":
    dag.test()

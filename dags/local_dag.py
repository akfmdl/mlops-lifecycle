import os
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

MODULES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules")
WORK_DIR = os.environ.get("WORK_DIR", "/tmp/airflow/data")

with DAG(
    "local_dag",
    description="YOLO 데이터셋 Collection, Split, Validation, Train, Deploy",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["yolo", "local"],
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
        "epochs": 10,
        "batch_size": 16,
        "img_size": 640,
        "run_name": "yolo11n-onnx",
        "force_register": False,
        # 모델 버전 등 정보를 업데이트할 git 정보
        "git_branch": "main",
        # modules 디렉토리 경로
        "modules_dir": MODULES_DIR,
    },
    render_template_as_native_obj=True,
) as dag:
    download_task = BashOperator(
        task_id="download_dataset",
        bash_command="python {{ params.modules_dir }}/download_dataset.py \
            --dataset_url {{ params.dataset_url }} \
            --target_path {{ params.dataset_path }}",
    )

    validate_task = BashOperator(
        task_id="validate_dataset",
        bash_command="python {{ params.modules_dir }}/validate_dataset.py \
            --data_path {{ params.dataset_path }}",
    )

    split_task = BashOperator(
        task_id="split_dataset",
        bash_command="python {{ params.modules_dir }}/split_dataset.py \
            --data_path {{ params.dataset_path }} \
            --target_path {{ params.splits_path }} \
            --train_ratio {{ params.train_ratio }} \
            --val_ratio {{ params.val_ratio }} \
            --test_ratio {{ params.test_ratio }}",
    )

    create_data_yaml_task = BashOperator(
        task_id="create_data_yaml",
        bash_command="python {{ params.modules_dir }}/create_data_yaml.py \
            --train_path {{ params.splits_path }}/train \
            --val_path {{ params.splits_path }}/val \
            --test_path {{ params.splits_path }}/test \
            --dataset_cfg_url {{ params.dataset_cfg_url }} \
            --output_path {{ params.splits_path }}/data.yaml",
    )

    train_yolo_task = BashOperator(
        task_id="train_yolo",
        bash_command="python {{ params.modules_dir }}/train_yolo.py \
            --data_yaml_path {{ params.splits_path }}/data.yaml \
            --epochs {{ params.epochs }} \
            --batch_size {{ params.batch_size }} \
            --img_size {{ params.img_size }} \
            --run_name {{ params.run_name }} \
            --force_register {{ params.force_register }}",
    )

    update_triton_config_task = BashOperator(
        task_id="update_triton_config",
        bash_command="python {{ params.modules_dir }}/update_triton_config.py \
            --model_name {{ params.run_name }} \
            --branch {{ params.git_branch }}",
    )

    (
        download_task
        >> validate_task
        >> split_task
        >> create_data_yaml_task
        >> train_yolo_task
        >> update_triton_config_task
    )


if __name__ == "__main__":
    dag.test()

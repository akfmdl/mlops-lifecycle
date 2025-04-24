#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

import mlflow
import yaml

MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")


def clone_repo(repo_url, branch="main", target_dir=None):
    """Git repository를 clone합니다."""
    if target_dir is None:
        target_dir = tempfile.mkdtemp()

    print(f"Git repository 클론 중: {repo_url} -> {target_dir}")
    try:
        subprocess.run(["git", "clone", "-b", branch, repo_url, target_dir], check=True, capture_output=True, text=True)
        return target_dir
    except subprocess.CalledProcessError as e:
        print(f"Git clone 실패: {e.stderr}")
        sys.exit(1)


def get_current_model_version(values_path, model_name):
    """values.yaml 파일에서 현재 설정된 모델 버전을 가져옵니다."""
    try:
        with open(values_path, "r", encoding="utf-8") as f:
            values = yaml.safe_load(f)

        for server in values.get("tritonServers", []):
            if server.get("name") == model_name:
                for env_var in server.get("env", []):
                    if env_var.get("name") == "MLFLOW_MODEL_VERSION":
                        return env_var.get("value")

        print(f"경고: {model_name} 모델을 위한 MLFLOW_MODEL_VERSION 환경 변수를 찾을 수 없습니다.")
        return None
    except Exception as e:
        print(f"values.yaml에서 현재 버전 조회 실패: {str(e)}")
        return None


def update_values_yaml(values_path, model_name, new_version):
    """values.yaml 파일에서 특정 모델의 버전을 업데이트합니다."""
    print(f"values.yaml 업데이트 중: {values_path} (모델: {model_name}, 새 버전: {new_version})")

    try:
        with open(values_path, "r", encoding="utf-8") as f:
            values = yaml.safe_load(f)

        updated = False
        for server in values.get("tritonServers", []):
            if server.get("name") == model_name:
                for env_var in server.get("env", []):
                    if env_var.get("name") == "MLFLOW_MODEL_VERSION":
                        env_var["value"] = str(new_version)
                        updated = True
                        break

        if not updated:
            print(f"경고: {model_name} 모델을 위한 MLFLOW_MODEL_VERSION 환경 변수를 찾을 수 없습니다.")
            return False

        with open(values_path, "w", encoding="utf-8") as f:
            yaml.dump(values, f, default_flow_style=False)

        return True
    except Exception as e:
        print(f"values.yaml 업데이트 실패: {str(e)}")
        return False


def get_latest_model_version(model_name):
    """MLflow에서 최신 모델 버전을 가져옵니다."""
    try:
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        print(f"MLflow tracking URI 설정: {MLFLOW_TRACKING_URI}")

        client = mlflow.tracking.MlflowClient()
        versions = client.search_model_versions(f"name='{model_name}'")
        if versions:
            return max(int(v.version) for v in versions)
        return 1  # 기본값
    except Exception as e:
        print(f"MLflow에서 최신 버전 조회 실패: {str(e)}")
        return 1  # 에러 발생 시 기본값


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Triton Inference Server 설정 업데이트")
    parser.add_argument("--model_name", type=str, default="yolo11n", help="업데이트할 모델 이름")
    parser.add_argument(
        "--repo_url", type=str, default="https://github.com/akfmdl/mlops-lifecycle.git", help="Git repository URL"
    )
    parser.add_argument("--branch", type=str, default="test", help="Git branch")
    parser.add_argument(
        "--values_path",
        type=str,
        default="charts/tritoninferenceserver/values.yaml",
        help="values.yaml 파일의 상대 경로",
    )
    args = parser.parse_args()

    # Git repository 클론
    temp_dir = clone_repo(args.repo_url, args.branch)

    try:
        # values.yaml 파일 경로
        values_full_path = os.path.join(temp_dir, args.values_path)

        # 현재 values.yaml에 설정된 모델 버전 확인
        current_version = get_current_model_version(values_full_path, args.model_name)
        if current_version is None:
            print(f"values.yaml에서 {args.model_name} 모델의 현재 버전을 확인할 수 없습니다.")
            sys.exit(1)

        # MLflow의 최신 모델 버전 가져오기
        mlflow_latest_version = get_latest_model_version(args.model_name)

        # 버전이 같으면 업데이트하지 않음
        if str(mlflow_latest_version) == str(current_version):
            print(
                f"현재 버전({current_version})이 MLflow의 최신 버전({mlflow_latest_version})과 동일합니다. 업데이트가 필요하지 않습니다."
            )
            sys.exit(0)

        print(f"업데이트 필요: 현재 버전({current_version}) -> 최신 버전({mlflow_latest_version})")

        # values.yaml 파일 업데이트
        if update_values_yaml(values_full_path, args.model_name, mlflow_latest_version):
            # 변경사항 커밋 및 푸시
            subprocess.run(["git", "-C", temp_dir, "add", args.values_path], check=True, capture_output=True)
            subprocess.run(
                ["git", "-C", temp_dir, "commit", "-m", f"Update {args.model_name} version to {mlflow_latest_version}"],
                check=True,
                capture_output=True,
            )
            subprocess.run(["git", "-C", temp_dir, "push"], check=True, capture_output=True)

            print(
                f"Triton Inference Server 설정이 성공적으로 업데이트되었습니다. 모델: {args.model_name}, 버전: {mlflow_latest_version}"
            )
        else:
            print("values.yaml 업데이트 실패.")
    finally:
        # 임시 디렉토리 정리
        shutil.rmtree(temp_dir, ignore_errors=True)

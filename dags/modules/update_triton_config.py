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
GIT_USERNAME = os.environ.get("GIT_USERNAME", "")
GIT_EMAIL = os.environ.get("GIT_EMAIL", "")
GIT_TOKEN = os.environ.get("GIT_TOKEN", "")


def clone_repo(repo_url, branch="main", target_dir=None):
    """Git repository를 clone합니다."""
    if target_dir is None:
        target_dir = tempfile.mkdtemp()

    # Git 토큰이 있는 경우 URL에 인증 정보 추가
    auth_repo_url = repo_url
    if GIT_TOKEN:
        # https://github.com/user/repo.git -> https://token@github.com/user/repo.git
        if repo_url.startswith("https://"):
            auth_repo_url = repo_url.replace("https://", f"https://{GIT_TOKEN}@")
        print("Git 인증 정보가 URL에 추가되었습니다.")

    print(f"Git repository 클론 중: {repo_url} -> {target_dir}")
    try:
        subprocess.run(
            ["git", "clone", "-b", branch, auth_repo_url, target_dir], check=True, capture_output=True, text=True
        )
        return target_dir
    except subprocess.CalledProcessError as e:
        print(f"Git clone 실패: {e.stderr}")
        sys.exit(1)


def configure_git(repo_dir):
    """Git 사용자 정보를 설정합니다."""
    try:
        # 로컬 저장소에 Git 사용자 정보 설정
        if GIT_USERNAME:
            subprocess.run(
                ["git", "-C", repo_dir, "config", "user.name", GIT_USERNAME], check=True, capture_output=True
            )
            print(f"Git 사용자 이름 설정: {GIT_USERNAME}")

        if GIT_EMAIL:
            subprocess.run(["git", "-C", repo_dir, "config", "user.email", GIT_EMAIL], check=True, capture_output=True)
            print(f"Git 이메일 설정: {GIT_EMAIL}")

        # Git 보안 설정 - credential.helper 설정 (필요한 경우)
        if GIT_TOKEN:
            subprocess.run(
                ["git", "-C", repo_dir, "config", "credential.helper", "store"], check=True, capture_output=True
            )
            print("Git credential helper 설정 완료")

        return True
    except subprocess.CalledProcessError as e:
        print(f"Git 설정 실패: {e.stderr}")
        return False


def get_current_model_version(values_path, model_name):
    """values.yaml 파일에서 현재 설정된 모델 버전을 가져옵니다."""
    try:
        with open(values_path, "r", encoding="utf-8") as f:
            values = yaml.safe_load(f)

        for server in values.get("tritonServers", []):
            # MLFLOW_MODEL_NAME 환경 변수의 값이 model_name과 일치하는지 확인
            for env_var in server.get("env", []):
                if env_var.get("name") == "MLFLOW_MODEL_NAME" and env_var.get("value") == model_name:
                    # 일치하는 서버를 찾았으면, 해당 서버의 MLFLOW_MODEL_VERSION 환경 변수 값 반환
                    for version_env in server.get("env", []):
                        if version_env.get("name") == "MLFLOW_MODEL_VERSION":
                            return version_env.get("value")

                    print(f"경고: {model_name} 모델을 위한 MLFLOW_MODEL_VERSION 환경 변수를 찾을 수 없습니다.")
                    return None

        print(f"경고: MLFLOW_MODEL_NAME이 {model_name}인 서버를 찾을 수 없습니다.")
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
            # MLFLOW_MODEL_NAME 환경 변수의 값이 model_name과 일치하는지 확인
            for env_var in server.get("env", []):
                if env_var.get("name") == "MLFLOW_MODEL_NAME" and env_var.get("value") == model_name:
                    # 일치하는 서버를 찾았으면, 해당 서버의 MLFLOW_MODEL_VERSION 환경 변수 업데이트
                    for version_env in server.get("env", []):
                        if version_env.get("name") == "MLFLOW_MODEL_VERSION":
                            version_env["value"] = str(new_version)
                            updated = True
                            break
                    break  # 해당 서버에 대한 처리 완료

        if not updated:
            print(
                f"경고: MLFLOW_MODEL_NAME이 {model_name}인 서버를 찾을 수 없거나, MLFLOW_MODEL_VERSION 환경 변수가 없습니다."
            )
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


def commit_and_push_changes(repo_dir, file_path, model_name, new_version):
    """변경사항을 커밋하고 원격 저장소로 푸시합니다."""
    try:
        print("Git 변경사항 커밋 및 푸시 중...")

        # 변경 사항 추가
        result = subprocess.run(["git", "-C", repo_dir, "add", file_path], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print(f"Git add 실패: {result.stderr}")
            return False

        # 변경 사항 커밋
        commit_message = f"Update {model_name} version to {new_version}"
        result = subprocess.run(
            ["git", "-C", repo_dir, "commit", "-m", commit_message], capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            print(f"Git commit 실패: {result.stderr}")
            return False

        # 원격 저장소로 푸시
        result = subprocess.run(["git", "-C", repo_dir, "push"], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print(f"Git push 실패: {result.stderr}")
            return False

        print("Git 변경사항 성공적으로 커밋 및 푸시 완료")
        return True
    except Exception as e:
        print(f"Git 커밋/푸시 중 예외 발생: {str(e)}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Triton Inference Server 설정 업데이트")
    parser.add_argument("--model_name", type=str, default="yolo11n-onnx", help="업데이트할 모델 이름")
    parser.add_argument(
        "--repo_url", type=str, default="https://github.com/akfmdl/mlops-lifecycle.git", help="Git repository URL"
    )
    parser.add_argument("--branch", type=str, default="main", help="Git branch")
    parser.add_argument(
        "--values_path",
        type=str,
        default="charts/tritoninferenceserver/values.yaml",
        help="values.yaml 파일의 상대 경로",
    )
    parser.add_argument("--configure_git", action="store_true", help="Git config 설정하기")

    args = parser.parse_args()

    # Git 작업을 건너뛸 경우 Git credentials 없이도 진행 가능
    if args.configure_git:
        print("Git config 설정 옵션이 설정되어 있습니다.")

    # Git 인증 정보 확인
    if args.configure_git and not (GIT_USERNAME and GIT_EMAIL):
        print("경고: Git 사용자 정보(GIT_USERNAME, GIT_EMAIL)가 설정되지 않았습니다.")

    # Git repository 클론
    temp_dir = clone_repo(args.repo_url, args.branch)

    try:
        # Git 설정 (사용자 이름, 이메일 등)
        if args.configure_git:
            git_configured = configure_git(temp_dir)
            if not git_configured and not (GIT_USERNAME and GIT_EMAIL):
                print("다음 환경 변수를 설정하세요:")
                print("  GIT_USERNAME: Git 사용자 이름")
                print("  GIT_EMAIL: Git 이메일")
                print("  GIT_TOKEN: (선택) Git 인증 토큰")
                sys.exit(1)

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
                f"{args.model_name} 현재 버전({current_version})이 MLflow의 최신 버전({mlflow_latest_version})과 동일합니다. 업데이트가 필요하지 않습니다."
            )
            sys.exit(0)

        print(f"{args.model_name} 업데이트 필요: 현재 버전({current_version}) -> 최신 버전({mlflow_latest_version})")

        # values.yaml 파일 업데이트
        if update_values_yaml(values_full_path, args.model_name, mlflow_latest_version):
            # 변경사항 커밋 및 푸시
            if commit_and_push_changes(temp_dir, args.values_path, args.model_name, mlflow_latest_version):
                print(
                    f"Triton Inference Server 설정이 성공적으로 업데이트되었습니다. 모델: {args.model_name}, 버전: {mlflow_latest_version}"
                )
            else:
                print("Git 변경사항 적용 실패.")
                print("다음 환경 변수가 올바르게 설정되었는지 확인하세요:")
                print("  GIT_USERNAME: Git 사용자 이름")
                print("  GIT_EMAIL: Git 이메일")
                print("  GIT_TOKEN: Git 인증 토큰")
        else:
            print("values.yaml 업데이트 실패.")
    finally:
        # 임시 디렉토리 정리
        shutil.rmtree(temp_dir, ignore_errors=True)

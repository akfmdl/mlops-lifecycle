#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

import requests
import yaml


def create_data_yaml(train_path, val_path, test_path, dataset_cfg_url, output_path):
    """YOLO 학습용 data.yaml 파일 생성"""
    print(f"YAML 파일 생성 중: {output_path}")

    # 경로 객체로 변환
    train_path = Path(train_path)
    val_path = Path(val_path)
    test_path = Path(test_path)
    output_path = Path(output_path)

    # 경로 존재 확인
    if not train_path.exists():
        raise ValueError(f"학습 경로가 존재하지 않습니다: {train_path}")
    if not val_path.exists():
        raise ValueError(f"검증 경로가 존재하지 않습니다: {val_path}")
    if not test_path.exists():
        raise ValueError(f"테스트 경로가 존재하지 않습니다: {test_path}")

    # 출력 디렉토리 생성
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 기본 설정 다운로드
    print(f"데이터셋 설정 다운로드 중: {dataset_cfg_url}")
    response = requests.get(dataset_cfg_url, timeout=10)
    response.raise_for_status()

    # 기존 설정 파싱
    config = yaml.safe_load(response.text)

    # 경로 업데이트
    config["path"] = str(train_path.absolute().parent)
    config["train"] = str(train_path.absolute())
    config["val"] = str(val_path.absolute())
    config["test"] = str(test_path.absolute())

    # YAML 파일로 저장
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False)

    print(f"YAML 파일 생성 완료: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YOLO 학습용 data.yaml 파일 생성")
    parser.add_argument("--train_path", type=str, required=True, help="학습 데이터 경로")
    parser.add_argument("--val_path", type=str, required=True, help="검증 데이터 경로")
    parser.add_argument("--test_path", type=str, required=True, help="테스트 데이터 경로")
    parser.add_argument("--dataset_cfg_url", type=str, required=True, help="데이터셋 설정 URL")
    parser.add_argument("--output_path", type=str, required=True, help="출력 YAML 파일 경로")

    args = parser.parse_args()

    try:
        yaml_path = create_data_yaml(
            args.train_path, args.val_path, args.test_path, args.dataset_cfg_url, args.output_path
        )
        print(f"XCOM_RETURN:{yaml_path}")
    except Exception as e:
        print(f"YAML 생성 실패: {e}")
        sys.exit(1)

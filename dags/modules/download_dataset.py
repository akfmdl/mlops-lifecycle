#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

import requests


def download_dataset(dataset_url):
    """YOLO 포맷의 데이터셋을 다운로드합니다."""
    print(f"데이터셋 URL: {dataset_url}")
    download_path = Path("/tmp/data/raw")
    download_path.mkdir(parents=True, exist_ok=True)

    # 파일 다운로드
    response = requests.get(dataset_url, stream=True, timeout=10)
    response.raise_for_status()

    file_path = download_path / "dataset.zip"
    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"다운로드 완료: {file_path}")
    return str(file_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YOLO 데이터셋 다운로드")
    parser.add_argument("--dataset_url", type=str, required=True, help="데이터셋 다운로드 URL")

    args = parser.parse_args()

    try:
        file_path = download_dataset(args.dataset_url)
        print(f"XCOM_RETURN:{file_path}")
    except Exception as e:
        print(f"다운로드 실패: {e}")
        sys.exit(1)

#!/usr/bin/env python3
import argparse
import sys
import zipfile
from pathlib import Path


def extract_dataset(source_path, target_path):
    """압축 파일을 해제합니다."""
    extract_path = Path(target_path)
    extract_path.mkdir(parents=True, exist_ok=True)

    print(f"압축 해제 중: {source_path} -> {target_path}")
    with zipfile.ZipFile(source_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)

    print(f"압축 해제 완료: {extract_path}")
    return str(extract_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="데이터셋 압축 해제")
    parser.add_argument("--source_path", type=str, required=True, help="압축 데이터셋 경로")
    parser.add_argument("--target_path", type=str, required=True, help="압축 해제 대상 경로")

    args = parser.parse_args()

    try:
        extracted_path = extract_dataset(args.source_path, args.target_path)
        print(f"XCOM_RETURN:{extracted_path}")
    except Exception as e:
        print(f"압축 해제 실패: {e}")
        sys.exit(1)

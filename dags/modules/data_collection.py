import zipfile
from pathlib import Path

import requests


def download_dataset(dataset_url: str):
    """YOLO 포맷의 데이터셋을 다운로드합니다."""
    print(f"dataset_url: {dataset_url}")
    download_path = Path("./data/raw")
    download_path.mkdir(parents=True, exist_ok=True)

    # 파일 다운로드
    response = requests.get(dataset_url, stream=True, timeout=10)
    response.raise_for_status()

    file_path = download_path / "dataset.zip"
    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return str(file_path)


def extract_dataset(source_path: str, target_path: str):
    """압축 파일을 해제합니다."""
    extract_path = Path(target_path)
    extract_path.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(source_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)

    return str(extract_path)
#!/usr/bin/env python3
import argparse
import json
import os
from time import sleep

import requests


def test_get_models(base_url):
    """Test the GET / endpoint that lists available models"""
    print("\n=== Testing GET / (List Models) ===")

    # Success case
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print(f"Model list: {response.json()}")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Exception occurred: {str(e)}")


def test_predict(base_url):
    """Test the POST /predict endpoint with various scenarios"""
    print("\n=== Testing POST /predict (Model Inference) ===")

    # 1. Success case with valid image URL
    print("\n--- Test case: Valid request ---")
    valid_payload = {
        "model_version": "1",
        "image_url": "https://djl.ai/examples/src/test/resources/dog_bike_car.jpg",
    }

    try:
        response = requests.post(f"{base_url}/onnx-model/predict", json=valid_payload, timeout=10)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print(f"Result: {response.json()}")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Exception occurred: {str(e)}")

    # 2. Error case: Invalid image URL
    print("\n--- Test case: Invalid image URL ---")
    invalid_url_payload = {
        "model_version": "1",
        "image_url": "https://non-existent-domain-12345.com/image.jpg",
    }

    try:
        response = requests.post(f"{base_url}/onnx-model/predict", json=invalid_url_payload, timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Exception occurred: {str(e)}")

    # 3. Error case: Invalid model name
    print("\n--- Test case: Invalid model name ---")
    invalid_model_payload = {
        "model_version": "1",
        "image_url": "https://djl.ai/examples/src/test/resources/dog_bike_car.jpg",
    }

    try:
        response = requests.post(f"{base_url}/non-existent-model/predict", json=invalid_model_payload, timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Exception occurred: {str(e)}")

    # 5. Error case: Invalid JSON payload
    print("\n--- Test case: Invalid JSON payload ---")
    try:
        # Send malformed JSON
        response = requests.post(
            f"{base_url}/onnx-model/predict",
            data="This is not JSON",
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        print(f"Status code: {response.status_code}")
        print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Exception occurred: {str(e)}")

    # 6. Error case: Missing required field
    print("\n--- Test case: Missing required field ---")
    missing_field_payload = {
        "model_version": "1",
        # Missing image_url
    }

    try:
        response = requests.post(f"{base_url}/onnx-model/predict", json=missing_field_payload, timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Exception occurred: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description="Test FastAPI endpoints for model inference")
    parser.add_argument("--host", default="localhost", help="API host")
    parser.add_argument("--port", default="8000", help="API port")
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"
    print(f"Testing API at {base_url}")

    # Test model listing endpoint
    test_get_models(base_url)

    # Test prediction endpoint
    test_predict(base_url)

    print("\n=== All tests completed ===")


if __name__ == "__main__":
    main()

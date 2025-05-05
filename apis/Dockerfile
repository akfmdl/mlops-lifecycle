FROM python:3.12-slim

WORKDIR /app

# # hadolint ignore=DL3008
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     git \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --no-cache-dir -r requirements.txt
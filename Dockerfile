FROM caffeinism/pytorch:2.1.2-cpu-python3.11

ARG GIT_TOKEN
ARG DEBIAN_FRONTEND=noninteractive
ARG DUBBING_VERSION=latest

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    curl \
    git \
    libglib2.0-0 \
    ffmpeg \
    espeak-ng


RUN pip install -U "uvicorn[standard]" fastapi requests httpx python-multipart fastapi_camelcase apscheduler asyncstdlib aiofiles 'pydantic>2' starlette pyzmq msgpack msgpack_numpy tenacity

# Clone specific version of dubbing repository
RUN if [ "$DUBBING_VERSION" = "latest" ]; then \
        git clone https://${GIT_TOKEN}@github.com/team-ailab/dubbing.git /libs/dubbing; \
    else \
        git clone --branch $DUBBING_VERSION https://${GIT_TOKEN}@github.com/team-ailab/dubbing.git /libs/dubbing; \
    fi

RUN pip install /libs/dubbing /libs/dubbing/libs/audio-triton-client /libs/dubbing/libs/live-api-client
COPY app /src/app
COPY pyproject.toml /src/pyproject.toml
WORKDIR /src

# ENTRYPOINT 
CMD ["python", "-m", "uvicorn", "app.main:app", "--host=0.0.0.0", "--port=80", "--loop=asyncio"]

all: build push

CONTAINER_REGISTRY?=persolive.azurecr.io
PLATFORM?=linux/amd64
DUBBING_VERSION?=latest

build:
	sudo docker build . --tag=$(CONTAINER_REGISTRY)/audio-engine-server:$(TAG) --platform=$(PLATFORM) --build-arg DUBBING_VERSION=$(DUBBING_VERSION)
push:
	sudo docker push $(CONTAINER_REGISTRY)/audio-engine-server:$(TAG)

#!/bin/bash
REGISTRY="registry.rodox.dns.army/openedai-speech"
TAG="latest"

if [[ "$1" == "--deepspeed" ]]; then
    DEEPSPEED_ARG="--build-arg DEEPSPEED=true"
		TAG="deepspeed"
fi

echo "Building and pushing Docker image..."
docker buildx build $DEEPSPEED_ARG -t $REGISTRY:$TAG --push .


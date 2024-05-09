#!/bin/bash

# Define variables
IMAGE_NAME="shorts-generator:latest"
CONTAINER_NAME="shorts"

# Build the new Docker image
docker build -t $IMAGE_NAME .

# Stop the running container, ignore error if container does not exist
docker stop $CONTAINER_NAME || true

# Remove the stopped container, ignore error if container does not exist
docker rm $CONTAINER_NAME || true

# Run a new container with the newly built image
docker run -d -p 31415:31415 --name $CONTAINER_NAME --env-file .env $IMAGE_NAME
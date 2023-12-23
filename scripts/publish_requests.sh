#!/bin/bash

# Build the Docker image
docker build -f ../requests/Dockerfile -t requests ../requests

# Tag the Docker image
docker tag requests ikrash3d/requests:latest

# Push the Docker image to the repository
docker push ikrash3d/requests:latest
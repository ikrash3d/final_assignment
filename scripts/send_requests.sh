#!/bin/bash

# Access the env variables
source env_vars.sh

# Pulling requests_app's image
docker pull ikrash3d/requests:latest

# Running the requests_app's container with Orchestrator DNS
docker run -e ORCHESTRATOR_DNS="$ORCHESTRATOR_DNS" ikrash3d/requests:latest
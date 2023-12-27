#!/bin/bash

# Allow to track the progress of the script
exec > /home/ubuntu/steps.log 2>&1 # tail -f steps.log

# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update


# Install necessary dependencies
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add ec2-user to the docker group so you can execute Docker commands without using sudo
sudo usermod -a -G docker ec2-user

# Start Docker
sudo service docker start

# Pull the latest image flask_app image from Docker Hub
sudo docker pull ikrash3d/gatekeeper:latest

# Run the Flask app inside a Docker container
sudo docker run -p 80:80 ikrash3d/gatekeeper:latest
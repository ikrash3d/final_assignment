#!/bin/bash

# Access the env variables
source env_vars.sh

# Initialize Terraform
echo -e "Creating instances...\n"
cd ../infrastructure

# Initialize Terraform
terraform.exe init

# Apply the Terraform configuration
terraform.exe apply -auto-approve -var="AWS_ACCESS_KEY=$AWS_ACCESS_KEY" -var="AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY"

# Capture the IP addresses in JSON format
echo -e "Everything was created successfully\n"
echo -e "-----------\n"

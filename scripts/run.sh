#!/bin/bash

# Access the env variables
source env_vars.sh

cd ../infrastructure

cd ../scripts

# Getting AWS credentials from the terminal
echo "Please provide your AWS Access Key: "
read AWS_ACCESS_KEY

echo "Please provide your AWS Secret Access Key: "
read AWS_SECRET_ACCESS_KEY


# Exporting the credentials to be accessible in all the scripts
echo "export AWS_ACCESS_KEY='$AWS_ACCESS_KEY'" > env_vars.sh
echo "export AWS_SECRET_ACCESS_KEY='$AWS_SECRET_ACCESS_KEY'" >> env_vars.sh

echo -e "Starting Final assignement...\n"
echo -e "-----------\n"

# Deploying the infrastructure
echo -e "Deploying the infrastructure...\n"
./create_instances.sh


echo -e "Everything was created successuflly :)"

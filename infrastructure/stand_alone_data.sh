#!/bin/bash

# MYSQL_ROOT_PASSWORD="admin123"

# # Set MySQL root password
# sudo debconf-set-selections <<< "mysql-server mysql-server/root_password password $MYSQL_ROOT_PASSWORD"
# sudo debconf-set-selections <<< "mysql-server mysql-server/root_password_again password $MYSQL_ROOT_PASSWORD"

# Install MySQL server
sudo apt-get update
sudo apt-get -y install mysql-server

# # # Secure MySQL installation (optional, but recommended)
# sudo mysql_secure_installation

# # Restart MySQL service
# sudo systemctl restart mysql



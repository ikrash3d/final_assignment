#!/bin/bash

# Allow to track the progress of the script
exec > /home/ubuntu/steps.log 2>&1 # tail -f steps.log

# Install required packages
sudo apt-get update
sudo apt-get -y install unzip sysbench

# Install MySQL
sudo apt-get -y install mysql-server

# Wait for MySQL to start
while ! mysqladmin ping --silent; do
    sleep 1
done

# Download and unzip Sakila database
sudo wget https://downloads.mysql.com/docs/sakila-db.zip
sudo unzip sakila-db.zip
cd sakila-db

# Create Sakila database
sudo mysql -u root -e "SOURCE sakila-schema.sql;"
sudo mysql -u root -e "SOURCE sakila-data.sql;"

# Verify that the default tables were created
sudo mysql -u root -e "USE sakila; SHOW FULL TABLES;"
sudo mysql -u root -e "USE sakila; SELECT COUNT(*) FROM payment;"

# Prepare a MySQL database for an OLTP (Online Transaction Processing) benchmark
sudo sysbench /usr/share/sysbench/oltp_read_write.lua prepare --db-driver=mysql --mysql-user=root --mysql-db=sakila --table_size=1000000 --threads=6 --events=0 --time=60 --rand-type=uniform

# Run the OLTP benchmark
sudo sysbench /usr/share/sysbench/oltp_read_write.lua run --db-driver=mysql --mysql-user=root --mysql-db=sakila --table_size=1000000 --threads=6 --events=0 --time=60 --rand-type=uniform

# Cleanup the OLTP benchmark
sudo sysbench /usr/share/sysbench/oltp_read_write.lua cleanup --db-driver=mysql --mysql-user=root --mysql-db=sakila --table_size=1000000 --threads=6 --events=0 --time=60 --rand-type=uniform


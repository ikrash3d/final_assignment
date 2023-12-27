import logging
import random

import boto3
import ping3
import pymysql
from aws_creds import AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY
from flask import Flask, jsonify, request
from sshtunnel import SSHTunnelForwarder

app = Flask(__name__)

# AWS EC2 client configuration
client = boto3.client(
    service_name='ec2',
    region_name="us-east-1",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

used_manager_ip =''
used_worker_ip = ''

# Function to retrieve public IP addresses of EC2 instances with a specific keyword in their name
def get_instances_public_ips(keyword):
    response = client.describe_instances()
    instances_infos = []

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            if instance["State"]['Name'] == 'running':
                for tag in instance.get('Tags', []):
                    if tag.get("Key") == 'Name' and keyword in tag.get('Value'):
                        instance_name = tag.get('Value')
                        instance_infos = {"Name": instance_name, "PublicIpAddress": instance.get("PublicIpAddress")}
                        instances_infos.append(instance_infos)

    return instances_infos

# Function to retrieve the public IP address of the manager instance
def get_manager_public_ip():
    manager_infos = {}
    instances_infos = get_instances_public_ips("Manager")

    for instance_info in instances_infos:
        manager_infos = instance_info
        break 

    return manager_infos  

# Function to measure the ping time to a worker instance
def measure_worker_ping_time(worker_ip_adress, timeout=2):
    try:
        # Measure ping time using the ping3 library
        response = ping3.ping(worker_ip_adress, timeout=timeout)
        
        if response is not None:
            return response
    except Exception as e:
        print(f"Error while pinging {worker_ip_adress}: {e}")
    
    # Return a high value if ping fails
    return float('inf')

# Function to select the worker instance with the least response time
def select_worker_with_least_response_time(workers):
    min_ping_time = float('inf')
    selected_worker = None
    
    for worker in workers:
        worker_ip_address = worker['PublicIpAddress']
        ping_time = measure_worker_ping_time(worker_ip_address)
        
        if ping_time < min_ping_time:
            min_ping_time = ping_time
            selected_worker = worker
    
    return selected_worker

# Function to get a random worker instance
def get_random_worker(workers):
    if not workers:
        return None
    return random.choice(workers)

# Function to extract the public IP addresses from a list of instances
def extract_workers_ip_adresses(instances):
    ips=[]
    for instance in instances:
        ips.append(instance["PublicIpAddress"])   
    return ips

# Function to establish an SSH tunnel to a worker instance
def establish_tunnel(worker_ip, manager_ip):
    app.logger.info(f"Manager IP: {manager_ip}")
    app.logger.info(f"Worker IP: {worker_ip}")
    return SSHTunnelForwarder(worker_ip, ssh_username="ubuntu", ssh_pkey="my_key.pem", remote_bind_address=(manager_ip, 3306))

# Function to execute an SQL query through the established SSH tunnel
def execute_sql_query(tunnel, query,manager_ip):
    with tunnel:
        conn = pymysql.connect(
            host=manager_ip,
            port=3306,
            user='root',
            password='',
            database='sakila',
            autocommit=True
        )

        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        conn.close()

    return result

# Function to establish an SSH tunnel to the manager instance
def direct_hit():
    manager_ip = get_manager_public_ip().get('PublicIpAddress')
    tunnel = establish_tunnel(manager_ip, manager_ip)
    return tunnel

# Function to establish an SSH tunnel to a random worker instance
def random_node():
    workers = get_instances_public_ips("Worker")
    random_worker_ip = get_random_worker(workers).get('PublicIpAddress')
    manager_ip = get_manager_public_ip().get('PublicIpAddress')
    tunnel = establish_tunnel(random_worker_ip, manager_ip)
    return tunnel

# Function to establish an SSH tunnel to the fastest worker instance
def customized_node():
    workers = get_instances_public_ips("Worker")
    fastest_worker_ip = select_worker_with_least_response_time(workers).get('PublicIpAddress')
    manager_ip = get_manager_public_ip().get('PublicIpAddress')
    tunnel = establish_tunnel(fastest_worker_ip, manager_ip)
    return tunnel

# Route to check the health of the proxy
@app.route("/health", methods=['GET'])
def health():
    return jsonify({"status": "healthy"})

# Route to handle SQL queries based on the query_type parameter
@app.route('/query', methods=['GET'])
def query():
    # Get query_type parameter from the request
    query_type = request.args.get('query_type')

    # Determine the type of query based on the query_type parameter
    if query_type == 'direct_hit':
        tunnel = direct_hit()
    elif query_type == 'random':
        tunnel = random_node()
    elif query_type == 'customized':
        tunnel = customized_node()
    else:
        return jsonify({'error': 'Invalid query type'}), 400
    
    # Get SQL query parameter from the request
    sql_query = request.args.get('query')

    # Check if SQL query is provided
    if not sql_query:
        return jsonify({'error': 'No SQL query provided'}), 400

    # Get the manager's public IP address
    manager_ip = get_manager_public_ip().get('PublicIpAddress')

    try:
        # Execute SQL query through the established SSH tunnel
        result = execute_sql_query(tunnel, sql_query, manager_ip)
        print(result)
        return jsonify(
            {"Message": f"Query of type '{query_type}' was executed successfully", "Query Result": result, "Manager IP": manager_ip, "Used worker IP": tunnel.ssh_host})
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        # Close the SSH tunnel
        tunnel.close()

# Run the Flask application
if __name__ == '__main__':
    app.logger.setLevel(logging.INFO)
    app.run(debug=True, host='0.0.0.0', port=80)

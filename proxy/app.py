import logging
import random

import boto3
import ping3
import pymysql
from aws_creds import AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY
from flask import Flask, jsonify, request
from sshtunnel import SSHTunnelForwarder

app = Flask(__name__)

client = boto3.client(
    service_name='ec2',
    region_name="us-east-1",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

used_manager_ip = ''
used_worker_ip = ''


def get_instances_public_ips(keyword):
    """
    Get information about the running EC2 instances with a specified keyword in the 'Name' tag.

    Args:
    - keyword (str): Keyword to search for in the 'Name' tag.

    Returns:
    - list: List of dictionaries containing 'Name' and 'PublicIpAddress' of matched instances.
    """
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


def get_manager_public_ip():
    """
    Retrieve the public IP address of the manager instance.

    Returns:
    - dict: Dictionary containing 'Name' and 'PublicIpAddress' of the manager instance.
    """
    manager_infos = {}
    instances_infos = get_instances_public_ips("Manager")

    for instance_info in instances_infos:
        manager_infos = instance_info
        break

    return manager_infos


def measure_worker_ping_time(worker_ip_address, timeout=2):
    """
    Measure the ping time to a worker instance.

    Args:
    - worker_ip_address (str): Public IP address of the worker instance.
    - timeout (int): Timeout for the ping operation.

    Returns:
    - float: Ping time to the worker instance.
    """
    try:
        response = ping3.ping(worker_ip_address, timeout=timeout)

        if response is not None:
            return response
    except Exception as e:
        print(f"Error while pinging {worker_ip_address}: {e}")

    return float('inf')


def select_worker_with_least_response_time(workers):
    """
    Select the worker instance with the least response time.

    Args:
    - workers (list): List of worker instances.

    Returns:
    - dict: Dictionary containing 'Name' and 'PublicIpAddress' of the selected worker instance.
    """
    min_ping_time = float('inf')
    selected_worker = None

    for worker in workers:
        worker_ip_address = worker['PublicIpAddress']
        ping_time = measure_worker_ping_time(worker_ip_address)

        if ping_time < min_ping_time:
            min_ping_time = ping_time
            selected_worker = worker

    return selected_worker


def get_random_worker(workers):
    """
    Get a random worker instance.

    Args:
    - workers (list): List of worker instances.

    Returns:
    - dict: Dictionary containing 'Name' and 'PublicIpAddress' of the selected worker instance.
    """
    if not workers:
        return None
    return random.choice(workers)


def establish_tunnel(worker_ip, manager_ip):
    """
    Establish an SSH tunnel to a worker instance.

    Args:
    - worker_ip (str): Public IP address of the worker instance.
    - manager_ip (str): Public IP address of the manager instance.

    Returns:
    - SSHTunnelForwarder: An SSHTunnelForwarder object representing the established tunnel.
    """
    app.logger.info(f"Manager IP: {manager_ip}")
    app.logger.info(f"Worker IP: {worker_ip}")
    return SSHTunnelForwarder(worker_ip, ssh_username="ubuntu", ssh_pkey="my_key.pem", remote_bind_address=(manager_ip, 3306))


def execute_sql_query(tunnel, query, manager_ip):
    """
    Execute an SQL query through the established SSH tunnel.

    Args:
    - tunnel (SSHTunnelForwarder): An SSHTunnelForwarder object representing the established tunnel.
    - query (str): SQL query to execute.
    - manager_ip (str): Public IP address of the manager instance.

    Returns:
    - any: Result of the SQL query.
    """
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


def direct_hit():
    """
    Establish an SSH tunnel to the manager instance.

    Returns:
    - SSHTunnelForwarder: An SSHTunnelForwarder object representing the established tunnel.
    """
    manager_ip = get_manager_public_ip().get('PublicIpAddress')
    tunnel = establish_tunnel(manager_ip, manager_ip)
    return tunnel


def random_node():
    """
    Establish an SSH tunnel to a random worker instance.

    Returns:
    - SSHTunnelForwarder: An SSHTunnelForwarder object representing the established tunnel.
    """
    workers = get_instances_public_ips("Worker")
    random_worker_ip = get_random_worker(workers).get('PublicIpAddress')
    manager_ip = get_manager_public_ip().get('PublicIpAddress')
    tunnel = establish_tunnel(random_worker_ip, manager_ip)
    return tunnel


def customized_node():
    """
    Establish an SSH tunnel to the fastest worker instance.

    Returns:
    - SSHTunnelForwarder: An SSHTunnelForwarder object representing the established tunnel.
    """
    workers = get_instances_public_ips("Worker")
    fastest_worker_ip = select_worker_with_least_response_time(workers).get('PublicIpAddress')
    manager_ip = get_manager_public_ip().get('PublicIpAddress')
    tunnel = establish_tunnel(fastest_worker_ip, manager_ip)
    return tunnel


@app.route("/health", methods=['GET'])
def health():
    """
    Route to check the health of the proxy.

    Returns:
    - JSON: JSON response indicating the health status.
    """
    return jsonify({"status": "proxy healthy"})


@app.route('/query', methods=['GET'])
def query():
    """
    Route to handle SQL queries based on the query_type parameter.

    Returns:
    - JSON: JSON response containing the result of the SQL query and additional information.
    """
    query_type = request.args.get('query_type')

    if query_type == 'direct_hit':
        tunnel = direct_hit()
    elif query_type == 'random':
        tunnel = random_node()
    elif query_type == 'customized':
        tunnel = customized_node()
    else:
        return jsonify({'error': 'Invalid query type'}), 400

    sql_query = request.args.get('query')

    if not sql_query:
        return jsonify({'error': 'No SQL query provided'}), 400

    manager_ip = get_manager_public_ip().get('PublicIpAddress')

    try:
        result = execute_sql_query(tunnel, sql_query, manager_ip)
        return jsonify(
            {"Message": f"Query of type '{query_type}' was executed successfully", "Query Result": result,
             "Manager IP": manager_ip, "Used worker IP": tunnel.ssh_host})
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        tunnel.close()


if __name__ == '__main__':
    app.logger.setLevel(logging.INFO)
    app.run(debug=True, host='0.0.0.0', port=80)

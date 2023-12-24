from flask import Flask, request, jsonify
from aws_creds import AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN
from sshtunnel import SSHTunnelForwarder
import pymysql
import ping3
import random
import boto3

app = Flask(__name__)


client= boto3.client(
        service_name='ec2',
        region_name="us-east-1",
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_session_token=AWS_SESSION_TOKEN
    )

# # MySQL Cluster configuration
# cluster_nodes = [
#     {"host": "172.31.40.75", "port": 3306},
#     {"host": "172.31.35.48", "port": 3306},
#     {"host": "172.31.43.247", "port": 3306},
#     {"host": "172.31.33.114", "port": 3306}
# ]

# manager_ip= "172.31.40.75",
workers_private_ip= ["172.31.40.48","172.31.43.247", "172.31.33.114"]
# connection_port = "3306"

# # SSH tunnel configuration
# ssh_config = {
#     'ssh_address_or_host': ('proxy-ip', 22),
#     'ssh_username': 'your-ssh-username',
#     'ssh_password': 'your-ssh-password',
#     'remote_bind_address': ('127.0.0.1', 3306),
#     'local_bind_address': ('', 3307)  # You can choose any available local port
# }

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


def get_manager_public_ip():
    manager_infos = {}
    instances_infos = get_instances_public_ips("Manager")

    for instance_info in instances_infos:
        manager_infos = instance_info
        break 

    return manager_infos  
    
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

def get_random_worker(workers):
    if not workers:
        return None
    return random.choice(workers)


def extract_workers_ip_adresses(instances):
    ips=[]
    for instance in instances:
        ips.append(instance["PublicIpAddress"])   
    return ips

def extrac_manager_ip_adress(instance):
    return instance["PublicIpAddress"]

@app.route('/direct_hit', methods=['GET'])
def direct_hit():
    workers = get_instances_public_ips("Worker")
    workers_ip = extract_workers_ip_adresses(workers)
    worker_ip = str(workers_ip[0])
    print(str(worker_ip))
    manager = get_manager_public_ip()
    

    print(manager.get('PublicIpAddress'))
    with SSHTunnelForwarder((worker_ip,22), ssh_username="ubuntu", ssh_pkey="ssh_tunnel_key.pem", remote_bind_address=(manager.get("PublicIpAdress"),3306)) as tunnel:
        conn = pymysql.connect(
            host=get_manager_public_ip(),
            port=3306,
            user='root',
            password='',
            database='sakila',
            autocommit=True
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM payment;")
        result = cursor.fetchall()
        conn.close()
        return jsonify({"result": "Direct Hit Success", "data": result})

# @app.route('/random', methods=['GET', 'POST'])
# def random_proxy():
#     random_worker_ip = get_random_worker_ips()
#     with SSHTunnelForwarder(**ssh_config) as tunnel:
#         conn = pymysql.connect(
#             host=random_worker_ip,
#             port=connection_port,
#             user='root',
#             password='',
#             database='sakila'
#         )

#         # Implement your logic for random selection here
#         # Randomly choose a node for both write and read requests
#         nodes = cluster_nodes
#         chosen_node = random.choice(nodes)

#         cursor = conn.cursor()
#         cursor.execute("INSERT INTO your_table (column1, column2) VALUES (%s, %s)", ("value1", "value2"))
#         conn.commit()

#         cursor.execute("SELECT * FROM your_table")
#         result = cursor.fetchall()

#         conn.close()
#         return jsonify({"result": "Random Proxy Success", "data": result})

# @app.route('/customized', methods=['GET', 'POST'])
# def customized_proxy():
#     with SSHTunnelForwarder(**ssh_config) as tunnel:
#         conn = pymysql.connect(
#             host='127.0.0.1',
#             port=tunnel.local_bind_port,
#             user='your-mysql-username',
#             password='your-mysql-password',
#             database='your-database-name'
#         )

#         # Implement your logic for customized selection here
#         nodes = cluster_nodes
#         ping_times = {node["host"]: ping3.ping(node["host"]) for node in nodes}
#         chosen_node = min(ping_times, key=ping_times.get)

#         cursor = conn.cursor()
#         cursor.execute("INSERT INTO your_table (column1, column2) VALUES (%s, %s)", ("value1", "value2"))
#         conn.commit()

#         cursor.execute("SELECT * FROM your_table")
#         result = cursor.fetchall()

#         conn.close()
#         return jsonify({"result": "Customized Proxy Success", "data": result})

# @app.route('/query', methods=['POST'])
# def query():
#     query_type = request.json.get('type')

#     if query_type == 'direct_hit':
#         connection = direct_hit()
#     elif query_type == 'random':
#         connection = random_node()
#     elif query_type == 'customized':
#         connection = customized_node()
#     else:
#         return jsonify({'error': 'Invalid query type'}), 400

#     # Execute your SQL query here using 'connection'

#     connection.close()
#     return jsonify({'result': 'Query executed successfully'})
    
if __name__ == '__main__':
    # workers = get_workers_public_ips()
    # manager = get_manager_public_ip()
    # print("manager", manager)
    # print("workers", extract_workers_ip_adresses(workers))
    app.run(debug=True)
    
    # print("random", get_random_worker(workers))
    # print("fastest", select_worker_with_least_response_time(workers))
    
                 
              

    

    
    
    
    

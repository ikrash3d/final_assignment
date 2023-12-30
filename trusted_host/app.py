import requests
from aws_creds import AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY
from boto3 import client
from flask import Flask, jsonify, request
from sshtunnel import SSHTunnelForwarder

app = Flask(__name__)

ec2_client = client(
    service_name='ec2',
    region_name="us-east-1",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

def get_public_ip(keyword):
    """
    Get information about running EC2 instances with a specified keyword in the 'Name' tag.

    Args:
    - keyword (str): Keyword to search for in the 'Name' tag.

    Returns:
    - dict: Dictionary containing 'Name' and 'PublicDnsName' of the matched instance.
    """
    response = ec2_client.describe_instances()
    instance_infos = {}

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            if instance["State"]['Name'] == 'running':
                for tag in instance.get('Tags', []):
                    if tag.get("Key") == 'Name' and keyword in tag.get('Value'):
                        instance_name = tag.get('Value')
                        instance_infos = {"Name": instance_name, "PublicDnsName": instance.get("PublicDnsName")}
                      
    return instance_infos

def establish_tunnel():
    """
    Establish an SSH tunnel to the proxy instance.

    Returns:
    - SSHTunnelForwarder: An SSHTunnelForwarder object representing the established tunnel.
    """
    proxy_public_ip = get_public_ip("Proxy").get('PublicDnsName')
    return SSHTunnelForwarder((proxy_public_ip, 22), ssh_username="ubuntu", ssh_pkey="my_key.pem", remote_bind_address=(proxy_public_ip, 80))
     
def send_request_to_proxy(query_type, sql_query):
    """
    Send an HTTP GET request to a proxy instance through an SSH tunnel.

    Args:
    - query_type (str): Type of SQL query to execute.
    - sql_query (str): SQL query to execute.

    Returns:
    - str: Response text from the proxy instance.
    """
    proxy_public_ip = get_public_ip("Proxy").get('PublicDnsName')
    
    with establish_tunnel():
        return requests.get(f"http://{proxy_public_ip}/query?query_type={query_type}&query={sql_query}").text

@app.route('/health', methods=['GET'])
def health():
    """
    Endpoint to check the health status of the application.

    Returns:
    - JSON: JSON response indicating the health status.
    """
    return jsonify({'status': 'trusted host healthy'})

@app.route('/query', methods=['GET'])
def query():
    """
    Endpoint to execute SQL queries through an SSH tunnel to a proxy instance.

    Returns:
    - str: Response text from the proxy instance.
    """
    query_type = request.args.get('query_type')

    if query_type is None:
        return jsonify({'error': 'No query type provided'}), 400
    elif query_type not in ['direct_hit', 'random', 'customized']:
        return jsonify({'error': 'Invalid query type'}), 400
    
    sql_query = request.args.get('query')

    if not sql_query:
        return jsonify({'error': 'No SQL query provided'}), 400

    try:
        result = send_request_to_proxy(query_type, sql_query)
        return result
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        establish_tunnel().close()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=80)

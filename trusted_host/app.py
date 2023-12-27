import requests
from aws_creds import AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY
from boto3 import client
from flask import Flask, jsonify, request
from sshtunnel import SSHTunnelForwarder

app = Flask(__name__)

# Initialize AWS EC2 client
ec2_client = client(
    service_name='ec2',
    region_name="us-east-1",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

def get_public_ip(keyword):
    # Get information about EC2 instances
    response = ec2_client.describe_instances()
    instance_infos = {}

    # Loop through reservations and instances to find the one with the specified keyword
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            if instance["State"]['Name'] == 'running':
                for tag in instance.get('Tags', []):
                    if tag.get("Key") == 'Name' and keyword in tag.get('Value'):
                        instance_name = tag.get('Value')
                        instance_infos = {"Name": instance_name, "PublicDnsName": instance.get("PublicDnsName")}
                      
    return instance_infos

def establish_tunnel():
    # Get the public IP of the proxy instance
    proxy_public_ip = get_public_ip("Proxy").get('PublicDnsName')
    
    # Create an SSH tunnel to the proxy instance
    return SSHTunnelForwarder((proxy_public_ip, 22), ssh_username="ubuntu", ssh_pkey="my_key.pem", remote_bind_address=(proxy_public_ip, 80))
     
def send_request_to_proxy(query_type, sql_query):
    # Get the public IP of the proxy instance
    proxy_public_ip = get_public_ip("Proxy").get('PublicDnsName')
    
    # Use the established SSH tunnel to send a request to the proxy
    return requests.get(f"http://{proxy_public_ip}/query?query_type={query_type}&query={sql_query}").text

@app.route('/health', methods=['GET'])
def health():
    # Endpoint to check the health status of the application
    return jsonify({'status': 'trusted host healthy'})

@app.route('/query', methods=['GET'])
def query():
    # Get query_type parameter from the request
    query_type = request.args.get('query_type')

    if query_type is None:
        return jsonify({'error': 'No query type provided'}), 400
    elif query_type not in ['direct_hit', 'random', 'customized']:
        return jsonify({'error': 'Invalid query type'}), 400
    
    # Get SQL query parameter from the request
    sql_query = request.args.get('query')

    # Check if SQL query is provided
    if not sql_query:
        return jsonify({'error': 'No SQL query provided'}), 400

    try:
        # Execute SQL query through the established SSH tunnel
        result = send_request_to_proxy(query_type, sql_query)
        return result
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        # Close the SSH tunnel
        establish_tunnel().close()

if __name__ == "__main__":
    # Run the Flask application on 0.0.0.0:80
    app.run(debug=True, host='0.0.0.0', port=80)

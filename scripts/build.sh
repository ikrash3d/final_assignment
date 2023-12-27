# Change directory to the 'proxy' directory
cd ../proxy

# Display a message indicating that the Proxy is being built and pushed
echo "Building and pushing Proxy.."

# Build the Docker image for the Proxy and tag it as 'proxy:latest'
docker build -t proxy:latest .

# Tag the built Proxy image with the repository name 'ikrash3d/proxy:latest'
docker tag proxy:latest ikrash3d/proxy:latest

# Push the tagged Proxy image to the Docker registry 'ikrash3d/proxy:latest'
docker push ikrash3d/proxy:latest

# Change directory to the 'gatekeeper' directory
cd ../gatekeeper

# Display a message indicating that the Gatekeeper is being built and pushed
echo "Building and pushing Gatekeeper.."

# Build the Docker image for the Gatekeeper and tag it as 'gatekeeper:latest'
docker build -t gatekeeper:latest .

# Tag the built Gatekeeper image with the repository name 'ikrash3d/gatekeeper:latest'
docker tag gatekeeper:latest ikrash3d/gatekeeper:latest

# Push the tagged Gatekeeper image to the Docker registry 'ikrash3d/gatekeeper:latest'
docker push ikrash3d/gatekeeper:latest

# Change directory to the 'trusted_host' directory
cd ../trusted_host

# Display a message indicating that the Trusted Host is being built and pushed
echo "Building and pushing Trusted Host.."

# Build the Docker image for the Trusted Host and tag it as 'trusted_host:latest'
docker build -t trusted_host:latest .

# Tag the built Trusted Host image with the repository name 'ikrash3d/trusted_host:latest'
docker tag trusted_host:latest ikrash3d/trusted_host:latest

# Push the tagged Trusted Host image to the Docker registry 'ikrash3d/trusted_host:latest'
docker push ikrash3d/trusted_host:latest

# Display a message indicating that the building and pushing process is done
echo "Done building and pushing images!"

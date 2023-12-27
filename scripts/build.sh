cd ../proxy

echo "Building and pushing Proxy.."

docker build -t proxy:latest .

docker tag proxy:latest ikrash3d/proxy:latest

docker push ikrash3d/proxy:latest

cd ../gatekeeper

echo "Building and pushing Gatekeeper.."

docker build -t gatekeeper:latest .

docker tag gatekeeper:latest ikrash3d/gatekeeper:latest

docker push ikrash3d/gatekeeper:latest

cd ../trusted_host

echo "Building and pushing Trusted Host.."

docker build -t trusted_host:latest .

docker tag trusted_host:latest ikrash3d/trusted_host:latest

docker push ikrash3d/trusted_host:latest

echo "Done building and pushing images!"
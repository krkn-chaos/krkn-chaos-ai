
## Setup Virtual Environment

```
pip install uv
uv venv --python 3.9
source .venv/bin/activate

uv pip install -e .
```


## Deploying sample micro-service for testing Chaos AI

```
export DEMO_NAMESPACE=robot-shop
export IS_OPENSHIFT=true
./scripts/setup-demo-microservice.sh

oc config set-context --current --namespace=robot-shop

# To expose web services through nginx reverse-proxy
./scripts/setup-nginx.sh
```

## Running the Chaos AI CLI

```
# Set Prometheus reader parameters
export PROMETHEUS_URL=''
export PROMETHEUS_TOKEN=''

# Start chaos ai test
$ uv run chaos_ai run  --help
Usage: chaos_ai run [OPTIONS]

Options:
  -c, --config TEXT      Path to chaos ai config file.
  -k, --kubeconfig TEXT  Path to valid kubeconfig file.
  --help                 Show this message and exit.
```

## Running test with Chaos AI

```
$ uv run chaos_ai run -c config/robot-shop.yaml -o ./tmp/result/
```

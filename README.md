
## Setup Virtual Environment

```
pip install uv
uv venv --python 3.9
source .venv/bin/activate
```


## Deploying sample micro-service for testing Chaos AI

```
export DEMO_NAMESPACE=robot-shop
export IS_OPENSHIFT=true
./scripts/setup-demo-microservice.sh
```

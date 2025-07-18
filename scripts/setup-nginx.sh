#!/bin/bash

set -e
set -x

kubectl apply -f scripts/nginx/configmap.yaml
kubectl apply -f scripts/nginx/deployment.yaml
kubectl apply -f scripts/nginx/service.yaml

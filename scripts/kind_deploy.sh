#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python scripts/prepare_env.py
# Only these locally generated variables are read; .env is not executed as shell.
LAB_GRAFANA_PASSWORD="$(python -c 'from pathlib import Path; print(dict(x.split("=",1) for x in Path(".env").read_text().splitlines() if "=" in x)["GRAFANA_ADMIN_PASSWORD"])')"
if ! kind get clusters | grep -qx multicloud-lab; then
  kind create cluster --name multicloud-lab --config kubernetes/kind.yaml --image kindest/node:v1.32.2
fi
docker build -f docker/Dockerfile -t multicloud-lab-api:local .
kind load docker-image multicloud-lab-api:local --name multicloud-lab
kubectl --context kind-multicloud-lab apply -f kubernetes/namespace.yaml
kubectl --context kind-multicloud-lab -n multicloud-lab create secret generic grafana-admin --from-literal=password="$LAB_GRAFANA_PASSWORD" --dry-run=client -o yaml | kubectl --context kind-multicloud-lab apply -f -
kubectl --context kind-multicloud-lab apply -k .
kubectl --context kind-multicloud-lab -n multicloud-lab rollout status deployment/lab-api --timeout=180s
for service in prometheus loki grafana alertmanager; do
  kubectl --context kind-multicloud-lab -n multicloud-lab rollout status "deployment/$service" --timeout=180s
done

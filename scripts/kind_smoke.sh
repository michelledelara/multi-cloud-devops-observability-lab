#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p evidence/runtime
lab_pids=()
cleanup() { for pid in "${lab_pids[@]}"; do kill "$pid" 2>/dev/null || true; done; }
trap cleanup EXIT
for mapping in 'lab-api 8080:8080' 'prometheus 9090:9090' 'grafana 3000:3000'; do
  read -r service ports <<< "$mapping"
  kubectl --context kind-multicloud-lab -n multicloud-lab port-forward "svc/$service" "$ports" > "evidence/runtime/port-forward-$service.log" 2>&1 &
  lab_pids+=("$!")
done
python scripts/smoke.py

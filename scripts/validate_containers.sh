#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose config --quiet
docker run --rm --entrypoint promtool -v "$PWD/observability/prometheus:/etc/prometheus:ro" prom/prometheus:v3.5.0 check config /etc/prometheus/prometheus.yml
docker run --rm --entrypoint promtool -v "$PWD/observability/prometheus:/etc/prometheus:ro" prom/prometheus:v3.5.0 test rules /etc/prometheus/alerts.test.yml
docker run --rm -v "$PWD/observability/loki:/etc/loki:ro" grafana/loki:3.5.5 -config.file=/etc/loki/config.yml -verify-config=true
docker run --rm -v "$PWD/observability/alloy:/etc/alloy:ro" grafana/alloy:v1.10.2 validate /etc/alloy/config.alloy

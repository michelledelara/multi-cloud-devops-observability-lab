"""Exercise the API and verify metrics and logs reach the provisioned backends."""
import base64
import json
import os
from pathlib import Path
import time
import urllib.parse
import urllib.request

root = Path(__file__).resolve().parents[1]
settings = {}
if (root / ".env").exists():
    for line in (root / ".env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            settings[key] = value
password = os.environ.get("GRAFANA_ADMIN_PASSWORD", settings.get("GRAFANA_ADMIN_PASSWORD", ""))
if not password:
    raise SystemExit("Set GRAFANA_ADMIN_PASSWORD or run scripts/prepare_env.py first.")
api = os.environ.get("API_URL", "http://127.0.0.1:8080")
prom = os.environ.get("PROMETHEUS_URL", "http://127.0.0.1:9090")
grafana = os.environ.get("GRAFANA_URL", "http://127.0.0.1:3000")
auth = base64.b64encode(f"admin:{password}".encode()).decode()


def get(url, authenticated=False):
    headers = {"Authorization": f"Basic {auth}"} if authenticated else {}
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=5) as response:
        return json.load(response)


def eventually(name, operation, timeout=120):
    until = time.monotonic() + timeout
    last = "no result"
    while time.monotonic() < until:
        try:
            value = operation()
            if value:
                print(f"PASS: {name}", flush=True)
                return value
            last = "empty result"
        except Exception as error:
            last = str(error)
        time.sleep(2)
    raise SystemExit(f"FAIL: {name}: {last}")


eventually("API readiness", lambda: get(api + "/readyz")["status"] == "ready")
for _ in range(10):
    get(api + "/work?delay_ms=10")
eventually("Grafana health", lambda: get(grafana + "/api/health")["database"] == "ok")
query = urllib.parse.urlencode({"query": 'sum(lab_http_requests_total{job="lab-api",route="/work"})'})
eventually("Prometheus collected application metrics", lambda: any(
    float(row["value"][1]) >= 10 for row in get(prom + "/api/v1/query?" + query)["data"]["result"]))
query = urllib.parse.urlencode({"query": '{job="lab-api"} | json | route="/work"', "limit": 10})
eventually("Loki received structured application logs", lambda: get(
    grafana + "/api/datasources/proxy/uid/loki/loki/api/v1/query_range?" + query,
    authenticated=True)["data"]["result"])
print("API -> Prometheus and API -> Alloy -> Loki -> Grafana verified.")

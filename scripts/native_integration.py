"""Verify app -> Prometheus and app -> Alloy -> Loki with local Linux binaries.

Useful when a container daemon is unavailable. This does not validate containers.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import yaml

parser = argparse.ArgumentParser()
parser.add_argument("--tools-dir", type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
processes, logs = [], []


def fetch(url):
    with urllib.request.urlopen(url, timeout=3) as response:
        return response.read()


def wait_for(name, fn):
    last = None
    for _ in range(45):
        try:
            if fn():
                print("PASS:", name, flush=True)
                return
        except Exception as error:
            last = error
        time.sleep(1)
    raise RuntimeError(f"{name}: {last}")


with tempfile.TemporaryDirectory(prefix="multicloud-native-") as directory:
    tmp = Path(directory)
    def start(name, cmd, env=None):
        stream = (tmp / f"{name}.log").open("w")
        logs.append(stream)
        processes.append(subprocess.Popen(cmd, cwd=root, stdout=stream, stderr=stream, env=env))

    try:
        loki = yaml.safe_load((root / "observability/loki/config.yml").read_text())
        loki["server"].update(http_listen_address="127.0.0.1", http_listen_port=13100, grpc_listen_port=19095)
        loki["common"]["path_prefix"] = str(tmp / "loki")
        loki["common"]["instance_addr"] = "127.0.0.1"
        loki["common"]["storage"]["filesystem"] = {
            "chunks_directory": str(tmp / "loki/chunks"),
            "rules_directory": str(tmp / "loki/rules")}
        loki["compactor"]["working_directory"] = str(tmp / "loki/compactor")
        (tmp / "loki.yml").write_text(yaml.safe_dump(loki))
        prom = yaml.safe_load((root / "observability/prometheus/prometheus.yml").read_text())
        prom["global"] = {"scrape_interval": "1s", "evaluation_interval": "1s"}
        prom["rule_files"] = [str(root / "observability/prometheus/alerts.yml")]
        prom.pop("alerting")
        prom["scrape_configs"] = [{"job_name": "lab-api", "static_configs": [{"targets": ["127.0.0.1:8080"]}]}]
        (tmp / "prometheus.yml").write_text(yaml.safe_dump(prom))
        alloy = (root / "observability/alloy/config.alloy").read_text()
        alloy = alloy.replace("/var/log/lab/app.jsonl", str(tmp / "logs/app.jsonl"))
        alloy = alloy.replace("http://loki:3100", "http://127.0.0.1:13100")
        (tmp / "config.alloy").write_text(alloy)
        env = dict(os.environ, LOG_DIR=str(tmp / "logs"), ENABLE_FAULTS="true", HOSTNAME="native-api")
        start("api", [sys.executable, "-m", "app.main"], env)
        start("loki", [str(args.tools_dir / "loki"), f"-config.file={tmp / 'loki.yml'}"])
        start("prometheus", [str(args.tools_dir / "prometheus"), f"--config.file={tmp / 'prometheus.yml'}", f"--storage.tsdb.path={tmp / 'prometheus'}", "--web.listen-address=127.0.0.1:19090"])
        start("alloy", [str(args.tools_dir / "alloy"), "run", f"--storage.path={tmp / 'alloy'}", "--server.http.listen-addr=127.0.0.1:12345", str(tmp / "config.alloy")], env)
        wait_for("API ready", lambda: fetch("http://127.0.0.1:8080/readyz"))
        wait_for("Loki ready", lambda: fetch("http://127.0.0.1:13100/ready"))
        for _ in range(10):
            fetch("http://127.0.0.1:8080/work?delay_ms=5")
        try:
            fetch("http://127.0.0.1:8080/fail")
        except urllib.error.HTTPError as error:
            assert error.code == 500
        query = urllib.parse.urlencode({"query": 'sum(lab_http_requests_total{status="500"})'})
        wait_for("Prometheus collected controlled error", lambda: any(
            float(row["value"][1]) >= 1 for row in json.loads(fetch("http://127.0.0.1:19090/api/v1/query?" + query))["data"]["result"]))
        query = urllib.parse.urlencode({"query": '{job="lab-api"} | json | status=500'})
        wait_for("Alloy delivered error log to Loki", lambda: json.loads(fetch(
            "http://127.0.0.1:13100/loki/api/v1/query_range?" + query))["data"]["result"])
        print("Native integration passed: HTTP, metrics collection and structured log ingestion.")
    except Exception:
        for path in tmp.glob("*.log"):
            print(path.name, path.read_text()[-4000:])
        raise
    finally:
        for process in processes:
            process.terminate()
        for process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        for stream in logs:
            stream.close()

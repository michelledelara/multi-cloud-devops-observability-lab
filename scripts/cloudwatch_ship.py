"""Send a bounded JSONL log file to an existing AWS lab log group via AWS CLI."""
import argparse
import json
import subprocess
import tempfile
from datetime import datetime, timezone

parser = argparse.ArgumentParser()
parser.add_argument("file", help="JSONL exported from the lab application")
parser.add_argument("--log-group", default="/multicloud-lab/api")
parser.add_argument("--region", required=True)
args = parser.parse_args()
stream = "manual-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
events = []
with open(args.file, encoding="utf-8") as source:
    for line in source:
        record = json.loads(line)
        events.append({"timestamp": int(datetime.fromisoformat(record["timestamp"]).timestamp()*1000), "message": line.strip()})
if not events:
    raise SystemExit("No events in input.")
if len(events) > 1000 or sum(len(e["message"].encode())+26 for e in events) > 900_000:
    raise SystemExit("Use up to 1000 events and 900 KB per lab upload.")
events.sort(key=lambda e: e["timestamp"])
command = ["aws", "logs", "--region", args.region]
subprocess.run(command + ["create-log-stream", "--log-group-name", args.log_group, "--log-stream-name", stream], check=True)
with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8") as payload:
    json.dump(events, payload)
    payload.flush()
    subprocess.run(command + ["put-log-events", "--log-group-name", args.log_group, "--log-stream-name", stream, "--log-events", "file://" + payload.name], check=True)
print(f"Uploaded {len(events)} events to {args.log_group}/{stream}")

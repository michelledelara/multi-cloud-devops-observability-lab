"""Bounded traffic generator for an explicitly selected lab endpoint."""
import argparse
import concurrent.futures
import json
import time
import urllib.error
import urllib.request
from collections import Counter

parser = argparse.ArgumentParser()
parser.add_argument("--url", default="http://127.0.0.1:8080")
parser.add_argument("--mode", choices=["normal", "errors", "slow"], default="normal")
parser.add_argument("--seconds", type=int, default=60)
parser.add_argument("--workers", type=int, default=2)
args = parser.parse_args()
if not 1 <= args.seconds <= 600 or not 1 <= args.workers <= 8:
    parser.error("Use 1-600 seconds and 1-8 workers.")
endpoint = {"normal": "/work?delay_ms=20", "errors": "/fail", "slow": "/work?delay_ms=900"}[args.mode]
deadline = time.monotonic() + args.seconds


def worker(_):
    result = Counter()
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(args.url.rstrip("/") + endpoint, timeout=5) as response:
                result[str(response.status)] += 1
        except urllib.error.HTTPError as error:
            result[str(error.code)] += 1
        except (OSError, TimeoutError):
            result["connection_error"] += 1
        time.sleep(.1)
    return result


with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
    counts = sum(pool.map(worker, range(args.workers)), Counter())
print(json.dumps({"mode": args.mode, "seconds": args.seconds, "responses": counts}, indent=2))
if counts.get("connection_error") or counts.get("403"):
    raise SystemExit("Traffic did not complete as requested; inspect connectivity or ENABLE_FAULTS.")

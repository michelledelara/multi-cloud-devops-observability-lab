# Incident runbooks

Run scenarios against your local lab. Preserve the observed timestamps, command outputs and relevant log excerpts in `evidence/runtime/` if you need a record.

## API unavailable

**Detection:** `ApiTargetDown` or `ApiTargetsMissing`; missing responses or Prometheus target failure.

Controlled Compose incident:

```bash
docker compose stop api
```

Inspect Prometheus **Status → Target health**, the Alerts page and `docker compose ps`. A known target becomes down; in Kubernetes, deleting all replicas can instead remove discovered targets and activate the missing-target rule.

```bash
docker compose logs --tail=50 api prometheus
docker compose start api
python scripts/smoke.py
```

**Recovery criterion:** readiness returns 200, target `up` returns 1, telemetry arrives and the firing alert resolves. Recovery is not established solely by a running container status.

## High error rate

Set `ENABLE_FAULTS=true` in `.env`, then:

```bash
docker compose up -d --force-recreate api
python scripts/traffic.py --mode errors --seconds 240
```

This produces controlled HTTP 500 responses. Check `HighErrorRate`, the dashboard error ratio and `{job="lab-api"} | json | status >= 500`. Use `X-Request-ID` to locate a specific failed request in logs.

Restore `ENABLE_FAULTS=false`, then:

```bash
docker compose up -d --force-recreate api
python scripts/traffic.py --mode normal --seconds 180
```

**Recovery criterion:** the failure endpoint returns 403, business requests return 200, and the error alert resolves after its evaluation window. The temporary 500s are an injected application response, not an infrastructure outage.

## High latency

```bash
python scripts/traffic.py --mode slow --seconds 300
```

The API intentionally waits 900 ms before responding. Inspect p95, active requests, CPU and logs; a wait-heavy workload can have high latency without high CPU.

```bash
python scripts/traffic.py --mode normal --seconds 180
```

**Recovery criterion:** new requests complete normally and the p95/alert return below the threshold as old samples leave the two-minute window.

## Metrics missing

1. Request `/metrics` directly and look for `lab_http_requests_total` after business traffic.
2. Verify Prometheus target discovery, network reachability, named ports and job labels.
3. In Kubernetes, check the Prometheus service account and its Pod discovery Role.
4. Allow at least two scrapes for `rate()`; inspect the raw counter before changing queries.

## Logs missing

```bash
docker compose logs --tail=100 alloy loki
docker compose exec api sh -c 'ls -l /var/log/lab; tail -n 3 /var/log/lab/app.jsonl'
```

Verify the shared volume, readable file permissions, Alloy's path targets and Loki's readiness. In Kubernetes, inspect the Alloy container in the same API Pod. The dashboard queries job `lab-api`; changing labels requires updating queries. No Docker socket access is required by this collection model.

## Deployment does not become ready

Check image availability, config/Secret references, resource scheduling and probe responses. For kind, confirm that the local image was loaded into the named cluster. `ImagePullBackOff` is different from an application readiness failure; inspect events before changing code.

## Evidence record

Use `evidence/incident-template.md` to record symptoms, timeline, commands, root cause, corrective action and verification. Fill it from an actual run; the template intentionally contains no invented incident result.

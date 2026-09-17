# Observability model

## Metric contract

| Metric | Type | Meaning |
|---|---|---|
| `lab_http_requests_total` | Counter | Completed business requests, labeled by method, route template and status |
| `lab_http_request_duration_seconds` | Histogram | Request duration in seconds |
| `lab_http_requests_in_progress` | Gauge | Active business requests |
| `process_cpu_seconds_total` | Counter | API process CPU time |
| `process_resident_memory_bytes` | Gauge | API process resident memory |

Probe and scrape traffic is excluded. Unknown routes share `unmatched`; arbitrary URLs and query values do not become metric labels. The request ID exists in logs and response headers, not in labels. Process metrics depend on the Linux runtime; run the supplied Linux container for consistency.

The active-request panel is a saturation proxy. It is not a measurement of node capacity or a complete cluster saturation model. The application is served by one Gunicorn worker with four threads; the process metrics describe that application worker.

## PromQL

Traffic:

```promql
sum(rate(lab_http_requests_total{job="lab-api"}[2m]))
```

Server-error ratio:

```promql
(sum(rate(lab_http_requests_total{job="lab-api",status=~"5.."}[2m])) or vector(0))
/
clamp_min(sum(rate(lab_http_requests_total{job="lab-api"}[2m])), 0.001)
```

p95 latency, aggregating histogram buckets across replicas:

```promql
histogram_quantile(0.95,
  sum by (le) (rate(lab_http_request_duration_seconds_bucket{job="lab-api"}[2m]))
)
```

Counters restart when the process restarts; `rate()` handles resets. Histogram estimates depend on bucket boundaries. When traffic exists but no 5xx series has been created, the error numerator defaults to zero. With no traffic samples, rate-based panels can still show no data. Health and telemetry endpoints are not counted.

## JSON logs and LogQL

An event contains timestamp, level, service, environment, method, route, status, duration_ms and request_id. Bodies, authorization headers and query strings are not logged.

```logql
{job="lab-api"} | json
```

```logql
{job="lab-api"} | json | status >= 500
```

```logql
{job="lab-api"} | json | duration_ms > 500
```

```logql
{job="lab-api"} | json | request_id="REPLACE_WITH_RESPONSE_REQUEST_ID"
```

Alloy labels streams by job and instance; JSON fields are parsed at query time. This keeps request IDs and arbitrary request content out of Loki's indexed labels. Log files rotate at approximately 5 MB with three backups. Loki retention is 24 hours; API log rotation and backend retention are separate controls.

## Alert semantics

| Rule | Condition | Persistence |
|---|---|---|
| ApiTargetDown | A known target has `up == 0` | 1 minute |
| ApiTargetsMissing | No `up` series exists for the API job | 1 minute |
| HighErrorRate | 5xx ratio >5%, with traffic >0.1 requests/sec | 1 minute |
| HighLatency | p95 >500 ms, with traffic >0.1 requests/sec | 2 minutes |

The error and latency calculations use a two-minute range; the `for` window is additional persistence, not the range-vector duration. The thresholds are explicit laboratory operating criteria. They do not assert measured production reliability or a contractual SLA.

Alertmanager receives and groups alerts, visible at port 9093. The `local-observation` receiver deliberately has no external notification destination. Adding email, Slack or a webhook requires your own credentials and explicit destination configuration. Grafana displays the data; alert evaluation in this implementation is owned by Prometheus.

`alerts.test.yml` verifies sustained failure, healthy target behavior, the low-volume guard and high latency. Run via `scripts/validate_containers.sh` or `promtool test rules observability/prometheus/alerts.test.yml`.

## CloudWatch

CloudFormation defines a log group, JSON metric filter, alarm and dashboard. `scripts/cloudwatch_ship.py` provides a manual event ingestion path; it does not claim continuous collection from your workstation. CloudWatch metrics and Prometheus metrics have separate storage and evaluation semantics. The CloudWatch alarm uses an absolute error count, while the local Prometheus alert uses an error ratio.

## Tracing

Request IDs support log correlation. Distributed tracing is not implemented by this service and request IDs are not presented as traces.

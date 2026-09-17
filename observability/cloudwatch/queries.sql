-- Select the /multicloud-lab/api log group in CloudWatch Logs Insights.
fields @timestamp, service, route, status, duration_ms, request_id
| filter status >= 500
| sort @timestamp desc
| limit 100

-- Run separately: latency and volume by route.
-- fields route, duration_ms
-- | stats count(*) as requests, pct(duration_ms, 95) as p95_ms by route, bin(5m)

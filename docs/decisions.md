# Architecture decision records

## ADR-001: Independent cloud foundations

**Decision:** represent AWS, Azure and OCI through independent network definitions and state lifecycles.

**Reason:** network and identity semantics differ across providers. Separate lifecycles make plans understandable and prevent an unrelated cloud change from sharing a state lock. Non-overlapping CIDRs leave room for deliberate connectivity design.

**Consequence:** cloud applies do not deploy the local Kubernetes workload or establish inter-cloud connectivity.

## ADR-002: One portable instrumented service

**Decision:** use a stateless Python HTTP API with explicit metrics, JSON logs, probes and opt-in fault injection.

**Reason:** the same behavior can be compared across container execution, orchestration and observability tools without business-domain complexity.

**Consequence:** all generated metrics are laboratory traffic. Performance and reliability numbers require a documented workload and an actual measured run.

## ADR-003: Grafana Alloy file collection

**Decision:** tail rotating application files with Alloy and send them to Loki. In Kubernetes, colocate a collector sidecar with each API Pod.

**Reason:** collection requires no host filesystem mount or Docker socket. Grafana identifies Alloy as the successor for the discontinued Promtail collector.

**Consequence:** log positions and files share the Pod lifecycle in the Kubernetes lab. Logs not shipped before Pod deletion can be lost.

## ADR-004: One worker, horizontal replicas

**Decision:** use one Gunicorn worker with four threads per API container, scaling through Pods.

**Reason:** the default Prometheus Python registry is process-local. A single process makes metric semantics explicit without multiprocess aggregation.

**Consequence:** scaling process count inside a container requires changing the instrumentation strategy.

## ADR-005: Prometheus owns alerts

**Decision:** evaluate alert rules in Prometheus, group them in Alertmanager, and use Grafana for exploration and dashboards.

**Reason:** alert rules are versioned next to their tests and are consistent in Compose and Kubernetes.

**Consequence:** external delivery destinations are configured separately. A visible firing alert does not imply a notification was sent.

## ADR-006: Shared observability configuration

**Decision:** use common files for Compose and Kubernetes; Kustomize generates ConfigMaps from those files. Only the Prometheus discovery configuration differs by target.

**Reason:** storage queries, dashboards and alert rules should not drift between execution environments.

**Consequence:** configuration hashes trigger Kubernetes rollouts. Old unreferenced generated ConfigMaps can be removed during intentional namespace cleanup.

## ADR-007: Explicit cloud execution

**Decision:** CI validates infrastructure definitions while cloud plans/applies use an operator's authenticated session.

**Reason:** schema validation is useful without cloud credentials. Cloud changes should be reviewed against the actual account state and permissions.

**Consequence:** local validation and cloud deployment evidence are recorded separately.

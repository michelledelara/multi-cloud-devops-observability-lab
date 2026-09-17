# Security and operations

## Controls in the implementation

- The API runs as UID/GID 10001, without added capabilities and with a read-only root filesystem.
- Writable application paths are explicit: logs and a temporary directory.
- Compose binds workstation interfaces to loopback. Loki and Alloy use the internal container network.
- Kubernetes services use ClusterIP and interactive access uses local port forwarding.
- API Pods do not receive Kubernetes API tokens. Prometheus has namespace-scoped Pod discovery access.
- Fault injection is disabled by default and is enabled explicitly for a scenario.
- Secrets, real tfvars, private keys, state and saved plans are ignored by Git.
- Request bodies, authorization headers and query strings are absent from the structured log contract.
- JSON log rotation, Prometheus retention and Loki retention bound local data accumulation.

## Operating boundaries

The API is a lab service without application authentication or TLS termination. Compose loopback access and Kubernetes port forwards are its intended entry points. Exposing it through an external ingress requires an explicit authentication, TLS and access-control design. Loki has authentication disabled on its internal endpoint; do not publish it directly to a public network.

A Kubernetes Secret is an API object, not encryption by itself. Encryption at rest, cluster access and secret rotation belong to the hosting environment. The repository never commits the Grafana password.

Cloud network security groups/lists are scoped to each cloud's address space. They do not create encryption or connectivity between clouds. The AWS and OCI foundations have no internet egress route. Azure keeps its default outbound NSG behavior; outbound connectivity also depends on deployed compute and platform networking choices.

## Updates

Versions are intentionally pinned for reproducible configuration. Pins are not a statement that a release is the newest or free of vulnerabilities. Review vendor advisories, dependency update PRs and image scan results when operating or publishing a release. Update duplicate runtime image references in Compose and Kubernetes together, then rerun config and integration tests.

## Data and teardown

Compose volumes persist until removed with `down -v`. Kubernetes telemetry uses emptyDir and is discarded with Pod replacement. CloudWatch stores seven days of logs, and deleting the supplied stack deletes its log group. Choose where to retain evidence before teardown.

## Configuration management

Ansible writes environment and metadata files to `.lab-managed/` by default. This is an actual idempotent configuration operation and does not imply Docker or packages were installed on a remote host. To target a VM, provide an owned host in inventory, an SSH user and an appropriate `lab_config_dir`. Manage credentials outside inventory and use Ansible Vault for encrypted variables when necessary.

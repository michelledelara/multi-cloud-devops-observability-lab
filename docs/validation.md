# Validation record

This record distinguishes executed checks from deployment procedures. It contains no claimed cloud deployment, hosted pipeline run or production benchmark.

## Executed checks

| Check | Result |
|---|---|
| Python application behavior | 6 tests passed |
| Invalid/nonfinite delay input | Rejected with HTTP 400 |
| Fault injection opt-in | Disabled endpoint returns 403; enabled endpoint returns 500 |
| Metric cardinality and probe exclusions | Passed |
| JSON log contract and query-string exclusion | Passed |
| YAML/JSON/HCL parsing and config references | Passed |
| Docker Compose default configuration | `config --quiet` passed |
| GitLab Compose override | Merged `config --quiet` passed |
| Kubernetes manifests | `kubectl kustomize .` rendered successfully |
| CloudFormation schema | `cfn-lint` passed |
| Terraform formatting | `terraform fmt -check -recursive` passed |
| Prometheus Compose and Kubernetes configurations | `promtool check config` passed |
| Prometheus alert behavior | 5 rule test scenarios passed |
| Loki configuration | Native `-verify-config=true` passed |
| Alloy configuration | Native `validate` passed |
| Ansible syntax and execution | Passed; second run `changed=0`, `failed=0` |
| Bash script syntax | Passed |
| Native integration | Live API error metric collected by Prometheus; error log delivered by Alloy to Loki |

The native integration ran actual application, Prometheus, Alloy and Loki processes on loopback interfaces. Test-only configuration adjusted hostnames, local paths, ports and scrape intervals. Production of synthetic request traffic is part of the test; the collection result is observed, not simulated. Grafana and Alertmanager were not part of that native integration.

## Execution-dependent checks

| Check | Execution context |
|---|---|
| Docker image build and complete Compose runtime | Requires a Docker daemon; covered by the supplied CI jobs and smoke script |
| Kubernetes API validation and running Pods | Requires kind/Docker; supplied GitHub integration job performs server dry-run, rollout and telemetry smoke checks |
| Azure provider schema validation | Provider was downloaded, but this authoring runtime rejected the provider's Unix-domain socket; run `terraform validate` in a normal terminal or CI |
| OCI provider schema validation | Provider initialization was not completed in this runtime; run init/validate in a normal terminal or CI |
| Azure/OCI plan, apply and destroy | Requires an authenticated account and review of actual resource changes |
| AWS stack creation and CloudWatch ingestion | Requires an authenticated AWS account and explicit deployment/log upload |
| Hosted CI/CD and registry publication | Execute in the selected repository platform |
| Optional HPA | Requires a cluster with a functioning Metrics API |

No cloud resources were created while preparing this package. No repository was published and no image was pushed to a registry.

## Reproduction

```bash
python -m unittest discover -s tests -v
python scripts/check_config.py
cfn-lint cloudformation/aws/template.yaml
terraform fmt -check -recursive terraform
kubectl kustomize .
bash scripts/validate_containers.sh
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml
ansible-playbook -i ansible/inventory.ini ansible/playbook.yml
```

For an environment with Linux binaries and no Docker daemon, the native signal-path check is:

```bash
python scripts/native_integration.py --tools-dir /ABSOLUTE/PATH/TO/BINARIES
```

That directory must contain Prometheus 3.5.0, Alloy 1.10.2 and Loki 3.5.5 executable binaries. This test does not replace container or Kubernetes validation. It uses local ports 8080, 13100, 19090, 19095 and 12345, stops only its own processes and removes its temporary data.

After running your own deployment, record the commit, environment, command and output in `evidence/runtime/` or attach the hosted pipeline run. Use the incident template for actual recovery exercises.

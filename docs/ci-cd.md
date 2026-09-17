# Continuous integration and delivery

## Pipeline contract

A change is parsed, tested, built and exercised before its executable artifact is published. Repository CI does not use cloud credentials and does not run `terraform apply`.

| Stage | GitHub Actions | GitLab CI/CD | Azure Pipelines |
|---|---|---|---|
| Python tests / configuration / CloudFormation | Yes | Yes | Yes |
| Terraform fmt/init/validate | Matrix: Azure and OCI | Matrix: Azure and OCI | Loop: Azure and OCI |
| Ansible syntax | Yes | Yes | Yes |
| Ansible idempotence | Two runs | Execute locally or extend runner job | Two runs |
| Build and Compose integration | Yes | Yes | Yes |
| Native observability config checks in containers | Yes | Covered by local validator | Yes |
| Kubernetes deployment and smoke test | kind job | Local script supplied | Local script supplied |
| Registry publication | Separate manual GHCR workflow | Configure own registry integration | Configure own registry integration |

The pipeline definitions are executable templates for their respective services. A pipeline result exists only after it runs in that platform; configuration files alone are not evidence of a successful hosted run.

## GitHub Actions

`ci.yml` runs on push, pull request and manual dispatch. Infrastructure validation does not plan against an authenticated account. Integration jobs create isolated local environments on the runner and clean them up using always-run cleanup steps.

`publish.yml` runs only through **Actions → Publish API image to GHCR → Run workflow**. It tests, builds and publishes `ghcr.io/<owner>/<repository>:<commit-sha>` using the repository's package permission. Run and review the CI workflow for the same commit before publishing. Registry visibility and access follow your GitHub package settings. No release is created and no cloud cluster is mutated by this workflow.

Use immutable commit tags for selecting builds. For stricter release identity, resolve and pin the resulting image digest in the deployment manifest.

## GitLab CI/CD

The Docker-in-Docker job requires a runner configured for privileged DinD with TLS certificates shared at `/certs/client`. It uses a runner-only Compose override to expose application endpoints on the DinD service hostname. The default Compose file retains localhost-only host bindings for workstation use. Mount the build directory into the DinD service as required by your runner so Compose bind-mounted configuration files are accessible.

The repository does not modify runner administration settings. Use an isolated runner suitable for container integration jobs.

## Azure Pipelines

`azure-pipelines.yml` uses an Ubuntu hosted agent. UsePythonVersion selects Python 3.12 and Terraform is installed in a dedicated step. It validates IaC and runs the same Compose smoke script. Pull-request triggering depends on repository integration; Azure Repos commonly uses branch policies to trigger PR validation.

## Secrets and artifact boundaries

The local Grafana password is generated per environment. It is never uploaded as a CI artifact. Hosted CI does not require Azure, OCI or AWS account credentials for schema validation. The optional registry workflow uses the platform-provided token with package-write scope.

Failure artifacts contain Compose diagnostic logs. Avoid adding request secrets to logs. Dependency update configuration covers Python, the API Dockerfile, Actions and Terraform; manually review observability image pins in Compose/Kubernetes as part of updates.

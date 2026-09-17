# Kubernetes operations

## Deploy

Use kind v0.27.0 or a compatible version, kubectl compatible with Kubernetes 1.32, Docker and Bash. The supplied kind configuration has one control-plane node and one worker. It runs on your machine, without managed cloud cluster provisioning.

```bash
bash scripts/kind_deploy.sh
kubectl --context kind-multicloud-lab -n multicloud-lab get pods,deployments,services
bash scripts/kind_smoke.sh
```

The smoke script opens local port forwards, verifies telemetry and closes only its own forwards when complete. For interactive use, open separate terminals:

```bash
kubectl --context kind-multicloud-lab -n multicloud-lab port-forward svc/lab-api 8080:8080
kubectl --context kind-multicloud-lab -n multicloud-lab port-forward svc/prometheus 9090:9090
kubectl --context kind-multicloud-lab -n multicloud-lab port-forward svc/grafana 3000:3000
kubectl --context kind-multicloud-lab -n multicloud-lab port-forward svc/alertmanager 9093:9093
```

Use the same `.env` password as Compose. If the password changes, Grafana's existing database may retain the earlier password; follow Grafana's password reset procedure or intentionally reset the lab's ephemeral Grafana Pod.

## Configuration and identity

`kustomization.yaml` builds ConfigMaps from the same files used by Compose. Generated name hashes change when configuration changes, causing deployments referencing those ConfigMaps to roll out. The Grafana admin Secret is created separately and is not committed. The API's service-account token is not mounted.

Prometheus requires a service-account token for discovery and a namespace-scoped Role for Pods. It scrapes the named `http` port on every running API Pod. Running but unready Pods remain discoverable so target failure can still be observed.

## Scaling

```bash
kubectl --context kind-multicloud-lab -n multicloud-lab scale deployment lab-api --replicas=3
kubectl --context kind-multicloud-lab -n multicloud-lab get pods
```

A subsequent `kubectl apply -k .` restores the declared base replica count. The optional HPA is kept outside the base Kustomization because it requires the cluster's Metrics API.

After installing a compatible Metrics Server according to its official instructions, verify the API:

```bash
kubectl --context kind-multicloud-lab top pods -n multicloud-lab
kubectl --context kind-multicloud-lab apply -f kubernetes/hpa.yaml
kubectl --context kind-multicloud-lab -n multicloud-lab get hpa
```

The HPA targets **API container** CPU utilization relative to its 100m request, at 70%, with 2-5 replicas. Alloy CPU is excluded using a ContainerResource metric. Metrics Server and Prometheus serve different APIs; installing Prometheus alone does not satisfy the HPA. A delay-heavy HTTP request spends time sleeping, so the supplied slow-traffic scenario is not a CPU stress test and does not guarantee scale-out.

To return to fixed replicas:

```bash
kubectl --context kind-multicloud-lab -n multicloud-lab delete hpa lab-api
kubectl --context kind-multicloud-lab -n multicloud-lab scale deployment lab-api --replicas=2
```

## Update and rollback

```bash
docker build -f docker/Dockerfile -t multicloud-lab-api:v2 .
kind load docker-image multicloud-lab-api:v2 --name multicloud-lab
kubectl --context kind-multicloud-lab -n multicloud-lab set image deployment/lab-api api=multicloud-lab-api:v2
kubectl --context kind-multicloud-lab -n multicloud-lab rollout status deployment/lab-api
kubectl --context kind-multicloud-lab -n multicloud-lab rollout history deployment/lab-api
kubectl --context kind-multicloud-lab -n multicloud-lab rollout undo deployment/lab-api
```

For published images, replace the image reference with the commit-tagged registry image. A private registry requires an imagePullSecret configured outside source control. Reconcile the final image reference into version control after choosing the release.

## Diagnose

```bash
kubectl --context kind-multicloud-lab -n multicloud-lab describe deployment lab-api
kubectl --context kind-multicloud-lab -n multicloud-lab logs -l app=lab-api -c api --tail=50
kubectl --context kind-multicloud-lab -n multicloud-lab logs -l app=lab-api -c alloy --tail=50
kubectl --context kind-multicloud-lab -n multicloud-lab get events --sort-by=.metadata.creationTimestamp
```

For controlled failures, set `ENABLE_FAULTS=true` in the root Kustomization's `lab-app` literals and reapply. Restore `false` after the scenario.

## Teardown

```bash
kind delete cluster --name multicloud-lab
```

This removes the local cluster and all ephemeral telemetry in it.

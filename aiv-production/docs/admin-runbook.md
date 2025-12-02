## Admin Runbook – JupyterHub V1 (Local Auth)

### 1. Prerequisites

- Access to the target Kubernetes cluster (kubeconfig and context).
- `kubectl`, `helm`, and `docker` installed on the admin machine.
- Access to the container registry (e.g. `registry.example.com`).
- A Kubernetes cluster with sufficient CPU/RAM capacity and, if GPU workloads are required, NVIDIA GPU nodes with drivers and the NVIDIA device plugin installed.
- At least one default `StorageClass` (the manifests assume `standard` by default; adjust if your cluster uses a different name).
- A DNS name for JupyterHub (e.g. `jupyterhub-test.example.internal`) pointing at your ingress controller and a TLS certificate for that host (internal CA or Let’s Encrypt).
- (Recommended) A Prometheus + Grafana stack so that `infra/monitoring/servicemonitor.yaml` and `infra/monitoring/grafana-dashboard-v1.json` can be used for monitoring.

### 2. Build and Push the Base Notebook Image

From the `iav-jupyterhub` project root:

```bash
export REGISTRY="registry.example.com"
export IMAGE_NAME="iav/base-notebook"
export IMAGE_TAG="v1"
./scripts/build_base_image.sh
```

Update `infra/jupyterhub/values-v1.yaml` to reference the built image.

### 3. Configure Local Accounts

Edit `infra/jupyterhub/values-v1.yaml`:

- Set a strong password in `c.DummyAuthenticator.password`.
- Configure admin users in `c.Authenticator.admin_users`.

This password should be shared only with test users; rotate it regularly.

### 4. Deploy JupyterHub V1

From the project root:

```bash
./scripts/deploy_jhub_v1.sh
```

This script will:

- Create the `jupyterhub-test` namespace (if needed).
- Apply namespace/RBAC/storage manifests.
- Install/upgrade the JupyterHub Helm release.
- Apply ingress and ServiceMonitor manifests.

### 5. Validate Deployment

Run:

```bash
./scripts/smoke_test_v1.sh
```

Check:

- All JupyterHub pods are `Ready` in `jupyterhub-test`.
- `https://jupyterhub-test.example.internal` is reachable (certificate trusted or accepted).

### 6. User Management (V1)

- All testers authenticate with the shared password.
- Admins are listed in `values-v1.yaml`; changing admins requires a Helm upgrade.

To apply changes:

```bash
./scripts/deploy_jhub_v1.sh
```

### 7. Upgrading JupyterHub

To upgrade chart version or values:

1. Edit `infra/jupyterhub/values-v1.yaml` or the `CHART_VERSION` in `deploy_jhub_v1.sh`.
2. Run `./scripts/deploy_jhub_v1.sh`.

Helm performs a rolling update; sessions may restart depending on the change.

### 8. Rollback

To rollback to the previous version:

```bash
helm history jhub-v1 -n jupyterhub-test
helm rollback jhub-v1 <REVISION> -n jupyterhub-test
```

### 9. Logs and Monitoring

- Use `kubectl logs` on hub, proxy, and single-user pods for troubleshooting.
- Integrate the provided Grafana dashboard JSON into Grafana.
- Ensure Prometheus is scraping using `infra/monitoring/servicemonitor.yaml`.

### 10. Remove JupyterHub V1

To uninstall:

```bash
./scripts/delete_jhub_v1.sh
```

Optionally delete the namespace:

```bash
kubectl delete namespace jupyterhub-test
```

### 11. Entra ID (Azure AD) Integration – Preview

V1 uses local accounts for simplicity. To prepare for Entra ID (Azure AD / Entra ID) SSO on your lab cluster:

1. **Create an app registration in Entra ID** for JupyterHub:
   - Set the redirect URI to `https://<your-jupyterhub-host>/hub/oauth_callback`.
   - Note the **Tenant ID**, **Client ID**, and **Client Secret**.
2. **Ensure the hub image has `oauthenticator` installed.** The official JupyterHub Helm chart images normally include it; if using a custom hub image, add `pip install oauthenticator`.
3. **Edit `infra/jupyterhub/values-v1.yaml`:**
   - In `hub.extraConfig`, **comment out** the `00-local-auth` block.
   - **Uncomment** the `10-entra-id-auth-example` block and fill in your Tenant ID, Client ID, Client Secret, callback URL, and admin users.
4. **Redeploy JupyterHub**:

```bash
./scripts/deploy_jhub_v1.sh
```

After this change, users will authenticate via Entra ID instead of the shared local password.

### 12. Environment-Specific Configuration (Lab vs AIV)

To keep your lab setup close to AIV production while allowing easy migration:

- **Image registry and tag**: Set `REGISTRY`, `IMAGE_NAME`, and `IMAGE_TAG` when building/publishing the base image, and reference the same values under `singleuser.image` in `infra/jupyterhub/values-v1.yaml`.
- **Namespace and RBAC**: `infra/namespaces.yaml` currently uses `jupyterhub-test`; for AIV, clone and adjust the namespace name to match their standards.
- **Storage**: Update `storageClassName` and requested sizes in `infra/storage/pvc-home.yaml` to match the storage classes available in each environment (e.g. Ceph-backed classes at AIV).
- **Ingress**: Adjust the host and TLS secret in `infra/network/ingress.yaml` to the DNS name and certificate that will be used in each environment.
- **Deployment scripts**: Use environment variables such as `NAMESPACE` and `VALUES_FILE` when running `scripts/deploy_jhub_v1.sh` so the same script can target both your lab and the AIV clusters.

By keeping these settings isolated, you can validate everything on your on‑prem NVIDIA cluster and then switch to the client’s resources with minimal changes.



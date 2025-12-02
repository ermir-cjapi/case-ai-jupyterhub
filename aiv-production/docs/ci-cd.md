## CI/CD – JupyterHub V1

### 1. Overview

The GitLab CI pipeline builds the `base-notebook` image and can trigger a JupyterHub V1 deployment.

Files:

- `ci-cd/gitlab/.gitlab-ci.yml` – pipeline definition.
- `scripts/build_base_image.sh` – local build helper (can be mirrored in CI).
- `scripts/deploy_jhub_v1.sh` – deployment script used by the `deploy-jhub-v1` job.

### 2. Required GitLab Variables

Configure the following CI/CD variables in the GitLab project:

- `CI_REGISTRY`, `CI_REGISTRY_USER`, `CI_REGISTRY_PASSWORD` – standard GitLab registry variables.
- `REGISTRY` – e.g. `registry.example.com`.
- `KUBE_CONTEXT` – name of kubeconfig context used by `kubectl`.
- Kubernetes credentials (via GitLab Kubernetes integration or kubeconfig variables).

Adjust `REGISTRY`, `IMAGE_NAME`, and `IMAGE_TAG` in `.gitlab-ci.yml` to match your environment.

### 3. Pipeline Stages

1. `build-image`
   - Builds the `base-notebook` image from `images/base-notebook/Dockerfile`.
   - Pushes it to the configured registry.
2. `deploy-jhub-v1` (manual)
   - Uses `kubectl` and `scripts/deploy_jhub_v1.sh` to deploy to the cluster.

### 4. Typical Flow

1. Developer updates the Dockerfile or Helm values.
2. Push to `main` branch.
3. CI runs `build-image`.
4. An operator manually triggers `deploy-jhub-v1` after validation.

### 5. Environment-Specific Settings (Lab vs AIV)

To use the same pipeline for your on‑prem lab cluster and the AIV production cluster:

- Use different values for `REGISTRY`, `IMAGE_NAME`, and `IMAGE_TAG` per environment, or parameterize them via GitLab variables or protected branches.
- Configure `KUBE_CONTEXT` (and any required kubeconfig credentials) for each target cluster, so the `deploy-jhub-v1` job can point at either your lab cluster or the AIV cluster with the same script.
- Keep environment-specific Helm overrides (for example, different ingress hosts or storage classes) in separate values files and pass the appropriate `VALUES_FILE` via CI variables to `scripts/deploy_jhub_v1.sh`.

### 6. Using GitHub Actions Instead of GitLab (Optional)

If you prototype on GitHub before moving to AIV’s GitLab:

- Mirror the two stages (`build-image` and `deploy-jhub-v1`) as separate GitHub Actions workflows.
- Reuse `scripts/build_base_image.sh` and `scripts/deploy_jhub_v1.sh` so that only CI wiring differs between platforms.
- When migrating back to GitLab, you can keep the scripts unchanged and reattach them to the GitLab pipeline described above.



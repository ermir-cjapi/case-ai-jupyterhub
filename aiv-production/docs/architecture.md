## JupyterHub V1 Architecture – IAV On-Prem Kubernetes

### Scope

This document describes the **V1 JupyterHub deployment** for IAV, using **local authentication** for admins and testers and a single notebook image.

### High-Level Overview

- **Users** connect to `https://jupyterhub-test.example.internal` from the corporate network.
- **Ingress** routes traffic to the JupyterHub proxy service in the `jupyterhub-test` namespace.
- **JupyterHub Hub** manages authentication, routing, and spawns single-user notebook pods.
- **Single-user pods** run the `base-notebook` Docker image, optionally using GPUs if available.
- **Storage**:
  - Each user has a dynamically provisioned volume for `/home/jovyan`.
  - An additional shared PVC (`jupyterhub-shared-home`) is mounted at `/shared`.
- **Monitoring**:
  - Metrics are scraped by Prometheus via a `ServiceMonitor` (if Prometheus Operator is installed).
  - A basic Grafana dashboard shows activity and resource usage.

### Kubernetes Components

- Namespace: `jupyterhub-test`
- Service account: `jupyterhub-sa`
- RBAC:
  - `Role` and `RoleBinding` granting permissions for pods, services, PVCs, configmaps, secrets, and ingresses.
- Storage:
  - PVC `jupyterhub-shared-home` using storage class `standard` (adjust per cluster).
- Ingress:
  - Host: `jupyterhub-test.example.internal`
  - TLS secret: `jupyterhub-tls` (must be created by ops).

### Authentication (V1)

- Uses **DummyAuthenticator** with a **shared password** for all testers.
- Admin users are defined in Helm values (`c.Authenticator.admin_users`).
- This is suitable only for **internal testing**; V2 will replace it with EntraID/AD SSO.

### Images

- Base image: `registry.example.com/iav/base-notebook:v1`
- Derived from `jupyter/minimal-notebook` with common data-science libraries.

### Upgrade Path

V1 is intentionally simple to accelerate onboarding. It will be extended with:

- EntraID/AD + IAM integration.
- Ceph S3 integration for data and models.
- High availability, backup/restore, and production-grade CI/CD.



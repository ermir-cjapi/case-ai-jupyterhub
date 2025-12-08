# JupyterHub on Kubernetes

GPU-enabled JupyterHub with Azure AD authentication for your NVIDIA server.

## Structure

```
├── helm/              # Helm deployment (recommended)
├── azure-doc/         # Azure AD setup documentation
├── k8s-manifests/     # Plain Kubernetes YAML (learning)
├── images/            # Custom notebook image
├── local-testing/     # Local Docker Compose testing
└── aiv-production/    # AIV production deployment
```

## Quick Start (Helm)

```bash
# 1. Enable GPU sharing (run once)
./setup-gpu-timeslicing.sh

# 2. Build notebook image
source lab-config.env
docker login
./images/build_base_image.sh

# 3. Create Azure AD secret
cd helm
./create-azure-secret.sh

# 4. Deploy
./deploy_jhub_helm.sh

# Access at https://jupyterhub.ccrolabs.com
```

## Azure AD Authentication

JupyterHub uses Azure AD for authentication with group-based authorization.

### Required Azure AD Setup

1. **App Registration** with redirect URI: `https://your-domain.com/hub/oauth_callback`
2. **API Permissions**:
   - `User.Read` (Delegated)
   - `GroupMember.Read.All` (Application) + Admin Consent
3. **Client Secret** created

### Configuration

Edit `helm/values-helm.yaml`:

```python
c.AzureAdGraphAuthenticator.allowed_groups = {
    "group-object-id-1",  # JupyterHub-Admins
    "group-object-id-2",  # JupyterHub-Users
}

c.AzureAdGraphAuthenticator.admin_groups = {
    "group-object-id-1",  # JupyterHub-Admins
}
```

**See:** `azure-doc/README.md` for detailed setup instructions.

## Common Commands

```bash
# Status
kubectl get pods -n jupyterhub-test

# Logs
kubectl logs -n jupyterhub-test -l component=hub -f

# Redeploy
cd helm && ./deploy_jhub_helm.sh

# Delete
cd helm && ./delete_jhub_helm.sh
```

## GPU Support

### Enable GPU Sharing (Run Once)

```bash
./setup-gpu-timeslicing.sh  # 1 GPU → 4 users
```

Without sharing: 1 GPU = 1 user at a time  
With sharing: 1 GPU = 4 concurrent users

**See:** `GPU-USER-PROFILES.md` for profile options.

## Cloudflare Setup

Cloudflare tunnel handles ingress:
- Tunnel → `jupyterhub.ccrolabs.com` → `http://localhost:30080`
- No Kubernetes ingress needed

---

**Local testing?** See `local-testing/`  
**AIV production?** See `aiv-production/`

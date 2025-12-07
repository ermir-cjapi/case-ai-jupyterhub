# JupyterHub Azure AD - Quick Reference

## Two Questions Answered

### Q1: Why `/etc/jupyterhub/scripts/azure_ad_auth.py`?

**Answer**: That's the path **inside the Kubernetes pod**, not on your laptop!

```
┌─────────────────────────────────────────────────────────┐
│ Your Laptop (Windows)                                   │
│ C:\cc-ai\case-ai-jupyterhub\helm\azure_ad_auth.py      │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ 1. deploy_jhub_helm.sh creates ConfigMap
                   ↓
┌─────────────────────────────────────────────────────────┐
│ Kubernetes Cluster                                      │
│ ConfigMap: azure-auth-script                            │
│   data:                                                 │
│     azure_ad_auth.py: |                                 │
│       <content of the file>                             │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ 2. Helm mounts ConfigMap as volume
                   ↓
┌─────────────────────────────────────────────────────────┐
│ Inside Hub Pod (Linux container)                       │
│ /etc/jupyterhub/scripts/azure_ad_auth.py  ← File here! │
└─────────────────────────────────────────────────────────┘
```

**How it's configured**:

```yaml
# In values-helm.yaml
hub:
  extraVolumes:
    - name: azure-auth-script
      configMap:
        name: azure-auth-script  # ← Created by deploy script
  
  extraVolumeMounts:
    - name: azure-auth-script
      mountPath: /etc/jupyterhub/scripts  # ← Where it appears
```

**To verify it's there**:

```bash
# Check ConfigMap exists
kubectl get configmap azure-auth-script -n jupyterhub-test

# See inside the pod
kubectl exec -n jupyterhub-test -it $(kubectl get pod -n jupyterhub-test -l component=hub -o name) -- ls -la /etc/jupyterhub/scripts/

# Read the file inside pod
kubectl exec -n jupyterhub-test -it $(kubectl get pod -n jupyterhub-test -l component=hub -o name) -- cat /etc/jupyterhub/scripts/azure_ad_auth.py
```

---

### Q2: Should we use Group Names instead of Group IDs?

**Answer**: **No, stick with Object IDs!** Here's why:

#### Comparison

| Aspect | Object IDs (Current) | Display Names |
|--------|---------------------|---------------|
| **Example** | `d6c49ed5-eefc-48c4-90d0-2026f5fe3916` | `JupyterHub-Admins` |
| **Uniqueness** | ✅ Guaranteed unique forever | ❌ Admin can rename group |
| **Stability** | ✅ Never changes | ❌ Breaks if group renamed |
| **What API returns** | ✅ Returns IDs by default | ⚠️ Would need extra processing |
| **Readability** | ❌ Ugly UUIDs | ✅ Human-readable |
| **Best Practice** | ✅ Microsoft recommends | ❌ Not recommended |

#### Current Configuration (Recommended)

```python
# In values-helm.yaml
c.AzureAdGraphAuthenticator.allowed_groups = {
    "d6c49ed5-eefc-48c4-90d0-2026f5fe3916",  # JupyterHub-Admins
    "6543851f-fd97-40e8-b097-ab5a71e44ef2",  # JupyterHub-Users
}
```

**Benefits**:
- ✅ Works even if you rename "JupyterHub-Admins" to "Administrators"
- ✅ No code changes needed
- ✅ Comments show human-readable names

#### If You Renamed a Group

**Scenario**: You renamed "JupyterHub-Admins" to "Administrators" in Azure Portal

**With Object IDs** (Current):
```python
c.AzureAdGraphAuthenticator.admin_groups = {
    "d6c49ed5-eefc-48c4-90d0-2026f5fe3916"  # Administrators (was JupyterHub-Admins)
}
```
✅ **Still works!** Just update the comment.

**With Display Names** (If we used them):
```python
c.AzureAdGraphAuthenticator.admin_groups = {
    "JupyterHub-Admins"  # ← BROKEN! Group renamed
}
```
❌ **Broken!** Have to update config and redeploy.

#### How to Find Object IDs

**Method 1: Azure Portal**
1. Go to **Azure Portal** → **Azure Active Directory** → **Groups**
2. Click on your group (e.g., "JupyterHub-Admins")
3. Click **Overview**
4. Copy **Object ID** field

**Method 2: Hub Logs (Easiest)**

When a user logs in, check the logs:

```bash
kubectl logs -n jupyterhub-test -l component=hub -f
```

You'll see:
```
✅ Graph API: Found 2 groups for user
   - JupyterHub-Admins: d6c49ed5-eefc-48c4-90d0-2026f5fe3916
   - JupyterHub-Users: 6543851f-fd97-40e8-b097-ab5a71e44ef2
                       ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
                       Copy these Object IDs for your config
```

**Method 3: Microsoft Graph Explorer**

1. Go to: https://developer.microsoft.com/en-us/graph/graph-explorer
2. Sign in with your Azure account
3. Run query: `GET https://graph.microsoft.com/v1.0/groups`
4. Find your group and copy its `id` field

---

## Deployment Flow

### What Happens When You Run `./deploy_jhub_helm.sh`

```bash
#!/usr/bin/env bash

# Step 1: Create ConfigMap from Python file
kubectl create configmap azure-auth-script \
  --from-file=helm/azure_ad_auth.py \
  --namespace=jupyterhub-test

# Step 2: Deploy JupyterHub
helm upgrade --install jhub-v1 jupyterhub/jupyterhub \
  --values helm/values-helm.yaml
  
# Helm will:
# - Create namespace
# - Mount ConfigMap as volume
# - Start hub pod
# - Hub pod loads /etc/jupyterhub/scripts/azure_ad_auth.py
# - Authentication starts working!
```

### Inside the Hub Pod

When JupyterHub starts:

```python
# From values-helm.yaml extraConfig:
exec(open('/etc/jupyterhub/scripts/azure_ad_auth.py').read())
#          ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
#          This path is INSIDE the pod

# Now we have:
# - fetch_user_groups_from_graph_api() function
# - AzureAdGraphAuthenticator class

# Configure it:
c.JupyterHub.authenticator_class = AzureAdGraphAuthenticator
c.AzureAdGraphAuthenticator.allowed_groups = {...}
```

---

## Common Tasks

### Update Python Code

```bash
# 1. Edit the file
vim helm/azure_ad_auth.py

# 2. Update ConfigMap
kubectl create configmap azure-auth-script \
  --from-file=helm/azure_ad_auth.py \
  --namespace=jupyterhub-test \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Restart hub pod
kubectl rollout restart deployment hub -n jupyterhub-test
```

### Add a New Group

```bash
# 1. Find Object ID (check logs or Azure Portal)
# User logs in → Check logs:
kubectl logs -n jupyterhub-test -l component=hub -f

# 2. Edit values-helm.yaml
vim helm/values-helm.yaml

# Add to allowed_groups:
c.AzureAdGraphAuthenticator.allowed_groups = {
    "d6c49ed5-eefc-48c4-90d0-2026f5fe3916",  # JupyterHub-Admins
    "6543851f-fd97-40e8-b097-ab5a71e44ef2",  # JupyterHub-Users
    "NEW-GROUP-ID-HERE",                      # New Group Name
}

# 3. Redeploy
./deploy_jhub_helm.sh
```

### Change Admin Group

```bash
# Edit values-helm.yaml
c.AzureAdGraphAuthenticator.admin_groups = {
    "different-group-id"  # New admin group
}

# Redeploy
./deploy_jhub_helm.sh

# Users must re-login for admin status to update
```

---

## Troubleshooting

### ConfigMap Not Found

```
Error: configmap "azure-auth-script" not found
```

**Fix**: The deployment script should create it automatically. If not:

```bash
kubectl create configmap azure-auth-script \
  --from-file=helm/azure_ad_auth.py \
  --namespace=jupyterhub-test
```

### File Not Found in Pod

```
FileNotFoundError: [Errno 2] No such file or directory: '/etc/jupyterhub/scripts/azure_ad_auth.py'
```

**Fix**: ConfigMap not mounted. Check `values-helm.yaml`:

```yaml
hub:
  extraVolumes:
    - name: azure-auth-script
      configMap:
        name: azure-auth-script  # ← Must match ConfigMap name
  
  extraVolumeMounts:
    - name: azure-auth-script
      mountPath: /etc/jupyterhub/scripts
```

### Group Authorization Not Working

```
User can login but gets 403 Forbidden
```

**Debug**:

```bash
# 1. Check hub logs for user's groups
kubectl logs -n jupyterhub-test -l component=hub -f

# Look for:
# ✅ Graph API: Found 2 groups for user
#    - Group Name: group-object-id

# 2. Verify group ID is in allowed_groups
# Edit values-helm.yaml and check:
c.AzureAdGraphAuthenticator.allowed_groups = {
    "group-object-id",  # ← Must match exactly
}

# 3. Redeploy if changed
./deploy_jhub_helm.sh
```

---

## Summary

### Object IDs vs Names

**Use Object IDs** ✅
```python
c.AzureAdGraphAuthenticator.allowed_groups = {
    "d6c49ed5-eefc-48c4-90d0-2026f5fe3916",  # JupyterHub-Admins
}
```

**Don't use Names** ❌
```python
c.AzureAdGraphAuthenticator.allowed_groups = {
    "JupyterHub-Admins",  # Breaks if renamed
}
```

### File Paths

**On your laptop**:
```
C:\cc-ai\case-ai-jupyterhub\helm\azure_ad_auth.py
```

**Inside Kubernetes pod**:
```
/etc/jupyterhub/scripts/azure_ad_auth.py
```

**How they connect**:
```
Laptop file → ConfigMap → Volume mount → Pod file
```

---

Ready to deploy? 🚀

```bash
cd helm
./deploy_jhub_helm.sh
```


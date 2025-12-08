# Azure AD Authentication for JupyterHub

This document explains how JupyterHub integrates with Azure AD for authentication and group-based authorization.

## Overview

JupyterHub uses Azure AD (Microsoft Entra ID) for:
- **Authentication**: Users log in with their Azure AD credentials
- **Authorization**: Access is controlled by Azure AD group membership
- **Admin Rights**: Users in specific groups get admin privileges

## Why We Use Microsoft Graph API

**Problem**: Azure AD Free tier does NOT include groups in OAuth tokens.

**Solution**: We fetch groups via Microsoft Graph API using Client Credentials flow.

```
User logs in → Azure AD returns user info → 
JupyterHub calls Graph API → "What groups is this user in?" →
Grant/deny access based on group membership
```

## Architecture

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │ 1. Visit JupyterHub
       ↓
┌─────────────────┐
│   JupyterHub    │
└──────┬──────────┘
       │ 2. Redirect to Azure AD
       ↓
┌─────────────────┐
│   Azure AD      │
│   OAuth Login   │
└──────┬──────────┘
       │ 3. Returns user info (email, name, Object ID)
       ↓
┌─────────────────┐
│   JupyterHub    │ 4. Gets app-only token (Client Credentials)
└──────┬──────────┘
       │ 5. Call Graph API: /users/{user-id}/memberOf
       ↓
┌─────────────────────────────┐
│  Microsoft Graph API        │
└──────┬──────────────────────┘
       │ 6. Returns list of groups
       ↓
┌─────────────────┐
│   JupyterHub    │ 7. Check allowed_groups & admin_groups
└─────────────────┘
       │ 8. Grant/Deny Access
       ↓
┌─────────────────┐
│  User's         │
│  Notebook       │
└─────────────────┘
```

## Required Azure AD Configuration

### 1. App Registration

Create an app registration in Azure Portal:
- **Name**: JupyterHub Production
- **Redirect URI**: `https://your-domain.com/hub/oauth_callback`

### 2. API Permissions

Add these permissions to your app registration:

| Permission | Type | Purpose |
|------------|------|---------|
| `User.Read` | Delegated | Read user profile during login |
| `GroupMember.Read.All` | **Application** | Read any user's group memberships |

**Important**: Click "Grant admin consent" after adding permissions!

### 3. Client Secret

Create a client secret and note the **value** (not the ID).

## Key Files

| File | Purpose |
|------|---------|
| `helm/azure_ad_auth.py` | Custom authenticator with Graph API integration |
| `helm/values-helm.yaml` | JupyterHub configuration |
| `helm/create-azure-secret.sh` | Creates Kubernetes secret with credentials |
| `helm/deploy_jhub_helm.sh` | Deployment script |

## Configuration

### Group IDs

Groups are identified by their **Object ID** (UUID), not display name:

```python
c.AzureAdGraphAuthenticator.allowed_groups = {
    "d6c49ed5-eefc-48c4-90d0-2026f5fe3916",  # JupyterHub-Admins
    "6543851f-fd97-40e8-b097-ab5a71e44ef2",  # JupyterHub-Users
}

c.AzureAdGraphAuthenticator.admin_groups = {
    "d6c49ed5-eefc-48c4-90d0-2026f5fe3916"   # JupyterHub-Admins
}
```

**How to find Object IDs**: Azure Portal → Groups → [Your Group] → Overview → Object ID

### Adding/Removing Groups

1. Edit `helm/values-helm.yaml`
2. Add/remove group IDs in `allowed_groups` or `admin_groups`
3. Run `./deploy_jhub_helm.sh`
4. Users must re-login for changes to take effect

## Deployment

### First-Time Setup

```bash
cd helm

# 1. Create secret with Azure credentials
./create-azure-secret.sh

# 2. Deploy JupyterHub
./deploy_jhub_helm.sh
```

### Update Configuration

```bash
cd helm

# Update ConfigMap with latest code
kubectl create configmap azure-auth-script \
  --from-file=azure_ad_auth.py \
  --namespace=jupyterhub-test \
  --dry-run=client -o yaml | kubectl apply -f -

# Deploy changes
./deploy_jhub_helm.sh
```

## Troubleshooting

### View Logs

```bash
kubectl logs -n jupyterhub-test -l component=hub -f
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 403 Forbidden | Missing Graph API permission | Add `GroupMember.Read.All` (Application) + grant consent |
| User not found | Guest user email lookup failed | Code uses Object ID (should work automatically) |
| No groups found | User not in any Azure AD groups | Add user to groups in Azure Portal |
| Hub pod crash | Python syntax error | Check logs for traceback |

### Test Graph API Manually

```bash
# Get a token
TOKEN=$(curl -s -X POST \
  "https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/token" \
  -d "client_id=<client-id>" \
  -d "client_secret=<client-secret>" \
  -d "scope=https://graph.microsoft.com/.default" \
  -d "grant_type=client_credentials" | jq -r '.access_token')

# Test user lookup
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://graph.microsoft.com/v1.0/users/<user-object-id>/memberOf" | jq
```

## Guest Users (External Users)

Guest users (with `#EXT#` in their userPrincipalName) are fully supported. The code automatically uses the user's **Object ID** instead of email for Graph API lookups.

## Upgrading to Azure AD Premium

If you upgrade to Premium P1/P2, you can simplify by using token-based groups:

```python
# Premium P1/P2 - Groups are in the token automatically
c.JupyterHub.authenticator_class = AzureAdOAuthenticator
c.AzureAdOAuthenticator.manage_groups = True
```

This eliminates the Graph API call but costs ~$6/user/month.

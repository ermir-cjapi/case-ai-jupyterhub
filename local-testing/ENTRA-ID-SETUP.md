# Azure AD / Entra ID Authentication Setup

Step-by-step guide to set up Microsoft Entra ID (Azure AD) authentication for JupyterHub.

## Prerequisites

- Azure account with access to Microsoft Entra ID (Azure AD)
- Permission to create App registrations (or ask your IT admin)

## Step 1: Create App Registration

1. Go to **[Azure Portal](https://portal.azure.com)**
2. Search for **"Microsoft Entra ID"** (or "Azure Active Directory")
3. Click **"App registrations"** in the left menu
4. Click **"+ New registration"**

### Fill in:

| Field | Value |
|-------|-------|
| **Name** | `JupyterHub Local Test` |
| **Supported account types** | Select based on your needs (see below) |
| **Redirect URI** | Platform: `Web`, URL: `http://localhost:8000/hub/oauth_callback` |

### Account Types:

- **Single tenant** - Only users from your organization
- **Multi-tenant** - Users from any Azure AD organization
- **Personal Microsoft accounts** - Also allow personal accounts

For testing, choose **"Accounts in this organizational directory only (Single tenant)"**

5. Click **"Register"**

## Step 2: Copy IDs

After registration, you'll see the app overview page:

1. Copy **"Application (client) ID"** → This is your `CLIENT_ID`
2. Copy **"Directory (tenant) ID"** → This is your `TENANT_ID`

Example:
```
Client ID: 12345678-1234-1234-1234-123456789abc
Tenant ID: 87654321-4321-4321-4321-cba987654321
```

## Step 3: Create Client Secret

1. In your app registration, click **"Certificates & secrets"**
2. Click **"+ New client secret"**
3. Description: `JupyterHub secret`
4. Expiration: Choose (e.g., 12 months)
5. Click **"Add"**
6. **IMMEDIATELY COPY the "Value"** (you can't see it again!)

This is your `CLIENT_SECRET`

Example:
```
Client Secret: abc123~XYZ789...
```

## Step 4: Configure API Permissions

1. Click **"API permissions"** in the left menu
2. Click **"+ Add a permission"**
3. Select **"Microsoft Graph"**
4. Select **"Delegated permissions"**
5. Add these permissions:
   - ✅ `email`
   - ✅ `openid`
   - ✅ `profile`
   - ✅ `User.Read`
   - ✅ `GroupMember.Read.All` (optional - for group-based access)

6. Click **"Add permissions"**
7. Click **"Grant admin consent for [Your Organization]"** (if you're an admin)

## Step 5: Update JupyterHub Config

Edit `local-testing/jupyterhub_config.py`:

```python
# Around lines 58-61, replace:
c.AzureAdOAuthenticator.tenant_id = 'YOUR_TENANT_ID_HERE'
c.AzureAdOAuthenticator.client_id = 'YOUR_CLIENT_ID_HERE'
c.AzureAdOAuthenticator.client_secret = 'YOUR_CLIENT_SECRET_HERE'

# With your actual values:
c.AzureAdOAuthenticator.tenant_id = '87654321-4321-4321-4321-cba987654321'
c.AzureAdOAuthenticator.client_id = '12345678-1234-1234-1234-123456789abc'
c.AzureAdOAuthenticator.client_secret = 'abc123~XYZ789...'
```

## Step 6: Restart JupyterHub

```bash
cd local-testing
docker-compose restart
```

## Step 7: Test Login

1. Open browser: **http://localhost:8000**
2. Click **"Sign in with Azure AD"** (or similar)
3. Microsoft login page appears
4. Login with your Azure AD account
5. Authorize the app
6. You're logged in! 🎉

---

## Roles and Access Control

### Allow Specific Users

```python
# Only allow these email addresses
c.Authenticator.allowed_users = {
    'alice@yourcompany.com',
    'bob@yourcompany.com'
}
```

### Allow Azure AD Groups

First, add `GroupMember.Read.All` permission in Azure Portal, then:

```python
# Allow users from specific Azure AD groups
c.AzureAdOAuthenticator.allowed_groups = {
    'JupyterHub-Users',
    'Data-Science-Team'
}
```

### Admin Users

```python
# Specific users are admins
c.Authenticator.admin_users = {'admin@yourcompany.com'}

# OR: Members of these groups are admins
c.AzureAdOAuthenticator.admin_groups = {'JupyterHub-Admins'}
```

### Admin Rights

Admins can:
- Access admin panel (`/hub/admin`)
- Start/stop other users' servers
- Add/remove users
- View all running servers
- Access other users' notebooks (if configured)

---

## Common Issues

### Error: "AADSTS50011: Reply URL does not match"

**Cause:** The redirect URI in Azure doesn't match your config.

**Fix:** Make sure Azure Portal has exactly:
```
http://localhost:8000/hub/oauth_callback
```

### Error: "AADSTS700016: Application not found"

**Cause:** Wrong Client ID or Tenant ID.

**Fix:** Double-check the IDs from Azure Portal.

### Error: "Unauthorized" or "Invalid client secret"

**Cause:** Client secret is wrong or expired.

**Fix:** Create a new client secret in Azure Portal.

### Can't see groups

**Cause:** Missing `GroupMember.Read.All` permission.

**Fix:** 
1. Add the permission in API permissions
2. Grant admin consent
3. Restart JupyterHub

---

## Production Setup (Kubernetes)

When you deploy to Kubernetes on your NVIDIA server, the config goes in `values.yaml`:

```yaml
hub:
  extraConfig:
    azure-ad-auth: |
      from oauthenticator.azuread import AzureAdOAuthenticator
      c.JupyterHub.authenticator_class = AzureAdOAuthenticator
      c.AzureAdOAuthenticator.tenant_id = "YOUR_TENANT_ID"
      c.AzureAdOAuthenticator.client_id = "YOUR_CLIENT_ID"
      c.AzureAdOAuthenticator.client_secret = "YOUR_CLIENT_SECRET"
      c.AzureAdOAuthenticator.oauth_callback_url = "https://jupyterhub.ccrolabs.com/hub/oauth_callback"
      c.AzureAdOAuthenticator.allowed_groups = {"JupyterHub-Users"}
      c.AzureAdOAuthenticator.admin_groups = {"JupyterHub-Admins"}
```

**Important:** For production, change the callback URL to your real domain:
```
https://jupyterhub.ccrolabs.com/hub/oauth_callback
```

---

## Summary

| Config Location | File |
|-----------------|------|
| Docker Compose (local) | `jupyterhub_config.py` |
| Kubernetes (production) | `values.yaml` |

| Role | Config |
|------|--------|
| Who can login | `allowed_users` or `allowed_groups` |
| Who is admin | `admin_users` or `admin_groups` |

| Setting | Description |
|---------|-------------|
| `tenant_id` | Your Azure AD organization ID |
| `client_id` | App registration ID |
| `client_secret` | Secret for authentication |
| `oauth_callback_url` | Where Azure redirects after login |
| `allowed_groups` | Azure AD groups that can login |
| `admin_groups` | Azure AD groups with admin rights |


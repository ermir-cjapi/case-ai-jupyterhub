# Azure AD Authentication - Quick Reference

## 📋 Configuration Templates

Copy and paste these into your `helm/values-helm.yaml` file under `hub.extraConfig.00-azure-ad-auth`.

---

## Template 1: Allow Everyone in Tenant (Testing)

**Use case**: Initial testing, small trusted organization

```python
from oauthenticator.azuread import AzureAdOAuthenticator
c.JupyterHub.authenticator_class = AzureAdOAuthenticator

c.AzureAdOAuthenticator.tenant_id = "YOUR_TENANT_ID"
c.AzureAdOAuthenticator.client_id = "YOUR_CLIENT_ID"
c.AzureAdOAuthenticator.client_secret = "YOUR_CLIENT_SECRET"
c.AzureAdOAuthenticator.oauth_callback_url = "https://jupyterhub.ccrolabs.com/hub/oauth_callback"

# Allow ALL users in your Azure AD tenant
c.Authenticator.allow_all = True

# Specific admin by email
c.Authenticator.admin_users = {"your-email@yourcompany.com"}
```

**Required API Permissions**: `email`, `openid`, `profile`, `User.Read`

---

## Template 2: Email Whitelist (Small Teams)

**Use case**: 5-20 users, don't want to manage groups

```python
from oauthenticator.azuread import AzureAdOAuthenticator
c.JupyterHub.authenticator_class = AzureAdOAuthenticator

c.AzureAdOAuthenticator.tenant_id = "YOUR_TENANT_ID"
c.AzureAdOAuthenticator.client_id = "YOUR_CLIENT_ID"
c.AzureAdOAuthenticator.client_secret = "YOUR_CLIENT_SECRET"
c.AzureAdOAuthenticator.oauth_callback_url = "https://jupyterhub.ccrolabs.com/hub/oauth_callback"

# Allow specific users by email
c.Authenticator.allowed_users = {
    "alice@yourcompany.com",
    "bob@yourcompany.com",
    "charlie@yourcompany.com"
}

# Admin users
c.Authenticator.admin_users = {
    "admin@yourcompany.com"
}
```

**Required API Permissions**: `email`, `openid`, `profile`, `User.Read`

**⚠️ Note**: Must redeploy JupyterHub to add/remove users

---

## Template 3: Azure AD Groups (RECOMMENDED)

**Use case**: Production, scalable teams, centralized management

```python
from oauthenticator.azuread import AzureAdOAuthenticator
c.JupyterHub.authenticator_class = AzureAdOAuthenticator

c.AzureAdOAuthenticator.tenant_id = "YOUR_TENANT_ID"
c.AzureAdOAuthenticator.client_id = "YOUR_CLIENT_ID"
c.AzureAdOAuthenticator.client_secret = "YOUR_CLIENT_SECRET"
c.AzureAdOAuthenticator.oauth_callback_url = "https://jupyterhub.ccrolabs.com/hub/oauth_callback"

# Allow users in Azure AD groups
c.AzureAdOAuthenticator.allowed_groups = {
    "JupyterHub-Users",
    "JupyterHub-Admins",  # Admins need access too!
    "Data-Science-Team"
}

# Admins based on Azure AD group
c.AzureAdOAuthenticator.admin_groups = {
    "JupyterHub-Admins"
}
```

**Required API Permissions**: `email`, `openid`, `profile`, `User.Read`, **`GroupMember.Read.All`**

**✅ Benefits**: Add/remove users in Azure AD without redeploying JupyterHub

---

## Template 4: Hybrid (Groups + Email)

**Use case**: Mostly group-based, but need to add external contractors

```python
from oauthenticator.azuread import AzureAdOAuthenticator
c.JupyterHub.authenticator_class = AzureAdOAuthenticator

c.AzureAdOAuthenticator.tenant_id = "YOUR_TENANT_ID"
c.AzureAdOAuthenticator.client_id = "YOUR_CLIENT_ID"
c.AzureAdOAuthenticator.client_secret = "YOUR_CLIENT_SECRET"
c.AzureAdOAuthenticator.oauth_callback_url = "https://jupyterhub.ccrolabs.com/hub/oauth_callback"

# Allow users in groups
c.AzureAdOAuthenticator.allowed_groups = {
    "JupyterHub-Users"
}

# Plus allow specific external users (not in group)
c.Authenticator.allowed_users = {
    "contractor@external.com",
    "partner@vendor.com"
}

# Admins from group
c.AzureAdOAuthenticator.admin_groups = {"JupyterHub-Admins"}

# Plus specific admin user
c.Authenticator.admin_users = {"cto@yourcompany.com"}
```

**Required API Permissions**: `email`, `openid`, `profile`, `User.Read`, **`GroupMember.Read.All`**

---

## Template 5: Using Kubernetes Secrets (Production Best Practice)

**Use case**: Keep secrets out of git

### Step 1: Create Kubernetes Secret

```bash
kubectl create secret generic jupyterhub-azure-secret \
  --from-literal=tenant-id='YOUR_TENANT_ID' \
  --from-literal=client-id='YOUR_CLIENT_ID' \
  --from-literal=client-secret='YOUR_CLIENT_SECRET' \
  -n jupyterhub
```

### Step 2: Update values-helm.yaml

```yaml
hub:
  # Load secrets as environment variables
  extraEnv:
    AZURE_TENANT_ID:
      valueFrom:
        secretKeyRef:
          name: jupyterhub-azure-secret
          key: tenant-id
    AZURE_CLIENT_ID:
      valueFrom:
        secretKeyRef:
          name: jupyterhub-azure-secret
          key: client-id
    AZURE_CLIENT_SECRET:
      valueFrom:
        secretKeyRef:
          name: jupyterhub-azure-secret
          key: client-secret

  extraConfig:
    00-azure-ad-auth: |
      import os
      from oauthenticator.azuread import AzureAdOAuthenticator
      c.JupyterHub.authenticator_class = AzureAdOAuthenticator
      
      # Load from environment variables (populated from Kubernetes secrets)
      c.AzureAdOAuthenticator.tenant_id = os.environ.get('AZURE_TENANT_ID')
      c.AzureAdOAuthenticator.client_id = os.environ.get('AZURE_CLIENT_ID')
      c.AzureAdOAuthenticator.client_secret = os.environ.get('AZURE_CLIENT_SECRET')
      c.AzureAdOAuthenticator.oauth_callback_url = "https://jupyterhub.ccrolabs.com/hub/oauth_callback"
      
      # Access control
      c.AzureAdOAuthenticator.allowed_groups = {"JupyterHub-Users"}
      c.AzureAdOAuthenticator.admin_groups = {"JupyterHub-Admins"}
```

---

## 🔧 App Registration Setup Steps

### 1. Create App Registration

1. Go to **Azure Portal** → **Microsoft Entra ID** → **App registrations**
2. Click **"New registration"**
3. Fill in:
   - **Name**: `JupyterHub Production`
   - **Supported account types**: `Accounts in this organizational directory only (Single tenant)`
   - **Redirect URI**: `Web` → `https://jupyterhub.ccrolabs.com/hub/oauth_callback`
4. Click **"Register"**

### 2. Copy Credentials

After creation:

1. Go to **Overview** page
2. Copy **Application (client) ID** → This is your `CLIENT_ID`
3. Copy **Directory (tenant) ID** → This is your `TENANT_ID`

### 3. Create Client Secret

1. Go to **Certificates & secrets**
2. Click **"New client secret"**
3. Description: `JupyterHub Production Secret`
4. Expires: Choose duration (e.g., 24 months)
5. Click **"Add"**
6. **⚠️ IMMEDIATELY COPY THE VALUE** → This is your `CLIENT_SECRET`
   - You can't see it again after leaving this page!

### 4. Configure API Permissions

1. Go to **API permissions**
2. Click **"Add a permission"**
3. Select **"Microsoft Graph"**
4. Select **"Delegated permissions"**
5. Add these permissions:
   - ✅ `email`
   - ✅ `openid`
   - ✅ `profile`
   - ✅ `User.Read`
   - ✅ `GroupMember.Read.All` (only if using group-based auth)
6. Click **"Add permissions"**
7. Click **"Grant admin consent for [Your Org]"** button
8. Click **"Yes"** to confirm

### 5. Create Azure AD Groups (If Using Group-Based Auth)

1. Go to **Azure Active Directory** → **Groups**
2. Click **"New group"**
3. Create first group:
   - **Group type**: `Security`
   - **Group name**: `JupyterHub-Users`
   - **Group description**: `Users who can access JupyterHub`
4. Click **"Create"**
5. Repeat for `JupyterHub-Admins`
6. Add users to groups:
   - Open each group → **Members** → **Add members**

---

## 📝 Common Configuration Patterns

### Pattern: Restrict to Specific Domain

```python
# Custom username mapping - only allow @yourcompany.com
c.AzureAdOAuthenticator.username_claim = "email"

# Add allowed_users or allowed_groups as normal
c.Authenticator.allowed_users = {
    "user@yourcompany.com"  # Only yourcompany.com emails
}
```

### Pattern: Multiple Admin Groups

```python
c.AzureAdOAuthenticator.admin_groups = {
    "JupyterHub-Admins",
    "IT-Team",
    "Data-Science-Leads"
}
```

### Pattern: Read-Only Admins

```python
# In hub.config section (not extraConfig)
hub:
  config:
    JupyterHub:
      admin_access: false  # Admins can manage but not access user files

  extraConfig:
    00-azure-ad-auth: |
      # ... authentication config ...
      c.Authenticator.admin_users = {"manager@company.com"}
```

---

## 🧪 Testing Checklist

### Before Deployment

- [ ] App registration created
- [ ] Tenant ID, Client ID, Client Secret copied
- [ ] API permissions added and admin consent granted
- [ ] Azure AD groups created (if using group-based auth)
- [ ] Users added to groups
- [ ] Redirect URI matches your JupyterHub URL exactly

### After Deployment

- [ ] Non-admin user can login
- [ ] Non-admin user CANNOT see `/hub/admin`
- [ ] Admin user can login
- [ ] Admin user CAN see `/hub/admin`
- [ ] Admin can view other users' servers (if `admin_access: true`)
- [ ] Logout and re-login works
- [ ] Adding user to group grants access (if using group-based)

---

## 🚨 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Invalid redirect URI" | Check redirect URI in app registration matches EXACTLY (http vs https, trailing slash) |
| User can't login | Verify user is in `allowed_users` or `allowed_groups` |
| Admin can't see admin panel | Admin must ALSO be in `allowed_users` or `allowed_groups` |
| Groups not working | Check `GroupMember.Read.All` permission granted with admin consent |
| Secret expired | Create new client secret in Azure Portal, update config, redeploy |

### Debug Logs

```bash
# View JupyterHub logs
kubectl logs -n jupyterhub deployment/hub -f

# Look for authentication errors
kubectl logs -n jupyterhub deployment/hub | grep -i "auth\|error"
```

---

## 📚 Related Documentation

- Main guide: `AZURE-AD-AUTHORIZATION-GUIDE.md`
- Local testing: `local-testing/ENTRA-ID-SETUP.md`
- Deployment: `aiv-production/QUICK-START-GUIDE.md`
- Architecture: `aiv-production/docs/architecture.md`


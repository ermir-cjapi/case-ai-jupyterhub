# Azure AD Authorization Guide for JupyterHub

## Overview

JupyterHub uses a **two-layer authorization model** when integrated with Azure AD:

```
┌──────────────────────────────────────────────────────────┐
│  Layer 1: AUTHENTICATION (Azure AD)                      │
│  • Who can prove their identity                          │
│  • Handled by: Microsoft Entra ID OAuth                  │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│  Layer 2: AUTHORIZATION (Hybrid: Azure AD + JupyterHub) │
│  • Who can ACCESS: Azure AD groups                       │
│  • Who is ADMIN: Azure AD groups OR Helm config          │
│  • Handled by: OAuthenticator + JupyterHub config        │
└──────────────────────────────────────────────────────────┘
```

---

## Admin vs Regular User Capabilities

### 🔐 JupyterHub Admin Powers

When `admin_access: true` is set (as in your config), admins can:

| Capability | Admin | Regular User |
|-----------|-------|--------------|
| Start/stop their own server | ✅ | ✅ |
| Access their own notebooks | ✅ | ✅ |
| **Access other users' servers** | ✅ | ❌ |
| **Start/stop other users' servers** | ✅ | ❌ |
| **View admin panel** (`/hub/admin`) | ✅ | ❌ |
| **Add/remove users** | ✅ | ❌ |
| **Grant admin rights** | ✅ | ❌ |
| **View server logs** | ✅ | ❌ |
| **Access token management** | ✅ | ❌ |

**Security Note**: `admin_access: true` means admins can **see and modify** other users' notebooks. This is powerful but necessary for support/debugging. Turn it off if you want admins to only manage servers without file access.

---

## Authorization Strategies

### Strategy 1: Simple Email-Based (Good for Small Teams)

**Use case**: Small team, manual user management

```yaml
# In helm/values-helm.yaml
00-azure-ad-auth: |
  from oauthenticator.azuread import AzureAdOAuthenticator
  c.JupyterHub.authenticator_class = AzureAdOAuthenticator
  
  c.AzureAdOAuthenticator.tenant_id = "YOUR_TENANT_ID"
  c.AzureAdOAuthenticator.client_id = "YOUR_CLIENT_ID"
  c.AzureAdOAuthenticator.client_secret = "YOUR_CLIENT_SECRET"
  c.AzureAdOAuthenticator.oauth_callback_url = "https://jupyterhub.ccrolabs.com/hub/oauth_callback"
  
  # Allow specific users
  c.Authenticator.allowed_users = {
      "alice@yourcompany.com",
      "bob@yourcompany.com",
      "charlie@yourcompany.com"
  }
  
  # Specific admins
  c.Authenticator.admin_users = {
      "admin@yourcompany.com"
  }
```

**Pros**: Simple, no extra Azure AD permissions needed  
**Cons**: Must update Helm config and redeploy to add/remove users

---

### Strategy 2: Azure AD Group-Based (RECOMMENDED for Production)

**Use case**: Scalable teams, centralized user management

#### Step 1: Create Azure AD Groups

In Azure Portal (you can do this NOW without a subscription!):

1. Go to **Azure Active Directory** → **Groups**
2. Create two groups:
   - **JupyterHub-Users** (regular access)
   - **JupyterHub-Admins** (admin access)
3. Add users to these groups

#### Step 2: Configure App Registration

In your app registration:

1. Go to **API permissions**
2. Add **Microsoft Graph** → **Delegated permissions**:
   - `email`
   - `openid`
   - `profile`
   - `User.Read`
   - **`GroupMember.Read.All`** ← Important for group-based access!
3. Click **"Grant admin consent for [Your Org]"**

#### Step 3: Update Helm Config

```yaml
# In helm/values-helm.yaml
00-azure-ad-auth: |
  from oauthenticator.azuread import AzureAdOAuthenticator
  c.JupyterHub.authenticator_class = AzureAdOAuthenticator
  
  c.AzureAdOAuthenticator.tenant_id = "YOUR_TENANT_ID"
  c.AzureAdOAuthenticator.client_id = "YOUR_CLIENT_ID"
  c.AzureAdOAuthenticator.client_secret = "YOUR_CLIENT_SECRET"
  c.AzureAdOAuthenticator.oauth_callback_url = "https://jupyterhub.ccrolabs.com/hub/oauth_callback"
  
  # Allow users in specific Azure AD groups
  c.AzureAdOAuthenticator.allowed_groups = {
      "JupyterHub-Users",
      "JupyterHub-Admins"    # Admins should also be allowed to access
  }
  
  # Admins based on Azure AD group
  c.AzureAdOAuthenticator.admin_groups = {
      "JupyterHub-Admins"
  }
```

**Pros**: 
- ✅ Add/remove users in Azure AD without redeploying JupyterHub
- ✅ Centralized access management
- ✅ Scales to hundreds of users
- ✅ Can use existing organizational groups

**Cons**: Requires `GroupMember.Read.All` permission

---

### Strategy 3: Hybrid (Flexible)

Combine groups and specific users:

```yaml
00-azure-ad-auth: |
  from oauthenticator.azuread import AzureAdOAuthenticator
  c.JupyterHub.authenticator_class = AzureAdOAuthenticator
  
  c.AzureAdOAuthenticator.tenant_id = "YOUR_TENANT_ID"
  c.AzureAdOAuthenticator.client_id = "YOUR_CLIENT_ID"
  c.AzureAdOAuthenticator.client_secret = "YOUR_CLIENT_SECRET"
  c.AzureAdOAuthenticator.oauth_callback_url = "https://jupyterhub.ccrolabs.com/hub/oauth_callback"
  
  # Allow users in groups
  c.AzureAdOAuthenticator.allowed_groups = {
      "Data-Science-Team"
  }
  
  # Plus allow specific external collaborators (not in group)
  c.Authenticator.allowed_users = {
      "external-contractor@partner.com"
  }
  
  # Admins can come from group OR specific users
  c.AzureAdOAuthenticator.admin_groups = {"JupyterHub-Admins"}
  c.Authenticator.admin_users = {"cto@yourcompany.com"}  # CEO is always admin
```

---

## Quick Setup Checklist

### ✅ Phase 1: Azure AD Setup (Do This Now - No Subscription Needed!)

- [ ] Go to Azure Portal → Microsoft Entra ID → App registrations
- [ ] Create new app registration:
  - Name: `JupyterHub Production`
  - Redirect URI: `https://jupyterhub.ccrolabs.com/hub/oauth_callback`
- [ ] Copy **Tenant ID** and **Client ID**
- [ ] Create **Client Secret** and copy the value
- [ ] Add API permissions:
  - `email`, `openid`, `profile`, `User.Read`
  - (Optional) `GroupMember.Read.All` for group-based access
- [ ] Grant admin consent
- [ ] Create Azure AD groups (if using group-based):
  - `JupyterHub-Users`
  - `JupyterHub-Admins`
- [ ] Add yourself to `JupyterHub-Admins` group

### ✅ Phase 2: Update Helm Config

- [ ] Edit `helm/values-helm.yaml`
- [ ] Replace placeholders in `00-azure-ad-auth` section:
  - `YOUR_TENANT_ID` → Your tenant ID
  - `YOUR_CLIENT_ID` → Your client ID
  - `YOUR_CLIENT_SECRET` → Your client secret
- [ ] Choose authorization strategy (see above)
- [ ] Update `admin_users` or `admin_groups` with your info

### ✅ Phase 3: Deploy (Requires Azure Subscription)

```bash
# Deploy to Kubernetes with new config
cd helm/
./deploy_jhub_helm.sh

# Or if using scripts:
cd aiv-production/scripts/
./deploy-aiv-production.sh
```

---

## Testing Authentication

### Local Testing (Before Azure Deployment)

You can test Azure AD auth locally using Docker Compose:

```bash
cd local-testing/

# 1. Edit jupyterhub_config.py with your Azure AD credentials
# 2. Update redirect URI to: http://localhost:8000/hub/oauth_callback

# Start JupyterHub locally
docker-compose up

# Visit: http://localhost:8000
```

### Production Testing

After deployment:

1. **Test regular user login**:
   - Have a non-admin user access the JupyterHub URL
   - Verify they can login but DON'T see admin panel

2. **Test admin login**:
   - Login as admin user
   - Go to `/hub/admin` - you should see admin panel
   - Try accessing another user's server

---

## Security Best Practices

### 🔒 Credential Management

**❌ NEVER** commit secrets to git:

```yaml
# BAD - secrets visible in git
c.AzureAdOAuthenticator.client_secret = "actual-secret-here"
```

**✅ GOOD** - Use Kubernetes secrets:

```yaml
# In values-helm.yaml
hub:
  extraEnv:
    AZURE_CLIENT_SECRET:
      valueFrom:
        secretKeyRef:
          name: jupyterhub-azure-secret
          key: client-secret

  extraConfig:
    00-azure-ad-auth: |
      import os
      c.AzureAdOAuthenticator.client_secret = os.environ.get('AZURE_CLIENT_SECRET')
```

Create secret separately:

```bash
kubectl create secret generic jupyterhub-azure-secret \
  --from-literal=client-secret='YOUR_ACTUAL_SECRET' \
  -n jupyterhub
```

### 🔒 Admin Access Control

If admins DON'T need to access user files:

```yaml
hub:
  config:
    JupyterHub:
      admin_access: false  # Admins can manage servers but not access files
```

### 🔒 Group Permission Scope

Use the **minimum required permissions**:

- If using email-based auth: DON'T add `GroupMember.Read.All`
- If using group-based auth: `GroupMember.Read.All` is necessary

---

## Troubleshooting

### Users Can't Login

**Check**:
1. User is in allowed group or `allowed_users` list
2. App registration permissions granted
3. Redirect URI matches exactly (check for http vs https)
4. Client secret hasn't expired

**Debug**:
```bash
kubectl logs -n jupyterhub deployment/hub -f
```

### Admin Can't Access Admin Panel

**Check**:
1. User is in `admin_users` or `admin_groups`
2. User is also in `allowed_users` or `allowed_groups` (admins must also be allowed!)
3. Visit `/hub/admin` directly (link might not show)

### Group-Based Access Not Working

**Check**:
1. `GroupMember.Read.All` permission granted in app registration
2. Admin consent granted for permissions
3. Group names are exact matches (case-sensitive)
4. Wait 5-10 minutes after granting permissions

---

## FAQ

**Q: Can I mix Azure AD groups and individual users?**  
A: Yes! Users in `allowed_groups` OR `allowed_users` will have access.

**Q: Do Azure AD roles (like Global Administrator) automatically grant JupyterHub admin?**  
A: No! Azure AD tenant roles are separate from JupyterHub admin rights. You must explicitly configure `admin_users` or `admin_groups`.

**Q: Can I use Azure AD Conditional Access policies?**  
A: Yes! Since authentication goes through Azure AD, all conditional access policies (MFA, location-based, device compliance) apply automatically.

**Q: What happens if I remove someone from Azure AD group?**  
A: They lose access immediately on next login. Active sessions continue until server timeout.

**Q: Can I have multiple admin groups?**  
A: Yes! Add multiple groups to the set:
```python
c.AzureAdOAuthenticator.admin_groups = {"IT-Admins", "Data-Science-Leads"}
```

---

## Next Steps

1. ✅ Complete Phase 1 (Azure AD Setup) - **You can do this NOW!**
2. ⏳ Wait for Azure subscription access
3. ✅ Complete Phase 2 (Update Helm config)
4. ✅ Deploy and test (Phase 3)

**Remember**: Authentication setup in Azure AD can be done entirely without a subscription! Get it ready now, and you'll be able to deploy quickly once subscription access is granted.


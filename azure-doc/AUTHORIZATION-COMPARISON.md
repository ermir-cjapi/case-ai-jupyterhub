# Azure AD Authorization: WHERE Does Each Setting Live?

## 🎯 Quick Answer

**Authorization is a MIX of both Azure AD and Helm configuration!**

---

## 📊 Detailed Comparison Table

| What | Where Configured | Can Change Without Subscription? | Requires JupyterHub Redeploy? |
|------|------------------|----------------------------------|-------------------------------|
| **Authentication** (login process) | Azure AD App Registration | ✅ YES | ❌ NO (just update config) |
| **Who can access** (if using groups) | Azure AD Groups | ✅ YES | ❌ NO (dynamic) |
| **Who can access** (if using emails) | Helm `values-helm.yaml` | ✅ YES | ✅ YES |
| **Who is admin** (if using groups) | Azure AD Groups | ✅ YES | ❌ NO (dynamic) |
| **Who is admin** (if using emails) | Helm `values-helm.yaml` | ✅ YES | ✅ YES |
| **Admin can access user files?** | Helm `values-helm.yaml` | ✅ YES | ✅ YES |
| **API Permissions** | Azure AD App Registration | ✅ YES | ❌ NO |
| **Callback URL** | Both (must match!) | ✅ YES | ✅ YES |

---

## 🏗️ The Two Systems

### System 1: Azure AD (Identity Provider)

```
┌─────────────────────────────────────────────┐
│  AZURE AD / ENTRA ID                        │
│  (You can configure this NOW!)              │
├─────────────────────────────────────────────┤
│  ✓ App Registration                         │
│    - Client ID                              │
│    - Client Secret                          │
│    - Redirect URI                           │
│    - API Permissions                        │
│                                             │
│  ✓ User & Group Management                  │
│    - Create groups                          │
│    - Add users to groups                    │
│    - Manage memberships                     │
│                                             │
│  ✓ Conditional Access (optional)            │
│    - MFA requirements                       │
│    - Location-based access                  │
│    - Device compliance                      │
└─────────────────────────────────────────────┘
```

**What it does**:
- Proves user identity (authentication)
- Provides group membership info
- Enforces security policies (MFA, etc.)

**What it does NOT do**:
- Decide who is JupyterHub admin
- Control JupyterHub features
- Manage notebook resources

---

### System 2: JupyterHub Config (Application Layer)

```
┌─────────────────────────────────────────────┐
│  JUPYTERHUB CONFIG (values-helm.yaml)       │
│  (Requires subscription to deploy)          │
├─────────────────────────────────────────────┤
│  ✓ Access Control Logic                     │
│    - Which groups/users allowed?            │
│    - Which groups/users are admins?         │
│    - Allow all vs whitelist?                │
│                                             │
│  ✓ Admin Capabilities                       │
│    - Can admins access user files?          │
│    - What can admins do?                    │
│                                             │
│  ✓ Resource Profiles                        │
│    - CPU/GPU allocations                    │
│    - Memory limits                          │
│    - Storage quotas                         │
└─────────────────────────────────────────────┘
```

**What it does**:
- Interprets Azure AD data
- Applies access rules
- Defines admin permissions
- Controls resource allocation

**What it does NOT do**:
- Authenticate users (delegates to Azure AD)
- Create Azure AD groups
- Manage Azure AD users

---

## 🔄 How They Work Together

### Example: User Login Flow

```
1. User visits JupyterHub URL
   ↓
2. JupyterHub redirects to Azure AD login
   (Azure AD handles authentication)
   ↓
3. User enters credentials, completes MFA
   ↓
4. Azure AD verifies identity
   ↓
5. Azure AD sends user info + group memberships to JupyterHub
   (Returns to callback URL)
   ↓
6. JupyterHub checks its config:
   - Is user in allowed_groups or allowed_users? → Grant access
   - Is user in admin_groups or admin_users? → Grant admin
   ↓
7. User gets appropriate access level
```

---

## 📋 Configuration Decision Matrix

### Scenario 1: "I want to add a new user"

| Method | Steps | Requires Redeploy? |
|--------|-------|-------------------|
| **Email-based** | 1. Edit `values-helm.yaml`<br>2. Add email to `allowed_users`<br>3. Deploy JupyterHub | ✅ YES |
| **Group-based** | 1. Go to Azure AD<br>2. Add user to `JupyterHub-Users` group<br>3. Done! | ❌ NO |

**Winner**: Group-based (no deployment needed!)

---

### Scenario 2: "I want to make someone an admin"

| Method | Steps | Requires Redeploy? |
|--------|-------|-------------------|
| **Email-based** | 1. Edit `values-helm.yaml`<br>2. Add email to `admin_users`<br>3. Deploy JupyterHub | ✅ YES |
| **Group-based** | 1. Go to Azure AD<br>2. Add user to `JupyterHub-Admins` group<br>3. Wait ~5 min for token refresh | ❌ NO |

**Winner**: Group-based (near-instant!)

---

### Scenario 3: "I want to remove someone's access"

| Method | Steps | Takes Effect When? |
|--------|-------|-------------------|
| **Email-based** | 1. Edit `values-helm.yaml`<br>2. Remove from `allowed_users`<br>3. Deploy JupyterHub | After deployment |
| **Group-based** | 1. Go to Azure AD<br>2. Remove from group | Next login attempt |
| **Both** | Disable user in Azure AD | Immediately (can't login) |

---

### Scenario 4: "I want to change admin file access permissions"

**This is ONLY in JupyterHub config**:

```yaml
# In values-helm.yaml
hub:
  config:
    JupyterHub:
      admin_access: true   # Admins CAN access user files
      # or
      admin_access: false  # Admins CANNOT access user files
```

Requires redeploy: ✅ YES

---

## 🎨 Visual Authorization Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    USER TRIES TO ACCESS                       │
│                    https://jupyterhub.ccrolabs.com            │
└───────────────────────────┬──────────────────────────────────┘
                            ↓
                ┌───────────────────────┐
                │  AZURE AD             │
                │  Authenticates user   │
                └───────────┬───────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │  Returns to JupyterHub:               │
        │  • User email: bob@company.com        │
        │  • Groups: [JupyterHub-Users]         │
        └───────────┬───────────────────────────┘
                    ↓
        ┌────────────────────────────────────────────────┐
        │  JUPYTERHUB CONFIG (values-helm.yaml)          │
        │                                                │
        │  Checks:                                       │
        │  1. Is bob@company.com in allowed_users?   ❌  │
        │  2. Is "JupyterHub-Users" in allowed_groups? ✅ │
        │     → GRANT ACCESS                             │
        │                                                │
        │  3. Is bob@company.com in admin_users?     ❌  │
        │  4. Is "JupyterHub-Users" in admin_groups? ❌  │
        │     → NO ADMIN RIGHTS                          │
        └────────────┬───────────────────────────────────┘
                     ↓
        ┌────────────────────────────┐
        │  Bob gets:                 │
        │  ✅ Regular user access    │
        │  ❌ No admin panel         │
        └────────────────────────────┘
```

---

## 💡 Key Insights

### 1. Azure AD vs JupyterHub Roles Are Different!

| Azure AD Role | JupyterHub Role | Relationship |
|---------------|-----------------|--------------|
| Global Administrator | (none by default) | ❌ NO automatic mapping |
| User Administrator | (none by default) | ❌ NO automatic mapping |
| Member of "JupyterHub-Admins" group | JupyterHub Admin | ✅ YES (if configured in Helm) |

**Important**: Being a Global Admin in Azure AD does NOT make you a JupyterHub admin! You must explicitly configure this in `values-helm.yaml`.

---

### 2. Group-Based vs Email-Based Trade-offs

| Aspect | Group-Based | Email-Based |
|--------|-------------|-------------|
| **Flexibility** | ⭐⭐⭐⭐⭐ Add users without redeploy | ⭐⭐ Requires redeploy |
| **Setup complexity** | ⭐⭐⭐ Requires GroupMember permission | ⭐⭐⭐⭐⭐ Simple |
| **Scalability** | ⭐⭐⭐⭐⭐ Scales to 1000s | ⭐⭐ Manual list management |
| **Audit trail** | ⭐⭐⭐⭐⭐ Azure AD logs | ⭐⭐⭐ Git history |
| **Centralized mgmt** | ⭐⭐⭐⭐⭐ Same as other apps | ⭐⭐ JupyterHub-specific |

**Recommendation**: Use group-based for production!

---

### 3. What You Can Prepare NOW (No Subscription!)

✅ **Can do without subscription**:
- Create app registration in Azure AD
- Get Client ID, Client Secret, Tenant ID
- Create Azure AD groups (`JupyterHub-Users`, `JupyterHub-Admins`)
- Add users to groups
- Configure API permissions
- Grant admin consent
- Edit `values-helm.yaml` with credentials
- Test locally with Docker Compose

❌ **Need subscription for**:
- Deploy JupyterHub to Azure Kubernetes Service
- Create Azure resources (storage, networking, etc.)
- Access production JupyterHub URL

---

## 🚀 Recommended Configuration for Production

```yaml
# helm/values-helm.yaml
hub:
  config:
    JupyterHub:
      admin_access: true  # Admins can help users with their notebooks

  extraConfig:
    00-azure-ad-auth: |
      from oauthenticator.azuread import AzureAdOAuthenticator
      c.JupyterHub.authenticator_class = AzureAdOAuthenticator
      
      # Credentials (better to use Kubernetes secrets - see template 5)
      c.AzureAdOAuthenticator.tenant_id = "YOUR_TENANT_ID"
      c.AzureAdOAuthenticator.client_id = "YOUR_CLIENT_ID"
      c.AzureAdOAuthenticator.client_secret = "YOUR_CLIENT_SECRET"
      c.AzureAdOAuthenticator.oauth_callback_url = "https://jupyterhub.ccrolabs.com/hub/oauth_callback"
      
      # GROUP-BASED ACCESS (recommended!)
      c.AzureAdOAuthenticator.allowed_groups = {
          "JupyterHub-Users",
          "JupyterHub-Admins"  # Admins need access too!
      }
      
      # GROUP-BASED ADMIN
      c.AzureAdOAuthenticator.admin_groups = {
          "JupyterHub-Admins"
      }
```

**Why this is best**:
- ✅ Add/remove users in Azure AD → takes effect immediately
- ✅ Centralized user management (same as other org apps)
- ✅ Admins can help users debug notebooks
- ✅ Scales to large teams
- ✅ Audit trail in Azure AD

---

## 📚 Next Steps

1. **Read**: `AZURE-AD-AUTHORIZATION-GUIDE.md` (comprehensive guide)
2. **Copy config**: Use templates from `AZURE-AD-AUTH-QUICK-REFERENCE.md`
3. **Set up Azure AD**: Create app registration and groups (can do NOW!)
4. **Test locally**: Use `local-testing/` with Docker Compose
5. **Deploy**: Once you have Azure subscription access

---

## ❓ Still Confused?

Think of it like a **nightclub**:

- **Azure AD** = Bouncer at the door
  - Checks your ID (authentication)
  - Confirms you're on the guest list (group membership)
  
- **JupyterHub Config** = Club manager
  - Decides which guest lists are valid (`allowed_groups`)
  - Decides who gets VIP access (`admin_groups`)
  - Sets VIP privileges (`admin_access`)

The bouncer doesn't decide who's VIP - the club manager does!  
The club manager doesn't check IDs - the bouncer does!

**Both work together** to control access.


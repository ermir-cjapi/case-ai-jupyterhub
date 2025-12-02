# Multi-User Authentication Guide

This guide explains how to configure different authentication methods for JupyterHub to support multiple users, especially when you don't yet have access to Azure AD/Entra ID.

## Authentication Options Comparison

| Method | Setup Complexity | User Management | Best For | Azure AD Required |
|--------|-----------------|-----------------|----------|-------------------|
| DummyAuthenticator | Very Low | ❌ Shared password | Quick testing, proof-of-concept | ❌ No |
| NativeAuthenticator | Low | ✅ Per-user passwords | Lab with controlled users | ❌ No |
| GitHub OAuth | Medium | ✅ GitHub accounts | Teams already using GitHub | ❌ No |
| Entra ID (Azure AD) | Medium-High | ✅ Corporate directory | Production | ✅ Yes |

---

## Option 1: DummyAuthenticator (Simplest Multi-User Simulation)

### Overview

- **One shared password** for all users
- Users differentiate themselves by **username only**
- Perfect for testing multi-user resource isolation without complex auth setup

### How It Works

- User logs in with username `alice` and shared password → gets pod `jupyter-alice`
- User logs in with username `bob` and same password → gets pod `jupyter-bob`
- Each user has:
  - Separate home directory
  - Separate resources (CPU, memory, GPU)
  - Separate notebook server

### Configuration

Already configured in `infra/jupyterhub/values-v1.yaml`:

```yaml
hub:
  extraConfig:
    00-local-auth: |
      from jupyterhub.auth import DummyAuthenticator
      c.JupyterHub.authenticator_class = DummyAuthenticator
      
      # Shared password - CHANGE THIS
      c.DummyAuthenticator.password = "TestPass123!"
      
      # Admin users (by username)
      c.Authenticator.admin_users = {"admin", "yourname"}
      
      # Optional: Allow any username
      c.Authenticator.allow_all = True
```

### Testing Multi-User Access

**Test 1: Multiple browser sessions**

```bash
# Session 1 (regular browser)
Username: alice
Password: TestPass123!

# Session 2 (incognito/private window)
Username: bob
Password: TestPass123!

# Session 3 (different browser)
Username: carol
Password: TestPass123!
```

**Verify isolation:**

```bash
kubectl get pods -n jupyterhub-test

# You should see:
# jupyter-alice-...
# jupyter-bob-...
# jupyter-carol-...
```

**Test resource isolation:**

In Alice's notebook:
```python
import os
print(f"I am: {os.environ.get('JUPYTERHUB_USER')}")  # alice
!touch ~/alice-file.txt
```

In Bob's notebook:
```python
import os
print(f"I am: {os.environ.get('JUPYTERHUB_USER')}")  # bob
!ls ~/  # alice-file.txt will NOT be here (different home directory)
```

### Pros and Cons

**Pros:**
- ✅ Extremely simple setup
- ✅ No external dependencies
- ✅ Perfect for testing multi-user scenarios
- ✅ Great for demos and proof-of-concept

**Cons:**
- ❌ Security: Anyone with the password can log in as any user
- ❌ No real authentication
- ❌ Shared password must be rotated and distributed manually

### When to Use

- Initial lab testing
- Demos and presentations
- Learning JupyterHub behavior
- Testing resource allocation and GPU scheduling

---

## Option 2: NativeAuthenticator (Real Passwords, No External Auth)

### Overview

- **Per-user passwords** stored in JupyterHub database
- Admin approval workflow for new users
- Password policies (length, complexity, failed login tracking)

### Configuration

Edit `infra/jupyterhub/values-v1.yaml`:

```yaml
hub:
  extraConfig:
    00-install-native: |
      # Install nativeauthenticator if not in hub image
      import subprocess
      import sys
      try:
          import nativeauthenticator
      except ImportError:
          subprocess.check_call([sys.executable, "-m", "pip", "install", 
                               "jupyterhub-nativeauthenticator"])
    
    01-native-auth: |
      from nativeauthenticator import NativeAuthenticator
      c.JupyterHub.authenticator_class = NativeAuthenticator
      
      # Admin users (must be in admin_users to access admin panel)
      c.Authenticator.admin_users = {"admin"}
      
      # Security settings
      c.NativeAuthenticator.open_signup = False  # Require admin approval
      c.NativeAuthenticator.minimum_password_length = 10
      c.NativeAuthenticator.check_common_password = True
      c.NativeAuthenticator.allowed_failed_logins = 3
      c.NativeAuthenticator.seconds_before_next_try = 600  # 10 minutes lockout
      
      # Optional: Allow self-signup (less secure)
      # c.NativeAuthenticator.open_signup = True
      
      # Optional: Ask for additional info during signup
      # c.NativeAuthenticator.ask_email_on_signup = True
```

### User Management Workflow

**Step 1: Admin creates account or user signs up**

User visits: `https://your-jupyterhub/hub/signup`

Fills in:
- Username
- Password
- (Optional) Email

**Step 2: Admin authorizes user**

1. Admin logs in (must be in `admin_users` list)
2. Goes to: `https://your-jupyterhub/hub/authorize`
3. Sees pending users
4. Clicks "Authorize" for each user

**Step 3: User can now log in**

User returns to login page and uses their username/password.

### Managing Users

**Add users programmatically:**

```python
# In a JupyterHub admin notebook or via hub API
from jupyterhub.auth import NativeAuthenticator

auth = NativeAuthenticator()
auth.create_user({'name': 'alice', 'password': 'SecurePassword123!'})
```

**Via admin UI:**

1. Log in as admin
2. Go to `https://your-jupyterhub/hub/admin`
3. Add users, delete users, start/stop servers

**Command line (requires exec into hub pod):**

```bash
kubectl exec -it -n jupyterhub-test hub-... -- bash

# Inside the hub pod
python3 -c "
from nativeauthenticator import NativeAuthenticator
auth = NativeAuthenticator()
# Add user logic here
"
```

### Pros and Cons

**Pros:**
- ✅ Real per-user authentication
- ✅ Password policies
- ✅ Admin approval workflow
- ✅ No external dependencies
- ✅ Failed login protection

**Cons:**
- ❌ Passwords stored in JupyterHub database (needs backup)
- ❌ Manual user management
- ❌ No SSO integration
- ❌ Password reset requires admin intervention

### When to Use

- Lab environment with controlled user list
- Educational settings (class of students)
- Small teams (< 50 users)
- When external auth providers are not available yet

---

## Option 3: GitHub OAuth (Realistic Multi-User Without Azure AD)

### Overview

- Users authenticate with their **GitHub accounts**
- No password management needed
- Can restrict by GitHub organization/team
- Great for tech teams already on GitHub

### Setup Steps

**Step 1: Create GitHub OAuth App**

1. Go to GitHub → **Settings** → **Developer settings** → **OAuth Apps**
2. Click **New OAuth App**
3. Fill in:
   - **Application name**: `JupyterHub Lab`
   - **Homepage URL**: `https://jupyterhub.lab.local`
   - **Authorization callback URL**: `https://jupyterhub.lab.local/hub/oauth_callback`
4. Click **Register application**
5. Note the **Client ID**
6. Click **Generate a new client secret**
7. **Copy the secret** (you won't see it again!)

**Step 2: Update JupyterHub Configuration**

Edit `infra/jupyterhub/values-v1.yaml`:

```yaml
hub:
  extraConfig:
    10-github-auth: |
      from oauthenticator.github import GitHubOAuthenticator
      c.JupyterHub.authenticator_class = GitHubOAuthenticator
      
      # OAuth credentials from Step 1
      c.GitHubOAuthenticator.client_id = "your_client_id_here"
      c.GitHubOAuthenticator.client_secret = "your_client_secret_here"
      c.GitHubOAuthenticator.oauth_callback_url = "https://jupyterhub.lab.local/hub/oauth_callback"
      
      # Admin users (by GitHub username)
      c.Authenticator.admin_users = {"your-github-username"}
      
      # Access control options:
      
      # Option A: Allow all GitHub users
      c.Authenticator.allow_all = True
      
      # Option B: Allow specific users only
      # c.Authenticator.allowed_users = {"alice", "bob", "carol"}
      
      # Option C: Allow all members of a GitHub organization
      # c.GitHubOAuthenticator.allowed_organizations = {"your-org-name"}
      
      # Option D: Allow specific teams within an organization
      # c.GitHubOAuthenticator.allowed_organizations = {"your-org-name"}
      # c.GitHubOAuthenticator.allowed_teams = {
      #     "your-org-name:data-science-team",
      #     "your-org-name:ml-engineers"
      # }
```

**Step 3: Deploy**

```bash
# Comment out DummyAuthenticator or NativeAuthenticator
# Ensure only the GitHub OAuth block is active

./scripts/deploy_jhub_v1.sh
```

**Step 4: Test**

1. Visit `https://jupyterhub.lab.local`
2. You'll be redirected to GitHub
3. Click "Authorize <your-app-name>"
4. You'll be redirected back to JupyterHub and logged in

### Advanced: Organization/Team Restrictions

**Restrict to organization members:**

```python
c.GitHubOAuthenticator.allowed_organizations = {"your-company"}
```

**Restrict to specific teams:**

```python
c.GitHubOAuthenticator.allowed_organizations = {"your-company"}
c.GitHubOAuthenticator.allowed_teams = {
    "your-company:jupyterhub-users",
    "your-company:data-scientists"
}
```

**Make certain teams admins:**

```python
# Regular users from these teams
c.GitHubOAuthenticator.allowed_teams = {
    "your-company:data-science",
    "your-company:ml-engineers"
}

# Admins from this team
c.Authenticator.admin_users = {"alice", "bob"}  # Specific users
# OR
c.GitHubOAuthenticator.admin_users = {"alice"}
```

### Scopes and Permissions

By default, GitHubOAuthenticator requests:
- `user:email` – To get user email
- `read:org` – To check organization membership (if using org restrictions)

No write access to repositories or other data.

### Pros and Cons

**Pros:**
- ✅ Real authentication without managing passwords
- ✅ Users already have GitHub accounts
- ✅ Organization/team-based access control
- ✅ No password reset requests
- ✅ Audit trail via GitHub

**Cons:**
- ❌ Requires external service (GitHub.com)
- ❌ Users need GitHub accounts
- ❌ Not suitable if company doesn't use GitHub
- ❌ OAuth can be blocked by some corporate firewalls

### When to Use

- Tech teams already using GitHub
- Open source projects
- When you want realistic multi-user auth without setting up identity infrastructure
- Bridge solution while waiting for Entra ID setup at AIV

---

## Option 4: Entra ID / Azure AD (Production for AIV)

### Overview

- Enterprise Single Sign-On (SSO)
- Integrated with corporate directory
- Group-based access control
- Required for final AIV production deployment

### Prerequisites

- Azure/Entra ID tenant
- Permissions to register applications
- JupyterHub must use HTTPS (required for OAuth)

### Setup Steps

**Step 1: Register Application in Entra ID**

1. Go to **Azure Portal** → **Azure Active Directory** → **App registrations**
2. Click **New registration**
3. Fill in:
   - **Name**: `JupyterHub Lab` (or `JupyterHub Production`)
   - **Supported account types**: Accounts in this organizational directory only
   - **Redirect URI**: 
     - Platform: `Web`
     - URL: `https://jupyterhub.lab.local/hub/oauth_callback`
4. Click **Register**
5. Note the **Application (client) ID**
6. Note the **Directory (tenant) ID**

**Step 2: Create Client Secret**

1. Go to **Certificates & secrets** → **Client secrets**
2. Click **New client secret**
3. Description: `JupyterHub OAuth`
4. Expiry: Choose based on policy (e.g., 12 months)
5. Click **Add**
6. **Copy the secret value** (you won't see it again!)

**Step 3: Configure API Permissions (Optional)**

1. Go to **API permissions**
2. Default permissions are usually sufficient:
   - `User.Read` (delegated)
3. If you want group-based auth, add:
   - `GroupMember.Read.All` (delegated or application)
4. Click **Grant admin consent** for your tenant

**Step 4: Update JupyterHub Configuration**

Edit `infra/jupyterhub/values-v1.yaml` (or `values-aiv-prod.yaml`):

```yaml
hub:
  extraConfig:
    10-entra-id-auth: |
      from oauthenticator.azuread import AzureAdOAuthenticator
      c.JupyterHub.authenticator_class = AzureAdOAuthenticator
      
      # From Azure App Registration
      c.AzureAdOAuthenticator.tenant_id = "your-tenant-id"
      c.AzureAdOAuthenticator.client_id = "your-client-id"
      c.AzureAdOAuthenticator.client_secret = "your-client-secret"
      c.AzureAdOAuthenticator.oauth_callback_url = "https://jupyterhub.lab.local/hub/oauth_callback"
      
      # Admin users by email or username
      c.Authenticator.admin_users = {"admin@yourcompany.com", "alice@yourcompany.com"}
      
      # Access control options:
      
      # Option A: Allow all users in the tenant
      c.Authenticator.allow_all = True
      
      # Option B: Allow specific users
      # c.Authenticator.allowed_users = {"alice@yourcompany.com", "bob@yourcompany.com"}
      
      # Option C: Allow based on Entra ID group membership
      # c.AzureAdOAuthenticator.allowed_groups = {
      #     "jupyterhub-users",  # Group display name or object ID
      #     "data-science-team"
      # }
      
      # Option D: Admin based on group
      # c.AzureAdOAuthenticator.admin_groups = {"jupyterhub-admins"}
```

**Step 5: Deploy and Test**

```bash
./scripts/deploy_jhub_v1.sh
```

Visit JupyterHub, you'll be redirected to Microsoft login.

### Group-Based Access (Recommended for AIV)

Create Entra ID groups for access control:

**In Azure Portal:**

1. **Azure Active Directory** → **Groups** → **New group**
2. Create groups:
   - `JupyterHub-Admins` – Admin access
   - `JupyterHub-Users` – Regular user access
   - `JupyterHub-GPU-Users` – Users allowed GPU profiles (optional)

**In JupyterHub config:**

```python
c.AzureAdOAuthenticator.allowed_groups = {
    "JupyterHub-Users",
    "JupyterHub-GPU-Users"
}
c.AzureAdOAuthenticator.admin_groups = {"JupyterHub-Admins"}
```

### Pros and Cons

**Pros:**
- ✅ Enterprise SSO
- ✅ Corporate directory integration
- ✅ Centralized user management
- ✅ Meets compliance requirements
- ✅ Group-based access control
- ✅ Audit trail

**Cons:**
- ❌ Requires Azure/Entra ID subscription
- ❌ More complex setup
- ❌ Requires coordination with IT/identity team

### When to Use

- Production deployments
- Enterprise environments
- AIV final deployment
- When corporate SSO is required

---

## Migration Path: Lab → AIV Production

### Recommended Sequence

**Phase 1: Lab Setup (Your NVIDIA Server)**

```
DummyAuthenticator (quick test)
    ↓
GitHub OAuth (realistic multi-user)
    ↓
Entra ID (test with your tenant, if available)
```

**Phase 2: AIV Production**

```
Entra ID with AIV's tenant
```

### Configuration Management

Keep environment-specific auth in separate value files:

**`infra/jupyterhub/values-lab.yaml`** (your environment):
```yaml
hub:
  extraConfig:
    10-github-auth: |
      # GitHub OAuth config
```

**`infra/jupyterhub/values-aiv-prod.yaml`** (AIV environment):
```yaml
hub:
  extraConfig:
    10-entra-id-auth: |
      # Entra ID config with AIV tenant
```

---

## Testing Multi-User Scenarios

### Test Cases to Verify

**1. User Isolation**
- Login as multiple users
- Verify separate pods: `kubectl get pods -n jupyterhub-test`
- Verify separate home directories
- Verify users can't access each other's files

**2. Resource Limits**
- Start notebooks as different users
- Check CPU/memory usage: `kubectl top pods -n jupyterhub-test`
- Verify limits are enforced

**3. GPU Allocation**
- If using GPUs, verify:
  - Only designated users get GPUs
  - GPU not shared between users (unless intended)
  - `nvidia-smi` in notebook shows correct GPU

**4. Admin Functions**
- Login as admin user
- Access admin panel: `https://your-hub/hub/admin`
- Start/stop other users' servers
- Add new users (if using NativeAuthenticator)

**5. Authentication Edge Cases**
- Wrong password → denied
- Unauthorized user → denied
- Expired session → redirect to login
- Concurrent logins from same user → allowed or blocked based on config

---

## Troubleshooting

### DummyAuthenticator Issues

**Problem**: Can't login with any password

```bash
# Check hub logs
kubectl logs -n jupyterhub-test -l component=hub --tail=50

# Verify config
kubectl get configmap -n jupyterhub-test hub -o yaml | grep -A 10 extraConfig
```

### GitHub OAuth Issues

**Problem**: "Redirect URI mismatch"

- Ensure callback URL in GitHub app matches exactly: `https://your-host/hub/oauth_callback`
- Check for trailing slashes
- Verify HTTPS is working

**Problem**: "Not authorized"

- Check `allowed_organizations` or `allowed_users` settings
- Verify user is member of the specified org/team
- Check hub logs for authorization details

### Entra ID Issues

**Problem**: "AADSTS50011: Reply URL mismatch"

- Callback URL in Azure must match exactly
- Check both the URL and platform type (Web)

**Problem**: "User not in allowed groups"

- Verify group names or object IDs
- User must be direct member (not nested groups, unless configured)
- Check group membership in Azure Portal

**Problem**: Token/secret expired

- Regenerate client secret in Azure
- Update JupyterHub config
- Redeploy

---

## Summary and Recommendations

For your **lab environment** without Azure AD access:

1. **Start with DummyAuthenticator** for initial setup and smoke tests
2. **Switch to GitHub OAuth** for realistic multi-user testing if your team uses GitHub
3. **Use NativeAuthenticator** if you prefer local accounts over external providers

For **AIV production**:

1. Work with AIV IT to set up **Entra ID** app registration
2. Test in lab with your own Entra tenant first (if available)
3. Switch to AIV's tenant for final deployment

All authentication methods provide proper **user isolation**, **resource limits**, and **multi-user functionality** – the difference is mainly in how users prove their identity.


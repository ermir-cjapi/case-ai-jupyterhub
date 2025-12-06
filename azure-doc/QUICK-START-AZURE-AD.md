# 🚀 Quick Start: Azure AD for JupyterHub

**Time needed**: 15 minutes  
**Prerequisites**: Global Administrator access to Azure AD tenant

---

## 📝 What You'll Create

```
Azure AD:
├─ App Registration: "JupyterHub Production"
├─ Group: "JupyterHub-Users" (regular access)
└─ Group: "JupyterHub-Admins" (admin access)

JupyterHub Config:
└─ Group-based authentication with Azure AD
```

---

## ⚡ Step 1: Create App Registration (5 min)

### 1.1 Navigate to App Registrations

```
Azure Portal → Search "Microsoft Entra ID" 
→ App registrations → + New registration
```

### 1.2 Fill in Form

```
Name: JupyterHub Production

Supported account types:
● Accounts in this organizational directory only (Single tenant)

Redirect URI:
Platform: Web
URL: https://jupyterhub.ccrolabs.com/hub/oauth_callback
```

Click **Register**

### 1.3 Copy Credentials

From the **Overview** page, copy these values:

```
┌─────────────────────────────────────────────────┐
│ SAVE THESE VALUES:                              │
├─────────────────────────────────────────────────┤
│                                                 │
│ Tenant ID:                                      │
│ [                                            ]  │
│                                                 │
│ Client ID:                                      │
│ [                                            ]  │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 🔑 Step 2: Create Client Secret (2 min)

### 2.1 Generate Secret

```
In your app → Certificates & secrets 
→ Client secrets → + New client secret
```

```
Description: JupyterHub Production Secret
Expires: 24 months
```

Click **Add**

### 2.2 Copy Secret Value

**⚠️ COPY IMMEDIATELY - You can't see this again!**

```
┌─────────────────────────────────────────────────┐
│ Client Secret:                                  │
│ [                                            ]  │
└─────────────────────────────────────────────────┘
```

---

## 🔐 Step 3: Configure Permissions (3 min)

### 3.1 Add Permissions

```
In your app → API permissions → + Add a permission
→ Microsoft Graph → Delegated permissions
```

**Search and select these** (check each box):
- [ ] `email`
- [ ] `openid`
- [ ] `profile`
- [ ] `User.Read`
- [ ] `GroupMember.Read.All`

Click **Add permissions**

### 3.2 Grant Admin Consent

```
Click: ✓ Grant admin consent for [Your Organization]
→ Click "Yes"
```

**Verify**: All permissions show green checkmark ✓

---

## 👥 Step 4: Create Groups (5 min)

### 4.1 Create JupyterHub-Users Group

```
Azure AD → Groups → + New group
```

```
Group type: Security
Group name: JupyterHub-Users
Group description: Regular users who can access JupyterHub
Azure AD roles: No
Membership type: Assigned
Owners: [Add yourself]
Members: [Add users or skip for now]
```

Click **Create**

### 4.2 Create JupyterHub-Admins Group

```
Azure AD → Groups → + New group
```

```
Group type: Security
Group name: JupyterHub-Admins
Group description: Administrators who can manage JupyterHub
Azure AD roles: No
Membership type: Assigned
Owners: [Add yourself]
Members: [Add yourself NOW!]
```

Click **Create**

### 4.3 Add Yourself to Both Groups

**Important**: Make sure you're in BOTH groups!

```
Groups → JupyterHub-Users → Members → + Add members → [Find yourself] → Select
Groups → JupyterHub-Admins → Members → + Add members → [Find yourself] → Select
```

---

## ⚙️ Step 5: Update Configuration (2 min)

### 5.1 Open Config File

```bash
# Open in your editor:
helm/values-helm.yaml
```

### 5.2 Find Credentials Section

Look for lines ~60-63:

```python
c.AzureAdOAuthenticator.tenant_id = "YOUR_TENANT_ID_HERE"
c.AzureAdOAuthenticator.client_id = "YOUR_CLIENT_ID_HERE"
c.AzureAdOAuthenticator.client_secret = "YOUR_CLIENT_SECRET_HERE"
```

### 5.3 Replace with Your Values

Paste your actual credentials:

```python
c.AzureAdOAuthenticator.tenant_id = "12345678-1234-1234-1234-123456789abc"
c.AzureAdOAuthenticator.client_id = "87654321-4321-4321-4321-cba987654321"
c.AzureAdOAuthenticator.client_secret = "AbC123~XyZ789_defGHI456-jklMNO789"
```

### 5.4 Save File

```bash
# Save and close the file
```

**Done!** Configuration is ready for deployment.

---

## ✅ Verification Checklist

Before deploying, verify:

### Azure AD
- [ ] App registration created
- [ ] Tenant ID copied (format: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX)
- [ ] Client ID copied (format: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX)
- [ ] Client Secret copied (includes letters, numbers, ~ or -)
- [ ] Redirect URI: `https://jupyterhub.ccrolabs.com/hub/oauth_callback`
- [ ] 5 permissions added (email, openid, profile, User.Read, GroupMember.Read.All)
- [ ] Admin consent granted (green checkmarks)
- [ ] Group `JupyterHub-Users` created (Security, Assigned)
- [ ] Group `JupyterHub-Admins` created (Security, Assigned)
- [ ] You are member of `JupyterHub-Users`
- [ ] You are member of `JupyterHub-Admins`

### Configuration
- [ ] `values-helm.yaml` updated with Tenant ID
- [ ] `values-helm.yaml` updated with Client ID
- [ ] `values-helm.yaml` updated with Client Secret
- [ ] File saved

---

## 🚀 Deploy (When You Have Subscription)

### Option A: Helm Deployment

```bash
cd helm/
./deploy_jhub_helm.sh
```

### Option B: AIV Production Deployment

```bash
cd aiv-production/scripts/
./deploy-aiv-production.sh
```

---

## 🧪 Test Login

After deployment:

1. **Visit**: `https://jupyterhub.ccrolabs.com`
2. **Click**: Sign in (redirects to Azure AD)
3. **Login**: With your Microsoft credentials
4. **Success**: You should land on JupyterHub home page

### Test Admin Access

```
Visit: https://jupyterhub.ccrolabs.com/hub/admin
```

You should see:
- ✅ List of all users
- ✅ Server status
- ✅ Start/stop buttons

---

## 👥 Add More Users (After Deployment)

### Add Regular User

```
Azure AD → Groups → JupyterHub-Users 
→ Members → + Add members → Select user → Done
```

User can login immediately (no redeploy needed!)

### Make Someone Admin

```
Azure AD → Groups → JupyterHub-Admins
→ Members → + Add members → Select user → Done
```

**Remember**: Admins should be in BOTH groups!

### Invite External User (Guest)

```
Azure AD → Users → + New user → Invite external user
→ Email: user@outlook.com
→ Groups: [Select JupyterHub-Users]
→ Invite
```

User receives email → accepts → can login

---

## 📊 Quick Reference

### Your Credentials

```
App Name: JupyterHub Production

Tenant ID: [Your 36-character UUID]
Client ID: [Your 36-character UUID]
Client Secret: [Your secret string]

Redirect URI: https://jupyterhub.ccrolabs.com/hub/oauth_callback

Expires: [Set calendar reminder!]
```

### Your Groups

```
JupyterHub-Users
├─ Type: Security
├─ Purpose: Regular access
└─ Members: [Your team]

JupyterHub-Admins
├─ Type: Security
├─ Purpose: Admin access
└─ Members: [You + other admins]
```

### Configuration

```python
# In helm/values-helm.yaml

Allowed Groups:
  - JupyterHub-Users
  - JupyterHub-Admins

Admin Groups:
  - JupyterHub-Admins
```

---

## 🚨 Troubleshooting

### Can't create app registration
**Problem**: Missing permissions  
**Solution**: Verify you're Global Administrator

### "Invalid redirect URI" error
**Problem**: Mismatch between app registration and config  
**Solution**: Ensure URIs match exactly (check https://)

### User can't login
**Problem**: Not in any group  
**Solution**: Add to JupyterHub-Users or JupyterHub-Admins

### Groups not working
**Problem**: Missing permission or consent  
**Solution**: Check GroupMember.Read.All granted with green checkmark

### Admin can't see admin panel
**Problem**: Not in JupyterHub-Admins group  
**Solution**: Add to JupyterHub-Admins (and JupyterHub-Users!)

### Client secret expired
**Problem**: Secret past expiration date  
**Solution**: Create new secret, update config, redeploy

---

## 📚 More Information

For detailed information, see:

- **Step-by-step guide**: `SETUP-AZURE-APP-REGISTRATION.md`
- **Complete checklist**: `NEXT-STEPS-CHECKLIST.md`
- **Visual diagrams**: `AZURE-AD-SETUP-DIAGRAM.md`
- **Configuration templates**: `AZURE-AD-AUTH-QUICK-REFERENCE.md`
- **Authorization guide**: `AZURE-AD-AUTHORIZATION-GUIDE.md`

---

## ✨ What You've Achieved

After completing this guide:

✅ Azure AD authentication configured  
✅ Group-based access control  
✅ Dynamic user management (add/remove without redeploy)  
✅ Admin capabilities enabled  
✅ Production-ready security  

**Total time**: 15 minutes  
**Future time to add users**: 30 seconds (no redeploy!)

---

## 🎯 Next Steps

1. ✅ Complete all steps above
2. ⏸️ Wait for Azure subscription access
3. 🚀 Deploy JupyterHub
4. ✅ Test authentication
5. 👥 Add team members to groups
6. 🎉 Start using JupyterHub!

---

**Need more details?** See `AZURE-AD-SETUP-SUMMARY.md` for comprehensive overview.


# Deploy Graph API Solution - Quick Guide

## What Changed

✅ **New**: Fetch groups via Microsoft Graph API (works with Azure AD Free)  
❌ **Removed**: Trying to extract groups from token (doesn't work with Free tier)

---

## Prerequisites

Before deploying, ensure:

1. ✅ Azure AD App Registration has `GroupMember.Read.All` permission
2. ✅ Admin consent granted for the permission
3. ✅ Kubernetes secret `jupyterhub-azure-oauth` exists

### Check/Add Graph API Permission

1. Go to **Azure Portal** → **App Registrations** → **JupyterHub Production**
2. Click **API Permissions**
3. Verify you have:
   - `User.Read` (Delegated) ✅
   - `GroupMember.Read.All` (Delegated) ✅ **← Must have this**
4. If `GroupMember.Read.All` is missing:
   - Click **Add a permission**
   - Choose **Microsoft Graph** → **Delegated permissions**
   - Search for `GroupMember.Read.All` and select it
   - Click **Add permissions**
   - **IMPORTANT**: Click **Grant admin consent for [Your Org]**

---

## Deployment Steps

### 1. Clean Deployment (Recommended)

```bash
# SSH to your NVIDIA server
ssh ecjapi@your-server

# Navigate to helm directory
cd ~/case-ai-jupyterhub/helm

# Delete existing deployment
./delete_jhub_helm.sh

# Wait 30 seconds for cleanup
sleep 30

# Verify everything is gone
kubectl get all -n jupyterhub-test
# Should show: No resources found

# Delete the database PVC (fresh start)
kubectl delete pvc hub-db-dir -n jupyterhub-test

# Deploy with new Graph API solution
./deploy_jhub_helm.sh
```

### 2. Watch Deployment

```bash
# Watch pods come up
kubectl get pods -n jupyterhub-test -w

# Wait for:
# hub-xxxxx         1/1   Running
# proxy-xxxxx       1/1   Running
# (Press Ctrl+C to exit watch mode)
```

### 3. Check Hub Logs (Verify Upgrade)

```bash
# Check that oauthenticator v17+ is installed
kubectl logs -n jupyterhub-test -l component=hub --tail=50 | grep -i "oauthenticator"

# Expected output:
# Upgrading oauthenticator to v17+...
# oauthenticator v17+ installed to: /home/jovyan/.local/lib/python3.11/site-packages
# oauthenticator upgrade complete!
```

---

## Testing

### 1. Login Test

1. Open browser: `https://jupyterhub.ccrolabs.com`
2. Click **Sign in with Azure AD**
3. Login with your Azure credentials
4. **Watch the terminal** for detailed logs

### 2. Expected Logs (Success)

```bash
# Watch logs in real-time
kubectl logs -n jupyterhub-test -l component=hub -f

# You should see:
================================================================================
🔍 FETCHING USER GROUPS FROM MICROSOFT GRAPH API
================================================================================
✅ Access token present (length: 1234 chars)
📡 Making API request to: https://graph.microsoft.com/v1.0/me/memberOf
📥 Response status code: 200
✅ API call successful!
📦 Found 2 membership objects
  - Type: #microsoft.graph.group, Name: 'JupyterHub-Admins', ID: d6c49ed5-eefc-48c4-90d0-2026f5fe3916
    ✅ Added to group list
  - Type: #microsoft.graph.group, Name: 'JupyterHub-Users', ID: 6543851f-fd97-40e8-b097-ab5a71e44ef2
    ✅ Added to group list

✅ FINAL RESULT: User belongs to 2 Azure AD groups:
   - d6c49ed5-eefc-48c4-90d0-2026f5fe3916
   - 6543851f-fd97-40e8-b097-ab5a71e44ef2
================================================================================
```

### 3. Test Admin Access

1. After login, click your username (top right)
2. Click **Admin** in the dropdown
3. You should see the admin panel with:
   - User list
   - Add/remove users
   - Start/stop servers

**If you see "403 Forbidden"**: Groups didn't match. Check logs.

---

## Troubleshooting

### Error: 403 Forbidden (Permission Denied)

```
❌ PERMISSION DENIED (403 Forbidden)
   TO FIX:
   1. Go to Azure Portal → App Registrations → Your App
   2. API Permissions → Add 'GroupMember.Read.All' (Delegated)
   3. Click 'Grant admin consent'
```

**Solution**:
1. Add `GroupMember.Read.All` permission (see Prerequisites above)
2. **Grant admin consent** (critical!)
3. Redeploy JupyterHub

### Error: 401 Unauthorized

```
❌ AUTHENTICATION FAILED (401 Unauthorized)
```

**Solution**: Token might be expired or invalid. Try:
1. Clear browser cache
2. Login again
3. Check logs for more details

### No Groups Found

```
✅ FINAL RESULT: User belongs to 0 Azure AD groups:
```

**Possible causes**:
1. User not added to any groups in Azure AD
2. Groups are nested (Graph API only returns direct memberships)
3. Groups are distribution lists, not security groups

**Solution**:
1. Go to **Azure Portal** → **Groups**
2. Find your groups (`JupyterHub-Admins`, `JupyterHub-Users`)
3. Click **Members** → **Add members**
4. Add your user
5. Wait 5 minutes for replication
6. Login again

### Hub Pod Crashes

```bash
# Check hub logs for errors
kubectl logs -n jupyterhub-test -l component=hub --tail=100

# Common issues:
# 1. Python syntax error in values-helm.yaml
# 2. Missing `requests` library
# 3. Indentation errors in extraConfig
```

**Solution**: Check logs for specific error, fix `values-helm.yaml`, redeploy.

---

## Verify Graph API Permissions (Azure Portal)

### Option 1: Via Azure Portal

1. **Azure Portal** → **App Registrations** → **JupyterHub Production**
2. Click **API Permissions**
3. You should see:

   ```
   Microsoft Graph (2)
   ├── User.Read (Delegated) ✅ Granted for Your Org
   └── GroupMember.Read.All (Delegated) ✅ Granted for Your Org
   ```

4. If "Granted" is missing, click **Grant admin consent**

### Option 2: Via Graph API Test

You can test the permission manually:

```bash
# Get an access token (replace with your values)
TENANT_ID="your-tenant-id"
CLIENT_ID="your-client-id"
CLIENT_SECRET="your-client-secret"

# Get token
TOKEN=$(curl -s -X POST \
  "https://login.microsoftonline.com/$TENANT_ID/oauth2/v2.0/token" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" \
  -d "grant_type=client_credentials" \
  -d "scope=https://graph.microsoft.com/.default" | jq -r '.access_token')

# Test Graph API
curl -H "Authorization: Bearer $TOKEN" \
  "https://graph.microsoft.com/v1.0/users/your-email@company.com/memberOf"

# Expected: JSON with list of groups
# If 403: Permission not granted
```

---

## Post-Deployment Validation

### 1. Check JupyterHub Version

```bash
kubectl exec -n jupyterhub-test -it $(kubectl get pod -n jupyterhub-test -l component=hub -o name) -- jupyterhub --version
```

### 2. Check Python Packages

```bash
kubectl exec -n jupyterhub-test -it $(kubectl get pod -n jupyterhub-test -l component=hub -o name) -- pip list | grep -E "(oauthenticator|requests|PyJWT)"

# Expected:
# oauthenticator    17.0.0  (or higher)
# requests          2.31.0  (or higher)
# PyJWT             2.8.0   (or higher)
```

### 3. Test Login End-to-End

- [ ] Can login with Azure AD
- [ ] See detailed logs in hub pod
- [ ] Groups fetched successfully
- [ ] Admin access works
- [ ] Can start notebook server
- [ ] Can access JupyterLab

---

## Rollback (If Needed)

If the new solution doesn't work, you can rollback:

```bash
# Restore Git version (if you committed before)
cd ~/case-ai-jupyterhub
git checkout HEAD~1 helm/values-helm.yaml

# Or use hardcoded admin (temporary)
# Edit helm/values-helm.yaml:
c.Authenticator.allow_all = True
c.Authenticator.admin_users = {"your-email@company.com"}

# Redeploy
cd helm
./deploy_jhub_helm.sh
```

---

## Next Steps

Once working:

1. ✅ Test with multiple users
2. ✅ Test with users in different groups
3. ✅ Document your group IDs in a secure location
4. ✅ Set up monitoring/alerting for Graph API failures
5. ✅ Consider upgrading to Azure AD Premium P1 for production (optional)

---

## Quick Reference

### Your Group IDs

```python
# JupyterHub-Admins (admin rights)
"d6c49ed5-eefc-48c4-90d0-2026f5fe3916"

# JupyterHub-Users (regular access)
"6543851f-fd97-40e8-b097-ab5a71e44ef2"

# Unknown group (your current membership)
"4fb32c31-b135-43d5-a00e-9e566e6aceff"
```

### Useful Commands

```bash
# Watch logs
kubectl logs -n jupyterhub-test -l component=hub -f

# Restart hub (reload config)
kubectl rollout restart deployment hub -n jupyterhub-test

# Delete database (fresh start)
kubectl delete pvc hub-db-dir -n jupyterhub-test

# Full cleanup
./delete_jhub_helm.sh
kubectl delete pvc hub-db-dir -n jupyterhub-test
```

---

**Good luck! 🚀**

If you see the detailed Graph API logs with your groups, **IT WORKS!** 🎉


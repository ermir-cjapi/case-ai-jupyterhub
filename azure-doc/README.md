# Azure AD Integration Documentation

## Overview

This directory contains comprehensive documentation for integrating JupyterHub with Azure AD (Microsoft Entra ID) for authentication and group-based authorization.

---

## The Problem We Solved

**Challenge**: Azure AD Free tier does NOT include group claims in OAuth tokens, making group-based authorization seemingly impossible.

**Solution**: Fetch user groups via Microsoft Graph API after authentication.

---

## Documentation Index

### 1. 📘 [Azure AD Free Tier Solution](./AZURE-AD-FREE-TIER-SOLUTION.md)

**Read this first!**

- Explains Azure AD tier limitations (Free vs Premium)
- Why groups aren't in OAuth tokens
- How the Microsoft Graph API solution works
- Performance considerations
- Migration path to Premium (if needed)

**Key Topics**:
- Azure AD tier comparison
- Microsoft Graph API implementation
- Debugging guide with logs
- Rate limits and performance

---

### 2. 🚀 [Deployment Guide](./DEPLOY-GRAPH-API-SOLUTION.md)

**Step-by-step deployment instructions**

- Prerequisites checklist
- Azure AD permission setup
- Deployment commands
- Testing procedures
- Troubleshooting common errors

**Use this when**:
- Deploying for the first time
- Upgrading from token-based to Graph API
- Troubleshooting login issues

---

### 3. 📝 [Post-Mortem Analysis](./POST-MORTEM.md)

**What we learned the hard way**

- Timeline of 8-hour debugging session
- What went wrong (and why)
- What we did right
- Lessons learned
- Prevention strategies

**Use this when**:
- Learning from our mistakes
- Training new team members
- Planning future integrations
- Understanding the "why" behind decisions

---

## Quick Start

### For First-Time Setup

1. **Read**: [AZURE-AD-FREE-TIER-SOLUTION.md](./AZURE-AD-FREE-TIER-SOLUTION.md) (15 min)
2. **Configure**: Add `GroupMember.Read.All` permission in Azure Portal
3. **Deploy**: Follow [DEPLOY-GRAPH-API-SOLUTION.md](./DEPLOY-GRAPH-API-SOLUTION.md)
4. **Test**: Login and watch logs for Graph API calls

### For Troubleshooting

1. **Check**: [DEPLOY-GRAPH-API-SOLUTION.md](./DEPLOY-GRAPH-API-SOLUTION.md) → Troubleshooting section
2. **Review**: Hub pod logs for detailed error messages
3. **Verify**: Azure AD permissions are granted
4. **Reference**: [POST-MORTEM.md](./POST-MORTEM.md) for common pitfalls

---

## Architecture Diagram

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
│   Azure AD      │ ← Free Tier (Groups NOT in token)
│   OAuth Login   │
└──────┬──────────┘
       │ 3. Returns: access_token + id_token
       │    (id_token has NO groups)
       ↓
┌─────────────────┐
│   JupyterHub    │
│   Authenticator │ 4. Extracts access_token
└──────┬──────────┘
       │ 5. Call Graph API
       ↓
┌─────────────────────────────┐
│  Microsoft Graph API        │
│  GET /me/memberOf           │
│  Authorization: Bearer      │
└──────┬──────────────────────┘
       │ 6. Returns: List of groups
       ↓
┌─────────────────┐
│   JupyterHub    │ 7. Check allowed_groups
│   Authorization │    & admin_groups
└─────────────────┘
       │ 8. Grant/Deny Access
       ↓
┌─────────────────┐
│  User's         │
│  Notebook       │
└─────────────────┘
```

---

## Key Files

### Configuration

```
case-ai-jupyterhub/
├── helm/
│   ├── values-helm.yaml           ← Main config with Graph API code
│   ├── deploy_jhub_helm.sh        ← Deployment script
│   └── create-azure-secret.sh     ← Creates K8s secret for credentials
│
└── azure-doc/                      ← You are here
    ├── README.md                   ← This file
    ├── AZURE-AD-FREE-TIER-SOLUTION.md
    ├── DEPLOY-GRAPH-API-SOLUTION.md
    └── POST-MORTEM.md
```

### Critical Code Section

The Graph API integration is in `helm/values-helm.yaml`:

```yaml
hub:
  extraConfig:
    01-azure-ad-auth: |
      # Custom function: fetch_user_groups_from_graph_api()
      # Custom class: AzureAdGraphAuthenticator
      # Calls: https://graph.microsoft.com/v1.0/me/memberOf
```

---

## Common Tasks

### Add a New User Group

1. **Azure Portal** → **Groups** → **New group**
2. Copy the group's **Object ID** (UUID)
3. Edit `helm/values-helm.yaml`:
   ```python
   c.AzureAdGraphAuthenticator.allowed_groups = {
       "existing-group-id",
       "new-group-id",  # ← Add here
   }
   ```
4. Redeploy:
   ```bash
   cd helm
   ./deploy_jhub_helm.sh
   ```

### Change Admin Group

1. Edit `helm/values-helm.yaml`:
   ```python
   c.AzureAdGraphAuthenticator.admin_groups = {
       "new-admin-group-id"
   }
   ```
2. Redeploy
3. Users must re-login for changes to take effect

### Check Current Groups

```bash
# Watch hub logs during login
kubectl logs -n jupyterhub-test -l component=hub -f

# Look for:
# ✅ FINAL RESULT: User belongs to 2 Azure AD groups:
#    - d6c49ed5-eefc-48c4-90d0-2026f5fe3916
#    - 6543851f-fd97-40e8-b097-ab5a71e44ef2
```

### Test Graph API Manually

See [DEPLOY-GRAPH-API-SOLUTION.md](./DEPLOY-GRAPH-API-SOLUTION.md) → "Verify Graph API Permissions"

---

## FAQ

### Q: Why not just use email-based access control?

**A**: Email-based requires redeploying JupyterHub every time you add/remove users. Group-based lets you manage access in Azure AD without redeployment.

### Q: Can I use group display names instead of IDs?

**A**: Not with Free tier. Azure AD Free sends Object IDs, not names. Premium P1/P2 can be configured to send names, but IDs are more reliable anyway (names can change).

### Q: How much does Azure AD Premium cost?

**A**: 
- **Premium P1**: ~$6/user/month
- **Premium P2**: ~$9/user/month

[Official Pricing](https://www.microsoft.com/en-us/security/business/microsoft-entra-pricing)

### Q: Should I upgrade to Premium?

**A**: Consider upgrading if:
- You have >100 users (avoid Graph API rate limits)
- Login speed is critical (<500ms)
- You want simpler code (groups in token automatically)
- You need Conditional Access policies

**Stay with Free if**:
- Small team (<50 users)
- Development/testing environment
- Cost is a concern
- Current solution works fine

### Q: What if Graph API is down?

**A**: Users won't be able to login. The code has timeout protection (10 seconds) but no fallback. For production, consider:
- Monitoring Graph API availability
- Alerting on failures
- Emergency hardcoded admin user

### Q: How do I rotate Azure AD credentials?

See `helm/create-azure-secret.sh` for credential management.

---

## Monitoring & Alerts (Recommended)

### What to Monitor

1. **Graph API Success Rate**
   - Watch logs for 403/401 errors
   - Alert if >5% failures

2. **Login Duration**
   - Normal: 700-1000ms
   - Slow: >2000ms (investigate)

3. **Graph API Rate Limits**
   - Microsoft Graph: 2,000 req/sec
   - Alert at 80% usage

### How to Monitor

```bash
# Count Graph API errors in last hour
kubectl logs -n jupyterhub-test -l component=hub --since=1h | grep -c "❌ PERMISSION DENIED"

# Check average login time
kubectl logs -n jupyterhub-test -l component=hub --tail=1000 | grep "FETCHING USER GROUPS" -A 20 | grep "Response status"
```

---

## Upgrade Path to Premium

When you're ready to simplify:

### Before (Current - Graph API)

```python
class AzureAdGraphAuthenticator(AzureAdOAuthenticator):
    async def update_auth_model(self, auth_model):
        groups = await fetch_user_groups_from_graph_api(...)
        auth_model['groups'] = groups
        return auth_model
```

### After (Premium - Token-based)

```python
from oauthenticator.azuread import AzureAdOAuthenticator
c.JupyterHub.authenticator_class = AzureAdOAuthenticator
c.AzureAdOAuthenticator.manage_groups = True
# Groups automatically in token!
```

**Much simpler**, but costs $6/user/month.

---

## Support & Troubleshooting

### First Steps

1. **Check hub logs**: `kubectl logs -n jupyterhub-test -l component=hub --tail=200`
2. **Look for detailed error messages** (we have lots of logging!)
3. **Check Azure AD permissions** in Portal

### Common Issues & Solutions

| Error | Solution |
|-------|----------|
| 403 Forbidden | Add `GroupMember.Read.All` permission + grant consent |
| 401 Unauthorized | Token expired, clear browser cache and re-login |
| No groups found | User not in any groups, add them in Azure Portal |
| Hub pod crashes | Check logs for Python syntax errors |

### Get Help

- See [DEPLOY-GRAPH-API-SOLUTION.md](./DEPLOY-GRAPH-API-SOLUTION.md) → Troubleshooting
- Check [POST-MORTEM.md](./POST-MORTEM.md) → What We Did Wrong
- Review hub logs with `-f` flag for real-time debugging

---

## Credits

**Solution**: Developed through collaborative debugging  
**Time Investment**: 9 hours (including 6 hours of wrong approaches)  
**Key Insight**: Azure Portal error message about group assignment  
**Documentation**: Created to prevent others from repeating our mistakes

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Dec 6, 2024 | Initial release - Graph API solution |

---

## Next Steps

Ready to deploy? Start here:

→ [DEPLOY-GRAPH-API-SOLUTION.md](./DEPLOY-GRAPH-API-SOLUTION.md)

Want to understand why? Read this:

→ [AZURE-AD-FREE-TIER-SOLUTION.md](./AZURE-AD-FREE-TIER-SOLUTION.md)

Curious about our journey? Check out:

→ [POST-MORTEM.md](./POST-MORTEM.md)

---

**Happy JupyterHub-ing! 🚀**


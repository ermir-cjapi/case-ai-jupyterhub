# Step-by-Step: Create Azure AD App Registration for JupyterHub

Follow these steps to create your app registration and collect the required information.

## 📋 Step 1: Create App Registration

1. **Go to Azure Portal**
   - Open: https://portal.azure.com
   - Sign in with your Global Administrator account

2. **Navigate to App Registrations**
   - Search for **"Microsoft Entra ID"** or **"Azure Active Directory"**
   - Click on it
   - In the left menu, click **App registrations**
   - Click **+ New registration** button

3. **Fill in the Registration Form**:

   ```
   Name: JupyterHub Production
   
   Supported account types: 
   ● Accounts in this organizational directory only (Single tenant)
     [Your organization name - Single tenant]
   
   Redirect URI (optional):
   Platform: [Web ▼]
   URL: https://jupyterhub.ccrolabs.com/hub/oauth_callback
   ```

4. **Click "Register"** button

---

## 📋 Step 2: Copy Application (Client) ID and Tenant ID

After creation, you'll see the **Overview** page:

### ✅ Copy These Values:

```
┌─────────────────────────────────────────────────────┐
│ JupyterHub Production                               │
├─────────────────────────────────────────────────────┤
│ Application (client) ID:                            │
│ ┌─────────────────────────────────────────────┐    │
│ │ XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX        │ [📋]│ ← COPY THIS!
│ └─────────────────────────────────────────────┘    │
│                                                     │
│ Directory (tenant) ID:                              │
│ ┌─────────────────────────────────────────────┐    │
│ │ YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY        │ [📋]│ ← COPY THIS!
│ └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

**📝 Save these values somewhere safe! You'll need them in a moment.**

Example format:
```
Tenant ID: 12345678-1234-1234-1234-123456789abc
Client ID: 87654321-4321-4321-4321-cba987654321
```

---

## 📋 Step 3: Create Client Secret

1. **In your app registration**, look at the left menu
2. Click **Certificates & secrets**
3. Click the **Client secrets** tab
4. Click **+ New client secret** button

5. **Fill in the form**:
   ```
   Description: JupyterHub Production Secret
   
   Expires: 24 months (recommended)
            (or choose 12/24 months based on your security policy)
   ```

6. Click **Add**

7. **⚠️ IMMEDIATELY COPY THE SECRET VALUE!**

   ```
   ┌─────────────────────────────────────────────────────┐
   │ Client secrets                                      │
   ├─────────────────────────────────────────────────────┤
   │ Description          Value              Expires     │
   ├─────────────────────────────────────────────────────┤
   │ JupyterHub...  [📋 Copy]  🔒 ••••••••  Dec 6, 2027 │
   │                     ↑                                │
   │              CLICK "COPY" HERE!                     │
   │         (You can NEVER see this again!)             │
   └─────────────────────────────────────────────────────┘
   ```

**📝 Save this secret immediately! You cannot view it again after leaving this page!**

Example:
```
Client Secret: AbC123~XyZ789_defGHI456-jklMNO789
```

---

## 📋 Step 4: Configure API Permissions

1. **In your app registration**, click **API permissions** (left menu)

2. You'll see **Microsoft Graph > User.Read** already added

3. Click **+ Add a permission** button

4. **Select Microsoft Graph**:
   - Click **Microsoft Graph** tile
   - Click **Delegated permissions**

5. **Search and add these permissions**:
   
   In the search box, type and select each:
   
   - ✅ `email` - under OpenId permissions
   - ✅ `openid` - under OpenId permissions  
   - ✅ `profile` - under OpenId permissions
   - ✅ `User.Read` - should already be there
   - ✅ `GroupMember.Read.All` - under Group permissions

   **For GroupMember.Read.All**:
   - Type "group" in search
   - Expand **Group** section
   - Check **GroupMember.Read.All**

6. Click **Add permissions** button

7. **⚠️ IMPORTANT: Grant Admin Consent**
   
   You'll see a warning that admin consent is required.
   
   - Click **✓ Grant admin consent for [Your Organization]** button
   - Click **Yes** to confirm
   
   Wait for all permissions to show **"Granted for [Your Organization]"** in green

---

## 📋 Step 5: Verify Permissions

Your API permissions should look like this:

```
┌────────────────────────────────────────────────────────────────┐
│ API permissions                                                │
├────────────────────────────────────────────────────────────────┤
│ Permission                Type        Admin consent required   │
├────────────────────────────────────────────────────────────────┤
│ email                     Delegated   No                       │
│ ✓ Granted for [Your Org]                                      │
├────────────────────────────────────────────────────────────────┤
│ GroupMember.Read.All      Delegated   Yes                     │
│ ✓ Granted for [Your Org]                                      │
├────────────────────────────────────────────────────────────────┤
│ openid                    Delegated   No                       │
│ ✓ Granted for [Your Org]                                      │
├────────────────────────────────────────────────────────────────┤
│ profile                   Delegated   No                       │
│ ✓ Granted for [Your Org]                                      │
├────────────────────────────────────────────────────────────────┤
│ User.Read                 Delegated   No                       │
│ ✓ Granted for [Your Org]                                      │
└────────────────────────────────────────────────────────────────┘
```

All should have green checkmarks ✓

---

## 📋 Step 6: Collect All Your Values

You should now have these 3 values:

```
┌─────────────────────────────────────────────────────────────┐
│ COPY THESE VALUES - YOU'LL NEED THEM FOR JUPYTERHUB CONFIG │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Tenant ID:                                                  │
│ [Paste your tenant ID here]                                 │
│                                                             │
│ Client ID:                                                  │
│ [Paste your client ID here]                                 │
│                                                             │
│ Client Secret:                                              │
│ [Paste your client secret here]                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Step 7: Create Azure AD Groups

Now create the two security groups for access control:

### Create Group 1: JupyterHub-Users

1. **Go to Groups**:
   - Azure Active Directory → **Groups** (left menu)
   - Click **+ New group**

2. **Fill in**:
   ```
   Group type: Security
   
   Group name: JupyterHub-Users
   
   Group description: Regular users who can access JupyterHub
   
   Azure AD roles can be assigned to the group: No
   
   Membership type: Assigned
   
   Owners: [Add yourself]
   
   Members: [Add users now or later]
   ```

3. Click **Create**

### Create Group 2: JupyterHub-Admins

1. Click **+ New group** again

2. **Fill in**:
   ```
   Group type: Security
   
   Group name: JupyterHub-Admins
   
   Group description: Administrators who can manage JupyterHub
   
   Azure AD roles can be assigned to the group: No
   
   Membership type: Assigned
   
   Owners: [Add yourself]
   
   Members: [Add yourself - you're an admin!]
   ```

3. Click **Create**

### Add Yourself to Both Groups

Important: **Add yourself to BOTH groups!**

- JupyterHub-Users (you need access)
- JupyterHub-Admins (you're an admin)

---

## ✅ Verification Checklist

Before proceeding, verify:

- [ ] App registration created: "JupyterHub Production"
- [ ] Copied Tenant ID (looks like: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX)
- [ ] Copied Client ID (looks like: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX)
- [ ] Copied Client Secret (looks like: AbC123~XyZ789...)
- [ ] Redirect URI set to: https://jupyterhub.ccrolabs.com/hub/oauth_callback
- [ ] API permissions added: email, openid, profile, User.Read, GroupMember.Read.All
- [ ] Admin consent granted (all permissions show green checkmark)
- [ ] Group created: JupyterHub-Users (Security group)
- [ ] Group created: JupyterHub-Admins (Security group)
- [ ] You are member of JupyterHub-Users
- [ ] You are member of JupyterHub-Admins

---

## 🎯 Next Step

Now that you have all the values, you can update your `values-helm.yaml` file!

The configuration file will be updated with:
- Your Tenant ID
- Your Client ID  
- Your Client Secret
- Group-based authorization (JupyterHub-Users and JupyterHub-Admins)

---

## 🔐 Security Notes

**⚠️ Keep Your Client Secret Safe!**

- Never commit it to git
- Store it in a password manager
- For production, use Kubernetes secrets (not plaintext in YAML)
- Rotate it periodically (before expiration)

**Client Secret Expiration**:
- Mark your calendar for ~1 month before expiration
- Create a new secret
- Update JupyterHub configuration
- Test the new secret
- Delete the old secret

---

## 🆘 Troubleshooting

### Can't find "Grant admin consent" button

**Solution**: You need Global Administrator or Privileged Role Administrator role

### Permission shows "Not granted"

**Solution**: Click the "Grant admin consent" button at the top of the permissions list

### Can't see Client Secret value

**Problem**: You left the page  
**Solution**: Create a new client secret (you can have multiple). Old one still works.

### Groups don't show up in app

**Problem**: Missing GroupMember.Read.All permission  
**Solution**: Add the permission and grant admin consent

---

## 📚 What's Next?

After completing this guide:
1. ✅ You have your credentials
2. ✅ You have your groups created
3. ⏭️ Update `values-helm.yaml` with your credentials
4. ⏭️ Deploy JupyterHub (when you have Azure subscription)

Ready to update your configuration file!


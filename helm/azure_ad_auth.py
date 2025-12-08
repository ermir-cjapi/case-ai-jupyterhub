"""
Azure AD Authentication with Microsoft Graph API for JupyterHub

This module provides group-based authorization for Azure AD Free tier
by fetching user groups via Microsoft Graph API.

Why this exists:
- Azure AD Free tier doesn't include groups in OAuth tokens
- We fetch groups separately via Graph API after authentication
- See: azure-doc/AZURE-AD-FREE-TIER-SOLUTION.md for details

Requirements:
- Azure AD App must have 'GroupMember.Read.All' as APPLICATION permission
- Admin consent must be granted
"""

import os
import requests
from oauthenticator.azuread import AzureAdOAuthenticator
from traitlets import Set


def get_graph_token_client_credentials():
    """
    Get a Microsoft Graph access token using Client Credentials flow.
    
    This is an app-only token (no user context) that allows us to
    query any user's group memberships.
    
    Requires:
    - 'GroupMember.Read.All' as APPLICATION permission (not delegated)
    - Admin consent granted in Azure Portal
    
    Returns:
        str: Microsoft Graph access token, or empty string on failure
    """
    print("================================================================================")
    print("🔑 CLIENT CREDENTIALS: Getting app-only Graph token...")
    
    tenant_id = os.environ.get("AZURE_TENANT_ID")
    client_id = os.environ.get("AZURE_CLIENT_ID")
    client_secret = os.environ.get("AZURE_CLIENT_SECRET")
    
    if not (tenant_id and client_id and client_secret):
        print("❌ ERROR: Missing AZURE_TENANT_ID / AZURE_CLIENT_ID / AZURE_CLIENT_SECRET")
        print("================================================================================")
        return ""
    
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
    }
    
    print(f"🌐 Token URL: {token_url}")
    
    try:
        resp = requests.post(token_url, data=data, timeout=10)
        print(f"📥 Response status: {resp.status_code}")
        
        if resp.status_code != 200:
            print("❌ ERROR: Failed to get Graph token")
            print(f"📄 Response: {resp.text[:500]}")
            print("")
            print("   HINTS:")
            print("   1. Add 'GroupMember.Read.All' as APPLICATION permission (not delegated)")
            print("   2. Click 'Grant admin consent' in Azure Portal")
            print("================================================================================")
            return ""
        
        token_data = resp.json()
        graph_token = token_data.get("access_token", "")
        
        if not graph_token:
            print("❌ ERROR: No 'access_token' in response")
            print("================================================================================")
            return ""
        
        print("✅ SUCCESS: Got Microsoft Graph app token")
        print("================================================================================")
        return graph_token
        
    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: {e}")
        print("================================================================================")
        return ""
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        print("================================================================================")
        return ""


def fetch_user_groups(user_id: str) -> list:
    """
    Fetch a user's Azure AD group memberships via Microsoft Graph API.
    
    Uses Client Credentials flow (app-only token) to query groups.
    
    Args:
        user_id: User's Object ID (GUID) or userPrincipalName from Azure AD
        
    Returns:
        list: List of group Object IDs (UUIDs) the user belongs to
    """
    print("================================================================================")
    print(f"🔍 FETCHING GROUPS for user: {user_id}")
    print("================================================================================")
    
    if not user_id:
        print("❌ ERROR: No user identifier provided")
        print("================================================================================")
        return []
    
    # Step 1: Get app-only Graph token
    graph_token = get_graph_token_client_credentials()
    if not graph_token:
        print("❌ Cannot fetch groups without Graph token")
        print("================================================================================")
        return []
    
    # Step 2: Query user's group memberships
    # Use /users/{id}/memberOf to get groups for specific user
    # user_id can be Object ID (GUID) or userPrincipalName
    graph_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/memberOf"
    
    headers = {
        "Authorization": f"Bearer {graph_token}",
        "Content-Type": "application/json",
    }
    
    print(f"📡 API request: GET {graph_url}")
    
    try:
        response = requests.get(graph_url, headers=headers, timeout=10)
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            groups_data = data.get("value", [])
            print(f"📦 Found {len(groups_data)} membership objects")
            
            # Extract group IDs (filter out non-groups like roles)
            group_ids = []
            for item in groups_data:
                odata_type = item.get("@odata.type", "")
                display_name = item.get("displayName", "Unknown")
                group_id = item.get("id", "")
                
                print(f"  - Type: {odata_type}, Name: '{display_name}', ID: {group_id}")
                
                if "#microsoft.graph.group" in odata_type:
                    group_ids.append(group_id)
                    print("    ✅ Added to group list")
                else:
                    print("    ⏭️  Skipped (not a group)")
            
            print("")
            print(f"✅ RESULT: User belongs to {len(group_ids)} Azure AD groups:")
            for gid in group_ids:
                print(f"   - {gid}")
            print("================================================================================")
            return group_ids
            
        elif response.status_code == 404:
            print(f"❌ USER NOT FOUND: {user_id}")
            print("   The user identifier (Object ID or email) was not found in Azure AD")
            print(f"📄 Response: {response.text[:500]}")
            print("================================================================================")
            return []
            
        elif response.status_code == 403:
            print("❌ PERMISSION DENIED (403)")
            print("   The app doesn't have permission to read group memberships.")
            print("")
            print("   TO FIX:")
            print("   1. Azure Portal → App Registrations → Your App")
            print("   2. API Permissions → Add permission → Microsoft Graph")
            print("   3. Select 'Application permissions' → GroupMember.Read.All")
            print("   4. Click 'Grant admin consent'")
            print(f"📄 Response: {response.text[:500]}")
            print("================================================================================")
            return []
            
        else:
            print(f"❌ UNEXPECTED ERROR (HTTP {response.status_code})")
            print(f"📄 Response: {response.text[:500]}")
            print("================================================================================")
            return []
            
    except requests.exceptions.Timeout:
        print("❌ REQUEST TIMEOUT")
        print("================================================================================")
        return []
    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: {e}")
        print("================================================================================")
        return []
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        import traceback
        print(traceback.format_exc())
        print("================================================================================")
        return []


class AzureAdGraphAuthenticator(AzureAdOAuthenticator):
    """
    Custom Azure AD authenticator that fetches groups via Graph API.
    
    Extends the standard AzureAdOAuthenticator to add group fetching
    via Microsoft Graph API (Client Credentials flow) after authentication.
    
    Why this is needed:
    - Azure AD Free tier doesn't send groups in OAuth tokens
    - We fetch groups via API call after the user logs in
    - Uses app-only token, so requires APPLICATION permissions
    
    Azure AD Setup Required:
    1. App Registration → API Permissions
    2. Add 'GroupMember.Read.All' as APPLICATION permission
    3. Grant admin consent
    """
    
    # Define these traits explicitly so JupyterHub recognizes them
    allowed_groups = Set(
        config=True,
        help="""
        Set of Azure AD group Object IDs that are allowed to login.
        If empty, all authenticated users are allowed.
        Example: {"group-uuid-1", "group-uuid-2"}
        """
    )
    
    admin_groups = Set(
        config=True,
        help="""
        Set of Azure AD group Object IDs whose members have admin privileges.
        Example: {"admin-group-uuid"}
        """
    )
    
    async def authenticate(self, handler, data=None):
        """
        Override authenticate to fetch groups after Azure AD login.
        """
        print("=" * 80)
        print("🔐 AUTHENTICATE: Custom authenticate method called")
        print("=" * 80)
        
        # Call parent's authenticate method first
        auth_model = await super().authenticate(handler, data)
        
        if not auth_model:
            print("❌ Authentication failed at parent level")
            print("=" * 80)
            return None
        
        print("✅ Parent authentication succeeded")
        print(f"📦 auth_model keys: {list(auth_model.keys())}")
        
        # Fetch groups and check authorization
        return await self._fetch_and_add_groups(auth_model)
    
    async def _fetch_and_add_groups(self, auth_model):
        """
        Fetch user's groups from Graph API and add to auth_model.
        """
        print("=" * 80)
        print("🔍 FETCHING GROUPS: _fetch_and_add_groups called")
        print("=" * 80)
        
        username = auth_model.get('name', 'Unknown')
        print(f"👤 User: {username}")
        
        # Get user's identifier from auth_state
        auth_state = auth_model.get('auth_state', {})
        if not auth_state:
            print("❌ WARNING: No auth_state in auth_model!")
            print("=" * 80)
            return auth_model
        
        # Try to get user identifier from auth_state
        # Priority: Object ID (oid) > sub > email
        # Object ID is required for guest/external users!
        user_info = auth_state.get('user', {})
        
        # Debug: show what's available
        print(f"📋 user_info keys: {list(user_info.keys())}")
        
        # Get Object ID (works for all users including guests)
        user_oid = user_info.get('oid') or user_info.get('sub')
        user_email = (
            user_info.get('email') or 
            user_info.get('preferred_username') or
            user_info.get('upn')
        )
        
        print(f"🆔 User Object ID (oid): {user_oid}")
        print(f"📧 User email: {user_email}")
        
        # Prefer Object ID (required for guest users)
        user_identifier = user_oid or user_email
        
        if not user_identifier:
            print("❌ WARNING: Could not determine user identifier!")
            print(f"   auth_state keys: {list(auth_state.keys())}")
            print(f"   user_info: {user_info}")
            print("   Cannot fetch groups without user identifier")
            print("=" * 80)
            return auth_model
        
        print(f"✅ Using identifier: {user_identifier}")
        
        # Fetch groups from Microsoft Graph API
        user_groups = fetch_user_groups(user_identifier)
        
        # Add groups to auth_model
        auth_model['groups'] = user_groups
        print(f"✅ Auth model updated with {len(user_groups)} groups")
        
        # Check group-based authorization
        if self.allowed_groups:
            print(f"🔒 Checking allowed_groups: {len(self.allowed_groups)} configured")
            if not any(group in self.allowed_groups for group in user_groups):
                print(f"❌ User {username} not in any allowed groups!")
                print(f"   User groups: {user_groups}")
                print(f"   Allowed groups: {self.allowed_groups}")
                print("=" * 80)
                return None  # Deny access
            else:
                print(f"✅ User {username} is in allowed groups")
        
        # Check admin group membership
        if self.admin_groups:
            is_admin = any(group in self.admin_groups for group in user_groups)
            auth_model['admin'] = is_admin
            print(f"👑 Admin status: {is_admin}")
            if is_admin:
                matching_groups = self.admin_groups & set(user_groups)
                print(f"   User is in admin group(s): {matching_groups}")
        
        print("=" * 80)
        return auth_model

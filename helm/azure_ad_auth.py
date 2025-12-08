"""
Azure AD Authentication with Microsoft Graph API for JupyterHub

This module provides group-based authorization for Azure AD Free tier
by fetching user groups via Microsoft Graph API (Client Credentials flow).

Why this exists:
- Azure AD Free tier doesn't include groups in OAuth tokens
- We fetch groups separately via Graph API after authentication

Requirements:
- Azure AD App must have 'GroupMember.Read.All' as APPLICATION permission
- Admin consent must be granted

See: azure-doc/README.md for setup instructions
"""

import os
import requests
from oauthenticator.azuread import AzureAdOAuthenticator
from traitlets import Set


def get_graph_token():
    """
    Get a Microsoft Graph access token using Client Credentials flow.
    
    Returns:
        str: Microsoft Graph access token, or empty string on failure
    """
    tenant_id = os.environ.get("AZURE_TENANT_ID")
    client_id = os.environ.get("AZURE_CLIENT_ID")
    client_secret = os.environ.get("AZURE_CLIENT_SECRET")
    
    if not (tenant_id and client_id and client_secret):
        print("❌ Missing Azure credentials (TENANT_ID/CLIENT_ID/CLIENT_SECRET)")
        return ""
    
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    try:
        resp = requests.post(token_url, data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/.default",
        }, timeout=10)
        
        if resp.status_code != 200:
            print(f"❌ Failed to get Graph token: {resp.status_code}")
            print(f"   Response: {resp.text[:300]}")
            return ""
        
        return resp.json().get("access_token", "")
        
    except Exception as e:
        print(f"❌ Graph token error: {e}")
        return ""


def fetch_user_groups(user_id: str) -> list:
    """
    Fetch a user's Azure AD group memberships via Microsoft Graph API.
    
    Args:
        user_id: User's Object ID (GUID) from Azure AD
        
    Returns:
        list: List of group Object IDs the user belongs to
    """
    if not user_id:
        return []
    
    graph_token = get_graph_token()
    if not graph_token:
        return []
    
    graph_url = f"https://graph.microsoft.com/v1.0/users/{user_id}/memberOf"
    
    try:
        response = requests.get(
            graph_url,
            headers={"Authorization": f"Bearer {graph_token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            groups_data = response.json().get("value", [])
            # Filter to only actual groups (not roles)
            group_ids = [
                item.get("id") 
                for item in groups_data 
                if "#microsoft.graph.group" in item.get("@odata.type", "")
            ]
            print(f"✅ User {user_id[:8]}... belongs to {len(group_ids)} groups")
            return group_ids
            
        elif response.status_code == 403:
            print("❌ Permission denied - add GroupMember.Read.All (Application) + grant consent")
            return []
        elif response.status_code == 404:
            print(f"❌ User not found: {user_id}")
            return []
        else:
            print(f"❌ Graph API error: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Graph API error: {e}")
        return []


class AzureAdGraphAuthenticator(AzureAdOAuthenticator):
    """
    Azure AD authenticator with group fetching via Microsoft Graph API.
    
    Extends AzureAdOAuthenticator to fetch groups via Graph API,
    since Azure AD Free tier doesn't include groups in OAuth tokens.
    
    Configuration:
        c.AzureAdGraphAuthenticator.allowed_groups = {"group-id-1", "group-id-2"}
        c.AzureAdGraphAuthenticator.admin_groups = {"admin-group-id"}
    """
    
    allowed_groups = Set(
        config=True,
        help="Set of Azure AD group Object IDs that are allowed to login."
    )
    
    admin_groups = Set(
        config=True,
        help="Set of Azure AD group Object IDs whose members have admin privileges."
    )
    
    async def authenticate(self, handler, data=None):
        """Override authenticate to fetch groups after Azure AD login."""
        # Standard Azure AD authentication
        auth_model = await super().authenticate(handler, data)
        
        if not auth_model:
            return None
        
        username = auth_model.get('name', 'Unknown')
        print(f"🔐 Azure AD login: {username}")
        
        # Fetch groups and check authorization
        return await self._fetch_and_add_groups(auth_model)
    
    async def _fetch_and_add_groups(self, auth_model):
        """Fetch user's groups from Graph API and add to auth_model."""
        username = auth_model.get('name', 'Unknown')
        auth_state = auth_model.get('auth_state', {})
        
        if not auth_state:
            print("⚠️ No auth_state available")
            return auth_model
        
        # Get user identifier (Object ID preferred for guest users)
        user_info = auth_state.get('user', {})
        user_oid = user_info.get('oid') or user_info.get('sub')
        user_email = user_info.get('email') or user_info.get('preferred_username')
        user_identifier = user_oid or user_email
        
        if not user_identifier:
            print("⚠️ Could not determine user identifier")
            return auth_model
        
        # Fetch groups from Graph API
        user_groups = fetch_user_groups(user_identifier)
        auth_model['groups'] = user_groups
        
        # Check allowed_groups
        if self.allowed_groups:
            if not any(g in self.allowed_groups for g in user_groups):
                print(f"❌ {username} not in allowed groups")
                return None  # Deny access
            print(f"✅ {username} authorized (in allowed groups)")
        
        # Check admin_groups
        if self.admin_groups:
            is_admin = any(g in self.admin_groups for g in user_groups)
            auth_model['admin'] = is_admin
            if is_admin:
                print(f"👑 {username} granted admin privileges")
        
        return auth_model

"""
Azure AD Authentication with Microsoft Graph API for JupyterHub

This module provides group-based authorization for Azure AD Free tier
by fetching user groups via Microsoft Graph API.

Why this exists:
- Azure AD Free tier doesn't include groups in OAuth tokens
- We fetch groups separately via Graph API after authentication
- See: azure-doc/AZURE-AD-FREE-TIER-SOLUTION.md for details

Requirements:
- Azure AD App must have 'GroupMember.Read.All' permission
- Admin consent must be granted
"""

import os
import requests
from oauthenticator.azuread import AzureAdOAuthenticator
from traitlets import Set


async def fetch_user_groups_from_graph_api(access_token):
    """
    Fetch user's Azure AD group memberships via Microsoft Graph API.
    
    This is necessary because Azure AD Free tier does NOT include
    groups in the OAuth token. We must fetch them separately.
    
    Args:
        access_token (str): OAuth access token from Azure AD
    
    Returns:
        list: List of group Object IDs (UUIDs) the user belongs to
    
    API Reference:
        https://learn.microsoft.com/en-us/graph/api/user-list-memberof
    """
    print("=" * 80)
    print("🔍 FETCHING USER GROUPS FROM MICROSOFT GRAPH API")
    print("=" * 80)
    
    if not access_token:
        print("❌ ERROR: No access_token provided")
        print("=" * 80)
        return []
    
    print(f"✅ Access token present (length: {len(access_token)} chars)")
    
    # Microsoft Graph API endpoint to get user's group memberships
    graph_api_url = "https://graph.microsoft.com/v1.0/me/memberOf"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print(f"📡 Making API request to: {graph_api_url}")
    print(f"📋 Request headers: Authorization: Bearer <token>, Content-Type: application/json")
    
    try:
        # Make synchronous request (we're in async context but requests is sync)
        # In production, consider using aiohttp for true async
        response = requests.get(graph_api_url, headers=headers, timeout=10)
        
        print(f"📥 Response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API call successful!")
            print(f"📊 Raw response keys: {list(data.keys())}")
            
            # Extract group IDs from the response
            # Response format: {"value": [{"id": "group-uuid", "displayName": "group-name", ...}, ...]}
            groups_data = data.get('value', [])
            print(f"📦 Found {len(groups_data)} membership objects")
            
            # Filter to only security groups (not all memberOf are groups)
            # Microsoft Graph returns various types: groups, roles, administrative units
            group_ids = []
            for item in groups_data:
                # Check if this is actually a group
                odata_type = item.get('@odata.type', '')
                display_name = item.get('displayName', 'Unknown')
                group_id = item.get('id', '')
                
                print(f"  - Type: {odata_type}, Name: '{display_name}', ID: {group_id}")
                
                # Only include actual groups (not roles or other membership types)
                if '#microsoft.graph.group' in odata_type:
                    group_ids.append(group_id)
                    print(f"    ✅ Added to group list")
                else:
                    print(f"    ⏭️  Skipped (not a group)")
            
            print(f"")
            print(f"✅ FINAL RESULT: User belongs to {len(group_ids)} Azure AD groups:")
            for gid in group_ids:
                print(f"   - {gid}")
            print("=" * 80)
            
            return group_ids
        
        elif response.status_code == 401:
            print(f"❌ AUTHENTICATION FAILED (401 Unauthorized)")
            print(f"   This usually means:")
            print(f"   1. Access token is expired")
            print(f"   2. Access token doesn't have required permissions")
            print(f"   3. Token is invalid or malformed")
            print(f"📄 Response body: {response.text[:500]}")
            print("=" * 80)
            return []
        
        elif response.status_code == 403:
            print(f"❌ PERMISSION DENIED (403 Forbidden)")
            print(f"   This usually means:")
            print(f"   1. App registration doesn't have 'GroupMember.Read.All' permission")
            print(f"   2. Admin hasn't granted consent for the permission")
            print(f"   3. User doesn't have permission to read group memberships")
            print(f"")
            print(f"   TO FIX:")
            print(f"   1. Go to Azure Portal → App Registrations → Your App")
            print(f"   2. API Permissions → Add 'GroupMember.Read.All' (Delegated)")
            print(f"   3. Click 'Grant admin consent'")
            print(f"📄 Response body: {response.text[:500]}")
            print("=" * 80)
            return []
        
        else:
            print(f"❌ UNEXPECTED ERROR (HTTP {response.status_code})")
            print(f"📄 Response body: {response.text[:500]}")
            print("=" * 80)
            return []
    
    except requests.exceptions.Timeout:
        print(f"❌ REQUEST TIMEOUT (>10 seconds)")
        print(f"   Microsoft Graph API did not respond in time")
        print(f"   This might be a network issue or Azure service slowdown")
        print("=" * 80)
        return []
    
    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: {str(e)}")
        print(f"   Could not connect to Microsoft Graph API")
        print(f"   Check network connectivity and DNS resolution")
        print("=" * 80)
        return []
    
    except Exception as e:
        print(f"❌ UNEXPECTED EXCEPTION: {type(e).__name__}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        print("=" * 80)
        return []


class AzureAdGraphAuthenticator(AzureAdOAuthenticator):
    """
    Custom Azure AD authenticator that fetches groups via Graph API.
    
    Extends the standard AzureAdOAuthenticator to add group fetching
    via Microsoft Graph API after successful authentication.
    
    Why this is needed:
    - Azure AD Free tier doesn't send groups in OAuth tokens
    - We fetch groups via API call using the access_token
    - See: azure-doc/AZURE-AD-FREE-TIER-SOLUTION.md
    """
    
    # Define these traits explicitly so JupyterHub recognizes them
    # These allow group-based authorization configuration
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
    
    async def update_auth_model(self, auth_model):
        """
        Called after authentication to enrich user info with groups.
        
        This is where we fetch groups from Microsoft Graph API and
        add them to the auth_model so JupyterHub can use them for
        authorization decisions.
        """
        print("=" * 80)
        print("🔐 POST-AUTHENTICATION: update_auth_model called")
        print("=" * 80)
        
        # Call parent class method first
        auth_model = await super().update_auth_model(auth_model)
        
        username = auth_model.get('name', 'Unknown')
        print(f"👤 User: {username}")
        print(f"📧 Email: {auth_model.get('auth_state', {}).get('user', {}).get('email', 'Unknown')}")
        
        # Get access_token from auth_state
        auth_state = auth_model.get('auth_state', {})
        access_token = auth_state.get('access_token')
        
        if not access_token:
            print("❌ WARNING: No access_token in auth_state!")
            print(f"   Available auth_state keys: {list(auth_state.keys())}")
            print("   Cannot fetch groups without access_token")
            print("=" * 80)
            return auth_model
        
        # Fetch groups from Microsoft Graph API
        user_groups = await fetch_user_groups_from_graph_api(access_token)
        
        # Add groups to auth_model
        auth_model['groups'] = user_groups
        
        print(f"✅ Auth model updated with {len(user_groups)} groups")
        
        # Check group-based authorization
        if self.allowed_groups:
            print(f"🔒 Checking allowed_groups: {self.allowed_groups}")
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
                print(f"   User is in admin group(s): {self.admin_groups & set(user_groups)}")
        
        print("=" * 80)
        return auth_model


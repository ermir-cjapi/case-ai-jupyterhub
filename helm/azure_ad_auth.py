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


def get_graph_access_token_on_behalf_of(user_access_token: str) -> str:
    """
    Exchange the JupyterHub access_token for a Microsoft Graph token
    using the OAuth2 On-Behalf-Of (OBO) flow.

    This keeps us in the 'delegated' model (Option A):
    - User signs in once to JupyterHub
    - Our app calls Graph *on behalf of* that user

    Docs:
    - https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-on-behalf-of-flow
    """
    print("================================================================================")
    print("🔁 OBO FLOW: Exchanging access_token for Microsoft Graph token...")

    tenant_id = os.environ.get("AZURE_TENANT_ID")
    client_id = os.environ.get("AZURE_CLIENT_ID")
    client_secret = os.environ.get("AZURE_CLIENT_SECRET")

    if not (tenant_id and client_id and client_secret):
        print("❌ OBO ERROR: Missing AZURE_TENANT_ID / AZURE_CLIENT_ID / AZURE_CLIENT_SECRET env vars")
        print("   Cannot perform On-Behalf-Of flow without these values")
        print("================================================================================")
        return ""

    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    data = {
        # OBO grant type
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "requested_token_use": "on_behalf_of",
        # Our app
        "client_id": client_id,
        "client_secret": client_secret,
        # Incoming user token (for JupyterHub app)
        "assertion": user_access_token,
        # Ask for Graph scopes; .default uses what you configured on the app
        "scope": "https://graph.microsoft.com/.default",
    }

    print(f"🌐 OBO token_url: {token_url}")

    try:
        resp = requests.post(token_url, data=data, timeout=10)
        print(f"📥 OBO response status: {resp.status_code}")

        if resp.status_code != 200:
            print("❌ OBO ERROR: Failed to obtain Graph access token")
            print(f"📄 Response body: {resp.text[:500]}")
            print("   HINTS:")
            print("   - Ensure your app registration has Microsoft Graph delegated permissions")
            print("     like 'User.Read' and 'GroupMember.Read.All'")
            print("   - Click 'Grant admin consent' in Azure Portal")
            print("   - Ensure you're using the v2.0 token endpoint")
            print("================================================================================")
            return ""

        token_data = resp.json()
        graph_token = token_data.get("access_token", "")
        if not graph_token:
            print("❌ OBO ERROR: No 'access_token' field in response JSON")
            print(f"   Keys: {list(token_data.keys())}")
            print("================================================================================")
            return ""

        print("✅ OBO SUCCESS: Obtained Microsoft Graph access token")
        print("================================================================================")
        return graph_token

    except requests.exceptions.RequestException as e:
        print(f"❌ OBO NETWORK ERROR: {e}")
        print("   Could not contact Azure AD token endpoint for OBO flow")
        print("================================================================================")
        return ""
    except Exception as e:
        print(f"❌ OBO UNEXPECTED EXCEPTION: {type(e).__name__}: {e}")
        import traceback

        print(traceback.format_exc())
        print("================================================================================")
        return ""


async def fetch_user_groups_from_graph_api(access_token):
    """
    Fetch user's Azure AD group memberships via Microsoft Graph API.

    This is necessary because Azure AD Free tier does NOT include
    groups in the OAuth token. We must fetch them separately.

    Args:
        access_token (str): OAuth access token issued for the JupyterHub app
                            (we will exchange it for a Graph token via OBO).

    Returns:
        list: List of group Object IDs (UUIDs) the user belongs to

    API Reference:
        https://learn.microsoft.com/en-us/graph/api/user-list-memberof
    """
    print("🚨 DEBUG: fetch_user_groups_from_graph_api() ENTERED")
    print(f"🚨 DEBUG: access_token type: {type(access_token)}")
    print(f"🚨 DEBUG: access_token value: {access_token[:50] if access_token else 'None'}...")
    print("================================================================================")
    print("🔍 FETCHING USER GROUPS FROM MICROSOFT GRAPH API")
    print("================================================================================")

    if not access_token:
        print("❌ ERROR: No access_token provided")
        print("================================================================================")
        return []

    print(f"✅ Access token present (length: {len(access_token)} chars)")

    # ------------------------------------------------------------------
    # STEP 1: Exchange hub token for a Microsoft Graph token (OBO)
    # ------------------------------------------------------------------
    graph_token = get_graph_access_token_on_behalf_of(access_token)
    if not graph_token:
        print("❌ ERROR: Could not obtain Microsoft Graph access token via OBO flow")
        print("   Cannot query /me/memberOf without a valid Graph token")
        print("================================================================================")
        return []

    # ------------------------------------------------------------------
    # STEP 2: Call Microsoft Graph with the GRAPH token
    # ------------------------------------------------------------------
    graph_api_url = "https://graph.microsoft.com/v1.0/me/memberOf"

    headers = {
        "Authorization": f"Bearer {graph_token}",
        "Content-Type": "application/json",
    }

    print(f"📡 Making API request to: {graph_api_url}")
    print("📋 Request headers: Authorization: Bearer <graph_token>, Content-Type: application/json")

    try:
        # Make synchronous request (we're in async context but requests is sync)
        response = requests.get(graph_api_url, headers=headers, timeout=10)

        print(f"📥 Response status code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ API call successful!")
            print(f"📊 Raw response keys: {list(data.keys())}")

            # Extract group IDs from the response
            # Response format: {"value": [{"id": "group-uuid", "displayName": "group-name", ...}, ...]}
            groups_data = data.get("value", [])
            print(f"📦 Found {len(groups_data)} membership objects")

            # Filter to only security groups (not all memberOf are groups)
            # Microsoft Graph returns various types: groups, roles, administrative units
            group_ids = []
            for item in groups_data:
                # Check if this is actually a group
                odata_type = item.get("@odata.type", "")
                display_name = item.get("displayName", "Unknown")
                group_id = item.get("id", "")

                print(f"  - Type: {odata_type}, Name: '{display_name}', ID: {group_id}")

                # Only include actual groups (not roles or other membership types)
                if "#microsoft.graph.group" in odata_type:
                    group_ids.append(group_id)
                    print("    ✅ Added to group list")
                else:
                    print("    ⏭️  Skipped (not a group)")

            print("")
            print(f"✅ FINAL RESULT: User belongs to {len(group_ids)} Azure AD groups:")
            for gid in group_ids:
                print(f"   - {gid}")
            print("================================================================================")

            return group_ids

        elif response.status_code == 401:
            print("❌ AUTHENTICATION FAILED (401 Unauthorized)")
            print("   This usually means:")
            print("   1. Graph access token is expired")
            print("   2. Graph token doesn't have required permissions")
            print("   3. Token is invalid or malformed")
            print(f"📄 Response body: {response.text[:500]}")
            print("================================================================================")
            return []

        elif response.status_code == 403:
            print("❌ PERMISSION DENIED (403 Forbidden)")
            print("   This usually means:")
            print("   1. App registration doesn't have 'GroupMember.Read.All' permission")
            print("   2. Admin hasn't granted consent for the permission")
            print("   3. User doesn't have permission to read group memberships")
            print("")
            print("   TO FIX:")
            print("   1. Go to Azure Portal → App Registrations → Your App")
            print("   2. API Permissions → Add 'GroupMember.Read.All' (Delegated)")
            print("   3. Click 'Grant admin consent'")
            print(f"📄 Response body: {response.text[:500]}")
            print("================================================================================")
            return []

        else:
            print(f"❌ UNEXPECTED ERROR (HTTP {response.status_code})")
            print(f"📄 Response body: {response.text[:500]}")
            print("================================================================================")
            return []

    except requests.exceptions.Timeout:
        print("❌ REQUEST TIMEOUT (>10 seconds)")
        print("   Microsoft Graph API did not respond in time")
        print("   This might be a network issue or Azure service slowdown")
        print("================================================================================")
        return []

    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: {str(e)}")
        print("   Could not connect to Microsoft Graph API")
        print("   Check network connectivity and DNS resolution")
        print("================================================================================")
        return []

    except Exception as e:
        print(f"❌ UNEXPECTED EXCEPTION: {type(e).__name__}: {str(e)}")
        import traceback

        print(traceback.format_exc())
        print("================================================================================")
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
    
    async def authenticate(self, handler, data=None):
        """
        Override authenticate to fetch groups after Azure AD login.
        
        This is called on every login attempt.
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
        
        print(f"✅ Parent authentication succeeded")
        print(f"📦 auth_model keys: {list(auth_model.keys())}")
        
        # Now do our custom group fetching
        return await self._fetch_and_add_groups(auth_model)
    
    async def _fetch_and_add_groups(self, auth_model):
        """
        Helper method to fetch groups and add to auth_model.
        """
        print("=" * 80)
        print("🔍 FETCHING GROUPS: _fetch_and_add_groups called")
        print("=" * 80)
        
        # Call parent class method first
        auth_model = await super().update_auth_model(auth_model)
        
        username = auth_model.get('name', 'Unknown')
        print(f"👤 User: {username}")
        
        # Get access_token from auth_state
        auth_state = auth_model.get('auth_state', {})
        if not auth_state:
            print("❌ WARNING: No auth_state in auth_model!")
            print(f"   Available auth_model keys: {list(auth_model.keys())}")
            print("=" * 80)
            return auth_model
        
        print(f"📧 Email: {auth_state.get('user', {}).get('email', 'Unknown')}")
        
        access_token = auth_state.get('access_token')
        if not access_token:
            print("❌ WARNING: No access_token in auth_state!")
            print(f"   Available auth_state keys: {list(auth_state.keys())}")
            print("   Cannot fetch groups without access_token")
            print("=" * 80)
            return auth_model
        
        print(f"✅ Access token found (length: {len(access_token)} chars)")
        
        # Fetch groups from Microsoft Graph API
        print(f"📞 Calling fetch_user_groups_from_graph_api()...")
        user_groups = await fetch_user_groups_from_graph_api(access_token)
        print(f"📞 fetch_user_groups_from_graph_api() returned: {user_groups}")
        
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


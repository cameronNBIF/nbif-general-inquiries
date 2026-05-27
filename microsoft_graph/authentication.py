from azure.identity import ClientSecretCredential

from config import AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID, GRAPH_SCOPE

# ─────────────────────────────────────────────────────────────────────────────
# Microsoft Graph — Authentication
# ─────────────────────────────────────────────────────────────────────────────

def get_graph_token() -> str:
    """
    Acquire a short-lived OAuth 2.0 access token for Microsoft Graph using
    the client credentials flow (app-only, no signed-in user required).

    azure-identity handles token caching internally — repeated calls within
    the token's lifetime will return the cached token rather than making a
    new network request.
    """
    credential = ClientSecretCredential(
        tenant_id=AZURE_TENANT_ID,
        client_id=AZURE_CLIENT_ID,
        client_secret=AZURE_CLIENT_SECRET,
    )
    token = credential.get_token(GRAPH_SCOPE)
    return token.token


def graph_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
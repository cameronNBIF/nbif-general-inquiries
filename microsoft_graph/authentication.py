from azure.identity import ClientSecretCredential

from config import AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID, GRAPH_SCOPE

# ─────────────────────────────────────────────────────────────────────────────
# Microsoft Graph — Authentication
# ─────────────────────────────────────────────────────────────────────────────

_credential: ClientSecretCredential | None = None


def _get_credential() -> ClientSecretCredential:
    global _credential
    if _credential is None:
        _credential = ClientSecretCredential(
            tenant_id=AZURE_TENANT_ID,
            client_id=AZURE_CLIENT_ID,
            client_secret=AZURE_CLIENT_SECRET,
        )
    return _credential


def get_graph_token() -> str:
    return _get_credential().get_token(GRAPH_SCOPE).token


def graph_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

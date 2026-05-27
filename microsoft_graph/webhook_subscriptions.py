from datetime import datetime, timedelta, timezone
from urllib import request

from function_app import GRAPH_BASE
from microsoft_graph.authentication import graph_headers

# ─────────────────────────────────────────────────────────────────────────────
# Microsoft Graph — Webhook Subscriptions
# ─────────────────────────────────────────────────────────────────────────────

def renew_graph_subscription(token: str, subscription_id: str) -> str:
    """
    Extend the Graph webhook subscription's expiry by the maximum allowed
    duration for mail subscriptions (3 days).

    Returns the new expiration datetime string for logging.
    """
    new_expiry = (
        datetime.now(timezone.utc) + timedelta(days=3)
    ).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    url = f"{GRAPH_BASE}/subscriptions/{subscription_id}"
    resp = request.patch(
        url,
        json={"expirationDateTime": new_expiry},
        headers=graph_headers(token),
    )
    resp.raise_for_status()
    return new_expiry
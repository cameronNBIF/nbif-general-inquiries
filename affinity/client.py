from config import AFFINITY_API_KEY


# ─────────────────────────────────────────────────────────────────────────────
# Affinity
# ─────────────────────────────────────────────────────────────────────────────


def affinity_auth() -> tuple[str, str]:
    """
    Affinity uses HTTP Basic Auth with an empty username and the API key
    as the password.
    """
    return ("", AFFINITY_API_KEY)













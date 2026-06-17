import functools
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from config import AFFINITY_API_KEY

# ─────────────────────────────────────────────────────────────────────────────
# Affinity
# ─────────────────────────────────────────────────────────────────────────────


@functools.lru_cache(maxsize=1)
def get_affinity_session() -> requests.Session:
    """
    Returns a singleton requests Session configured with HTTP Basic Auth,
    connection pooling, and an exponential backoff retry strategy for resilience.
    """
    session = requests.Session()
    # Affinity uses HTTP Basic Auth with an empty username and the API key as the password
    session.auth = ("", AFFINITY_API_KEY)

    retries = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        # Only retry idempotent operations to prevent duplicate records if a timeout occurs
        allowed_methods=["HEAD", "GET", "OPTIONS", "PUT"],
    )

    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)

    return session

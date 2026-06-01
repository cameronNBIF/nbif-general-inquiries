import html
import re
import requests

from config import GRAPH_BASE, GRAPH_USER_EMAIL
from microsoft_graph.authentication import graph_headers

# ─────────────────────────────────────────────────────────────────────────────
# Microsoft Graph — Mail
# ─────────────────────────────────────────────────────────────────────────────

def fetch_message(token: str, message_id: str) -> dict:
    """
    Fetch a single message from the info@nbif.ca mailbox using its Graph message ID.

    We use $select to retrieve only the fields we need rather than the full
    message object, which keeps the response payload small.
    """
    select_fields = "id,subject,from,body,receivedDateTime,conversationId"
    url = (
        f"{GRAPH_BASE}/users/{GRAPH_USER_EMAIL}"
        f"/messages/{message_id}"
        f"?$select={select_fields}"
    )
    resp = requests.get(url, headers=graph_headers(token))
    resp.raise_for_status()
    return resp.json()


def parse_body(content: str, content_type: str) -> str:
    """
    Return clean plain text from a message body.

    Graph returns the body in whichever format the sender used. HTML emails
    are common, so we strip tags with a simple regex. For plain text bodies
    we just strip surrounding whitespace.

    Note: this regex handles the common case well. If NBIF ever receives
    emails with very complex HTML structures, a library like `beautifulsoup4`
    can be added to requirements.txt for more robust parsing.
    """
    if content_type.lower() == "html":
        text = re.sub(r"<[^>]+>", " ", content)
        text = html.unescape(text)              # &nbsp; → space, &amp; → &, etc.
        text = re.sub(r"\s+", " ", text)
        return text.strip()
    return html.unescape(content).strip()


def split_display_name(display_name: str) -> tuple[str, str]:
    """
    Split 'Jane Doe' → ('Jane', 'Doe').
    Handles single-word names (first name only, empty last name) gracefully.
    """
    parts = display_name.strip().split(" ", 1)
    first = parts[0] if parts else ""
    last  = parts[1] if len(parts) > 1 else ""
    return first, last
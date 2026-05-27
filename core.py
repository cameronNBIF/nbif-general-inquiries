import logging

from affinity.affinity import create_list_entry, populate_affinity_entry, resolve_or_create_person
from azure_table_storage.azure_table_storage import conversation_exists, store_conversation
from config import FORM_SUBJECT_PREFIX
from microsoft_graph.mail import fetch_message, parse_body, split_display_name

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Core Processing Logic
# ─────────────────────────────────────────────────────────────────────────────

def process_notification(token: str, message_id: str) -> None:
    """
    Handle a single Graph change notification end-to-end:

      1. Fetch the full message from Graph.
      2. Check Table Storage — if the conversationId already exists, this is
         a reply to an existing thread. Log and return without touching Affinity.
      3. Determine whether the email came via the website form or directly.
      4. Resolve or create the sender as a Person in Affinity.
      5. Create a list entry in General Inquiries and populate all fields.
      6. Persist the conversationId so future replies are deduplicated.

    This function is intentionally separate from the HTTP trigger so it can
    be unit-tested independently of the Azure Functions runtime.
    """

    # Step 1 — Fetch
    message         = fetch_message(token, message_id)
    conversation_id = message["conversationId"]
    received_at     = message["receivedDateTime"]
    subject         = message.get("subject", "")
    sender_email    = message["from"]["emailAddress"]["address"]
    sender_name     = message["from"]["emailAddress"].get("name", sender_email)
    body_text       = parse_body(message["body"]["content"], message["body"]["contentType"])

    logger.info(
        "Message fetched | from: %s | conversationId: %s | subject: %s",
        sender_email, conversation_id, subject,
    )

    # Step 2 — Deduplicate
    if conversation_exists(conversation_id):
        logger.info(
            "conversationId %s already tracked — reply thread, skipping Affinity.",
            conversation_id,
        )
        return

    # Step 3 — Source detection
    source = (
        "Website Form"
        if subject.startswith(FORM_SUBJECT_PREFIX)
        else "Direct Email"
    )

    # Steps 4 & 5 — Affinity
    first_name, last_name = split_display_name(sender_name)
    person_id     = resolve_or_create_person(first_name, last_name, sender_email)
    list_entry_id = create_list_entry(person_id)
    populate_affinity_entry(list_entry_id, body_text, received_at, source, conversation_id)

    logger.info(
        "Affinity entry created | list_entry_id: %s | person: %s %s <%s> | source: %s",
        list_entry_id, first_name, last_name, sender_email, source,
    )

    # Step 6 — Persist conversationId
    store_conversation(conversation_id, sender_email, received_at)
    logger.info("conversationId %s stored in Table Storage.", conversation_id)
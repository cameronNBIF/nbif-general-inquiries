import logging

from config import FORM_SUBJECT_PREFIX
from affinity.person import resolve_or_create_person
from affinity.entry import (
    create_list_entry, 
    populate_affinity_entry
)
from azure_table_storage.conversation import (
    release_conversation_claim,
    try_claim_conversation
)
from microsoft_graph.mail import (
    fetch_message,
    parse_body,
    parse_form_submission,
    split_display_name,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Core Processing Logic
# ─────────────────────────────────────────────────────────────────────────────


def process_notification(token: str, message_id: str) -> None:
    """
    Handle a single Graph change notification end-to-end:

      1. Fetch the full message from Graph.
      2. Determine whether the email came via the website form or directly.
      3. Check Table Storage — if the conversationId already exists, this is
         a reply to an existing thread. Log and return without touching Affinity.
      4. Resolve or create the sender as a Person in Affinity.
      5. Create a list entry in General Inquiries and populate all fields.
      6. Persist the conversationId so future replies are deduplicated.

    This function is intentionally separate from the HTTP trigger so it can
    be unit-tested independently of the Azure Functions runtime.
    """

    # Step 1 — Fetch
    message = fetch_message(token, message_id)
    conversation_id = message["conversationId"]
    received_at = message["receivedDateTime"]
    subject = message.get("subject", "")
    body_text = parse_body(message["body"]["content"], message["body"]["contentType"])

    is_form = subject.startswith(FORM_SUBJECT_PREFIX)

    # Step 2 — Source detection
    source = "Website Form" if is_form else "Direct Email"

    if is_form:
        parsed = parse_form_submission(body_text)
        if parsed:
            sender_name = parsed["name"]
            sender_email = parsed["email"]
            body_text = parsed["message"]  # store just the message, not the full body
        else:
            logger.warning(
                "Form submission body could not be parsed for message %s — falling back to envelope sender.",
                message_id,
            )
            sender_email = message["from"]["emailAddress"]["address"]
            sender_name = message["from"]["emailAddress"].get("name", sender_email)
    else:
        sender_email = message["from"]["emailAddress"]["address"]
        sender_name = message["from"]["emailAddress"].get("name", sender_email)

    logger.info(
        "Message fetched | from: %s | conversationId: %s | subject: %s",
        sender_email,
        conversation_id,
        subject,
    )

    #Step 3 — Deduplicate
    claimed = try_claim_conversation(conversation_id, sender_email, received_at)
    if not claimed:
        logger.info(
            "conversationId %s already claimed — duplicate notification, skipping Affinity.",
            conversation_id,
        )
        return

    try:
        #Steps 4-5 — Affinity population
        first_name, last_name = split_display_name(sender_name)
        person_id = resolve_or_create_person(first_name, last_name, sender_email)
        list_entry_id = create_list_entry(person_id)
        populate_affinity_entry(
            person_id, list_entry_id, body_text, received_at, source, conversation_id
        )
    except Exception:
        release_conversation_claim(conversation_id)
        raise  # let function_app.py's error handler log it and Graph retry

    # If field population fails, the entry exists in Affinity and future
    # notifications for this thread won't create duplicates.
    logger.info("Affinity population complete for conversationId %s.", conversation_id)

    logger.info(
        "Affinity entry created | list_entry_id: %s | person: %s %s <%s> | source: %s",
        list_entry_id,
        first_name,
        last_name,
        sender_email,
        source,
    )

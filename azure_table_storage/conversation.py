from azure_table_storage.client import get_table_client
from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError
from config import STORAGE_CONNECTION_STRING, STORAGE_TABLE_NAME, TABLE_PARTITION_KEY

# ─────────────────────────────────────────────────────────────────────────────
# Azure Table Storage
# ─────────────────────────────────────────────────────────────────────────────

def try_claim_conversation(
    conversation_id: str, sender_email: str, received_at: str
) -> bool:
    """
    Atomically attempt to claim a conversationId by inserting a new row.
    Returns True if this invocation successfully claimed it (i.e., it's the
    first to process this conversation). Returns False if the row already
    exists, meaning another invocation already claimed it.

    Uses insert-only (not upsert) so that concurrent executions race to
    write the row, and only one wins — eliminating the check-then-act
    race condition.
    """
    entity = {
        "PartitionKey": TABLE_PARTITION_KEY,
        "RowKey": conversation_id,
        "SenderEmail": sender_email,
        "ReceivedAt": received_at,
    }
    try:
        get_table_client(STORAGE_CONNECTION_STRING, STORAGE_TABLE_NAME).create_entity(entity=entity)
        return True
    except ResourceExistsError:
        return False  # Another invocation already claimed this conversation


def release_conversation_claim(conversation_id: str) -> None:
    """Delete a claimed conversationId row so the message can be retried."""
    try:
        get_table_client(STORAGE_CONNECTION_STRING, STORAGE_TABLE_NAME).delete_entity(
            partition_key=TABLE_PARTITION_KEY,
            row_key=conversation_id,
        )
    except ResourceNotFoundError:
        pass  # nothing to do

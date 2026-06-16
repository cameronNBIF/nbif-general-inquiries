from azure.data.tables import TableClient
from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError

from config import STORAGE_CONNECTION_STRING, STORAGE_TABLE_NAME, TABLE_PARTITION_KEY

# ─────────────────────────────────────────────────────────────────────────────
# Azure Table Storage
# ─────────────────────────────────────────────────────────────────────────────


def get_table_client() -> TableClient:
    return TableClient.from_connection_string(
        conn_str=STORAGE_CONNECTION_STRING,
        table_name=STORAGE_TABLE_NAME,
    )

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
        get_table_client().create_entity(entity=entity)
        return True
    except ResourceExistsError:
        return False  # Another invocation already claimed this conversation

def conversation_exists(conversation_id: str) -> bool:
    """
    Return True if this conversationId has already been written to Table Storage,
    meaning an Affinity entry for this thread already exists.

    This is the deduplication gate — replies to existing threads return True
    and are skipped without touching Affinity.
    """
    try:
        get_table_client().get_entity(
            partition_key=TABLE_PARTITION_KEY,
            row_key=conversation_id,
        )
        return True
    except ResourceNotFoundError:
        return False


def store_conversation(
    conversation_id: str, sender_email: str, received_at: str
) -> None:
    """
    Persist a new conversationId row after a successful Affinity entry creation.
    Uses upsert (insert-or-replace) so re-processing the same message ID from
    a Graph retry is safely idempotent.
    """
    entity = {
        "PartitionKey": TABLE_PARTITION_KEY,
        "RowKey": conversation_id,
        "SenderEmail": sender_email,
        "ReceivedAt": received_at,
    }
    get_table_client().upsert_entity(entity=entity)


def get_stored_value(row_key: str) -> str | None:
    """
    Retrieve a single string value from Table Storage by its row key.
    Used to fetch the Graph subscription ID that was stored during Step 7.
    Returns None if the row does not exist.
    """
    try:
        entity = get_table_client().get_entity(
            partition_key=TABLE_PARTITION_KEY,
            row_key=row_key,
        )
        return entity.get("Value")
    except ResourceNotFoundError:
        return None


def store_value(row_key: str, value: str) -> None:
    """Store a simple key-value row — used to persist the Graph subscription ID."""
    entity = {
        "PartitionKey": TABLE_PARTITION_KEY,
        "RowKey": row_key,
        "Value": value,
    }
    get_table_client().upsert_entity(entity=entity)

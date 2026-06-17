from azure_table_storage.client import get_table_client
from azure.core.exceptions import ResourceNotFoundError
from config import TABLE_PARTITION_KEY

# ─────────────────────────────────────────────────────────────────────────────
# Azure Table Storage
# ─────────────────────────────────────────────────────────────────────────────


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

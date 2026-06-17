import functools
from azure.data.tables import TableClient

# ─────────────────────────────────────────────────────────────────────────────
# Azure Table Storage
# ─────────────────────────────────────────────────────────────────────────────


@functools.lru_cache(maxsize=2)
def get_table_client(connection_string: str, table_name: str) -> TableClient:
    return TableClient.from_connection_string(
        conn_str=connection_string, table_name=table_name
    )

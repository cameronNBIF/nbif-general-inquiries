# config.py
import os

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
#
# All values are injected as environment variables by the Azure Function App
# at runtime. Secrets are resolved from Key Vault references transparently —
# by the time os.environ reads them here, they are already plain strings.
# ─────────────────────────────────────────────────────────────────────────────

GRAPH_USER_EMAIL          = os.environ["GRAPH_USER_EMAIL"]
FORM_SUBJECT_PREFIX       = os.environ["FORM_SUBJECT_PREFIX"]
GRAPH_WEBHOOK_SECRET      = os.environ["GRAPH_WEBHOOK_SECRET"]
AZURE_CLIENT_ID           = os.environ["AZURE_CLIENT_ID"]
AZURE_TENANT_ID           = os.environ["AZURE_TENANT_ID"]
AZURE_CLIENT_SECRET       = os.environ["AZURE_CLIENT_SECRET"]
AFFINITY_API_KEY          = os.environ["AFFINITY_API_KEY"]
AFFINITY_LIST_ID          = os.environ["AFFINITY_LIST_ID"]
AFFINITY_STATUS_NEW_ID    = os.environ["AFFINITY_STATUS_NEW_ID"]
STORAGE_CONNECTION_STRING = os.environ["STORAGE_CONNECTION_STRING"]
STORAGE_TABLE_NAME        = os.environ["STORAGE_TABLE_NAME"]

AFFINITY_FIELD_IDS = {
    "message":       os.environ["AFFINITY_FIELD_ID_MESSAGE"],
    "date_received": os.environ["AFFINITY_FIELD_ID_DATE_RECEIVED"],
    "source":        os.environ["AFFINITY_FIELD_ID_SOURCE"],
    "thread_id":     os.environ["AFFINITY_FIELD_ID_THREAD_ID"],
    "status":        os.environ["AFFINITY_FIELD_ID_STATUS"],
}

GRAPH_BASE            = "https://graph.microsoft.com/v1.0"
GRAPH_SCOPE           = "https://graph.microsoft.com/.default"
AFFINITY_BASE         = "https://api.affinity.co"
TABLE_PARTITION_KEY   = "nbif"
SUBSCRIPTION_ROW_KEY  = "graph_subscription_id"
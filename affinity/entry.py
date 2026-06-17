from affinity.client import get_affinity_session
from config import (
    AFFINITY_BASE,
    AFFINITY_FIELD_IDS,
    AFFINITY_LIST_ID,
    AFFINITY_STATUS_NEW,
)

# ─────────────────────────────────────────────────────────────────────────────
# Affinity
# ─────────────────────────────────────────────────────────────────────────────


def set_field_value(
    person_id: int, list_entry_id: int, field_id: str, value, existing_values: dict
) -> None:
    """Set a single custom field value on a list entry, updating if it already exists."""
    existing_id = existing_values.get(int(field_id))

    session = get_affinity_session()

    if existing_id:
        resp = session.put(
            f"{AFFINITY_BASE}/field-values/{existing_id}",
            json={"value": value},
        )
    else:
        resp = session.post(
            f"{AFFINITY_BASE}/field-values",
            json={
                "field_id": int(field_id),
                "entity_id": person_id,
                "list_entry_id": list_entry_id,
                "value": value,
            },
        )

    resp.raise_for_status()


def create_list_entry(person_id: int) -> int:
    """
    Add the resolved Person to the General Inquiries list.
    """

    session = get_affinity_session()

    resp = session.post(
        f"{AFFINITY_BASE}/lists/{AFFINITY_LIST_ID}/list-entries",
        json={"entity_id": person_id},
    )
    resp.raise_for_status()
    return resp.json()["id"]


def populate_affinity_entry(
    person_id: int,
    list_entry_id: int,
    message: str,
    received_at: str,
    source: str,
    conversation_id: str,
) -> None:
    # Fetch all existing field values for this list entry once

    session = get_affinity_session()

    resp = session.get(
        f"{AFFINITY_BASE}/field-values",
        params={"list_entry_id": list_entry_id},
    )
    resp.raise_for_status()
    existing_values = {fv["field_id"]: fv["id"] for fv in resp.json()}

    set_field_value(
        person_id,
        list_entry_id,
        AFFINITY_FIELD_IDS["message"],
        message,
        existing_values,
    )
    set_field_value(
        person_id,
        list_entry_id,
        AFFINITY_FIELD_IDS["date_received"],
        received_at,
        existing_values,
    )
    set_field_value(
        person_id, list_entry_id, AFFINITY_FIELD_IDS["source"], source, existing_values
    )
    set_field_value(
        person_id,
        list_entry_id,
        AFFINITY_FIELD_IDS["thread_id"],
        conversation_id,
        existing_values,
    )
    set_field_value(
        person_id,
        list_entry_id,
        AFFINITY_FIELD_IDS["status"],
        int(AFFINITY_STATUS_NEW),
        existing_values,
    )

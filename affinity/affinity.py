from config import AFFINITY_API_KEY, AFFINITY_BASE, AFFINITY_FIELD_IDS, AFFINITY_LIST_ID, AFFINITY_STATUS_NEW_ID

import requests

# ─────────────────────────────────────────────────────────────────────────────
# Affinity
# ─────────────────────────────────────────────────────────────────────────────

def affinity_auth() -> tuple[str, str]:
    """
    Affinity uses HTTP Basic Auth with an empty username and the API key
    as the password.
    """
    return ("", AFFINITY_API_KEY)


def resolve_or_create_person(first_name: str, last_name: str, email: str) -> int:
    """
    Attempt to find an existing Person in Affinity by their email. 
    If they do not exist, create a new Person.
    """
    search_resp = requests.get(
        f"{AFFINITY_BASE}/persons",
        params={"term": email},
        auth=affinity_auth(),
    )
    search_resp.raise_for_status()
    
    search_data = search_resp.json()
    persons_list = search_data.get("persons", [])
    
    if persons_list and len(persons_list) > 0:
        return persons_list[0]["id"]
        
    create_resp = requests.post(
        f"{AFFINITY_BASE}/persons",
        json={
            "first_name": first_name,
            "last_name":  last_name,
            "emails":     [email],
        },
        auth=affinity_auth(),
    )
    create_resp.raise_for_status()
    return create_resp.json()["id"]


def create_list_entry(person_id: int) -> int:
    """
    Add the resolved Person to the General Inquiries list.
    """
    resp = requests.post(
        f"{AFFINITY_BASE}/lists/{AFFINITY_LIST_ID}/list-entries",
        json={"entity_id": person_id},
        auth=affinity_auth(),
    )
    resp.raise_for_status()
    return resp.json()["id"]


def set_field_value(person_id: int, list_entry_id: int, field_id: str, value) -> None:
    """Set a single custom field value on a list entry."""
    resp = requests.post(
        f"{AFFINITY_BASE}/field-values",
        json={
            "field_id":      int(field_id),
            "entity_id":     person_id,      # <--- The missing piece!
            "list_entry_id": list_entry_id,
            "value":         value,
        },
        auth=affinity_auth(),
    )
    resp.raise_for_status()


def populate_affinity_entry(
    person_id: int,
    list_entry_id: int,
    message: str,
    received_at: str,
    source: str,
    conversation_id: str,
) -> None:
    """
    Write all five custom field values to the list entry.
    """
    set_field_value(person_id, list_entry_id, AFFINITY_FIELD_IDS["message"],       message)
    set_field_value(person_id, list_entry_id, AFFINITY_FIELD_IDS["date_received"], received_at)
    set_field_value(person_id, list_entry_id, AFFINITY_FIELD_IDS["source"],        source)
    set_field_value(person_id, list_entry_id, AFFINITY_FIELD_IDS["thread_id"],     conversation_id)
    set_field_value(person_id, list_entry_id, AFFINITY_FIELD_IDS["status"], int(AFFINITY_STATUS_NEW_ID))
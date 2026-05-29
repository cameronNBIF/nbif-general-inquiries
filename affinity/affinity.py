from config import AFFINITY_API_KEY, AFFINITY_BASE, AFFINITY_FIELD_IDS, AFFINITY_LIST_ID

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
    
    # If a match is found, return the existing ID
    if persons_list and len(persons_list) > 0:
        return persons_list[0]["id"]
        
    # If the search comes back empty, they are new — create them
    # (The /persons endpoint successfully parses JSON bodies)
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


def get_existing_list_entry(person_id: int) -> int | None:
    """
    Fetch the person's profile to find their existing entry on our specific list.
    """
    resp = requests.get(
        f"{AFFINITY_BASE}/persons/{person_id}",
        auth=affinity_auth(),
    )
    resp.raise_for_status()
    
    person_data = resp.json()
    for entry in person_data.get("list_entries", []):
        if str(entry.get("list_id")) == str(AFFINITY_LIST_ID):
            return entry.get("id")
            
    return None


def create_list_entry(person_id: int) -> int:
    """
    Add the resolved Person to the General Inquiries list.
    If they are already on the list, gracefully return their existing list entry ID.
    """
    try:
        # We use data= (form-encoding) because the list-entries endpoint 
        # often rejects application/json bodies with RequiredErrors.
        resp = requests.post(
            f"{AFFINITY_BASE}/lists/{AFFINITY_LIST_ID}/list-entries",
            data={"entity_id": person_id},
            auth=affinity_auth(),
        )
        resp.raise_for_status()
        return resp.json()["id"]
        
    except requests.HTTPError as exc:
        if exc.response.status_code == 422:
            # A 422 here almost always means the person is already on the list.
            # We catch it and fetch their existing list entry ID instead of crashing.
            existing_id = get_existing_list_entry(person_id)
            if existing_id:
                return existing_id
                
        # If it's a different error (or they aren't on the list), bubble the error up
        raise


def set_field_value(list_entry_id: int, field_id: str, value) -> None:
    """Set a single custom field value on a list entry."""
    # We use data= here as well for endpoint consistency
    resp = requests.post(
        f"{AFFINITY_BASE}/field-values",
        data={
            "field_id":      int(field_id),
            "list_entry_id": list_entry_id,
            "value":         value,
        },
        auth=affinity_auth(),
    )
    resp.raise_for_status()


def populate_affinity_entry(
    list_entry_id: int,
    message: str,
    received_at: str,
    source: str,
    conversation_id: str,
) -> None:
    """
    Write all five custom field values to the list entry.
    Status is always set to 'New' so the team knows it requires attention.
    """
    set_field_value(list_entry_id, AFFINITY_FIELD_IDS["message"],       message)
    set_field_value(list_entry_id, AFFINITY_FIELD_IDS["date_received"], received_at)
    set_field_value(list_entry_id, AFFINITY_FIELD_IDS["source"],        source)
    set_field_value(list_entry_id, AFFINITY_FIELD_IDS["thread_id"],     conversation_id)
    set_field_value(list_entry_id, AFFINITY_FIELD_IDS["status"],        "New")
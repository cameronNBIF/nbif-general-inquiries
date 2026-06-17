import requests

from affinity.client import affinity_auth
from config import AFFINITY_BASE


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

    for person in persons_list:
        if any(e.lower() == email.lower() for e in person.get("emails", [])):
            return person["id"]

    body = {
        "first_name": first_name,
        "emails": [email],
    }
    if last_name:  # only include if non-empty
        body["last_name"] = last_name
    else:
        body["last_name"] = ""

    create_resp = requests.post(
        f"{AFFINITY_BASE}/persons",
        json=body,
        auth=affinity_auth(),
    )
    create_resp.raise_for_status()
    return create_resp.json()["id"]
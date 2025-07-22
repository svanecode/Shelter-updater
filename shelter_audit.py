import sys
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
import os

# --- Configuration (hard-coded) ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DATAFORDELER_USERNAME = os.getenv("DATAFORDELER_USERNAME")
DATAFORDELER_PASSWORD = os.getenv("DATAFORDELER_PASSWORD")
BBR_API_URL = os.getenv("BBR_API_URL")
DAR_API_URL = os.getenv("DAR_API_URL")

# Validate that variables are set
if not (SUPABASE_URL and SUPABASE_KEY and DATAFORDELER_USERNAME and DATAFORDELER_PASSWORD):
    sys.stderr.write("Error: One or more configuration variables are missing.\n")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Requests session with retry/backoff
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retries)
session.mount('https://', adapter)
session.mount('http://', adapter)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

PAGE_SIZE = 1000

# --- Helper functions ---

def fetch_all_shelters() -> List[Dict[str, Any]]:
    """
    Fetches shelter records last checked over a month ago (or never checked) using pagination.
    """
    shelters: List[Dict[str, Any]] = []
    offset = 0
    cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()
    while True:
        params = {
            'select': '*',
            'order': 'last_checked.asc.nullsfirst',
            'or': f'(last_checked.is.null,last_checked.lt.{cutoff})',
            'limit': PAGE_SIZE,
            'offset': offset
        }
        url = f"{SUPABASE_URL}/rest/v1/sheltersv2"
        try:
            r = session.get(url, headers=HEADERS, params=params)
            r.raise_for_status()
            batch = r.json()
            if not isinstance(batch, list) or not batch:
                break
            shelters.extend(batch)
            offset += PAGE_SIZE
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching shelters: {e}")
            break
    return shelters


def fetch_bbr_data(bygning_id: str) -> Optional[Dict[str, Any]]:
    """Fetches building data from the BBR API."""
    params = {
        "username": DATAFORDELER_USERNAME,
        "password": DATAFORDELER_PASSWORD,
        "format": "json",
        "Id": bygning_id
    }
    try:
        r = session.get(f"{BBR_API_URL}/bygning", params=params)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list) and data:
            return data[0]
    except requests.exceptions.RequestException as e:
        logger.error(f"BBR fetch error for {bygning_id}: {e}")
    return None


def fetch_dar_data(husnummer_id: str) -> Optional[Dict[str, Any]]:
    """Fetches address data from the DAR API."""
    params = {
        "username": DATAFORDELER_USERNAME,
        "password": DATAFORDELER_PASSWORD,
        "format": "json",
        "id": husnummer_id
    }
    try:
        r = session.get(f"{DAR_API_URL}/husnummer", params=params)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list) and data:
            return data[0]
    except requests.exceptions.RequestException as e:
        logger.error(f"DAR fetch error for {husnummer_id}: {e}")
    return None


def update_shelter(bygning_id: str, update_fields: Dict[str, Any]) -> bool:
    """Updates a shelter record in Supabase and logs detailed errors."""
    url = f"{SUPABASE_URL}/rest/v1/sheltersv2?bygning_id=eq.{bygning_id}"
    try:
        r = session.patch(url, headers=HEADERS, json=update_fields)
        r.raise_for_status()
        return True
    except requests.exceptions.HTTPError as e:
        resp = e.response
        logger.error(f"Error updating shelter {bygning_id}: HTTP {resp.status_code} - {resp.text}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error updating shelter {bygning_id}: {e}")
        return False


def soft_delete_shelter(bygning_id: str, reason: str) -> bool:
    """Marks a shelter as deleted with a timestamp."""
    now = datetime.utcnow().isoformat()
    fields = {"deleted": now, "last_checked": now}
    logger.info(f"Soft deleting {bygning_id} (Reason: {reason})")
    return update_shelter(bygning_id, fields)


def main() -> None:
    shelters = fetch_all_shelters()
    total = len(shelters)
    if total == 0:
        logger.info("No shelters need checking (all up to date).")
        return

    for idx, shelter in enumerate(shelters, start=1):
        bygning_id = shelter.get("bygning_id")
        print(f"[{idx}/{total}] ", end="", flush=True)
        if not bygning_id:
            print("Skipped (no id)")
            continue

        bbr = fetch_bbr_data(bygning_id)
        now = datetime.utcnow().isoformat()

        # Determine deletion reason
        if not bbr:
            reason = "Not found in BBR"
        elif not bbr.get("byg069Sikringsrumpladser"):
            reason = "No shelter capacity"
        elif bbr.get("status") != "6":
            reason = f"Status not 'in use' (status={bbr.get('status')})"
        else:
            reason = None

        if reason:
            success = soft_delete_shelter(bygning_id, reason)
            print(f"Deleted {bygning_id} (Reason: {reason})" if success else f"Failed delete {bygning_id}")
            continue

        # Prepare updates
        updates: Dict[str, Any] = {}
        bbr_map = {
            "byg069Sikringsrumpladser": "shelter_capacity",
            "byg021BygningensAnvendelse": "anvendelse",
            "kommunekode": "kommunekode"
        }
        for b_key, s_key in bbr_map.items():
            val = bbr.get(b_key)
            if val != shelter.get(s_key):
                updates[s_key] = val

        husnummer_id = bbr.get("husnummer")
        if husnummer_id:
            dar = fetch_dar_data(husnummer_id)
            if dar:
                dar_map = {
                    "adgangsadressebetegnelse": "address",
                    lambda d: d.get("postnummer", {}).get("postnr"): "postnummer",
                    lambda d: d.get("navngivenVej", {}).get("vejnavn"): "vejnavn",
                    "husnummertekst": "husnummer"
                }
                for d_key, s_key in dar_map.items():
                    val = d_key(dar) if callable(d_key) else dar.get(d_key)
                    if val and val != shelter.get(s_key):
                        updates[s_key] = val

        if updates:
            updates["last_checked"] = now
            success = update_shelter(bygning_id, updates)
            print(f"Updated {bygning_id}: {updates}" if success else f"Failed update {bygning_id}")
        else:
            update_shelter(bygning_id, {"last_checked": now})
            print(f"No changes for {bygning_id}")

if __name__ == "__main__":
    main()

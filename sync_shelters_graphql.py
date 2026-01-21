#!/usr/bin/env python3
"""
Shelter Sync via GraphQL

This script synchronizes shelters from Datafordeler BBR GraphQL API to Supabase.
It performs a full synchronization of all active shelters (status 6).

Features:
- Fetches all shelters with status 6 (Civil Defense) from BBR GraphQL.
- Compares with existing Supabase records to minimize writes.
- Fetches detailed address data from DAR for new shelters.
- Soft-deletes shelters that are no longer present in BBR.
- Resurrects soft-deleted shelters if they reappear.
"""

import os
import sys
import time
import random
import json
import requests
import logging
from datetime import datetime
from typing import Dict, Any, List, Set, Optional
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()

# Environment Variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DATAFORDELER_API_KEY = os.getenv("DATAFORDELER_API_KEY")

# Validation
def validate_env():
    required_vars = [
        "SUPABASE_URL", "SUPABASE_KEY", "DATAFORDELER_API_KEY"
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"CRITICAL: Missing environment variables: {', '.join(missing_vars)}")
        sys.exit(1)

BBR_GRAPHQL_URL = "https://graphql.datafordeler.dk/BBR/v1"

# Tuning parameters
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "200")) # Supabase upsert batch size
DAR_SLEEP_TIME = float(os.getenv("DAR_SLEEP_TIME", "0.1")) # Throttle DAR requests
GRAPHQL_PAGE_SLEEP = float(os.getenv("GRAPHQL_PAGE_SLEEP", "0.2")) # Throttle GraphQL pages
PAGE_SIZE = int(os.getenv("PAGE_SIZE", "500")) # GraphQL objects per page
ADDRESS_REFRESH_DAYS = int(os.getenv("ADDRESS_REFRESH_DAYS", "90")) # Re-fetch address if data is older than this
MAX_GRAPHQL_RETRIES = int(os.getenv("MAX_GRAPHQL_RETRIES", "8")) # Max retries per page
GRAPHQL_RETRY_BASE_SLEEP = int(os.getenv("GRAPHQL_RETRY_BASE_SLEEP", "5")) # Base backoff for retryable errors (seconds)
SAFE_THRESHOLD = int(os.getenv("SAFE_THRESHOLD", "500"))
MIN_DELETE_COVERAGE = float(os.getenv("MIN_DELETE_COVERAGE", "0.8"))
SUMMARY_PATH = os.getenv("SUMMARY_PATH")
LOG_PAGE_INTERVAL = int(os.getenv("LOG_PAGE_INTERVAL", "10"))

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ShelterSync")

HEADERS_SUPABASE = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates",
}

def fetch_existing_state() -> Dict[str, Dict[str, Any]]:
    """
    Loads all existing shelter IDs and their state from Supabase.
    Returns a dict mapped by bygning_id.
    """
    logger.info("Fetching existing state from Supabase...")
    state = {}
    offset = 0
    limit = 1000 # Set to 1000 to match Supabase default max rows
    session = requests.Session()
    session.headers.update(HEADERS_SUPABASE)
    
    while True:
        headers = {"Range": f"{offset}-{offset + limit - 1}"}
        # Select location to check if we need to backfill coordinates
        url = (
            f"{SUPABASE_URL}/rest/v1/sheltersv2?"
            "select=id,bygning_id,shelter_capacity,deleted,last_checked,last_address_checked,"
            "location,anvendelse,kommunekode&order=id.asc"
        )
        data = None
        for attempt in range(1, 4):
            try:
                r = session.get(url, headers=headers, timeout=60)
                r.raise_for_status()
                data = r.json()
                break
            except Exception as e:
                if attempt == 3:
                    logger.error(f"Error fetching state: {e}")
                    sys.exit(1)
                time.sleep(2 * attempt)

        if not data:
            break

        for item in data:
            bid = item.get('bygning_id')
            if bid:
                state[bid] = {
                    'id': item['id'],
                    'capacity': item.get('shelter_capacity'),
                    'deleted': item.get('deleted') is not None,
                    'last_checked': item.get('last_checked'),
                    'last_address_checked': item.get('last_address_checked'),
                    'location': item.get('location'),
                    'anvendelse': item.get('anvendelse'),
                    'kommunekode': item.get('kommunekode')
                }

        if len(data) < limit:
            break
        offset += limit
        print(f"  Loaded {len(state)} records...", end='\r')
            
    print() # Clear line
    logger.info(f"Total loaded: {len(state)} records.")
    return state

def fetch_address_data(husnummer_id: str) -> Dict[str, Any]:
    """
    Fetches address details and WGS84 coordinates from DAWA (Dataforsyningen).
    Replaces the old Datafordeler DAR lookup to get proper GeoJSON coordinates.
    """
    if not husnummer_id: return {}
    
    url = f"https://api.dataforsyningen.dk/adgangsadresser/{husnummer_id}"
    
    try:
        # Retry logic
        for attempt in range(3):
            try:
                r = requests.get(url, timeout=10)
                if r.status_code == 404:
                    # Address ID not found in DAWA (might be obsolete)
                    return {}
                if r.status_code == 429:
                    time.sleep(1 * (attempt + 1))
                    continue
                r.raise_for_status()
                data = r.json()
                
                # Extract Address Components
                # Note: 'navngivenvej' only contains href/id. Street name is in 'vejstykke'.
                vej = data.get('vejstykke', {})
                post = data.get('postnummer', {})
                husnr = data.get('husnr')
                
                # Extract Coordinates (WGS84: [lon, lat])
                coords = data.get('adgangspunkt', {}).get('koordinater')
                location_geojson = None
                if coords and len(coords) == 2:
                    location_geojson = {
                        "type": "Point",
                        "coordinates": coords # DAWA returns [lon, lat]
                    }

                return {
                    "address": data.get('adressebetegnelse'),
                    "vejnavn": vej.get('navn'),
                    "husnummer": husnr,
                    "postnummer": post.get('nr'),
                    "location": location_geojson
                }
            except requests.exceptions.RequestException:
                if attempt == 2: raise
                time.sleep(0.5)
        return {}
    except Exception as e:
        logger.warning(f"Failed to fetch address data for {husnummer_id}: {e}")
        return {}

def should_refresh_address(
    last_address_checked_str: Optional[str],
    last_checked_str: Optional[str]
) -> bool:
    """Returns True if the record hasn't been updated/checked in a long time."""
    ts_str = last_address_checked_str or last_checked_str
    if not ts_str:
        return True
    try:
        # Robust parsing: Take first 19 chars (YYYY-MM-DDTHH:MM:SS) ignoring fractional/TZ
        # This avoids python version differences with isoformat
        clean_ts = ts_str[:19]
        last_checked = datetime.fromisoformat(clean_ts)
        days_diff = (datetime.utcnow() - last_checked).days
        return days_diff > ADDRESS_REFRESH_DAYS
    except ValueError as e:
        logger.warning(f"Date parse error for {ts_str}: {e} -> Forcing refresh.")
        return True

def save_cursor(cursor: Optional[str]):
    """Saves the current GraphQL cursor to Supabase."""
    try:
        url = f"{SUPABASE_URL}/rest/v1/sync_state?id=eq.1"
        data = {"cursor": cursor, "last_run": datetime.utcnow().isoformat()}
        requests.patch(url, headers=HEADERS_SUPABASE, json=data, timeout=10)
    except Exception as e:
        logger.warning(f"Failed to save cursor: {e}")

def get_saved_cursor() -> Optional[str]:
    """Retrieves the last saved cursor."""
    try:
        url = f"{SUPABASE_URL}/rest/v1/sync_state?id=eq.1&select=cursor"
        r = requests.get(url, headers=HEADERS_SUPABASE, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data: return data[0].get('cursor')
    except Exception as e:
        logger.warning(f"Failed to get cursor: {e}")
    return None

def sync():
    validate_env()
    logger.info("Starting GraphQL Sync...")
    
    # Try to resume
    saved_cursor = get_saved_cursor()
    if saved_cursor:
        logger.info(f"Resuming from saved cursor: {saved_cursor[:10]}...")
        after = saved_cursor
    else:
        after = None

    existing_state = fetch_existing_state()
    
    seen_ids = set()
    unchanged_ids = []
    stats = {
        "new": 0,
        "updated": 0,
        "restored": 0,
        "unchanged": 0,
        "deleted": 0,
        "address_refreshed": 0,
        "missing_location": 0
    }
    
    # Time variable for GraphQL (Datafordeler expects strict ISO8601)
    run_ts = datetime.utcnow().isoformat()
    now_ts = datetime.utcnow().isoformat(timespec='seconds') + "Z"
    
    query = """
    query GetShelters($now: DafDateTime, $after: String, $first: Int) {
      BBR_Bygning(
        first: $first, 
        after: $after,
        registreringstid: $now, 
        virkningstid: $now,
        where: { 
          status: { eq: \"6\" }
        }
      ) {
        nodes {
          id_lokalId
          byg069Sikringsrumpladser
          byg021BygningensAnvendelse
          kommunekode
          husnummer
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
    """
    
    has_next = True
    completed_successfully = False
    graphql_had_errors = False
    graphql_error_count = 0
    page_index = 0
    
    insert_queue_full = []
    insert_queue_partial = []
    
    session = requests.Session()

    def write_summary(payload: Dict[str, Any]):
        if not SUMMARY_PATH:
            return
        try:
            with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write summary file: {e}")

    summary_payload = {
        "new": stats["new"],
        "updated": stats["updated"],
        "restored": stats["restored"],
        "deleted": stats["deleted"],
        "address_refreshed": stats["address_refreshed"],
        "missing_location": stats["missing_location"],
        "unchanged": stats["unchanged"],
        "pages": page_index,
        "seen_ids": len(seen_ids),
        "active_existing": 0,
        "min_seen_required": 0,
        "graphql_error_count": graphql_error_count,
        "completed_successfully": completed_successfully,
        "graphql_had_errors": graphql_had_errors,
        "timestamp_utc": datetime.utcnow().isoformat()
    }
    write_summary(summary_payload)
    
    def post_graphql_with_retry(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for attempt in range(1, MAX_GRAPHQL_RETRIES + 1):
            try:
                r = session.post(
                    BBR_GRAPHQL_URL,
                    json=payload,
                    params={"apikey": DATAFORDELER_API_KEY},
                    timeout=45
                )

                if r.status_code == 200:
                    res_data = r.json()
                    if "errors" in res_data:
                        logger.error(f"GraphQL API Errors: {res_data['errors']}")
                        raise RuntimeError("GraphQL errors returned in response.")
                    return res_data

                if r.status_code in {429, 500, 502, 503, 504}:
                    logger.warning(
                        f"GraphQL transient error (Status {r.status_code}), retry {attempt}/{MAX_GRAPHQL_RETRIES}..."
                    )
                else:
                    logger.error(f"GraphQL Error (Status {r.status_code}): {r.text}")
                    return None
            except Exception as e:
                logger.warning(f"GraphQL request failed (attempt {attempt}): {e}")

            backoff = GRAPHQL_RETRY_BASE_SLEEP * (2 ** (attempt - 1))
            jitter = random.uniform(0, 1.0)
            time.sleep(backoff + jitter)

        logger.error("GraphQL request failed after max retries.")
        return None

    while has_next:
        try:
            payload = {
                'query': query, 
                'variables': {"now": now_ts, "after": after, "first": PAGE_SIZE}
            }

            res_data = post_graphql_with_retry(payload)
            if res_data is None:
                graphql_had_errors = True
                graphql_error_count += 1
                logger.error(
                    "GraphQL failed for page "
                    f"{page_index} (cursor={after}, seen={len(seen_ids)})"
                )
                break
                
            data_block = res_data.get('data', {}).get('BBR_Bygning', {})
            nodes = data_block.get('nodes', [])
            page_info = data_block.get('pageInfo', {})
            
            page_index += 1
            if page_index % LOG_PAGE_INTERVAL == 0 or page_index == 1:
                logger.info(
                    "GraphQL progress: page=%s, nodes=%s, seen=%s",
                    page_index,
                    len(nodes),
                    len(seen_ids)
                )

            for node in nodes:
                # FILTER: Only valid capacity
                cap_val = node.get('byg069Sikringsrumpladser')
                try:
                    capacity = int(cap_val)
                except (TypeError, ValueError):
                    continue
                if capacity <= 0:
                    continue

                bygning_id = node['id_lokalId']
                incoming_anvendelse = node.get('byg021BygningensAnvendelse')
                incoming_kommunekode = node.get('kommunekode')
                seen_ids.add(bygning_id)
                
                curr = existing_state.get(bygning_id)
                record_update = {}
                
                needs_address = False
                action = "none"

                if not curr:
                    # NEW RECORD
                    action = f"new (Cap: {capacity})"
                    stats["new"] += 1
                    needs_address = True
                    # Per-record logs are intentionally suppressed to keep output concise.
                
                else:
                    # EXISTING RECORD
                    has_missing_location = curr.get('location') is None

                    if curr['deleted']:
                        action = "restored (was deleted)"
                        stats["restored"] += 1
                        record_update = {"deleted": None}
                        needs_address = True # Fetch address to ensure restored record is complete
                        # Per-record logs are intentionally suppressed to keep output concise.
                    
                    elif (
                        curr.get('capacity') != capacity
                        or curr.get('anvendelse') != incoming_anvendelse
                        or curr.get('kommunekode') != incoming_kommunekode
                    ):
                        action = (
                            "updated (capacity/anvendelse/kommunekode changed)"
                        )
                        stats["updated"] += 1
                        # Per-record logs are intentionally suppressed to keep output concise.
                    
                    elif (
                        should_refresh_address(
                            curr.get('last_address_checked'),
                            curr.get('last_checked')
                        )
                        or has_missing_location
                    ):
                        reason = "missing_loc" if has_missing_location else "stale"
                        last_addr = curr.get('last_address_checked') or curr.get('last_checked')
                        action = f"refresh_addr ({reason}, last: {last_addr})"
                        stats["address_refreshed"] += 1
                        needs_address = True
                    
                    else:
                        stats["unchanged"] += 1
                        unchanged_ids.append(bygning_id)
                        continue # Skip upsert if absolutely nothing changed

                # Prepare the record
                record_update["_action"] = action # Store action for logging

                if "new" in action or needs_address:
                    addr_data = fetch_address_data(node.get('husnummer'))
                    time.sleep(DAR_SLEEP_TIME) # Polite throttling
                    if addr_data.get("location") is None:
                        stats["missing_location"] += 1

                    address_fields = {}
                    for key in ("address", "postnummer", "vejnavn", "husnummer", "location"):
                        if key in addr_data and addr_data.get(key) is not None:
                            address_fields[key] = addr_data.get(key)

                    record_update.update({
                        "bygning_id": bygning_id,
                        "shelter_capacity": capacity,
                        "anvendelse": incoming_anvendelse,
                        "kommunekode": incoming_kommunekode,
                        "last_checked": run_ts,
                        "last_seen_at": run_ts,
                        "last_address_checked": run_ts
                    })
                    if address_fields:
                        record_update.update(address_fields)
                    insert_queue_full.append(record_update)
                else:
                    # Minimal update
                    record_update.update({
                        "bygning_id": bygning_id,
                        "shelter_capacity": capacity,
                        "anvendelse": incoming_anvendelse,
                        "kommunekode": incoming_kommunekode,
                        "last_checked": run_ts,
                        "last_seen_at": run_ts
                    })
                    insert_queue_partial.append(record_update)
                
                # Flush queues
                if len(insert_queue_full) >= BATCH_SIZE:
                    upsert_to_supabase(insert_queue_full)
                    insert_queue_full = []
                
                if len(insert_queue_partial) >= BATCH_SIZE:
                    upsert_to_supabase(insert_queue_partial)
                    insert_queue_partial = []

            has_next = page_info.get('hasNextPage', False)
            after = page_info.get('endCursor')
            
            # SAVE PROGRESS
            save_cursor(after)

            if page_index % LOG_PAGE_INTERVAL == 0 or not has_next:
                logger.info(
                    "Page complete %s: has_next=%s",
                    page_index,
                    has_next
                )

            summary_payload.update({
                "new": stats["new"],
                "updated": stats["updated"],
                "restored": stats["restored"],
                "deleted": stats["deleted"],
                "address_refreshed": stats["address_refreshed"],
                "missing_location": stats["missing_location"],
                "unchanged": stats["unchanged"],
                "pages": page_index,
                "seen_ids": len(seen_ids),
                "graphql_error_count": graphql_error_count,
                "completed_successfully": completed_successfully,
                "graphql_had_errors": graphql_had_errors,
                "timestamp_utc": datetime.utcnow().isoformat()
            })
            write_summary(summary_payload)
            
            if not has_next:
                completed_successfully = True
                save_cursor(None) # Clear cursor on success
            
            # Rate limiting for GraphQL
            time.sleep(GRAPHQL_PAGE_SLEEP)

        except KeyboardInterrupt:
            logger.warning("Sync interrupted by user.")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Unexpected error during sync loop: {e}")
            break

    # Flush remaining inserts
    if insert_queue_full:
        upsert_to_supabase(insert_queue_full)
    if insert_queue_partial:
        upsert_to_supabase(insert_queue_partial)

    if completed_successfully and not graphql_had_errors:
        touch_last_seen(unchanged_ids, run_ts)
        
    # --- DELETION PHASE ---
    # Only proceed if we scanned a significant number of records to avoid wiping DB on API failure
    active_existing = sum(1 for data in existing_state.values() if not data.get('deleted'))
    min_seen_required = max(SAFE_THRESHOLD, int(active_existing * MIN_DELETE_COVERAGE))
    
    if completed_successfully and not graphql_had_errors and len(seen_ids) >= min_seen_required:
        logger.info("Processing deletions...")
        to_delete = []
        
        for bid, data in existing_state.items():
            if not data['deleted'] and bid not in seen_ids:
                to_delete.append(data['id']) # Use internal ID for faster deletion if mapped
        
        stats["deleted"] = len(to_delete)
        
        if to_delete:
            logger.info(f"Marking {len(to_delete)} records as deleted...")
            soft_delete_in_supabase(to_delete)
    else:
        if not completed_successfully:
            logger.warning("Skipping deletion phase: Scan did not complete successfully.")
        elif graphql_had_errors:
            logger.warning("Skipping deletion phase: GraphQL errors occurred during scan.")
        else:
            logger.warning(
                f"Skipping deletion phase: Too few records found ({len(seen_ids)} < {min_seen_required}). "
                "Possible API issue."
            )
        
    logger.info("Sync complete.")
    logger.info(
        "Summary: New: %s, Updated: %s, Restored: %s, Deleted: %s, "
        "Address Refreshed: %s, Missing Location: %s, Unchanged: %s",
        stats["new"],
        stats["updated"],
        stats["restored"],
        stats["deleted"],
        stats["address_refreshed"],
        stats["missing_location"],
        stats["unchanged"]
    )

    summary_payload.update({
        "new": stats["new"],
        "updated": stats["updated"],
        "restored": stats["restored"],
        "deleted": stats["deleted"],
        "address_refreshed": stats["address_refreshed"],
        "missing_location": stats["missing_location"],
        "unchanged": stats["unchanged"],
        "pages": page_index,
        "seen_ids": len(seen_ids),
        "active_existing": active_existing,
        "min_seen_required": min_seen_required,
        "graphql_error_count": graphql_error_count,
        "completed_successfully": completed_successfully,
        "graphql_had_errors": graphql_had_errors,
        "timestamp_utc": datetime.utcnow().isoformat()
    })
    write_summary(summary_payload)

    github_summary = os.getenv("GITHUB_STEP_SUMMARY")
    if github_summary:
        try:
            with open(github_summary, "a", encoding="utf-8") as f:
                f.write("## Shelter Sync Summary\n\n")
                for key, value in summary_payload.items():
                    f.write(f"- **{key}**: {value}\n")
        except Exception as e:
            logger.warning(f"Failed to write GitHub summary: {e}")

def upsert_to_supabase(batch: List[Dict]):
    if not batch: return

    cleaned_batch = []
    action_map = {} # Map ID to action for logging

    for item in batch:
        new_item = item.copy()
        if "_action" in new_item:
            action_map[new_item['bygning_id']] = new_item.pop("_action")
        cleaned_batch.append(new_item)

    url = f"{SUPABASE_URL}/rest/v1/sheltersv2?on_conflict=bygning_id"
    try:
        # Explicitly specify the conflict column for upsert
        r = requests.post(url, headers=HEADERS_SUPABASE, json=cleaned_batch, timeout=30)
        r.raise_for_status()
        
        if len(batch) == 1:
            bid = batch[0].get('bygning_id')
            act = action_map.get(bid, "unknown")
            logger.info(f"Successfully saved shelter {bid} (Reason: {act})")
        else:
            logger.info(f"Successfully saved batch of {len(batch)} records.")
    except Exception as e:
        logger.error(f"Batch upsert failed: {e}")
        if 'r' in locals() and hasattr(r, 'text'):
            logger.error(f"Response text: {r.text}")
        
        # Fallback: Try one by one
        logger.info("Retrying batch one by one...")
        for item in batch:
            try:
                # Try full update first
                r_single = requests.post(url, headers=HEADERS_SUPABASE, json=[item], timeout=10)
                r_single.raise_for_status()
            except Exception as single_e:
                logger.warning(f"Failed to upsert item {item.get('bygning_id')}: {single_e}")
                
                # EMERGENCY FALLBACK: Minimal update (Fixes FK violations preventing restore)
                try:
                    minimal_item = {
                        "bygning_id": item["bygning_id"],
                        "shelter_capacity": item.get("shelter_capacity"),
                        "last_checked": item.get("last_checked"),
                        "deleted": None, # Force un-delete
                        # Force clear potential bad FKs to allow save
                        "anvendelse": None, 
                        "kommunekode": None 
                    }
                    logger.info(f"  Attempting minimal recovery for {item.get('bygning_id')}...")
                    r_min = requests.post(url, headers=HEADERS_SUPABASE, json=[minimal_item], timeout=10)
                    r_min.raise_for_status()
                    logger.info("  Success: Minimal recovery saved.")
                except Exception as min_e:
                    logger.error(f"  Critical: Could not save record even with minimal data: {min_e}")
                    if hasattr(r_single, 'text'):
                        logger.error(f"  Original Error: {r_single.text}")
        # If batch fails, we could try one by one, but for now just log it.

def touch_last_seen(bygning_ids: List[str], run_ts: str):
    if not bygning_ids:
        return
    chunk_size = 100
    url = f"{SUPABASE_URL}/rest/v1/sheltersv2"
    for i in range(0, len(bygning_ids), chunk_size):
        chunk = bygning_ids[i:i + chunk_size]
        params = {
            "bygning_id": "in.(" + ",".join([f"\"{bid}\"" for bid in chunk]) + ")"
        }
        try:
            r = requests.patch(
                url,
                headers=HEADERS_SUPABASE,
                params=params,
                json={"last_seen_at": run_ts},
                timeout=30
            )
            r.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to update last_seen_at for chunk: {e}")

def soft_delete_in_supabase(ids: List[str]):
    chunk_size = 100
    for i in range(0, len(ids), chunk_size):
        chunk = ids[i:i + chunk_size]
        # Assuming 'id' is the primary key (UUID) or int. If 'id' is distinct from 'bygning_id'.
        # The existing state stored 'id' (supabase PK) which is safer.
        url = f"{SUPABASE_URL}/rest/v1/sheltersv2?id=in.({','.join(map(str, chunk))})"
        try:
            r = requests.patch(
                url, 
                headers=HEADERS_SUPABASE, 
                json={"deleted": datetime.utcnow().isoformat()},
                timeout=30
            )
            r.raise_for_status()
        except Exception as e:
            logger.error(f"Supabase delete error: {e}")

if __name__ == "__main__":
    sync()

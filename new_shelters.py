import requests
from datetime import datetime
import time
import sys
from dotenv import load_dotenv
import os

# --- Configuration (set your values here) ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BBR_API_URL = os.getenv("BBR_API_URL")
DAR_API_URL = os.getenv("DAR_API_URL")
DATAFORDELER_USERNAME = os.getenv("DATAFORDELER_USERNAME")
DATAFORDELER_PASSWORD = os.getenv("DATAFORDELER_PASSWORD")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

# --- Helper Functions ---

def fetch_kommune_to_process():
    """
    Fetches the next municipality to process. It prioritizes any municipality
    that is already in progress before starting a new one.
    """
    print("Fetching next municipality to process...")
    # PREREQUISITE: Your 'kommunekoder' table must have a 'last_page' (int4) column.
    
    # First, check for any municipality that is already being processed.
    in_progress_url = f"{SUPABASE_URL}/rest/v1/kommunekoder?select=kode,last_page&not.last_page.is.null&limit=1"
    try:
        r = requests.get(in_progress_url, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
        if data:
            kommune_info = data[0]
            print(f"Found in-progress municipality: {kommune_info['kode']}")
            return kommune_info
    except requests.exceptions.RequestException as e:
        print(f"Error checking for in-progress municipalities: {e}")
        # Continue to try finding a new one
    
    # If no municipalities are in progress, find a new one to start.
    print("No in-progress municipalities found. Looking for a new one to start...")
    new_url = f"{SUPABASE_URL}/rest/v1/kommunekoder?select=kode,last_page&order=last_updated.asc.nullsfirst&limit=1"
    try:
        r = requests.get(new_url, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
        if data:
            kommune_info = data[0]
            print(f"Found new municipality to start: {kommune_info['kode']}")
            return kommune_info
        else:
            print("No municipalities found in the 'kommunekoder' table.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Fatal error fetching new municipality to process: {e}")
        return None

def fetch_specific_kommune_info(kommunekode):
    """Fetches the info for a specific municipality provided via command line."""
    print(f"Fetching info for specified municipality: {kommunekode}")
    # Use the raw kommunekode for the lookup, as it might be stored with leading zeros.
    url = f"{SUPABASE_URL}/rest/v1/kommunekoder?select=kode,last_page&kode=eq.{kommunekode}&limit=1"
    try:
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
        if data:
            return data[0]
        else:
            print(f"Municipality with code {kommunekode} not found in the database.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching info for municipality {kommunekode}: {e}")
        return None


def update_kommune_progress(kommunekode, page_number):
    """Updates the 'last_page' for the current municipality and verifies the update."""
    print(f"  - Attempting to update progress for municipality {kommunekode} to page {page_number}.")
    url = f"{SUPABASE_URL}/rest/v1/kommunekoder?kode=eq.{kommunekode}"
    update_data = {"last_page": page_number}
    try:
        # The 'Prefer: return=representation' header asks Supabase to return the updated row(s).
        r = requests.patch(url, headers=HEADERS, json=update_data)
        r.raise_for_status()
        
        # Check if the response contains data, which confirms the update was successful.
        if r.json():
            print(f"  - Successfully verified progress update for {kommunekode}.")
        else:
            # This can happen if the PATCH returns 204 No Content, which means success but no body.
            # However, with 'return=representation', we expect a body. An empty body might indicate a problem.
            print(f"  - Warning: Update request for {kommunekode} was successful, but no data was returned. The row may not have been updated.")

    except requests.exceptions.RequestException as e:
        print(f"    - Error updating progress for {kommunekode}: {e}")
        print("    - Please check your SUPABASE_URL, SUPABASE_KEY, and network connection.")

def mark_kommune_as_complete(kommunekode):
    """Marks a municipality as fully scanned by updating its timestamp and resetting its page count."""
    print(f"  - Attempting to mark municipality {kommunekode} as complete.")
    url = f"{SUPABASE_URL}/rest/v1/kommunekoder?kode=eq.{kommunekode}"
    update_data = {
        "last_updated": datetime.utcnow().isoformat(),
        "last_page": None # Reset for the next cycle
    }
    try:
        r = requests.patch(url, headers=HEADERS, json=update_data)
        r.raise_for_status()
        
        if r.json():
             print(f"  - Successfully verified completion for {kommunekode}.")
        else:
             print(f"  - Warning: Completion update request for {kommunekode} was successful, but no data was returned.")

    except requests.exceptions.RequestException as e:
        print(f"    - Error marking {kommunekode} as complete: {e}")
        print("    - Please check your SUPABASE_URL, SUPABASE_KEY, and network connection.")


def fetch_existing_shelter_ids():
    """
    Fetches ALL existing bygning_id from the database, handling pagination.
    This is crucial for accurately checking for duplicates.
    """
    print("Fetching all existing shelter IDs from the database...")
    ids = set()
    offset = 0
    limit = 1000 # The default Supabase limit
    while True:
        try:
            print(f"  - Fetching shelters {offset} to {offset + limit - 1}...", end='\r')
            # Use the Range header to control pagination
            paginated_headers = HEADERS.copy()
            paginated_headers['Range'] = f"{offset}-{offset + limit - 1}"
            
            url = f"{SUPABASE_URL}/rest/v1/sheltersv2?select=bygning_id"
            r = requests.get(url, headers=paginated_headers)
            r.raise_for_status()
            
            data = r.json()
            if not data:
                # No more results, we have fetched everything
                break
            
            for item in data:
                ids.add(item['bygning_id'])
            
            offset += limit
            
        except requests.exceptions.RequestException as e:
            print(f"\nFatal error fetching existing shelter IDs: {e}")
            print("Please check your SUPABASE_URL, SUPABASE_KEY, and network connection.")
            return None
    
    print(f"\nSuccessfully fetched a total of {len(ids)} existing shelter IDs. ")
    return ids

def fetch_dar_data(husnummer_id):
    """Fetches address data from the DAR API using the husnummer UUID from BBR."""
    params = {
        "username": DATAFORDELER_USERNAME,
        "password": DATAFORDELER_PASSWORD,
        "format": "json",
        "id": husnummer_id
    }
    try:
        r = requests.get(f"{DAR_API_URL}/husnummer", params=params)
        r.raise_for_status()
        if r.json():
            return r.json()[0]
    except requests.exceptions.RequestException as e:
        print(f"    - Warning: Error fetching DAR data for husnummer ID {husnummer_id}: {e}")
    return None

def add_shelter_to_db(shelter_data):
    """Adds a new shelter record to the Supabase database."""
    url = f"{SUPABASE_URL}/rest/v1/sheltersv2"
    try:
        r = requests.post(url, headers=HEADERS, json=shelter_data)
        r.raise_for_status()
        return r.status_code == 201
    except requests.exceptions.RequestException as e:
        if 'duplicate key value violates unique constraint' in str(e):
             print("    - Info: Shelter already exists in DB. Skipping.")
             return True
        print(f"    - Error adding shelter to database: {e}")
        print("    - Please check your SUPABASE_URL, SUPABASE_KEY, and network connection.")
    return False

def main():
    """
    Main function to discover new shelters. It processes one full municipality per run,
    resuming from the last processed page if the script was interrupted.
    """
    existing_ids = fetch_existing_shelter_ids()
    if existing_ids is None:
        sys.exit("Could not fetch existing shelter IDs. Aborting.")

    kommune_info = None
    # Check for a command-line argument to specify a municipality
    if len(sys.argv) > 1:
        kommune_kode_arg = sys.argv[1]
        print(f"Command-line argument provided. Processing specific municipality: {kommune_kode_arg}")
        kommune_info = fetch_specific_kommune_info(kommune_kode_arg)
    else:
        # If no argument is provided, fetch the next municipality from the database
        kommune_info = fetch_kommune_to_process()

    if kommune_info is None:
        sys.exit("No municipality to process. Aborting.")

    kommune_to_process = kommune_info['kode']
    last_processed_page = kommune_info.get('last_page') or 0
    page = last_processed_page + 1
    total_new_shelters_in_run = 0

    print(f"\nProcessing municipality {kommune_to_process}, starting from page {page}...")
    
    while True:
        params = {
            "username": DATAFORDELER_USERNAME,
            "password": DATAFORDELER_PASSWORD,
            "format": "json",
            "kommunekode": kommune_to_process,
            "page": page
        }
        try:
            print(f"  - Fetching page {page} for municipality {kommune_to_process}...", end='\r')
            r = requests.get(f"{BBR_API_URL}/bygning", params=params)
            r.raise_for_status()
            buildings_on_page = r.json()

            if not buildings_on_page:
                print(f"\n  - Fetching complete for municipality {kommune_to_process}.                       ")
                mark_kommune_as_complete(kommune_to_process)
                break
            
            # Filter the current page for shelters
            shelter_buildings = [
                b for b in buildings_on_page 
                if b.get("status") == "6" and b.get("byg069Sikringsrumpladser", 0) > 0
            ]

            if shelter_buildings:
                print(f"\n  - Found {len(shelter_buildings)} potential shelters on page {page}. Checking against database...")
                for bbr in shelter_buildings:
                    bygning_id = bbr.get("id")

                    if bygning_id and bygning_id not in existing_ids:
                        print(f"    -> New shelter found! ID: {bygning_id}. Processing...")
                        total_new_shelters_in_run += 1
                        
                        husnummer_id = bbr.get("husnummer")
                        dar_data = fetch_dar_data(husnummer_id) if husnummer_id else None
                        
                        new_shelter_payload = {
                            "bygning_id": bygning_id,
                            "shelter_capacity": bbr.get("byg069Sikringsrumpladser"),
                            "anvendelse": bbr.get("byg021BygningensAnvendelse"),
                            "kommunekode": bbr.get("kommunekode"),
                            "address": dar_data.get("adgangsadressebetegnelse") if dar_data else None,
                            "postnummer": dar_data.get("postnummer", {}).get("postnr") if dar_data else None,
                            "vejnavn": dar_data.get("navngivenVej", {}).get("vejnavn") if dar_data else None,
                            "husnummer": dar_data.get("husnummertekst") if dar_data else None,
                            "last_checked": datetime.utcnow().isoformat(),
                        }

                        print(f"      - Adding shelter at address: {new_shelter_payload.get('address') or 'N/A'}")
                        if add_shelter_to_db(new_shelter_payload):
                            print("      - Successfully added to the database.")
                            existing_ids.add(bygning_id)
                        else:
                            print("      - Failed to add to the database.")
            
            # Update progress after successfully processing the page
            update_kommune_progress(kommune_to_process, page)
            page += 1
            time.sleep(0.5) 
        except requests.exceptions.RequestException as e:
            print(f"\n  - Error fetching page {page} for municipality {kommune_to_process}: {e}")
            print("  - Stopping process. The last successfully processed page is saved.")
            break
    
    print(f"\nDiscovery run finished for municipality {kommune_to_process}. Found {total_new_shelters_in_run} new shelters in total during this run.")

if __name__ == "__main__":
    main()

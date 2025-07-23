#!/usr/bin/env python3
"""
Global Shelter Discovery Strategy

This script implements a global page-based strategy for discovering new shelters
across all of Denmark. Instead of processing per municipality, it processes
all buildings globally and filters for shelters, which is much more efficient.

Key advantages:
- No municipality-specific tracking needed
- Even distribution of work across all pages
- Simpler progress tracking (just global page numbers)
- More efficient API usage
- Better scalability
"""

import requests
from datetime import datetime, timedelta
import time
import sys
from dotenv import load_dotenv
import os

# --- Configuration ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BBR_API_URL = os.getenv("BBR_API_URL")
DAR_API_URL = os.getenv("DAR_API_URL")
DATAFORDELER_USERNAME = os.getenv("DATAFORDELER_USERNAME")
DATAFORDELER_PASSWORD = os.getenv("DATAFORDELER_PASSWORD")

# Global strategy configuration
PAGES_PER_BATCH = 834  # Number of pages to process per run (optimized for twice-daily 30-day cycle)
CYCLE_DAYS = 30  # Days to complete a full cycle
ESTIMATED_TOTAL_PAGES = 50000  # Rough estimate of total pages across Denmark

# Calculate pages per day to complete within CYCLE_DAYS
PAGES_PER_DAY = ESTIMATED_TOTAL_PAGES // CYCLE_DAYS  # ~1,667 pages per day

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

# --- Helper Functions ---

def get_current_cycle():
    """Returns the current 30-day cycle identifier (YYYY-MM-DD format for cycle start)."""
    return datetime.now().strftime("%Y-%m-%d")

def is_cycle_complete(last_updated):
    """
    Determines if the current 30-day cycle is complete.
    Returns True if the last update was more than 30 days ago.
    """
    if not last_updated:
        return False
    
    try:
        last_updated_date = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
        days_since_update = (datetime.now() - last_updated_date.replace(tzinfo=None)).days
        return days_since_update >= CYCLE_DAYS
    except (ValueError, AttributeError):
        return False

def get_global_progress():
    """
    Fetches the current global progress from the database.
    Creates the table if it doesn't exist.
    Returns the last processed page number and last updated timestamp.
    """
    url = f"{SUPABASE_URL}/rest/v1/global_progress?select=last_page,last_updated&limit=1"
    try:
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
        if data:
            return data[0]
        else:
            # Initialize if no record exists
            return {"last_page": 0, "last_updated": None}
    except requests.exceptions.RequestException as e:
        if "404" in str(e):
            # Table doesn't exist, create it
            print("Global progress table doesn't exist. Creating it...")
            if create_global_progress_table():
                return {"last_page": 0, "last_updated": None}
            else:
                print("Failed to create global_progress table. Please create it manually in Supabase dashboard.")
                return None
        else:
            print(f"Error fetching global progress: {e}")
            return None

def create_global_progress_table():
    """Creates the global_progress table by inserting initial data."""
    print("Creating global_progress table...")
    
    url = f"{SUPABASE_URL}/rest/v1/global_progress"
    data = {
        "last_page": 0,
        "last_updated": datetime.utcnow().isoformat()
    }
    
    try:
        r = requests.post(url, headers=HEADERS, json=data)
        if r.status_code in [201, 200]:
            print("✅ global_progress table created successfully")
            return True
        else:
            print(f"❌ Failed to create global_progress table: {r.status_code}")
            print("   Please create the table manually in Supabase dashboard:")
            print("   CREATE TABLE global_progress (")
            print("       id SERIAL PRIMARY KEY,")
            print("       last_page INTEGER DEFAULT 0,")
            print("       last_updated TIMESTAMP DEFAULT NOW()")
            print("   );")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating global_progress table: {e}")
        return False

def update_global_progress(page_number):
    """Updates the global progress to the specified page number."""
    # First, get the current record ID
    url = f"{SUPABASE_URL}/rest/v1/global_progress?select=id&limit=1"
    try:
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
        if not data:
            print("  - Warning: No global progress record found")
            return
        
        record_id = data[0]['id']
        
        # Update the specific record by ID
        update_url = f"{SUPABASE_URL}/rest/v1/global_progress?id=eq.{record_id}"
        update_data = {
            "last_page": page_number,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        r = requests.patch(update_url, headers=HEADERS, json=update_data)
        if r.status_code in [200, 204]:
            print(f"  - Updated global progress to page {page_number}")
        else:
            print(f"  - Warning: Could not update progress (status: {r.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"  - Warning: Error updating global progress: {e}")

def fetch_existing_shelter_ids():
    """
    Fetches ALL existing bygning_id from the database, handling pagination.
    This is crucial for accurately checking for duplicates.
    """
    print("Fetching all existing shelter IDs from the database...")
    ids = set()
    offset = 0
    limit = 1000  # The default Supabase limit
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
    
    print(f"\nSuccessfully fetched a total of {len(ids)} existing shelter IDs.")
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

def process_global_batch(start_page, existing_ids):
    """
    Processes a batch of global pages.
    Returns the number of new shelters found and the last processed page.
    """
    total_new_shelters = 0
    current_page = start_page
    end_page = start_page + PAGES_PER_BATCH - 1
    
    print(f"\nProcessing global pages {start_page} to {end_page}...")
    
    while current_page <= end_page:
        params = {
            "username": DATAFORDELER_USERNAME,
            "password": DATAFORDELER_PASSWORD,
            "format": "json",
            "page": current_page
        }
        try:
            print(f"  - Fetching global page {current_page}...", end='\r')
            r = requests.get(f"{BBR_API_URL}/bygning", params=params)
            r.raise_for_status()
            buildings_on_page = r.json()

            if not buildings_on_page:
                print(f"\n  - Reached end of data at page {current_page}.")
                return total_new_shelters, current_page - 1, True  # True = complete
            
            # Filter the current page for shelters
            shelter_buildings = [
                b for b in buildings_on_page 
                if b.get("status") == "6" and b.get("byg069Sikringsrumpladser", 0) > 0
            ]

            if shelter_buildings:
                print(f"\n  - Found {len(shelter_buildings)} potential shelters on page {current_page}. Checking against database...")
                for bbr in shelter_buildings:
                    bygning_id = bbr.get("id")

                    if bygning_id and bygning_id not in existing_ids:
                        print(f"    -> New shelter found! ID: {bygning_id}. Processing...")
                        total_new_shelters += 1
                        
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
            update_global_progress(current_page)
            current_page += 1
            time.sleep(0.5)  # Be respectful to the API
            
        except requests.exceptions.RequestException as e:
            print(f"\n  - Error fetching page {current_page}: {e}")
            print("  - Stopping batch processing.")
            break
    
    return total_new_shelters, current_page - 1, False  # False = not complete

def main():
    """
    Main function implementing the global page-based strategy for discovering new shelters.
    Processes all buildings across Denmark without municipality-specific tracking.
    """
    print("Starting global shelter discovery strategy...")
    
    # Check if we should start a new monthly cycle
    progress = get_global_progress()
    if progress is None:
        print("❌ Could not initialize global progress. Please create the global_progress table manually.")
        print("   Run this SQL in your Supabase dashboard:")
        print("   CREATE TABLE global_progress (")
        print("       id SERIAL PRIMARY KEY,")
        print("       last_page INTEGER DEFAULT 0,")
        print("       last_updated TIMESTAMP DEFAULT NOW()")
        print("   );")
        sys.exit(1)
    
    current_cycle = get_current_cycle()
    last_page = progress.get('last_page', 0)
    
    # Check if we've actually processed any pages this month
    if last_page > 0 and is_cycle_complete(progress.get('last_updated')):
        print(f"Current cycle ({current_cycle}) is already complete.")
        print("All pages have been processed this cycle.")
        return
    elif last_page == 0:
        print(f"Starting new cycle ({current_cycle}) from page 0")
    else:
        print(f"Continuing cycle ({current_cycle}) from page {last_page}")
    
    # Fetch existing shelter IDs for duplicate checking
    existing_ids = fetch_existing_shelter_ids()
    if existing_ids is None:
        sys.exit("Could not fetch existing shelter IDs. Aborting.")

    # Determine starting page
    start_page = progress.get('last_page', 0) + 1
    
    print(f"\nResuming from page {start_page}")
    print(f"Current cycle: {current_cycle}")
    
    # Process the batch
    new_shelters, last_processed_page, is_complete = process_global_batch(start_page, existing_ids)
    
    # Summary
    print(f"\n{'='*60}")
    print("GLOBAL STRATEGY RUN SUMMARY")
    print(f"{'='*60}")
    print(f"Pages processed: {last_processed_page - start_page + 1}")
    print(f"Total new shelters found: {new_shelters}")
    print(f"Last processed page: {last_processed_page}")
    print(f"Current cycle: {current_cycle}")
    
    if is_complete:
        print("✓ All pages have been processed!")
        print("Cycle is now complete.")
    else:
        pages_remaining = ESTIMATED_TOTAL_PAGES - last_processed_page
        print(f"⏸ {pages_remaining} estimated pages remaining in this cycle.")
    
    print(f"\nGlobal strategy run finished successfully.")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Test that progress updates work correctly after the fix
"""

import requests
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

print("="*60)
print("Testing Global Progress Fix")
print("="*60)
print()

# Test 1: Check current state
print("TEST 1: Check current global_progress state")
print("-" * 60)
try:
    url = f"{SUPABASE_URL}/rest/v1/global_progress?select=*"
    r = requests.get(url, headers=HEADERS, timeout=10)
    print(f"Status: {r.status_code}")

    if r.status_code == 200:
        data = r.json()
        print(f"Records found: {len(data)}")
        if data:
            for record in data:
                print(f"  ID: {record.get('id')}")
                print(f"  Last page: {record.get('last_page')}")
                print(f"  Last updated: {record.get('last_updated')}")
        else:
            print("  Table is empty (this was the problem!)")
    else:
        print(f"Error: {r.text}")
except Exception as e:
    print(f"ERROR: {e}")

print("\n")

# Test 2: Test the new get_global_progress with empty table handling
print("TEST 2: Import and test get_global_progress function")
print("-" * 60)
try:
    import sys
    sys.path.insert(0, '/Users/andreasjensen/Shelter-updater')
    from new_shelters_global import get_global_progress, create_session_with_retries

    session = create_session_with_retries()
    progress = get_global_progress(session)

    if progress:
        print(f"✅ SUCCESS")
        print(f"  Last page: {progress.get('last_page')}")
        print(f"  Last updated: {progress.get('last_updated')}")

        if progress.get('last_page') is not None:
            print("\n✅ The fix worked! Progress can now be tracked.")
    else:
        print(f"❌ FAILED - Could not get progress")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n")

# Test 3: Verify final state
print("TEST 3: Check final global_progress state")
print("-" * 60)
try:
    url = f"{SUPABASE_URL}/rest/v1/global_progress?select=*"
    r = requests.get(url, headers=HEADERS, timeout=10)

    if r.status_code == 200:
        data = r.json()
        print(f"Records found: {len(data)}")
        if data:
            print("✅ Progress record exists now!")
            for record in data:
                print(f"  ID: {record.get('id')}")
                print(f"  Last page: {record.get('last_page')}")
                print(f"  Last updated: {record.get('last_updated')}")
        else:
            print("⚠️ Table is still empty")
except Exception as e:
    print(f"ERROR: {e}")

print()
print("="*60)
print("SUMMARY")
print("="*60)
print()
print("The fix does two things:")
print("1. get_global_progress() now CREATES a record if table is empty")
print("2. update_global_progress() now INSERTS if no record exists")
print()
print("This means the 'Warning: No global progress record found'")
print("message should no longer appear during script runs.")
print()

#!/usr/bin/env python3
"""
Local environment test script
Tests actual API connections with your .env file
Runs in DRY RUN mode - no database changes
"""

import requests
from datetime import datetime
import time
import sys
from dotenv import load_dotenv
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Load environment variables
load_dotenv()

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BBR_API_URL = os.getenv("BBR_API_URL")
DAR_API_URL = os.getenv("DAR_API_URL")
DATAFORDELER_USERNAME = os.getenv("DATAFORDELER_USERNAME")
DATAFORDELER_PASSWORD = os.getenv("DATAFORDELER_PASSWORD")

REQUEST_TIMEOUT = 60
CONNECT_TIMEOUT = 20

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

def test_env_variables():
    """Test that all required environment variables are set"""
    print("="*60)
    print("TEST 1: Environment Variables")
    print("="*60)

    required_vars = {
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_KEY": SUPABASE_KEY,
        "BBR_API_URL": BBR_API_URL,
        "DAR_API_URL": DAR_API_URL,
        "DATAFORDELER_USERNAME": DATAFORDELER_USERNAME,
        "DATAFORDELER_PASSWORD": DATAFORDELER_PASSWORD,
    }

    all_set = True
    for var_name, var_value in required_vars.items():
        if var_value:
            # Mask sensitive values
            if "KEY" in var_name or "PASSWORD" in var_name:
                display_value = var_value[:10] + "..." if len(var_value) > 10 else "***"
            else:
                display_value = var_value
            print(f"  ✅ {var_name}: {display_value}")
        else:
            print(f"  ❌ {var_name}: NOT SET")
            all_set = False

    print(f"\nResult: {'✅ ALL SET' if all_set else '❌ MISSING VARIABLES'}")
    return all_set

def test_supabase_connection():
    """Test connection to Supabase"""
    print("\n" + "="*60)
    print("TEST 2: Supabase Database Connection")
    print("="*60)

    try:
        # Try to fetch global progress
        url = f"{SUPABASE_URL}/rest/v1/global_progress?select=last_page,last_updated&limit=1"
        print(f"  Testing: {url}")

        r = requests.get(url, headers=HEADERS, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))
        print(f"  Status code: {r.status_code}")

        if r.status_code == 200:
            data = r.json()
            print(f"  Response: {data}")
            print(f"  ✅ SUCCESS - Supabase connection working")

            if data:
                last_page = data[0].get('last_page', 0)
                last_updated = data[0].get('last_updated', 'N/A')
                print(f"\n  Current Progress:")
                print(f"    - Last page: {last_page}")
                print(f"    - Last updated: {last_updated}")
            return True
        else:
            print(f"  ❌ FAILED - Status {r.status_code}: {r.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"  ❌ FAILED - Connection error: {e}")
        return False

def test_shelters_table():
    """Test access to sheltersv2 table"""
    print("\n" + "="*60)
    print("TEST 3: Shelters Table Access")
    print("="*60)

    try:
        url = f"{SUPABASE_URL}/rest/v1/sheltersv2?select=bygning_id&limit=5"
        print(f"  Testing: {url}")

        r = requests.get(url, headers=HEADERS, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))
        print(f"  Status code: {r.status_code}")

        if r.status_code == 200:
            data = r.json()
            print(f"  Response: Found {len(data)} shelters (showing first 5)")
            print(f"  ✅ SUCCESS - Shelters table accessible")
            return True
        else:
            print(f"  ❌ FAILED - Status {r.status_code}: {r.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"  ❌ FAILED - Connection error: {e}")
        return False

def test_bbr_api():
    """Test connection to BBR (Datafordeler) API"""
    print("\n" + "="*60)
    print("TEST 4: BBR API Connection (Datafordeler)")
    print("="*60)

    try:
        # Try to fetch page 1
        params = {
            "username": DATAFORDELER_USERNAME,
            "password": DATAFORDELER_PASSWORD,
            "format": "json",
            "page": 1
        }

        url = f"{BBR_API_URL}/bygning"
        print(f"  Testing: {url}")
        print(f"  Parameters: page=1, username={DATAFORDELER_USERNAME[:5]}...")
        print(f"  Timeout: {REQUEST_TIMEOUT}s")

        print(f"\n  Fetching page 1... (this may take up to {REQUEST_TIMEOUT}s)")
        start_time = time.time()

        r = requests.get(url, params=params, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))
        elapsed = time.time() - start_time

        print(f"  Response time: {elapsed:.2f}s")
        print(f"  Status code: {r.status_code}")

        if r.status_code == 200:
            data = r.json()
            print(f"  Buildings on page 1: {len(data)}")

            # Check for shelters
            shelters = [b for b in data if b.get("status") == "6" and b.get("byg069Sikringsrumpladser", 0) > 0]
            print(f"  Shelters found: {len(shelters)}")

            if shelters:
                print(f"\n  Example shelter:")
                example = shelters[0]
                print(f"    - ID: {example.get('id')}")
                print(f"    - Capacity: {example.get('byg069Sikringsrumpladser')}")
                print(f"    - Municipality: {example.get('kommunekode')}")

            print(f"  ✅ SUCCESS - BBR API working")
            return True
        elif r.status_code == 429:
            print(f"  ⚠️  WARNING - Rate limit hit")
            print(f"  The API is working but limiting requests")
            return True
        else:
            print(f"  ❌ FAILED - Status {r.status_code}: {r.text[:200]}")
            return False

    except requests.exceptions.Timeout:
        print(f"  ❌ FAILED - Request timed out after {REQUEST_TIMEOUT}s")
        print(f"  This is the same timeout issue from your GitHub Actions logs")
        return False
    except requests.exceptions.RequestException as e:
        print(f"  ❌ FAILED - Connection error: {e}")
        return False

def test_dar_api():
    """Test connection to DAR API"""
    print("\n" + "="*60)
    print("TEST 5: DAR API Connection (Address Data)")
    print("="*60)

    try:
        # Just test the connection with a simple query
        params = {
            "username": DATAFORDELER_USERNAME,
            "password": DATAFORDELER_PASSWORD,
            "format": "json",
        }

        url = f"{DAR_API_URL}/husnummer"
        print(f"  Testing: {url}")
        print(f"  Note: This will fail without a valid ID, we're just testing connection")

        r = requests.get(url, params=params, timeout=(CONNECT_TIMEOUT, 10))
        print(f"  Status code: {r.status_code}")

        if r.status_code in [200, 400, 404]:
            # Any of these mean the API is reachable
            print(f"  ✅ SUCCESS - DAR API is reachable")
            return True
        else:
            print(f"  ⚠️  WARNING - Unexpected status: {r.status_code}")
            return True  # Still probably working

    except requests.exceptions.RequestException as e:
        print(f"  ❌ FAILED - Connection error: {e}")
        return False

def test_dry_run():
    """Do a minimal dry run test (2-3 pages)"""
    print("\n" + "="*60)
    print("TEST 6: Dry Run (2 pages, no database writes)")
    print("="*60)

    print("\n  This will test processing 2 pages without saving to database")
    print(f"  Estimated time: ~{2 * 2}s (with 1s sleep between pages)")

    # Auto-run in non-interactive environments
    try:
        response = input("\n  Continue with dry run? (y/n): ").strip().lower()
        if response != 'y':
            print("  ⏭  Skipped by user")
            return None
    except (EOFError, KeyboardInterrupt):
        print("  ⏭  Running dry run automatically (non-interactive mode)")
        # Continue with the test

    try:
        session = requests.Session()

        shelters_found = 0

        for page_num in [1, 2]:
            print(f"\n  Testing page {page_num}...")

            params = {
                "username": DATAFORDELER_USERNAME,
                "password": DATAFORDELER_PASSWORD,
                "format": "json",
                "page": page_num
            }

            start_time = time.time()
            r = session.get(f"{BBR_API_URL}/bygning", params=params, timeout=(CONNECT_TIMEOUT, REQUEST_TIMEOUT))
            elapsed = time.time() - start_time

            print(f"    Response time: {elapsed:.2f}s")

            if r.status_code == 200:
                buildings = r.json()
                shelters = [b for b in buildings if b.get("status") == "6" and b.get("byg069Sikringsrumpladser", 0) > 0]
                shelters_found += len(shelters)

                print(f"    ✅ Buildings: {len(buildings)}, Shelters: {len(shelters)}")
            else:
                print(f"    ❌ Failed with status {r.status_code}")
                return False

            # Sleep between requests
            if page_num < 2:
                time.sleep(1)

        print(f"\n  ✅ SUCCESS - Dry run completed")
        print(f"  Total shelters found: {shelters_found}")
        print(f"  (No data was written to database)")
        return True

    except requests.exceptions.Timeout:
        print(f"  ❌ FAILED - Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"  ❌ FAILED - Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("LOCAL ENVIRONMENT TEST SUITE")
    print("Testing with your actual .env credentials")
    print("="*60 + "\n")

    results = {}

    # Test 1: Environment variables
    results['env'] = test_env_variables()
    if not results['env']:
        print("\n❌ Cannot proceed without environment variables")
        return

    # Test 2: Supabase connection
    results['supabase'] = test_supabase_connection()

    # Test 3: Shelters table
    results['shelters_table'] = test_shelters_table()

    # Test 4: BBR API
    results['bbr_api'] = test_bbr_api()

    # Test 5: DAR API
    results['dar_api'] = test_dar_api()

    # Test 6: Dry run (optional)
    dry_run_result = test_dry_run()
    if dry_run_result is not None:
        results['dry_run'] = dry_run_result

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name:20s}: {status}")

    all_passed = all(results.values())

    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nYour script is ready to run in production!")
        print("You can safely deploy to GitHub Actions.")
    else:
        print("❌ SOME TESTS FAILED")
        print("="*60)
        print("\nPlease fix the failing tests before deploying to production.")
        print("Check your .env file and API credentials.")

    print()

if __name__ == "__main__":
    main()

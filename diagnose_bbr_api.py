#!/usr/bin/env python3
"""
Diagnose BBR API connection issues
Tests different endpoints, parameters, and encoding methods
"""

import requests
from dotenv import load_dotenv
import os
from urllib.parse import quote, urlencode

load_dotenv()

USERNAME = os.getenv('DATAFORDELER_USERNAME')
PASSWORD = os.getenv('DATAFORDELER_PASSWORD')
BBR_API_URL = os.getenv('BBR_API_URL')

print("="*60)
print("BBR API DIAGNOSTIC TOOL")
print("="*60)
print(f"\nUsername: {USERNAME}")
print(f"Password: {PASSWORD}")
print(f"API URL: {BBR_API_URL}")
print()

# Test 1: Simple connection test (no page parameter)
print("TEST 1: Basic connection (no page parameter)")
print("-" * 60)
try:
    params = {
        'username': USERNAME,
        'password': PASSWORD,
        'format': 'json'
    }

    url = f"{BBR_API_URL}/bygning"
    print(f"URL: {url}")
    print(f"Params: {params}")

    r = requests.get(url, params=params, timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Response length: {len(r.text)}")
    print(f"First 200 chars: {r.text[:200]}")

    if r.status_code == 200:
        print("✅ SUCCESS - Basic connection works!")
        data = r.json()
        print(f"Records returned: {len(data) if isinstance(data, list) else 'N/A'}")
    else:
        print(f"❌ FAILED - Status {r.status_code}")
except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n")

# Test 2: With page=0
print("TEST 2: With page=0")
print("-" * 60)
try:
    params = {
        'username': USERNAME,
        'password': PASSWORD,
        'format': 'json',
        'page': 0
    }

    url = f"{BBR_API_URL}/bygning"
    print(f"URL: {url}")
    print(f"Params: {params}")

    r = requests.get(url, params=params, timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Response length: {len(r.text)}")
    print(f"First 200 chars: {r.text[:200]}")

    if r.status_code == 200:
        print("✅ SUCCESS - page=0 works!")
        data = r.json()
        print(f"Records returned: {len(data) if isinstance(data, list) else 'N/A'}")
    else:
        print(f"❌ FAILED - Status {r.status_code}")
except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n")

# Test 3: With page=1 (URL encoded password)
print("TEST 3: With page=1 (URL encoded password)")
print("-" * 60)
try:
    # URL encode the password to handle special characters
    params = {
        'username': USERNAME,
        'password': PASSWORD,  # requests library will encode this automatically
        'format': 'json',
        'page': 1
    }

    url = f"{BBR_API_URL}/bygning"
    print(f"URL: {url}")
    print(f"Params (before encoding): {params}")
    print(f"Password URL encoded: {quote(PASSWORD)}")

    r = requests.get(url, params=params, timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Response length: {len(r.text)}")
    print(f"First 500 chars: {r.text[:500]}")

    if r.status_code == 200:
        print("✅ SUCCESS - page=1 works!")
        data = r.json()
        print(f"Records returned: {len(data) if isinstance(data, list) else 'N/A'}")

        # Check for shelters
        if isinstance(data, list) and len(data) > 0:
            shelters = [b for b in data if b.get("status") == "6" and b.get("byg069Sikringsrumpladser", 0) > 0]
            print(f"Shelters found: {len(shelters)}")
    else:
        print(f"❌ FAILED - Status {r.status_code}")
except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n")

# Test 4: Manual URL construction
print("TEST 4: Manual URL construction with encoded password")
print("-" * 60)
try:
    # Build URL manually with proper encoding
    encoded_params = urlencode({
        'username': USERNAME,
        'password': PASSWORD,
        'format': 'json',
        'page': 1
    })

    full_url = f"{BBR_API_URL}/bygning?{encoded_params}"
    print(f"Full URL (password masked):")
    print(f"{full_url.replace(PASSWORD, '***')}")

    r = requests.get(full_url, timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Response length: {len(r.text)}")
    print(f"First 500 chars: {r.text[:500]}")

    if r.status_code == 200:
        print("✅ SUCCESS - Manual URL construction works!")
        data = r.json()
        print(f"Records returned: {len(data) if isinstance(data, list) else 'N/A'}")
    else:
        print(f"❌ FAILED - Status {r.status_code}")
except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n")

# Test 5: Try with per parameter (which might be the correct param name)
print("TEST 5: Try with 'per' parameter instead of 'page'")
print("-" * 60)
try:
    params = {
        'username': USERNAME,
        'password': PASSWORD,
        'format': 'json',
        'per': 1
    }

    url = f"{BBR_API_URL}/bygning"
    print(f"URL: {url}")
    print(f"Params: {params}")

    r = requests.get(url, params=params, timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Response length: {len(r.text)}")
    print(f"First 200 chars: {r.text[:200]}")

    if r.status_code == 200:
        print("✅ SUCCESS - 'per' parameter works!")
        data = r.json()
        print(f"Records returned: {len(data) if isinstance(data, list) else 'N/A'}")
    else:
        print(f"❌ FAILED - Status {r.status_code}")
except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n")

# Test 6: Check response headers for clues
print("TEST 6: Detailed response headers analysis")
print("-" * 60)
try:
    params = {
        'username': USERNAME,
        'password': PASSWORD,
        'format': 'json',
        'page': 1
    }

    url = f"{BBR_API_URL}/bygning"

    r = requests.get(url, params=params, timeout=30)
    print(f"Status: {r.status_code}")
    print(f"\nResponse Headers:")
    for key, value in r.headers.items():
        print(f"  {key}: {value}")

    print(f"\nFull response text:")
    print(r.text)

except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n")
print("="*60)
print("DIAGNOSTIC COMPLETE")
print("="*60)

#!/usr/bin/env python3
"""
Test BBR API with different authentication methods
"""

import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import os

load_dotenv()

USERNAME = os.getenv('DATAFORDELER_USERNAME')
PASSWORD = os.getenv('DATAFORDELER_PASSWORD')
BBR_API_URL = os.getenv('BBR_API_URL')

print("="*60)
print("BBR API AUTHENTICATION TESTS")
print("="*60)
print(f"\nUsername: {USERNAME}")
print(f"Password: {PASSWORD}")
print()

# Test 1: Query parameters (current method)
print("TEST 1: Query Parameters (current method)")
print("-" * 60)
try:
    params = {
        'username': USERNAME,
        'password': PASSWORD,
        'format': 'json',
        'page': 1
    }

    r = requests.get(f"{BBR_API_URL}/bygning", params=params, timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:200]}")
except Exception as e:
    print(f"ERROR: {e}")

print("\n")

# Test 2: HTTP Basic Auth
print("TEST 2: HTTP Basic Authentication")
print("-" * 60)
try:
    params = {
        'format': 'json',
        'page': 1
    }

    r = requests.get(
        f"{BBR_API_URL}/bygning",
        params=params,
        auth=HTTPBasicAuth(USERNAME, PASSWORD),
        timeout=30
    )
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:200]}")

    if r.status_code == 200:
        print("✅ SUCCESS with Basic Auth!")
        data = r.json()
        print(f"Records: {len(data)}")
    else:
        print("❌ FAILED")
except Exception as e:
    print(f"ERROR: {e}")

print("\n")

# Test 3: Check if credentials are valid with a simpler endpoint
print("TEST 3: Test credentials with /status or simpler endpoint")
print("-" * 60)
try:
    # Try the base URL
    r = requests.get(
        BBR_API_URL,
        auth=HTTPBasicAuth(USERNAME, PASSWORD),
        timeout=30
    )
    print(f"Base URL status: {r.status_code}")
    print(f"Response: {r.text[:200]}")
except Exception as e:
    print(f"ERROR: {e}")

print("\n")

# Test 4: Check what GitHub Actions is using
print("TEST 4: Check GitHub Actions workflow file")
print("-" * 60)
try:
    with open('.github/workflows/shelter_updater.yml', 'r') as f:
        content = f.read()
        if 'DATAFORDELER_USERNAME' in content:
            print("✅ Found DATAFORDELER_USERNAME in workflow")
        if 'DATAFORDELER_PASSWORD' in content:
            print("✅ Found DATAFORDELER_PASSWORD in workflow")

        # Extract the relevant section
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'DATAFORDELER' in line:
                print(f"  Line {i+1}: {line}")
except Exception as e:
    print(f"ERROR: {e}")

print("\n")
print("="*60)
print("RECOMMENDATION")
print("="*60)
print()
print("The API is consistently returning 500 errors.")
print("This suggests one of the following:")
print()
print("1. ❌ Credentials are incorrect/expired")
print("   → Double-check against GitHub Secrets")
print()
print("2. ⚠️  API is down/having issues")
print("   → Check https://datafordeler.dk for status")
print()
print("3. 🔒 IP-based restrictions")
print("   → API works from GitHub Actions but not locally")
print()
print("4. 📝 Different credentials for local vs GitHub")
print("   → GitHub Secrets might have different values")
print()

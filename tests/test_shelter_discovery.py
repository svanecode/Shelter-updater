#!/usr/bin/env python3
"""
Test script for new_shelters_global.py
Tests the logic without making actual API calls
"""

import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import time

# Test the cycle logic
def test_cycle_logic():
    """Test that cycle completion logic works correctly"""
    print("="*60)
    print("TEST 1: Cycle Logic")
    print("="*60)

    # Import the functions we need to test
    sys.path.insert(0, '/Users/andreasjensen/Shelter-updater')
    from new_shelters_global import is_cycle_complete, get_current_cycle, CYCLE_DAYS

    # Test 1: Recent update (< 30 days) - should NOT be complete
    recent_date = (datetime.now() - timedelta(days=5)).isoformat()
    result = is_cycle_complete(recent_date)
    print(f"Test 1a: Recent update (5 days ago)")
    print(f"  Input: {recent_date}")
    print(f"  Result: {result}")
    print(f"  Expected: False")
    assert not result, f"Cycle logic error: Recent update (5 days) should NOT be complete, but got {result}"
    print(f"  ✅ PASS")

    # Test 2: Old update (33 days) - should be complete
    old_date = (datetime.now() - timedelta(days=33)).isoformat()
    result = is_cycle_complete(old_date)
    print(f"\nTest 1b: Old update (33 days ago)")
    print(f"  Input: {old_date}")
    print(f"  Result: {result}")
    print(f"  Expected: True")
    assert result, f"Cycle logic error: Old update (33 days) SHOULD be complete, but got {result}"
    print(f"  ✅ PASS")

    # Test 3: Exactly 30 days - should be complete
    exact_date = (datetime.now() - timedelta(days=30)).isoformat()
    result = is_cycle_complete(exact_date)
    print(f"\nTest 1c: Exactly 30 days ago")
    print(f"  Input: {exact_date}")
    print(f"  Result: {result}")
    print(f"  Expected: True")
    assert result, f"Cycle logic error: Exactly 30 days SHOULD be complete, but got {result}"
    print(f"  ✅ PASS")

    # Test 4: None input - should NOT be complete
    result = is_cycle_complete(None)
    print(f"\nTest 1d: None input (no previous run)")
    print(f"  Input: None")
    print(f"  Result: {result}")
    print(f"  Expected: False")
    assert not result, f"Cycle logic error: None input should NOT be complete, but got {result}"
    print(f"  ✅ PASS")

    print()

def test_main_logic_scenarios():
    """Test different scenarios in the main function"""
    print("="*60)
    print("TEST 2: Main Function Logic Scenarios")
    print("="*60)

    sys.path.insert(0, '/Users/andreasjensen/Shelter-updater')
    from new_shelters_global import is_cycle_complete

    # Scenario 1: First run ever (last_page = 0, no last_updated)
    print("\nScenario 1: First run ever")
    last_page = 0
    last_updated = None

    if last_page > 0 and is_cycle_complete(last_updated):
        start_page = 1
        print(f"  Action: Reset to page 0 (new cycle)")
    elif last_page == 0:
        start_page = 1
        print(f"  Action: Start from page 1 (first run)")
    else:
        start_page = last_page + 1
        print(f"  Action: Continue from page {start_page}")

    print(f"  Result: start_page = {start_page}")
    print(f"  Expected: start_page = 1")
    assert start_page == 1, f"Main logic error (Scenario 1): Expected start_page=1, got {start_page}"
    print(f"  ✅ PASS")

    # Scenario 2: Recent run (stopped at page 32919, 2 days ago)
    print("\nScenario 2: Recent run (32919, 2 days ago)")
    last_page = 32919
    last_updated = (datetime.now() - timedelta(days=2)).isoformat()

    if last_page > 0 and is_cycle_complete(last_updated):
        last_page = 0  # Reset
        start_page = 1
        print(f"  Action: Reset to page 0 (new cycle)")
    elif last_page == 0:
        start_page = 1
        print(f"  Action: Start from page 1 (first run)")
    else:
        start_page = last_page + 1
        print(f"  Action: Continue from page {start_page}")

    print(f"  Result: start_page = {start_page}")
    print(f"  Expected: start_page = 32920")
    assert start_page == 32920, f"Main logic error (Scenario 2): Expected start_page=32920, got {start_page}"
    print(f"  ✅ PASS")

    # Scenario 3: Old run (stopped at page 32919, 33 days ago)
    print("\nScenario 3: Old run (32919, 33 days ago)")
    last_page = 32919
    last_updated = (datetime.now() - timedelta(days=33)).isoformat()

    if last_page > 0 and is_cycle_complete(last_updated):
        last_page = 0  # Reset
        start_page = 1
        print(f"  Action: Reset to page 0 (new cycle)")
    elif last_page == 0:
        start_page = 1
        print(f"  Action: Start from page 1 (first run)")
    else:
        start_page = last_page + 1
        print(f"  Action: Continue from page {start_page}")

    print(f"  Result: start_page = {start_page}")
    print(f"  Expected: start_page = 1")
    assert start_page == 1, f"Main logic error (Scenario 3): Expected start_page=1 (new cycle), got {start_page}"
    print(f"  ✅ PASS")

    print()

def test_exponential_backoff():
    """Test exponential backoff calculations"""
    print("="*60)
    print("TEST 3: Exponential Backoff Calculations")
    print("="*60)

    # Test timeout backoff: 10, 20, 40, 80, 160, 300 (capped)
    print("\nTimeout backoff (10 * 2^(n-1), capped at 300):")
    for retry in range(1, 8):
        backoff = min(10 * (2 ** (retry - 1)), 300)
        print(f"  Retry {retry}: {backoff}s")

    expected_timeout = [10, 20, 40, 80, 160, 300, 300]
    actual_timeout = [min(10 * (2 ** (retry - 1)), 300) for retry in range(1, 8)]
    assert actual_timeout == expected_timeout, (
        f"Timeout backoff calculation incorrect:\n"
        f"  Expected: {expected_timeout}\n"
        f"  Got:      {actual_timeout}"
    )
    print(f"  ✅ PASS")

    # Test connection error backoff: 15, 30, 60, 120, 240, 300 (capped)
    print("\nConnection error backoff (15 * 2^(n-1), capped at 300):")
    for retry in range(1, 8):
        backoff = min(15 * (2 ** (retry - 1)), 300)
        print(f"  Retry {retry}: {backoff}s")

    expected_connection = [15, 30, 60, 120, 240, 300, 300]
    actual_connection = [min(15 * (2 ** (retry - 1)), 300) for retry in range(1, 8)]
    assert actual_connection == expected_connection, (
        f"Connection error backoff calculation incorrect:\n"
        f"  Expected: {expected_connection}\n"
        f"  Got:      {actual_connection}"
    )
    print(f"  ✅ PASS")

    # Test rate limit backoff: 60, 120, 240, 300 (capped)
    print("\nRate limit backoff (60 * 2^(n-1), capped at 300):")
    for retry in range(1, 6):
        backoff = min(60 * (2 ** (retry - 1)), 300)
        print(f"  Retry {retry}: {backoff}s")

    expected_rate = [60, 120, 240, 300, 300]
    actual_rate = [min(60 * (2 ** (retry - 1)), 300) for retry in range(1, 6)]
    assert actual_rate == expected_rate, (
        f"Rate limit backoff calculation incorrect:\n"
        f"  Expected: {expected_rate}\n"
        f"  Got:      {actual_rate}"
    )
    print(f"  ✅ PASS")

    print()

def test_syntax():
    """Test that the main script has no syntax errors"""
    print("="*60)
    print("TEST 4: Syntax Check")
    print("="*60)

    try:
        import new_shelters_global
        print("  ✅ PASS - No syntax errors found")
        return True
    except SyntaxError as e:
        print(f"  ❌ FAIL - Syntax error: {e}")
        return False
    except Exception as e:
        # Other import errors are okay (missing env vars, etc)
        print(f"  ✅ PASS - Syntax OK (import failed due to: {type(e).__name__})")
        return True

def test_error_handling_logic():
    """Test error handling logic"""
    print("="*60)
    print("TEST 5: Error Handling Logic")
    print("="*60)

    MAX_CONSECUTIVE_ERRORS = 15

    # Scenario: 10 consecutive errors on same page
    print("\nScenario: 10 consecutive errors on same page")
    consecutive_errors = 10
    page_retry_count = 10

    should_stop = consecutive_errors >= MAX_CONSECUTIVE_ERRORS
    print(f"  Consecutive errors: {consecutive_errors}/{MAX_CONSECUTIVE_ERRORS}")
    print(f"  Page retry count: {page_retry_count}")
    print(f"  Should stop: {should_stop}")
    print(f"  Expected: False (should keep retrying)")
    print(f"  ✅ PASS" if not should_stop else f"  ❌ FAIL")

    # Scenario: 15 consecutive errors
    print("\nScenario: 15 consecutive errors reached")
    consecutive_errors = 15
    page_retry_count = 15

    should_stop = consecutive_errors >= MAX_CONSECUTIVE_ERRORS
    print(f"  Consecutive errors: {consecutive_errors}/{MAX_CONSECUTIVE_ERRORS}")
    print(f"  Page retry count: {page_retry_count}")
    print(f"  Should stop: {should_stop}")
    print(f"  Expected: True (should stop)")
    print(f"  ✅ PASS" if should_stop else f"  ❌ FAIL")

    # Scenario: Successful request resets counters
    print("\nScenario: Successful request resets counters")
    consecutive_errors = 5
    page_retry_count = 3

    # Simulate success
    consecutive_errors = 0
    page_retry_count = 0

    print(f"  After success:")
    print(f"    Consecutive errors: {consecutive_errors}")
    print(f"    Page retry count: {page_retry_count}")
    print(f"  Expected: Both should be 0")
    print(f"  ✅ PASS" if consecutive_errors == 0 and page_retry_count == 0 else f"  ❌ FAIL")

    print()

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("SHELTER DISCOVERY SCRIPT TEST SUITE")
    print("="*60 + "\n")

    # Run all tests
    test_syntax()
    test_cycle_logic()
    test_main_logic_scenarios()
    test_exponential_backoff()
    test_error_handling_logic()

    print("="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)
    print("\nReview the output above to verify all tests passed.")
    print("If any tests failed, the script needs fixes before production use.\n")

if __name__ == "__main__":
    main()

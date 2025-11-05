#!/usr/bin/env python3
"""
Global Strategy Progress Monitor

This script provides a comprehensive view of the current status of the global
shelter discovery strategy. It shows progress across all pages rather than
per municipality.
"""

import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

# Configuration
ESTIMATED_TOTAL_PAGES = 50000
PAGES_PER_BATCH = 278  # Pages per run (matching new_shelters_global.py)
RUNS_PER_DAY = 3  # Number of runs per day
CYCLE_DAYS = 30  # Days to complete a full cycle

def get_current_cycle():
    """Returns the current 30-day cycle identifier."""
    return datetime.now().strftime("%Y-%m-%d")

def is_cycle_complete(last_updated):
    """Determines if the current 30-day cycle is complete."""
    if not last_updated:
        return False
    
    try:
        last_updated_date = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
        days_since_update = (datetime.now() - last_updated_date.replace(tzinfo=None)).days
        return days_since_update >= CYCLE_DAYS
    except (ValueError, AttributeError):
        return False

def fetch_global_progress():
    """Fetches the current global progress from the database."""
    url = f"{SUPABASE_URL}/rest/v1/global_progress?select=last_page,last_updated&limit=1"
    try:
        r = requests.get(url, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
        if data:
            return data[0]
        else:
            return {"last_page": 0, "last_updated": None}
    except requests.exceptions.RequestException as e:
        if "404" in str(e):
            print("Global progress table doesn't exist yet.")
            print("Run 'python new_shelters_global.py' to create it automatically.")
            return None
        else:
            print(f"Error fetching global progress: {e}")
            return None

def calculate_progress_stats(progress):
    """Calculates various progress statistics."""
    current_cycle = get_current_cycle()
    last_page = progress.get('last_page', 0)
    last_updated = progress.get('last_updated')
    
    # Calculate completion percentage
    completion_percentage = (last_page / ESTIMATED_TOTAL_PAGES * 100) if ESTIMATED_TOTAL_PAGES > 0 else 0
    
    # Calculate pages remaining
    pages_remaining = max(0, ESTIMATED_TOTAL_PAGES - last_page)
    
    # Determine cycle status - if we're at page 0, we haven't started
    # If we've processed some pages, we're in progress
    cycle_complete = False
    if last_page == 0:
        cycle_complete = False  # Haven't started
    elif last_page >= ESTIMATED_TOTAL_PAGES:
        cycle_complete = True   # Completed all pages
    else:
        cycle_complete = False  # In progress
    
    # Calculate time since last update
    time_since_update = None
    if last_updated:
        try:
            last_date = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            time_since_update = datetime.now() - last_date.replace(tzinfo=None)
        except:
            pass
    
    return {
        'current_cycle': current_cycle,
        'last_page': last_page,
        'completion_percentage': completion_percentage,
        'pages_remaining': pages_remaining,
        'cycle_complete': cycle_complete,
        'time_since_update': time_since_update,
        'last_updated': last_updated
    }

def print_progress_report(stats):
    """Prints a comprehensive progress report."""
    print(f"\n{'='*80}")
    print(f"GLOBAL STRATEGY PROGRESS REPORT - {stats['current_cycle']}")
    print(f"{'='*80}")
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"   Current cycle: {stats['current_cycle']}")
    print(f"   Last processed page: {stats['last_page']:,}")
    print(f"   Estimated total pages: {ESTIMATED_TOTAL_PAGES:,}")
    print(f"   Pages remaining: {stats['pages_remaining']:,}")
    print(f"   Completion: {stats['completion_percentage']:.1f}%")
    
    # Cycle Status
    if stats['cycle_complete']:
        print(f"   Cycle status: ✅ COMPLETE")
    else:
        print(f"   Cycle status: ⏸ IN PROGRESS")
    
    # Time Information
    if stats['time_since_update']:
        days_ago = stats['time_since_update'].days
        hours_ago = stats['time_since_update'].total_seconds() / 3600
        
        if days_ago > 0:
            print(f"   Last update: {days_ago} days ago")
        else:
            print(f"   Last update: {hours_ago:.1f} hours ago")
    else:
        print(f"   Last update: Never")
    
    # Progress Bar
    print(f"\n📈 PROGRESS:")
    bar_length = 50
    filled_length = int(bar_length * stats['completion_percentage'] / 100)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    print(f"   [{bar}] {stats['completion_percentage']:.1f}%")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if stats['cycle_complete']:
        print(f"   • Cycle is complete! All pages processed.")
        print(f"   • Ready for next cycle.")
    else:
        if stats['pages_remaining'] > 0:
            print(f"   • {stats['pages_remaining']:,} pages remaining in this cycle")

            # Estimate completion time
            pages_per_day = PAGES_PER_BATCH * RUNS_PER_DAY
            days_to_complete = stats['pages_remaining'] / pages_per_day
            print(f"   • Estimated {days_to_complete:.1f} days to complete at current rate ({pages_per_day:,} pages/day)")

            print(f"   • Continue running the global strategy to complete the cycle")
        else:
            print(f"   • All estimated pages have been processed")
            print(f"   • Consider increasing ESTIMATED_TOTAL_PAGES if more data exists")
    
    if stats['time_since_update'] and stats['time_since_update'].days > 7:
        print(f"   • ⚠️  No updates in {stats['time_since_update'].days} days - check if script is running")
    
    # Performance Tips
    print(f"\n🚀 PERFORMANCE TIPS:")
    print(f"   • Currently running {RUNS_PER_DAY}x daily to process {PAGES_PER_BATCH * RUNS_PER_DAY:,} pages per day")
    print(f"   • Each run processes {PAGES_PER_BATCH} pages with 3-second intervals between requests")
    print(f"   • With {ESTIMATED_TOTAL_PAGES:,} total pages, aim for ~{ESTIMATED_TOTAL_PAGES//CYCLE_DAYS:,} pages per day")
    print(f"   • Adjust PAGES_PER_BATCH in new_shelters_global.py if needed")
    
    print(f"\n{'='*80}")

def main():
    """Main function to run the global progress monitoring report."""
    print("Fetching global progress...")
    
    progress = fetch_global_progress()
    if progress is None:
        print("Failed to fetch global progress. Check your database connection.")
        return
    
    stats = calculate_progress_stats(progress)
    print_progress_report(stats)

if __name__ == "__main__":
    main() 
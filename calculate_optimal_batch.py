#!/usr/bin/env python3
"""
Calculate Optimal Batch Size for 30-Day Completion

This script calculates the optimal batch size and processing frequency
to complete all pages within a 30-day cycle.
"""

# Configuration
ESTIMATED_TOTAL_PAGES = 50000
CYCLE_DAYS = 30

def calculate_optimal_batch():
    """Calculate optimal batch size and processing frequency."""
    
    print("=" * 60)
    print("OPTIMAL BATCH SIZE CALCULATOR")
    print("=" * 60)
    
    # Calculate required pages per day
    pages_per_day = ESTIMATED_TOTAL_PAGES / CYCLE_DAYS
    print(f"\n📊 REQUIREMENTS:")
    print(f"   Total pages: {ESTIMATED_TOTAL_PAGES:,}")
    print(f"   Cycle days: {CYCLE_DAYS}")
    print(f"   Required pages per day: {pages_per_day:.1f}")
    
    # Different processing frequencies
    frequencies = [
        ("Daily", 1),
        ("Twice daily", 2),
        ("Every 6 hours", 4),
        ("Every 4 hours", 6),
        ("Every 2 hours", 12),
        ("Hourly", 24)
    ]
    
    print(f"\n📈 BATCH SIZE CALCULATIONS:")
    print(f"{'Frequency':<15} {'Runs/Day':<10} {'Pages/Run':<12} {'Total/Day':<12}")
    print("-" * 50)
    
    for freq_name, runs_per_day in frequencies:
        pages_per_run = pages_per_day / runs_per_day
        total_per_day = pages_per_run * runs_per_day
        print(f"{freq_name:<15} {runs_per_day:<10} {pages_per_run:<12.1f} {total_per_day:<12.1f}")
    
    # Recommended configurations
    print(f"\n💡 RECOMMENDED CONFIGURATIONS:")
    
    # Option 1: Daily processing with larger batch
    daily_batch = int(pages_per_day)
    print(f"1. Daily Processing:")
    print(f"   • Frequency: Once per day")
    print(f"   • Batch size: {daily_batch:,} pages")
    print(f"   • GitHub Actions: cron: '0 2 * * *'")
    print(f"   • Completion time: {ESTIMATED_TOTAL_PAGES / daily_batch:.1f} days")
    
    # Option 2: Twice daily with medium batch
    twice_daily_batch = int(pages_per_day / 2)
    print(f"\n2. Twice Daily Processing:")
    print(f"   • Frequency: Twice per day")
    print(f"   • Batch size: {twice_daily_batch:,} pages")
    print(f"   • GitHub Actions: cron: '0 2,14 * * *'")
    print(f"   • Completion time: {ESTIMATED_TOTAL_PAGES / (twice_daily_batch * 2):.1f} days")
    
    # Option 3: Every 6 hours with smaller batch
    six_hour_batch = int(pages_per_day / 4)
    print(f"\n3. Every 6 Hours Processing:")
    print(f"   • Frequency: 4 times per day")
    print(f"   • Batch size: {six_hour_batch:,} pages")
    print(f"   • GitHub Actions: cron: '0 */6 * * *'")
    print(f"   • Completion time: {ESTIMATED_TOTAL_PAGES / (six_hour_batch * 4):.1f} days")
    
    # Current configuration analysis
    current_batch = 834  # Updated for twice-daily processing
    current_runs_per_day = 2  # Twice daily
    current_completion_days = ESTIMATED_TOTAL_PAGES / (current_batch * current_runs_per_day)
    
    print(f"\n⚠️  CURRENT CONFIGURATION ANALYSIS:")
    print(f"   • Current batch size: {current_batch:,} pages")
    print(f"   • Current runs per day: {current_runs_per_day}")
    print(f"   • Estimated completion: {current_completion_days:.1f} days")
    print(f"   • Status: {'❌ Too slow' if current_completion_days > CYCLE_DAYS else '✅ On track'}")
    
    if current_completion_days > CYCLE_DAYS:
        print(f"   • Recommendation: Increase batch size to {daily_batch:,} pages")
    else:
        print(f"   • Configuration is optimal for 30-day completion")
    
    print(f"\n🚀 GITHUB ACTIONS RECOMMENDATIONS:")
    print(f"1. For daily processing:")
    print(f"   cron: '0 2 * * *'  # Daily at 02:00 UTC")
    print(f"   PAGES_PER_BATCH = {daily_batch}")
    
    print(f"\n2. For twice daily processing:")
    print(f"   cron: '0 2,14 * * *'  # Daily at 02:00 and 14:00 UTC")
    print(f"   PAGES_PER_BATCH = {twice_daily_batch}")
    
    print(f"\n3. For every 6 hours:")
    print(f"   cron: '0 */6 * * *'  # Every 6 hours")
    print(f"   PAGES_PER_BATCH = {six_hour_batch}")
    
    print(f"\n" + "=" * 60)

if __name__ == "__main__":
    calculate_optimal_batch() 
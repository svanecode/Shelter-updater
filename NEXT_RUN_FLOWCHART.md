# What Will Happen on Next GitHub Actions Run

## Current State
- **Last page processed**: 32,919
- **Last updated**: October 29, 2025 (33 days ago)
- **Status**: Cycle is stale (> 30 days)

---

## Execution Flow

```
┌─────────────────────────────────────────┐
│  GitHub Actions Triggers Daily Run     │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  Script: new_shelters_global.py         │
│  Action: Starting...                    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  Check: Fetch global_progress           │
│  Result: last_page = 32919              │
│          last_updated = 2025-10-29      │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  Check: Is cycle complete?              │
│  Days since update: 33 days             │
│  Cycle threshold: 30 days               │
│  Result: YES - Cycle is complete        │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  Action: Start NEW CYCLE                │
│  - Reset last_page to 0                 │
│  - Update database: page = 0            │
│  - Calculate start_page = 0 + 1 = 1     │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  Action: Fetch existing shelter IDs     │
│  Result: ~23,694 shelter IDs loaded     │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  Action: Process pages 1 → 834          │
│  - Timeout: 60 seconds per request      │
│  - Sleep: 1 second between pages        │
│  - Save progress after each page        │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  IF: Page request succeeds              │
│  - Parse buildings                      │
│  - Filter for shelters                  │
│  - Add new shelters to DB               │
│  - Update progress                      │
│  - Continue to next page                │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  IF: Page request times out             │
│  - Retry with backoff:                  │
│    • 1st retry: 10s wait                │
│    • 2nd retry: 20s wait                │
│    • 3rd retry: 40s wait                │
│    • 4th retry: 80s wait                │
│    • 5th retry: 160s wait               │
│    • 6th+ retry: 300s wait              │
│  - After 15 consecutive errors: STOP    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  After ~30 minutes (834 pages)          │
│  - New shelters found: X                │
│  - Last processed page: 834             │
│  - Progress saved to database           │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  Summary Report                         │
│  ✅ Runtime: ~30 minutes                │
│  ✅ Pages processed: 834                │
│  ✅ New shelters: X                     │
│  ✅ Last page: 834                      │
│  ⏸  Pages remaining: ~49,166           │
└─────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  Next Day's Run                         │
│  - Will continue from page 835          │
│  - Process pages 835 → 1,668            │
│  - And so on...                         │
└─────────────────────────────────────────┘
```

---

## Key Differences from Previous Run

### OLD Behavior (What Failed on Oct 29)
```
Page 32920 timeout (30s) → Retry with 10s wait → Timeout again
→ Retry 10 times with 10s waits → All fail
→ STOP after 25 minutes → 0 pages processed
→ Next run: "Cycle complete, exiting" → 0 pages processed ❌
```

### NEW Behavior (What Will Happen Next)
```
Start new cycle from page 1
→ Fetch page with 60s timeout
→ If timeout: Exponential backoff (10s, 20s, 40s, 80s, 160s, 300s)
→ If still failing after 15 retries: STOP and save progress
→ Next run: Continue from last successful page ✅
```

---

## Expected Outcomes

### Best Case Scenario (API is healthy)
- ✅ Processes all 834 pages successfully
- ✅ Finds and adds new shelters
- ✅ Completes in ~30 minutes
- ✅ Progress: 1.7% of full cycle complete
- ✅ Next run continues from page 835

### Moderate Case (Some timeouts, but recovers)
- ⚠️  Some pages timeout initially
- ✅ Retries succeed with exponential backoff
- ✅ Processes most/all 834 pages
- ⚠️  Runtime: 45-60 minutes (due to retries)
- ✅ Next run continues from last successful page

### Worst Case (API is down/overloaded)
- ❌ Page 1 times out repeatedly
- ⚠️  15 consecutive errors reached
- ⏸  Stops gracefully after ~50 minutes
- ✅ Progress saved (even if 0 pages)
- ✅ Next run will retry from page 1
- 🔔 You'll see error logs indicating API issues

---

## What to Check After Next Run

### In GitHub Actions Logs:
1. **Check start message**: Should say "Starting new cycle from page 0"
2. **Check progress**: Should process pages 1-834
3. **Check summary**: Should show X pages processed, Y shelters found
4. **Check errors**: Any timeout messages? How many retries?

### In Supabase Database:
1. **global_progress table**:
   - `last_page` should be 834 (or less if errors)
   - `last_updated` should be today's date
2. **sheltersv2 table**:
   - Check if any new shelters were added
   - Look for `last_checked` timestamps from today

### Success Indicators:
- ✅ Script runs (doesn't exit immediately)
- ✅ Processes at least some pages (even if not all 834)
- ✅ Progress is saved to database
- ✅ Will continue on next run

---

## If Problems Persist

### If it still gets 0 pages processed:
1. Check Datafordeler API status
2. Try manual API call to test:
   ```bash
   curl "https://services.datafordeler.dk/BBR/BBRPublic/1/rest/bygning?page=1&username=YOUR_USERNAME&password=YOUR_PASSWORD"
   ```
3. Consider reducing `PAGES_PER_BATCH` from 834 to 100-200
4. Contact Datafordeler support

### If specific pages timeout:
- That's okay! Script will retry with long waits (up to 5 minutes)
- If persistent after 15 retries, script saves progress and continues next day
- Could be that specific pages have large datasets

---

**Bottom Line**: The script is now **guaranteed to try processing pages** on every run. It will never exit immediately due to old cycle data.

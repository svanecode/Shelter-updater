# Fix Global Progress Table Permissions

## Problem Identified

Your script is running but showing:
```
- Warning: No global progress record found
```

**Root Cause**: The `global_progress` table exists but:
1. ❌ It's empty (no records)
2. ❌ The API key doesn't have INSERT permission

## Quick Fix (5 minutes)

### Step 1: Open Supabase SQL Editor

1. Go to your Supabase dashboard: https://supabase.com/dashboard
2. Select your project: `irafzkpgqxdhsahoddxr`
3. Click **SQL Editor** in the left sidebar
4. Click **New Query**

### Step 2: Run This SQL

Copy and paste this entire SQL script into the editor:

```sql
-- Fix permissions for global_progress table

-- 1. Make sure the table exists
CREATE TABLE IF NOT EXISTS public.global_progress (
    id SERIAL PRIMARY KEY,
    last_page INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW()
);

-- 2. Enable Row Level Security
ALTER TABLE public.global_progress ENABLE ROW LEVEL SECURITY;

-- 3. Drop existing policies if any (to avoid conflicts)
DROP POLICY IF EXISTS "Allow anonymous read access" ON public.global_progress;
DROP POLICY IF EXISTS "Allow anonymous insert access" ON public.global_progress;
DROP POLICY IF EXISTS "Allow anonymous update access" ON public.global_progress;

-- 4. Create policies to allow anon role full access
CREATE POLICY "Allow anonymous read access" ON public.global_progress
    FOR SELECT
    TO anon
    USING (true);

CREATE POLICY "Allow anonymous insert access" ON public.global_progress
    FOR INSERT
    TO anon
    WITH CHECK (true);

CREATE POLICY "Allow anonymous update access" ON public.global_progress
    FOR UPDATE
    TO anon
    USING (true)
    WITH CHECK (true);

-- 5. Insert initial record
INSERT INTO public.global_progress (last_page, last_updated)
SELECT 0, NOW()
WHERE NOT EXISTS (SELECT 1 FROM public.global_progress);

-- 6. Verify it worked
SELECT * FROM public.global_progress;
```

### Step 3: Click "Run"

You should see:
```
Success. No rows returned
...
id | last_page | last_updated
1  | 0         | 2025-11-04 20:XX:XX
```

### Step 4: Test Locally

```bash
python test_progress_fix.py
```

You should now see:
```
✅ SUCCESS
Records found: 1
  ID: 1
  Last page: 0
  Last updated: 2025-11-04T20:XX:XX
```

---

## What This Does

1. **Creates the table** if it doesn't exist
2. **Enables RLS** (Row Level Security) for safety
3. **Adds policies** to allow your API key to:
   - SELECT (read progress)
   - INSERT (create progress records)
   - UPDATE (update progress)
4. **Inserts initial record** with page 0
5. **Verifies** everything worked

## Why This Happened

The `global_progress` table was created but didn't have proper RLS policies. By default, Supabase tables with RLS enabled block all access unless you explicitly allow it with policies.

Your `sheltersv2` table already has proper policies (that's why shelters can be added), but `global_progress` was missing them.

## After Fixing

Once you run the SQL:
- ✅ The script will track progress properly
- ✅ No more "Warning: No global progress record found"
- ✅ Can see progress in Supabase dashboard
- ✅ GitHub Actions will track where it stopped

---

## Alternative: Use Service Role Key (Not Recommended)

If you don't want to set up RLS policies, you could use the service_role key instead of the anon key, but this is **not recommended** because:
- ❌ Less secure (bypasses all RLS)
- ❌ Should not be exposed in client-side code
- ✅ Better to fix the policies (recommended approach above)

---

## Verification

After running the SQL, test with:

```bash
# Test progress tracking works
python test_progress_fix.py

# Run a quick test of the main script
python new_shelters_global.py
# (Cancel after a few pages with Ctrl+C)
```

You should see progress being saved without warnings!

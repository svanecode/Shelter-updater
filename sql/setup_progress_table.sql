-- Setup progress tracking table for global shelter discovery
-- Run this in your Supabase SQL Editor

-- 1. Create progress tracking table
CREATE TABLE IF NOT EXISTS public.global_progress (
    id SERIAL PRIMARY KEY,
    last_page INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW()
);

-- 2. Disable Row Level Security (RLS) on progress table
-- This is needed because we use the service_role key which should have full access
-- Progress tracking is not sensitive data and doesn't need row-level restrictions
ALTER TABLE public.global_progress DISABLE ROW LEVEL SECURITY;

-- 3. Insert initial record if table is empty
INSERT INTO public.global_progress (last_page, last_updated)
SELECT 0, NOW()
WHERE NOT EXISTS (SELECT 1 FROM public.global_progress);

-- 4. Verify the setup
SELECT * FROM public.global_progress;

-- Expected result: One row with id=1, last_page=0, and current timestamp

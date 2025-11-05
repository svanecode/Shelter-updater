-- Fix permissions for global_progress table
-- Run this in your Supabase SQL Editor

-- 1. Make sure the table exists
CREATE TABLE IF NOT EXISTS public.global_progress (
    id SERIAL PRIMARY KEY,
    last_page INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW()
);

-- 2. Enable Row Level Security (RLS)
ALTER TABLE public.global_progress ENABLE ROW LEVEL SECURITY;

-- 3. Create policies to allow anon role to INSERT, UPDATE, and SELECT
-- (The anon role is what your SUPABASE_KEY uses)

-- Allow SELECT (read)
CREATE POLICY "Allow anonymous read access" ON public.global_progress
    FOR SELECT
    TO anon
    USING (true);

-- Allow INSERT (create)
CREATE POLICY "Allow anonymous insert access" ON public.global_progress
    FOR INSERT
    TO anon
    WITH CHECK (true);

-- Allow UPDATE (modify)
CREATE POLICY "Allow anonymous update access" ON public.global_progress
    FOR UPDATE
    TO anon
    USING (true)
    WITH CHECK (true);

-- 4. If you already have policies, you might need to drop them first:
-- DROP POLICY IF EXISTS "Allow anonymous read access" ON public.global_progress;
-- DROP POLICY IF EXISTS "Allow anonymous insert access" ON public.global_progress;
-- DROP POLICY IF EXISTS "Allow anonymous update access" ON public.global_progress;
-- Then run the CREATE POLICY commands above

-- 5. Verify the table is accessible
SELECT * FROM public.global_progress;

-- 6. Insert initial record if table is empty
INSERT INTO public.global_progress (last_page, last_updated)
SELECT 0, NOW()
WHERE NOT EXISTS (SELECT 1 FROM public.global_progress);

-- 7. Verify the record was created
SELECT * FROM public.global_progress;

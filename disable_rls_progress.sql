-- Simple fix: Disable RLS on global_progress table
-- This table only contains progress tracking (not sensitive data)

-- Disable Row Level Security
ALTER TABLE public.global_progress DISABLE ROW LEVEL SECURITY;

-- Verify the table is now accessible
SELECT * FROM public.global_progress;

-- Migration: 003_add_monthly_review_table.sql
-- Description: Create the MonthlyReview table for AI-generated summaries.

CREATE TABLE IF NOT EXISTS public."MonthlyReview" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    summary TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(year, month)
);

-- Enable RLS
ALTER TABLE public."MonthlyReview" ENABLE ROW LEVEL SECURITY;

-- Allow public access (if consistent with other tables)
CREATE POLICY "Allow public read" ON public."MonthlyReview" FOR SELECT USING (true);
CREATE POLICY "Allow public insert" ON public."MonthlyReview" FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update" ON public."MonthlyReview" FOR UPDATE USING (true);

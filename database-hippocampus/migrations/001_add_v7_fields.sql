-- Migration: Add v7.1 fields to LogEntry table
-- Date: 2026-02-10
-- Description: Adds tags, habits, meta, and updatedAt columns to support LifeOS v7.1 features

-- Add new columns to LogEntry table
ALTER TABLE "LogEntry" 
  ADD COLUMN IF NOT EXISTS "tags" TEXT[] DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS "habits" JSONB DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS "meta" JSONB DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS "updatedAt" TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP;

-- Create an index on tags for better query performance
CREATE INDEX IF NOT EXISTS "LogEntry_tags_idx" ON "LogEntry" USING GIN ("tags");

-- Create an index on date for better query performance (if not exists)
CREATE INDEX IF NOT EXISTS "LogEntry_date_idx" ON "LogEntry" ("date");

-- Update existing rows to have updatedAt = createdAt if they don't have it
UPDATE "LogEntry" 
SET "updatedAt" = "createdAt" 
WHERE "updatedAt" IS NULL;

-- Make updatedAt NOT NULL after setting default values
ALTER TABLE "LogEntry" 
  ALTER COLUMN "updatedAt" SET NOT NULL;

COMMENT ON COLUMN "LogEntry"."tags" IS 'Array of tags extracted from the log entry';
COMMENT ON COLUMN "LogEntry"."habits" IS 'JSON object containing habit tracking data';
COMMENT ON COLUMN "LogEntry"."meta" IS 'JSON object containing metadata like metrics, graph seeds, etc.';
COMMENT ON COLUMN "LogEntry"."updatedAt" IS 'Timestamp of last update';

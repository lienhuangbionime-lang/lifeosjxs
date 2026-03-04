-- ============================================================================
-- LifeOS v3.6 - Supabase Migration 010
-- Purpose: Add LifeOS v7.1 AI Ingest Engine specific tracking columns
-- Date: 2026-03-05
-- ============================================================================

-- Add privacy isolation flag
ALTER TABLE public.memories ADD COLUMN IF NOT EXISTS is_private BOOLEAN DEFAULT false;

-- Add structured fact extraction from AI
ALTER TABLE public.memories ADD COLUMN IF NOT EXISTS facts JSONB DEFAULT '[]'::jsonb;

-- Add extensible custom metrics support (e.g. Sleep, Steps, etc.)
ALTER TABLE public.memories ADD COLUMN IF NOT EXISTS custom_metrics JSONB DEFAULT '{}'::jsonb;

-- Add metadata JSONB just in case for future schema-less expansion
ALTER TABLE public.memories ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

-- Adjust RPC match_memories to return is_private or filter them out if needed in the future
-- (Currently we just ensure the columns exist so the INSERT won't fail)

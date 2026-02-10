# 🚨 URGENT: Database Migration Required

## Quick Fix Steps (5 minutes)

### Step 1: Apply Database Migration ⚡
1. Open: https://app.supabase.com/project/epxpaghmtyzgidpjbfsh/sql/new
2. Paste this SQL:

```sql
ALTER TABLE "LogEntry" 
  ADD COLUMN IF NOT EXISTS "tags" TEXT[] DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS "habits" JSONB DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS "meta" JSONB DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS "updatedAt" TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP;

CREATE INDEX IF NOT EXISTS "LogEntry_tags_idx" ON "LogEntry" USING GIN ("tags");

UPDATE "LogEntry" SET "updatedAt" = "createdAt" WHERE "updatedAt" IS NULL;

ALTER TABLE "LogEntry" ALTER COLUMN "updatedAt" SET NOT NULL;
```

3. Click **RUN** ✅

### Step 2: Restart Backend Server
```powershell
# Stop current server (Ctrl+C if running)
cd backend-cortex
python -m uvicorn app.main:app --reload --port 8000
```

## What Was Fixed

✅ **Model Error**: Changed `gemini-3.0-pro-preview` → `gemini-2.5-pro`  
✅ **Database Schema**: Added missing columns (tags, habits, meta, updatedAt)  
✅ **Prisma Schema**: Updated to match v7.1 requirements

## Files Changed
- `backend-cortex/.env`
- `database-hippocampus/prisma/schema.prisma`
- `database-hippocampus/migrations/001_add_v7_fields.sql` (NEW)

## Verify It Works
After restarting, test the ingest endpoint:
```powershell
curl -X POST http://localhost:8000/api/v1/ingest -H "Content-Type: application/json" -d '{\"text\":\"Test entry\",\"date\":\"2026-02-10\"}'
```

You should see:
- ✅ No 404 model errors
- ✅ No database schema errors
- ✅ Successful AI processing

---

📖 **Full Details**: See `FIX_SUMMARY.md`

# Database Migrations

This directory contains SQL migration scripts for the LifeOS Hippocampus database.

## How to Apply Migrations

### Option 1: Using Supabase Dashboard (Recommended)

1. Go to your Supabase project dashboard: https://app.supabase.com/project/epxpaghmtyzgidpjbfsh
2. Navigate to **SQL Editor** in the left sidebar
3. Click **New Query**
4. Copy and paste the contents of the migration file (e.g., `001_add_v7_fields.sql`)
5. Click **Run** to execute the migration

### Option 2: Using Supabase CLI

If you have the Supabase CLI installed:

```bash
# Navigate to the database directory
cd database-hippocampus

# Apply the migration
supabase db push
```

### Option 3: Using psql (Direct Connection)

If you have direct database access:

```bash
psql "postgresql://postgres:[YOUR-PASSWORD]@db.epxpaghmtyzgidpjbfsh.supabase.co:5432/postgres" -f migrations/001_add_v7_fields.sql
```

## Migration Files

- **001_add_v7_fields.sql** - Adds v7.1 fields (tags, habits, meta, updatedAt) to LogEntry table

## Current Schema

After applying all migrations, the `LogEntry` table should have:

- `id` (String, Primary Key)
- `date` (DateTime, Unique)
- `content` (String) - Markdown body
- `mood` (Int, Optional)
- `focus` (Int, Optional)
- `energy` (Int, Optional)
- `aiModel` (String, Optional)
- `isAi` (Boolean)
- `createdAt` (DateTime)
- `tags` (String Array) - **NEW in v7.1**
- `habits` (JSON) - **NEW in v7.1**
- `meta` (JSON) - **NEW in v7.1**
- `updatedAt` (DateTime) - **NEW in v7.1**

# Cortex Maintenance & Evolution Log

## 2026-02-12: The Dimensionality & Persistence Upgrade

### 🛠️ Issues Encountered
1. **Dimensionality Mismatch**: Gemini updated its embedding models to output 3072 dimensions, while Supabase was configured for 768. This caused a `Bad Request` (22000) during ingest.
2. **Ghost Process Interference**: Legacy backend processes held port 8000, preventing new code logic (Overwrite/Merge) from taking effect.
3. **API Deprecation**: The `embedding-001` model was removed/renamed, causing "Memory without Soul" (empty vector) saving.

### ✅ Solutions Implemented
- **Schema Evolution**: Upgraded Supabase `memories` table and `match_memories` function to **3072 dimensions**.
- **Associative Intelligence**: Switched to `models/gemini-embedding-001` for full precision linkage.
- **Dual-Write Logic**: Implemented `mode: overwrite/append` to allow users to clean up or merge daily logs.
- **Process Guard**: Introduced a strict port-killing routine before backend reboots to ensure code integrity.

### 📜 Future Guardrails
- **Sync Pillar**: Any change in AI output dimensions MUST trigger a report and a database schema migration proposal.
- **Health Checks**: Always verify both Database and C Kernel locks before declaring a successful sync.

---
*Recorded by Antigravity and 蒼禾*

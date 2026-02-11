"""
LifeOS v3.1 - Dual-Write Ingest API
雙寫入策略：同時寫入 Supabase 和 C Kernel

設計理念：
- Supabase: 工作副本（可編輯、可搜尋、給前端用）
- C Kernel: 數位原版（不可變、永久保存、給自己留底）
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import sys
from pathlib import Path

# 添加 backend-cortex 到 Python path
sys.path.append(str(Path(__file__).parent.parent))

import kernel_driver
from app.agents.sorter import SorterAgent
from tools.scoring_engine import engine as scoring_engine

router = APIRouter(prefix="/api/v1/ingest", tags=["ingest"])

# Initialize C Kernel status check
KERNEL_AVAILABLE = kernel_driver.check_kernel_integrity()
if KERNEL_AVAILABLE:
    print("[OK] C Kernel verified (Binary found)")
else:
    print("[WARN] C Kernel binary not found. Running in Cloud-Only mode.")


# ============================================================================
# Pydantic Models
# ============================================================================

class IngestLogEntry(BaseModel):
    """日記條目 (用於 API 請求與寫入)"""
    content: str = Field(..., description="日記內容")
    mood: int = Field(..., ge=0, le=10, description="心情 (0-10)")
    focus: int = Field(..., ge=0, le=10, description="專注度 (0-10)")
    energy: int = Field(..., ge=0, le=10, description="能量 (0-10)")
    tags: list[str] = Field(default=[], description="標籤列表")
    projects: list[str] = Field(default=[], description="偵測到的專案")
    date: Optional[str] = Field(None, description="日期 (YYYY-MM-DD)，不提供則為今天")
    is_private: bool = Field(default=False, description="是否隔離 (僅存本地)")
    raw_text: Optional[str] = Field(None, description="原始未加工內容 (用於圖譜提取)")


class AnalysisData(BaseModel):
    markdown_body: str
    meta: dict
    tasks: list

class IngestResponse(BaseModel):
    """寫入回應"""
    status: str
    db_id: Optional[str] = None
    kernel_locked: bool = False
    kernel_day_offset: Optional[int] = None
    message: str
    model: str = "None"
    data: Optional[AnalysisData] = None
    is_private: bool = False


class IngestRequest(BaseModel):
    """前端請求格式"""
    text: str = Field(..., description="日記內容")
    date: str = Field(..., description="日期 YYYY-MM-DD")
    habits: list[str] = Field(default=[], description="習慣列表")
    skip_ai: bool = Field(False, description="是否跳過 AI 分析")
    mode: str = Field("append", description="寫入模式: overwrite (覆蓋), append (追加/合併)")

# ============================================================================
# API Endpoints
# ============================================================================

@router.post("", response_model=IngestResponse)
async def ingest_root(request: IngestRequest):
    """
    處理前端的 Ingest 請求
    - skip_ai=True: 直接寫入資料庫 (Supabase + Kernel)
    - skip_ai=False: 僅進行 AI 分析，不寫入 資料庫
    """
    print(f"[INGEST] Incoming request for {request.date} (skip_ai={request.skip_ai}, mode={request.mode})")
    try:
        content = request.text
        log_date = datetime.strptime(request.date, "%Y-%m-%d")
        
        # 情境 A: 僅 AI 分析 (不寫入 DB)
        # 用戶點擊 "INGEST & ANALYZE"
        # 使用 LifeOS v7.1 Sorter Agent
        if not request.skip_ai:
            try:
                # Initialize Sorter Agent
                agent = SorterAgent()
                result = agent.process(content) # Returns LogEntry (v7.1 structured)
                
                # [FACT-BASED SCORING] Use ScoringEngine for objective metrics
                objective_focus = scoring_engine.calculate_score("focus", getattr(result, 'facts', []))
                objective_energy = scoring_engine.calculate_score("energy", getattr(result, 'facts', []))

                # Sorter v7.1 puts the Markdown Analysis directly into result.content
                # We can use it directly
                md_output = result.content
                
                # Construct internal metrics dict
                # If AI provided facts, use objective score, else fallback to AI's feeling
                # [MANUAL OVERRIDE] Detect MOOD: X in raw text to respect user intent over AI/Engine
                import re
                manual_mood = re.search(r"(?i)MOOD:\s*(\d+)", content)
                manual_focus = re.search(r"(?i)FOCUS:\s*(\d+)", content)
                manual_energy = re.search(r"(?i)ENERGY:\s*(\d+)", content)

                def resolve_metric(manual_match, ai_val, objective_res):
                    if manual_match:
                        return int(manual_match.group(1))
                    # If AI was confident enough to change from 5
                    if ai_val is not None and ai_val != 5:
                        return ai_val
                    # If facts exist, use objective score
                    if objective_res.get("calculation_log"):
                        return int(objective_res["score"])
                    return ai_val or 5

                metrics = {
                    "mood": resolve_metric(manual_mood, result.mood, {"score": 5, "calculation_log": []}), # Mood has no engine yet
                    "focus": resolve_metric(manual_focus, result.focus, objective_focus),
                    "energy": resolve_metric(manual_energy, result.energy, objective_energy)
                }
                
                # [FIX] Automatically SAVE the analyzed result to DB
                # Pass BOTH raw text and processed markdown for logic downstream
                entry = IngestLogEntry(
                    content=md_output,
                    mood=metrics["mood"],
                    focus=metrics["focus"],
                    energy=metrics["energy"],
                    date=result.date or request.date,
                    tags=result.tags or [],
                    projects=result.projects or [],
                    is_private=result.is_private,
                    raw_text=content # Pass original raw input for exhaustive graph extraction
                )
                
                # Call ingest_log internal logic
                save_res = await ingest_log(entry, mode=request.mode)
                
                # Attach analysis data to response
                final_date = result.date or request.date
                save_res.data = AnalysisData(
                        markdown_body=md_output,
                        meta={"metrics": metrics, "tags": result.tags, "category": result.category, "date": final_date},
                        tasks=[] 
                )
                save_res.model = agent.model_name
                
                return save_res
            except Exception as e:
                print(f"[WARN] Sorter Analysis failed: {e}")
                
                # [FIX] Fallback: Save RAW content with default metrics
                entry = IngestLogEntry(
                    content=content,
                    mood=5, focus=5, energy=5,
                    date=request.date,
                    tags=[]
                )
                
                save_res = await ingest_log(entry, mode=request.mode)
                
                save_res.status = "analyzed_failed_saved"
                save_res.message = f"Saved Raw Content (AI Failed: {str(e)})"
                save_res.data = AnalysisData(
                        markdown_body=f"## Cortex Offline\n\n{content}\n\n*Error: {str(e)}*",
                        meta={"metrics": {"mood": 5, "focus": 5, "energy": 5}, "tags": [], "category": "Unsorted", "date": request.date},
                        tasks=[]
                )
                
                return save_res
        
        # 情境 B: 直接寫入 (跳過 AI)
        # 用戶點擊 "SAVE"
        entry = IngestLogEntry(
            content=content,
            mood=5,
            focus=5,
            energy=5,
            date=request.date
        )
        
        return await ingest_log(entry, mode=request.mode)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/log", response_model=IngestResponse)
async def ingest_log(entry: IngestLogEntry, mode: str = "append"):
    """
    寫入日記（雙寫入策略）
    """
    try:
        log_date = datetime.now()
        if entry.date:
            try:
                # Try standard format first
                log_date = datetime.strptime(entry.date, "%Y-%m-%d")
            except Exception:
                try:
                    # Try flexible parsing
                    from dateutil import parser
                    log_date = parser.parse(entry.date)
                except Exception as date_e:
                    print(f"⚠️ Invalid date format '{entry.date}', using today: {date_e}")
        
        # ========================================
        # 1. 寫入 Supabase (工作副本)
        # ========================================
        # [FORCE SYNC] For now, we save everything to Supabase to maintain RAG quality, 
        # even if AI thinks it's private. C Kernel is preferred for absolute privacy but not ready.
        if entry.is_private:
            print(f"[PRIVACY-LEVEL] AI tagged as Private for {log_date.date()}, but sinking to Supabase for RAG indexing.")
        
        if True: # Force always True for cloud sync until local kernel is active
            try:
                from supabase import create_client
                import os
                
                supabase_url = os.getenv("SUPABASE_URL")
                supabase_key = os.getenv("SUPABASE_KEY")
                
                if supabase_url and supabase_key:
                    supabase = create_client(supabase_url, supabase_key)
                    
                    # [OVERWRITE MODE] Cleanup existing records for this date
                    if mode == "overwrite":
                        print(f"[CLEANUP] Overwrite mode: Removing existing records for {entry.date}")
                        # 1. Delete Memories
                        supabase.table("memories").delete().eq("date", entry.date).execute()
                        # 2. Delete Node (Edges will cascade)
                        supabase.table("nodes").delete().eq("label", entry.date).execute()
                    
                    try:
                        # [NEW] Generate Embedding for RAG
                        from app.core.gemini import get_embeddings
                        embedding = get_embeddings(entry.content)
                        
                        data = {
                            "date": log_date.date().isoformat(),
                            "content": entry.content,
                            "mood": entry.mood,
                            "focus": entry.focus,
                            "energy": entry.energy,
                            "tags": entry.tags,
                            "embedding": embedding if embedding else None,
                            "created_at": datetime.now().isoformat()
                        }
                        
                        # [DEDUPLICATION] Check if identical content exists for this date
                        dup_check = supabase.table("memories").select("id").eq("date", data["date"]).eq("content", data["content"]).execute()
                        if dup_check.data:
                            db_id = dup_check.data[0]["id"]
                            print(f"[INFO] Supabase: Identical entry exists, skipping insert (ID: {db_id})")
                        else:
                            db_result = supabase.table("memories").insert(data).execute()
                            db_id = db_result.data[0]['id'] if db_result.data else None
                            print(f"[OK] Supabase: Saved to DB (ID: {db_id})")

                        # [NEW] Auto-create Projects
                        if entry.projects:
                            for p_name in entry.projects:
                                try:
                                    p_check = supabase.table("projects").select("id").eq("name", p_name).execute()
                                    if not p_check.data:
                                        supabase.table("projects").insert({
                                            "name": p_name,
                                            "status": "active",
                                            "progress": 0,
                                            "meta": {"category": "macro", "detected_by": "ai"}
                                        }).execute()
                                        print(f"[OK] AI Auto-Project Created: {p_name}")
                                    else:
                                        print(f"[INFO] Project already exists: {p_name}")
                                except Exception as proj_e:
                                    print(f"[WARN] Failed to auto-project sync: {proj_e}")

                    except Exception as inner_e:
                        print(f"[ERROR] Supabase Insert Error: {inner_e}")
                        import traceback
                        traceback.print_exc()
                        db_id = f"ERROR: {str(inner_e)}" 
                else:
                    print("[WARN] Supabase: Not configured (missing URL/KEY)")
                    db_id = "ERROR: Missing Supabase Env Vars"
            except Exception as e:
                import traceback
                print(f"[ERROR] Supabase write critical failure: {e}")
                traceback.print_exc()
                db_id = None

        
        # ========================================
        # 2. 寫入 C Kernel (數位原版)
        # ========================================
        kernel_locked = False
        kernel_day_offset = None
        
        if KERNEL_AVAILABLE:
            try:
                # 调用 kernel_driver 的写入函数
                kernel_locked = kernel_driver.write_to_kernel(
                    date_obj=log_date,
                    content=entry.content,
                    mood=entry.mood,
                    flags=1 # Default text flag
                )
                
                if kernel_locked:
                    print(f"[OK] C Kernel: Secured for {log_date.date()}")
                else:
                    print(f"[WARN] C Kernel: Write skipped or failed")
            
            except Exception as e:
                print(f"[ERROR] C Kernel write failed: {e}")
        
        # ========================================
        # 3. 返回結果
        # ========================================
        # 3. 建立知識圖譜關聯 (Nodes & Edges)
        # ========================================
        if db_id:
            try:
                # 提取實體 (從 原始輸入 + 處理過內容 雙重提取)
                import re
                processed_content = entry.content or ""
                raw_text = getattr(entry, 'raw_text', '') or ""
                combined_text = processed_content + " " + raw_text
                
                # 1. 標籤提取 (支持中文、底線、點號)
                tags = re.findall(r"#([\w\u4e00-\u9fa5\._-]+)", combined_text)
                # 2. 人物提取
                mentions = re.findall(r"@([\w\u4e00-\u9fa5\._-]+)", combined_text)
                # 3. 概念與跨日期引用 [[Name]]
                wiki_links = re.findall(r"\[\[(.*?)\]\]", combined_text)
                
                # 所有的「對象」匯整
                entities = []
                for t in tags: entities.append({"label": t.strip(), "type": "tag"})
                for m in mentions: entities.append({"label": m.strip(), "type": "person"})
                for w in wiki_links: entities.append({"label": w.strip(), "type": "concept"})
                
                # 合併 AI 提取出的標籤
                if hasattr(entry, 'tags') and entry.tags:
                    for t in entry.tags: entities.append({"label": t.strip(), "type": "tag"})
                if hasattr(entry, 'projects') and entry.projects:
                    for p in entry.projects: entities.append({"label": p.strip(), "type": "project"})
                
                # 去重並清洗標籤
                unique_entities = {}
                for e in entities:
                    label = e["label"]
                    if not label: continue
                    # 統一清洗標籤符號
                    label_clean = label.strip("[]#@ ")
                    if label_clean:
                        # 優先保留非 concept 類型，如果同名
                        if label_clean not in unique_entities or e["type"] != "concept":
                            unique_entities[label_clean] = {"label": label_clean, "type": e["type"]}
                
                # 建立日記節點 ID (使用日期作為標籤以維持與 UI 一致)
                log_node_label = entry.date or datetime.now().strftime("%Y-%m-%d")

                # 1. 確保日記節點存在 (儲存完整 Meta 以便圖譜點擊預覽)
                log_metadata = {
                    "is_log": True,
                    "memory_id": db_id, # Link back to the memory record
                    "content": entry.content,
                    "mood": entry.mood,
                    "focus": entry.focus,
                    "energy": entry.energy,
                    "date": log_node_label,
                    "tags": entry.tags
                }
                supabase.table("nodes").upsert({
                    "label": log_node_label, 
                    "type": "concept", # Use concept to pass DB check constraint
                    "metadata": log_metadata
                }, on_conflict="label").execute()
                log_node_res = supabase.table("nodes").select("id").eq("label", log_node_label).execute()
                log_node_id = log_node_res.data[0]["id"] if log_node_res.data else None
                
                sync_count = 0
                if log_node_id:
                    for ent in unique_entities.values():
                        # 防止自我連結 (例如 2/2 指向 2/2)
                        if ent["label"] == log_node_label:
                            continue

                        # 2. 確保實體節點存在
                        supabase.table("nodes").upsert({"label": ent["label"], "type": ent["type"]}).execute()
                        ent_node_res = supabase.table("nodes").select("id").eq("label", ent["label"]).execute()
                        ent_node_id = ent_node_res.data[0]["id"] if ent_node_res.data else None
                        
                        if ent_node_id:
                            # 3. 建立連線 (Log -> Entity)
                            # [DEDUPLICATION] Check if edge already exists
                            edge_check = supabase.table("edges").select("id").eq("source_id", log_node_id).eq("target_id", ent_node_id).eq("relation", "related").execute()
                            
                            if not edge_check.data:
                                supabase.table("edges").insert({
                                    "source_id": log_node_id,
                                    "target_id": ent_node_id,
                                    "relation": "related"
                                }).execute()
                                # Use basic addition to fix lint
                                sync_count = sync_count + 1
                            else:
                                # Edge exists, consider it synced
                                sync_count = sync_count + 1
                            
                print(f"[OK] Graph Sync: Generated {sync_count} linkages for {log_node_label}")
            except Exception as graph_e:
                print(f"[WARN] Graph synchronization failed: {graph_e}")

        # ========================================
        # 4. 總結回應
        # ========================================
        if db_id and kernel_locked:
            status = "synced"
            message = "Successfully synced to Supabase (Memory + Graph) and C Kernel"
        elif db_id:
            status = "db_only"
            message = "Saved to Supabase (Memory + Graph) only"
        elif kernel_locked:
            status = "kernel_only"
            message = "Saved to C Kernel only"
        else:
            status = "failed"
            # If db_id contains the error string, we show it
            if db_id and db_id.startswith("ERROR:"):
                message = f"Failed to save: {db_id}"
            else:
                message = "Failed to save to both systems (Cloud and Local both unavailable)"
        
        return IngestResponse(
            status=status,
            db_id=db_id,
            kernel_locked=kernel_locked,
            kernel_day_offset=kernel_day_offset,
            message=message,
            is_private=entry.is_private
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify/{date}")
async def verify_entry(date: str):
    """
    驗證指定日期的記錄
    """
    try:
        log_date = datetime.strptime(date, "%Y-%m-%d")
        
        # 從 Supabase 讀取
        db_content = None
        try:
            from supabase import create_client
            import os
            
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if supabase_url and supabase_key:
                supabase = create_client(supabase_url, supabase_key)
                result = supabase.table("memories").select("*").eq("date", date).execute()
                
                if result.data:
                    db_content = result.data[0]['content']
        except Exception as e:
            print(f"[WARN] Supabase read failed: {e}")
        
        # 從 C Kernel 讀取
        kernel_content = None
        if KERNEL_AVAILABLE:
            try:
                # kernel_driver.read_from_kernel returns string content or None
                kernel_content = kernel_driver.read_from_kernel(log_date)
            except Exception as e:
                print(f"[WARN] C Kernel read failed: {e}")
        
        # 比較
        exists_in_db = db_content is not None
        exists_in_kernel = kernel_content is not None
        content_match = db_content == kernel_content if (exists_in_db and exists_in_kernel) else None
        
        return {
            "date": date,
            "exists_in_db": exists_in_db,
            "exists_in_kernel": exists_in_kernel,
            "content_match": content_match,
            "db_length": len(db_content) if db_content else 0,
            "kernel_length": len(kernel_content) if kernel_content else 0,
            "status": "verified" if content_match else "mismatch" if (exists_in_db and exists_in_kernel) else "partial"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kernel/read/{date}")
async def read_from_kernel(date: str):
    """
    直接從 C Kernel 讀取（用於驗證數位原版）
    """
    if not KERNEL_AVAILABLE:
        raise HTTPException(status_code=503, detail="C Kernel not available")
    
    try:
        log_date = datetime.strptime(date, "%Y-%m-%d")
        text = kernel_driver.read_from_kernel(log_date)
        
        if not text:
            raise HTTPException(status_code=404, detail="Entry not found in C Kernel")
        
        return {
            "date": date,
            "content": text,
            "params": "Metadata temporarily unavailable in Driver v3.4", 
            "source": "C Kernel (Digital Original)"
        }
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format (use YYYY-MM-DD)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kernel/status")
async def kernel_status():
    """
    獲取 C Kernel 狀態
    """
    from pathlib import Path
    
    idx_path = Path("backend-cortex/kernel/storage/life.index")
    txt_path = Path("backend-cortex/kernel/storage/life.text")
    
    return {
        "kernel_available": KERNEL_AVAILABLE,
        "index_file_exists": idx_path.exists(),
        "text_file_exists": txt_path.exists(),
        "index_file_size": idx_path.stat().st_size if idx_path.exists() else 0,
        "text_file_size": txt_path.stat().st_size if txt_path.exists() else 0,
        "estimated_entries": idx_path.stat().st_size // 32 if idx_path.exists() else 0,
        "storage_path": str(idx_path.parent) if idx_path.exists() else None
    }

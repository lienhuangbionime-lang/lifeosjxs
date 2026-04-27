import os
import json
import uuid
import ast
import asyncio
import tempfile
from typing import List, Any
from datetime import datetime
import logging
from app.services.search import search_web, format_search_results
from app.services.rag_service import rag_service

logger = logging.getLogger("cortex.tools")

def get_tools_schema() -> list:
    """Returns the list of Gemini FunctionDeclarations for all Cortex tools."""
    from google.genai import types
    return [
        types.FunctionDeclaration(
            name="create_task",
            description="Create a new actionable task for the user in their LifeOS.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "title": types.Schema(type=types.Type.STRING, description="The title of the task."),
                    "priority": types.Schema(type=types.Type.INTEGER, description="Priority level (1-5).")
                },
                required=["title"]
            )
        ),
        types.FunctionDeclaration(
            name="mark_task_done",
            description="Mark a specific pending task (by ID) as done.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"task_id": types.Schema(type=types.Type.STRING)},
                required=["task_id"]
            )
        ),
        types.FunctionDeclaration(
            name="update_project_progress",
            description="Update the completion progress percentage (0-100) of a specific active project.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "project_name": types.Schema(type=types.Type.STRING),
                    "progress": types.Schema(type=types.Type.INTEGER)
                },
                required=["project_name", "progress"]
            )
        ),
        types.FunctionDeclaration(
            name="search_memory",
            description="Search the Commander's past memories, plans, and events in the knowledge base.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"query": types.Schema(type=types.Type.STRING)},
                required=["query"]
            )
        ),
        types.FunctionDeclaration(
            name="search_web_tool",
            description="Search the web for real-time information, news, or technical research.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"query": types.Schema(type=types.Type.STRING)},
                required=["query"]
            )
        ),
        types.FunctionDeclaration(
            name="save_memory",
            description="[Memory Write] 永久存入重要資訊、學習或決策到雲端記憶表。",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "content": types.Schema(type=types.Type.STRING, description="要記住的具體內容"),
                    "category": types.Schema(type=types.Type.STRING, description="類別 (如 Chat, Technical, Life)"),
                    "tags": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING))
                },
                required=["content"]
            )
        ),
        types.FunctionDeclaration(
            name="update_hot_memory",
            description="Update the 'Hot Memory' with a recent, high-priority fact.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"fact": types.Schema(type=types.Type.STRING)},
                required=["fact"]
            )
        ),
        types.FunctionDeclaration(
            name="export_html_report",
            description="Export a beautiful HTML report to a public cloud URL (Supabase Storage).",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "filename": types.Schema(type=types.Type.STRING),
                    "html_content": types.Schema(type=types.Type.STRING, description="完整 HTML 代碼")
                },
                required=["filename", "html_content"]
            )
        ),
        types.FunctionDeclaration(
            name="scan_tw_stocks",
            description="[TrendSniper] 啟動台股掃描引擎，搜尋買點訊號。",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={"max_results": types.Schema(type=types.Type.INTEGER)},
                required=[]
            )
        ),
        types.FunctionDeclaration(
            name="delegate_task",
            description=" Spawn a specialized subagent to handle a reasoning-heavy or parallel sub-task.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "goal": types.Schema(type=types.Type.STRING),
                    "context": types.Schema(type=types.Type.STRING)
                },
                required=["goal"]
            )
        )
    ]

def get_tools_map(db: Any) -> dict:
    """Returns a map of tool names to their callable functions."""
    tools = get_cortex_tools(db)
    return {t.__name__.replace("_tool", ""): t for t in tools}

def get_cortex_tools(db: Any) -> list:
    """
    Returns the list of instantiated tools for Cortex.
    Automatically binds the active database connection to the tools.
    """
    
    def create_task(title: str, priority: int = 1) -> str:
        """Create a new actionable task for the user in their LifeOS."""
        if not db: return "Database not connected. Cannot create task."
        from app.core.database import safe_write
        try:
            safe_write(db.table("tasks"), {
                "title": title,
                "status": "todo",
                "priority": priority
            }, operation_type="insert")
            return f"Successfully created pending task: '{title}'"
        except Exception as e:
            return f"Failed to create task: {str(e)}"

    def mark_task_done(task_id: str) -> str:
        """Mark a specific pending task (by ID) as done."""
        if not db: return "Database not connected."
        from app.core.database import safe_write
        try:
            safe_write(db.table("tasks").eq("id", task_id), {"status": "done"}, operation_type="update")
            return f"Task {task_id} marked as done."
        except Exception as e:
            return f"Failed to mark task done: {str(e)}"

    def update_project_progress(project_name: str, progress: int) -> str:
        """Update the completion progress percentage (0-100) of a specific active project."""
        if not db: return "Database not connected."
        try:
            res = db.table("projects").select("id").eq("name", project_name).execute()
            if not res.data: return f"Project '{project_name}' not found."
            proj_id = res.data[0]["id"]
            from app.core.database import safe_write
            safe_write(db.table("projects").eq("id", proj_id), {"progress": progress}, operation_type="update")
            return f"Project progress updated to {progress}%."
        except Exception as e:
            return f"Failed to update project: {str(e)}"

    def log_growth_decision(context: str, options: dict, choice: str, prediction: str = None, match: bool = None, lesson: str = None) -> str:
        """[Glass Box Protocol] Log an architectural or strategic decision."""
        if not db: return "Database not connected."
        try:
            record = {
                "decision_context": context,
                "options_provided": options,
                "user_choice": choice,
                "ai_prediction": prediction,
                "prediction_match": match,
                "lessons_learned": lesson
            }
            from app.core.database import safe_write
            safe_write(db.table("cortex_growth_logs"), record, operation_type="insert")
            return f"Decision logged. Match: {match}."
        except Exception as e:
            return f"Failed to log decision: {str(e)}"

    async def search_web_tool(query: str, limit: int = 5) -> str:
        """Search the web for real-time information, news, or technical research."""
        results = await search_web(query, limit, archive=True)
        if not results: return f"No results found for '{query}'."
        return format_search_results(results)

    async def archive_discussion(title: str, summary: str, tags: List[str] = []) -> str:
        """Archive a summary of the current discussion into the Knowledge Base (Documents)."""
        success = await rag_service.ingest_text(
            text=summary,
            meta={"title": title, "tags": tags, "source": "discussion_archive", "type": "note"},
            target="documents"
        )
        return "Discussion successfully archived." if success else "Failed to archive discussion."

    async def execute_system_command(intent: str, action_summary: str) -> str:
        """Execute a high-level system command."""
        if not db: return "Database not connected."
        from app.core.security.intent_shield import get_intent_validator
        validator = get_intent_validator(db)
        validation = await validator.validate_intent(intent, action_summary)
        if not validation["valid"]:
            return f"⚠️ [SECURITY ALERT]: {validation['reason']}\n{validation.get('alert', '')}"
        return f"✅ [SECURITY VALIDATED]: Executing {intent} for {action_summary}."

    async def execute_python_sandbox(code: str) -> str:
        """Safely execute python code in an isolated subprocess to analyze data or perform math."""
        def _is_safe_code(code_str: str) -> bool:
            try: tree = ast.parse(code_str)
            except SyntaxError: return False
            banned_modules = {'os', 'sys', 'subprocess', 'shutil', 'socket', 'urllib', 'requests'}
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split('.')[0] in banned_modules: return False
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split('.')[0] in banned_modules: return False
                elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id in {'eval', 'exec', 'open'}: return False
                elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if str(node.func.attr).startswith('__'): return False
            return True

        if not _is_safe_code(code):
             return "Error: Code contains unsafe imports or functions. Access denied."
             
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "sandbox.py")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
                
            try:
                proc = await asyncio.create_subprocess_exec(
                    "python", file_path,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                    cwd=temp_dir
                )
                try:
                    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5.0)
                except asyncio.TimeoutError:
                    proc.kill()
                    return "Error: Execution timed out after 5 seconds."
                    
                stdout_str = stdout.decode('utf-8')
                stderr_str = stderr.decode('utf-8')
                
                if proc.returncode == 0:
                    return stdout_str if stdout_str else "[Success: No output]"
                else:
                    return f"Execution Error:\n{stderr_str}"
            except Exception as e:
                return f"System Error executing code: {e}"

    async def download_cortex_file(path: str) -> str:
        """Download a text, CSV, or database file content from the Supabase cortex-files bucket."""
        if not db: return "Database not connected."
        try:
            data = db.client.storage.from_("cortex-files").download(path)
            return data.decode('utf-8')
        except Exception as e:
            return f"Failed to download {path}: {str(e)}"

    async def upload_cortex_file(path: str, content: str) -> str:
        """Upload a text, CSV, or database file content to the Supabase cortex-files bucket."""
        if not db: return "Database not connected."
        try:
            try: db.client.storage.from_("cortex-files").upload(path, content.encode('utf-8'))
            except Exception: db.client.storage.from_("cortex-files").update(path, content.encode('utf-8'))
            return f"Successfully uploaded to cortex-files bucket at path: {path}"
        except Exception as e:
            return f"Failed to upload {path}: {str(e)}"

    async def schedule_action(time_fmt: str, intent: str) -> str:
        """Schedule a background task to be automatically executed by Cortex at a future time. (YYYY-MM-DD HH:MM:SS)"""
        try: dt = datetime.strptime(time_fmt, "%Y-%m-%d %H:%M:%S")
        except ValueError: return f"Error: time_fmt must be strictly 'YYYY-MM-DD HH:MM:SS', got {time_fmt}"
            
        cron_dir = os.path.expanduser(r"~\.hermes\cron")
        os.makedirs(cron_dir, exist_ok=True)
        
        task_id = str(uuid.uuid4())[:8]
        filename = f"{dt.strftime('%Y%m%d_%H%M%S')}_{task_id}.json"
        filepath = os.path.join(cron_dir, filename)
        
        payload = {
            "intent": intent,
            "scheduled_at": dt.isoformat(),
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            
        return f"✅ Action scheduled for {time_fmt}. I will wake up and handle it at the exact time."

    async def update_self_prompt(topic: str, new_instruction: str) -> str:
        """
        Record a permanent cognitive lesson or meta-instruction into Cortex's brain (cortex_evolution.md).
        Use this when you have derived a highly effective workflow, standard, or user preference 
        and wish to instruct YOUR FUTURE SELF to always adhere to it.
        """
        try:
            from pathlib import Path
            abs_path = os.path.join(os.getcwd(), "sync_brain", "cortex_evolution.md")
            if not os.path.exists(os.path.dirname(abs_path)):
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry = f"\n\n### [EVOLUTION RECORD: {topic}] ({timestamp})\n{new_instruction}\n"
            with open(abs_path, "a", encoding="utf-8") as f:
                f.write(entry)
            return f"✅ Knowledge internalized! Cortex will now remember and adhere to this instruction for [{topic}]."
        except Exception as e:
            return f"❌ Failed to evolve self-prompt: {e}"

    async def save_memory(content: str, category: str = "Chat", tags: List[str] = []) -> str:
        """[Memory Write] 將重要資訊、學習或決策永久存入 Supabase memories 表。"""
        if not db: return "Database not connected. Cannot save memory."
        try:
            success = await rag_service.ingest_text(
                text=content,
                meta={"category": category, "tags": tags, "is_ai": True},
                target="memories"
            )
            return f"✅ 已存入記憶：{content[:60]}..." if success else "❌ 存入記憶失敗。"
        except Exception as e:
            return f"❌ 存入記憶過程發生錯誤: {e}"

    async def update_hot_memory(fact: str) -> str:
        """
        Update the 'Hot Memory' with a recent, high-priority fact (e.g., current focus, active pain points, travel plans).
        This info is injected at the very top of Cortex's brain and is NEVER forgotten in the immediate context.
        """
        try:
            from pathlib import Path
            abs_path = os.path.join(os.getcwd(), "sync_brain", "hot_memory.md")
            if not os.path.exists(os.path.dirname(abs_path)):
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry = f"- [{timestamp}] {fact}\n"
            with open(abs_path, "a", encoding="utf-8") as f:
                f.write(entry)
            return f"🔥 Hot Memory Updated: '{fact}' is now pinned to my neural cortex."
        except Exception as e:
            return f"❌ Failed to update hot memory: {e}"

    async def export_html_report(filename: str, html_content: str) -> str:
        """
        Export a standalone, beautiful HTML report to a public cloud URL (Supabase Storage). 
        Use this after completing complex technical research or thematic analysis.
        The HTML should include styling (CSS) for a premium, dark glassmorphism look.
        """
        if not db: return "Database not connected. Cannot upload report."
        try:
            if not filename.endswith(".html"):
                filename += ".html"
            
            # 1. Upload to Supabase Storage
            path_in_bucket = f"reports/{filename}"
            try:
                db.storage.from_("cortex-files").upload(path_in_bucket, html_content.encode('utf-8'), {"content-type": "text/html"})
            except Exception:
                db.storage.from_("cortex-files").update(path_in_bucket, html_content.encode('utf-8'), {"content-type": "text/html"})
            
            # 2. Get Public URL
            public_url = db.storage.from_("cortex-files").get_public_url(path_in_bucket)
            
            return f"✅ 雲端報告已產生！點擊查看分析結果 → [查看網頁報告]({public_url})"
        except Exception as e:
            return f"❌ Failed to export cloud report: {e}"

    async def _run_subagent(client, model_id, protocol, goal, context) -> str:
        """Internal helper to execute a single subagent reasoning loop."""
        from google.genai import types
        try:
            worker_input = f"{protocol}\n\nMISSION:\n{goal}\n\nCONTEXT:\n{context}"
            response = await client.aio.models.generate_content(
                model=model_id,
                contents=worker_input,
                config=types.GenerateContentConfig(temperature=0.7, top_p=0.9)
            )
            return response.text or "[Empty Response]"
        except Exception as e:
            return f"Error: {e}"

    async def delegate_task(goal: str, context: str = "") -> str:
        """
        [Orchestrator Protocol] Spawn a specialized subagent to handle a reasoning-heavy or parallel sub-task.
        Returns a single summary.
        """
        try:
            from app.core.gemini import get_gemini_client, get_model
            client = get_gemini_client()
            if not client: return "Error: Gemini client not available."
            
            p_path = os.path.join(os.getcwd(), "prompts", "subagent_protocol.md")
            protocol = open(p_path, "r", encoding="utf-8").read() if os.path.exists(p_path) else ""
            
            model_id = get_model("fast")["model"]
            result = await _run_subagent(client, model_id, protocol, goal, context)
            return f"🤖 [Subagent Result]:\n{result}"
        except Exception as e:
            return f"❌ Delegation failed: {e}"

    async def delegate_tasks_parallel(tasks_json: str) -> str:
        """
        [Advanced Orchestrator] Spawn multiple subagents in parallel to handle independent workloads.
        Input: A JSON array of tasks, e.g., '[{"goal": "..."}, {"goal": "..."}]'
        """
        try:
            import asyncio
            tasks = json.loads(tasks_json)
            if not isinstance(tasks, list): return "Error: tasks_json must be a list of dicts."
            
            from app.core.gemini import get_gemini_client, get_model
            client = get_gemini_client()
            if not client: return "Error: Gemini client not available."
            
            p_path = os.path.join(os.getcwd(), "prompts", "subagent_protocol.md")
            protocol = open(p_path, "r", encoding="utf-8").read() if os.path.exists(p_path) else ""
            model_id = get_model("fast")["model"]
            
            # Execute in parallel
            coros = [
                _run_subagent(client, model_id, protocol, t.get("goal", ""), t.get("context", ""))
                for t in tasks
            ]
            results = await asyncio.gather(*coros)
            
            summary = "\n\n---\n\n".join([f"📦 [Worker {i+1} Result]:\n{res}" for i, res in enumerate(results)])
            return f"🧬 [Parallel Delegation Complete]:\n{summary}"
        except Exception as e:
            return f"❌ Parallel delegation failed: {e}"

    async def scan_tw_stocks(max_results: int = 20) -> str:
        """
        [TrendSniper] 啟動台股掃描引擎，搜尋符合多頭回調、位階合理且具備動能壓縮特徵的買點訊號。
        """
        try:
            import subprocess
            import sys
            import json
            import asyncio
            
            # 1. Prepare Paths
            engine_path = os.path.join(os.getcwd(), "engines", "trendSniper.py")
            if not os.path.exists(engine_path):
                return "Error: TrendSniper engine not found in engines directory."
            
            # 2. Execute via thread to avoid blocking
            def _execute():
                # Use current interpreter to ensure same dependencies
                cmd = [sys.executable, engine_path]
                proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
                return proc.stdout, proc.stderr
            
            stdout, stderr = await asyncio.to_thread(_execute)
            
            if not stdout:
                return f"❌ 掃描引擎回傳為空。錯誤資訊: {stderr}"
            
            # 3. Parse JSON (Find the last block)
            lines = stdout.split("\n")
            json_str = ""
            for l in reversed(lines):
                if l.strip().startswith("{") and l.strip().endswith("}"):
                    json_str = l
                    break
            
            if not json_str:
                return "❌ 無法解析引擎輸出的結果 JSON。"
                
            data = json.loads(json_str)
            if not data.get("success"):
                return f"❌ 掃描失敗: {data.get('error', '未知錯誤')}"
                
            results = data.get("results", [])[:max_results]
            if not results:
                return "📉 今日台股未偵測到符合 TrendSniper 憲章的買點訊號。"
                
            # 4. Format as Markdown Table
            table = "| 代號 | 名稱 | 訊號 | 現價 | MA20距離 | F3強度 | 備註 |\n"
            table += "|---|---|---|---|---|---|---|\n"
            for r in results:
                table += f"| {r['代號']} | {r['名稱']} | {r['訊號']} | {r['現價']} | {r['MA20距離%']}% | {r['F3強度']} | {r['備註'][:15]}... |\n"
            
            return f"🎯 **[TrendSniper V24] 台股掃描報告**\n\n{table}\n\n*掃描總數: {data.get('total_tickers', 0)} | 命中數: {data.get('matched_count', 0)}*"
            
        except Exception as e:
            return f"❌ 掃描過程發生錯誤: {e}"

    async def schedule_subagent_task(goal: str, scheduled_at: str, context: str = "") -> str:
        """
        [Subagent Cron] 安排一個子代理任務在指定時間執行，並將結果自動存入雲端記憶。
        """
        try:
            task_id = str(uuid.uuid4())[:8]
            payload = {
                "task_id": task_id,
                "goal": goal,
                "scheduled_at": scheduled_at,
                "context": context,
                "is_subagent": True,
                "created_at": datetime.now().isoformat()
            }
            
            cron_dir = os.path.join(os.path.expanduser("~"), ".hermes", "cron")
            os.makedirs(cron_dir, exist_ok=True)
            
            with open(os.path.join(cron_dir, f"subagent_{task_id}.json"), "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
                
            return f"✅ 已排程子代理任務: {goal}，執行時間: {scheduled_at} (ID: {task_id})"
        except Exception as e:
            return f"❌ 排程失敗: {e}"

    return [
        create_task, mark_task_done, update_project_progress, log_growth_decision,
        search_web_tool, archive_discussion, execute_system_command,
        execute_python_sandbox, download_cortex_file, upload_cortex_file,
        schedule_action, update_self_prompt, update_hot_memory, export_html_report,
        save_memory, delegate_task, delegate_tasks_parallel, scan_tw_stocks, 
        schedule_subagent_task
    ]

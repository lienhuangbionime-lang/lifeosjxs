import os
from google import genai
from dotenv import load_dotenv
from app.models.gemini import LogEntry

load_dotenv()

class SorterAgent:
    def __init__(self):
        # 使用 Flash 模型進行快速分類
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not found in environment variables")
        self.client = genai.Client(api_key=api_key)
        # 優先從環境變數讀取，若無則預設為 Flash Lite
        self.model_name = os.getenv("GEMINI_FAST_MODEL", "gemini-flash-lite-latest")

    def process(self, user_input: str) -> LogEntry:
        # Load System Prompt from external file
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "prompts", "system_daily.md")
        
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()
            print(f"[INFO] Loaded custom prompt from {prompt_path}")
        except Exception as e:
            print(f"[WARN] Could not load custom prompt: {e}. Using default fallback.")
            system_prompt = "You are a Log Sorter. Analyze into Markdown."

        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        final_prompt = f"""
        {system_prompt}
        
        Current Date: {current_date}
        --------------------------------------------------
        使用者輸入: {user_input}
        --------------------------------------------------
        直接輸出完整的 Markdown 內容，不需要包裹在 JSON 中。
        確保 Daily Metrics 區塊格式正確以便解析。
        
        重要指南：
        1. 優先使用使用者輸入標題中的日期（例如 # 2026-02-01）作為輸出的標題日期。
        2. 只有在使用者完全沒提供日期時，才使用目前的日期 ({current_date})。
        3. 輸出標題格式維持為 # [YYYY-MM-DD] 日記。
        """
        
        # [MODIFIED] Request Plain Text (Markdown) instead of JSON
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=final_prompt,
            # config removed to allow raw text output
        )
        
        raw_markdown = response.text
        return self._parse_markdown(raw_markdown)

    def _parse_markdown(self, text: str) -> LogEntry:
        import re
        import json
        
        # Default local variables
        mood, focus, energy = 5, 5, 5
        category = "Life"
        tags_list = []
        projects_list = []
        facts_list = []
        
        # 1. Try to find the JSON block at the end
        json_pattern = re.compile(r"```json(.*?)```", re.DOTALL)
        matches = json_pattern.findall(text)
        
        clean_content = text
        is_private = False
        
        if matches:
            try:
                # Use the last match as the metadata block
                json_str = matches[-1].strip()
                data = json.loads(json_str)
                
                # Update metrics from JSON
                mood = int(data.get("mood", 5))
                focus = int(data.get("focus", 5))
                energy = int(data.get("energy", 5))
                category = str(data.get("category", "Life"))
                tags_raw = data.get("tags", [])
                projects_raw = data.get("projects", [])
                is_private = bool(data.get("is_private", False))
                facts_list = data.get("facts", [])

                
                if isinstance(tags_raw, list):
                    tags_list = tags_raw
                else:
                    tags_list = []

                if isinstance(projects_raw, list):
                    projects_list = projects_raw
                else:
                    projects_list = []
                
                # Handle custom metrics by adding them to tags
                if "custom_metrics" in data and isinstance(data["custom_metrics"], dict):
                    for k, v in data["custom_metrics"].items():
                        tags_list.append(f"metric:{k}:{v}")
                
                # Remove the JSON block from content
                last_block_full = f"```json{matches[-1]}```"
                clean_content = text.replace(last_block_full, "").strip()
                clean_content = re.sub(r"### Machine Processing Protocol \(Hidden\).*", "", clean_content, flags=re.DOTALL).strip()
                
            except Exception as e:
                print(f"[WARN] JSON Parsing failed: {e}. Falling back to Regex.")
        
        # 2. Extract Date (Search for # [YYYY-MM-DD] header first, then fallback to any date)
        # 支持 # YYYY-MM-DD, # [YYYY-MM-DD], # 2024/01/01, # 2024-1-1 等格式
        header_date_match = re.search(r"#\s*\[?(\d{4}[-/]\d{1,2}[-/]\d{1,2})\]?", text)
        if header_date_match:
             raw_date = header_date_match.group(1).replace("/", "-")
             # Ensure YYYY-MM-DD (zero padded) for system compatibility
             parts = raw_date.split("-")
             found_date = f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"
        else:
             date_match = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})", text)
             if date_match:
                 raw_date = date_match.group(1).replace("/", "-")
                 parts = raw_date.split("-")
                 found_date = f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"
             else:
                 found_date = None
        
        # 3. Extract Tags
        if not tags_list:
             tags_found = re.findall(r"#([\w\u4e00-\u9fa5\._-]+)", clean_content)
             tags_list = list(set(tags_found))

        return LogEntry(
            content=clean_content,
            mood=mood,
            focus=focus,
            energy=energy,
            tags=tags_list,
            projects=projects_list,
            category=category,
            date=found_date,
            is_private=is_private,
            facts=facts_list
        )


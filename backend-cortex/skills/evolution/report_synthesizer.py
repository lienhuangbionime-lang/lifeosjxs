import os
import json
import datetime
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Sovereign Report Synthesizer v1.0
# Goal: Scan memories for #SOUL and #FRICTION to generate a "Pulse" report.

class ReportSynthesizer:
    def __init__(self):
        load_dotenv("backend-cortex/.env")
        self.supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
        self.report_dir = Path("sync_brain/Reports")
        self.report_dir.mkdir(parents=True, exist_ok=True)

    async def generate_pulse_report(self, days=7):
        print(f"🎬 Starting LLM-driven Pulse Synthesis for last {days} days...")
        
        # 1. Fetch relevant memories
        res = self.supabase.table("memories").select("*").order("date", desc=True).limit(20).execute()
        memories = res.data or []
        
        if not memories:
            print("📭 No memories to analyze.")
            return None

        # 2. Use Gemini to "Discover Themes" (Schema-Agnostic)
        from app.core.gemini import get_model, safe_generate_content
        # We'll use a local client or the core model
        import google.genai as genai
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        full_text = "\n\n---\n\n".join([f"[{m['date']}] {m['content']}" for m in memories])
        
        prompt = f"""
分析以下使用者的日記內容，並生成一份「主權進度報告」。
不要只侷限於 #SOUL 或 #FRICTION。請自動識別使用者生活中的「所有重要維度」（例如：育兒、財經、旅行、品牌、技術、心情等）。

【日記內容】:
{full_text}

【輸出要求】:
1. 自動分類：為每個發現的維度建立一個小節。
2. 深度分析：紀錄每個維度的「進展」或「衝突」。
3. 戰略建議：為接下來的一週提供主權推進建議。
4. 保持風格：文字要帶感性與戰略感。
"""
        
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            report_body = response.text
        except Exception as e:
            print(f"❌ LLM Synthesis failed: {e}")
            report_body = "無法自動生成報告，請檢查 API 金鑰。"

        # 3. Structure the Final Output
        today = datetime.date.today().isoformat()
        final_report = f"# Sovereign Pulse Report: {today}\n" + report_body
        
        # 4. Save to sync_brain
        report_path = self.report_dir / f"Pulse_v2_{today}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(final_report)
            
        print(f"✅ LLM Pulse Report delivered to: {report_path}")
        return report_path

if __name__ == "__main__":
    import asyncio
    synther = ReportSynthesizer()
    asyncio.run(synther.generate_pulse_report())

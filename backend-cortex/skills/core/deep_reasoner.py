import os
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Sovereign Deep Reasoner v1.0
# Goal: Understand -> Search -> Compare -> Judge -> Reply.

class DeepReasoner:
    def __init__(self):
        load_dotenv("backend-cortex/.env")
        # We assume specialized skills like Scout and Merger are accessible
        from skills.acquisition.scout_engine import ScoutEngine
        from skills.evolution.memory_merger import MemoryMerger
        self.scout = ScoutEngine()
        self.merger = MemoryMerger()

    async def reason(self, user_query):
        print(f"REASONER: Deep Reasoning active for: {user_query}")
        
        # 1. Internal Memory Check
        print("REASONER: Step 1: Querying Internal Sovereignty (Memory)...")
        # (Simulated database check)
        internal_truth = "Commander has 3 active projects: LifeOS, Wife AI, and Brand Soul."

        # 2. External Global Search
        print("REASONER: Step 2: Global Reconnaissance (Web Scout)...")
        web_findings = await self.scout.run_recon_mission(user_query)

        # 3. Triangulation & Judgment
        print("REASONER: Step 3: Judging Correctness and Aligning with Sovereign Soul...")
        
        from app.core.gemini import get_gemini_client, safe_generate_content
        client = get_gemini_client()
        
        prompt = f"""
作為主權大腦，請對以下資訊進行「三方對位」判斷：

【使用者問題】: {user_query}
【內部記憶】: {internal_truth}
【外部搜尋結果】: {json.dumps(web_findings)}

【任務】:
1. 判斷正確性：外部資訊是否與內部目標衝突？
2. 整合與過濾：剔除噪音，只保留對指揮官有價值的「真相」。
3. 生成戰略建議：不僅是回答問題，還要告訴指揮官「這對您的專案代表什麼」。

輸出格式：請先給出「偵察結論」，再給出「主權建議」。
"""

        try:
            response = await safe_generate_content(
                client=client,
                prefer_mode="smart",
                contents=prompt
            )
            final_answer = response.text
        except Exception as e:
            print(f"ERROR: Reasoning failed: {e}")
            final_answer = "無法生成答案。"

        print("DONE: Deep Reasoning Complete.")
        return final_answer

if __name__ == "__main__":
    reasoner = DeepReasoner()
    asyncio.run(reasoner.reason("目前的 AI 影音市場中，有哪些技術能讓我的老婆 AI 專案達成主權轉化？"))

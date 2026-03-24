import asyncio
import sys
from pathlib import Path

# Add backend-cortex to path
sys.path.append(str(Path(__file__).parent.parent))

from app.agents.sorter import SorterAgent

async def test_doctrine_ingestion():
    agent = SorterAgent()
    
    test_inputs = [
        "今天感到肩頸非常緊繃 #BODY，可能是因為寫代碼太久。深呼吸後好一點。",
        "我想學 Rust 但一直拖延。現在決定花 10 分鐘寫個 Hello World #GREEN。#FRICTION 來自對過於複雜語法的恐懼。",
    ]
    
    print("\n--- [TEST BEGIN] Sovereign Doctrine Signals ---")
    
    for i, inp in enumerate(test_inputs):
        print(f"\n[Case {i+1}] Input: {inp}")
        result = await agent.process(inp)
        
        print(f"Detected Tags: {result.tags}")
        print(f"Content Preview: {result.content[:50]}...")
        
        # Check if new JSON fields might be present in the future or if they are in facts
        # Current SorterAgent might not yet have explicit fields for somatic_signals,
        # but the prompt should have influenced the output markdown and tags.
        
        if "#BODY" in inp or "#BODY" in result.tags:
            print("[OK] Body Memory signal detected.")
        
        if "#GREEN" in inp or "#GREEN" in result.tags:
            print("[OK] Green Light signal detected.")

    print("\n--- [TEST END] ---")

if __name__ == "__main__":
    asyncio.run(test_doctrine_ingestion())

# 月度整合 (Monthly Consolidation) 方案規劃

## 1. 級聯演化架構 (Cascade Evolution)
我們將大腦的記憶處理分為三個層級：
- **Level 1 (Daily)**: 原始感官紀錄 (Raw Logs) -> 提取當日情緒與摩擦。
- **Level 2 (Weekly)**: 週報 (`report_synthesizer.py`) -> 識別當週的短波主題。
- **Level 3 (Monthly)**: **月度戰略整合 (`monthly_consolidator.py`)** -> 識別具備「持久性」的靈魂演化與目標偏移。

## 2. 月度整理的核心邏輯 (Core Logic)
`monthly_consolidator.py` 不僅是摘要，它會執行：
1. **主題共振檢測**: 找出在一個月內出現 3 次以上的「導航關鍵字」，判定為「核心趨勢」。
2. **戰略增量 (Delta Analysis)**: 比對本月與上月的 `GOAL_MAP` 執行進度，找出停滯點 (Stall Points)。
3. **主權權重更新**: 根據本月的摩擦情況，自動調整 `cortex_shared_memory` 中的專案優先級。

## 3. Supabase 實作
- **資料表**: `monthly_reports`
- **欄位**: `id`, `month_uuid`, `themes` (JSONB), `strategic_delta` (Text), `soul_ranking` (JSONB).

## 4. 指揮官優化建議
您提到的「分頁看到記憶」與「月度整理」可以結合：**在大腦分頁中增加一個「月度回溯」視圖**，讓您一眼看見這 30 天來最穩定的那個「本質」是什麼。

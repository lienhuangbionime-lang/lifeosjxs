# backend-cortex/app/subconscious/evolution.py
"""
Evolution Agent: 掃描可用 Gemini 模型、篩選升級候選、沙盒測試結構化輸出相容性。
僅回傳掃描報告，不寫入 .env。
"""
import json
import re
import requests
import time
from typing import Any, List, Dict, Optional, Tuple

from app.core.config import settings
from app.models.gemini import LogAnalysisResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _list_models_via_rest() -> List[Dict[str, Any]]:
    """使用 REST API 取得所有模型列表。"""
    url = "https://generativelanguage.googleapis.com/v1beta/models"
    resp = requests.get(url, params={"key": settings.GEMINI_API_KEY}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data.get("models") or []


def _supports_generate_content(model: Dict[str, Any]) -> bool:
    """是否支援 generateContent。"""
    methods = model.get("supportedGenerationMethods") or []
    return "generateContent" in methods


def _name_contains_gemini(name: str) -> bool:
    """模型名稱是否包含 gemini。"""
    return "gemini" in (name or "").lower()


def _parse_version(model_name: str) -> tuple[int, ...]:
    """
    從模型名稱抽出版本號便於比較，例如:
    models/gemini-2.5-flash -> (2, 5)
    models/gemini-2.0-flash -> (2, 0)
    """
    # 預期格式: models/gemini-2.5-flash 或 gemini-2.5-flash
    name = (model_name or "").split("/")[-1]
    match = re.search(r"gemini-([\d.]+)", name, re.I)
    if not match:
        return (0,)
    parts = [int(p) for p in match.group(1).split(".") if p.isdigit()]
    return tuple(parts) if parts else (0,)


def _is_newer_than(candidate_name: str, current: str) -> bool:
    """簡單版本比較：候選模型版本是否比 current 新（嚴格大於）。"""
    v_c = _parse_version(current)
    v_n = _parse_version(candidate_name)
    return v_n > v_c


def _run_level1_test(model_name: str) -> Tuple[bool, Optional[str]]:
    """
    Level 1 (Basic): 僅發送簡單文字 Prompt，不帶 responseSchema。
    驗證模型能否正常 respond。
    回傳 (passed, error_message)。
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": settings.GEMINI_API_KEY}
    payload = {
        "contents": [{"parts": [{"text": "Reply with exactly: OK"}]}],
        "generationConfig": {"temperature": 0},
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        text = (data.get("candidates") or [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")
        if not text or "OK" not in (text or ""):
            return (False, "Empty or unexpected response")
        return (True, None)
    except Exception as e:
        return (False, str(e))


def _run_level2_test(model_name: str) -> Tuple[bool, Optional[str]]:
    """
    Level 2 (Advanced): 帶 Pydantic Schema 的結構化輸出測試。
    通過才視為完整相容、可列入 recommended_upgrade。
    回傳 (passed, error_message)。
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": settings.GEMINI_API_KEY}
    schema = LogAnalysisResult.model_json_schema()
    payload = {
        "contents": [{"parts": [{"text": "Test payload. Respond with strict JSON."}]}],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
            "responseSchema": schema,
        },
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        text = (data.get("candidates") or [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")
        if not text:
            return (False, "Empty response text")
        parsed = json.loads(text)
        LogAnalysisResult.model_validate(parsed)
        return (True, None)
    except Exception as e:
        return (False, str(e))


# ---------------------------------------------------------------------------
# Evolution Agent
# ---------------------------------------------------------------------------

def _sort_by_priority(candidates: List[str]) -> List[str]:
    """優先 flash 系列，再 pro 系列。"""
    def key(name: str) -> int:
        n = (name or "").lower()
        if "flash" in n:
            return 0
        if "pro" in n:
            return 1
        return 2
    return sorted(candidates, key=key)


def run_evolution_scan() -> Dict[str, Any]:
    """
    執行一次進化掃描並回傳報告。
    不回寫 .env，僅回傳結果供上層或 System API 使用。
    """
    current_model = settings.MODEL_SMART
    current_for_api = current_model if current_model.startswith("models/") else f"models/{current_model}"

    report: Dict[str, Any] = {
        "current_model": current_model,
        "available_upgrades": [],
        "tested_candidates": [],
        "recommended_upgrade": None,
        "error_log": None,
    }

    try:
        models = _list_models_via_rest()
    except Exception as e:
        report["scan_error"] = str(e)
        report["error_log"] = str(e)
        return report

    # 篩選：支援 generateContent、名稱含 gemini、版本比當前新
    candidates = []
    for m in models:
        name = m.get("name") or ""
        short = name.replace("models/", "") if name.startswith("models/") else name
        if not _supports_generate_content(m) or not _name_contains_gemini(name):
            continue
        if _is_newer_than(name, current_for_api):
            candidates.append(short)

    report["available_upgrades"] = sorted(candidates)
    # 優先測試 flash，再測試 pro
    ordered = _sort_by_priority(candidates)

    for model_name in ordered:
        # Level 1: 簡單文字，無 Schema
        l1_passed, l1_err = _run_level1_test(model_name)
        if not l1_passed:
            report["tested_candidates"].append({
                "model": model_name,
                "passed": False,
                "partial_compatibility": False,
                "error": l1_err,
            })
            time.sleep(5)
            continue
        # Level 2: 帶 Schema 的結構化輸出
        l2_passed, l2_err = _run_level2_test(model_name)
        if l2_passed:
            report["tested_candidates"].append({
                "model": model_name,
                "passed": True,
                "partial_compatibility": False,
                "error": None,
            })
            report["recommended_upgrade"] = model_name
            break
        # Level 1 通過、Level 2 失敗 → 部分相容
        report["tested_candidates"].append({
            "model": model_name,
            "passed": False,
            "partial_compatibility": True,
            "error": l2_err,
        })
        time.sleep(5)

    return report


def check_for_upgrades() -> Dict[str, Any]:
    """
    排程用主函式：執行進化掃描並記錄結果（不寫入 .env）。
    供 subconscious.scheduler 每 24 小時呼叫；System API 可回傳此報告。
    """
    report = run_evolution_scan()
    # 僅記錄，實際寫入 .env 由 System API 處理
    if report.get("scan_error"):
        print(f"[Evolution] Scan error: {report['scan_error']}")
    elif report.get("available_upgrades"):
        print(f"[Evolution] Available upgrades: {report['available_upgrades']}, recommended={report.get('recommended_upgrade')}")
    else:
        print("[Evolution] No upgrades available.")
    return report

# backend-cortex/app/subconscious/evolution.py
"""
Evolution Agent: ?ƒæ??¯ç”¨ Gemma æ¨¡å??ç¯©?¸å?ç´šå€™é¸?æ??’æ¸¬è©¦ç?æ§‹å?è¼¸å‡º?¸å®¹?§ã€?
?…å??³æ??å ±?Šï?ä¸å¯«??.env??
"""
import json
import re
import requests
import time
from typing import Any, List, Dict, Optional, Tuple

from app.core.config import settings
from app.models.gemma import LogAnalysisResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _list_models_via_rest() -> List[Dict[str, Any]]:
    """ä½¿ç”¨ REST API ?–å??€?‰æ¨¡?‹å?è¡¨ã€?""
    url = "https://generativelanguage.googleapis.com/v1beta/models"
    resp = requests.get(url, params={"key": settings.GEMMA_API_KEY}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data.get("models") or []


def _supports_generate_content(model: Dict[str, Any]) -> bool:
    """?¯å¦?¯æ´ generateContent??""
    methods = model.get("supportedGenerationMethods") or []
    return "generateContent" in methods


def _name_contains_gemma(name: str) -> bool:
    """æ¨¡å??ç¨±?¯å¦?…å« gemma??""
    return "gemma" in (name or "").lower()


def _parse_version(model_name: str) -> tuple[int, ...]:
    """
    å¾æ¨¡?‹å?ç¨±æŠ½?ºç??¬è?ä¾¿æ–¼æ¯”è?ï¼Œä?å¦?
    models/gemma-2.5-flash -> (2, 5)
    models/gemma-2.0-flash -> (2, 0)
    """
    # ?æ??¼å?: models/gemma-2.5-flash ??gemma-2.5-flash
    name = (model_name or "").split("/")[-1]
    match = re.search(r"gemma-([\d.]+)", name, re.I)
    if not match:
        return (0,)
    parts = [int(p) for p in match.group(1).split(".") if p.isdigit()]
    return tuple(parts) if parts else (0,)


def _is_newer_than(candidate_name: str, current: str) -> bool:
    """ç°¡å–®?ˆæœ¬æ¯”è?ï¼šå€™é¸æ¨¡å??ˆæœ¬?¯å¦æ¯?current ?°ï??´æ ¼å¤§æ–¼ï¼‰ã€?""
    v_c = _parse_version(current)
    v_n = _parse_version(candidate_name)
    return v_n > v_c


def _run_level1_test(model_name: str) -> Tuple[bool, Optional[str]]:
    """
    Level 1 (Basic): ?…ç™¼?ç°¡?®æ?å­?Promptï¼Œä?å¸?responseSchema??
    é©—è?æ¨¡å??½å¦æ­?¸¸ respond??
    ?å‚³ (passed, error_message)??
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": settings.GEMMA_API_KEY}
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
    Level 2 (Advanced): å¸?Pydantic Schema ?„ç?æ§‹å?è¼¸å‡ºæ¸¬è©¦??
    ?šé??è??ºå??´ç›¸å®¹ã€å¯?—å…¥ recommended_upgrade??
    ?å‚³ (passed, error_message)??
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": settings.GEMMA_API_KEY}
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
    """?ªå? flash ç³»å?ï¼Œå? pro ç³»å???""
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
    ?·è?ä¸€æ¬¡é€²å??ƒæ?ä¸¦å??³å ±?Šã€?
    ä¸å?å¯?.envï¼Œå??å‚³çµæ?ä¾›ä?å±¤æ? System API ä½¿ç”¨??
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

    # ç¯©é¸ï¼šæ”¯??generateContent?å?ç¨±å« gemma?ç??¬æ??¶å???
    candidates = []
    for m in models:
        name = m.get("name") or ""
        short = name.replace("models/", "") if name.startswith("models/") else name
        if not _supports_generate_content(m) or not _name_contains_gemma(name):
            continue
        if _is_newer_than(name, current_for_api):
            candidates.append(short)

    report["available_upgrades"] = sorted(candidates)
    # ?ªå?æ¸¬è©¦ flashï¼Œå?æ¸¬è©¦ pro
    ordered = _sort_by_priority(candidates)

    for model_name in ordered:
        # Level 1: ç°¡å–®?‡å?ï¼Œç„¡ Schema
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
        # Level 2: å¸?Schema ?„ç?æ§‹å?è¼¸å‡º
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
        # Level 1 ?šé??Level 2 å¤±æ? ???¨å??¸å®¹
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
    ?’ç??¨ä¸»?½å?ï¼šåŸ·è¡Œé€²å??ƒæ?ä¸¦è??„ç??œï?ä¸å¯«??.envï¼‰ã€?
    ä¾?subconscious.scheduler æ¯?24 å°æ??¼å«ï¼›System API ?¯å??³æ­¤?±å???
    """
    report = run_evolution_scan()
    # ?…è??„ï?å¯¦é?å¯«å…¥ .env ??System API ?•ç?
    if report.get("scan_error"):
        print(f"[Evolution] Scan error: {report['scan_error']}")
    elif report.get("available_upgrades"):
        print(f"[Evolution] Available upgrades: {report['available_upgrades']}, recommended={report.get('recommended_upgrade')}")
    else:
        print("[Evolution] No upgrades available.")
    return report

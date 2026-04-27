"""
app/services/scoring_engine.py
Objective fact-based score validation engine.
Compares AI-generated mood/focus/energy scores against fact-detected evidence.
If divergence > threshold, logs to cortex_growth_logs as a calibration event.
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger("cortex.scoring_engine")

DIVERGENCE_THRESHOLD = 2.0  # If AI score differs by more than this, it's a bias event


class PatternEvaluator:
    """Detects behavioral patterns and risks across multiple days."""

    def evaluate_focus_risk(self, score_history: List[float]):
        if len(score_history) < 3:
            return None
        if all(s < 4 for s in score_history[-3:]):
            return {
                "pattern": "focus_degradation",
                "risk_level": "high",
                "evidence": score_history[-3:],
                "message": "è­¦å?ï¼šå?æ³¨åº¦å·²é€??ä¸‰å¤©?•æ–¼ä½Žè°·?‚å»ºè­°å??•ç’°å¢ƒæ??†æ?ä»»å?ç°¡å?ç¨‹å???
            }
        return None


class ScoringEngine:
    """
    Objective scoring engine for LifeOS.
    Takes observed facts and outputs a structured score with evidence.
    """
    def __init__(self):
        self.pattern_evaluator = PatternEvaluator()

    FOCUS_WEIGHTS = {
        "deep_work_session": 2.0,
        "completed_milestone": 3.0,
        "distraction_event": -1.5,
        "task_switching": -1.0,
        "procrastination_mention": -2.5,
        "external_interruption": -0.5
    }

    ENERGY_WEIGHTS = {
        "sleep_hours_over_7": 2.0,
        "regular_exercise": 1.5,
        "healthy_meal": 1.0,
        "work_overtime": -2.0,
        "physical_pain": -2.0,
        "caffeine_crash": -1.5
    }

    def calculate_score(self, category: str, facts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate a score (0-10) based on identified facts."""
        base_score = 5.0
        weights = getattr(self, f"{category.upper()}_WEIGHTS", {})
        calculation_log = []
        total_delta = 0.0

        for fact in facts:
            fact_type = fact.get("type")
            count = fact.get("count", 1)
            weight = weights.get(fact_type, 0.0)
            if weight != 0:
                delta = float(weight * count)
                total_delta += delta
                calculation_log.append({
                    "fact": fact_type,
                    "delta": delta,
                    "evidence": fact.get("evidence", "")
                })

        final_score = max(0.0, min(10.0, base_score + total_delta))
        return {
            "score": round(final_score, 1),
            "calculation_log": calculation_log,
            "summary": f"Based on {len(calculation_log)} facts, {category} score = {round(final_score, 1)}."
        }

    def analyze_trends(self, score_history: List[float]):
        return self.pattern_evaluator.evaluate_focus_risk(score_history)

    def validate_ai_scores(
        self,
        ai_mood: float,
        ai_focus: float,
        ai_energy: float,
        content: str
    ) -> Dict[str, Any]:
        """
        [Phase D] Simple heuristic validation of AI-assigned scores.
        Extracts keyword signals from content and checks if AI scores are plausible.
        Returns divergence report.
        """
        # Heuristic keyword facts from content
        content_lower = content.lower()
        focus_facts = []
        energy_facts = []

        # Focus signals
        if any(w in content_lower for w in ["å°ˆæ³¨", "deep work", "å®Œæ?", "finished", "milestone"]):
            focus_facts.append({"type": "deep_work_session", "count": 1})
        if any(w in content_lower for w in ["?†å?", "?–å»¶", "procrastinate", "distracted"]):
            focus_facts.append({"type": "procrastination_mention", "count": 1})

        # Energy signals
        if any(w in content_lower for w in ["?¡å¥½", "?¡ç??…è¶³", "?¡ä?", "7å°æ?", "8å°æ?"]):
            energy_facts.append({"type": "sleep_hours_over_7", "count": 1})
        if any(w in content_lower for w in ["? ç­", "overtime", "ç´?, "?²æ?", "exhausted"]):
            energy_facts.append({"type": "work_overtime", "count": 1})
        if any(w in content_lower for w in ["?‹å?", "exercise", "gym", "workout"]):
            energy_facts.append({"type": "regular_exercise", "count": 1})

        engine_focus = self.calculate_score("focus", focus_facts)["score"] if focus_facts else None
        engine_energy = self.calculate_score("energy", energy_facts)["score"] if energy_facts else None

        divergences = []
        if engine_focus is not None:
            diff = abs(ai_focus - engine_focus)
            if diff > DIVERGENCE_THRESHOLD:
                divergences.append({
                    "metric": "focus",
                    "ai_score": ai_focus,
                    "engine_score": engine_focus,
                    "delta": round(diff, 1),
                    "note": "AI focus score may be biased"
                })
        if engine_energy is not None:
            diff = abs(ai_energy - engine_energy)
            if diff > DIVERGENCE_THRESHOLD:
                divergences.append({
                    "metric": "energy",
                    "ai_score": ai_energy,
                    "engine_score": engine_energy,
                    "delta": round(diff, 1),
                    "note": "AI energy score may be biased"
                })

        return {
            "has_divergence": len(divergences) > 0,
            "divergences": divergences,
            "engine_focus": engine_focus,
            "engine_energy": engine_energy,
        }


# Singleton
scoring_engine = ScoringEngine()

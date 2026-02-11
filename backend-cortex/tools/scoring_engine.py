import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger("cortex.scoring_engine")

class PatternEvaluator:
    """
    Detects behavioral patterns and risks across multiple days.
    """
    def evaluate_focus_risk(self, score_history: List[float]):
        if len(score_history) < 3:
            return None

        # Detect persistent low focus (below 4 for 3 consecutive days)
        if all(s < 4 for s in score_history[-3:]):
            return {
                "pattern": "focus_degradation",
                "risk_level": "high",
                "evidence": score_history[-3:],
                "message": "警告：專注度已連續三天處於低谷。建議啟動環境清理或任務簡化程序。"
            }
        return None

class ScoringEngine:
    """
    Objective scoring engine for LifeOS.
    Takes observed facts and outputs a structured score with evidence.
    """
    def __init__(self):
        self.pattern_evaluator = PatternEvaluator()

    # Default weights for facts - AI can eventually propose updates to these
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
        """
        Calculate a score (0-10) based on identified facts.
        """
        base_score = 5.0  # Start at middle ground
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
            "summary": f"Based on {len(calculation_log)} identified facts, {category} score set to {round(final_score, 1)}."
        }

    def analyze_trends(self, score_history: List[float]):
        """Analyze history for risks using PatternEvaluator"""
        return self.pattern_evaluator.evaluate_focus_risk(score_history)

# Singleton instance
engine = ScoringEngine()

if __name__ == "__main__":
    # Test execution
    test_facts = [
        {"type": "deep_work_session", "count": 2, "evidence": "Implemented scoring engine"},
        {"type": "distraction_event", "count": 1, "evidence": "Checked emails for 20 mins"}
    ]
    result = engine.calculate_score("focus", test_facts)
    print("Daily Score Result:")
    print(json.dumps(result, indent=2))

    # Test Pattern Evaluation
    history = [3.2, 2.5, 3.8] # 3 days of low focus
    risk = engine.analyze_trends(history)
    if risk:
        print("\n[ALERT] Risk Pattern Detected:")
        print(json.dumps(risk, indent=2))

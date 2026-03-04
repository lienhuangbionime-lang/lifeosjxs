import datetime
import math

def calculate_decay_score(raw_similarity: float, access_count: int, last_accessed_at: datetime.datetime, current_time: datetime.datetime = None) -> float:
    """
    LifeOS Knowledge Decay Formula (Phase E)
    Adjusts the raw pgvector cosine similarity score based on time elapsed and retrieval frequency.
    """
    if current_time is None:
        current_time = datetime.datetime.now(datetime.timezone.utc)
        
    # 1. Calculate time decay penalty (Half-life based)
    # Let's say baseline half-life is 30 days.
    base_half_life_days = 30
    
    # Each time a memory is accessed, its "survival capability" increases.
    # We extend the half-life by 7 days for every access, up to a max of 365 days.
    effective_half_life = min(365, base_half_life_days + (access_count * 7))
    
    # Calculate days since last access
    if last_accessed_at is None:
        days_elapsed = 0
    else:
        # If it's a naive datetime, assume UTC for the simulation
        if last_accessed_at.tzinfo is None:
            last_accessed_at = last_accessed_at.replace(tzinfo=datetime.timezone.utc)
        
        delta = current_time - last_accessed_at
        days_elapsed = max(0, delta.total_seconds() / 86400.0)
    
    # Exponential decay formula: N(t) = N0 * (1/2)^(t/h)
    decay_multiplier = math.pow(0.5, days_elapsed / effective_half_life)
    
    # 2. Access Frequency Boost
    # Add a tiny flat semantic boost for highly accessed items (Max +0.05 to similarity)
    # This ensures frequently used items always float to the top of identical semantic matches
    frequency_boost = min(0.05, access_count * 0.005)
    
    # 3. Final Score
    final_score = (raw_similarity * decay_multiplier) + frequency_boost
    
    # Ensure it stays within reasonable bounds [0, 1] roughly
    return max(0.0, min(1.0, final_score))

if __name__ == "__main__":
    print("--- LifeOS Sandbox: Knowledge Decay Simulation ---\n")
    
    now = datetime.datetime.now(datetime.timezone.utc)
    test_cases = [
        {"name": "Brand New Memory (High Sim)", "sim": 0.85, "access": 0, "days_ago": 0},
        {"name": "1 Month Old, Never Accessed", "sim": 0.85, "access": 0, "days_ago": 30},
        {"name": "6 Months Old, Never Accessed", "sim": 0.85, "access": 0, "days_ago": 180},
        {"name": "6 Months Old, Accessed 20 times", "sim": 0.85, "access": 20, "days_ago": 180},
        {"name": "1 Year Old, Accessed 50 times", "sim": 0.85, "access": 50, "days_ago": 365},
    ]
    
    print(f"{'Memory State':<35} | {'Raw Sim':<8} | {'Final Score':<12} | {'Decay %':<10}")
    print("-" * 75)
    
    for tc in test_cases:
        last_access = now - datetime.timedelta(days=tc["days_ago"])
        final_score = calculate_decay_score(tc["sim"], tc["access"], last_access, now)
        decay_pct = (1.0 - (final_score / tc["sim"])) * 100 if tc["sim"] > 0 else 0
        
        # If score went UP because of frequency boost, show as negative decay (Boost)
        if final_score > tc["sim"]:
            decay_str = f"+{(final_score/tc['sim'] - 1)*100:.1f}% Boost"
        else:
            decay_str = f"-{decay_pct:.1f}%"
            
        print(f"{tc['name']:<35} | {tc['sim']:<8.3f} | {final_score:<12.3f} | {decay_str:<10}")
        
    print("\nConclusion: The half-life formula successfully drops forgotten memories' scores, while protecting frequently accessed ones.")

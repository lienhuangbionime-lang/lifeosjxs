
import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime

logger = logging.getLogger("cortex.model_discovery")

class ModelDiscoveryService:
    """
    Autonomous Model Discovery & Validation Service (v3.9).
    Detects available Gemini models, runs sandbox health tests, and maintains a verified registry.
    """
    
    def __init__(self, registry_path: str = None):
        if not registry_path:
            # v5.6 Standard Path - Up to lifeosjxs/
            root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            self.registry_path = os.path.join(root, "sync_brain", "model_registry.json")
        else:
            self.registry_path = registry_path
            
        self.verified_models: Dict[str, List[str]] = {"fast": [], "smart": []}
        self.pending_models: Dict[str, List[str]] = {"fast": [], "smart": []}
        self.quota_exhausted: Dict[str, List[str]] = {"fast": [], "smart": []}
        self.last_discovery: Optional[str] = None
        self._load_registry()

    def _load_registry(self):
        """Load the verified model registry from disk with flat-list fallback."""
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    raw_verified = data.get("verified_models", [])
                    
                    # Handle flat list from test.py probe
                    if isinstance(raw_verified, list):
                        self.verified_models["fast"] = [m for m in raw_verified if "lite" in m or "flash" in m]
                        self.verified_models["smart"] = [m for m in raw_verified if "pro" in m or "3" in m]
                    else:
                        self.verified_models = raw_verified
                        
                    # Handle exhausted models list
                    raw_exhausted = data.get("quota_exhausted", [])
                    if isinstance(raw_exhausted, list):
                        self.quota_exhausted["fast"] = [m for m in raw_exhausted if "lite" in m or "flash" in m]
                        self.quota_exhausted["smart"] = [m for m in raw_exhausted if "pro" in m or "3" in m]
                    else:
                        self.quota_exhausted = raw_exhausted

                    self.pending_models = data.get("pending_models", {"fast": [], "smart": []})
                    self.last_discovery = data.get("last_discovery") or data.get("last_updated") or data.get("timestamp")
                logger.info(f"[OK] Loaded model registry: {len(self.verified_models['fast'])} fast, {len(self.verified_models['smart'])} smart. Pending: {len(self.pending_models['fast'])} fast, {len(self.pending_models['smart'])} smart")
            except Exception as e:
                logger.error(f"[ERROR] Failed to load model registry: {e}")

    def _save_registry(self):
        """Persist the verified model registry to disk."""
        try:
            os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump({
                    "verified_models": self.verified_models,
                    "pending_models": self.pending_models,
                    "last_discovery": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"[OK] Persisted model registry to {self.registry_path}")
        except Exception as e:
            logger.error(f"[ERROR] Failed to save model registry: {e}")

    def approve_models(self):
        """Move models from pending to verified status."""
        if not self.pending_models["fast"] and not self.pending_models["smart"]:
            return False
            
        # Merge or replace? Let's favor new verified ones at the top
        new_fast = self.pending_models["fast"] + [m for m in self.verified_models["fast"] if m not in self.pending_models["fast"]]
        new_smart = self.pending_models["smart"] + [m for m in self.verified_models["smart"] if m not in self.pending_models["smart"]]
        
        self.verified_models["fast"] = list(new_fast)
        self.verified_models["smart"] = list(new_smart)
        self.pending_models = {"fast": [], "smart": []}
        self._save_registry()
        return True

    async def discover_and_verify(self, client: Any):
        """
        Main entry point: List models from API and run sandbox verification.
        """
        if not client:
            logger.warning("[WARN] No Gemini client provided for discovery")
            return

        logger.info("🔭 Starting autonomous model discovery...")
        
        discovered_fast = []
        discovered_smart = []

        try:
            # 1. List all available models
            for m in client.models.list():
                name = m.name
                if "flash" in name.lower():
                    discovered_fast.append(name)
                elif "pro" in name.lower():
                    discovered_smart.append(name)
            
            logger.info(f"Discovered {len(discovered_fast)} flash models and {len(discovered_smart)} pro models.")

            # 2. Preference Ranking (Newest/Known High-Perf first)
            # This is a heuristic based on string versioning
            discovered_fast.sort(key=self._rank_score, reverse=True)
            discovered_smart.sort(key=self._rank_score, reverse=True)

            # 3. Sandbox Verification (Test top 3 of each)
            verified_fast = await self._verify_group(client, list(discovered_fast[:3]))
            verified_smart = await self._verify_group(client, list(discovered_smart[:3]))

            # Logic Change: New models go to PENDING first for user report
            # If they are already verified, don't re-pending them
            new_pending_fast = [m for m in verified_fast if m not in self.verified_models["fast"]]
            new_pending_smart = [m for m in verified_smart if m not in self.verified_models["smart"]]

            if new_pending_fast or new_pending_smart:
                self.pending_models["fast"] = new_pending_fast
                self.pending_models["smart"] = new_pending_smart
                self._save_registry()
                logger.info(f"✨ Found {len(new_pending_fast) + len(new_pending_smart)} new compatible models. Awaiting user approval.")
            else:
                logger.info("☀️ No new models to report. Current verified set is up-to-date.")

        except Exception as e:
            logger.error(f"[ERROR] Discovery process failed: {e}")

    def _rank_score(self, model_name: str) -> float:
        """Heuristic to rank models higher if they are stable or newer versions."""
        score = 0.0
        # Stability over Novelty for Production
        if "1.5-flash" in model_name: score += 80 # Highly stable GA
        elif "2.0-flash" in model_name and "lite" not in model_name: score += 90 # Fast & stable
        elif "3.1" in model_name: score += 100 # Newest
        elif "3.0" in model_name: score += 70
        elif "2.0" in model_name: score += 50
        
        # Penalties for high-demand experimental tiers
        if "lite" in model_name: score -= 30 
        if "preview" in model_name: score -= 20
        
        return score

    async def _verify_group(self, client: Any, models: List[str]) -> List[str]:
        """Test a list of models and return only those that pass."""
        verified = []
        for model_id in models:
            if await self._sandbox_test(client, model_id):
                verified.append(model_id)
        return verified

    async def _sandbox_test(self, client: Any, model_id: str) -> bool:
        """Run a minimal generation test (Sandbox heartbeat)."""
        try:
            # Using absolute minimal prompt
            response = await client.aio.models.generate_content(
                model=model_id,
                contents="hi",
                config={"max_output_tokens": 5}
            )
            if response and response.text:
                logger.info(f"[PASS] Sandbox Test: {model_id}")
                return True
            return False
        except Exception as e:
            logger.warning(f"[FAIL] Sandbox Test: {model_id} - {e}")
            return False

    def get_best_model(self, mode: Literal["fast", "smart"] = "fast") -> str:
        """Returns the top verified model for the requested mode. Empty string if none available."""
        # [v5.6] Lazy Reload: if memory is empty, try reloading from disk once
        if not self.verified_models.get(mode):
            self._load_registry()
            
        models = self.verified_models.get(mode, [])
        if models:
            return models[0]
        return ""  # Caller handles fallback; no hardcoded default here

# Singleton instance
model_discovery = ModelDiscoveryService()

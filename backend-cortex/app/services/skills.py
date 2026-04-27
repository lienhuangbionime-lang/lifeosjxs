import os
import yaml
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger("cortex.skills")

class SkillOrchestrator:
    def __init__(self, skills_dir: str = None):
        if skills_dir is None:
            # Default to relative path from backend root
            self.skills_dir = Path("skills")
            if not self.skills_dir.exists():
                # Try absolute path fallback for Windows
                self.skills_dir = Path(r"C:\Users\lien.huang\AppData\lifeosjxs\backend-cortex\skills")
        else:
            self.skills_dir = Path(skills_dir)
        
        logger.info(f"[SKILLS] Initialized with directory: {self.skills_dir}")

    def get_available_skills(self) -> List[Dict]:
        """Scans the directory and returns metadata for all SKILL.md files."""
        skills = []
        if not self.skills_dir.exists():
            return []
            
        for skill_path in self.skills_dir.glob("*/SKILL.md"):
            try:
                with open(skill_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # Parse Frontmatter (simple YAML block)
                metadata = self._parse_frontmatter(content)
                if metadata:
                    metadata["id"] = skill_path.parent.name
                    skills.append(metadata)
            except Exception as e:
                logger.error(f"[SKILLS] Failed to parse {skill_path}: {e}")
                
        return skills

    def get_skill_protocol(self, skill_id: str) -> Optional[str]:
        """Returns the full protocol (Markdown) for a specific skill."""
        skill_path = self.skills_dir / skill_id / "SKILL.md"
        if not skill_path.exists():
            return None
            
        try:
            with open(skill_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Remove frontmatter for the final prompt injection
            clean_content = re.sub(r"---.*?---", "", content, flags=re.DOTALL).strip()
            return clean_content
        except Exception as e:
            logger.error(f"[SKILLS] Failed to read skill {skill_id}: {e}")
            return None

    def _parse_frontmatter(self, content: str) -> Optional[Dict]:
        """Extracts YAML frontmatter from Markdown."""
        match = re.search(r"^---(.*?)---", content, re.DOTALL)
        if match:
            try:
                return yaml.safe_load(match.group(1))
            except Exception:
                return None
        return None

    def find_relevant_skills(self, query: str) -> List[str]:
        """
        Heuristic: Detect if the user query suggests specific skill usage.
        For now, we use simple keyword mapping.
        """
        # Mapping keywords to skill IDs
        keyword_map = {
            "?çÊÄ?: "reflection",
            "reflection": "reflection",
            "?ÜÊ?": "reflection",
            "?™Â?": "database-optimization",
            "optimize": "database-optimization",
            "‰∫§Êé•": "handoff",
            "handoff": "handoff",
            "?ãÁôº": "handoff",
            "dev": "handoff",
            "?úÂ?": "research",
            "?•‰?‰∏?: "research",
            "news": "research",
            "research": "research",
            "‰∏äÁ∂≤": "research",
            "?∏Â?": "core",
            "‰ªªÂ?": "core",
            "Â∞àÊ?": "core",
            "ÁÆ°Á?": "core",
            "task": "core",
            "project": "core",
            "done": "core",
            "todo": "core"
        }
        
        detected = []
        for kw, skill_id in keyword_map.items():
            if kw in query.lower():
                detected.append(skill_id)
        
        return list(set(detected))

# Global Instance
orchestrator = SkillOrchestrator()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill Bridge (V1.0)
==================
Centralized registry for semantic skill lookup.
Prevents entry points from breaking when internal folder structures change.
"""

from pathlib import Path
import sys

# Semantic to Physical Mapping
SKILL_MAP = {
    "MASHUP_CORE": "skills/mashup_intelligence/scripts/core.py",
    "CUEING_V3": "skills/cueing_intelligence/scripts/v3.py",
    "CUEING_PRO": "skills/cueing_intelligence/scripts/pro.py",
    "AUDIT_CORE": "skills/aesthetic_expert/scripts/audit.py",
    "CURATOR": "skills/aesthetic_expert/scripts/curator.py",
    "PHRASE_ENERGY": "skills/rhythmic_energy/scripts/phrase.py",
    "UNIFIED_CORE": "skills/general_tools/scripts/unified_core.py"
}

def get_skill_path(name: str) -> Path:
    """Return the absolute path for a semantic skill name."""
    rel_path = SKILL_MAP.get(name)
    if not rel_path:
        raise ValueError(f"Unknown skill: {name}")
    return Path("d:/anti") / rel_path

class SkillBridge:
    """Dynamic Loader for standardized skills."""
    
    @staticmethod
    def get_mashup_intelligence():
        from skills.mashup_intelligence.scripts.core import MashupIntelligence
        return MashupIntelligence

    @staticmethod
    def get_cueing_v3():
        from skills.cueing_intelligence.scripts.v3 import generate_intelligent_cues_v3
        return generate_intelligent_cues_v3

    @staticmethod
    def get_audit_core():
        from skills.aesthetic_expert.scripts.audit import ProfessionalAudit
        return ProfessionalAudit

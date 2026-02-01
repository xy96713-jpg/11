#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill Bridge (V12.0 Singularity)
================================
The UNIQUE entrance for all semantic skill actions.
Eliminates architectural sprawl by enforcing a single interface for all skills.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# 1. 基础路径审计
BASE_DIR = Path("d:/anti")
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
    sys.path.insert(0, str(BASE_DIR / "skills"))
    sys.path.insert(0, str(BASE_DIR / "core"))

# --- [V13.0 Decoupling] 战略意图权重配置 ---
STRATEGIC_INTENTS = {
    "set": {
        "harmonic": 0.40,      # 宏观调性流向
        "bpm": 0.25,           # BPM 动态平滑
        "energy": 0.20,        # 能量曲线一致性
        "aesthetic": 0.10,     # 审美补正
        "mashup": 0.05         # Mashup 兼容性 (Set 模式下仅作为彩蛋)
    },
    "mashup": {
        "mashup": 0.45,        # Stems 对撞与 Mashup 兼容性
        "harmonic": 0.20,      # 基本调性
        "bpm": 0.15,           # 基本节奏
        "aesthetic": 0.10,     # 审美相似度
        "energy": 0.10         # 能量对等
    },
    "curator": {
        "aesthetic": 0.40,     # 审美、时代、文化一致性
        "narrative": 0.30,     # 叙事广度
        "harmonic": 0.15,
        "bpm": 0.10,
        "energy": 0.05
    }
}

class SkillBridge:
    """[Singularity] 唯一技能中轴线"""
    
    _instances = {}

    @classmethod
    def execute(cls, command: str, **kwargs) -> Any:
        print(f"🚀 [Singularity] SkillBridge routing command: {command}")
        
        # --- Mashup & Audio DNA ---
        if command == "calculate-mashup":
            return cls._get_mashup_engine().calculate_mashup_score(**kwargs)
        elif command == "get-mashup-archetype":
            return cls._get_mashup_engine().get_mashup_archetype(**kwargs)
        elif command == "map-dna":
            from audio_dna import map_dna_features
            return map_dna_features(**kwargs)
        elif command == "dna-affinity":
            from audio_dna import calculate_dna_affinity
            return calculate_dna_affinity(**kwargs)

        # --- Aesthetic & Audit ---
        elif command == "get-aesthetic-match":
            return cls._get_aesthetic_curator().calculate_aesthetic_match(**kwargs)
        elif command == "get-vibe":
            return cls._get_aesthetic_curator().get_track_vibe(**kwargs)
        elif command == "audit-completeness":
            from aesthetic_expert.scripts.audit import calculate_set_completeness
            return calculate_set_completeness(**kwargs)
        elif command == "get-energy-curve-summary":
            from aesthetic_expert.scripts.audit import get_energy_curve_summary
            return get_energy_curve_summary(**kwargs)

        # --- Narrative ---
        elif command == "calculate-narrative":
            return cls._get_set_planner().calculate_narrative_score(**kwargs)
        elif command == "get-narrative-advice":
            return cls._get_set_planner().get_narrative_advice(**kwargs)

        # --- Rhythmic & BPM ---
        elif command == "detect-vocals":
            from skills.cueing_intelligence.scripts.vocal import check_vocal_overlap_at_mix_point
            return check_vocal_overlap_at_mix_point(**kwargs)
        elif command == "check-phrase":
            from rhythmic_energy.scripts.phrase import check_phrase_alignment
            return check_phrase_alignment(**kwargs)
        elif command == "validate-energy":
            from rhythmic_energy.scripts.phrase import validate_energy_curve
            return validate_energy_curve(**kwargs)
        elif command == "validate-bpm":
            from rhythmic_energy.scripts.bpm import validate_bpm_progression
            return validate_bpm_progression(**kwargs)
            
        elif command == "get-strategy-weights":
            mode = kwargs.get("mode", "set").lower()
            return STRATEGIC_INTENTS.get(mode, STRATEGIC_INTENTS["set"])
            
        else:
            # Fallback for minor/legacy helpers as identity functions
            print(f"⚠️ [Singularity Warning] Routing '{command}' to identity fallback.")
            if "tracks" in kwargs: return kwargs["tracks"]
            return None

    # --- 内部引擎工厂 (Lazy Loading) ---

    @classmethod
    def _get_mashup_engine(cls):
        if "mashup" not in cls._instances:
            from mashup_intelligence.scripts.core import MashupIntelligence
            cls._instances["mashup"] = MashupIntelligence()
        return cls._instances["mashup"]

    @classmethod
    def _get_aesthetic_curator(cls):
        if "curator" not in cls._instances:
            from aesthetic_expert.scripts.curator import AestheticCurator
            cls._instances["curator"] = AestheticCurator()
        return cls._instances["curator"]

    @classmethod
    def _get_set_planner(cls):
        if "planner" not in cls._instances:
            from set_curation_expert.narrative_set_planner import NarrativePlanner
            cls._instances["planner"] = NarrativePlanner()
        return cls._instances["planner"]

if __name__ == "__main__":
    print("🏆 Singularity Bridge Extended.")

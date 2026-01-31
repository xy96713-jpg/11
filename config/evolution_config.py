# DJ Set Evolution Strategy: Scoring Profiles Configuration

class ScoringProfile:
    def __init__(self, name, description, weights, skill_settings=None):
        self.name = name
        self.description = description
        self.weights = weights
        self.skill_settings = skill_settings or {
            "vocal_warning_bars": 8,       # 人声预警提前量 (小节)
            "vocal_gap_min_bars": 16,      # 认定为人声空隙的最小长度 (小节)
            "radar_risk_threshold": 70.0,  # 混音雷达判定为 "Risk" 的分值
            "radar_conflict_threshold": 50.0, # 混音雷达判定为 "Conflict" 的分值
            "mashup_threshold": 80.0       # 判定为适合叠歌的阈值
        }

PROFILES = {
    "BALANCED_ALPHA": ScoringProfile(
        name="Balanced Alpha",
        description="Current baseline. Balanced prioritization of BPM, Key, and Energy.",
        weights={
            "bpm_match": 100,
            "key_match": 1.0,
            "vocal_conflict_penalty": 5.0,
            "energy_match": 15,
            "timbre_match": 10,
            "genre_match": 15,
            "brightness_match": 8,
            "bass_match": 10
        },
        skill_settings={
            "vocal_warning_bars": 8,
            "vocal_gap_min_bars": 16,
            "radar_risk_threshold": 75.0,
            "radar_conflict_threshold": 55.0
        }
    ),
    "CONSERVATIVE_ANTI_CLASH": ScoringProfile(
        name="Conservative Anti-Clash",
        description="Priority: Avoid vocal clashes at all costs. Higher penalties for overlapping vocals.",
        weights={
            "bpm_match": 100,
            "key_match": 0.8,
            "vocal_conflict_penalty": 25.0,
            "energy_match": 10,
            "timbre_match": 8,
            "genre_match": 10,
            "brightness_match": 5,
            "bass_match": 8
        },
        skill_settings={
            "vocal_warning_bars": 16,      # 更早的预警
            "vocal_gap_min_bars": 32,      # 只有超大空隙才提示
            "radar_risk_threshold": 85.0,  # 极其严格
            "radar_conflict_threshold": 70.0 
        }
    ),
    "FLOW_FIRST": ScoringProfile(
        name="Flow-First (Groove)",
        description="Priority: Maintain rhythmic energy and BPM momentum. Willing to risk minor vocal overlaps.",
        weights={
            "bpm_match": 150,
            "key_match": 0.5,
            "vocal_conflict_penalty": 2.0,
            "energy_match": 25,
            "timbre_match": 15,
            "genre_match": 20,
            "brightness_match": 10,
            "bass_match": 15
        },
        skill_settings={
            "vocal_warning_bars": 4,       # 较短的预警，允许快速切入
            "vocal_gap_min_bars": 8,       # 较小的空隙也认为是机会
            "radar_risk_threshold": 65.0,  # 容忍度较高
            "radar_conflict_threshold": 45.0
        }
    )
}

DEFAULT_PROFILE = "BALANCED_ALPHA"

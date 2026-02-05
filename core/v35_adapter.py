"""
V35 Intelligence Adapter
========================
Translates V35 God Mode / Sonic DNA tags into quantifiable metrics for the Set Sorter.
"""

def interpret_energy_tier(vibe_tags):
    """
    Translates "Energy:TierX" tags into numeric 0-100 energy values.
    """
    if not vibe_tags:
        return 50
    
    tier_map = {
        "Tier1": 20, # Low/Chill
        "Tier2": 40, # Steady/Groove
        "Tier3": 65, # Driving/Active
        "Tier4": 85, # High Energy/Peak
        "Tier5": 100 # Maximum Intensity
    }
    
    for tag in vibe_tags:
        if "Energy:Tier" in tag:
            for tier, value in tier_map.items():
                if tier in tag:
                    return value
    return 50

def extract_vibe_summary(sonic_dna, vibe_analysis=None):
    """
    Summarizes the "feel" of the track based on Sonic DNA.
    Maps granular Neural tags to broad categories for synergy scoring.
    """
    if vibe_analysis is None:
        vibe_analysis = {}
        
    summary = []
    
    # Mapping for Spatial Synergy
    spatial_map = {
        "wide": ["Stadium", "Wide", "Ambient", "Envelopment", "Binaural"],
        "narrow": ["Mono", "Dry", "Centered", "Close-mic"],
        "cinematic": ["Cinematic", "Ethereal", "Epic"]
    }
    
    def map_tag(tag, mapping):
        for broad, patterns in mapping.items():
            if any(p.lower() in tag.lower() for p in patterns):
                return broad
        return tag

    # 1. Check Cognitive Intent
    cog = vibe_analysis.get("cognitive_dna", [])
    if cog:
        intent = cog[0]['tag']
        summary.append(f"Intent: {intent}")
        
    # 2. Check Spatial/Acoustic
    spatial = vibe_analysis.get("spatial", [])
    if spatial:
        raw_space = spatial[0]['tag']
        mapped_space = map_tag(raw_space, spatial_map)
        summary.append(f"Space: {mapped_space}")
        
    # 3. Check Production Era
    era = vibe_analysis.get("production_era", [])
    if era:
        summary.append(f"Texture: {era[0]['tag']}")
        
    return " | ".join(summary) if summary else "Standard Vibe"

def get_v35_enhanced_data(analysis_dict):
    """
    EntryPoint: Takes a raw V35 analysis dict and returns enhanced fields.
    """
    # 1. Handle Vibe Analysis (Tags)
    vibe_tags = analysis_dict.get("tags", []) # V35 often puts Tier tags here
    energy = interpret_energy_tier(vibe_tags)
    
    # 2. Handle Sonic DNA
    sonic_dna = analysis_dict.get("sonic_dna", {}) # God Mode details
    summary = extract_vibe_summary(analysis_dict.get("sonic_dna", {}), analysis_dict.get("god_mode_details", {}))
    
    return {
        "energy": energy,
        "vibe_summary": summary,
        "is_v35": True
    }

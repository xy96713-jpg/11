
import sys
import asyncio
# Add search path for core modules
sys.path.insert(0, "d:/anti")
sys.path.insert(0, "d:/anti/skills/mashup_intelligence/scripts")

from core import MashupIntelligence, SonicMatcher
from rekordbox_mcp.database import RekordboxDatabase, SearchOptions

async def debug_sonic():
    print("--- Debugging Sonic DNA ---")
    
    # Verify Sonic Gallery
    print(f"Sonic Gallery Keys: {SonicMatcher.SONIC_GALLERY.keys()}")
    
    db = RekordboxDatabase()
    await db.connect()
    
    # Fetch Tracks
    t1_list = await db.search_tracks(SearchOptions(query="忍者", limit=1))
    t2_list = await db.search_tracks(SearchOptions(query="Foot Fungus", limit=1))
    
    if not t1_list or not t2_list:
        print("Tracks not found!")
        return

    t1 = t1_list[0]
    t2 = t2_list[0]
    
    print(f"Track 1: {t1.title} (BPM: {t1.bpm}, Key: {t1.key})")
    print(f"Track 2: {t2.title} (BPM: {t2.bpm}, Key: {t2.key})")
    
    # Mock Dictionary format expected by logic
    t1_dict = {
        'title': t1.title,
        'bpm': t1.bpm,
        'key': t1.key,
        'analysis': {'bpm': t1.bpm, 'key': t1.key, 'energy': 0.8},
        'track_info': {'title': t1.title}
    }
    t2_dict = {
        'title': t2.title,
        'bpm': t2.bpm,
        'key': t2.key,
        'analysis': {'bpm': t2.bpm, 'key': t2.key, 'energy': 0.8},
        'track_info': {'title': t2.title}
    }
    
    # Run Calculation
    mi = MashupIntelligence()
    score, details = mi.calculate_mashup_score(t1_dict, t2_dict)
    
    print(f"\nFINAL SCORE: {score}")
    print("DETAILS:")
    for k, v in details.items():
        print(f"  {k}: {v}")
        
    await db.disconnect()

asyncio.run(debug_sonic())

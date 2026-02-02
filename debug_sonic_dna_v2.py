
import sys
import asyncio
sys.path.insert(0, "d:/anti")
sys.path.insert(0, "d:/anti/skills/mashup_intelligence/scripts")

from core import MashupIntelligence, SonicMatcher
from rekordbox_mcp.database import RekordboxDatabase, SearchOptions

async def debug_sonic():
    print("--- Debugging Sonic DNA V2 ---")
    db = RekordboxDatabase()
    await db.connect()
    
    # Check 1: Ninja
    t1_list = await db.search_tracks(SearchOptions(query="忍者", limit=10))
    print(f"Query '忍者' found {len(t1_list)} tracks.")
    if t1_list:
        print(f"  First: {t1_list[0].title}")

    # Check 2: Foot Fungus
    t2_list = await db.search_tracks(SearchOptions(query="Foot Fungus", limit=10))
    print(f"Query 'Foot Fungus' found {len(t2_list)} tracks.")
    if t2_list:
        print(f"  First: {t2_list[0].title}")

    if t1_list and t2_list:
        t1 = t1_list[0]
        t2 = t2_list[0]
        mi = MashupIntelligence()
        
        # Build Mock Dicts
        t1_dict = {'title': t1.title, 'bpm': t1.bpm, 'key': t1.key, 'analysis': {'bpm': t1.bpm, 'key': t1.key, 'energy': 0.8}, 'track_info': {'title': t1.title}}
        t2_dict = {'title': t2.title, 'bpm': t2.bpm, 'key': t2.key, 'analysis': {'bpm': t2.bpm, 'key': t2.key, 'energy': 0.8}, 'track_info': {'title': t2.title}}
        
        score, details = mi.calculate_mashup_score(t1_dict, t2_dict)
        print(f"\n--- CALCULATION ---")
        print(f"Score: {score}")
        print(f"Sonic Details: {details.get('sonic_dna', 'None')}")
        print(f"Output Reasons: {details}")

    await db.disconnect()

asyncio.run(debug_sonic())

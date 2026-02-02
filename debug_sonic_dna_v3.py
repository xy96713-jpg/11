
import sys
import asyncio
sys.path.insert(0, "d:/anti")
sys.path.insert(0, "d:/anti/skills/mashup_intelligence/scripts")

from core import MashupIntelligence, SonicMatcher
from rekordbox_mcp.database import RekordboxDatabase, SearchOptions

async def debug_sonic():
    print("--- Debugging Sonic DNA V3 ---", flush=True)
    db = RekordboxDatabase()
    await db.connect()
    
    t1_list = await db.search_tracks(SearchOptions(query="忍者", limit=1))
    t2_list = await db.search_tracks(SearchOptions(query="Foot Fungus", limit=1))
    
    if t1_list and t2_list:
        t1 = t1_list[0]
        t2 = t2_list[0]
        print(f"Match: {t1.title} x {t2.title}", flush=True)
        
        mi = MashupIntelligence()
        t1_dict = {'title': t1.title, 'bpm': t1.bpm, 'key': t1.key, 'analysis': {'bpm': t1.bpm, 'key': t1.key, 'energy': 0.8}, 'track_info': {'title': t1.title}}
        t2_dict = {'title': t2.title, 'bpm': t2.bpm, 'key': t2.key, 'analysis': {'bpm': t2.bpm, 'key': t2.key, 'energy': 0.8}, 'track_info': {'title': t2.title}}
        
        score, details = mi.calculate_mashup_score(t1_dict, t2_dict)
        print(f"SCORE: {score}", flush=True)
        print(f"SONIC: {details.get('sonic_dna', 'None')}", flush=True)
    else:
        print("Tracks not found", flush=True)

    await db.disconnect()

asyncio.run(debug_sonic())

import json
import os
from collections import defaultdict, Counter

CACHE_FILE = r"d:\anti\song_analysis_cache.json"

def verify_stats():
    if not os.path.exists(CACHE_FILE):
        print("Cache file not found.")
        return

    print("Loading cache...")
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        cache = json.load(f)

    total_songs = len(cache)
    print(f"\n===== 全库打标统计报告 (Total: {total_songs} unique tracks) =====")

    # Metric Counters
    has_energy_tier = 0
    has_mood = 0
    has_theme = 0
    has_story = 0
    has_ver = 0
    has_era = 0
    has_bpm = 0
    
    # Value Distributions
    mood_dist = Counter()
    era_dist = Counter()
    energy_dist = Counter()

    total_tags_count = 0

    for h, entry in cache.items():
        anlz = entry.get('analysis', {})
        
        # 1. BPM
        if anlz.get('bpm'): has_bpm += 1

        # 2. Energy Tier
        # 假设存在 deep_tags 字典或直接字段，先检查直接字段，再检查 tags 列表
        # 这里假设是 v7 架构，标签可能在 'tags' 列表或 'classifications' 中
        # 根据用户描述，是 "Energy:Tier", "Mood", etc.
        
        # 检查 analysis 里的 tags 列表
        tags = anlz.get('tags', [])
        # 也可能是 extra_features 或 classifications
        
        # 为了兼容，我们在 tags 列表中搜索特定前缀
        song_tags = set(tags)
        
        # Energy Tier
        if any(t.startswith("Energy:") for t in song_tags):
            has_energy_tier += 1
            for t in song_tags:
                if t.startswith("Energy:"): energy_dist[t] += 1

        # Mood
        if any(t.startswith("Mood:") for t in song_tags):
            has_mood += 1
            for t in song_tags:
                if t.startswith("Mood:"): mood_dist[t] += 1
        
        # Theme
        if any(t.startswith("Theme:") for t in song_tags):
            has_theme += 1
            
        # Story
        if any(t.startswith("Story:") for t in song_tags):
            has_story += 1
            
        # Version
        if any(t.startswith("Ver:") for t in song_tags):
            has_ver += 1
            
        # Era (Generation)
        if any(t.startswith("Era:") or t.startswith("Gen:") for t in song_tags):
            has_era += 1
            for t in song_tags:
                if t.startswith("Era:") or t.startswith("Gen:"): era_dist[t] += 1
                
        total_tags_count += len(song_tags)

    # Print Stats
    print(f"\n[覆盖率统计]")
    print(f"BPM Analysis : {has_bpm}/{total_songs} ({has_bpm/total_songs*100:.1f}%)")
    print(f"Energy Tier  : {has_energy_tier}/{total_songs} ({has_energy_tier/total_songs*100:.1f}%)")
    print(f"Mood Tag     : {has_mood}/{total_songs} ({has_mood/total_songs*100:.1f}%)")
    print(f"Theme Tag    : {has_theme}/{total_songs} ({has_theme/total_songs*100:.1f}%)")
    print(f"Story Tag    : {has_story}/{total_songs} ({has_story/total_songs*100:.1f}%)")
    print(f"Era/Gen Tag  : {has_era}/{total_songs} ({has_era/total_songs*100:.1f}%)")
    
    avg_tags = total_tags_count / total_songs if total_songs > 0 else 0
    print(f"\n平均标签数: {avg_tags:.1f} tags/song")
    
    print(f"\n[Top Moods]")
    for k, v in mood_dist.most_common(5):
        print(f"  {k}: {v}")

    print(f"\n[Era Distribution]")
    for k, v in era_dist.most_common(5):
        print(f"  {k}: {v}")

if __name__ == "__main__":
    verify_stats()

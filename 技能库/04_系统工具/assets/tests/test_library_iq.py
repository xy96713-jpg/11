import sys
from pathlib import Path

# 设置路径
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "skills"))

from skills.skill_aesthetic_curator import AestheticCurator

def test_tag_affinity():
    print("--- [Library-IQ: 多维标签审美验证] ---")
    curator = AestheticCurator()
    
    # 场景 1: 完美的审美一致性 (同为 4th Gen, 同为 Remix, 同为 Happy)
    track1 = {
        'title': 'NewJeans - Super Shy',
        'tags': ['Era:4th Gen', 'Ver:Original', 'Mood:Happy', 'Playlist:K-Pop'],
        'genre': 'K-Pop',
        'energy': 60,
        'valence': 0.8
    }
    
    track2 = {
        'title': 'IVE - I AM (Remix)',
        'tags': ['Era:4th Gen', 'Ver:Remix', 'Mood:Happy', 'Playlist:K-Pop'],
        'genre': 'K-Pop',
        'energy': 80,
        'valence': 0.9
    }
    
    print("\n[Case 1] 验证划代一致性 (IVE & NewJeans)")
    score1, details1 = curator.calculate_aesthetic_match(track1, track2)
    print(f"审美得分: {score1}")
    print(f"评分详情: {details1}")

    # 场景 2: 风格与时代对冲 (2nd Gen vs 5th Gen)
    track3 = {
        'title': 'SNSD - Gee',
        'tags': ['Era:2nd Gen', 'Ver:Original', 'Mood:Happy'],
        'genre': 'K-Pop',
        'energy': 70,
        'valence': 0.9
    }
    
    track4 = {
        'title': 'ILLIT - Magnetic',
        'tags': ['Era:5th Gen', 'Ver:Original', 'Mood:Happy'],
        'genre': 'K-Pop',
        'energy': 65,
        'valence': 0.85
    }

    print("\n[Case 2] 验证跨代际（二代 vs 五代）")
    score2, details2 = curator.calculate_aesthetic_match(track3, track4)
    print(f"审美得分: {score2}")
    print(f"评分详情: {details2}")

if __name__ == "__main__":
    test_tag_affinity()

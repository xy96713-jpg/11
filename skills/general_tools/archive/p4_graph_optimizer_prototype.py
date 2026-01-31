"""
P4: 图优化算法原型 - 验证 TSP 风格排序是否优于贪婪算法
用 NewJeans Set 作为测试用例
"""
import json
import itertools
from pathlib import Path
from typing import List, Dict, Tuple
import sys

sys.path.insert(0, "d:/anti")
sys.path.insert(0, "d:/anti/core/rekordbox-mcp")

try:
    from core.common_utils import get_advanced_harmonic_score
except:
    def get_advanced_harmonic_score(k1, k2):
        return (50, "Unknown")

CACHE_FILE = Path("d:/anti/song_analysis_cache.json")

def load_cache():
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_transition_score(track_a: dict, track_b: dict) -> float:
    """计算两首歌之间的过渡评分 (用作边权)"""
    score = 0.0
    
    # BPM 匹配 (0-35分)
    bpm_a = track_a.get('bpm', 128)
    bpm_b = track_b.get('bpm', 128)
    bpm_diff = abs(bpm_a - bpm_b)
    if bpm_diff <= 3:
        score += 35
    elif bpm_diff <= 6:
        score += 25
    elif bpm_diff <= 10:
        score += 15
    elif bpm_diff <= 15:
        score += 5
    else:
        score -= 10
    
    # 调性和谐 (0-30分)
    key_a = track_a.get('key', '1A')
    key_b = track_b.get('key', '1A')
    harm_score, _ = get_advanced_harmonic_score(key_a, key_b)
    score += harm_score * 0.3
    
    # 能量匹配 (0-20分)
    energy_a = track_a.get('energy', 50)
    energy_b = track_b.get('energy', 50)
    energy_diff = abs(energy_a - energy_b)
    if energy_diff <= 5:
        score += 20
    elif energy_diff <= 10:
        score += 12
    elif energy_diff <= 15:
        score += 5
    else:
        score -= 5
    
    # Brightness 匹配 (0-8分)
    br_a = track_a.get('brightness', 0.5)
    br_b = track_b.get('brightness', 0.5)
    if br_a and br_b:
        br_diff = abs(br_a - br_b)
        if br_diff <= 0.1:
            score += 8
        elif br_diff <= 0.2:
            score += 4
    
    return score

def greedy_sort(tracks: List[dict]) -> Tuple[List[dict], float]:
    """贪婪排序 (当前算法)"""
    if not tracks:
        return [], 0
    
    sorted_list = [tracks[0]]
    remaining = tracks[1:]
    total_score = 0
    
    while remaining:
        current = sorted_list[-1]
        best_score = -999
        best_idx = 0
        
        for i, track in enumerate(remaining):
            score = calculate_transition_score(current, track)
            if score > best_score:
                best_score = score
                best_idx = i
        
        total_score += best_score
        sorted_list.append(remaining.pop(best_idx))
    
    return sorted_list, total_score

def calculate_path_score(tracks: List[dict]) -> float:
    """计算一条路径的总分"""
    total = 0
    for i in range(len(tracks) - 1):
        total += calculate_transition_score(tracks[i], tracks[i+1])
    return total

def brute_force_optimal(tracks: List[dict]) -> Tuple[List[dict], float]:
    """穷举法找最优排列 (仅适用于小数据集)"""
    if len(tracks) > 8:
        print(f"  [WARN] 曲目数 {len(tracks)} > 8，穷举法耗时过长，跳过...")
        return tracks, 0
    
    best_order = None
    best_score = -9999999
    
    for perm in itertools.permutations(range(len(tracks))):
        ordered = [tracks[i] for i in perm]
        score = calculate_path_score(ordered)
        if score > best_score:
            best_score = score
            best_order = ordered
    
    return best_order, best_score

def nearest_neighbor_tsp(tracks: List[dict], start_idx: int = 0) -> Tuple[List[dict], float]:
    """最近邻启发式 TSP (快速近似)"""
    n = len(tracks)
    visited = [False] * n
    path = [start_idx]
    visited[start_idx] = True
    
    for _ in range(n - 1):
        current = path[-1]
        best_next = -1
        best_score = -9999
        
        for j in range(n):
            if not visited[j]:
                score = calculate_transition_score(tracks[current], tracks[j])
                if score > best_score:
                    best_score = score
                    best_next = j
        
        if best_next >= 0:
            path.append(best_next)
            visited[best_next] = True
    
    ordered = [tracks[i] for i in path]
    total_score = calculate_path_score(ordered)
    return ordered, total_score

def main():
    print("=" * 60)
    print("P4: 图优化算法原型验证")
    print("=" * 60)
    
    cache = load_cache()
    
    # 找 NewJeans 曲目
    nj_tracks = []
    for entry in cache.values():
        file_path = entry.get("file_path", "")
        if "newjeans" in file_path.lower() or "new jeans" in file_path.lower():
            analysis = entry.get("analysis", {})
            nj_tracks.append({
                "title": Path(file_path).stem[:40],
                "bpm": analysis.get("bpm", 128),
                "key": analysis.get("key", "1A"),
                "energy": analysis.get("energy", 50),
                "brightness": analysis.get("brightness", 0.5)
            })
    
    print(f"\n找到 {len(nj_tracks)} 首 NewJeans 曲目")
    
    if len(nj_tracks) < 3:
        print("曲目数不足，退出。")
        return
    
    # 只取前 8 首进行穷举对比
    test_tracks = nj_tracks[:8]
    print(f"使用前 {len(test_tracks)} 首进行对比测试")
    
    # 方法 1: 贪婪排序
    greedy_order, greedy_score = greedy_sort(test_tracks.copy())
    print(f"\n[贪婪算法] 总评分: {greedy_score:.1f}")
    print("排序结果:")
    for i, t in enumerate(greedy_order):
        print(f"  {i+1}. {t['title'][:30]} (BPM:{t['bpm']:.0f} Key:{t['key']} E:{t['energy']:.0f})")
    
    # 方法 2: TSP 最近邻启发式
    tsp_order, tsp_score = nearest_neighbor_tsp(test_tracks.copy(), 0)
    print(f"\n[TSP 最近邻] 总评分: {tsp_score:.1f}")
    print("排序结果:")
    for i, t in enumerate(tsp_order):
        print(f"  {i+1}. {t['title'][:30]} (BPM:{t['bpm']:.0f} Key:{t['key']} E:{t['energy']:.0f})")
    
    # 方法 3: 穷举法 (最优解)
    if len(test_tracks) <= 8:
        print("\n[穷举法 (最优解)] 计算中...")
        optimal_order, optimal_score = brute_force_optimal(test_tracks.copy())
        print(f"[穷举法] 总评分: {optimal_score:.1f}")
        print("排序结果:")
        for i, t in enumerate(optimal_order):
            print(f"  {i+1}. {t['title'][:30]} (BPM:{t['bpm']:.0f} Key:{t['key']} E:{t['energy']:.0f})")
    else:
        optimal_score = None
    
    # 结论
    print("\n" + "=" * 60)
    print("📊 对比结论")
    print("=" * 60)
    
    if optimal_score:
        greedy_gap = ((optimal_score - greedy_score) / optimal_score * 100) if optimal_score > 0 else 0
        tsp_gap = ((optimal_score - tsp_score) / optimal_score * 100) if optimal_score > 0 else 0
        
        print(f"贪婪 vs 最优: 差距 {greedy_gap:.1f}%")
        print(f"TSP  vs 最优: 差距 {tsp_gap:.1f}%")
        
        if greedy_gap < 5:
            print("\n✅ 结论: 贪婪算法已足够好 (差距 <5%)，无需替换")
        else:
            print(f"\n⚠️ 结论: 贪婪算法有 {greedy_gap:.1f}% 提升空间，考虑使用 TSP")
    else:
        diff = tsp_score - greedy_score
        print(f"TSP vs 贪婪: 评分差 {diff:.1f}")
        if diff > 10:
            print("⚠️ TSP 显著优于贪婪")
        else:
            print("✅ 差异不大，贪婪算法足够")
    
    print("=" * 60)

if __name__ == "__main__":
    main()

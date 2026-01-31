"""
专业系统审计脚本 - 数据可信度 & 优化建议
"""
import json
from pathlib import Path
from collections import Counter

CACHE_FILE = Path("d:/anti/song_analysis_cache.json")

def audit():
    print("=" * 70)
    print("🔍 DJ SET SYSTEM 专业审计报告")
    print("=" * 70)
    
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        cache = json.load(f)
    
    total = len(cache)
    print(f"\n📊 缓存总条目: {total}")
    
    # === 1. 数据完整性检查 ===
    print("\n" + "=" * 50)
    print("1️⃣ 数据完整性检查")
    print("=" * 50)
    
    critical_dims = [
        "bpm", "key", "energy", "phrase_length", 
        "intro_vocal_ratio", "outro_vocal_ratio",
        "brightness", "busy_score", "valence", "arousal"
    ]
    
    missing_stats = {dim: 0 for dim in critical_dims}
    none_stats = {dim: 0 for dim in critical_dims}
    
    for entry in cache.values():
        analysis = entry.get("analysis", {})
        for dim in critical_dims:
            val = analysis.get(dim)
            if dim not in analysis:
                missing_stats[dim] += 1
            elif val is None:
                none_stats[dim] += 1
    
    print(f"{'维度':<25} | {'缺失':<10} | {'None值':<10} | {'有效率':<10}")
    print("-" * 60)
    for dim in critical_dims:
        valid = total - missing_stats[dim] - none_stats[dim]
        pct = valid / total * 100 if total > 0 else 0
        status = "✅" if pct > 90 else "⚠️" if pct > 70 else "❌"
        print(f"{dim:<25} | {missing_stats[dim]:<10} | {none_stats[dim]:<10} | {pct:.1f}% {status}")
    
    # === 2. 置信度分布 ===
    print("\n" + "=" * 50)
    print("2️⃣ 置信度分布 (关键维度)")
    print("=" * 50)
    
    confidence_dims = [
        ("bpm_confidence", "BPM"),
        ("key_confidence", "Key"),
        ("phrase_confidence", "Phrase"),
        ("detected_genre_confidence", "Genre")
    ]
    
    for conf_key, label in confidence_dims:
        values = []
        for entry in cache.values():
            analysis = entry.get("analysis", {})
            v = analysis.get(conf_key)
            if v is not None and isinstance(v, (int, float)):
                values.append(v)
        
        if values:
            avg = sum(values) / len(values)
            high = sum(1 for v in values if v >= 0.8)
            low = sum(1 for v in values if v < 0.5)
            status = "✅" if avg > 0.8 else "⚠️" if avg > 0.6 else "❌"
            print(f"{label:<10}: 平均={avg:.2f} | 高置信(≥0.8)={high} | 低置信(<0.5)={low} {status}")
        else:
            print(f"{label:<10}: 无数据")
    
    # === 3. Valence/Arousal 数据质量 ===
    print("\n" + "=" * 50)
    print("3️⃣ 情感维度质量检查 (Valence/Arousal)")
    print("=" * 50)
    
    val_all_1 = 0
    aro_all_1 = 0
    valid_emotion = 0
    
    for entry in cache.values():
        analysis = entry.get("analysis", {})
        v = analysis.get("valence")
        a = analysis.get("arousal")
        if v == 1.0:
            val_all_1 += 1
        if a == 1.0:
            aro_all_1 += 1
        if v is not None and a is not None and v != 1.0 and a != 1.0:
            valid_emotion += 1
    
    print(f"Valence 全为 1.0 (无效): {val_all_1} ({val_all_1/total*100:.1f}%)")
    print(f"Arousal 全为 1.0 (无效): {aro_all_1} ({aro_all_1/total*100:.1f}%)")
    print(f"有效情感数据: {valid_emotion} ({valid_emotion/total*100:.1f}%)")
    
    if val_all_1 > total * 0.5 or aro_all_1 > total * 0.5:
        print("⚠️ 警告: 情感数据可能存在质量问题 (大量固定值)")
    
    # === 4. 风格分布 ===
    print("\n" + "=" * 50)
    print("4️⃣ 风格标签分布")
    print("=" * 50)
    
    genres = []
    for entry in cache.values():
        analysis = entry.get("analysis", {})
        g = analysis.get("detected_genre")
        if g:
            genres.append(g)
    
    genre_counts = Counter(genres)
    print(f"总计检测到 {len(genre_counts)} 种风格:")
    for genre, count in genre_counts.most_common(10):
        print(f"  {genre}: {count}")
    
    # === 5. 优化建议 ===
    print("\n" + "=" * 50)
    print("5️⃣ 优化建议")
    print("=" * 50)
    
    recommendations = []
    
    # 检查低覆盖维度
    for dim in critical_dims:
        valid = total - missing_stats[dim] - none_stats[dim]
        pct = valid / total * 100 if total > 0 else 0
        if pct < 80:
            recommendations.append(f"🔧 {dim}: 有效率仅 {pct:.1f}%, 建议重新分析缺失条目")
    
    # 检查情感数据
    if valid_emotion < total * 0.5:
        recommendations.append("🔧 情感分析 (Valence/Arousal): 数据质量差, 建议重新提取或禁用相关评分")
    
    # 检查分析版本
    versions = Counter()
    for entry in cache.values():
        analysis = entry.get("analysis", {})
        v = analysis.get("deep_analysis_version", "unknown")
        versions[v] = versions.get(v, 0) + 1
    
    if len(versions) > 1:
        recommendations.append(f"🔧 分析版本不一致: {dict(versions)} - 建议统一重新分析")
    
    if not recommendations:
        print("✅ 系统状态良好, 暂无关键优化建议")
    else:
        for r in recommendations:
            print(r)
    
    print("\n" + "=" * 70)
    print("审计完成")
    print("=" * 70)

if __name__ == "__main__":
    audit()

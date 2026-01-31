import asyncio
import sys
from pathlib import Path

BASE_DIR = Path("d:/anti")
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "core" / "rekordbox-mcp"))

from rekordbox_mcp.database import RekordboxDatabase
from skills.mashup_intelligence.scripts.core import MashupIntelligence
from core.cache_manager import load_cache

# 强制 UTF-8 输出
if sys.stdout.encoding.lower() != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def main():
    db = RekordboxDatabase()
    await db.connect()
    
    # 1. 寻找“忍者”
    found_tracks = await db.search_tracks_by_filename("忍者")
    if not found_tracks:
        # 尝试标题搜索
        all_tracks = await db.get_most_played_tracks(limit=1000)
        found_tracks = [t for t in all_tracks if "忍者" in t.title]
        
    if not found_tracks:
        print("❌ 找不到曲目：忍者")
        await db.disconnect()
        return

    target_track = found_tracks[0]
    print(f"🎯 目标曲目: {target_track.title} - {target_track.artist} (BPM: {target_track.bpm}, Key: {target_track.key})")

    # 2. 加载全库分析数据
    cache = load_cache()
    # 建立路径映射
    path_map = {v.get('file_path', '').replace('\\', '/'): v for v in cache.values()}
    
    def get_analysis_for_track(t):
        path = t.file_path.replace('\\', '/')
        entry = path_map.get(path)
        if not entry:
            return {
                'bpm': t.bpm,
                'key': t.key,
                'vocal_ratio': 0.5,
                'energy': t.rating * 20 if t.rating else 50,
                'file_path': t.file_path,
                'tags': []
            }
        if 'analysis' in entry:
            return entry['analysis']
        return entry

    target_analysis = {
        'track_info': {'title': target_track.title, 'artist': target_track.artist, 'file_path': target_track.file_path},
        'analysis': get_analysis_for_track(target_track)
    }

    # 3. 扫描库中所有音轨
    all_lib_tracks = await db.get_most_played_tracks(limit=1500)
    
    mi = MashupIntelligence()
    matches = []
    
    print(f"🔎 正在扫描曲库寻找完美契合点 (V5.2 引擎, 阈值: 40)...")
    for t in all_lib_tracks:
        if t.file_path == target_track.file_path:
            continue
            
        candidate_analysis = {
            'track_info': {'title': t.title, 'artist': t.artist, 'file_path': t.file_path},
            'analysis': get_analysis_for_track(t)
        }
        
        score, details = mi.calculate_mashup_score(target_analysis, candidate_analysis)
        
        if score >= 40:
            matches.append({
                'score': score,
                'details': details,
                'track': t,
                'analysis': candidate_analysis
            })

    matches.sort(key=lambda x: x['score'], reverse=True)

    report_path = Path("d:/anti/ninja_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 忍者 (Ninja) - Mashup 专家复盘 (V5.2 审美比例版)\n\n")
        f.write(f"🎯 **目标曲目**: {target_track.title} - {target_track.artist}\n")
        f.write(f"- BPM: {target_track.bpm} | Key: {target_track.key}\n\n")
        f.write("> [!IMPORTANT]\n")
        f.write("> **V5.2 飞跃更新**：系统现在支持 **3:4 / 2:3 审美比例对齐** 与 **采样 DNA 溯源**。不再局限于 BPM 数值，即使是 105bpm 与 140bpm 的跨界，只要律动相位一致，系统也会将其识别为极品 Match。\n\n")
        f.write("---\n\n")
        
        for i, m in enumerate(matches[:25]):
            t = m['track']
            f.write(f"### {i+1}. [{m['score']:.1f}] {t.title} - {t.artist}\n")
            f.write(f"**契合维度**:\n")
            f.write(f"- 审美速度/比例: {m['details'].get('perceptual_speed', 'N/A')}\n")
            f.write(f"- 调性兼容得分: {m['details'].get('key', 'N/A')}\n")
            
            # V5.2 新指标
            if 'sampling_heritage' in m['details'] or 'cross_cultural' in m['details']:
                f.write(f"- **文化 DNA**: {m['details'].get('sampling_heritage', '')} {m['details'].get('cross_cultural', '')}\n")
                
            f.write(f"- 核心模式: {m['details'].get('mashup_pattern', '自由组合')}\n\n")
            
            guide = mi.generate_unified_guide(target_analysis, m['analysis'], m['score'], m['details'])
            f.write(f"**🏮 [最强大脑] 专家复盘与执行建议**:\n")
            for line in guide[1:]:
                f.write(f"> {line.replace('>', '').strip()}\n")
            f.write("\n---\n\n")

    print(f"✅ 报告已生成至: {report_path}")
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main())

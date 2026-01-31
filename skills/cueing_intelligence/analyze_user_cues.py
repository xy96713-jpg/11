from pyrekordbox import Rekordbox6Database
from sqlalchemy import text
import statistics

def analyze_user_cue_patterns():
    db = Rekordbox6Database()
    
    #查询所有有手动标记的歌曲
    query = text("""
        SELECT 
            c.ID as ContentID,
            c.Title,
            c.BPM,
            cue.Kind,
            cue.InMsec,
            cue.Comment
        FROM djmdContent c
        INNER JOIN djmdCue cue ON c.ID = cue.ContentID
        WHERE cue.rb_local_deleted = 0
        ORDER BY c.Title, cue.Kind
    """)
    
    results = db.session.execute(query).fetchall()
    
    if not results:
        print("未找到任何手动标记的Cue点")
        return
    
    # 统计数据结构
    kind_distribution = {}
    tracks_with_cues = {}
    cue_patterns = {
        'has_AB': 0,  # A+B组合
        'has_CD': 0,  # C+D组合
        'has_ABCD': 0,  # 完整ABCD
        'only_A': 0,
        'only_C': 0,
        'memory_only': 0,
    }
    
    bar_lengths = {
        'entry': [],  # A->B的长度
        'exit': [],   # C->D的长度
        'AC': []      # A->C的长度
    }
    
    # 按track整理数据
    for row in results:
        content_id, title, bpm, kind, inmsec, comment = row
        
        if content_id not in tracks_with_cues:
            tracks_with_cues[content_id] = {
                'title': title,
                'bpm': bpm if bpm else 120,  # BPM is stored as integer in Rekordbox 6
                'cues': {}
            }
        
        tracks_with_cues[content_id]['cues'][kind] = {
            'time': inmsec / 1000.0,
            'comment': comment or ''
        }
        
        # Kind分布统计
        kind_name = {
            0: 'Memory Cue',
            1: 'HotCue A',
            2: 'HotCue B',
            3: 'HotCue C',
            4: 'HotCue D',
            5: 'HotCue E',
            6: 'HotCue F',
            7: 'HotCue G',
            8: 'HotCue H'
        }.get(kind, f'Unknown {kind}')
        
        kind_distribution[kind_name] = kind_distribution.get(kind_name, 0) + 1
    
    # 分析每首歌的Cue组合模式
    for track_id, track_data in tracks_with_cues.items():
        cues = track_data['cues']
        bpm = track_data['bpm']
        
        has_A = 1 in cues
        has_B = 2 in cues
        has_C = 3 in cues
        has_D = 4 in cues
        has_memory = 0 in cues
        
        # 模式识别
        if has_A and has_B and has_C and has_D:
            cue_patterns['has_ABCD'] += 1
        elif has_A and has_B:
            cue_patterns['has_AB'] += 1
        elif has_C and has_D:
            cue_patterns['has_CD'] += 1
        elif has_A and not has_B:
            cue_patterns['only_A'] += 1
        elif has_C and not has_D:
            cue_patterns['only_C'] += 1
        
        if has_memory and not (has_A or has_B or has_C or has_D):
            cue_patterns['memory_only'] += 1
        
        # 计算Bar长度
        if has_A and has_B:
            entry_sec = cues[2]['time'] - cues[1]['time']
            entry_bars = round((entry_sec * (bpm / 60.0)) / 4.0)
            bar_lengths['entry'].append(entry_bars)
        
        if has_C and has_D:
            exit_sec = cues[4]['time'] - cues[3]['time']
            exit_bars = round((exit_sec * (bpm / 60.0)) / 4.0)
            bar_lengths['exit'].append(exit_bars)
        
        if has_A and has_C:
            ac_sec = cues[3]['time'] - cues[1]['time']
            ac_bars = round((ac_sec * (bpm / 60.0)) / 4.0)
            bar_lengths['AC'].append(ac_bars)
    
    # 输出分析报告
    print("=" * 80)
    print("用户打点习惯分析报告 (User Cue Pattern Analysis)")
    print("=" * 80)
    print(f"\n总计分析歌曲数: {len(tracks_with_cues)}")
    print(f"总计Cue点数: {sum(kind_distribution.values())}")
    
    print("\n--- Kind分布统计 ---")
    for kind_name, count in sorted(kind_distribution.items(), key=lambda x: x[1], reverse=True):
        print(f"  {kind_name}: {count}个")
    
    print("\n--- 打点组合模式 ---")
    print(f"  完整ABCD组合: {cue_patterns['has_ABCD']}首")
    print(f"  仅AB组合(进歌窗): {cue_patterns['has_AB']}首")
    print(f"  仅CD组合(出歌窗): {cue_patterns['has_CD']}首")
    print(f"  仅A点: {cue_patterns['only_A']}首")
    print(f"  仅C点: {cue_patterns['only_C']}首")
    print(f"  仅Memory Cue: {cue_patterns['memory_only']}首")
    
    if bar_lengths['entry']:
        print("\n--- 进歌窗口长度分析 (A→B) ---")
        print(f"  平均: {statistics.mean(bar_lengths['entry']):.1f} bars")
        print(f"  中位数: {statistics.median(bar_lengths['entry']):.1f} bars")
        print(f"  最常用: {statistics.mode(bar_lengths['entry']) if len(set(bar_lengths['entry'])) < len(bar_lengths['entry']) else '无明显偏好'}")
        print(f"  范围: {min(bar_lengths['entry'])}-{max(bar_lengths['entry'])} bars")
    
    if bar_lengths['exit']:
        print("\n--- 出歌窗口长度分析 (C→D) ---")
        print(f"  平均: {statistics.mean(bar_lengths['exit']):.1f} bars")
        print(f"  中位数: {statistics.median(bar_lengths['exit']):.1f} bars")
        print(f"  最常用: {statistics.mode(bar_lengths['exit']) if len(set(bar_lengths['exit'])) < len(bar_lengths['exit']) else '无明显偏好'}")
        print(f"  范围: {min(bar_lengths['exit'])}-{max(bar_lengths['exit'])} bars")
    
    if bar_lengths['AC']:
        print("\n--- 混音总跨度分析 (A→C) ---")
        print(f"  平均: {statistics.mean(bar_lengths['AC']):.1f} bars")
        print(f"  中位数: {statistics.median(bar_lengths['AC']):.1f} bars")
    
    # 示例歌曲展示
    print("\n--- 打点示例（前5首歌） ---")
    for i, (track_id, track_data) in enumerate(list(tracks_with_cues.items())[:5], 1):
        print(f"\n{i}. {track_data['title']}")
        for kind in sorted(track_data['cues'].keys()):
            cue = track_data['cues'][kind]
            kind_name = {0: 'Mem', 1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G', 8: 'H'}.get(kind, '?')
            comment_str = f" ({cue['comment']})" if cue['comment'] else ""
            print(f"  {kind_name}: {cue['time']:.1f}s{comment_str}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    analyze_user_cue_patterns()

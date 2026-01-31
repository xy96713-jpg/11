import sys
from pathlib import Path
import json

# 设置路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "core" / "rekordbox-mcp"))

try:
    from pyrekordbox import Rekordbox6Database
    import sqlalchemy as sa
except ImportError:
    print("Error: pyrekordbox or sqlalchemy not found.")
    sys.exit(1)

def diagnose():
    print("--- [最强大脑: 曲库元数据深度诊断] ---")
    try:
        db = Rekordbox6Database()
        content = list(db.get_content())
        total = len(content)
        print(f"检测到总音轨数: {total}")
        
        # 定义我们关心的字段
        target_fields = [
            'ArtistName', 'GenreName', 'AlbumName', 'KeyName', 
            'BPM', 'Rating', 'ReleaseYear', 'LabelName', 
            'RemixerName', 'Message', 'Commnt', 'ComposerName',
            'DateCreated', 'TrackNo'
        ]
        
        stats = {field: 0 for field in target_fields}
        sample_data = []

        for i, item in enumerate(content):
            for field in target_fields:
                val = getattr(item, field, None)
                if val and str(val).strip() and val != 0:
                    stats[field] += 1
            
            # 记录前 5 个样本的全部非空字段
            if i < 5:
                sample_data.append({f: str(getattr(item, f, "None")) for f in target_fields})

        print("\n[字段覆盖率报告]:")
        for field, count in stats.items():
            percentage = (count / total) * 100 if total > 0 else 0
            print(f"- {field:15}: {count:5} ({percentage:5.1f}%)")
            
        print("\n[典型数据样本]:")
        print(json.dumps(sample_data, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"诊断失败: {e}")

if __name__ == "__main__":
    diagnose()

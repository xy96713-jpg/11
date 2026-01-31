import xml.etree.ElementTree as ET
import sys
from pathlib import Path

def audit_xml(xml_path):
    print(f"\n🔍 正在审计 XML: {xml_path}")
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        collection = root.find("COLLECTION")
        if collection is None:
            print("❌ 错误：未找到 COLLECTION 节点")
            return
            
        tracks = collection.findall("TRACK")
        print(f"📊 总音轨数: {len(tracks)}")
        
        issue_count = 0
        for track in tracks:
            track_id = track.get("TrackID")
            name = track.get("Name")
            marks = track.findall("POSITION_MARK")
            tempo = track.find("TEMPO")
            
            # 报告异常：没有标点 或 没有节奏网格
            if not marks or tempo is None:
                issue_count += 1
                print(f"  ⚠️ 异常音轨 [{track_id}]: {name}")
                if not marks: print("    - ❌ 缺失 POSITION_MARK (标点)")
                if tempo is None: print("    - ❌ 缺失 TEMPO (节拍网格)")
            else:
                # 统计不同类型的标点
                hotcues = [m for m in marks if m.get("Num") != "-1"]
                memcues = [m for m in marks if m.get("Num") == "-1"]
                # print(f"  ✅ {name[:30]:<30} | 标点: {len(hotcues)} Hot, {len(memcues)} Mem")
        
        if issue_count == 0:
            print("\n🎉 审计通过！所有音轨均包含标点和节拍信息。")
        else:
            print(f"\n❌ 审计失败！存在 {issue_count} 个异常音轨。")
            
    except Exception as e:
        print(f"❌ 解析 XML 失败: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        audit_xml(sys.argv[1])
    else:
        # 默认找最新的 XML
        import glob
        xml_files = glob.glob("D:/生成的set/**/*.xml", recursive=True)
        if xml_files:
            latest_xml = max(xml_files, key=Path).replace('\\', '/')
            audit_xml(latest_xml)
        else:
            print("❌ 未找到任何 XML 文件。")

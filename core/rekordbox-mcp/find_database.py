#!/usr/bin/env python3
"""
查找Rekordbox数据库文件
"""

import os
import glob
import sys

def find_rekordbox_database():
    print("🔍 查找Rekordbox数据库文件")
    print("=" * 50)
    
    # 常见的Rekordbox数据库位置
    possible_paths = [
        r"C:\Users\Administrator\AppData\Roaming\Pioneer\rekordbox",
        r"C:\Users\Administrator\AppData\Local\Pioneer\rekordbox", 
        r"C:\Users\Administrator\Documents\Pioneer\rekordbox",
        r"C:\ProgramData\Pioneer\rekordbox",
        r"C:\Users\Administrator\AppData\Roaming\rekordbox",
        r"C:\Users\Administrator\AppData\Local\rekordbox"
    ]
    
    found_databases = []
    
    for base_path in possible_paths:
        if os.path.exists(base_path):
            print(f"✅ 找到目录: {base_path}")
            
            # 查找数据库文件
            db_patterns = [
                os.path.join(base_path, "**", "*.db"),
                os.path.join(base_path, "**", "*.sqlite"),
                os.path.join(base_path, "**", "master.db"),
                os.path.join(base_path, "**", "rekordbox.db")
            ]
            
            for pattern in db_patterns:
                files = glob.glob(pattern, recursive=True)
                for file in files:
                    if os.path.isfile(file):
                        size = os.path.getsize(file)
                        print(f"  📁 数据库文件: {file} ({size} bytes)")
                        found_databases.append(file)
        else:
            print(f"❌ 目录不存在: {base_path}")
    
    # 也检查整个AppData目录
    print("\n🔍 搜索整个AppData目录...")
    appdata_path = r"C:\Users\Administrator\AppData"
    if os.path.exists(appdata_path):
        for root, dirs, files in os.walk(appdata_path):
            for file in files:
                if file.endswith('.db') and ('rekordbox' in file.lower() or 'pioneer' in file.lower()):
                    full_path = os.path.join(root, file)
                    size = os.path.getsize(full_path)
                    print(f"  📁 找到数据库: {full_path} ({size} bytes)")
                    found_databases.append(full_path)
    
    print(f"\n📊 总共找到 {len(found_databases)} 个可能的数据库文件")
    
    if found_databases:
        print("\n🎯 建议的数据库文件:")
        for i, db_path in enumerate(found_databases, 1):
            print(f"{i}. {db_path}")
        
        # 尝试使用第一个数据库文件
        if found_databases:
            test_db = found_databases[0]
            print(f"\n🧪 测试数据库: {test_db}")
            
            try:
                import pyrekordbox
                # 尝试使用指定路径
                db = pyrekordbox.Rekordbox6Database(db_path=test_db)
                content = list(db.get_content())
                print(f"✅ 成功连接！找到 {len(content)} 首歌曲")
                return test_db
            except Exception as e:
                print(f"❌ 连接失败: {e}")
                try:
                    db = pyrekordbox.Rekordbox7Database(db_path=test_db)
                    content = list(db.get_content())
                    print(f"✅ 成功连接！找到 {len(content)} 首歌曲")
                    return test_db
                except Exception as e2:
                    print(f"❌ 连接也失败: {e2}")
    else:
        print("\n❌ 未找到Rekordbox数据库文件")
        print("\n请确保:")
        print("1. 已运行过Rekordbox软件")
        print("2. 已导入音乐文件到Rekordbox")
        print("3. Rekordbox已完全关闭")
    
    return None

if __name__ == "__main__":
    database_path = find_rekordbox_database()
    if database_path:
        print(f"\n✅ 建议使用数据库路径: {database_path}")
    else:
        print("\n❌ 未找到可用的数据库文件")











# 使用示例

## 示例 1: 单曲下载

```bash
cd D:\anti\.agent\skills\dl\scripts
python download_and_tag.py "aespa Supernova" --name "aespa_Supernova"
```

输出:
```
🔍 尝试平台方案: scsearch1:aespa Supernova ...
✅ 锁定资源: Supernova (来自 soundcloud)
🎨 正在从 iTunes 搜索官方元数据: 'aespa Supernova'...
✅ ID3 标签(v2.3)与高清封面写入成功！
🎉 完美交付: D:\song\Final_Music_Official\aespa_Supernova.mp3
```

## 示例 2: 从截图批量下载

1. 用户发送包含歌曲列表的截图
2. Agent 识别歌曲信息:
   - 82MAJOR - Need That Bass
   - KiiiKiii - Delulu
   - $uicideboy$ - Starry 9

3. 逐一调用下载:
```bash
python download_and_tag.py "82MAJOR Need That Bass" --name "82MAJOR_Need_That_Bass"
python download_and_tag.py "KiiiKiii Delulu" --name "KiiiKiii_Delulu"
python download_and_tag.py "Suicideboys Starry 9" --name "Suicideboys_Starry_9"
```

## 示例 3: 修复缺失封面

当用户反馈某些歌曲没有封面时:

```python
# 编辑 fix_missing_covers.py 中的 files_to_fix 列表
files_to_fix = [
    ("Delulu.mp3", "KiiiKiii Delulu"),
    ("Some_Song.mp3", "Artist Name Song Title"),
]
```

然后运行:
```bash
python fix_missing_covers.py
```

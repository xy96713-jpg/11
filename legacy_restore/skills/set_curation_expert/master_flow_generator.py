#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import asyncio
from pathlib import Path
from contextlib import contextmanager

# 导入各模块功能
from enhanced_harmonic_set_sorter import create_enhanced_harmonic_sets

OUTPUT_DIR = Path("D:/生成的set")

@contextmanager
def silence_technical_noise():
    """静默掉不需要的库警告（如 pyrekordbox, sqlalchemy 等）"""
    import logging
    import warnings
    # 抑制所有警告
    warnings.filterwarnings("ignore")
    # 抑制标准 logging
    logging.getLogger('sqlalchemy').setLevel(logging.ERROR)
    logging.getLogger('pyrekordbox').setLevel(logging.ERROR)
    try:
        yield
    finally:
        pass

async def run_integrated_master_flow(playlist_name="House", is_boutique=False):
    """
    一键集成主流程：
    调用 Sorter 最强大脑进行排序、混音分析和全格式导出

    注意：所有文件导出（M3U/CSV/TXT/XML）均由 enhanced_harmonic_set_sorter.py 完成
    本脚本只负责用户交互和调用 Sorter
    """
    print("\n" + "="*60)
    print("AI DJ 工作流自动化 - 最强大脑集成版 V3.0")
    print("="*60)

    print(f"\n[1/1] 正在调动最强大脑进行集序优化、混音分析与全格式导出...")
    print(f"  播放列表: {playlist_name}")
    print(f"  模式: {'精品回馈' if is_boutique else '标准模式'}")

    # --- Step 2: 调用原装排序大脑（已包含所有导出：M3U/CSV/TXT/XML）---
    with silence_technical_noise():
        all_sets = await create_enhanced_harmonic_sets(
            playlist_name=playlist_name,
            is_master=True,
            is_boutique=is_boutique
        )

    if not all_sets:
        print(f"\n错误：未能在播放列表 '{playlist_name}' 中找到轨道。")
        return

    print("\n流程圆满完成！")
    print("\n" + "="*60)
    print(f"所有文件已生成至：{OUTPUT_DIR}")
    print("包含格式：M3U, CSV, TXT (混音建议), XML (Rekordbox)")
    print("提示：导入 XML 后请在 Rekordbox 中右键点击播放列表 -> '导入到收藏集'。")
    print("="*60 + "\n")

if __name__ == "__main__":
    import sys
    # 支持命令行参数: python master_flow_generator.py [playlist_name] [--boutique]
    playlist = "House"
    boutique = False
    
    if len(sys.argv) > 1:
        playlist = sys.argv[1]
    if "--boutique" in sys.argv:
        boutique = True
    
    asyncio.run(run_integrated_master_flow(playlist, boutique))

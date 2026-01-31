#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级调性算法库 (Harmonic Utils)
提供Camelot Wheel调性转换、兼容性评分与5度圈计算逻辑。
"""

from functools import lru_cache

# Camelot轮盘兼容规则（快速查找字典，用于简单场景）
CAMELOT_COMPATIBLE_DICT = {
    '1A': ['1A', '12A', '2A', '1B'],
    '2A': ['2A', '1A', '3A', '2B'],
    '3A': ['3A', '2A', '4A', '3B'],
    '4A': ['4A', '3A', '5A', '4B'],
    '5A': ['5A', '4A', '6A', '5B'],
    '6A': ['6A', '5A', '7A', '6B'],
    '7A': ['7A', '6A', '8A', '7B'],
    '8A': ['8A', '7A', '9A', '8B'],
    '9A': ['9A', '8A', '10A', '9B'],
    '10A': ['10A', '9A', '11A', '10B'],
    '11A': ['11A', '10A', '12A', '11B'],
    '12A': ['12A', '11A', '1A', '12B'],
    '1B': ['1B', '12B', '2B', '1A'],
    '2B': ['2B', '1B', '3B', '2A'],
    '3B': ['3B', '2B', '4B', '3A'],
    '4B': ['4B', '3B', '5B', '4A'],
    '5B': ['5B', '4B', '6B', '5A'],
    '6B': ['6B', '5B', '7B', '6A'],
    '7B': ['7B', '6B', '8B', '7A'],
    '8B': ['8B', '7B', '9B', '8A'],
    '9B': ['9B', '8B', '10B', '9A'],
    '10B': ['10B', '9B', '11B', '10A'],
    '11B': ['11B', '10B', '12B', '11A'],
    '12B': ['12B', '11B', '1B', '12A'],
}

def convert_open_key_to_camelot(open_key: str) -> str:
    """
    将Open Key格式转换为Camelot格式
    
    Open Key System:
    - 小调：1m-12m (minor)
    - 大调：1d-12d (major/dur)
    
    Camelot Wheel:
    - 小调：1A-12A (minor)
    - 大调：1B-12B (major)
    
    Returns:
        str: Camelot格式的调性（如果输入已经是Camelot格式，则原样返回）
    """
    if open_key is None:
        return "未知"
    # 先把类型收敛：Rekordbox/SQL 有时会给出整数ID，直接当未知处理
    if isinstance(open_key, (int, float)):
        return "未知"
    if not isinstance(open_key, str):
        try:
            open_key = str(open_key)
        except Exception:
            return "未知"
    open_key = open_key.strip()
    if not open_key or open_key == "未知":
        return "未知"

    # 明显异常：纯数字/超长数字（常见于数据库内部ID），不要原样透传到报告里
    if open_key.isdigit() and len(open_key) >= 3:
        return "未知"
    
    # 如果已经是Camelot格式（以A或B结尾），直接返回
    if len(open_key) >= 2 and open_key[-1] in ['A', 'B']:
        try:
            # 验证格式正确（数字+A/B）
            int(open_key[:-1])
            return open_key
        except ValueError:
            pass
    
    try:
        # 检测Open Key格式
        if open_key.endswith('m'):
            # 小调：1m-12m → 1A-12A
            num = int(open_key[:-1])
            if 1 <= num <= 12:
                return f"{num}A"
        elif open_key.endswith('d'):
            # 大调：1d-12d → 1B-12B
            num = int(open_key[:-1])
            if 1 <= num <= 12:
                return f"{num}B"
    except (ValueError, IndexError):
        pass
    
    # 如果无法识别，返回未知（更符合“专业DJ报告/评分”的期望）
    return "未知"


def detect_key_system(key: str) -> str:
    """
    检测调性系统类型
    
    Returns:
        str: "camelot", "open_key", "unknown"
    """
    if not key or key == "未知":
        return "unknown"
    
    # 检测Open Key格式
    if len(key) >= 2 and (key.endswith('m') or key.endswith('d')):
        try:
            num = int(key[:-1])
            if 1 <= num <= 12:
                return "open_key"
        except ValueError:
            pass
    
    # 检测Camelot格式
    if len(key) >= 2 and key[-1] in ['A', 'B']:
        try:
            num = int(key[:-1])
            if 1 <= num <= 12:
                return "camelot"
        except ValueError:
            pass
    
    return "unknown"


@lru_cache(maxsize=10000)
def get_key_compatibility_flexible(current_key: str, next_key: str) -> int:
    """
    专业T字混音法（Camelot Wheel）+ 5度圈调性兼容性检查
    
    基于Camelot轮盘和5度圈理论：
    - 同号不同调式（A↔B）：最和谐（相对调性关系）
    - ±1：5度圈相邻，非常和谐
    - ±2：5度圈隔一个，较和谐
    - ±3-4：需要技巧
    - 相对调性（±7）：特殊和谐（如1A-8A，C大调-C小调）
    
    支持Open Key System自动转换（1m-12m / 1d-12d → 1A-12A / 1B-12B）
    
    Returns:
        int: 0-100 的兼容性评分
    """
    if not current_key or current_key == "未知" or not next_key or next_key == "未知":
        return 50  # 未知调性给中等分数，允许使用
    
    # Open Key System兼容：自动转换Open Key格式到Camelot格式
    current_key = convert_open_key_to_camelot(current_key)
    next_key = convert_open_key_to_camelot(next_key)
    
    try:
        curr_num = int(current_key[:-1])
        curr_letter = current_key[-1]
        next_num = int(next_key[:-1])
        next_letter = next_key[-1]
        
        # 1. 同调性（最完美）- 100分
        if current_key == next_key:
            return 100
        
        # 2. 同号不同调式（A↔B切换，T字混音法最和谐）- 100分
        # 这是相对调性关系（如C大调↔C小调），专业DJ最常用的混音方式
        if curr_num == next_num and curr_letter != next_letter:
            return 100
        
        # 计算5度圈距离（考虑轮盘循环）
        def circle_distance(a, b):
            """计算Camelot轮盘上的5度圈距离（考虑循环）"""
            direct = abs(a - b)
            wrap = 12 - direct
            return min(direct, wrap)
        
        diff = circle_distance(curr_num, next_num)
        
        # 3. ±1（5度圈相邻，非常和谐）- 95分
        # 这是5度圈上的直接相邻关系（如1A→2A，C→G）
        if diff == 1:
            if curr_letter == next_letter:
                return 95
            else:
                return 85  # 不同调式但5度相邻
        
        # 4. ±2（5度圈隔一个，较和谐）- 85分
        # 这是5度圈上隔一个调的关系（如1A→3A，C→D）
        if diff == 2:
            if curr_letter == next_letter:
                return 85
            else:
                return 75
        
        # 5. ±3-4（需要技巧，但可用）- 70分
        # 5度圈上距离较远，需要更多混音技巧
        if diff <= 4:
            if curr_letter == next_letter:
                return 70
            else:
                return 60
        
        # 6. ±5（困难，需要高级技巧）- 45分
        # 5度圈上距离较远，混音难度高
        if diff == 5:
            if curr_letter == next_letter:
                return 45
            else:
                return 35
        
        # 7. ±6（非常困难，Camelot轮盘上最远距离）- 30分
        # 这是5度圈上的对角位置，调性冲突最大
        if diff == 6:
            if curr_letter == next_letter:
                return 30
            else:
                return 20
        
        # 8. 其他情况（理论上不会到这里）- 30分
        return 30
        
    except (ValueError, IndexError):
        return 50

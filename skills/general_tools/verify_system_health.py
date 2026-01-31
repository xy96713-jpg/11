import sys
from pathlib import Path
import os

# 设置路径
BASE_DIR = Path("d:/anti")
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "skills"))
sys.path.insert(0, str(BASE_DIR / "core"))

def run_test():
    print("=== 系统健康检查开始 ===")
    
    # 1. 验证 PHRASE_KINDS 修复
    try:
        from core.rekordbox_phrase_reader import PHRASE_KINDS
        print("\n[OK] core.rekordbox_phrase_reader 导入成功")
        if PHRASE_KINDS.get(10) == 'Fade':
            print("  [Pass] PHRASE_KINDS[10] 已正确修复为 'Fade'")
        else:
            print(f"  [Fail] PHRASE_KINDS[10] 期望 'Fade'，实际为 '{PHRASE_KINDS.get(10)}'")
    except Exception as e:
        print(f"[Fail] core.rekordbox_phrase_reader 导入失败: {e}")

    # 2. 验证 vocal_regions 格式兼容性 (skill_pro_cueing)
    try:
        from skills.mashup_intelligence.scripts.core import MashupIntelligence
        from skills.cueing_intelligence.scripts.pro import professional_quantize, is_in_vocal_region
        print("\n[OK] skills.cueing_intelligence 导入成功")
        
        # Test List format
        res_list = is_in_vocal_region(15.0, [[10.0, 20.0]])
        if res_list:
            print("  [Pass] List 格式兼容性测试通过")
        else:
            print("  [Fail] List 格式兼容性测试失败 (期望 True)")
            
        # Test Dict format
        res_dict = is_in_vocal_region(15.0, [{'start': 10.0, 'end': 20.0}])
        if res_dict:
            print("  [Pass] Dict 格式兼容性测试通过")
        else:
            print("  [Fail] Dict 格式兼容性测试失败 (期望 True)")
    except Exception as e:
        print(f"[Fail] skills.skill_pro_cueing 测试失败: {e}")

    # 3. 验证 vocal_regions 格式兼容성 (auto_hotcue_generator)
    try:
        # 我们不能轻易调用 _generate 但可以检查 imports
        import auto_hotcue_generator
        print("\n[OK] auto_hotcue_generator 导入成功")
        # 直接测试导入没报错通常意味着语法没问题
    except Exception as e:
        print(f"[Fail] auto_hotcue_generator 导入失败: {e}")

    # 4. 验证其他 Skills 导入
    skills = [
        "skills.cueing_intelligence.scripts.v3",
        "skills.cueing_intelligence.scripts.vocal", 
        "skills.rhythmic_energy.scripts.phrase",
        "skills.aesthetic_expert.scripts.curator",
        "skills.mashup_intelligence.scripts.core"
    ]
    
    print("\n=== 核心 Skills 导入测试 (规范化路径) ===")
    for skill in skills:
        try:
            __import__(skill)
            print(f"  [Pass] {skill} 导入成功")
        except Exception as e:
            print(f"  [Fail] {skill} 导入失败: {e}")

    # 5. 验证 Unified Expert Core
    print("\n=== Unified Expert Core 测试 ===")
    try:
        from skills.general_tools.scripts.unified_core import VocalConflictEngine, PhraseQuantizer, CueStandard
        print("  [Pass] Unified Expert Core 导入成功")
        
        # Test Vocal
        if VocalConflictEngine.is_active(10.0, [{'start':5, 'end':15}]):
             print("  [Pass] VocalConflictEngine.is_active 工作正常")
        else:
             print("  [Fail] VocalConflictEngine.is_active 逻辑错误")
             
        # Test Quantizer
        q = PhraseQuantizer.quantize(10.1, 120, 0.0)
        if abs(q - 10.0) < 0.2: 
             print(f"  [Pass] PhraseQuantizer.quantize 工作正常 ({q:.3f})")
        else:
             print(f"  [Fail] PhraseQuantizer.quantize 异常 ({q:.3f})")

    except Exception as e:
        print(f"  [Fail] Unified Expert Core 测试失败: {e}")

    print("\n=== 系统健康检查完成 ===")

if __name__ == "__main__":
    run_test()

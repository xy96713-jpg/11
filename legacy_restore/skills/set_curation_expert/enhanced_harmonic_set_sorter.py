#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版专业DJ Set排序工具
注重调性和谐 + 灵活排序 + 生成混音建议
"""

import os
import sys
import asyncio
import argparse
import json
import contextlib
import hashlib
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import statistics
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed

# 【Phase 9】系统目录整合 - 动态调整路径以支持 D:\anti 结构
BASE_DIR = Path(__file__).parent
for sub_dir in ["skills", "core", "config", "exporters", "agents"]:
    sys.path.insert(0, str(BASE_DIR / sub_dir))

# 添加 rekordbox-mcp 的父目录以支持 import rekordbox_mcp
sys.path.insert(0, str(BASE_DIR / "core" / "rekordbox-mcp"))

from exporters.xml_exporter import export_to_rekordbox_xml

# Audio Inspector Integration
def get_audio_inspector_data(file_path: str) -> Optional[Dict]:
    """使用 mcp-audio-inspector 获取音频元数据 (Node.js)"""
    inspector_path = BASE_DIR / "mcp-audio-inspector" / "index.js"
    if not inspector_path.exists():
        return None
        
    try:
        # Run: node index.js --standalone "file_path"
        result = subprocess.run(
            ["node", inspector_path, "--standalone", file_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass
    return None

sys.path.insert(0, str(Path(__file__).parent / "rekordbox-mcp"))

try:
    from rekordbox_mcp.database import RekordboxDatabase
    from rekordbox_mcp.models import SearchOptions
except ImportError as e:
    print(f"导入错误: {e}")
    # Fallback/Mock for standalone runs if needed
    class RekordboxDatabase: pass
    class SearchOptions: pass

try:
    from pyrekordbox import Rekordbox6Database
    from sqlalchemy import text
except ImportError as e:
    print(f"导入错误: {e}")
    sys.exit(1)

# 导入深度分析
try:
    from strict_bpm_multi_set_sorter import deep_analyze_track
except:
    def deep_analyze_track(file_path, db_bpm=None):
        return None

# 导入质量监控
try:
    from conflict_monitor_overlay import generate_radar_report
except ImportError:
    def generate_radar_report(tracks): return "无法生成雷达报告"

# 【Phase 8】导入人声感知混音点检测
try:
    from skills.cueing_intelligence.scripts.vocal import (
        check_vocal_overlap_at_mix_point,
        get_recommended_mix_points_avoiding_vocals
    )
    VOCAL_DETECTION_ENABLED = True
except ImportError:
    VOCAL_DETECTION_ENABLED = False
    def check_vocal_overlap_at_mix_point(*args, **kwargs): return (0.0, "未安装")
    def get_recommended_mix_points_avoiding_vocals(*args, **kwargs): return (None, None, "未安装")

# 【Phase 8】导入Phrase对齐和能量曲线检测
try:
    from skills.rhythmic_energy.scripts.phrase import (
        check_phrase_alignment,
        suggest_better_phrase_aligned_point,
        validate_energy_curve,
        suggest_energy_reorder
    )
    PHRASE_ENERGY_ENABLED = True
except ImportError:
    PHRASE_ENERGY_ENABLED = False
    def check_phrase_alignment(*args, **kwargs): return (0.0, "未安装")
    def suggest_better_phrase_aligned_point(*args, **kwargs): return (None, "未安装")
    def validate_energy_curve(*args, **kwargs): return (True, [])
    def suggest_energy_reorder(tracks): return tracks

# 【Phase 8】导入BPM渐进式管理
try:
    from skills.rhythmic_energy.scripts.bpm import (
        validate_bpm_progression,
        suggest_bpm_reorder,
        get_bpm_curve_summary
    )
    BPM_PROGRESSIVE_ENABLED = True
except ImportError:
    BPM_PROGRESSIVE_ENABLED = False
    def validate_bpm_progression(*args, **kwargs): return (True, [])
    def suggest_bpm_reorder(tracks, phase="auto"): return tracks
    def get_bpm_curve_summary(tracks): return {}

# 【Phase 9】导入专业审计和能量曲线分析
try:
    from skills.aesthetic_expert.scripts.audit import calculate_set_completeness, get_energy_curve_summary
    PROFESSIONAL_AUDIT_ENABLED = True
except ImportError:
    PROFESSIONAL_AUDIT_ENABLED = False
    def calculate_set_completeness(*args, **kwargs): return {"total_score": 0, "breakdown": {}}
    def get_energy_curve_summary(*args, **kwargs): return "N/A"

# 【Phase 10】导入自动Hotcue生成器
try:
    from auto_hotcue_generator import generate_hotcues, hotcues_to_rekordbox_format
    HOTCUE_GENERATOR_ENABLED = True
except ImportError:
    HOTCUE_GENERATOR_ENABLED = False
    def generate_hotcues(*args, **kwargs): return {}
    def hotcues_to_rekordbox_format(*args, **kwargs): return {}

# 【V5.3 P1】导入 Rekordbox Phrase Reader
try:
    from rekordbox_phrase_reader import RekordboxPhraseReader
    PHRASE_READER = RekordboxPhraseReader()
    PHRASE_READER_AVAILABLE = True
except ImportError:
    PHRASE_READER_AVAILABLE = False
    PHRASE_READER = None

# 【Phase 10】导入 Mashup Intelligence 核心联动模块
try:
    from skills.mashup_intelligence.scripts.core import MashupIntelligence
    MASHUP_INTELLIGENCE = MashupIntelligence()
    MASHUP_ENABLED = True
    print(f"[OK] 已成功挂载 Mashup Intelligence V4 微观引擎")
except ImportError:
    MASHUP_ENABLED = False
    class MashupIntelligence:
        def calculate_mashup_score(self, *args, **kwargs): return 0.0, {}
    MASHUP_INTELLIGENCE = MashupIntelligence()
    print(f"[WARN] 无法挂载 Mashup Intelligence，微观评分已降级")

# 【Phase 11】导入 Aesthetic Curator 审美策展引擎
try:
    from skills.aesthetic_expert.scripts.curator import AestheticCurator
    AESTHETIC_CURATOR = AestheticCurator()
    AESTHETIC_ENABLED = True
    print(f"[OK] 已成功挂载 Aesthetic Curator V4 审美引擎")
except ImportError:
    AESTHETIC_ENABLED = False
    class AestheticCurator:
        def calculate_aesthetic_match(self, *args, **kwargs): return 70.0, {}
        def get_mix_bible_advice(self, *args, **kwargs): return {"technique": "Standard Mix", "suggested_duration": "16 bars", "vibe_target": "Neutral"}
    AESTHETIC_CURATOR = AestheticCurator()
    print(f"[WARN] 无法挂载 Aesthetic Curator，审美评分已降级")

# 【Phase 12】导入 Narrative Planner 叙事规划引擎 [Intelligence-V5]
try:
    from narrative_set_planner import NarrativePlanner
    from skill_intelligence_researcher import IntelligenceResearcher
    
    RESEARCHER = IntelligenceResearcher()
    NARRATIVE_PLANNER = NarrativePlanner(researcher=RESEARCHER)
    NARRATIVE_ENABLED = True
    print(f"[OK] 已成功挂载 Narrative Planner V5 & Intelligence Researcher")
except ImportError:
    # 尝试从 skills 目录导入
    try:
        from skills.skill_intelligence_researcher import IntelligenceResearcher
        from narrative_set_planner import NarrativePlanner
        RESEARCHER = IntelligenceResearcher()
        NARRATIVE_PLANNER = NarrativePlanner(researcher=RESEARCHER)
        NARRATIVE_ENABLED = True
        print(f"[OK] 已成功挂载 Narrative Planner V5 (from skills)")
    except ImportError:
        NARRATIVE_ENABLED = False
        class NarrativePlanner:
            def calculate_narrative_score(self, *args, **kwargs): return 0.0, {}
            def get_narrative_advice(self, *args, **kwargs): return ""
            def set_theme(self, theme): pass
        NARRATIVE_PLANNER = NarrativePlanner()
        RESEARCHER = None
        print(f"[WARN] 无法挂载 Narrative Planner，叙事匹配已停用")

# 【Phase 13】导入 Set Blueprinter 叙事蓝图引擎
try:
    from blueprinter import SetBlueprinter
    BLUEPRINTER = SetBlueprinter()
    BLUEPRINT_ENABLED = True
    print(f"[OK] 已成功挂载 Set Blueprinter V5 蓝图引擎")
except ImportError:
    try:
        from skills.set_curation_expert.scripts.blueprinter import SetBlueprinter
        BLUEPRINTER = SetBlueprinter()
        BLUEPRINT_ENABLED = True
        print(f"[OK] 已成功挂载 Set Blueprinter V5 (from skills)")
    except ImportError:
        BLUEPRINT_ENABLED = False
        class SetBlueprinter:
            def get_phase_target(self, progress): return (40, 70, "General", {})
        BLUEPRINTER = SetBlueprinter()
        print(f"[WARN] 无法挂载 Set Blueprinter，将使用硬编码阶段")

CACHE_FILE = Path(__file__).parent / "song_analysis_cache.json"
# 分析器版本号（用于缓存失效控制）
ANALYZER_VERSION = "v1.2-pro-dimensions"
# 模型版本字典（用于缓存失效控制）
DEFAULT_MODEL_VERSIONS = {
    "genre": "g1.0",  # 风格分类模型版本
    "key": "k1.0",    # 调性检测模型版本
    "bpm": "b1.0",    # BPM检测模型版本
    "energy": "e1.0", # 能量分析模型版本
    "vocal": "v1.0",  # 人声检测模型版本
}

# 导入进化战略配置
try:
    import evolution_config
    ACTIVE_PROFILE = evolution_config.PROFILES[evolution_config.DEFAULT_PROFILE]
except Exception as e:
    print(f"警告: 无法加载进化配置，将使用默认权重: {e}")
    ACTIVE_PROFILE = None

# 【Phase 8】导入配置管理器，读取 dj_rules.yaml
try:
    from config.split_config import get_config
    DJ_RULES = get_config()
    print(f"[OK] 已加载 dj_rules.yaml 配置".encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
except Exception as e:
    print(f"警告: 无法加载 dj_rules.yaml，将使用默认值: {e}")
    DJ_RULES = {}

# 导入全局优化引擎
try:
    from global_optimization_engine import optimize_global_sets
except ImportError:
    def optimize_global_sets(sets, config, progress_logger=None): return 0

def _lock_file_handle(f):
    """跨平台文件锁（简单独占锁），避免并发写坏缓存"""
    try:
        if os.name == "nt":
            import msvcrt
            # 锁1个字节；若文件过小，允许扩展
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
            except OSError:
                # 确保有至少1个字节
                f.seek(0, os.SEEK_END)
                if f.tell() == 0:
                    f.write("\0")
                    f.flush()
                    f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    except Exception:
        pass


def _unlock_file_handle(f):
    """解锁文件"""
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception:
        pass


@contextlib.contextmanager
def _locked_file(path: Path, mode: str):
    """
    简易文件锁上下文管理器
    - path: 文件路径
    - mode: 打开模式（r/w/a等），必须是文本模式（带编码）
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # 允许读模式在不存在时返回空内容
    if "r" in mode and not path.exists():
        yield None
        return
    f = open(path, mode, encoding="utf-8")
    _lock_file_handle(f)
    try:
        yield f
    finally:
        _unlock_file_handle(f)
        try:
            f.close()
        except Exception:
            pass


try:
    from common_utils import verify_file_exists
except ImportError:
    def verify_file_exists(p): return os.path.exists(p)

def load_cache():
    """加载分析缓存（加文件锁，避免并发读取/写入冲突）"""
    try:
        if not CACHE_FILE.exists():
            return {}
        with _locked_file(CACHE_FILE, "r") as f:
            if f is None: return {}
            data = json.load(f)
            return data
    except Exception:
        return {}

def save_cache_atomic(cache_data, cache_file):
    """原子性保存缓存，防止并发写入损坏文件"""
    import tempfile
    cache_path = Path(cache_file)
    temp_fd, temp_path = tempfile.mkstemp(dir=cache_path.parent, suffix=".tmp")
    try:
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        
        # 跨设备移动/替换
        if os.path.exists(cache_file):
            os.replace(temp_path, cache_file)
        else:
            os.rename(temp_path, cache_file)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e

def save_cache(cache):
    """保存分析缓存（统一入口）"""
    try:
        # 清理非JSON类型
        sanitized = make_json_serializable(cache)
        save_cache_atomic(sanitized, CACHE_FILE)
    except Exception as e:
        print(f"❌ 缓存保存失败: {e}")

def get_cached_analysis(file_path: str, cache: dict):
    """从缓存获取分析结果（极致兼容）"""
    if not file_path: return None
    file_path_str = str(file_path).replace('\\', '/')
    
    # 1. 第一优先级：路径哈希匹配（最准确）
    file_hash = get_file_hash(file_path_str)
    if file_hash and file_hash in cache:
        cached = cache[file_hash]
        if isinstance(cached, dict):
            return cached.get('analysis')

    # 2. 第二优先级：路径直接匹配 (针对旧版本缓存)
    for k, v in cache.items():
        if isinstance(v, dict) and v.get('file_path', '').replace('\\', '/') == file_path_str:
            return v.get('analysis')
            
    return None

def _validate_cache_entry(cached, file_path_str=None):
    """
    验证缓存条目是否有效（内部辅助函数）
    返回: (is_valid, needs_incremental_update)
    """
    if not cached:
        return False, False
        
    # 如果提供了路径，验证路径匹配
    if file_path_str:
        cached_path = cached.get('file_path', '').replace('\\', '/')
        if cached_path != file_path_str:
            return False, False
            
    # 检查分析器版本
    analyzer_ver = cached.get("analyzer_version")
    
    # 完全匹配：v1.2 且 包含关键新字段
    if analyzer_ver == ANALYZER_VERSION:
        analysis = cached.get('analysis', {})
        # 检查是否包含 v1.2 的关键新字段
        if "language" in analysis and "kick_hardness" in analysis and "true_start_sec" in analysis:
            return True, False
        else:
            # 虽然版本号对了，但可能中途出错没存全，标记为需要增量更新
            return True, True

    # 兼容匹配：如果是 v1.1，我们认为它有效，但需要增量更新（补全语言、底鼓等维度）
    if analyzer_ver == "v1.1-cachekey-mixability-prep" or analyzer_ver is None:
        return True, True
        
    # 版本差距过大：视为失效
    return False, False

def is_cache_entry_valid(cached_entry, file_path_str=None):
    """
    检查缓存条目是否有效（用于批量验证）
    
    Args:
        cached_entry: 缓存条目字典
        file_path_str: 文件路径（可选，如果提供则验证路径匹配）
    
    Returns:
        (is_valid, reason): (是否有效, 失效原因)
    """
    if not cached_entry:
        return (False, "entry_missing")
    
    # 检查analyzer版本
    analyzer_ver = cached_entry.get("analyzer_version")
    if analyzer_ver != ANALYZER_VERSION:
        return (False, f"analyzer_version_mismatch:{analyzer_ver}")
    
    # 检查模型版本
    cached_model_versions = cached_entry.get("model_versions", {})
    if cached_model_versions:
        for key in ["genre", "key", "bpm"]:
            if key in DEFAULT_MODEL_VERSIONS:
                if cached_model_versions.get(key) != DEFAULT_MODEL_VERSIONS[key]:
                    return (False, f"model_version_mismatch:{key}")
    
    # 如果提供了文件路径，验证路径匹配
    if file_path_str:
        cached_path = cached_entry.get('file_path', '').replace('\\', '/')
        if cached_path != file_path_str.replace('\\', '/'):
            return (False, "path_mismatch")
        
        # 验证文件元数据
        cached_mtime = cached_entry.get('mtime')
        cached_size = cached_entry.get('size')
        if cached_mtime is not None and cached_size is not None:
            try:
                stat = os.stat(file_path_str)
                if stat.st_mtime != cached_mtime:
                    return (False, "mtime_mismatch")
                if stat.st_size != cached_size:
                    return (False, "size_mismatch")
            except OSError:
                # 文件不存在，但保留缓存（可能文件暂时不可用）
                pass
    
    return (True, "valid")

def get_file_hash(file_path):
    """获取文件的唯一标识（路径+修改时间）"""
    try:
        # Windows 路径不区分大小写，统一转为小写并使用正斜杠
        file_path_str = str(file_path).replace('\\', '/').lower()
        stat = os.stat(file_path_str)
        # 使用路径 + mtime_ns + size 构建稳定指纹
        key_base = f"{file_path_str}|{stat.st_mtime_ns}|{stat.st_size}"
        return hashlib.sha1(key_base.encode('utf-8')).hexdigest()
    except:
        return None

def cache_analysis(file_path, analysis, cache):
    """缓存分析结果（增强版：包含完整元数据和多维标签）"""
    if not file_path or not analysis:
        return
        
    file_path_str = str(file_path).replace('\\', '/')
    file_hash = get_file_hash(file_path_str)
    
    if file_hash:
        try:
            stat = os.stat(file_path_str)
            cache[file_hash] = {
                'file_path': file_path_str,
                'mtime': stat.st_mtime,
                'size': stat.st_size,
                'analyzer_version': ANALYZER_VERSION,
                'model_versions': DEFAULT_MODEL_VERSIONS,
                'analysis': make_json_serializable(analysis),
                'timestamp': datetime.now().isoformat(),
                # V5.1联动：确保艺术家、标题、BPM等顶级元数据的冗余，方便其他模块检索
                'artist': analysis.get('artist', 'Unknown'),
                'title': analysis.get('title', 'Unknown'),
                'bpm': analysis.get('bpm', 120.0)
            }
            # 原子化保存
            save_cache(cache)
        except Exception as e:
            print(f"Warning: Failed to cache analysis for {file_path_str}: {e}")

try:
    import librosa
    import numpy as np
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False
    np = None

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


def auto_group_by_bpm(tracks: List[Dict], max_bpm_range: float = 25.0) -> List[List[Dict]]:
    """
    自动按BPM分组，确保每组内BPM跨度不超过max_bpm_range
    
    算法：
    1. 按BPM排序所有歌曲
    2. 使用动态规划找到最优分组点
    3. 每组内BPM跨度控制在max_bpm_range以内
    4. 尽量让每组歌曲数量均匀
    
    Returns:
        List[List[Dict]]: 分组后的歌曲列表，每组按BPM排序
    """
    if not tracks:
        return []
    
    # 过滤掉没有BPM的歌曲，单独处理
    tracks_with_bpm = [t for t in tracks if t.get('bpm') and t.get('bpm') > 0]
    tracks_without_bpm = [t for t in tracks if not t.get('bpm') or t.get('bpm') <= 0]
    
    if not tracks_with_bpm:
        return [tracks] if tracks else []
    
    # 按BPM排序
    sorted_tracks = sorted(tracks_with_bpm, key=lambda t: t.get('bpm', 0))
    
    # 动态分组：遍历找分割点
    groups = []
    current_group = [sorted_tracks[0]]
    group_min_bpm = sorted_tracks[0].get('bpm', 0)
    
    for track in sorted_tracks[1:]:
        track_bpm = track.get('bpm', 0)
        
        # 如果加入这首歌会超过BPM范围限制，开始新组
        if track_bpm - group_min_bpm > max_bpm_range:
            groups.append(current_group)
            current_group = [track]
            group_min_bpm = track_bpm
        else:
            current_group.append(track)
    
    # 添加最后一组
    if current_group:
        groups.append(current_group)
    
    # 将没有BPM的歌曲分配到最接近中速的组
    if tracks_without_bpm:
        # 找到中速组（BPM在100-130之间的组）
        mid_group_idx = 0
        for i, group in enumerate(groups):
            avg_bpm = sum(t.get('bpm', 0) for t in group) / len(group)
            if 100 <= avg_bpm <= 130:
                mid_group_idx = i
                break
        groups[mid_group_idx].extend(tracks_without_bpm)
    
    # 合并过小的组（少于5首），但要检查BPM差距
    merged_groups = []
    for group in groups:
        if len(group) < 5 and merged_groups:
            # 检查与前一组的BPM差距
            prev_bpms = [t.get('bpm', 0) for t in merged_groups[-1] if t.get('bpm')]
            curr_bpms = [t.get('bpm', 0) for t in group if t.get('bpm')]
            
            if prev_bpms and curr_bpms:
                bpm_gap = min(curr_bpms) - max(prev_bpms)
                # 只有BPM差距小于15才合并，否则保持独立
                if bpm_gap <= 15:
                    merged_groups[-1].extend(group)
                    continue
            else:
                # 没有BPM信息，直接合并
                merged_groups[-1].extend(group)
                continue
        
        merged_groups.append(group)
    
    return merged_groups


def smooth_bpm_sequence(tracks: List[Dict]) -> List[Dict]:
    """
    平滑BPM序列，避免大幅度跳跃
    
    策略：使用贪心算法，每次选择BPM最接近的下一首歌
    同时考虑调性兼容性作为次要因素
    """
    if len(tracks) <= 2:
        return tracks
    
    # 找到BPM中位数附近的歌曲作为起点
    bpms = [t.get('bpm', 0) for t in tracks if t.get('bpm')]
    if not bpms:
        return tracks
    
    median_bpm = sorted(bpms)[len(bpms) // 2]
    
    # 选择最接近中位数BPM的歌曲作为起点
    start_track = min(tracks, key=lambda t: abs(t.get('bpm', 0) - median_bpm))
    
    result = [start_track]
    remaining = [t for t in tracks if t != start_track]
    
    while remaining:
        current = result[-1]
        current_bpm = current.get('bpm', 0)
        current_key = current.get('key', '')
        
        # 找BPM最接近的歌曲，调性作为次要因素
        best_track = None
        best_score = float('inf')
        
        for track in remaining:
            track_bpm = track.get('bpm', 0)
            track_key = track.get('key', '')
            
            # BPM差距（主要因素）
            bpm_diff = abs(track_bpm - current_bpm)
            
            # 调性兼容性（次要因素，0-100分转换为0-10的惩罚）
            key_score = get_key_compatibility_flexible(current_key, track_key)
            key_penalty = (100 - key_score) / 10  # 0-10
            
            # 综合分数（BPM差距 + 调性惩罚）
            score = bpm_diff + key_penalty
            
            if score < best_score:
                best_score = score
                best_track = track
        
        if best_track:
            result.append(best_track)
            remaining.remove(best_track)
        else:
            break
    
    return result


def get_bpm_group_label(group: List[Dict]) -> str:
    """获取BPM组的标签描述"""
    if not group:
        return "Empty"
    
    bpms = [t.get('bpm', 0) for t in group if t.get('bpm')]
    if not bpms:
        return "Unknown BPM"
    
    min_bpm = min(bpms)
    max_bpm = max(bpms)
    avg_bpm = sum(bpms) / len(bpms)
    
    # 根据平均BPM给出描述
    if avg_bpm < 90:
        tempo_label = "慢歌"
    elif avg_bpm < 115:
        tempo_label = "中慢速"
    elif avg_bpm < 130:
        tempo_label = "中速"
    elif avg_bpm < 145:
        tempo_label = "中快速"
    elif avg_bpm < 165:
        tempo_label = "快歌"
    else:
        tempo_label = "超快"
    
    return f"{tempo_label} ({min_bpm:.0f}-{max_bpm:.0f} BPM)"


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
    
    使用LRU缓存提升性能（重复生成Set时提升50-70%）
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

@lru_cache(maxsize=10000)
def get_bpm_compatibility_flexible(current_bpm: float, next_bpm: float) -> int:
    """
    灵活版BPM兼容性检查
    
    使用LRU缓存提升性能（重复生成Set时提升50-70%）
    """
    if not current_bpm or not next_bpm:
        return 60
    
    diff = abs(current_bpm - next_bpm)
    
    if diff <= 2:
        return 100  # 非常平滑
    elif diff <= 4:
        return 90
    elif diff <= 6:
        return 80
    elif diff <= 8:
        return 70
    elif diff <= 12:
        return 60  # 允许较大跨度
    elif diff <= 16:
        return 50
    elif diff <= 20:
        return 40
    else:
        return 30

def compare_rhythm_similarity(track_a: dict, track_b: dict) -> float:
    """
    基于onset方差的节奏相似度比较（更稳定版本）
    
    使用onset_std（onset强度标准差）来比较节奏变化模式
    相似度范围：0.0-1.0
    
    优点：
    - 更稳定：不受onset识别稀疏影响
    - 更准确：能捕捉节奏变化模式（稳定 vs 变化大）
    - 避免异常：对异常值不敏感
    
    Returns:
        float: 相似度分数（1.0表示完全相同，0.0表示完全不同）
    """
    # 从energy_profile中获取onset_std
    profile_a = track_a.get('energy_profile', {})
    profile_b = track_b.get('energy_profile', {})
    
    # 获取onset_std（如果存在）
    std_a = profile_a.get('onset_std', None)
    std_b = profile_b.get('onset_std', None)
    
    # 如果缺少数据，返回中等相似度（不惩罚也不奖励）
    if std_a is None or std_b is None:
        return 0.5
    
    # 计算方差差异（归一化到0-1）
    std_diff = abs(std_a - std_b)
    
    # 归一化相似度（差异越小，相似度越高）
    # 直接归一化，因为方差已经在0-1范围内
    similarity = 1.0 - min(std_diff, 1.0)
    
    return similarity


def optimize_mix_points_with_windows(current_track: dict, next_track: dict) -> Tuple[float, float]:
    """
    【P1优化】使用mixable_windows优化混音点选择
    
    Returns:
        (optimized_mix_out, optimized_mix_in)
    """
    # 获取原始混音点
    curr_mix_out = current_track.get('mix_out_point')
    next_mix_in = next_track.get('mix_in_point')
    
    # 获取mixable_windows
    curr_windows = current_track.get('mixable_windows', [])
    next_windows = next_track.get('mixable_windows', [])
    
    # 如果没有windows数据，返回原始混音点
    if not curr_windows or not next_windows:
        return (curr_mix_out, next_mix_in)
    
    try:
        # 当前歌曲：找最后一个适合混出的窗口
        # mixable_windows格式: [(start, end, quality_score), ...]
        best_mix_out = curr_mix_out
        best_out_score = 0
        
        for window in curr_windows:
            if len(window) >= 3:
                start, end, quality = window[0], window[1], window[2]
                # 选择靠近原始mix_out_point的高质量窗口
                if curr_mix_out:
                    distance = abs((start + end) / 2 - curr_mix_out)
                    # 质量高且距离近的窗口优先
                    score = quality / (1 + distance / 10)
                    if score > best_out_score:
                        best_out_score = score
                        best_mix_out = (start + end) / 2
        
        # 下一首歌曲：找第一个适合混入的窗口
        best_mix_in = next_mix_in
        best_in_score = 0
        
        for window in next_windows:
            if len(window) >= 3:
                start, end, quality = window[0], window[1], window[2]
                # 选择靠近原始mix_in_point的高质量窗口
                if next_mix_in is not None:
                    distance = abs((start + end) / 2 - next_mix_in)
                    # 质量高且距离近的窗口优先
                    score = quality / (1 + distance / 10)
                    if score > best_in_score:
                        best_in_score = score
                        best_mix_in = (start + end) / 2
        
        return (best_mix_out, best_mix_in)
    
    except Exception:
        # 如果优化失败，返回原始混音点
        return (curr_mix_out, next_mix_in)


def calculate_beat_alignment(current_track: dict, next_track: dict) -> Tuple[float, float]:
    """
    计算Beat对齐（16小节对齐 = 64拍对齐）
    
    DJ混音核心要求：必须16小节对齐，否则会出现节拍错位
    
    修复：如果BPM差>5，beat对齐已经不可能，直接返回0分
    【新增】支持不同拍号（4/4、3/4等）
    
    Args:
        current_track: 当前歌曲
        next_track: 下一首歌曲
    
    Returns:
        (beat_offset_diff, alignment_score)
        - beat_offset_diff: 强拍偏移（拍数）
        - alignment_score: 对齐评分（0-100，100表示完美对齐）
    """
    curr_bpm = current_track.get('bpm', 0)
    next_bpm = next_track.get('bpm', 0)
    # 【修复】字段名应该是 downbeat_offset，不是 beat_offset
    curr_beat_offset = current_track.get('downbeat_offset', 0)  # 第一拍偏移（可能是秒或拍）
    next_beat_offset = next_track.get('downbeat_offset', 0)
    curr_duration = current_track.get('duration', 0)
    curr_mix_out = current_track.get('mix_out_point', curr_duration * 0.85)  # 默认85%处混出
    next_mix_in = next_track.get('mix_in_point', 0)  # 默认开头混入
    
    # 【新增】获取拍号信息
    curr_time_sig = current_track.get('time_signature', '4/4')
    next_time_sig = next_track.get('time_signature', '4/4')
    curr_beats_per_bar = current_track.get('beats_per_bar', 4)
    next_beats_per_bar = next_track.get('beats_per_bar', 4)
    
    if curr_bpm <= 0 or next_bpm <= 0 or curr_duration <= 0:
        return (0.0, 50.0)  # 数据缺失，返回中等评分
    
    # ========== 【修复1C】数学修复：单位归一化 ==========
    # 统一 normalize downbeat_offset 单位到 beats（便于比较）
    def _normalize_offset(track_offset, bpm):
        if track_offset is None:
            return None
        offset_val = float(track_offset)
        # 如果看起来是以秒为单位（< 5.0 秒），转换为拍数
        if abs(offset_val) < 5.0 and bpm > 0:
            return offset_val * float(bpm) / 60.0
        # 否则可能已经是 beat 数
        return offset_val
    
    curr_off_beats = _normalize_offset(curr_beat_offset, curr_bpm)
    next_off_beats = _normalize_offset(next_beat_offset, next_bpm)
    
    # ========== 修复：BPM差>5时，beat对齐已经不可能 ==========
    bpm_diff = abs(curr_bpm - next_bpm)
    if bpm_diff > 5:
        # BPM差>5时，beat对齐已经不可能，返回0分
        return (999.0, 0.0)  # 返回极大偏移值，表示无法对齐
    
    # 【新增】如果拍号不同，对齐可能不准确（但允许尝试）
    if curr_time_sig != next_time_sig:
        # 拍号不同，降低对齐评分权重（但不完全禁止）
        pass  # 继续计算，但会在评分中考虑
    
    # 计算当前歌曲混出点的绝对时间（从歌曲开始）
    curr_mix_out_time = curr_mix_out
    
    # 计算下一首歌曲混入点的绝对时间（从歌曲开始）
    next_mix_in_time = next_mix_in
    
    # ========== 【P0优化】移除downbeat_confidence检查 ==========
    # 原因：诊断发现所有downbeat_confidence都是0.5（数据无效）
    # 修改：移除置信度检查，避免所有歌曲都被判定为"无法对齐"
    # 注释掉原有的置信度检查代码
    # curr_downbeat_conf = current_track.get('downbeat_confidence', 1.0)
    # next_downbeat_conf = next_track.get('downbeat_confidence', 1.0)
    # if curr_downbeat_conf < 0.6 or next_downbeat_conf < 0.6:
    #     return (999.0, 0.0)
    
    # 【修复】计算当前歌曲混出点距离第一拍的时间偏移（使用归一化后的拍数）
    if curr_off_beats is not None and curr_off_beats != 0:
        # 将拍数转换为时间，然后计算偏移
        curr_beat_time = (curr_off_beats % curr_beats_per_bar) * (60.0 / curr_bpm)
        curr_mix_out_beat_offset = (curr_mix_out_time - curr_beat_time) % (60.0 / curr_bpm)
    else:
        # 如果没有downbeat_offset，使用mix_out_point计算（可能不准确）
        # 【P0优化】移除置信度检查（因为数据无效）
        curr_mix_out_beat_offset = curr_mix_out_time % (60.0 / curr_bpm)
    
    # 【修复】计算下一首歌曲混入点距离第一拍的时间偏移（使用归一化后的拍数）
    if next_off_beats is not None and next_off_beats != 0:
        # 将拍数转换为时间，然后计算偏移
        next_beat_time = (next_off_beats % next_beats_per_bar) * (60.0 / next_bpm)
        next_mix_in_beat_offset = (next_mix_in_time - next_beat_time) % (60.0 / next_bpm)
    else:
        # 如果没有downbeat_offset，直接使用mix_in_point计算（可能不准确）
        next_mix_in_beat_offset = next_mix_in_time % (60.0 / next_bpm)
    
    # 【优化】根据拍号转换为拍数（不再假设4/4拍）
    # 对于4/4拍：1小节=4拍
    # 对于3/4拍：1小节=3拍
    # 对于6/8拍：1小节=6拍（但通常按2拍计算）
    curr_beats = curr_mix_out_beat_offset / (60.0 / curr_bpm)
    next_beats = next_mix_in_beat_offset / (60.0 / next_bpm)
    
    # 计算强拍偏移（拍数）
    beat_offset_diff = abs(curr_beats - next_beats)
    
    # 【新增】如果拍号不同，调整对齐评分
    if curr_time_sig != next_time_sig:
        # 拍号不同时，对齐可能不准确，增加偏移容忍度
        # 例如：4/4拍和3/4拍混音时，需要特殊处理
        beat_offset_diff *= 1.2  # 增加20%的偏移容忍度
    
    # 对齐评分：完美对齐（0拍偏移）= 100分，每偏移1拍扣10分
    if beat_offset_diff <= 0.5:  # ±0.5拍以内，完美对齐
        alignment_score = 100.0
    elif beat_offset_diff <= 1.0:  # ±1拍以内，优秀
        alignment_score = 90.0
    elif beat_offset_diff <= 2.0:  # ±2拍以内，可接受
        alignment_score = 70.0
    elif beat_offset_diff <= 4.0:  # ±4拍以内，需要调整
        alignment_score = 40.0
    else:  # ±4拍以上，严重错位
        alignment_score = 0.0
    
    # ========== P0-2优化：强拍偏移量化并自动建议修正 ==========
    beatgrid_fix_hints = {}
    needs_manual_alignment = False
    try:
        from beatgrid_fix_helper import calculate_phase_shift_correction
        
        fix_result = calculate_phase_shift_correction(current_track, next_track)
        if fix_result.get("needs_manual_alignment"):
            needs_manual_alignment = True
        
        # 为当前和下一首分别生成修正建议
        current_fix = fix_result.get("current_track_fix", {})
        next_fix = fix_result.get("next_track_fix", {})
        
        if current_fix.get("hint_text"):
            beatgrid_fix_hints["current"] = current_fix["hint_text"]
        if next_fix.get("hint_text"):
            beatgrid_fix_hints["next"] = next_fix["hint_text"]
        
        if fix_result.get("recommendation"):
            beatgrid_fix_hints["recommendation"] = fix_result["recommendation"]
    except ImportError:
        # 模块不存在，跳过
        pass
    except Exception:
        # 计算失败，跳过
        pass
    
    return (beat_offset_diff, alignment_score, beatgrid_fix_hints, needs_manual_alignment)


def calculate_drop_alignment(current_track: dict, next_track: dict) -> Tuple[float, float]:
    """
    计算Drop对齐（32小节对齐 = 128拍对齐）
    
    DJ混音高级技巧：Drop对齐可以让两首歌的Drop同时出现，产生强烈冲击
    
    修复：如果BPM差>5，drop对齐已经不可能，直接返回0分
    
    Args:
        current_track: 当前歌曲
        next_track: 下一首歌曲
    
    Returns:
        (drop_offset_diff, alignment_score)
        - drop_offset_diff: Drop偏移（拍数）
        - alignment_score: 对齐评分（0-100，100表示完美对齐）
    """
    curr_bpm = current_track.get('bpm', 0)
    next_bpm = next_track.get('bpm', 0)
    curr_first_drop = current_track.get('first_drop_time', None)
    next_first_drop = next_track.get('first_drop_time', None)
    curr_duration = current_track.get('duration', 0)
    curr_mix_out = current_track.get('mix_out_point', curr_duration * 0.85)
    next_mix_in = next_track.get('mix_in_point', 0)
    
    if curr_bpm <= 0 or next_bpm <= 0 or curr_duration <= 0:
        return (0.0, 50.0)  # 数据缺失，返回中等评分
    
    # ========== 修复：BPM差>5时，drop对齐已经不可能 ==========
    bpm_diff = abs(curr_bpm - next_bpm)
    if bpm_diff > 5:
        # BPM差>5时，drop对齐已经不可能，返回0分
        return (999.0, 0.0)  # 返回极大偏移值，表示无法对齐
    
    # 如果没有Drop时间信息，使用默认值（通常Drop在歌曲30-40%处）
    if curr_first_drop is None:
        curr_first_drop = curr_duration * 0.35
    if next_first_drop is None:
        next_first_drop = next_track.get('duration', 180) * 0.35
    
    # 计算当前歌曲混出点距离Drop的时间
    curr_drop_distance = curr_first_drop - curr_mix_out
    
    # 计算下一首歌曲混入点距离Drop的时间
    next_drop_distance = next_first_drop - next_mix_in
    
    # 转换为拍数（32小节 = 128拍）
    curr_beats = curr_drop_distance / (60.0 / curr_bpm)
    next_beats = next_drop_distance / (60.0 / next_bpm)
    
    # 计算Drop偏移（拍数）
    drop_offset_diff = abs(curr_beats - next_beats)
    
    # 对齐评分：完美对齐（0拍偏移）= 100分，每偏移16拍扣20分
    if drop_offset_diff <= 4.0:  # ±4拍以内，完美对齐
        alignment_score = 100.0
    elif drop_offset_diff <= 8.0:  # ±8拍以内，优秀
        alignment_score = 80.0
    elif drop_offset_diff <= 16.0:  # ±16拍以内，可接受
        alignment_score = 60.0
    elif drop_offset_diff <= 32.0:  # ±32拍以内，需要调整
        alignment_score = 30.0
    else:  # ±32拍以上，严重错位
        alignment_score = 0.0
    
    return (drop_offset_diff, alignment_score)


def compare_mfcc_similarity(track_a: dict, track_b: dict) -> float:
    """
    比较MFCC特征相似度（音色连续性）
    
    使用余弦相似度比较MFCC特征
    相似度范围：0.0-1.0
    
    优点：
    - 捕捉音色、音质等特征
    - 避免音色氛围突然跳转
    - 提升Set连贯性
    
    Returns:
        float: 相似度分数（1.0表示音色完全相同，0.0表示完全不同）
    """
    import numpy as np
    
    # 从energy_profile中获取mfcc_mean
    profile_a = track_a.get('energy_profile') or {}
    profile_b = track_b.get('energy_profile') or {}
    
    # 获取mfcc_mean（如果存在）
    mfcc_a = profile_a.get('mfcc_mean', None) if isinstance(profile_a, dict) else None
    mfcc_b = profile_b.get('mfcc_mean', None) if isinstance(profile_b, dict) else None
    
    # 如果缺少数据，返回中等相似度（不惩罚也不奖励）
    if mfcc_a is None or mfcc_b is None:
        return 0.5
    
    # 转换为numpy数组
    try:
        mfcc_a = np.array(mfcc_a)
        mfcc_b = np.array(mfcc_b)
        
        # 确保维度一致
        if mfcc_a.shape != mfcc_b.shape:
            return 0.5
        
        # 计算余弦相似度
        # 余弦相似度 = (A · B) / (||A|| * ||B||)
        dot_product = np.dot(mfcc_a, mfcc_b)
        norm_a = np.linalg.norm(mfcc_a)
        norm_b = np.linalg.norm(mfcc_b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.5
        
        similarity = dot_product / (norm_a * norm_b)
        
        # 确保相似度在0-1范围内
        similarity = max(0.0, min(1.0, similarity))
        
        return float(similarity)
    except Exception:
        # 如果计算失败，返回中等相似度
        return 0.5


def check_vocal_conflict(current_track: dict, next_track: dict) -> Tuple[float, bool]:
    """
    【V6.3新增】检查人声冲突
    
    检测两首歌混音时人声段落是否会重叠：
    - 当前歌曲的outro人声 vs 下一首的intro人声
    - 重叠>50%：严重冲突，扣30分
    - 重叠30-50%：轻微冲突，扣15分
    - 重叠<30%：可接受
    
    Args:
        current_track: 当前歌曲
        next_track: 下一首歌曲
    
    Returns:
        (penalty, has_conflict): 惩罚分数和是否有冲突
    """
    curr_vocal = current_track.get('vocal_segments', [])
    next_vocal = next_track.get('vocal_segments', [])
    
    if not curr_vocal or not next_vocal:
        return 0, False  # 无人声数据，不扣分
    
    # 计算混音区域的人声重叠
    curr_duration = current_track.get('duration', 0)
    next_duration = next_track.get('duration', 0)
    
    if curr_duration == 0 or next_duration == 0:
        return 0, False
    
    # 混音区域：当前歌曲的最后30% vs 下一首的前30%
    curr_mix_start = curr_duration * 0.7
    next_mix_end = next_duration * 0.3
    
    # 计算重叠比例
    overlap_ratio = calculate_vocal_overlap(
        curr_vocal, next_vocal,
        curr_mix_start, curr_duration,
        0, next_mix_end
    )
    
    if overlap_ratio > 0.5:
        return -30, True  # 严重冲突
    elif overlap_ratio > 0.3:
        return -15, True  # 轻微冲突
    else:
        return 0, False  # 可接受


def calculate_vocal_overlap(
    curr_vocal: List[Tuple[float, float]], 
    next_vocal: List[Tuple[float, float]],
    curr_start: float, curr_end: float,
    next_start: float, next_end: float
) -> float:
    """
    计算人声段落重叠比例
    
    Args:
        curr_vocal: 当前歌曲的人声段落列表 [(start, end), ...]
        next_vocal: 下一首的人声段落列表 [(start, end), ...]
        curr_start, curr_end: 当前歌曲的混音区域
        next_start, next_end: 下一首的混音区域
    
    Returns:
        overlap_ratio: 重叠比例（0.0-1.0）
    """
    # 提取混音区域内的人声段落
    curr_vocal_in_mix = []
    for start, end in curr_vocal:
        if end > curr_start and start < curr_end:
            # 有重叠
            overlap_start = max(start, curr_start)
            overlap_end = min(end, curr_end)
            curr_vocal_in_mix.append((overlap_start, overlap_end))
    
    next_vocal_in_mix = []
    for start, end in next_vocal:
        if end > next_start and start < next_end:
            # 有重叠
            overlap_start = max(start, next_start)
            overlap_end = min(end, next_end)
            next_vocal_in_mix.append((overlap_start, overlap_end))
    
    if not curr_vocal_in_mix or not next_vocal_in_mix:
        return 0.0  # 没有人声重叠
    
    # 计算人声总时长
    curr_vocal_duration = sum(end - start for start, end in curr_vocal_in_mix)
    next_vocal_duration = sum(end - start for start, end in next_vocal_in_mix)
    
    # 计算重叠比例（相对于较短的人声段落）
    min_vocal_duration = min(curr_vocal_duration, next_vocal_duration)
    
    if min_vocal_duration == 0:
        return 0.0
    
    # 假设混音时两段人声会同时播放
    # 重叠比例 = min(curr_vocal_duration, next_vocal_duration) / mix_duration
    mix_duration = (curr_end - curr_start + next_end - next_start) / 2
    
    if mix_duration == 0:
        return 0.0
    
    overlap_ratio = min_vocal_duration / mix_duration
    
    return min(1.0, overlap_ratio)


def get_phase_number(phase_name: str) -> int:
    """
    获取阶段编号（用于单峰结构约束）
    
    阶段顺序：Warm-up(0) → Build-up(1) → Peak(2) → Intense(3) → Cool-down(4)
    """
    phase_map = {
        "Warm-up": 0,
        "Build-up": 1,
        "Peak": 2,
        "Intense": 3,
        "Cool-down": 4
    }
    return phase_map.get(phase_name, 1)  # 默认Build-up


def check_phase_constraint(current_phase_num: int, candidate_phase_num: int, 
                          max_phase_reached: int, in_cool_down: bool) -> tuple:
    """
    检查阶段约束（确保单峰结构）
    
    规则：
    - 只能前进，不能后退（除了Cool-down是最终阶段）
    - Intense后只能是Cool-down
    - Cool-down后不能再回到其他阶段
    
    返回: (is_valid, penalty_score)
        is_valid: 是否符合约束
        penalty_score: 不符合时的扣分（负数）
    """
    # 如果已经在Cool-down阶段，不能再回到其他阶段
    if in_cool_down:
        if candidate_phase_num < 4:  # 不是Cool-down
            return (False, -200)  # 严重违反，大幅扣分
        return (True, 0)  # Cool-down可以继续
    
    # 如果当前是Intense阶段，下一首必须是Cool-down
    if current_phase_num == 3:  # Intense
        if candidate_phase_num != 4:  # 不是Cool-down
            return (False, -150)  # 严重违反
        return (True, 0)
    
    # 如果候选阶段小于当前阶段（后退），不允许
    if candidate_phase_num < current_phase_num:
        # 特殊情况：如果还没到达过Peak，允许小幅后退（但扣分）
        if max_phase_reached < 2:  # 还没到Peak
            return (True, -30)  # 允许但扣分
        else:
            return (False, -100)  # 已到过Peak，不允许后退
    
    # 如果候选阶段超过max_phase_reached太多，轻微扣分（允许但鼓励渐进）
    if candidate_phase_num > max_phase_reached + 1:
        return (True, -20)  # 允许但扣分（鼓励渐进）
    
    # 其他情况：符合约束
    return (True, 0)


def get_energy_phase_target(current_position: float, total_tracks: int, 
                            current_bpm: float = None, current_energy: float = None,
                            sorted_tracks: List[Dict] = None, current_track: Dict = None) -> tuple:
    """
    根据当前位置强制分配能量阶段（V5优化：按位置硬分配）
    返回: (min_energy, max_energy, phase_name)
    
    【V5优化】强制按Set位置分配阶段，确保每个Set都有完整的能量曲线
    - 不再依赖歌曲实际能量值，而是强制按位置分配
    - 确保每个Set都有Warm-up → Build-up → Peak → Cooldown结构
    """
    if sorted_tracks is None:
        sorted_tracks = []
    
    progress = (current_position + 1) / max(total_tracks, 1)  # 0..1，基于位置
    
    # 【V5优化】优先使用蓝图引擎进行阶段分配
    if BLUEPRINT_ENABLED:
        base_min, base_max, phase_name, _ = BLUEPRINTER.get_phase_target(progress)
    else:
        # 【备选】硬分配阶段逻辑
        if progress <= 0.20:
            base_min, base_max, phase_name = (30, 55, "Warm-up")
        elif progress <= 0.40:
            base_min, base_max, phase_name = (50, 70, "Build-up")
        elif progress <= 0.75:
            base_min, base_max, phase_name = (65, 85, "Peak")
        elif progress <= 0.90:
            base_min, base_max, phase_name = (70, 90, "Sustain")
        else:
            base_min, base_max, phase_name = (45, 70, "Cool-down")
    
    # 分析已排序歌曲的实际能量趋势（用于验证和微调）
    if len(sorted_tracks) > 0:
        recent_energies = [t.get('energy', 50) for t in sorted_tracks[-5:] if isinstance(t.get('energy'), (int, float))]
        avg_recent_energy = sum(recent_energies) / len(recent_energies) if recent_energies else 50
        max_energy_reached = max([t.get('energy', 50) for t in sorted_tracks if isinstance(t.get('energy'), (int, float))], default=50)
        recent_phases = [t.get('assigned_phase') for t in sorted_tracks[-3:] if t.get('assigned_phase')]
        
        # 【修复】微调逻辑：确保不会破坏Peak和Cool-down阶段
        # 如果已排序歌曲的平均能量明显高于当前阶段，提升阶段（但不破坏Cool-down）
        if avg_recent_energy >= 65 and progress > 0.25 and progress < 0.90 and phase_name in ["Warm-up", "Build-up"]:
            phase_name = "Peak"
            base_min, base_max = (65, 85)
        elif avg_recent_energy >= 50 and progress > 0.1 and progress < 0.90 and phase_name == "Warm-up":
            phase_name = "Build-up"
            base_min, base_max = (50, 70)
        
        # 如果最高能量已经达到Intense水平，可以进入Intense（但不破坏Cool-down）
        if max_energy_reached >= 70 and progress > 0.5 and progress < 0.90 and phase_name in ["Warm-up", "Build-up", "Peak"]:
            if progress > 0.6:
                phase_name = "Sustain"  # 使用Sustain而不是Intense，保持一致性
                base_min, base_max = (70, 90)
            elif progress > 0.4:
                phase_name = "Peak"
                base_min, base_max = (65, 85)
        
        # 【修复】确保最后10%必须是Cool-down（除非能量极高）
        if progress >= 0.90 and max_energy_reached < 85:
            phase_name = "Cool-down"
            base_min, base_max = (45, 70)
    
    # 【优化】根据BPM和能量综合判断快歌/慢歌（不仅基于BPM）
    # 对于流行歌，BPM可能不好分辨，需要结合能量、节奏密度等综合判断
    if current_bpm is not None and current_bpm > 0:
        # 综合判断快歌/慢歌（不仅基于BPM）
        # 考虑因素：BPM、能量强度、节奏密度
        is_fast_song = False
        is_slow_song = False
        
        # 方法1：基于BPM的初步判断
        if current_bpm > 130:
            is_fast_song = True
        elif current_bpm < 100:
            is_slow_song = True
        elif 100 <= current_bpm <= 130:
            # 中等BPM范围（100-130），需要结合能量判断
            # 如果能量很高（>70），即使BPM中等，也可能是快歌
            if current_energy is not None and current_energy > 70:
                is_fast_song = True
            # 如果能量很低（<40），即使BPM中等，也可能是慢歌
            elif current_energy is not None and current_energy < 40:
                is_slow_song = True
        
        # 方法2：如果current_track中有能量特征信息，可以进一步验证
        if current_track:
            # 检查节奏密度（groove_density）和鼓点比例（perc_ratio）
            groove_density = current_track.get('groove_density', 0.5)
            perc_ratio = current_track.get('perc_ratio', 0.5)
            
            # 如果节奏密度高且鼓点比例高，更可能是快歌
            if groove_density > 0.6 and perc_ratio > 0.4:
                is_fast_song = True
            # 如果节奏密度低且鼓点比例低，更可能是慢歌
            elif groove_density < 0.4 and perc_ratio < 0.3:
                is_slow_song = True
        
        # 方法3：如果sorted_tracks中有能量特征信息，也可以参考
        elif sorted_tracks and len(sorted_tracks) > 0:
            # 获取当前歌曲的能量特征（如果有）
            current_track_info = None
            for track in sorted_tracks:
                if track.get('bpm', 0) == current_bpm:
                    current_track_info = track
                    break
            
            if current_track_info:
                # 检查节奏密度（groove_density）和鼓点比例（perc_ratio）
                groove_density = current_track_info.get('groove_density', 0.5)
                perc_ratio = current_track_info.get('perc_ratio', 0.5)
                
                # 如果节奏密度高且鼓点比例高，更可能是快歌
                if groove_density > 0.6 and perc_ratio > 0.4:
                    is_fast_song = True
                # 如果节奏密度低且鼓点比例低，更可能是慢歌
                elif groove_density < 0.4 and perc_ratio < 0.3:
                    is_slow_song = True
        
        # 应用快歌/慢歌的判断结果
        if is_fast_song:
            # 快歌不应该放在Warm-up阶段（除非是开头几首）
            if phase_name == "Warm-up" and progress > 0.05:  # 不是前5%
                # 提升到Build-up阶段
                phase_name = "Build-up"
                base_min, base_max = (50, 70)
            elif phase_name == "Cool-down" and progress < 0.95:  # 不是最后5%
                # 避免快歌过早进入Cool-down
                if progress < 0.85:
                    phase_name = "Intense"
                    base_min, base_max = (70, 90)
        elif is_slow_song:
            # 慢歌不应该放在Peak/Intense阶段（除非是高潮部分）
            if phase_name in ["Peak", "Intense"] and progress < 0.5:  # 前50%
                # 降低到Build-up阶段
                phase_name = "Build-up"
                base_min, base_max = (50, 70)
    
    return (base_min, base_max, phase_name)

def _calculate_candidate_score(track_data: tuple) -> tuple:
    """
    计算单个候选歌曲的得分（用于并行处理）
    
    参数:
        track_data: (track, current_track, current_bpm, min_energy, max_energy, phase_name, sorted_tracks, is_boutique)
    
    返回:
        (score, track, metrics)
    """
    track, current_track, current_bpm, min_energy, max_energy, phase_name, sorted_tracks, is_boutique = track_data
    
    if track.get('_used'):
        return (-999999, track, {})
    
    next_bpm = track.get('bpm', 0)
    bpm_diff = abs(current_bpm - next_bpm)
    bpm_change = next_bpm - current_bpm  # 正数=上升，负数=下降
    
    score = 0
    metrics = {
        "bpm_diff": bpm_diff,
        "bpm_change": bpm_change,
        "key_score": None,
        "percussive_diff": None,
        "dyn_var_diff": None,
        "style_penalty": False,
        "rhythm_penalty": False,
        "phase_penalty": False,
        "missing_profile": False,
        "fallback": False,
        "beat_offset_diff": None,
        "drop_offset_diff": None,
        "mi_score": 0.0,
        "mi_details": {},
        "ae_score": 70.0,
        "ae_details": {},
        "narrative_score": 0.0,
        "narrative_details": {},
        "audit_trace": []  # 【V6.0 Audit】审计追踪
    }
    
    def add_trace(key, val, impact, msg=""):
        metrics["audit_trace"].append({"dim": key, "val": val, "score": impact, "reason": msg})
    
    # ========== 【V7-PRO】微观维度注入：Mashup 兼容性评分 (30% 权重调节) ==========
    if MASHUP_ENABLED and current_track:
        # 计算微观兼容性得分 (11 维度)
        mi_score, mi_details = MASHUP_INTELLIGENCE.calculate_mashup_score(current_track, track, mode='set_sorting')
        
        metrics["mi_score"] = mi_score
        metrics["mi_details"] = mi_details
        
        # 将 mi_score 映射到 Sorter 的权重体系
        score += mi_score * 0.3 
        
        # 【V6.2】频谱掩蔽显性化审计
        if 'bass_clash' in mi_details:
            add_trace("Spectral Masking", "Bass Clash", -50, mi_details['bass_clash'])
        
        # 频谱掩蔽严重冲突惩罚
        if mi_score < 40 and not is_boutique:
             score -= 50
        elif mi_score < 30:
             score -= 150
             
    # ========== 【Phase 11】审美维度注入：Aesthetic Curator (审美一致性) ==========
    if AESTHETIC_ENABLED and current_track:
        ae_score, ae_details = AESTHETIC_CURATOR.calculate_aesthetic_match(current_track, track)
        metrics["ae_score"] = ae_score
        metrics["ae_details"] = ae_details
        
        # 【V4.0/V5.0 暂时禁用】按用户需求：标签/审美评分暂时不影响 Set 排序结果
        # score += (ae_score - 70) * 0.5
        pass

    # ========== 【Intelligence-V5】叙事维度注入：Narrative Planner (文化策展) ==========
    if NARRATIVE_ENABLED and current_track:
        nr_score, nr_details = NARRATIVE_PLANNER.calculate_narrative_score(current_track, track)
        metrics["narrative_score"] = nr_score
        metrics["narrative_details"] = nr_details
        
        # 【V5.0 暂时禁用】按用户需求：叙事评分暂时不影响 Set 排序结果
        # score += nr_score * 0.8
        pass
    
    # 获取 Profile 权重
    bpm_weight = 1.0
    if ACTIVE_PROFILE:
        bpm_weight = ACTIVE_PROFILE.weights.get("bpm_match", 100) / 100.0

    # ========== 【Boutique】精品模式硬性约束 ==========
    if is_boutique:
        # 1. 严格BPM约束：跨度超过8.0直接视为绝对不和谐（除非别无选择，但精品模式宁愿Set短一点）
        if bpm_diff > 8.0:
            return (-500000, track, {"boutique_rejected": "bpm_delta_too_high"})
        
        # 2. 调性兼容性预检
        key_score_pre = get_key_compatibility_flexible(current_track.get('key', ''), track.get('key', ''))
        # 调性得分低于80（非相邻、非相对、非跳跃3格）在精品模式下视为不合格
        if key_score_pre < 80:
            return (-400000, track, {"boutique_rejected": "key_incompatible"})
        
        # 3. 风格/能量防撞
        if track.get('energy', 50) > current_track.get('energy', 50) + 30:
            return (-300000, track, {"boutique_rejected": "energy_jump_too_high"})
    
    
    # ========== 【V6.2】节奏维度注入：拍号与律动 DNA (Rhythmic Integrity) ==========
    current_ts = current_track.get('time_signature', '4/4')
    next_ts = track.get('time_signature', '4/4')
    
    if current_ts != next_ts:
        # P0 级严重冲突：拍号不同（如 4/4 接 3/4）
        score -= 500
        metrics["meter_clash"] = f"{current_ts} vs {next_ts}"
        add_trace("Meter Compatibility", 0, -500, f"拍号冲突: {current_ts} 接 {next_ts}")
        
        # 精品模式下，直接在早期就拦截掉，不通过评分缓慢下降
        if is_boutique:
             return (-600000, track, {"boutique_rejected": "meter_clash"})
    else:
        add_trace("Meter Compatibility", 100, 0, f"拍号一致: {current_ts}")

    # P1 级律动同步：Swing DNA
    curr_swing = current_track.get('swing_dna', 0.0)
    next_swing = track.get('swing_dna', 0.0)
    swing_diff = abs(curr_swing - next_swing)
    
    swing_score_impact = 0
    if swing_diff < 0.15:
        # 律动高度一致（如都是 Straight 或 都是同档位 Swing）
        swing_score_impact = 20
        score += swing_score_impact
    elif swing_diff > 0.4:
        # 律动突变（如从 极度 Straight 突然跳到 极度 Swing）
        swing_score_impact = -40
        score += swing_score_impact
        
    add_trace("Groove Consistency", f"diff:{swing_diff:.2f}", swing_score_impact, f"Swing DNA 匹配度")

    # ========== 第1优先级：BPM（最高100分，强化版） ==========
    # 专业DJ规则：BPM应该逐渐上升或保持，不能下降
    if bpm_diff <= 2:
        score += 100 * bpm_weight # BPM几乎相同，最高分
    elif bpm_diff <= 4:
        if bpm_change > 0:  # BPM上升
            score += 90 * bpm_weight # 上升奖励
        elif bpm_change == 0:
            score += 85 * bpm_weight # 保持
        else:  # BPM下降
            score += 60 * bpm_weight # 下降惩罚
    elif bpm_diff <= 6:
        if bpm_change > 0:  # BPM上升
            score += 70 * bpm_weight # 上升奖励
        elif bpm_change == 0:
            score += 50 * bpm_weight # 保持
        else:  # BPM下降
            score += 20 * bpm_weight # 下降惩罚
    elif bpm_diff <= 8:
        if bpm_change > 0:  # BPM上升
            score += 50 * bpm_weight # 上升奖励
        elif bpm_change == 0:
            score += 30 * bpm_weight # 保持
        else:  # BPM下降
            score -= 20 * bpm_weight # 下降惩罚
    elif bpm_diff <= 10:
        if bpm_change > 0:  # BPM上升
            score += 30 * bpm_weight # 上升奖励
        elif bpm_change == 0:
            score += 10 * bpm_weight # 保持
        else:  # BPM下降
            score -= 60 * bpm_weight # 下降严重惩罚
    elif bpm_diff <= 12:
        if bpm_change > 0:  # BPM上升
            score += 10 * bpm_weight # 上升轻微奖励
        else:  # BPM下降或保持
            score -= 80 * bpm_weight # 下降严重惩罚
    elif bpm_diff <= 16:
        if bpm_change > 0:  # BPM上升
            score -= 20 * bpm_weight # 跨度大但上升，轻微惩罚
        else:  # BPM下降或保持
            score -= 100 * bpm_weight # 下降极严重惩罚
    elif bpm_diff <= 20:
        if bpm_change > 0:  # BPM上升
            score -= 60 * bpm_weight # 跨度大但上升，严重惩罚
        else:  # BPM下降或保持
            score -= 150 * bpm_weight # 下降极严重惩罚
    elif bpm_diff <= 30:
        score -= 200 * bpm_weight # 超大跨度极严重惩罚
    else:
        score -= 300 * bpm_weight # 超大跨度极严重惩罚，几乎拒绝
    
    add_trace("BPM Compatibility", bpm_diff, score, f"Diff: {bpm_diff:.1f}, Change: {bpm_change:.1f}")
    
    key_score = get_key_compatibility_flexible(
        current_track.get('key', ''),
        track.get('key', '')
    )
    metrics["key_score"] = key_score
    add_trace("Key Harmony", key_score, key_score * 0.4, f"Harmonic compatibility")
    
    # ========== 第2优先级：调性兼容性（修复版，降低权重确保BPM优先） ==========
    # 专业DJ规则：调性跳跃可以用效果器过渡，BPM匹配应该优先
    # 计算调性距离（用于判断是否需要严重惩罚）
    current_key = current_track.get('key', '')
    next_key = track.get('key', '')
    key_distance = None
    
    # 计算Camelot距离
    if current_key and next_key:
        try:
            # 提取Camelot编号
            curr_num = int(current_key[:-1]) if current_key[:-1].isdigit() else None
            next_num = int(next_key[:-1]) if next_key[:-1].isdigit() else None
            if curr_num and next_num:
                # 计算最短距离（考虑12的循环）
                dist1 = abs(next_num - curr_num)
                dist2 = 12 - dist1
                key_distance = min(dist1, dist2)
        except:
            pass
    
    # 根据歌曲类型动态调整调性权重
    current_style = current_track.get('style_hint', '').lower() if current_track.get('style_hint') else ''
    next_style = track.get('style_hint', '').lower() if track.get('style_hint') else ''
    current_genre = current_track.get('genre', '').lower() if current_track.get('genre') else ''
    next_genre = track.get('genre', '').lower() if track.get('genre') else ''
    
    # 判断是否是快速切换/Drop混音类型
    is_fast_switch = False
    if any(keyword in current_style or keyword in next_style for keyword in ['tech', 'hard', 'fast', 'dance']):
        is_fast_switch = True
    if any(keyword in current_genre or keyword in next_genre for keyword in ['tech house', 'hard trance', 'hardstyle']):
        is_fast_switch = True
    if current_track.get('energy', 50) > 70 or track.get('energy', 50) > 70:
        is_fast_switch = True
    
    # 调性权重：由 Profile 控制
    if ACTIVE_PROFILE:
        key_weight = ACTIVE_PROFILE.weights.get("key_match", 0.3)
    else:
        if is_fast_switch:
            key_weight = 0.2  # 快速切换类型，权重更低
        else:
            if key_score >= 100:
                key_weight = 0.3  # 完美匹配，最高权重（降低）
            elif key_score >= 95:
                key_weight = 0.25
            elif key_score >= 85:
                key_weight = 0.22
            else:
                key_weight = 0.2
    
    # 调性评分：基础评分
    score += key_score * key_weight
    
    # 调性距离惩罚：对于距离≥5的跳跃，进一步降低惩罚（允许但标记为"需技巧过渡"）
    if key_distance is not None:
        if key_distance >= 5:
            score -= 50  # 距离≥5，中等惩罚（进一步降低从-80到-50，允许但需要技巧）
            metrics["key_distance_penalty"] = key_distance
            metrics["needs_technique"] = True  # 标记需要技巧过渡
        elif key_distance >= 4:
            score -= 30  # 距离≥4，轻微惩罚（降低从-50到-30）
            metrics["key_distance_penalty"] = key_distance
        elif key_distance >= 3:
            score -= 15  # 距离≥3，轻微惩罚（降低从-25到-15）
            metrics["key_distance_penalty"] = key_distance
    
    # 【修复】调性兼容性额外惩罚 - 提高惩罚力度，改善调性过渡
    if key_score < 40:
        score -= 30  # 调性完全不兼容，严重惩罚（从-10提高到-30）
        metrics["key_incompatible"] = True
    elif key_score < 60:
        score -= 15  # 调性不兼容，中等惩罚（从-5提高到-15）
        metrics["key_incompatible"] = True
    
    # 优化：避免连续相同调性
    current_key = current_track.get('key', '')
    next_key = track.get('key', '')
    if current_key and next_key and current_key == next_key and current_key != "未知":
        if len(sorted_tracks) > 0:
            prev_key = sorted_tracks[-1].get('key', '') if len(sorted_tracks) > 0 else ''
            if prev_key == current_key:
                score -= 3
    
    # ========== 【V6.1】 声学与律动审计 (LUFS & Swing) ==========
    # 1. 响度一致性 (LUFS) - 确保增益平稳
    current_lufs = current_track.get('loudness_lufs')
    if current_lufs is None:
        current_lufs = current_track.get('lufs_db', -10.0) # 兼容旧键名
    
    next_lufs = track.get('loudness_lufs')
    if next_lufs is None:
        next_lufs = track.get('lufs_db', -10.0)
    
    if current_lufs is not None and next_lufs is not None:
         # 转换为float安全处理
         try:
             c_lufs = float(current_lufs)
             n_lufs = float(next_lufs)
             lufs_diff = abs(c_lufs - n_lufs)
             lufs_score = 0
             if lufs_diff > 6.0:
                 lufs_score = -80 # 极差，需要巨大的Gain调整
                 metrics["lufs_penalty"] = True
             elif lufs_diff > 4.5:
                 lufs_score = -40 * (lufs_diff / 4.5) # 超过4.5dB严重惩罚
                 metrics["lufs_penalty"] = True
             elif lufs_diff > 2.5:
                 lufs_score = -10 # 轻微惩罚
             
             score += lufs_score
             add_trace("Acoustics (LUFS)", n_lufs, lufs_score, f"Diff: {lufs_diff:.1f}dB ({c_lufs:.1f}->{n_lufs:.1f})")
             metrics["lufs_db"] = n_lufs
         except:
             pass

    # 2. 律动一致性 (Swing/Groove) - 避免直拍撞摇摆
    current_swing = current_track.get('swing_dna', 0.0)
    next_swing = track.get('swing_dna', 0.0)
    
    if current_swing is not None and next_swing is not None:
        try:
            c_swing = float(current_swing)
            n_swing = float(next_swing)
            swing_diff = abs(c_swing - n_swing)
            swing_score = 0
            
            # Swing系数通常在 0.0 (Straight) 到 0.5 (Heavy Swing) 之间
            if swing_diff > 0.35: # Straight vs Heavy Swing
                swing_score = -100 
                metrics["rhythm_clash"] = True
            elif swing_diff > 0.2:
                swing_score = -30
            elif swing_diff < 0.05:
                swing_score = 20 # 律动完美贴合，加分
            
            score += swing_score
            # 只在有显著特征时记录Trace
            if swing_diff > 0.1 or swing_score != 0:
                add_trace("Rhythm (Swing)", n_swing, swing_score, f"Groove Diff: {swing_diff:.2f}")
            metrics["swing_dna"] = n_swing
        except:
            pass
            
    # ========== 【V5优化 - 专业建议】能量阶段匹配评分（权重提升到20%） ==========
    # 基于目标能量范围计算匹配度，确保能量曲线符合阶段要求
    # 【专业建议】权重从12%提升到20%，使能量曲线更平滑
    energy = track.get('energy', 50)
    current_energy = current_track.get('energy', 50)
    
    # 计算目标能量范围的中心值
    if min_energy is not None and max_energy is not None:
        target_center = (min_energy + max_energy) / 2.0
        # 计算候选歌曲能量与目标中心的距离
        energy_target_diff = abs(energy - target_center)
        # 转换为评分（0-1，越小越好）
        # 使用40作为饱和参数（能量差40时评分为0）
        energy_phase_score = max(0.0, 1.0 - (energy_target_diff / 40.0))
        # 【专业建议】权重从12%提升到20%（建议权重：bpm 0.40 | key 0.25 | energy_phase 0.20 | style 0.10）
        energy_phase_weight = 0.20
        score += energy_phase_score * 100 * energy_phase_weight  # 转换为0-20分（从12分提升）
        metrics["energy_phase_score"] = energy_phase_score
        metrics["energy_phase_match"] = energy_target_diff <= 20  # 能量差≤20认为匹配
    else:
        metrics["energy_phase_score"] = 0.5  # 默认中等评分
        metrics["energy_phase_match"] = False
    
    # ========== 【V6.3修复】严格能量阶段匹配惩罚 ==========
    # 如果候选歌曲的能量低于阶段最低要求，大幅扣分
    if min_energy is not None and energy < min_energy:
        # 能量低于阶段最低要求
        energy_shortage = min_energy - energy
        if phase_name in ["Build-up", "Peak", "Sustain"]:
            # Build-up/Peak/Sustain阶段，严格惩罚低能量歌曲
            if energy_shortage >= 15:
                score -= 300  # 能量严重不足（≥15），极重度扣分（基本排除）
                metrics["energy_shortage_severe"] = energy_shortage
            elif energy_shortage >= 10:
                score -= 200  # 能量严重不足（≥10），重度扣分
                metrics["energy_shortage_severe"] = energy_shortage
            elif energy_shortage >= 5:
                score -= 100  # 能量不足（≥5），中度扣分
                metrics["energy_shortage_medium"] = energy_shortage
            else:
                score -= 50  # 能量轻微不足（<5），轻度扣分
                metrics["energy_shortage_light"] = energy_shortage
    
    # ========== 【V6.1新增】严格能量倒退惩罚 ==========
    # 计算能量变化（正数=上升，负数=下降）
    energy_drop = current_energy - energy
    
    # 在非Cool-down阶段，严格惩罚能量倒退
    if phase_name not in ['Cool-down', 'Outro', 'Reset']:
        if energy_drop > 50:
            # 能量暴跌50+，极重度扣分（基本排除）
            score -= 200
            metrics["energy_drop_severe"] = energy_drop
        elif energy_drop > 35:
            # 能量暴跌35+，重度扣分
            score -= 120
            metrics["energy_drop_severe"] = energy_drop
        elif energy_drop > 25:
            # 能量下降25+，中度扣分
            score -= 70
            metrics["energy_drop_medium"] = energy_drop
        elif energy_drop > 15:
            # 能量下降15+，轻度扣分
            score -= 35
            metrics["energy_drop_light"] = energy_drop
        elif energy_drop > 8:
            # 能量轻微下降，小扣分
            score -= 15
            metrics["energy_drop_minor"] = energy_drop
        elif energy_drop > 3:
            # 能量轻微下降（3-8），小扣分（新增）
            score -= 8
            metrics["energy_drop_minor"] = energy_drop
    else:
        # Cool-down阶段，能量下降是正常的，给予奖励
        if energy_drop > 10:
            score += 15  # 奖励能量下降
            metrics["energy_drop_cooldown_bonus"] = energy_drop
    
    # 第2优先级：能量（根据阶段动态调整权重，保留原有逻辑用于相邻歌曲能量过渡）
    energy_diff = abs(energy - current_energy)
    
    # 根据阶段动态调整能量权重
    # Build-up和Peak阶段更重视能量匹配（提升到40分）
    if phase_name in ["Build-up", "Peak"]:
        max_energy_score = 40  # 提升到40分
        energy_weights = {
            5: 40,    # 能量差≤5：40分
            10: 27,   # 能量差≤10：27分（40*0.67）
            15: 13,   # 能量差≤15：13分（40*0.33）
            20: 7,    # 能量差≤20：7分（40*0.17）
        }
    else:
        max_energy_score = 30  # 保持30分
        energy_weights = {
            5: 30,    # 能量差≤5：30分
            10: 20,   # 能量差≤10：20分
            15: 10,   # 能量差≤15：10分
            20: 5,    # 能量差≤20：5分
        }
    
    # 能量匹配度得分（保留原有逻辑，用于相邻歌曲能量过渡）
    if energy_diff <= 5:
        score += energy_weights[5]
    elif energy_diff <= 10:
        score += energy_weights[10]
    elif energy_diff <= 15:
        score += energy_weights[15]
    elif energy_diff <= 20:
        score += energy_weights[20]
    else:
        score -= 5

    # 【V5.3 P1】集成 PSSI Intensity (Rekordbox 官方段落强度)
    # 逻辑：如果 PSSI 探测到强度突增/突降，进行额外权重校验
    curr_intensity = current_track.get('pssi_intensity_outro')
    next_intensity = track.get('pssi_intensity_intro')
    if curr_intensity is not None and next_intensity is not None:
        intensity_diff = abs(curr_intensity - next_intensity)
        if intensity_diff <= 1:
            score += 15  # 官方强度平滑过渡，大额加分
            metrics["pssi_intensity_match"] = "excellent"
            add_trace("PSSI Intensity", intensity_diff, 15, "Excellent flow")
            add_trace("PSSI", intensity_diff, 15, "Excellent flow")
        elif intensity_diff <= 2:
            score += 7   # 较平滑
            metrics["pssi_intensity_match"] = "good"
            add_trace("PSSI", intensity_diff, 7, "Smooth flow")
        else:
            score -= 10  # 强度突变（如 1->5 或 5->1），扣分
            metrics["pssi_intensity_match"] = "jump"
            add_trace("PSSI", intensity_diff, -10, "Intensity jump penalty")

    # 【V6.0 Intelligence】音色与复杂度匹配 (Brightness & Busy Score)
    curr_brightness = current_track.get('brightness', 0.5)
    next_brightness = track.get('brightness', 0.5)
    brightness_diff = abs(curr_brightness - next_brightness)
    if brightness_diff <= 0.15:
        score += 8  # 音色明亮度非常接近
        metrics["timbre_match"] = "consistent"
        add_trace("Timbre/Brightness", brightness_diff, 8, "Close match")
    elif brightness_diff > 0.4:
        score -= 5  # 音色明暗反差过大（可能突兀）
        metrics["timbre_match"] = "contrast"

    # 【V6.0】3-Band Tonal Balance Proxy Matching
    curr_low = current_track.get('tonal_balance_low', 0.5)
    next_low = track.get('tonal_balance_low', 0.5)
    if abs(curr_low - next_low) <= 0.1:
        score += 5  # 低频能量特征一致（意味着类似的 Kick/Bass 质感）
        metrics["spectrum_match_low"] = "pass"
        add_trace("Spectral Balance (Low)", abs(curr_low - next_low), 5, "Bass consistency")

    curr_busy = current_track.get('busy_score', 0.5)
    next_busy = track.get('busy_score', 0.5)
    busy_diff = abs(curr_busy - next_busy)
    if busy_diff <= 0.2:
        score += 7  # 编曲复杂度/繁忙度对等
        metrics["complexity_match"] = "balanced"
    elif busy_diff > 0.5:
        score -= 5  # 从极简突然变极繁（或相反）
        metrics["complexity_match"] = "abrupt"

    # 【V6.0 Intelligence】语义标签联动 (Semantic Tagging)
    # 如果 B 轨标记了 "Vocal" 而 A 轨尾部人声较多，适当降权（避免对冲）
    if "VOCAL" in track.get('semantic_tags', []) and current_track.get('outro_vocal_ratio', 0) > 0.3:
        score -= 10
        metrics["semantic_conflict"] = "vocal_overlap"
    
    # 如果 B 轨标记了 "DROP" 且 A 轨是高能量结尾，加分
    if "DROP" in track.get('semantic_tags', []) and current_track.get('energy', 50) > 70:
        score += 10
        metrics["semantic_bonus"] = "energy_surge"
    
    # 能量阶段匹配（额外加分）
    if min_energy <= energy <= max_energy:
        score += 5
    elif energy < min_energy:
        if phase_name in ["Warm-up", "Cool-down"]:
            score += 3
        else:
            score += 1
    else:
        if phase_name in ["Peak", "Intense"]:
            score += 3
        elif phase_name == "Cool-down":
            score -= 5
        else:
            score += 1
    
    # 律动相似度（基于onset密度）- 降低权重，避免与风格标签重叠
    rhythm_similarity = compare_rhythm_similarity(current_track, track)
    if rhythm_similarity > 0.8:
        score += 10  # 节奏密度接近，加分（降低权重）
    elif rhythm_similarity < 0.4:
        score -= 5  # 节奏密度差异太大，扣分（降低权重）
    
    # ========== 【V6.1 Pro-Acoustics】增益平顺度 (Gain Normalization) ==========
    curr_lufs = current_track.get('lufs_db', -10.0)
    next_lufs = track.get('lufs_db', -10.0)
    lufs_diff = abs(curr_lufs - next_lufs)
    
    # 理想响度差异在 2dB 以内
    if lufs_diff <= 2.0:
        score += 10
        metrics["gain_match"] = "perfect"
        add_trace("Acoustics (LUFS)", lufs_diff, 10, "Loudness consistent")
    elif lufs_diff > 4.5:
        score -= 15  # 响度跳变过大，现场需要频繁动手调 Gain，扣分
        metrics["gain_match"] = "jump"
        add_trace("Acoustics (LUFS)", lufs_diff, -15, "Loudness jump penalty")
        
    # ========== 【V6.1 Pro-Acoustics】律动兼容性 (Groove Swing Alignment) ==========
    curr_swing = current_track.get('swing_offset', 0.0)
    next_swing = track.get('swing_offset', 0.0)
    swing_diff = abs(curr_swing - next_swing)
    
    # 识别 Straight (Swing < 0.1) vs Swingy (Swing > 0.3)
    if (curr_swing < 0.1 and next_swing > 0.3) or (curr_swing > 0.3 and next_swing < 0.1):
        score -= 12  # 律动冲突：硬直鼓点 vs 摇摆鼓点，混音时会产生“马蹄声”
        metrics["groove_conflict"] = "swing_mismatch"
        add_trace("Rhythm (Swing)", swing_diff, -12, "Swing vs Straight conflict")
    elif swing_diff <= 0.15:
        score += 8  # 律动感受一致
        metrics["groove_conflict"] = "synchronized"
        add_trace("Rhythm (Swing)", swing_diff, 8, "Groove synchronized")
    
    # ========== 【V6.2新增】基于Genre的律动兼容性检查 ==========
    # 使用Genre标签检测律动冲突（准确率90%+，远高于音频特征检测的33%）
    current_genre = current_track.get('genre', '').lower()
    next_genre = track.get('genre', '').lower()
    
    # 定义律动组（基于Genre关键词）
    def get_rhythm_group_from_genre(genre_str: str) -> str:
        """根据Genre字符串判断律动组"""
        genre_lower = genre_str.lower()
        
        # Four-on-Floor（标准4/4拍，每拍都有kick）
        four_on_floor_keywords = [
            'house', 'deep house', 'tech house', 'progressive house',
            'techno', 'trance', 'hard trance', 'electro house', 'edm',
            'minimal', 'acid house', 'chicago house', 'detroit techno'
        ]
        for keyword in four_on_floor_keywords:
            if keyword in genre_lower:
                return 'four_on_floor'
        
        # Breakbeat（碎拍，不规则kick-snare）
        breakbeat_keywords = [
            'breaks', 'breakbeat', 'uk garage', 'speed garage',
            'drum and bass', 'jungle', 'dnb', 'd&b', 'garage'
        ]
        for keyword in breakbeat_keywords:
            if keyword in genre_lower:
                return 'breakbeat'
        
        # Half-time（半拍，Trap特征）
        half_time_keywords = [
            'trap', 'dubstep', 'bass music', 'future bass',
            'riddim', 'brostep', 'chillstep'
        ]
        for keyword in half_time_keywords:
            if keyword in genre_lower:
                return 'half_time'
        
        # Latin（拉丁律动，Afro/Tribal）
        latin_keywords = [
            'afro', 'afro house', 'latin', 'tribal', 'baile funk',
            'reggaeton', 'dembow', 'moombahton'
        ]
        for keyword in latin_keywords:
            if keyword in genre_lower:
                return 'latin'
        
        # 默认：如果无法识别，假设是four_on_floor（最常见）
        return 'four_on_floor'
    
    current_rhythm_group = get_rhythm_group_from_genre(current_genre)
    next_rhythm_group = get_rhythm_group_from_genre(next_genre)
    
    # 【辅助】音频特征检测（检测Genre和音频特征不一致的情况）
    current_drum_pattern = current_track.get('drum_pattern', 'unknown')
    next_drum_pattern = track.get('drum_pattern', 'unknown')
    
    # 如果音频特征检测到Trap，但Genre不是Trap，标记为可能冲突
    if current_drum_pattern == 'trap' and current_rhythm_group != 'half_time':
        metrics["rhythm_warning"] = "audio_genre_mismatch_trap_current"
        score -= 20  # 轻微惩罚（音频和Genre不一致）
    if next_drum_pattern == 'trap' and next_rhythm_group != 'half_time':
        metrics["rhythm_warning"] = "audio_genre_mismatch_trap_next"
        score -= 20  # 轻微惩罚（音频和Genre不一致）
    
    # 律动冲突检测（基于Genre）
    if current_rhythm_group != next_rhythm_group:
        # Half-time vs Four-on-floor（最严重冲突）
        if (current_rhythm_group == 'half_time' and next_rhythm_group == 'four_on_floor') or \
           (current_rhythm_group == 'four_on_floor' and next_rhythm_group == 'half_time'):
            score -= 80  # 严重冲突，基本排除
            metrics["rhythm_conflict"] = f"{current_rhythm_group}_vs_{next_rhythm_group}"
            metrics["rhythm_conflict_severity"] = "severe"
        
        # Breakbeat vs Four-on-floor（中等冲突）
        elif (current_rhythm_group == 'breakbeat' and next_rhythm_group == 'four_on_floor') or \
             (current_rhythm_group == 'four_on_floor' and next_rhythm_group == 'breakbeat'):
            score -= 40  # 中等冲突
            metrics["rhythm_conflict"] = f"{current_rhythm_group}_vs_{next_rhythm_group}"
            metrics["rhythm_conflict_severity"] = "medium"
        
        # Latin vs Four-on-floor（轻微冲突，可以过渡）
        elif (current_rhythm_group == 'latin' and next_rhythm_group == 'four_on_floor') or \
             (current_rhythm_group == 'four_on_floor' and next_rhythm_group == 'latin'):
            score -= 15  # 轻微冲突，允许但不鼓励
            metrics["rhythm_transition"] = f"{current_rhythm_group}_vs_{next_rhythm_group}"
            metrics["rhythm_conflict_severity"] = "light"
        
        # 其他组合（未知冲突）
        else:
            score -= 25  # 中等惩罚
            metrics["rhythm_conflict"] = f"{current_rhythm_group}_vs_{next_rhythm_group}"
            metrics["rhythm_conflict_severity"] = "medium"
    else:
        # 同律动组，加分鼓励
        metrics["rhythm_match"] = current_rhythm_group
    
    # ========== 【V6.5新增】风格兼容性评分（基于预处理的风格标签）==========
    # 使用缓存中预处理的detected_genre进行风格兼容性检查
    # 权重：15%（新增维度，从其他维度调整而来）
    try:
        from genre_compatibility import are_genres_compatible
        
        curr_genre = current_track.get('detected_genre', '')
        next_genre = track.get('detected_genre', '')

        # 【防负优化】置信度门控：只有在风格标签足够可信时才启用“冲突扣分”
        # - 你现在的主流程会对缺失风格做 filename 兜底，但默认置信度较低（0.6）
        # - update_genre_cache 批量写入的标签可设置更高置信度（建议 0.85+）
        try:
            from split_config import get_config as _get_cfg
            _cfg = _get_cfg() or {}
            min_conf = float(((_cfg.get("genre_profile") or {}).get("min_confidence_for_sort", 0.85)))
        except Exception:
            min_conf = 0.85
        try:
            curr_conf = float(current_track.get("detected_genre_confidence", 0.0) or 0.0)
        except Exception:
            curr_conf = 0.0
        try:
            next_conf = float(track.get("detected_genre_confidence", 0.0) or 0.0)
        except Exception:
            next_conf = 0.0
        
        if curr_genre and next_genre and curr_conf >= min_conf and next_conf >= min_conf:
            is_compatible, compat_score, reason = are_genres_compatible(curr_genre, next_genre)
            
            if is_compatible:
                # 风格兼容，根据兼容度加分（0-27分，对应15%权重）
                genre_bonus = compat_score * 0.27
                score += genre_bonus
                metrics["genre_compatible"] = True
                metrics["genre_compat_score"] = compat_score
                metrics["genre_reason"] = reason
            else:
                # 风格冲突，扣分
                score -= 20
                metrics["genre_compatible"] = False
                metrics["genre_conflict"] = f"{curr_genre} vs {next_genre}"
                metrics["genre_reason"] = reason
        else:
            # 风格未知，中性处理
            metrics["genre_compatible"] = None
    except ImportError:
        # 如果genre_compatibility模块不可用，跳过
        pass
    
    # ========== 【V5优化 - 专业建议】风格段落匹配评分（权重降低到8%）==========
    # 检查风格段落匹配（如果歌曲有_style_block标记）
    # 【V6.5调整】权重从10%降低到8%（为风格兼容性让出2%）
    # 新权重分配：bpm 0.35 | key 0.20 | energy_phase 0.20 | genre_compat 0.15 | style_block 0.08
    current_style_block = current_track.get('_style_block')
    next_style_block = track.get('_style_block')
    
    if current_style_block and next_style_block:
        if current_style_block == next_style_block:
            # 同风格段落内，加分（权重8%，对应14分）
            score += 14  # 风格段落匹配，加分（从18降低到14，对应8%权重）
            metrics["style_block_match"] = True
        else:
            # 检查是否为相似风格（house和house_generic视为相似）
            similar_styles = {
                'house': ['house_generic'],
                'house_generic': ['house'],
                'afro': ['latin'],
                'latin': ['afro'],
            }
            is_similar = False
            if current_style_block in similar_styles:
                if next_style_block in similar_styles[current_style_block]:
                    is_similar = True
                    score += 4  # 相似风格，轻微加分（从5降低到4，对应8%权重）
            if not is_similar:
                # 不同风格段落，扣分（但允许，因为段落间需要过渡）
                score -= 5  # 风格段落不匹配，扣分（从-6降低到-5，对应8%权重）
            metrics["style_block_match"] = False
            metrics["style_transition"] = f"{current_style_block} → {next_style_block}"
    elif current_style_block or next_style_block:
        # 只有一个有风格标记，中性处理
        metrics["style_block_match"] = None
    else:
        # 都没有风格标记，使用原有的genre_tag逻辑
        current_genre_tag = current_track.get('genre_tag', '')
        next_genre_tag = track.get('genre_tag', '')
        if current_genre_tag and next_genre_tag:
            if current_genre_tag == next_genre_tag:
                score += 3  # 风格匹配，轻微加分（作为辅助参考）
                metrics["genre_match"] = True
            else:
                score -= 2  # 风格不匹配，轻微扣分（作为辅助参考）
                metrics["genre_match"] = False
    
    # 音色连续性（MFCC相似度）- 次级打分项（±10分）
    mfcc_similarity = compare_mfcc_similarity(current_track, track)
    if mfcc_similarity > 0.8:
        score += 10  # 音色相似，加分
        metrics["mfcc_similarity"] = mfcc_similarity
    elif mfcc_similarity < 0.4:
        score -= 10  # 音色差异大，扣分
        metrics["mfcc_similarity"] = mfcc_similarity
        metrics["timbre_penalty"] = True
    else:
        metrics["mfcc_similarity"] = mfcc_similarity
    
    # ========== 【V6.4新增】音频特征深度匹配 ==========
    # 这些维度来自缓存中的深度分析数据，用于更精确的混音兼容性评估
    
    # 1. 音色明亮度匹配 (brightness) - ±8分
    # 明亮度相近的歌曲混在一起更自然，避免突然变亮/变暗
    curr_brightness = current_track.get('brightness', 0.5)
    next_brightness = track.get('brightness', 0.5)
    if curr_brightness > 0 and next_brightness > 0:
        brightness_diff = abs(curr_brightness - next_brightness)
        if brightness_diff <= 0.1:
            score += 8  # 音色明亮度非常接近
            metrics["brightness_match"] = "excellent"
        elif brightness_diff <= 0.2:
            score += 4  # 音色明亮度较接近
            metrics["brightness_match"] = "good"
        elif brightness_diff > 0.4:
            score -= 6  # 音色明亮度差异大，可能听起来突兀
            metrics["brightness_match"] = "poor"
            metrics["brightness_diff"] = brightness_diff
    
    # 2. 低频匹配 (kick_drum_power + sub_bass_level) - ±10分
    # 低频是混音的关键，底鼓和低音相近的歌更容易混
    curr_kick = current_track.get('kick_drum_power', 0.5)
    next_kick = track.get('kick_drum_power', 0.5)
    curr_sub = current_track.get('sub_bass_level', 0.5)
    next_sub = track.get('sub_bass_level', 0.5)
    
    if curr_kick > 0 and next_kick > 0:
        kick_diff = abs(curr_kick - next_kick)
        sub_diff = abs(curr_sub - next_sub)
        bass_diff = (kick_diff + sub_diff) / 2
        
        if bass_diff <= 0.1:
            score += 10  # 低频特性非常匹配
            metrics["bass_match"] = "excellent"
        elif bass_diff <= 0.2:
            score += 5  # 低频特性较匹配
            metrics["bass_match"] = "good"
        elif bass_diff > 0.35:
            score -= 8  # 低频差异大，混音时可能打架
            metrics["bass_match"] = "poor"
            metrics["bass_diff"] = bass_diff
    
    # 3. 动态范围匹配 (dynamic_range_db) - ±6分
    # 动态范围相近的歌曲音量更容易平衡
    curr_dr = current_track.get('dynamic_range_db', 10)
    next_dr = track.get('dynamic_range_db', 10)
    
    if curr_dr > 0 and next_dr > 0:
        dr_diff = abs(curr_dr - next_dr)
        if dr_diff <= 3:
            score += 6  # 动态范围接近，音量容易平衡
            metrics["dynamic_match"] = "excellent"
        elif dr_diff <= 6:
            score += 2  # 动态范围较接近
            metrics["dynamic_match"] = "good"
        elif dr_diff > 10:
            score -= 5  # 动态范围差异大，需要手动调整增益
            metrics["dynamic_match"] = "poor"
            metrics["dynamic_diff"] = dr_diff
    
    # 4. 情感效价匹配 (valence + arousal) - ±8分
    # 情感相近的歌曲过渡更自然，避免突然从欢快变悲伤
    curr_valence = current_track.get('valence', 0.5)
    next_valence = track.get('valence', 0.5)
    curr_arousal = current_track.get('arousal', 0.5)
    next_arousal = track.get('arousal', 0.5)
    
    # 检查数据有效性（arousal全是1.0说明数据有问题，跳过）
    valence_valid = (curr_valence != 1.0 or next_valence != 1.0) and (curr_valence > 0 and next_valence > 0)
    arousal_valid = (curr_arousal != 1.0 or next_arousal != 1.0) and (curr_arousal > 0 and next_arousal > 0)
    
    if valence_valid and arousal_valid:
        valence_diff = abs(curr_valence - next_valence)
        arousal_diff = abs(curr_arousal - next_arousal)
        emotion_diff = (valence_diff + arousal_diff) / 2
        
        if emotion_diff <= 0.15:
            score += 8  # 情感非常一致
            metrics["emotion_match"] = "excellent"
        elif emotion_diff <= 0.25:
            score += 4  # 情感较一致
            metrics["emotion_match"] = "good"
        elif emotion_diff > 0.4:
            score -= 6  # 情感差异大，过渡可能不自然
            metrics["emotion_match"] = "poor"
            metrics["emotion_diff"] = emotion_diff
    
    # 5. 乐句长度匹配 (phrase_length) - ±6分
    # 相同乐句长度的歌更容易对齐混音（8拍、16拍、32拍）
    curr_phrase = current_track.get('phrase_length', 16)
    next_phrase = track.get('phrase_length', 16)
    
    if curr_phrase > 0 and next_phrase > 0:
        if curr_phrase == next_phrase:
            score += 6  # 乐句长度完全一致
            metrics["phrase_match"] = "exact"
        elif curr_phrase % next_phrase == 0 or next_phrase % curr_phrase == 0:
            score += 3  # 乐句长度是倍数关系（如8和16）
            metrics["phrase_match"] = "multiple"
        else:
            score -= 3  # 乐句长度不兼容
            metrics["phrase_match"] = "mismatch"
    
    # 6. 前奏/尾奏人声互补 (intro_vocal_ratio + outro_vocal_ratio) - ±8分
    # 理想过渡：A尾奏无人声 + B前奏无人声 = 完美过渡点
    curr_outro_vocal = current_track.get('outro_vocal_ratio', 0.5)
    next_intro_vocal = track.get('intro_vocal_ratio', 0.5)
    
    vocal_base_score = 8
    vocal_conflict_penalty = 5
    if ACTIVE_PROFILE:
        vocal_conflict_penalty = ACTIVE_PROFILE.weights.get("vocal_conflict_penalty", 5)

    if curr_outro_vocal is not None and next_intro_vocal is not None:
        # 理想情况：当前歌尾奏无人声(低)，下首歌前奏无人声(低)
        if curr_outro_vocal < 0.3 and next_intro_vocal < 0.3:
            score += vocal_base_score  # 完美过渡点：两边都没人声
            metrics["vocal_transition"] = "perfect"
        elif curr_outro_vocal < 0.3 or next_intro_vocal < 0.3:
            score += vocal_base_score / 2  # 较好过渡：至少一边没人声
            metrics["vocal_transition"] = "good"
        elif curr_outro_vocal > 0.7 and next_intro_vocal > 0.7:
            score -= vocal_conflict_penalty  # 人声冲突：惩罚值由 Profile 决定
            metrics["vocal_transition"] = "conflict"
    
    # 7. 编曲繁忙度匹配 (busy_score) - ±6分
    # 繁忙度相近的歌混起来不会打架
    curr_busy = current_track.get('busy_score', 0.5)
    next_busy = track.get('busy_score', 0.5)
    
    if curr_busy > 0 and next_busy > 0:
        busy_diff = abs(curr_busy - next_busy)
        if busy_diff <= 0.1:
            score += 6  # 繁忙度非常接近
            metrics["busy_match"] = "excellent"
        elif busy_diff <= 0.2:
            score += 3  # 繁忙度较接近
            metrics["busy_match"] = "good"
        elif busy_diff > 0.35:
            score -= 4  # 繁忙度差异大，混音可能打架
            metrics["busy_match"] = "poor"
    
    # 8. 频段平衡匹配 (tonal_balance_low/mid/high) - ±6分
    # 频段分布相近的歌EQ更容易调
    curr_low = current_track.get('tonal_balance_low', 0.5)
    curr_mid = current_track.get('tonal_balance_mid', 0.3)
    curr_high = current_track.get('tonal_balance_high', 0.1)
    next_low = track.get('tonal_balance_low', 0.5)
    next_mid = track.get('tonal_balance_mid', 0.3)
    next_high = track.get('tonal_balance_high', 0.1)
    
    if curr_low > 0 and next_low > 0:
        # 计算频段差异（加权：低频最重要）
        tonal_diff = abs(curr_low - next_low) * 0.5 + abs(curr_mid - next_mid) * 0.3 + abs(curr_high - next_high) * 0.2
        if tonal_diff <= 0.1:
            score += 6  # 频段分布非常接近
            metrics["tonal_match"] = "excellent"
        elif tonal_diff <= 0.2:
            score += 3  # 频段分布较接近
            metrics["tonal_match"] = "good"
        elif tonal_diff > 0.35:
            score -= 4  # 频段差异大，EQ需要大调整
            metrics["tonal_match"] = "poor"
    
    # 9. Hook强度匹配 (hook_strength) - ±4分
    # Hook强度相近的歌过渡更自然
    curr_hook = current_track.get('hook_strength', 0.5)
    next_hook = track.get('hook_strength', 0.5)
    
    if curr_hook > 0 and next_hook > 0:
        hook_diff = abs(curr_hook - next_hook)
        if hook_diff <= 0.15:
            score += 4  # Hook强度接近
            metrics["hook_match"] = "good"
        elif hook_diff > 0.4:
            score -= 3  # Hook强度差异大
            metrics["hook_match"] = "poor"
    
    phase_hint = track.get('phase_hint')
    if isinstance(phase_hint, str):
        phase_hint = phase_hint.strip().lower()
        if phase_hint == phase_name.lower():
            score += 3
    
    return (score, track, metrics)

def enhanced_harmonic_sort(tracks: List[Dict], target_count: int = 40, progress_logger=None, debug_reporter=None, is_boutique: bool = False, is_live: bool = False) -> Tuple[List[Dict], List[Dict], Dict]:
    """
    增强版调性和谐排序（灵活版 + 能量曲线管理 + 时长平衡 + 艺术家分布）
    注重调性兼容性，但允许一定灵活性
    
    性能优化版本：
    - 限制候选池大小（只计算BPM最接近的N首）
    - 使用堆维护候选（避免全量排序）
    - 早期剪枝（快速排除不合适候选）
    """
    if not tracks:
        return [], [], {}
    
    # ========== 【P0优化】过滤异常时长歌曲 ==========
    # 原因：诊断发现duration范围异常（1.77秒~1942秒）
    # 修改：过滤<30秒或>600秒的歌曲
    filtered_tracks = []
    abnormal_tracks = []
    for track in tracks:
        duration = track.get('duration', 0)
        if 30 <= duration <= 600:  # 30秒-10分钟
            filtered_tracks.append(track)
        else:
            abnormal_tracks.append(track)
            if progress_logger:
                title = track.get('title', 'Unknown')[:40]
                progress_logger.log(f"过滤异常时长: {title} ({duration:.1f}秒)", console=False)
    
    if abnormal_tracks and progress_logger:
        progress_logger.log(f"已过滤 {len(abnormal_tracks)} 首异常时长歌曲", console=True)
    
    # 使用过滤后的歌曲列表
    tracks = filtered_tracks
    
    if not tracks:
        return [], [], {}
    
    # 准备数据
    for track in tracks:
        track['_used'] = False
        track['transition_hint'] = None
        track['transition_warnings'] = track.get('transition_warnings') or []
        if 'assigned_phase' in track:
            track.pop('assigned_phase')
    
    sorted_tracks = []
    conflict_tracks: List[Dict] = []
    junk_drawer = []  # 【最强大脑】质量屏障：记录那些实在不知道怎么排的歌
    remaining_tracks = tracks.copy()
    
    # 选择起始点：使用全局中位能量/BPM，避免固定Warm-up曲目开场
    energies = [t.get('energy') for t in remaining_tracks if isinstance(t.get('energy'), (int, float))]
    bpms = [t.get('bpm') for t in remaining_tracks if isinstance(t.get('bpm'), (int, float)) and t.get('bpm')]
    target_energy = statistics.median(energies) if energies else 55
    target_bpm = statistics.median(bpms) if bpms else 122
    start_track = min(
        remaining_tracks,
        key=lambda t: (
            abs(t.get('energy', target_energy) - target_energy),
            abs((t.get('bpm') or target_bpm) - target_bpm)
        )
    )
    sorted_tracks.append(start_track)
    remaining_tracks.remove(start_track)
    start_track['_used'] = True
    start_bpm = start_track.get('bpm', 0)
    start_energy = start_track.get('energy', 50)
    start_key = start_track.get('key', '')  # 记录起始调性（用于尾曲选择）
    
    # 【优化1】强制基于实际能量值分配阶段（起始歌曲通常是Warm-up）
    if start_energy < 50:
        start_phase = "Warm-up"
    elif start_energy < 65:
        start_phase = "Build-up"
    elif start_energy < 80:
        start_phase = "Peak"
    elif start_energy < 90:
        start_phase = "Intense"
    else:
        start_phase = "Intense"
    
    # 起始歌曲通常是Warm-up（除非能量极高）
    if start_energy < 65:
        start_phase = "Warm-up"
    
    start_track['assigned_phase'] = start_phase
    
    # 单峰结构约束：阶段状态追踪
    current_phase_num = get_phase_number(start_phase)
    max_phase_reached = current_phase_num  # 追踪已到达的最高阶段
    in_cool_down = (start_phase == "Cool-down")  # 是否已进入Cool-down阶段
    
    current_track = start_track
    max_iterations = len(tracks) * 2
    iteration = 0
    
    # 性能优化：动态候选池大小（根据歌曲总数调整）
    if len(tracks) > 200:
        CANDIDATE_POOL_SIZE = 80  # 大歌单用更大的候选池
    elif len(tracks) > 100:
        CANDIDATE_POOL_SIZE = 60
    elif len(tracks) > 50:
        CANDIDATE_POOL_SIZE = 50
    else:
        CANDIDATE_POOL_SIZE = min(30, len(tracks) // 2)  # 小歌单用较小的候选池
    
    # 完全移除冲突阈值，确保所有歌曲都能排进去
    CONFLICT_SCORE_THRESHOLD = -999999  # 设置为极低值，永不触发
    SEVERE_SCORE_THRESHOLD = -999999
    
    # 修复：确保处理所有歌曲，循环条件改为检查是否有未使用的歌曲
    def has_unused_tracks():
        """检查是否还有未使用的歌曲"""
        return any(not t.get('_used') for t in remaining_tracks)
    
    # ========== FULL DEBUG: 初始化调试数据收集 ==========
    debug_rounds = []
    debug_candidate_scores = []
    debug_backtrack_logs = []
    debug_conflict_logs = []
    debug_candidate_pool_sizes = []
    debug_selection_score_details = []
    debug_fallback_logs = []
    
    # 【Boutique】精品模式：设置硬性长度限制
    actual_target = target_count if is_boutique else len(tracks)
    
    # 只要还有未使用的歌曲，就继续循环
    while has_unused_tracks() and iteration < max_iterations:
        iteration += 1
        
        # 【Boutique】精品模式强制退出逻辑
        if is_boutique and len(sorted_tracks) >= actual_target:
            if progress_logger:
                progress_logger.log(f"✨ [精品回馈] 已达到目标曲目数 ({actual_target})，停止生成。", console=True)
            break
        
        # ========== FULL DEBUG: 记录当前轮次信息 ==========
        round_debug = {
            'round': iteration,
            'current_track': {
                'title': current_track.get('title', 'Unknown'),
                'bpm': current_track.get('bpm', 0),
                'key': current_track.get('key', 'Unknown'),
                'energy': current_track.get('energy', 50),
                'phase': current_track.get('assigned_phase', 'Unknown'),
                'file_path': current_track.get('file_path', 'Unknown')
            },
            'remaining_count': len([t for t in remaining_tracks if not t.get('_used')]),
            'sorted_count': len(sorted_tracks),
            'candidates': []
        }
        
        # 获取当前阶段的能量目标（考虑当前BPM和能量值）
        current_bpm = current_track.get('bpm', 0)
        current_energy = current_track.get('energy', 50)
        min_energy, max_energy, phase_name = get_energy_phase_target(
            len(sorted_tracks), len(tracks), current_bpm, current_energy, sorted_tracks, current_track
        )
        
        # 更新当前阶段编号（基于实际分配的阶段）
        # 注意：这里使用current_track的assigned_phase，而不是基于位置计算的phase_name
        # 因为单峰结构约束要求基于实际阶段状态
        if current_track.get('assigned_phase'):
            current_phase_num = get_phase_number(current_track.get('assigned_phase'))
        
        # 修复：大幅放宽候选池筛选，确保所有歌曲都能参与排序
        # 移除BPM限制，所有未使用的歌曲都可以进入候选池
        bpm_candidates = []
        
        for track in remaining_tracks:
            if track.get('_used'):
                continue
            next_bpm = track.get('bpm', 0)
            bpm_diff = abs(current_bpm - next_bpm) if current_bpm > 0 and next_bpm > 0 else 0
            
            # 完全移除BPM限制，所有歌曲都可以进入候选池
            # 计算能量匹配度（第2优先级）
            energy = track.get('energy', 50)
            energy_diff = abs(energy - current_track.get('energy', 50))
            
            # 检查调性兼容性（第3优先级，使用5度圈和T字法）
            key_score = get_key_compatibility_flexible(
                current_track.get('key', ''),
                track.get('key', '')
            )
            
            # 【V5优化 - 阶段2】检查风格段落匹配（如果当前歌曲有风格标记）
            # 增强优先级：同风格段落歌曲优先（提升到第2优先级）
            style_match = 0
            current_style_block = current_track.get('_style_block')
            track_style_block = track.get('_style_block')
            if current_style_block and track_style_block:
                if current_style_block == track_style_block:
                    style_match = 1  # 同风格段落，优先
            
            # 存储：BPM差、风格匹配（提升优先级）、能量差、调性分、歌曲
            bpm_candidates.append((bpm_diff, -style_match, energy_diff, key_score, track))
        
        # 排序：第1优先级BPM差小，第2优先级风格匹配（提升），第3优先级能量差小，第4优先级调性分高
        bpm_candidates.sort(key=lambda x: (x[0], x[1], x[2], -x[3]))  # BPM差小 > 风格匹配 > 能量差小 > 调性分高
        
        # 修复：移除候选池大小限制，使用所有剩余歌曲（确保所有歌曲都能参与排序）
        # 候选池：使用所有剩余歌曲，不再限制数量，但排除已使用的歌曲
        candidate_tracks = [t for _, _, _, _, t in bpm_candidates if not t.get('_used')]
        
        # 【V5优化 - 阶段2】优先选择同风格段落歌曲（如果存在）
        # 如果当前歌曲有风格标记，优先从同风格段落中选择
        current_style_block = current_track.get('_style_block')
        if current_style_block and candidate_tracks:
            same_style_tracks = [t for t in candidate_tracks if t.get('_style_block') == current_style_block]
            if same_style_tracks:
                # 如果同风格段落有候选歌曲，优先使用它们（但保留其他歌曲作为备选）
                # 将同风格歌曲放在前面
                other_tracks = [t for t in candidate_tracks if t.get('_style_block') != current_style_block]
                candidate_tracks = same_style_tracks + other_tracks
        
        candidate_results = []
        
        # 计算每个候选的得分
        # 注意：LRU缓存已优化兼容性计算（重复生成Set时提升50-70%）
        for track in candidate_tracks:
            if track.get('_used'):
                continue
            
            next_bpm = track.get('bpm', 0)
            bpm_diff = abs(current_bpm - next_bpm)
            
            metrics = {
                "bpm_diff": bpm_diff,
                "key_score": None,
                "percussive_diff": None,
                "dyn_var_diff": None,
                "style_penalty": False,
                "rhythm_penalty": False,
                "phase_penalty": False,
                "missing_profile": False,
                "fallback": False,
                "bpm_confidence": None,
                "key_confidence": None,
                "groove_density_diff": None,
                "spectral_centroid_diff": None,
                "drum_pattern_mismatch": False,
                "boutique_penalty": 0
            }

            # ========== 【Boutique】精品模式多级评分机制 (代替硬性拦截) ==========
            boutique_penalty = 0
            if is_boutique:
                # 调性兼容度预计算
                k_score = get_key_compatibility_flexible(current_track.get('key', ''), track.get('key', ''))
                energy_diff = abs(track.get('energy', 50) - current_track.get('energy', 50))
                
                # Tier 1 (Gold): 极致平滑 (BPM diff <= 8, Key Score >= 90, Energy Jump <= 25)
                # Tier 2 (Silver): 专业标准 (BPM diff <= 12, Key Score >= 75) -> 扣 150 分
                # Tier 3 (Bronze): 超过专业标准 -> 扣 500 分
                
                if bpm_diff <= 8.0 and k_score >= 90 and energy_diff <= 25:
                    boutique_penalty = 0 # 完美匹配，不扣分
                elif bpm_diff <= 12.0 and k_score >= 75:
                    boutique_penalty = 150 # 略有瑕疵，但在专业可接受范围内
                else:
                    # 此时已经属于“较难接”的范畴，但在精品模式下作为最后的保底，不推荐使用
                    boutique_penalty = 500 # 严重扣分，只有在别无选择时才会排入
            
            score = -boutique_penalty
            if is_boutique and boutique_penalty > 0:
                metrics["boutique_penalty"] = boutique_penalty
            
            # 第1优先级：BPM（最高100分）
            # 【修复】DJ排法：BPM应该逐渐上升或保持，但允许有条件的下降（breakdown过渡）
            bpm_score = get_bpm_compatibility_flexible(current_bpm, next_bpm)
            bpm_change = next_bpm - current_bpm  # 正数=上升，负数=下降
            
            # 获取能量变化（用于判断是否是breakdown过渡）
            current_energy = current_track.get('energy', 50)
            next_energy = track.get('energy', 50)
            energy_diff = next_energy - current_energy  # 正数=能量上升，负数=能量下降
            
            # 判断是否是breakdown过渡（BPM下降且能量也下降）
            is_breakdown_transition = (bpm_change < 0 and energy_diff < -5)
            
            if bpm_diff <= 2:
                if bpm_change >= 0:
                    score += 100  # BPM上升或持平：最高100分
                else:
                    if is_breakdown_transition:
                        score += 90  # Breakdown过渡：允许，轻微奖励
                    else:
                        score += 80  # BPM轻微下降（≤2）：轻微惩罚
            elif bpm_diff <= 4:
                if bpm_change >= 0:
                    score += 80  # BPM上升：80分
                else:
                    if is_breakdown_transition:
                        score += 60  # Breakdown过渡：允许，中等奖励
                    else:
                        score += 50  # BPM下降：严重惩罚
            elif bpm_diff <= 6:
                if bpm_change >= 0:
                    score += 60  # BPM上升：60分
                else:
                    if is_breakdown_transition:
                        score += 30  # Breakdown过渡：允许，轻微奖励
                    else:
                        score += 20  # BPM下降：严重惩罚
            elif bpm_diff <= 8:
                if bpm_change >= 0:
                    score += 40  # BPM上升：40分
                else:
                    if is_breakdown_transition:
                        score += 10  # Breakdown过渡：允许，不扣分
                    else:
                        score -= 20  # BPM下降：严重惩罚
            elif bpm_diff <= 10:
                if bpm_change >= 0:
                    score += 20  # BPM上升：20分
                else:
                    if is_breakdown_transition:
                        score -= 20  # Breakdown过渡：允许，轻微惩罚
                    else:
                        score -= 60  # BPM下降：极严重惩罚
            elif bpm_diff <= 12:
                if bpm_change >= 0:
                    score += 5  # BPM上升：轻微加分
                else:
                    score -= 100  # BPM下降：极严重惩罚
            elif bpm_diff <= 16:
                if bpm_change >= 0:
                    score -= 20  # BPM上升但跨度大：轻微惩罚
                else:
                    score -= 150  # BPM下降且跨度大：极严重惩罚
            elif bpm_diff <= 20:
                if bpm_change >= 0:
                    score -= 60  # BPM上升但跨度大：严重惩罚
                else:
                    score -= 200  # BPM下降且跨度大：极严重惩罚
            elif bpm_diff <= 30:
                if bpm_change >= 0:
                    score -= 100  # BPM上升但跨度超大：严重惩罚
                else:
                    score -= 250  # BPM下降且跨度超大：极严重惩罚
            else:
                if bpm_change >= 0:
                    score -= 160  # BPM上升但跨度极大：极严重惩罚
                else:
                    score -= 300  # BPM下降且跨度极大：极严重惩罚
            
            key_score = get_key_compatibility_flexible(
                current_track.get('key', ''),
                track.get('key', '')
            )
            metrics["key_score"] = key_score
            
            # 根据歌曲类型动态调整调性权重
            # 对于快速切换/Drop混音类型的歌曲，调性权重降低
            current_style = current_track.get('style_hint', '').lower() if current_track.get('style_hint') else ''
            next_style = track.get('style_hint', '').lower() if track.get('style_hint') else ''
            current_genre = current_track.get('genre', '').lower() if current_track.get('genre') else ''
            next_genre = track.get('genre', '').lower() if track.get('genre') else ''
            
            # 判断是否是快速切换/Drop混音类型（调性不那么重要）
            is_fast_switch = False
            if any(keyword in current_style or keyword in next_style for keyword in ['tech', 'hard', 'fast', 'dance']):
                is_fast_switch = True
            if any(keyword in current_genre or keyword in next_genre for keyword in ['tech house', 'hard trance', 'hardstyle']):
                is_fast_switch = True
            # 高能量歌曲通常可以快速切换
            if current_track.get('energy', 50) > 70 or track.get('energy', 50) > 70:
                is_fast_switch = True
            
            # ========== 第2优先级：调性兼容性（修复版，降低权重确保BPM优先） ==========
            # 专业DJ规则：调性跳跃可以用效果器过渡，BPM匹配应该优先
            # 计算调性距离（用于判断是否需要严重惩罚）
            current_key = current_track.get('key', '')
            next_key = track.get('key', '')
            key_distance = None
            
            # 计算Camelot距离
            if current_key and next_key:
                try:
                    # 提取Camelot编号
                    curr_num = int(current_key[:-1]) if current_key[:-1].isdigit() else None
                    next_num = int(next_key[:-1]) if next_key[:-1].isdigit() else None
                    if curr_num and next_num:
                        # 计算最短距离（考虑12的循环）
                        dist1 = abs(next_num - curr_num)
                        dist2 = 12 - dist1
                        key_distance = min(dist1, dist2)
                except:
                    pass
            
            # 调性权重：降低到0.2-0.3（从0.3-0.4降低），确保BPM优先
            if is_fast_switch:
                key_weight = 0.2  # 快速切换类型，权重更低
            else:
                if key_score >= 100:
                    key_weight = 0.3  # 完美匹配，最高权重（降低）
                elif key_score >= 95:
                    key_weight = 0.25
                elif key_score >= 85:
                    key_weight = 0.22
                else:
                    key_weight = 0.2
            
            # 调性评分：基础评分
            score += key_score * key_weight
            
            # 调性距离惩罚：对于距离≥5的跳跃，进一步降低惩罚（允许但标记为"需技巧过渡"）
            if key_distance is not None:
                if key_distance >= 5:
                    score -= 50  # 距离≥5，中等惩罚（进一步降低从-80到-50，允许但需要技巧）
                    metrics["key_distance_penalty"] = key_distance
                    metrics["needs_technique"] = True  # 标记需要技巧过渡
                elif key_distance >= 4:
                    score -= 30  # 距离≥4，轻微惩罚（降低从-50到-30）
                    metrics["key_distance_penalty"] = key_distance
                elif key_distance >= 3:
                    score -= 15  # 距离≥3，轻微惩罚（降低从-25到-15）
                    metrics["key_distance_penalty"] = key_distance
            
            # 调性兼容性额外惩罚（进一步降低）
            if key_score < 40:
                score -= 10  # 调性完全不兼容，轻微惩罚（降低从-20到-10）
            elif key_score < 60:
                score -= 5  # 调性不兼容，轻微惩罚（降低从-10到-5）
            
            # 优化：避免连续相同调性（但不要过度惩罚，调性兼容性优先）
            current_key = current_track.get('key', '')
            next_key = track.get('key', '')
            if current_key and next_key and current_key == next_key and current_key != "未知":
                # 如果调性完全相同，稍微降低分数（但仍然是高分，因为兼容性好）
                # 检查前面是否也是相同调性
                if len(sorted_tracks) > 0:
                    prev_key = sorted_tracks[-1].get('key', '') if len(sorted_tracks) > 0 else ''
                    if prev_key == current_key:
                        # 连续三首相同调性，轻微降低分数（从8降到3）
                        score -= 3
                    else:
                        # 只是两首相同，不降低分数（调性兼容性优先）
                        pass
            
            # 第2优先级：能量（根据阶段动态调整权重）
            energy = track.get('energy', 50)
            current_energy = current_track.get('energy', 50)
            energy_diff = abs(energy - current_energy)
            
            # 根据阶段动态调整能量权重
            # Build-up和Peak阶段更重视能量匹配（提升到40分）
            if phase_name in ["Build-up", "Peak"]:
                max_energy_score = 40  # 提升到40分
                energy_weights = {
                    5: 40,    # 能量差≤5：40分
                    10: 27,   # 能量差≤10：27分（40*0.67）
                    15: 13,   # 能量差≤15：13分（40*0.33）
                    20: 7,    # 能量差≤20：7分（40*0.17）
                }
            else:
                max_energy_score = 30  # 保持30分
                energy_weights = {
                    5: 30,    # 能量差≤5：30分
                    10: 20,   # 能量差≤10：20分
                    15: 10,   # 能量差≤15：10分
                    20: 5,    # 能量差≤20：5分
                }
            
            # 能量匹配度得分（能量差越小，得分越高）
            if energy_diff <= 5:
                score += energy_weights[5]
            elif energy_diff <= 10:
                score += energy_weights[10]
            elif energy_diff <= 15:
                score += energy_weights[15]
            elif energy_diff <= 20:
                score += energy_weights[20]
            else:
                score -= 5  # 能量差太大，轻微惩罚
            
            # 单峰结构约束：检查阶段约束（在能量阶段匹配之前）
            # 获取候选歌曲的预期阶段
            candidate_phase = get_energy_phase_target(
                len(sorted_tracks) + 1, len(tracks), next_bpm, energy, sorted_tracks, track
            )[2]
            candidate_phase_num = get_phase_number(candidate_phase)
            
            # 检查阶段约束
            is_valid_phase, phase_penalty = check_phase_constraint(
                current_phase_num, candidate_phase_num, max_phase_reached, in_cool_down
            )
            
            # 如果违反阶段约束，大幅扣分（强化能量曲线约束）
            if not is_valid_phase:
                score += phase_penalty  # phase_penalty已经是负数
                metrics["phase_constraint_violation"] = True
            elif phase_penalty < 0:
                score += phase_penalty  # 轻微违反，扣分但允许
                metrics["phase_constraint_warning"] = True
            
            # 修复：允许小幅能量回落，只惩罚大幅回落
            # 如果能量回落后再提升（除了Cool-down），根据回落幅度扣分
            if sorted_tracks and len(sorted_tracks) > 0:
                recent_phases = [t.get('assigned_phase') for t in sorted_tracks[-5:] if t.get('assigned_phase')]
                recent_energies = [t.get('energy', 50) for t in sorted_tracks[-5:] if isinstance(t.get('energy'), (int, float))]
                
                if recent_phases and recent_energies:
                    last_phase = recent_phases[-1]
                    last_phase_num = get_phase_number(last_phase)
                    candidate_phase_num = get_phase_number(candidate_phase)
                    
                    # 计算能量回落幅度
                    max_energy_reached = max(recent_energies) if recent_energies else 50
                    energy_regression = max_energy_reached - energy if energy < max_energy_reached else 0
                    
                    # 如果能量回落后再提升（已到过Peak或更高，现在又回到更早阶段）
                    if last_phase_num >= 2 and candidate_phase_num < last_phase_num and candidate_phase != "Cool-down":
                        if energy_regression <= 5:
                            # 小幅能量回落（±5能量内），允许，轻微惩罚
                            score -= 20
                            metrics["energy_regression_penalty"] = "minor"
                        elif energy_regression <= 10:
                            # 中等能量回落（5-10能量），中等惩罚
                            score -= 50
                            metrics["energy_regression_penalty"] = "moderate"
                        else:
                            # 大幅能量回落（>10能量），严重惩罚
                            score -= 100
                            metrics["energy_regression_penalty"] = "severe"
            
            # 能量阶段匹配（额外加分）
            if min_energy <= energy <= max_energy:
                score += 5  # 能量阶段匹配，额外加分
            elif energy < min_energy:
                if phase_name in ["Warm-up", "Cool-down"]:
                    score += 3
                else:
                    score += 1
            else:
                if phase_name in ["Peak", "Intense"]:
                    score += 3
                elif phase_name == "Cool-down":
                    score -= 5  # Cool-down阶段能量过高，惩罚
                else:
                    score += 1
            
            # ========== 【P1优化】张力曲线匹配（配合能量阶段）==========
            # 检查两首歌的张力走向是否符合当前能量阶段
            curr_tension = current_track.get('tension_curve')
            next_tension = track.get('tension_curve')
            
            if curr_tension and next_tension and len(curr_tension) > 2 and len(next_tension) > 2:
                try:
                    # 计算张力趋势（上升/下降/平稳）
                    # 取最后30%的张力值来判断趋势
                    curr_tail = curr_tension[-int(len(curr_tension)*0.3):]
                    next_head = next_tension[:int(len(next_tension)*0.3)]
                    
                    # 计算趋势（线性回归斜率）
                    curr_trend = (curr_tail[-1] - curr_tail[0]) / len(curr_tail) if len(curr_tail) > 1 else 0
                    next_trend = (next_head[-1] - next_head[0]) / len(next_head) if len(next_head) > 1 else 0
                    
                    # 判断趋势方向
                    curr_direction = 'up' if curr_trend > 0.01 else ('down' if curr_trend < -0.01 else 'flat')
                    next_direction = 'up' if next_trend > 0.01 else ('down' if next_trend < -0.01 else 'flat')
                    
                    # 根据能量阶段评分（配合Set整体曲线）
                    if candidate_phase in ["Warm-up", "Build-up"]:
                        # 上升阶段：鼓励上升趋势
                        if curr_direction == 'up' and next_direction == 'up':
                            score += 10  # 情绪递进
                            metrics["tension_match"] = "rising_phase_rising_tension"
                        elif curr_direction == 'up' and next_direction == 'down':
                            score -= 15  # 情绪冲突
                            metrics["tension_conflict"] = "rising_phase_falling_tension"
                        elif curr_direction == 'flat' or next_direction == 'flat':
                            score += 3  # 平稳过渡
                            metrics["tension_match"] = "neutral"
                    
                    elif candidate_phase in ["Peak", "Intense"]:
                        # 高潮阶段：鼓励平稳或持续高能
                        if curr_direction == 'flat' and next_direction == 'flat':
                            score += 10  # 维持高能量
                            metrics["tension_match"] = "peak_phase_stable_tension"
                        elif curr_direction == 'up' and next_direction == 'up':
                            score += 5  # 继续推高
                            metrics["tension_match"] = "peak_phase_rising_tension"
                        elif curr_direction == 'down' and next_direction == 'down':
                            score -= 5  # 过早衰退
                            metrics["tension_warning"] = "peak_phase_falling_tension"
                        elif curr_direction == 'flat' or next_direction == 'flat':
                            score += 3
                            metrics["tension_match"] = "neutral"
                    
                    elif candidate_phase == "Cool-down":
                        # 收尾阶段：鼓励下降趋势
                        if curr_direction == 'down' and next_direction == 'down':
                            score += 10  # 平稳收尾
                            metrics["tension_match"] = "cooldown_phase_falling_tension"
                        elif curr_direction == 'up' and next_direction == 'down':
                            score += 5  # 自然过渡到收尾
                            metrics["tension_match"] = "cooldown_phase_natural_transition"
                        elif curr_direction == 'down' and next_direction == 'up':
                            score -= 10  # 违反收尾逻辑
                            metrics["tension_conflict"] = "cooldown_phase_rising_tension"
                        elif curr_direction == 'flat' or next_direction == 'flat':
                            score += 3
                            metrics["tension_match"] = "neutral"
                    
                    else:
                        # 其他阶段：方向一致即可
                        if curr_direction == next_direction:
                            score += 5
                            metrics["tension_match"] = "same_direction"
                        elif curr_direction == 'flat' or next_direction == 'flat':
                            score += 3
                            metrics["tension_match"] = "neutral"
                
                except Exception:
                    pass
            
            # 律动相似度（基于onset密度）
            rhythm_similarity = compare_rhythm_similarity(current_track, track)
            if rhythm_similarity > 0.8:
                score += 15  # 节奏密度接近，加分
                metrics["rhythm_similarity"] = rhythm_similarity
            elif rhythm_similarity < 0.4:
                score -= 10  # 节奏密度差异太大，扣分
                metrics["rhythm_similarity"] = rhythm_similarity
                metrics["rhythm_penalty"] = True
            else:
                metrics["rhythm_similarity"] = rhythm_similarity
            
            phase_hint = track.get('phase_hint')
            if isinstance(phase_hint, str):
                phase_hint = phase_hint.strip().lower()
                current_phase = phase_name.lower()
                if phase_hint == current_phase:
                    score += 15
                elif (phase_hint == 'warm-up' and current_phase in {'build-up', 'peak', 'intense'}) or (
                    phase_hint == 'cool-down' and current_phase in {'peak', 'intense'}):
                    score -= 30
                    metrics["phase_penalty"] = True
                elif phase_hint != current_phase:
                    score -= 12
                    metrics["phase_penalty"] = True
            
            energy_diff = energy - current_track.get('energy', 50)
            if abs(energy_diff) <= 5:
                score += 2
            elif -10 <= energy_diff <= 15:
                score += 1
            
            curr_profile = current_track.get('energy_profile', {})
            next_profile = track.get('energy_profile', {})
            if curr_profile and next_profile:
                curr_percussive = curr_profile.get('percussive_ratio', 0)
                next_percussive = next_profile.get('percussive_ratio', 0)
                percussive_diff = abs(curr_percussive - next_percussive)
                metrics["percussive_diff"] = percussive_diff
                
                if percussive_diff < 0.2:
                    score += 5
                elif percussive_diff > 0.5:
                    score -= 15
                else:
                    score += (1 - percussive_diff) * 5
                
                curr_dyn_var = curr_profile.get('dynamic_variance', 0)
                next_dyn_var = next_profile.get('dynamic_variance', 0)
                dyn_var_diff = abs(curr_dyn_var - next_dyn_var)
                metrics["dyn_var_diff"] = dyn_var_diff
                if dyn_var_diff < 0.1:
                    score += 3
                elif dyn_var_diff > 0.3:
                    score -= 8
            else:
                metrics["missing_profile"] = True
            
            curr_style = current_track.get('style_hint')
            next_style = track.get('style_hint')
            curr_rhythm = current_track.get('rhythm_hint') or current_track.get('time_signature')
            next_rhythm = track.get('rhythm_hint') or track.get('time_signature')
            
            if curr_style and next_style:
                if curr_style == next_style:
                    score += 5
                elif curr_style in ['ballad', 'slow'] and next_style in ['eurobeat', 'fast', 'dance']:
                    score -= 20
                    metrics["style_penalty"] = True
                elif curr_style in ['eurobeat', 'fast', 'dance'] and next_style in ['ballad', 'slow']:
                    score -= 15
                    metrics["style_penalty"] = True
                    if phase_name == "Cool-down":
                        score += 10
                else:
                    score -= 5
                    metrics["style_penalty"] = True
            
            # ========== 【P0优化】降低time_signature权重，避免误检影响 ==========
            # 原因：99.6%的歌曲都是4/4拍，功能失去区分度
            # 修改：降低奖励（8→3）和惩罚（-25→-10），因为可能误检
            if curr_rhythm and next_rhythm:
                if curr_rhythm == next_rhythm:
                    score += 3  # 降低奖励（从8→3）
                elif (curr_rhythm == '3/4' and next_rhythm == '4/4') or (curr_rhythm == '4/4' and next_rhythm == '3/4'):
                    score -= 10  # 降低惩罚（从-25→-10，因为可能误检）
                    metrics["rhythm_penalty"] = True
                else:
                    score -= 5  # 降低惩罚（从-8→-5）
                    metrics["rhythm_penalty"] = True

            # ========== 第3优先级：质量过滤（BPM/Key Confidence） ==========
            # 优化：使用置信度进行质量过滤，低置信度降低权重
            # BPM Confidence质量过滤（权重1-2%）
            curr_bpm_conf = current_track.get('bpm_confidence')
            next_bpm_conf = track.get('bpm_confidence')
            if curr_bpm_conf is not None and next_bpm_conf is not None:
                # 如果两首歌曲的BPM置信度都较低，降低BPM评分权重
                avg_bpm_conf = (curr_bpm_conf + next_bpm_conf) / 2.0
                if avg_bpm_conf < 0.5:
                    # 低置信度：降低BPM评分权重（最多-10分）
                    score -= int((0.5 - avg_bpm_conf) * 20)  # 0.5置信度时-0分，0.3置信度时-4分，0.0置信度时-10分
                    metrics["low_bpm_confidence"] = avg_bpm_conf
                elif avg_bpm_conf > 0.8:
                    # 高置信度：轻微奖励（最多+2分）
                    score += int((avg_bpm_conf - 0.8) * 10)  # 0.8置信度时+0分，1.0置信度时+2分
                    metrics["high_bpm_confidence"] = avg_bpm_conf
            
            # Key Confidence质量过滤（权重1-2%）
            curr_key_conf = current_track.get('key_confidence')
            next_key_conf = track.get('key_confidence')
            if curr_key_conf is not None and next_key_conf is not None:
                # 如果两首歌曲的Key置信度都较低，降低Key评分权重
                avg_key_conf = (curr_key_conf + next_key_conf) / 2.0
                if avg_key_conf < 0.5:
                    # 低置信度：降低Key评分权重（最多-8分）
                    score -= int((0.5 - avg_key_conf) * 16)  # 0.5置信度时-0分，0.3置信度时-3.2分，0.0置信度时-8分
                    metrics["low_key_confidence"] = avg_key_conf
                elif avg_key_conf > 0.8:
                    # 高置信度：轻微奖励（最多+2分）
                    score += int((avg_key_conf - 0.8) * 10)  # 0.8置信度时+0分，1.0置信度时+2分
                    metrics["high_key_confidence"] = avg_key_conf
            
            # ========== 第4优先级：BPM Confidence硬约束（必须实施）⭐ ==========
            # 优化：如果BPM置信度低（<0.6），标记为"不适合长混音"
            # 强制建议Echo Out（而不是长混音）
            if next_bpm_conf is not None and next_bpm_conf < 0.6:
                # BPM置信度低，标记为不适合长混音
                track['_low_bpm_confidence'] = True
                track['_suggest_echo_out'] = True  # 建议Echo Out
                # 不扣分，但标记为需要特殊处理
                metrics["low_bpm_confidence_hard"] = next_bpm_conf
            
            # ========== 第6优先级：Groove Density节奏匹配（新增） ==========
            # 优化：使用Groove Density进行节奏匹配，识别Tech House/Afrobeat等风格
            # Groove Density存储在energy_profile中
            # 注意：curr_profile和next_profile在后面定义，这里需要重新获取
            curr_profile_for_groove = current_track.get('energy_profile', {})
            next_profile_for_groove = track.get('energy_profile', {})
            curr_groove = curr_profile_for_groove.get('groove_density') if curr_profile_for_groove else None
            next_groove = next_profile_for_groove.get('groove_density') if next_profile_for_groove else None
            if curr_groove is not None and next_groove is not None:
                groove_diff = abs(curr_groove - next_groove)
                metrics["groove_density_diff"] = groove_diff
                
                if groove_diff < 0.15:
                    # Groove Density非常接近，奖励（权重1-2%）
                    score += 5  # 节奏紧凑度匹配，加分
                    metrics["groove_match"] = True
                elif groove_diff < 0.25:
                    # Groove Density接近，轻微奖励
                    score += 2
                    metrics["groove_match"] = True
                elif groove_diff > 0.5:
                    # Groove Density差异很大，轻微惩罚（但允许，因为可能是风格切换）
                    score -= 3
                    metrics["groove_mismatch"] = True
            
            # ========== 第5优先级：Spectral Centroid能量类型判断（新增，如果存在） ==========
            # 优化：使用Spectral Centroid判断能量类型（Deep/Bright），用于能量匹配
            # Spectral Centroid可能存储在energy_profile中，如果不存在则跳过
            # 注意：curr_profile和next_profile在后面定义，这里需要重新获取
            curr_profile_for_spectral = current_track.get('energy_profile', {})
            next_profile_for_spectral = track.get('energy_profile', {})
            curr_spectral = curr_profile_for_spectral.get('spectral_centroid_mean') if curr_profile_for_spectral else None
            next_spectral = next_profile_for_spectral.get('spectral_centroid_mean') if next_profile_for_spectral else None
            if curr_spectral is not None and next_spectral is not None:
                spectral_diff = abs(curr_spectral - next_spectral)
                metrics["spectral_centroid_diff"] = spectral_diff
                
                # Spectral Centroid差异越小，音色越相似（Deep vs Bright）
                # 归一化差异（假设Spectral Centroid范围在1000-5000 Hz）
                normalized_diff = spectral_diff / 4000.0  # 归一化到0-1
                
                if normalized_diff < 0.1:
                    # Spectral Centroid非常接近，奖励（权重1%）
                    score += 3  # 能量类型匹配（Deep/Bright），加分
                    metrics["spectral_match"] = True
                elif normalized_diff < 0.2:
                    # Spectral Centroid接近，轻微奖励
                    score += 1
                    metrics["spectral_match"] = True
                # 差异较大时不惩罚，因为可能是风格切换（Deep → Bright）

            # ========== 第8优先级：Beat对齐和Drop对齐（极低权重，仅参考） ==========
            # 重要调整：AI对流行歌曲的Drop和Beat Grid检测经常不准
            # 将权重从30-100分大幅降低到5-10分，并且只在BPM置信度极高时才启用
            # 不要让对齐问题影响BPM和调性的主排序逻辑
            # P0-2优化：返回包含beatgrid_fix_hints的结果
            beat_result = calculate_beat_alignment(current_track, track)
            if len(beat_result) >= 4:
                beat_offset_diff, beat_alignment_score, beatgrid_fix_hints, needs_manual_align = beat_result
            else:
                # 兼容旧版本（如果返回值只有2个）
                beat_offset_diff, beat_alignment_score = beat_result[:2]
                beatgrid_fix_hints = {}
                needs_manual_align = False
            drop_offset_diff, drop_alignment_score = calculate_drop_alignment(current_track, track)
            
            metrics["beat_offset_diff"] = beat_offset_diff
            metrics["drop_offset_diff"] = drop_offset_diff
            metrics["beat_alignment_score"] = beat_alignment_score
            metrics["drop_alignment_score"] = drop_alignment_score
            
            # 【优化2】优化强拍对齐检测：提高BPM置信度阈值，减少误报
            # 条件1：BPM差≤3（收紧从≤5到≤3，只对BPM非常接近的歌曲进行对齐评分）
            # 条件2：BPM置信度≥0.85（提高从≥0.7到≥0.85，只对高置信度BPM进行对齐评分）
            # 条件3：beat_offset必须存在（避免使用默认值0导致误报）
            avg_bpm_conf_for_alignment = (curr_bpm_conf + next_bpm_conf) / 2.0 if (curr_bpm_conf is not None and next_bpm_conf is not None) else 0.0
            is_bpm_conf_acceptable = avg_bpm_conf_for_alignment >= 0.85  # 提高阈值到0.85
            
            # 【修复】检查downbeat_offset是否真实存在（不是默认值0）
            curr_downbeat_offset = current_track.get('downbeat_offset', None)
            next_downbeat_offset = track.get('downbeat_offset', None)
            has_real_beat_offset = (curr_downbeat_offset is not None and curr_downbeat_offset != 0) or \
                                   (next_downbeat_offset is not None and next_downbeat_offset != 0)
            
            if bpm_diff <= 3 and is_bpm_conf_acceptable and has_real_beat_offset:
                # ========== 【修复3】降低 Drop/Beat 对齐权重（100分→10-20分） ==========
                # 因为AI检测存在误差，不能让它拥有一票否决权
                # 将权重从 100分 降低到 10-20分（乘以 0.15 系数）
                # Beat对齐评分（权重10-20分，仅作为参考）
                if beat_offset_diff <= 0.5:
                    score += 20  # 完美对齐，最高奖励20分（原100分→20分）
                elif beat_offset_diff <= 1.0:
                    score += 15  # 优秀对齐，15分（原90分→15分）
                elif beat_offset_diff <= 2.0:
                    score += 10  # 可接受对齐，10分（原70分→10分）
                elif beat_offset_diff <= 4.0:
                    score += 5   # 轻微奖励，5分（原40分→5分）
                elif beat_offset_diff <= 8.0:
                    score -= 5   # 严重错位，轻微惩罚-5分（不影响主排序）
                else:
                    score -= 10  # 极严重错位，轻微惩罚-10分（不影响主排序）
            elif bpm_diff > 3:
                # BPM差>3时，强拍对齐不可靠，不评分
                pass
            elif not is_bpm_conf_acceptable:
                # BPM置信度不够高：不评分（提供参考信息，让DJ手动调整）
                pass
            elif not has_real_beat_offset:
                # beat_offset不存在或为默认值：不评分（避免误报）
                pass
            
            # Drop对齐评分：只在BPM差≤2、BPM置信度极高且Drop时间已知时给予奖励
            # 如果Drop时间未知（DROP_UNKNOWN），不评分
            curr_drop = current_track.get('first_drop_time')
            next_drop = track.get('first_drop_time')
            has_drop_info = curr_drop is not None and next_drop is not None
            
            # 使用is_bpm_conf_acceptable代替未定义的is_bpm_conf_high
            is_bpm_conf_high = avg_bpm_conf_for_alignment >= 0.90  # 更高阈值用于Drop对齐
            if bpm_diff <= 2 and is_bpm_conf_high and has_drop_info:
                # ========== 【修复3】Drop对齐评分：降低权重（10-20分） ==========
                # 只有在BPM差≤2、BPM置信度极高且Drop时间已知时才给予奖励
                if drop_offset_diff <= 4.0:
                    score += 20  # 完美Drop对齐，最高奖励20分（原100分→20分）
                elif drop_offset_diff <= 8.0:
                    score += 15  # 优秀Drop对齐，15分（原80分→15分）
                elif drop_offset_diff <= 16.0:
                    score += 10  # 可接受Drop对齐，10分（原60分→10分）
                # 偏移>16.0拍：不评分（提供参考信息，不惩罚）
            # BPM差>2、BPM置信度不够高或Drop时间未知：不评分（提供参考信息，让DJ手动调整）

            # 【V6.3新增】混音兼容性综合评分
            try:
                from mix_compatibility_scorer import calculate_mix_compatibility_score
                mix_score, mix_metrics = calculate_mix_compatibility_score(
                    current_track, 
                    track
                )
                # 权重8%（混音兼容性作为综合参考）
                score += mix_score * 0.08
                metrics["mix_compatibility_score"] = mix_score
                metrics["mix_compatibility_metrics"] = mix_metrics
                
                # 记录关键警告
                if mix_metrics.get('drop_clash'):
                    metrics["mix_warning_drop_clash"] = True
                if mix_metrics.get('beat_offset_large'):
                    metrics["mix_warning_beat_offset"] = True
            except (ImportError, Exception):
                # 优雅降级：如果模块不存在或出错，不影响排序
                pass
            
            vocal_penalty, has_vocal_conflict = check_vocal_conflict(current_track, track)
            score += vocal_penalty
            metrics["vocal_conflict_penalty"] = vocal_penalty
            metrics["has_vocal_conflict"] = has_vocal_conflict
            
            # ========== 【V4.0 Ultra+ 专家级增强】审美与 Mashup 联动评分 ==========
            # 1. Aesthetic Curator: 审美匹配 (曲风/时代/情感) - 权重 15%
            aesthetic_score, aesthetic_details = AESTHETIC_CURATOR.calculate_aesthetic_match(current_track, track)
            score += aesthetic_score * 0.15
            metrics["aesthetic_score"] = aesthetic_score
            metrics["aesthetic_details"] = aesthetic_details
            
            # 2. Mashup Intelligence: 跨界桥接与 Stems 兼容 - 权重 15%
            mashup_score, mashup_details = MASHUP_INTELLIGENCE.calculate_mashup_score(current_track, track)
            score += mashup_score * 0.15
            metrics["mashup_score"] = mashup_score
            metrics["mashup_details"] = mashup_details
            
            # ========== 【V4.1 Neural Sync】深度神经同步评分 ==========
            # A. 乐句长度匹配 (Phrase Parity) - 理想: 32拍+32拍
            phrase_parity_bonus = 0
            curr_outro_bars = current_track.get('outro_bars', 8)
            next_intro_bars = track.get('intro_bars', 8)
            if curr_outro_bars == next_intro_bars:
                phrase_parity_bonus = 25  # 物理量化完美契合
                score += phrase_parity_bonus
                metrics["phrase_parity_bonus"] = phrase_parity_bonus
            
            # B. 人声/伴奏互补 (Proactive Stem Synergy)
            vocal_synergy_bonus = 0
            # 【V5.2 HOTFIX】确保 vocal_ratio 不为 None
            curr_v_ratio = current_track.get('outro_vocal_ratio') or 0.5
            next_v_ratio = track.get('intro_vocal_ratio') or 0.5
            # 如果一个是纯人声/重人声，另一个是纯伴奏/重伴奏
            if (curr_v_ratio > 0.7 and next_v_ratio < 0.3) or (curr_v_ratio < 0.3 and next_v_ratio > 0.7):
                vocal_synergy_bonus = 20
                score += vocal_synergy_bonus
                metrics["vocal_synergy_bonus"] = vocal_synergy_bonus
                metrics["mashup_sweet_spot"] = True
            
            # C. 爆发点对齐 (Drop Alignment)
            drop_align_bonus = 0
            next_drop = track.get('first_drop_time')
            if next_drop:
                # 检查 B 轨 Drop 是否能在大约 32-64 拍内通过 A 轨 Outro 引出
                # 这是一个简化的对齐评分
                drop_align_bonus = 5
                score += drop_align_bonus
                metrics["drop_align_bonus"] = drop_align_bonus
            
            # ========== 【P1优化】使用mixable_windows优化混音点 ==========
            # 尝试使用mixable_windows优化混音点选择
            optimized_mix_out, optimized_mix_in = optimize_mix_points_with_windows(current_track, track)
            
            # 如果优化成功，更新指标（用于后续持久化到音轨对象）
            if optimized_mix_out is not None and optimized_mix_in is not None:
                # 记录优化值，确保 TXT 报告与 XML 强同步
                metrics["mix_points_optimized"] = True
                metrics["optimized_mix_out"] = optimized_mix_out
                metrics["optimized_mix_in"] = optimized_mix_in
                # 局部变量用于后续计算
                curr_mix_out = optimized_mix_out
                next_mix_in = optimized_mix_in
            else:
                # 使用原始分析点
                curr_mix_out = current_track.get('mix_out_point')
                next_mix_in = track.get('mix_in_point')
            
            # 能量释放点优化 + 结构标签硬约束
            curr_duration = current_track.get('duration', 0)
            curr_structure = current_track.get('structure', {})
            next_structure = track.get('structure', {})
            
            # 混音点计算（仅用于显示，不影响排序）
            if curr_mix_out and next_mix_in and curr_duration > 0:
                # 修正混音点间隔计算：
                # curr_mix_out是当前歌曲的混出点（从开始计算的秒数）
                # next_mix_in是下一首歌曲的混入点（从开始计算的秒数）
                # 混音点间隔 = 下一首混入点 - (当前歌曲时长 - 当前混出点)
                mix_gap = next_mix_in - (curr_duration - curr_mix_out)
                metrics["mix_gap"] = mix_gap
                
                # 检查结构标签（仅用于标记警告，不影响排序）
                curr_mix_out_in_verse = False
                next_mix_in_in_verse = False
                
                if curr_structure:
                    verses = curr_structure.get('verse', [])
                    # 检查是否在Verse中间（仅标记，不扣分）
                    for verse in verses:
                        if verse[0] < curr_mix_out < verse[1]:
                            curr_mix_out_in_verse = True
                            break
                
                if next_structure:
                    verses = next_structure.get('verse', [])
                    # 检查是否在Verse中间（仅标记，不扣分）
                    for verse in verses:
                        if verse[0] < next_mix_in < verse[1]:
                            next_mix_in_in_verse = True
                            break
                
                # 标记警告（不影响排序）
                if curr_mix_out_in_verse or next_mix_in_in_verse:
                    metrics["structure_warning"] = True
            # ========== V3.0 Ultra+ 专家级补完：人声避让与物理审计 ==========
            # 1. 人声安全锁 (Vocal Guard): 强制扣减 40% 分数 (V3.0 红线)
            if metrics.get("has_vocal_conflict"):
                score *= 0.6 
                metrics["v3_vocal_shield_active"] = True
            
            # 2. 低音相位审计 (Bass Swap Detection)
            curr_low = current_track.get('energy_profile', {}).get('low_energy', 0)
            next_low = track.get('energy_profile', {}).get('low_energy', 0)
            if curr_low > 0.6 and next_low > 0.6:
                metrics["bass_swap_required"] = True
                metrics["bass_swap_reason"] = f"双轨低频对撞 (Low Energy: {curr_low:.1f}/{next_low:.1f})"
            
            # 3. 律动感知 (Swing Matching)
            # 确保 Swing 风格过渡平滑，避免 Straight 与 Heavy Swing 硬碰硬
            curr_swing = current_track.get('swing_ratio') or current_track.get('analysis', {}).get('swing_ratio', 0.0)
            next_swing = track.get('swing_ratio') or track.get('analysis', {}).get('swing_ratio', 0.0)
            if abs(float(curr_swing) - float(next_swing)) > 0.4:
                score -= 25
                metrics["swing_mismatch_penalty"] = True
            
            # 4. 音色解析 (Synthesis Consistency)
            # 保持音色合成类型的一致性 (Analog vs Digital)
            curr_synth = current_track.get('synthesis_type') or current_track.get('analysis', {}).get('synthesis_type')
            next_synth = track.get('synthesis_type') or track.get('analysis', {}).get('synthesis_type')
            if curr_synth and next_synth and curr_synth != next_synth:
                score -= 15
                metrics["synthesis_jump_penalty"] = True
            
            candidate_results.append({
                "track": track,
                "score": score,
                "metrics": metrics,
            })
            
            # ========== FULL DEBUG: 收集每个候选的完整评分信息 ==========
            if debug_reporter:
                candidate_debug = {
                    'track': {
                        'title': track.get('title', 'Unknown'),
                        'bpm': track.get('bpm', 0),
                        'key': track.get('key', 'Unknown'),
                        'energy': track.get('energy', 50),
                        'file_path': track.get('file_path', 'Unknown'),
                        'duration': track.get('duration', 0),
                        'first_drop_time': track.get('first_drop_time'),
                        'mix_in_point': track.get('mix_in_point'),
                        'beat_offset': track.get('beat_offset'),
                        'structure': track.get('structure', {}),
                        'energy_profile': track.get('energy_profile', {})
                    },
                    'total_score': score,
                    'scores': {
                        'bpm_score': metrics.get('bpm_diff', 0),
                        'bpm_change': (track.get('bpm', 0) - current_bpm) if current_bpm > 0 else 0,
                        'key_score': metrics.get('key_score', 0),
                        'energy_score': metrics.get('energy_diff', 0),
                        'energy_phase': phase_name,
                        'drop_alignment': metrics.get('drop_alignment', None),
                        'beat_alignment': metrics.get('beat_offset_diff', None),
                        'mix_gap': metrics.get('mix_gap', None),
                        'percussive_diff': metrics.get('percussive_diff', None),
                        'dyn_var_diff': metrics.get('dyn_var_diff', None),
                        'style_penalty': metrics.get('style_penalty', False),
                        'rhythm_penalty': metrics.get('rhythm_penalty', False),
                        'phase_penalty': metrics.get('phase_penalty', False),
                        'missing_profile': metrics.get('missing_profile', False)
                    },
                    'details': {
                        'current_track_bpm': current_bpm,
                        'current_track_key': current_track.get('key', 'Unknown'),
                        'current_track_energy': current_track.get('energy', 50),
                        'current_track_phase': current_track.get('assigned_phase', 'Unknown'),
                        'target_phase': phase_name,
                        'target_energy_range': (min_energy, max_energy),
                        'all_metrics': metrics.copy()
                    }
                }
                debug_candidate_scores.append(candidate_debug)
                round_debug['candidates'].append({
                    'title': track.get('title', 'Unknown')[:50],
                    'score': score,
                    'bpm': track.get('bpm', 0),
                    'key': track.get('key', 'Unknown'),
                    'energy': track.get('energy', 50)
                })
        
        candidate_results.sort(key=lambda item: item["score"], reverse=True)
        has_close_bpm_option = any(
            (item["metrics"].get("bpm_diff") is not None)
            and (item["metrics"]["bpm_diff"] <= 16)
            for item in candidate_results
        )
        
        if not candidate_results:
            # 修复：如果没有候选，直接使用remaining_tracks中的第一首，添加到sorted_tracks而不是conflict_tracks
            if remaining_tracks:
                # 找到第一个未使用的歌曲
                fallback_track = None
                for t in remaining_tracks:
                    if not t.get('_used'):
                        fallback_track = t
                        break
                
                if fallback_track:
                    # ========== FULL DEBUG: 记录Fallback ==========
                    if debug_reporter:
                        debug_fallback_logs.append({
                            'tier': 'Tier1',
                            'round': iteration,
                            'reason': '没有候选结果，使用fallback',
                            'selected_track': {
                                'title': fallback_track.get('title', 'Unknown'),
                                'bpm': fallback_track.get('bpm', 0),
                                'key': fallback_track.get('key', 'Unknown'),
                                'energy': fallback_track.get('energy', 50)
                            },
                            'details': {
                                'candidate_count': len(candidate_results),
                                'remaining_count': len([t for t in remaining_tracks if not t.get('_used')])
                            }
                        })
                    
                    fallback_track['_used'] = True
                    # 【优化1】强制基于实际能量值分配阶段
                    fallback_energy = fallback_track.get('energy', 50)
                    progress = len(sorted_tracks) / max(len(tracks), 1)
                    
                    # 【优化1】强制基于实际能量值分配阶段（更严格的阈值）
                    if fallback_energy < 45:  # 从50降低到45
                        phase_name = "Warm-up"
                    elif fallback_energy < 60:  # 从65降低到60
                        phase_name = "Build-up"
                    elif fallback_energy < 75:  # 从80降低到75
                        phase_name = "Peak"
                    elif fallback_energy < 85:  # 从90降低到85
                        phase_name = "Intense"
                    else:
                        phase_name = "Intense"
                    
                    # 最后10%强制Cool-down（除非能量极高）
                    if progress >= 0.9 and fallback_energy < 80:  # 从85降低到80
                        phase_name = "Cool-down"
                    
                    fallback_track['assigned_phase'] = phase_name
                    fallback_track['transition_warnings'] = fallback_track.get('transition_warnings') or []
                    sorted_tracks.append(fallback_track)
                    remaining_tracks.remove(fallback_track)
                    current_track = fallback_track
                    if progress_logger:
                        progress_logger.log(f"Fallback添加: {fallback_track.get('title', 'Unknown')[:40]}", console=True)
                    continue
            break
        
        # 尾曲选择优化：如果是尾曲阶段，给尾曲候选额外加分
        remaining_count_check = len(remaining_tracks) - sum(1 for t in remaining_tracks if t.get('_used'))
        is_closure_phase_check = (len(sorted_tracks) >= target_count - 2) or (remaining_count_check <= 2)
        
        if is_closure_phase_check:
            for item in candidate_results:
                track = item["track"]
                if track.get('_is_closure_candidate', False):
                    closure_bonus = track.get('_closure_score', 0)
                    if closure_bonus > 0:
                        # 将尾曲得分转换为额外加分（最高+50分）
                        bonus = min(50, closure_bonus * 0.5)
                        item["score"] += bonus
        
        # 重新排序（考虑尾曲加分）
        candidate_results.sort(key=lambda x: x["score"], reverse=True)
        
        # 【最强大脑】质量屏障 (Quality Guardrail) - 优化：由硬性过滤改为降级宽容
        QUALITY_FLOOR = 40  # 40分为及格线
        
        best_result = None
        # 首先寻找及格的候选
        for result in candidate_results:
            if not result["track"].get('_used'):
                if result["score"] >= QUALITY_FLOOR:
                    best_result = result
                    break
        
        # 如果没有及格的，但在精品模式下，我们优先寻找次优解，而不是直接终止（除非彻底无歌）
        if best_result is None and is_boutique:
            # 在精品模式下，如果找不到及格的，尝试寻找分数最高的一个
            for result in candidate_results:
                if not result["track"].get('_used'):
                    best_result = result
                    if progress_logger:
                        progress_logger.log(f"⚠️ [精品降级] 为了连贯性接受次优解: {best_result['track'].get('title', 'Unknown')[:30]} (分数: {best_result['score']:.1f})", console=False)
                    break
            
            # 如果真的没歌了才终止
            if best_result is None:
                if progress_logger:
                    progress_logger.log("⚠️ [精品回馈] 彻底无法找到任何可用候选，提前终止生成。", console=True)
                break

        # [V4.0 LIVE MODE] 如果没有及格的且是直播模式，将当前剩余曲目中匹配度最低的移入残差桶，寻找下一个
        if best_result is None and is_live and has_unused_tracks():
            # 这种情况通常是由于当前歌曲与剩余所有歌曲都不兼容
            # 在直播模式下，我们不能终止，需要将当前无法匹配的歌曲暂时挂起或强行排入
            # 这里采取策略：如果连保底都没有（即candidate_results为空），则将剩余曲目中最违和的一首扔进 junk_drawer
            if not candidate_results:
                misfit = next(t for t in remaining_tracks if not t.get('_used'))
                misfit['_used'] = True
                junk_drawer.append(misfit)
                remaining_tracks.remove(misfit)
                if progress_logger:
                    progress_logger.log(f"📦 [直播残差] 歌曲无法衔接，暂存至末尾: {misfit.get('title')[:30]}", console=True)
                continue # 继续寻找下一首能接上的
        
        # 如果没有及格的，但在非精品/非直播模式下，取分数最高的作为保底
        if best_result is None and candidate_results:
            # 找到最高分的未使用歌曲
            for result in candidate_results:
                if not result["track"].get('_used'):
                    best_result = result
                    if progress_logger:
                        progress_logger.log(f"[降级衔接] 质量不足但强制链入: {best_result['track'].get('title', 'Unknown')[:30]} (分数: {best_result['score']:.1f})", console=False)
                    break
        
        # 如果是因为剔除了 misfit 而导致的 best_result 为 None，继续寻找
        if best_result is None and has_unused_tracks():
            continue
            
        # 如果所有候选都已被使用或被踢入 Junk Drawer，跳过这一轮
        if best_result is None:
            if progress_logger and not has_unused_tracks():
                progress_logger.log(f"排序完成或无可用歌选", console=False)
            break 
        # 移除分数过滤，接受任何候选（确保所有歌曲都能排进去）
        # if best_result["score"] < 50 and len(candidate_results) > 1:
        #     filtered = [item for item in candidate_results if item["score"] >= 40]
        #     if filtered:
        #         best_result = filtered[0]
        
        # 即使没有接近的BPM选项，如果BPM跨度超过30，也不应该强制接受
        if not has_close_bpm_option:
            best_bpm_diff = best_result["metrics"].get("bpm_diff")
            if best_bpm_diff is None or best_bpm_diff <= 30:
                best_result["metrics"]["force_accept"] = True
        
        best_track = best_result["track"]
        best_score = best_result["score"]
        # 使用 best_result 中对应的 metrics，避免 iteration 变量残留
        metrics = best_result["metrics"].copy()
        
        # 如果选中的是尾曲候选，标记为尾曲
        if best_track.get('_is_closure_candidate', False):
            best_track['_is_closure'] = True
            best_track.pop('_is_closure_candidate', None)
            best_track.pop('_closure_score', None)
        
        reasons = []
        bpm_diff = metrics.get("bpm_diff")
        if bpm_diff is not None and bpm_diff > 12:
            reasons.append(f"BPM跨度 {bpm_diff:.1f}")
        key_score = metrics.get("key_score")
        if key_score is not None and key_score < 45:
            reasons.append(f"调性兼容度低({key_score:.0f})")
        percussive_diff = metrics.get("percussive_diff")
        if percussive_diff is not None and percussive_diff > 0.45:
            reasons.append("快慢歌差异大")
        dyn_var_diff = metrics.get("dyn_var_diff")
        if dyn_var_diff is not None and dyn_var_diff > 0.35:
            reasons.append("动态变化差异大")
        if metrics.get("style_penalty"):
            reasons.append("风格不匹配")
        if metrics.get("rhythm_penalty"):
            reasons.append("节奏型不匹配")
        if metrics.get("phase_penalty"):
            reasons.append("能量阶段与手动标注冲突")
        if metrics.get("structure_warning"):
            reasons.append("混音点在Verse中间（不推荐）")
        # 移除冲突检测，不再因为分数低而标记为冲突
        # if best_score < CONFLICT_SCORE_THRESHOLD:
        #     reasons.append(f"综合得分偏低({best_score:.1f})")
        
        if len(sorted_tracks) % 10 == 0:
            remaining = len(remaining_tracks) - 1
            print(f"  排序进度: {len(sorted_tracks)}/{target_count} ({len(sorted_tracks)*100//target_count}%) | 剩余: {remaining}首 | 候选池: {len(candidate_tracks)}首")
        
        # 局部回溯机制：检查是否有更好的调性连接
        # 限制回溯深度为2，避免性能问题
        if len(sorted_tracks) >= 2 and key_score_val is not None and key_score_val < 85:
            # 如果当前选择的调性兼容性不够好（<85），尝试回溯
            backtrack_depth = min(2, len(sorted_tracks))
            best_backtrack_score = best_score
            best_backtrack_track = best_track
            best_backtrack_metrics = metrics
            
            for backtrack_idx in range(1, backtrack_depth + 1):
                if backtrack_idx >= len(sorted_tracks):
                    break
                
                # 获取回溯位置的歌曲
                backtrack_track = sorted_tracks[-backtrack_idx]
                backtrack_bpm = backtrack_track.get('bpm', 0)
                
                # 在当前候选池中寻找与回溯位置调性兼容性更好的歌曲
                for candidate in candidate_tracks:
                    if candidate.get('_used') or candidate == best_track:
                        continue
                    
                    candidate_bpm = candidate.get('bpm', 0)
                    candidate_bpm_diff = abs(backtrack_bpm - candidate_bpm)
                    
                    # 修复：改为软降权，不再硬过滤
                    # 如果BPM差太大，降权但不排除
                    if candidate_bpm_diff > 8:
                        # 降权：BPM差>8时，调性提升需要更大才能被选中
                        # 这里不continue，而是增加调性提升的阈值
                        pass  # 已经在下面的条件中处理了（candidate_key_score >= key_score_val + 15）
                    
                    candidate_key_score = get_key_compatibility_flexible(
                        backtrack_track.get('key', ''),
                        candidate.get('key', '')
                    )
                    
                    # 修复：改为软降权，不再硬过滤BPM差
                    # 如果调性兼容性更好（提升>=15分），考虑回溯
                    # BPM差>6时降权，但不排除
                    key_improvement = candidate_key_score - key_score_val
                    bpm_penalty = 0
                    if candidate_bpm_diff > 6:
                        bpm_penalty = (candidate_bpm_diff - 6) * 2  # BPM差每超过6，降权2分
                    
                    # 如果调性提升足够大（考虑BPM降权后），考虑回溯
                    if key_improvement >= 15 - bpm_penalty:
                        # 计算回溯后的总得分
                        backtrack_score = best_score
                        # 调性提升带来的加分
                        key_improvement = (candidate_key_score - key_score_val) * 0.5
                        backtrack_score += key_improvement
                        # BPM差稍大的惩罚
                        if candidate_bpm_diff > bpm_diff:
                            backtrack_score -= (candidate_bpm_diff - bpm_diff) * 2
                        
                        # 如果回溯后得分更好，记录
                        if backtrack_score > best_backtrack_score + 5:  # 需要明显提升才回溯
                            best_backtrack_score = backtrack_score
                            best_backtrack_track = candidate
                            # 尝试从 candidate_results 中找到该候选的 metrics
                            candidate_metrics = None
                            for res in candidate_results:
                                if res["track"] == candidate:
                                    candidate_metrics = res["metrics"].copy()
                                    break
                            
                            if candidate_metrics:
                                best_backtrack_metrics = candidate_metrics
                                best_backtrack_metrics.update({
                                    "backtracked": True,
                                    "backtrack_depth": backtrack_idx
                                })
                            else:
                                best_backtrack_metrics = {
                                    "bpm_diff": candidate_bpm_diff,
                                    "key_score": candidate_key_score,
                                    "backtracked": True,
                                    "backtrack_depth": backtrack_idx,
                                    "audit_trace": []
                                }
                            break  # 找到更好的就停止回溯
            
            # 如果回溯找到了更好的选择，使用回溯结果
            if best_backtrack_track != best_track and best_backtrack_metrics.get("backtracked"):
                # ========== FULL DEBUG: 记录回溯信息 ==========
                if debug_reporter:
                    backtrack_debug = {
                        'round': iteration,
                        'reason': f'调性兼容性不足 (key_score={key_score_val:.0f} < 85)',
                        'depth': best_backtrack_metrics.get("backtrack_depth", 0),
                        'original_track': {
                            'title': best_track.get('title', 'Unknown'),
                            'key': best_track.get('key', 'Unknown'),
                            'key_score': key_score_val
                        },
                        'backtrack_track': {
                            'title': backtrack_track.get('title', 'Unknown'),
                            'key': backtrack_track.get('key', 'Unknown')
                        },
                        'selected_track': {
                            'title': best_backtrack_track.get('title', 'Unknown'),
                            'key': best_backtrack_track.get('key', 'Unknown'),
                            'key_score': best_backtrack_metrics.get('key_score', 0)
                        },
                        'key_improvement': best_backtrack_metrics.get('key_score', 0) - key_score_val,
                        'process': [
                            f"回溯到位置 -{best_backtrack_metrics.get('backtrack_depth', 0)}",
                            f"原选择: {best_track.get('title', 'Unknown')[:40]} (key_score={key_score_val:.0f})",
                            f"新选择: {best_backtrack_track.get('title', 'Unknown')[:40]} (key_score={best_backtrack_metrics.get('key_score', 0):.0f})",
                            f"调性分提升: {best_backtrack_metrics.get('key_score', 0) - key_score_val:.0f}"
                        ]
                    }
                    debug_backtrack_logs.append(backtrack_debug)
                
                # 将回溯的歌曲从sorted_tracks中移除（如果需要）
                if best_backtrack_metrics.get("backtrack_depth", 0) > 0:
                    # 不实际移除，只是记录回溯信息
                    pass
                best_track = best_backtrack_track
                best_score = best_backtrack_score
                metrics = best_backtrack_metrics
                if progress_logger:
                    progress_logger.log(f"局部回溯：选择调性兼容性更好的歌曲（调性分提升 {best_backtrack_metrics.get('key_score', 0) - key_score_val:.0f}分）", console=False)
        
        # 修复：防止重复添加同一首歌曲
        if best_track.get('_used'):
            if progress_logger:
                progress_logger.log(f"警告：尝试添加已使用的歌曲 {best_track.get('title', 'Unknown')[:40]}，跳过", console=True)
            # 跳过已使用的歌曲，继续下一轮
            continue
        
        if best_track in remaining_tracks:
            remaining_tracks.remove(best_track)
        best_track['_used'] = True

        force_accept = bool(metrics.get("force_accept"))
        bpm_diff = metrics.get("bpm_diff")
        key_score_val = metrics.get("key_score")

        major_penalties = 0
        # BPM跨度超过30直接标记为严重冲突
        if bpm_diff is not None and bpm_diff > 30:
            major_penalties += 3  # 严重冲突，强制移到冲突列表
        elif bpm_diff is not None and bpm_diff > 20:
            major_penalties += 1
        if key_score_val is not None and key_score_val < 40:
            major_penalties += 1
        if metrics.get("rhythm_penalty"):
            major_penalties += 1
        if metrics.get("style_penalty"):
            major_penalties += 1
        if metrics.get("phase_penalty"):
            major_penalties += 1

        # 修改：所有歌曲都参与排序，只标记冲突信息，不拒绝
        is_conflict = False
        
        # 完全移除冲突检测，所有歌曲都正常排序（不标记为冲突）
        is_conflict = False
        # 只记录警告信息，不标记为冲突
        if bpm_diff is not None and bpm_diff > 30:
            if "BPM超大跨度" not in reasons:
                reasons.append(f"BPM超大跨度 {bpm_diff:.1f}（无法直接混音）")
        
        # ========== FULL DEBUG: 记录冲突信息（如果有） ==========
        if debug_reporter and (major_penalties >= 3 or bpm_diff is not None and bpm_diff > 30 or key_score_val is not None and key_score_val < 40):
            conflict_debug = {
                'round': iteration,
                'reason': ' | '.join(reasons) if reasons else '综合评分低',
                'tracks': [{
                    'title': best_track.get('title', 'Unknown'),
                    'file_path': best_track.get('file_path', 'Unknown'),
                    'bpm': best_track.get('bpm', 0),
                    'key': best_track.get('key', 'Unknown'),
                    'energy': best_track.get('energy', 50),
                    'conflict_reason': ' | '.join(reasons) if reasons else 'Unknown',
                    'score': best_score,
                    'major_penalties': major_penalties
                }]
            }
            debug_conflict_logs.append(conflict_debug)
        # elif best_score < SEVERE_SCORE_THRESHOLD:
        #     is_conflict = True
        # elif best_score < CONFLICT_SCORE_THRESHOLD and major_penalties >= 3:
        #     is_conflict = True
        
        # 标记冲突，但仍然排上
        if is_conflict:
            if not reasons:
                reasons.append("综合得分偏低或兼容性不足")
            best_track['_is_conflict'] = True  # 统一使用_is_conflict标记
            best_track['_conflict_reasons'] = reasons
        else:
            best_track['_is_conflict'] = False  # 统一使用_is_conflict标记

        if reasons:
            warnings = best_track.get('transition_warnings') or []
            warnings.extend([r for r in reasons if r not in warnings])
            best_track['transition_warnings'] = warnings

        mix_gap_val = metrics.get("mix_gap")
        if mix_gap_val is not None and not (-8.0 <= mix_gap_val <= 16.0):
            warnings = best_track.get('transition_warnings') or []
            gap_msg = f"混音点间隔 {mix_gap_val:.1f}s"
            if gap_msg not in warnings:
                warnings.append(gap_msg)
            best_track['transition_warnings'] = warnings

        # 【优化1】更新阶段状态（单峰结构约束）- 强制基于实际能量值分配阶段
        best_energy = best_track.get('energy', 50)
        progress = len(sorted_tracks) / max(len(tracks), 1)
        
        # 【优化1】强制基于实际能量值分配阶段（更严格的阈值）
        if best_energy < 45:  # 从50降低到45
            best_phase = "Warm-up"
        elif best_energy < 60:  # 从65降低到60
            best_phase = "Build-up"
        elif best_energy < 75:  # 从80降低到75
            best_phase = "Peak"
        elif best_energy < 85:  # 从90降低到85
            best_phase = "Intense"
        else:
            best_phase = "Intense"
        
        # 最后10%强制Cool-down（除非能量极高）
        if progress >= 0.9 and best_energy < 80:  # 从85降低到80
            best_phase = "Cool-down"
        
        best_phase_num = get_phase_number(best_phase)
        
        # 更新当前阶段和最高阶段
        current_phase_num = best_phase_num
        if best_phase_num > max_phase_reached:
            max_phase_reached = best_phase_num
        
        # 如果进入Cool-down阶段，标记为Cool-down状态
        if best_phase == "Cool-down":
            in_cool_down = True
        
        best_track['assigned_phase'] = best_phase
        
        # ========== 【进化战略】注入雷达报告指标 ==========
        best_track['_transition_score'] = best_score
        best_track['_transition_metrics'] = metrics.copy()
        best_track['audit_trace'] = metrics.get('audit_trace', [])  # 【V6.0 Audit】审计追踪持久化
        
        # 【最强大脑修复】将排序时优化的混音点持久化到音轨对象中
        # 这确保了 TXT 报告与 XML Hotcue 能够对齐“专家推荐”位
        if metrics.get("mix_points_optimized"):
            opt_out = metrics.get("optimized_mix_out")
            opt_in = metrics.get("optimized_mix_in")
            # 找到前一曲并更新其出歌点
            if len(sorted_tracks) > 0 and opt_out is not None:
                sorted_tracks[-1]['mix_out_point'] = opt_out
            # 更新本曲进歌点
            if opt_in is not None:
                best_track['mix_in_point'] = opt_in

        # 修复：防止重复添加（双重检查）
        if best_track not in sorted_tracks:
            sorted_tracks.append(best_track)
        else:
            if progress_logger:
                progress_logger.log(f"严重错误：尝试重复添加歌曲 {best_track.get('title', 'Unknown')[:40]}，已跳过", console=True)
            continue  # 跳过重复添加
        current_track = best_track
        
        # ========== FULL DEBUG: 记录本轮最终选择 ==========
        if debug_reporter:
            round_debug['selected_track'] = {
                'title': best_track.get('title', 'Unknown'),
                'bpm': best_track.get('bpm', 0),
                'key': best_track.get('key', 'Unknown'),
                'energy': best_track.get('energy', 50),
                'phase': best_track.get('assigned_phase', 'Unknown'),
                'score': best_score,
                'reasons': reasons.copy() if reasons else []
            }
            round_debug['candidate_count'] = len(candidate_results)
            debug_rounds.append(round_debug)
            
            # 记录候选池大小
            debug_candidate_pool_sizes.append({
                'round': iteration,
                'pool_size': len(candidate_tracks),
                'remaining': len([t for t in remaining_tracks if not t.get('_used')]),
                'selected_track': {
                    'title': best_track.get('title', 'Unknown'),
                    'bpm': best_track.get('bpm', 0),
                    'key': best_track.get('key', 'Unknown')
                }
            })
            
            # 记录选曲评分明细
            debug_selection_score_details.append({
                'round': iteration,
                'track': {
                    'title': best_track.get('title', 'Unknown'),
                    'bpm': best_track.get('bpm', 0),
                    'key': best_track.get('key', 'Unknown'),
                    'energy': best_track.get('energy', 50)
                },
                'total_score': best_score,
                'scores': {
                    'key_score': metrics.get('key_score', 0),
                    'bpm_score': get_bpm_compatibility_flexible(current_bpm, best_track.get('bpm', 0)),
                    'bpm_diff': metrics.get('bpm_diff', 0),
                    'energy_score': abs(best_track.get('energy', 50) - current_energy),
                    'style_score': 0,  # 需要从metrics中提取
                    'drop_score': 0,  # 需要从metrics中提取
                    'drop_alignment': metrics.get('drop_alignment', None),
                    'beat_alignment': metrics.get('beat_offset_diff', None)
                }
            })
        
        # 尾曲选择优化：在最后2-3首时特殊处理
        remaining_count = len(remaining_tracks) - sum(1 for t in remaining_tracks if t.get('_used'))
        is_closure_phase = (len(sorted_tracks) >= target_count - 2) or (remaining_count <= 2)
        
        if is_closure_phase and remaining_count > 0:
            # 获取当前最后一首的信息
            current_track = sorted_tracks[-1]
            current_bpm = current_track.get('bpm', 0)
            current_energy = current_track.get('energy', 50)
            
            # 从剩余歌曲中选择最适合的尾曲
            closure_candidates = [t for t in remaining_tracks if not t.get('_used')]
            
            if closure_candidates:
                best_closure_track = None
                best_closure_score = -999999
                
                for candidate in closure_candidates:
                    candidate_bpm = candidate.get('bpm', 0)
                    candidate_key = candidate.get('key', '')
                    candidate_energy = candidate.get('energy', 50)
                    
                    closure_score = 0
                    
                    # 1. BPM略低（≤5）加分
                    if current_bpm > 0 and candidate_bpm > 0:
                        bpm_diff = current_bpm - candidate_bpm
                        if 0 <= bpm_diff <= 5:
                            closure_score += 20  # BPM略低，加分
                        elif bpm_diff < 0:
                            closure_score -= 15  # BPM上升，扣分
                        elif bpm_diff > 10:
                            closure_score -= 10  # BPM下降太多，扣分
                    
                    # 2. 调性回到起始调（兼容性≥80分）加分
                    if start_key and start_key != "未知" and candidate_key and candidate_key != "未知":
                        key_score_to_start = get_key_compatibility_flexible(start_key, candidate_key)
                        if key_score_to_start >= 100:
                            closure_score += 40  # 调性完全回到起始调，大幅加分
                        elif key_score_to_start >= 80:
                            closure_score += 30  # 调性回到起始调，加分
                        elif key_score_to_start >= 60:
                            closure_score += 15  # 调性兼容，中等加分
                    
                    # 3. 能量平滑下降（50-75）加分
                    if 50 <= candidate_energy <= 75:
                        energy_diff = current_energy - candidate_energy
                        if 0 <= energy_diff <= 15:
                            closure_score += 15  # 能量平滑下降，加分
                        elif energy_diff < 0:
                            closure_score -= 10  # 能量上升，扣分
                    elif candidate_energy > 75:
                        closure_score -= 5  # 能量太高，不适合尾曲
                    
                    # 4. 与当前歌曲的兼容性（仍然重要）
                    key_score_current = get_key_compatibility_flexible(
                        current_track.get('key', ''),
                        candidate_key
                    )
                    closure_score += key_score_current * 0.1  # 调性兼容性仍然重要（10%权重）
                    
                    bpm_diff_current = abs(current_bpm - candidate_bpm) if current_bpm > 0 and candidate_bpm > 0 else 999
                    if bpm_diff_current <= 10:
                        closure_score += (10 - bpm_diff_current) * 2  # BPM兼容性加分
                    
                    if closure_score > best_closure_score:
                        best_closure_score = closure_score
                        best_closure_track = candidate
                
                # 如果找到合适的尾曲（得分>0），优先使用它
                # 注意：这里只是标记，实际使用会在下一轮循环中通过正常排序逻辑选择
                # 但我们可以通过提高尾曲的得分来增加它被选中的概率
                if best_closure_track and best_closure_score > 0:
                    # 标记为尾曲候选，在下一轮循环中会优先考虑
                    best_closure_track['_closure_score'] = best_closure_score
                    best_closure_track['_is_closure_candidate'] = True
                    
                    if progress_logger:
                        closure_reasons = []
                        if start_key and start_key != "未知":
                            key_score = get_key_compatibility_flexible(start_key, best_closure_track.get('key', ''))
                            if key_score >= 80:
                                closure_reasons.append(f"调性回到起始调({start_key})")
                        if current_bpm > 0 and best_closure_track.get('bpm', 0) > 0:
                            bpm_diff = current_bpm - best_closure_track.get('bpm', 0)
                            if 0 <= bpm_diff <= 5:
                                closure_reasons.append(f"BPM略低({bpm_diff:.1f})")
                        if closure_reasons:
                            progress_logger.log(f"尾曲候选：{best_closure_track.get('title', '未知')} ({' | '.join(closure_reasons)})", console=False)
    
    # 修复：添加所有剩余未使用的歌曲（确保所有歌曲都被排进去）
    # 【Boutique】精品模式下，不再强制添加不满足条件的歌曲
    if not is_boutique:
        unused_remaining = [t for t in remaining_tracks if not t.get('_used')]
        total_input = len(tracks)
        total_sorted = len(sorted_tracks)
        total_unused = len(unused_remaining)
        if progress_logger:
            progress_logger.log(f"[V4调试] 排序循环结束：输入 {total_input} 首，已排序 {total_sorted} 首，剩余未使用 {total_unused} 首", console=True)
        if unused_remaining:
            if progress_logger:
                progress_logger.log(f"循环结束后，发现 {len(unused_remaining)} 首未处理的歌曲，将强制添加到末尾", console=True)
        
            # 按调性和BPM兼容性排序
            if sorted_tracks:
                last_track = sorted_tracks[-1]
                unused_remaining.sort(key=lambda t: (
                    -get_key_compatibility_flexible(last_track.get('key', ''), t.get('key', '')),
                    -get_bpm_compatibility_flexible(last_track.get('bpm', 0), t.get('bpm', 0))
                ))
            else:
                # 如果没有已排序的歌曲，按BPM排序
                unused_remaining.sort(key=lambda t: t.get('bpm', 0))
            
            for idx, track in enumerate(unused_remaining, start=len(sorted_tracks)):
                track['_used'] = True
                track_bpm = track.get('bpm', 0)
                track_energy = track.get('energy', 50)
                progress = idx / max(len(tracks), 1)
                
                # 【优化1】强制基于实际能量值分配阶段（更严格的阈值）
                if track_energy < 45:  # 从50降低到45
                    phase_name = "Warm-up"
                elif track_energy < 60:  # 从65降低到60
                    phase_name = "Build-up"
                elif track_energy < 75:  # 从80降低到75
                    phase_name = "Peak"
                elif track_energy < 85:  # 从90降低到85
                    phase_name = "Intense"
                else:
                    phase_name = "Intense"
                
                # 最后10%强制Cool-down（除非能量极高）
                if progress >= 0.9 and track_energy < 80:  # 从85降低到80
                    phase_name = "Cool-down"
                
                track['assigned_phase'] = phase_name
                track['_conflict_reasons'] = ["循环结束后添加（未在正常排序中处理）"]
            sorted_tracks.extend(unused_remaining)
            
            if progress_logger:
                progress_logger.log(f"[V4调试] 已强制添加 {len(unused_remaining)} 首剩余歌曲，当前总数：{len(sorted_tracks)} 首（应等于输入 {len(tracks)} 首）", console=True)
                if len(sorted_tracks) != len(tracks):
                    progress_logger.log(f"[V4警告] 歌曲数量不匹配！输入 {len(tracks)} 首，但排序后只有 {len(sorted_tracks)} 首（缺失 {len(tracks) - len(sorted_tracks)} 首）", console=True)

    # 修改：所有歌曲都已参与排序，冲突歌曲已在主序列中，只需统计
    conflict_count = sum(1 for t in sorted_tracks if t.get('_conflict', False))
    
    # 保留旧的冲突处理逻辑（但不再使用，因为所有歌曲都已排序）
    if False and conflict_tracks:
        import re
        insertable_conflicts = []  # BPM跨度<20，可以插入
        final_conflicts = []  # BPM跨度>=20，放到最后
        
        for conflict_track in conflict_tracks:
            conflict_reasons = conflict_track.get('_conflict_reasons', [])
            bpm_span = None
            
            # 从冲突原因中提取BPM跨度
            for reason in conflict_reasons:
                if 'BPM超大跨度' in reason:
                    try:
                        numbers = re.findall(r'\d+\.?\d*', reason)
                        if numbers:
                            bpm_span = float(numbers[0])
                            break
                    except:
                        pass
                elif 'BPM跨度' in reason and '超大' not in reason:
                    try:
                        numbers = re.findall(r'\d+\.?\d*', reason)
                        if numbers:
                            bpm_span = float(numbers[0])
                            break
                    except:
                        pass
            
            # 如果没有从原因中提取到，检查BPM是否与主序列相近
            if bpm_span is None:
                conflict_bpm = conflict_track.get('bpm', 0)
                if conflict_bpm > 0 and sorted_tracks:
                    # 检查与主序列的BPM差异
                    min_bpm_diff = min(
                        abs(conflict_bpm - t.get('bpm', 0))
                        for t in sorted_tracks
                        if t.get('bpm', 0) > 0
                    )
                    if min_bpm_diff < 20:
                        bpm_span = min_bpm_diff  # 使用最小BPM差异作为跨度
            
            # 如果BPM跨度<20，尝试插入；否则放到最后
            if bpm_span is not None and bpm_span < 20:
                insertable_conflicts.append((bpm_span, conflict_track))
            else:
                final_conflicts.append(conflict_track)
        
        # 按BPM跨度排序，优先插入跨度小的
        insertable_conflicts.sort(key=lambda x: x[0])
        
        # 尝试将可插入的冲突歌曲插入到相近BPM位置
        for bpm_span, conflict_track in insertable_conflicts:
            conflict_bpm = conflict_track.get('bpm', 0)
            if conflict_bpm <= 0:
                final_conflicts.append(conflict_track)
                continue
            
            # 优化：找到BPM和调性都相近的位置
            best_insert_idx = len(sorted_tracks)
            best_score = float('-inf')
            conflict_key = conflict_track.get('key', '')
            
            for idx, track in enumerate(sorted_tracks):
                track_bpm = track.get('bpm', 0)
                if track_bpm > 0:
                    bpm_diff = abs(conflict_bpm - track_bpm)
                    if bpm_diff < 20:
                        # 检查插入后不会造成新的大跨度
                        prev_bpm = sorted_tracks[idx - 1].get('bpm', 0) if idx > 0 else 0
                        next_bpm = sorted_tracks[idx + 1].get('bpm', 0) if idx + 1 < len(sorted_tracks) else 0
                        
                        # 检查插入后与前后歌曲的BPM跨度
                        can_insert = True
                        if prev_bpm > 0 and abs(conflict_bpm - prev_bpm) > 20:
                            can_insert = False
                        if next_bpm > 0 and abs(conflict_bpm - next_bpm) > 20:
                            can_insert = False
                        
                        if can_insert:
                            # 计算综合得分：BPM兼容性 + 调性兼容性
                            score = 0
                            # BPM得分（越小越好，所以用负值）
                            score -= bpm_diff * 2
                            
                            # 调性得分
                            track_key = track.get('key', '')
                            if conflict_key and track_key and conflict_key != "未知" and track_key != "未知":
                                key_score = get_key_compatibility_flexible(conflict_key, track_key)
                                score += key_score * 0.5  # 调性权重
                            
                            # 也考虑前后歌曲的调性
                            if idx > 0:
                                prev_key = sorted_tracks[idx - 1].get('key', '')
                                if conflict_key and prev_key and conflict_key != "未知" and prev_key != "未知":
                                    prev_key_score = get_key_compatibility_flexible(prev_key, conflict_key)
                                    score += prev_key_score * 0.3
                            
                            if score > best_score:
                                best_score = score
                                best_insert_idx = idx + 1  # 插入到后面
            
            # 如果找到合适位置，插入；否则放到最后
            if best_insert_idx < len(sorted_tracks):
                sorted_tracks.insert(best_insert_idx, conflict_track)
                conflict_track['_inserted'] = True
                conflict_track['_conflict'] = False  # 移除冲突标记
                if progress_logger:
                    progress_logger.log(f"插入BPM相近冲突歌曲（跨度{bpm_span:.1f}）：{conflict_track.get('title', 'Unknown')[:40]}", console=False)
            else:
                final_conflicts.append(conflict_track)
        
        # 剩余冲突歌曲按相近BPM/调性重新排序后放到最后
        if final_conflicts:
            reordered_conflicts = []
            reference_track = sorted_tracks[-1] if sorted_tracks else None
            remaining_conflicts = final_conflicts[:]

            while remaining_conflicts:
                if reference_track:
                    def conflict_score(track):
                        bpm_ref = reference_track.get('bpm') or 0
                        bpm_val = track.get('bpm') or 0
                        bpm_diff = abs(bpm_val - bpm_ref)
                        key_score = get_key_compatibility_flexible(reference_track.get('key', ''), track.get('key', ''))
                        return (bpm_diff, -key_score)

                    best_conflict = min(remaining_conflicts, key=conflict_score)
                else:
                    best_conflict = remaining_conflicts[0]

                reordered_conflicts.append(best_conflict)
                reference_track = best_conflict
                remaining_conflicts.remove(best_conflict)

            conflict_tracks = reordered_conflicts
        else:
            conflict_tracks = []
    
    # 全局优化：在保持BPM优先的前提下，优化调性连接
    # 限制优化范围，避免性能问题
    if len(sorted_tracks) > 10 and progress_logger:
        progress_logger.log("开始全局调性优化...", console=False)
    
    optimized_tracks = optimize_key_connections_global(sorted_tracks, progress_logger)
    
    # 修改：返回标记了冲突的歌曲列表（用于报告标注）
    marked_conflicts = [t for t in optimized_tracks if t.get('_is_conflict', False)]
    
    # 【最强大脑】将 Junk Drawer 里的歌追加到末尾
    if junk_drawer:
        if progress_logger:
            progress_logger.log(f"[质量屏障] 正在追加 {len(junk_drawer)} 首低兼容度歌曲到末尾备选区...", console=True)
        
        for misfit in junk_drawer:
            misfit['assigned_phase'] = "Extra (Misfit)"
            # 给最后一首歌加点衔接标记
            if optimized_tracks:
                misfit['_transition_score'] = -50  # 标记为极差连接
            optimized_tracks.append(misfit)

    # 返回排序结果、冲突列表和调试指标
    # 验证：确保所有输入歌曲都被包含在输出中
    if len(optimized_tracks) != len(tracks):
        if progress_logger:
            progress_logger.log(f"警告：输出歌曲数 ({len(optimized_tracks)}) 不等于输入歌曲数 ({len(tracks)})，缺失 {len(tracks) - len(optimized_tracks)} 首", console=True)
    metrics = {
        'n_input': len(tracks),
        'n_output': len(optimized_tracks),
        'conflict_count': len(marked_conflicts),
        'rounds': len(debug_rounds),
        'backtrack_count': len(debug_backtrack_logs),
        'conflict_count_debug': len(debug_conflict_logs)
    }
    
    # ========== 【V6优化P3.1】能量曲线验证和修正 ==========
    if len(optimized_tracks) > 10:  # 只有歌曲数>10才验证能量曲线
        if not validate_energy_curve(optimized_tracks):
            if progress_logger:
                progress_logger.log("⚠️ 能量曲线验证失败，进行自动修正", console=True)
            optimized_tracks = fix_energy_curve(optimized_tracks, progress_logger)
    
    return optimized_tracks, marked_conflicts, metrics


def validate_energy_curve(sorted_tracks: List[Dict]) -> bool:
    """
    【V6优化P3.1】验证能量曲线是否符合 Warm-up → Peak → Cool-down
    
    Returns:
        bool: True表示能量曲线完整，False表示需要修正
    """
    if len(sorted_tracks) < 5:
        return True  # 歌曲太少，不验证
    
    phases = [t.get('assigned_phase') for t in sorted_tracks if t.get('assigned_phase')]
    if not phases:
        return False  # 没有分配阶段，需要修正
    
    # 检查是否有Peak阶段（Peak/Sustain/Intense/Bang都算）
    has_peak = any(p in ['Peak', 'Sustain', 'Intense', 'Bang'] for p in phases)
    
    # 检查是否有Cool-down阶段（最后10%必须有Cool-down/Reset/Outro）
    last_10_percent = phases[-max(1, len(phases)//10):]
    has_cooldown = any(p in ['Cool-down', 'Reset', 'Outro'] for p in last_10_percent)
    
    # 检查是否有Warm-up阶段（前20%应该有Warm-up/Build-up）
    first_20_percent = phases[:max(1, len(phases)//5)]
    has_warmup = any(p in ['Warm-up', 'Build-up'] for p in first_20_percent)
    
    return has_peak and has_cooldown and has_warmup


def fix_energy_curve(tracks: List[Dict], progress_logger=None) -> List[Dict]:
    """
    【V6优化P3.2】修正能量曲线，确保有Peak和Cool-down
    
    策略：
    1. 找到能量最高的歌曲，强制标记为Peak
    2. 最后10%的歌曲，强制标记为Cool-down（除非能量极高>85）
    3. 前20%的歌曲，如果没有Warm-up，标记为Warm-up或Build-up
    """
    if len(tracks) < 5:
        return tracks  # 歌曲太少，不修正
    
    fixed_tracks = tracks.copy()
    total = len(fixed_tracks)
    
    # 1. 找到能量最高的歌曲，强制标记为Peak（如果还没标记）
    max_energy_track = max(fixed_tracks, key=lambda t: t.get('energy', 50))
    max_energy_idx = fixed_tracks.index(max_energy_track)
    if max_energy_track.get('assigned_phase') not in ['Peak', 'Sustain', 'Intense', 'Bang']:
        max_energy_track['assigned_phase'] = 'Peak'
        if progress_logger:
            progress_logger.log(f"✅ 修正：第{max_energy_idx+1}首（能量{max_energy_track.get('energy', 0)}）标记为Peak", console=False)
    
    # 2. 最后10%的歌曲，强制标记为Cool-down（除非能量极高>85）
    last_10_percent = fixed_tracks[-max(1, total//10):]
    for i, track in enumerate(last_10_percent):
        track_idx = fixed_tracks.index(track)
        if track.get('energy', 50) < 85:  # 能量<85才标记为Cool-down
            if track.get('assigned_phase') not in ['Cool-down', 'Reset', 'Outro']:
                track['assigned_phase'] = 'Cool-down'
                if progress_logger:
                    progress_logger.log(f"✅ 修正：第{track_idx+1}首（能量{track.get('energy', 0)}）标记为Cool-down", console=False)
    
    # 3. 前20%的歌曲，如果没有Warm-up，标记为Warm-up或Build-up
    first_20_percent = fixed_tracks[:max(1, total//5)]
    for i, track in enumerate(first_20_percent):
        track_idx = fixed_tracks.index(track)
        if track.get('assigned_phase') not in ['Warm-up', 'Build-up']:
            # 根据能量值决定是Warm-up还是Build-up
            if track.get('energy', 50) < 55:
                track['assigned_phase'] = 'Warm-up'
            else:
                track['assigned_phase'] = 'Build-up'
            if progress_logger:
                progress_logger.log(f"✅ 修正：第{track_idx+1}首（能量{track.get('energy', 0)}）标记为{track['assigned_phase']}", console=False)
    
    return fixed_tracks


def optimize_key_connections_global(tracks: List[Dict], progress_logger=None) -> List[Dict]:
    """
    全局调性优化：在保持BPM优先的前提下，优化调性连接
    允许小幅调整顺序（最多调整2-3个位置）以改善调性连接
    
    性能优化：
    - 限制优化窗口大小（每次只检查5-10首歌曲）
    - 限制调整距离（最多移动2-3个位置）
    - 只在调性兼容性明显提升时才调整
    """
    if len(tracks) <= 3:
        return tracks
    
    optimized = list(tracks)
    window_size = min(10, len(optimized) // 4)  # 优化窗口大小
    if window_size < 3:
        return tracks  # 窗口太小，不需要优化
    max_move_distance = 2  # 最多移动2个位置
    improvements = 0
    
    # 滑动窗口优化
    step_size = max(1, window_size // 2)  # 确保步长至少为1
    for start_idx in range(0, len(optimized) - window_size, step_size):
        end_idx = min(start_idx + window_size, len(optimized))
        window = optimized[start_idx:end_idx]
        
        if len(window) < 3:
            continue
        
        # 在窗口内尝试优化调性连接
        for i in range(1, len(window) - 1):
            current_track = window[i]
            prev_track = window[i - 1]
            next_track = window[i + 1]
            
            current_bpm = current_track.get('bpm', 0)
            prev_bpm = prev_track.get('bpm', 0)
            next_bpm = next_track.get('bpm', 0)
            
            # 计算当前调性连接得分
            prev_key_score = get_key_compatibility_flexible(
                prev_track.get('key', ''),
                current_track.get('key', '')
            )
            next_key_score = get_key_compatibility_flexible(
                current_track.get('key', ''),
                next_track.get('key', '')
            )
            current_total_score = prev_key_score + next_key_score
            
            # 尝试与前后2个位置内的歌曲交换
            best_swap_idx = None
            best_swap_score = current_total_score
            
            for swap_offset in range(-max_move_distance, max_move_distance + 1):
                if swap_offset == 0:
                    continue
                
                swap_idx = i + swap_offset
                if swap_idx < 0 or swap_idx >= len(window):
                    continue
                
                swap_track = window[swap_idx]
                swap_bpm = swap_track.get('bpm', 0)
                swap_bpm_diff = abs(current_bpm - swap_bpm)
                
                # 修复：改为软降权，不再硬过滤
                # BPM差>4时降权，但不排除
                bpm_swap_penalty = 0
                if swap_bpm_diff > 4:
                    bpm_swap_penalty = (swap_bpm_diff - 4) * 5  # BPM差每超过4，降权5分
                
                # 计算交换后的调性连接得分
                if swap_offset < 0:  # 向前交换
                    new_prev_track = window[swap_idx - 1] if swap_idx > 0 else prev_track
                    new_prev_key_score = get_key_compatibility_flexible(
                        new_prev_track.get('key', ''),
                        current_track.get('key', '')
                    )
                    new_next_key_score = get_key_compatibility_flexible(
                        current_track.get('key', ''),
                        swap_track.get('key', '')
                    )
                    swap_total_score = new_prev_key_score + new_next_key_score
                else:  # 向后交换
                    new_prev_key_score = get_key_compatibility_flexible(
                        prev_track.get('key', ''),
                        swap_track.get('key', '')
                    )
                    new_next_track = window[swap_idx + 1] if swap_idx < len(window) - 1 else next_track
                    new_next_key_score = get_key_compatibility_flexible(
                        swap_track.get('key', ''),
                        new_next_track.get('key', '')
                    )
                    swap_total_score = new_prev_key_score + new_next_key_score
                
                # 应用BPM降权（如果BPM差太大）
                swap_total_score -= bpm_swap_penalty
                
                # 如果调性连接明显改善（提升>=20分，考虑BPM降权后），考虑交换
                if swap_total_score > best_swap_score + 20:
                    best_swap_idx = swap_idx
                    best_swap_score = swap_total_score
            
            # 如果找到更好的交换，执行交换
            if best_swap_idx is not None:
                # 在实际列表中交换
                actual_i = start_idx + i
                actual_swap_idx = start_idx + best_swap_idx
                optimized[actual_i], optimized[actual_swap_idx] = optimized[actual_swap_idx], optimized[actual_i]
                improvements += 1
                if progress_logger and improvements % 5 == 0:
                    progress_logger.log(f"全局优化：已优化 {improvements} 处调性连接", console=False)
        
        # 更新窗口（因为可能已经交换了）
        optimized[start_idx:end_idx] = window
    
    if progress_logger and improvements > 0:
        progress_logger.log(f"全局调性优化完成：共优化 {improvements} 处调性连接", console=False)
    
    return optimized

def generate_transition_advice(curr_track: Dict, next_track: Dict, transition_idx: int) -> List[str]:
    """生成单对歌曲之间的混音建议"""
    advice = []
    
    curr_key = curr_track.get('key', '')
    next_key = next_track.get('key', '')
    curr_bpm = curr_track.get('bpm', 0)
    next_bpm = next_track.get('bpm', 0)
    curr_title = curr_track.get('title', 'Unknown')[:40]
    next_title = next_track.get('title', 'Unknown')[:40]
    curr_mix_out = curr_track.get('mix_out_point')
    next_mix_in = next_track.get('mix_in_point')
    
    # 调性兼容性分析
    if curr_key and next_key and curr_key != "未知" and next_key != "未知":
        key_score = get_key_compatibility_flexible(curr_key, next_key)
        
        # 调整阈值：95+完美和谐，85+非常和谐，70+较和谐，其他需要技巧
        if key_score >= 95:
            advice.append(f"    ✅ 调性过渡：{curr_key} → {next_key} （完美和谐，直接混音即可）")
        elif key_score >= 85:
            advice.append(f"    ✅ 调性过渡：{curr_key} → {next_key} （非常和谐，直接混音即可）")
        elif key_score >= 70:
            advice.append(f"    ⚠️ 调性过渡：{curr_key} → {next_key} （较和谐，标准混音即可）")
        else:
            try:
                curr_num = int(curr_key[:-1])
                next_num = int(next_key[:-1])
                diff = abs(curr_num - next_num)
                
                advice.append(f"    ⚠️ 调性过渡：{curr_key} → {next_key} （需要技巧）")
                
                if diff > 4:
                    advice.append(f"       • 建议混音手法：使用Echo/Filter效果器过渡")
                    advice.append(f"       • 在低能量段落（Intro/Outro）混音")
                    advice.append(f"       • 考虑使用Keylock功能微调")
                elif diff > 2:
                    advice.append(f"       • 建议混音手法：使用Filter Sweep过渡")
                    advice.append(f"       • 在Breakdown处混入")
                else:
                    advice.append(f"       • 建议混音手法：标准混音即可，注意能量衔接")
            except:
                advice.append(f"       • 建议混音手法：使用Filter效果器平滑过渡")
                advice.append(f"       • 在低能量段落混音")
    
    # ========== 【V4.0 Ultra+ 专家级增强】深度混音审计 (Big Brain Audit) ==========
    
    # 1. 乐句对齐审计 (Phrasing Alignment)
    if curr_mix_out is not None and next_mix_in is not None and curr_bpm > 0:
        # 计算乐句位置（假设16小节为一个大乐句）
        beats_per_bar = 4
        phrase_len_beats = 16 * beats_per_bar
        
        # 简化计算：检查 Mix-In 是否在理想的乐句点上（对齐 32/64 拍）
        is_phrase_aligned = (int(next_mix_in * next_bpm / 60) % 32) <= 1
        if is_phrase_aligned:
            advice.append(f"    📏 乐句对齐 (Phrasing): ✅ 完美乐句点进入 (对齐 32 拍)")
        else:
            advice.append(f"    📏 乐句对齐 (Phrasing): ⚠️ 进歌点非标准乐句起始，建议手动对齐 Beatgrid")

    # 2. 频段平衡与音色审计 (Timbre & EQ Balance)
    curr_low = curr_track.get('tonal_balance_low', 0.5)
    next_low = next_track.get('tonal_balance_low', 0.5)
    if abs(curr_low - next_low) > 0.3:
        advice.append(f"    🎚️ 频段审计 (EQ): {'下一首低频较重，建议提前 Cut Bass' if next_low > curr_low else '上一首低频较厚，建议使用 Bass Swap 技巧'}")
        
    # 3. 人声冲突 V2 保护 (Vocal Protection V2)
    curr_vocal = curr_track.get('vocal_ratio', 0.5)
    next_vocal = next_track.get('vocal_ratio', 0.5)
    if curr_vocal > 0.7 and next_vocal > 0.7:
        advice.append(f"    🗣️ 人声预警 (Vocal Clash): ⚠️ 双重人声冲突风险！建议其中一轨关闭 Vocal Stem")

    # ========== 【Neural Linkage】取长补短：极品 Mashup 联动提醒 (Big Brain Hook) ==========
    if MASHUP_ENABLED:
        try:
            m_score, m_details = MASHUP_INTELLIGENCE.calculate_mashup_score(curr_track, next_track)
            if m_score >= 85:
                # 1. 显式识别极品匹配，并提供 Stems 指南
                guide = MASHUP_INTELLIGENCE.generate_unified_guide(curr_track, next_track, m_score, m_details)
                advice.append(f"    🔥 极品 MASHUP 机会 (Neural Match: {m_score:.1f}/100):")
                advice.append(f"       • 策略: {m_details.get('mashup_pattern', '实时互补混音')}")
                
                # 2. V4.1 新增：获取精确甜点
                sweet_spots = MASHUP_INTELLIGENCE.get_mashup_sweet_spots(curr_track, next_track)
                if sweet_spots.get('can_mashup'):
                    for spot in sweet_spots['best_spots']:
                        advice.append(f"       • 甜点: {spot['type']} @ {spot['timestamp']:.1f}s - {spot['reason']}")
                
                if 'cultural_affinity' in m_details:
                    advice.append(f"       • 契合点: {m_details['cultural_affinity']}")
                advice.append(f"       • 操作: {guide[2] if len(guide) > 2 else '尝试 Stems 分离混音'}")
            
            # 3. V4.1 新增：乐句长度对齐详情
            curr_outro_bars = curr_track.get('outro_bars', 8)
            next_intro_bars = next_track.get('intro_bars', 8)
            advice.append(f"    📏 物理量化: A-Outro [{curr_outro_bars} Bars] | B-Intro [{next_intro_bars} Bars]")
            if curr_outro_bars == next_intro_bars:
                advice.append(f"       ✅ 乐句完美对齐 ({curr_outro_bars}x{next_intro_bars})，律动无缝切换")
            
            # 【V6.2】深度频谱对冲审计报告
            if 'bass_clash' in m_details:
                advice.append(f"    🎚️ 频谱预警 (Spectral): {m_details['bass_clash']}")
        except: pass

    # 4. 【V6.2】节奏拍号屏障审计 (Meter Shield Audit)
    curr_ts = curr_track.get('time_signature', '4/4')
    next_ts = next_track.get('time_signature', '4/4')
    if curr_ts != next_ts:
        advice.append(f"    ⚠️ 节奏冲突 (Meter Clash): {curr_ts} vs {next_ts} (混音极度危险，建议硬切)")
    
    # ========== 【Phase 11】最强大脑：审美策展建议 (AESTHETIC BIBLE) ==========
    if AESTHETIC_ENABLED:
        ae_advice = AESTHETIC_CURATOR.get_mix_bible_advice(curr_track, next_track)
        advice.append(f"    🎨 审美策展 (Aesthetic Guide):")
        advice.append(f"       • 推荐手法: {ae_advice['technique']}")
        advice.append(f"       • 建议时长: {ae_advice['suggested_duration']}")
        advice.append(f"       • 核心氛围: {ae_advice['vibe_target']}")
    
    # ========== 【Intelligence-V5】叙事维度注入：叙事连贯性能量 (Narrative Advice) ==========
    if NARRATIVE_ENABLED:
        nr_advice = NARRATIVE_PLANNER.get_narrative_advice(curr_track, next_track)
        advice.append(f"    📖 叙事连贯 (Narrative Link):")
        advice.append(f"       • 音乐学背景: {nr_advice}")
    
    # BPM过渡建议（放宽到15）
    if curr_bpm and next_bpm:
        bpm_diff = abs(curr_bpm - next_bpm)
        if bpm_diff > 15:
            advice.append(f"    ⚠️ BPM跨度：{curr_bpm:.1f} → {next_bpm:.1f} BPM （跨度 {bpm_diff:.1f}，超过15）")
            advice.append(f"       • 建议：使用Master Tempo功能，或逐步调整BPM")
        elif bpm_diff > 12:
            advice.append(f"    ⚠️ BPM跨度：{curr_bpm:.1f} → {next_bpm:.1f} BPM （跨度 {bpm_diff:.1f}，接近上限）")
            advice.append(f"       • 建议：使用Master Tempo功能，或逐步调整BPM")
        elif bpm_diff > 8:
            advice.append(f"    📊 BPM过渡：{curr_bpm:.1f} → {next_bpm:.1f} BPM （跨度 {bpm_diff:.1f}）")
            advice.append(f"       • 建议：注意BPM变化，可以逐步调整")
        elif bpm_diff > 4:
            advice.append(f"    📊 BPM过渡：{curr_bpm:.1f} → {next_bpm:.1f} BPM （跨度 {bpm_diff:.1f}）")
            advice.append(f"       • 建议：注意BPM变化，可以逐步调整")
            
    # 【Phase 10】专业混音窗口 (A/B Entry vs C/D Exit) - Big Brain Mode
    curr_exit_bars = curr_track.get('exit_bars', 0)
    next_entry_bars = next_track.get('entry_bars', 0)
    
    # 获取 AI 分析的结构数据，用于 cross-check
    curr_struct = curr_track.get('structure', {})
    next_struct = next_track.get('structure', {})
    
    if curr_track.get('hotcue_C') or next_track.get('hotcue_A'):
        advice.append(f"    🎯 专业层叠混音 (Transition Guard):")
        
        # 1. 核心对齐指导与 Phrase-Shift 检查
        if curr_track.get('hotcue_C') and next_track.get('hotcue_A'):
            advice.append(f"       • 动作：让 [上一首 C点] 对齐 [这一首 A点]")
            
            # Phrase 完整性检查 - 防止“抢拍”或“拖拍”
            if curr_exit_bars > 0 and next_entry_bars > 0:
                if curr_exit_bars == next_entry_bars:
                    advice.append(f"       • ✅ 黄金层叠：{curr_exit_bars}b 乐句完美同步")
                else:
                    # 风险预警：进度不一致
                    advice.append(f"       • ⚠️ 长度差：出歌{curr_exit_bars}b vs 进歌{next_entry_bars}b (注意调整衰减速度)")
            
            advice.append(f"       • 节点：上一首到 {chr(ord('A')+3)}点(D) 时，此首应在 {chr(ord('A')+1)}点(B) 完成统治")
            
        # 2. AI 混合建议 (AI-Ghost Windowing)
        elif curr_track.get('hotcue_C'):
            # 用户设了出歌点，但下一首没打点 -> AI 算一个匹配的进歌点
            fallback_bars = curr_exit_bars if curr_exit_bars > 0 else 16
            advice.append(f"       • 建议：上一首出歌窗口 {fallback_bars}b，建议下一首在该长度前开始进场")
            if next_track.get('mix_in_point'):
                advice.append(f"       • AI 匹配：已自动将下一首 A点 锚定在 AI Mix-In")
        
        elif next_track.get('hotcue_A'):
            # 用户设了进歌点，但上一首没打点
            fallback_bars = next_entry_bars if next_entry_bars > 0 else 16
            advice.append(f"       • 建议：这一首进歌窗口 {fallback_bars}b，请在上一首结束前至少 {fallback_bars}b 处切入")

    # 3. 乐句位置风险 (Phrase Alignment Check)
    # 如果手动 A 点没在 AI 生成的乐句起始位置，给出警告
    if next_track.get('hotcue_A') and next_struct:
        # 这里逻辑较复杂，简化为：检查 A 点是否在结构标记点的 0.5s 误差范围内
        struct_pts = []
        if isinstance(next_struct, dict) and 'structure' in next_struct:
            for pts in next_struct['structure'].values():
                if isinstance(pts, list): struct_pts.extend(pts)
                elif isinstance(pts, (int, float)): struct_pts.append(pts)
        
        a_point = next_track['hotcue_A']
        is_aligned = any(abs(a_point - p) < 0.5 for p in struct_pts)
        if not is_aligned and struct_pts:
            advice.append(f"    ⚠️ 乐句偏移：手动A点未对齐 AI 乐句起始点，建议检查节拍对齐 (Grid Check)")
    
    # ========== 【V6.2新增】律动变化警告 ==========
    # 检测Genre变化和律动冲突
    curr_genre = curr_track.get('genre', '').lower()
    next_genre = next_track.get('genre', '').lower()
    
    # 定义律动组判断函数（与评分函数中的定义一致）
    def get_rhythm_group_from_genre(genre_str: str) -> str:
        """根据Genre字符串判断律动组"""
        genre_lower = genre_str.lower()
        
        # Four-on-Floor
        four_on_floor_keywords = [
            'house', 'deep house', 'tech house', 'progressive house',
            'techno', 'trance', 'hard trance', 'electro house', 'edm',
            'minimal', 'acid house', 'chicago house', 'detroit techno'
        ]
        for keyword in four_on_floor_keywords:
            if keyword in genre_lower:
                return 'four_on_floor'
        
        # Breakbeat
        breakbeat_keywords = [
            'breaks', 'breakbeat', 'uk garage', 'speed garage',
            'drum and bass', 'jungle', 'dnb', 'd&b', 'garage'
        ]
        for keyword in breakbeat_keywords:
            if keyword in genre_lower:
                return 'breakbeat'
        
        # Half-time
        half_time_keywords = [
            'trap', 'dubstep', 'bass music', 'future bass',
            'riddim', 'brostep', 'chillstep'
        ]
        for keyword in half_time_keywords:
            if keyword in genre_lower:
                return 'half_time'
        
        # Latin
        latin_keywords = [
            'afro', 'afro house', 'latin', 'tribal', 'baile funk',
            'reggaeton', 'dembow', 'moombahton'
        ]
        for keyword in latin_keywords:
            if keyword in genre_lower:
                return 'latin'
        
        return 'four_on_floor'
    
    curr_rhythm_group = get_rhythm_group_from_genre(curr_genre)
    next_rhythm_group = get_rhythm_group_from_genre(next_genre)
    
    # 如果律动组不同，添加警告
    if curr_rhythm_group != next_rhythm_group:
        # 显示Genre名称（更直观）
        curr_genre_display = curr_track.get('genre', 'Unknown')
        next_genre_display = next_track.get('genre', 'Unknown')
        
        if curr_rhythm_group == 'half_time' or next_rhythm_group == 'half_time':
            advice.append(f"    ⚠️ 律动变化：{curr_genre_display} → {next_genre_display}")
            advice.append(f"       • 律动类型：{curr_rhythm_group} → {next_rhythm_group}")
            advice.append(f"       • 建议：需要快速切换（8-16拍内完成）")
            advice.append(f"       • 技巧：在Breakdown或Drop前快速切换，使用Filter/Echo Out过渡")
        elif curr_rhythm_group == 'breakbeat' or next_rhythm_group == 'breakbeat':
            advice.append(f"    ⚠️ 律动变化：{curr_genre_display} → {next_genre_display}")
            advice.append(f"       • 律动类型：{curr_rhythm_group} → {next_rhythm_group}")
            advice.append(f"       • 建议：在Breakdown处过渡，避免鼓点重叠")
        elif curr_rhythm_group == 'latin' or next_rhythm_group == 'latin':
            advice.append(f"    ℹ️ 风格变化：{curr_genre_display} → {next_genre_display}")
            advice.append(f"       • 律动类型：{curr_rhythm_group} → {next_rhythm_group}")
            advice.append(f"       • 建议：可以过渡，注意律动感的变化")
        else:
            advice.append(f"    ℹ️ 风格变化：{curr_genre_display} → {next_genre_display}")
            advice.append(f"       • 律动类型：{curr_rhythm_group} → {next_rhythm_group}")
    
    # 人声/鼓点匹配建议
    curr_vocals = curr_track.get('vocals')
    next_vocals = next_track.get('vocals')
    curr_drums = curr_track.get('drums')
    next_drums = next_track.get('drums')
    
    if curr_mix_out and next_mix_in and curr_vocals and next_vocals:
        # 检查当前歌曲的混出点是否在人声段落
        current_out_vocals = False
        for seg_start, seg_end in curr_vocals.get('segments', []):
            if seg_start <= curr_mix_out <= seg_end:
                current_out_vocals = True
                break
        
        # 检查下一首的混入点是否在人声段落
        next_in_vocals = False
        for seg_start, seg_end in next_vocals.get('segments', []):
            if seg_start <= next_mix_in <= seg_end:
                next_in_vocals = True
                break
        
        # 检查鼓点段落
        current_out_drums = False
        if curr_drums:
            for seg_start, seg_end in curr_drums.get('segments', []):
                if seg_start <= curr_mix_out <= seg_end:
                    current_out_drums = True
                    break
        
        next_in_drums = False
        if next_drums:
            for seg_start, seg_end in next_drums.get('segments', []):
                if seg_start <= next_mix_in <= seg_end:
                    next_in_drums = True
                    break
        
        # 给出建议
        if current_out_vocals and next_in_vocals:
            advice.append(f"    ⚠️ 混音元素：人声 → 人声 （不推荐）")
            advice.append(f"       • 建议：调整混音点，避免人声重叠")
            advice.append(f"       • 理想情况：人声混鼓点/旋律，或鼓点混人声")
        elif current_out_vocals and not next_in_vocals:
            if next_in_drums:
                advice.append(f"    ✅ 混音元素：人声 → 鼓点 （推荐）")
            else:
                advice.append(f"    ✅ 混音元素：人声 → 旋律/乐器 （推荐）")
        elif not current_out_vocals and next_in_vocals:
            if current_out_drums:
                advice.append(f"    ✅ 混音元素：鼓点 → 人声 （推荐）")
            else:
                advice.append(f"    ✅ 混音元素：旋律/乐器 → 人声 （推荐）")
        elif current_out_drums and next_in_drums:
            advice.append(f"    ✅ 混音元素：鼓点 → 鼓点 （可以）")
    
    # 混音点建议
    if curr_mix_out and next_mix_in:
        # 计算建议的混音时长
        bpm_diff = abs(curr_bpm - next_bpm) if curr_bpm and next_bpm else 0
        key_score = get_key_compatibility_flexible(curr_key, next_key) if curr_key and next_key else 50
        
        if key_score >= 80 and bpm_diff <= 4:
            mix_duration = "16-32拍（短混音）"
        elif key_score >= 60 and bpm_diff <= 6:
            mix_duration = "32-64拍（中混音）"
        else:
            mix_duration = "64-128拍（长混音）"
        
        advice.append(f"    🎯 混音点建议：")
        advice.append(f"       • 从 {curr_title} 的 {curr_mix_out:.1f}秒 开始淡出")
        advice.append(f"       • 在 {next_title} 的 {next_mix_in:.1f}秒 开始混入")
        advice.append(f"       • 建议混音时长：{mix_duration}")
    
    # 效果器推荐
    if curr_key and next_key and curr_key != "未知" and next_key != "未知":
        key_score = get_key_compatibility_flexible(curr_key, next_key)
        bpm_diff = abs(curr_bpm - next_bpm) if curr_bpm and next_bpm else 0
        
        try:
            curr_num = int(curr_key[:-1])
            next_num = int(next_key[:-1])
            diff = abs(curr_num - next_num)
            
            advice.append(f"    🎚️ 效果器推荐：")
            
            if key_score < 60 or diff > 4:
                advice.append(f"       • Echo Delay + Low Pass Filter")
                advice.append(f"       • 参数：Echo Time=1/2拍，Filter Cutoff=20-30%")
            elif diff > 2:
                advice.append(f"       • Filter Sweep")
                advice.append(f"       • 参数：Filter Cutoff从100%降至20%，用时32-64拍")
            elif bpm_diff > 6:
                advice.append(f"       • Master Tempo + Reverb")
                advice.append(f"       • 参数：BPM逐步调整，Reverb=25-30%")
            elif key_score >= 80:
                advice.append(f"       • 标准混音（可选Subtle Reverb）")
                advice.append(f"       • 参数：Reverb=15-20%（可选）")
            else:
                advice.append(f"       • 标准混音即可")
        except:
            pass
    
    # ========== V3.0 Ultra+ 专家报告：低音相位与人声防撞 ==========
    v3_metrics = next_track.get('_transition_metrics', {})
    if v3_metrics.get('bass_swap_required'):
        advice.append(f"    🔊 低音相位审计 (Bass Phase Guard):")
        advice.append(f"       • 🔴 警告：{v3_metrics.get('bass_swap_reason', '双轨低频对撞')}")
        advice.append(f"       • 建议：强制执行 [Bass Swap / Low Cut] 过渡")
    
    if v3_metrics.get('v3_vocal_shield_active'):
        advice.append(f"    🗣️ 人声避让协议 (Vocal Shield):")
        advice.append(f"       • 🔴 警告：建议混音区域存在人声碰撞 (Vocal Clash)")
        advice.append(f"       • 建议：在此处使用 Quick Cut 或等上一首人声彻底结束后再推高电平")

    if v3_metrics.get('groove_conflict') == "swing_mismatch" or v3_metrics.get('swing_mismatch_penalty'):
        advice.append(f"    🥁 律动不匹配 (Swing Mismatch):")
        advice.append(f"       • 🔴 警告：直拍 (Straight) 与摇摆 (Swing) 律动跨合，容易产生节奏打架")
        advice.append(f"       • 建议：避免在鼓点段落长混，使用 Quick Cut 或 Wait for Breakdown")

    # 【Phase 11.2】整合 Mashup Archetypes (V5.0 顶级配方)
    if MASHUP_ENABLED:
        archetype = MASHUP_INTELLIGENCE.get_mashup_archetype(curr_track, next_track)
        if archetype:
            advice.append(f"\n   🍳 [顶级配方] {archetype['name']}:")
            for step in archetype['steps']:
                advice.append(f"      - {step}")
            advice.append(f"      💡 原理: {archetype['rationale']}")

    # ========== 【V6.0 Audit】审计追踪板块 (Debug Only / Expert Mode) ==========
    # 尝试从 best_track['_transition_metrics'] 或直接属性中获取
    audit_trace = next_track.get('audit_trace', [])
    if not audit_trace and '_transition_metrics' in next_track:
        audit_trace = next_track['_transition_metrics'].get('audit_trace', [])
    
    if audit_trace:
        advice.append(f"\n    🔍 [V6.0 系统审计] 决策链路追踪 (Audit Trace):")
        for log in audit_trace:
            dim = log.get('dim', 'Unknown')
            val = log.get('val', 0.0)
            score_impact = log.get('score', 0)
            reason = log.get('reason', '')
            
            icon = "📈" if score_impact > 0 else "📉"
            sign = "+" if score_impact > 0 else ""
            advice.append(f"       • {icon} {dim}: {val:.2f} | 影响: {sign}{score_impact} ({reason})")

    return advice

def generate_mixing_advice(tracks: List[Dict]) -> str:
    """生成混音建议（保留用于兼容性）"""
    if not tracks:
        return ""
    
    advice = []
    
    # 分析调性过渡
    key_transitions = []
    for i in range(len(tracks) - 1):
        curr_key = tracks[i].get('key', '')
        next_key = tracks[i+1].get('key', '')
        if curr_key and next_key and curr_key != "未知" and next_key != "未知":
            key_score = get_key_compatibility_flexible(curr_key, next_key)
            key_transitions.append((i, tracks[i].get('title', ''), curr_key, next_key, key_score))
    
    # 找出可能需要特别注意的过渡
    difficult_transitions = [t for t in key_transitions if t[4] < 60]
    smooth_transitions = [t for t in key_transitions if t[4] >= 80]
    
    advice.append("=" * 60)
    advice.append("混音建议")
    advice.append("=" * 60)
    
    if smooth_transitions:
        try:
            advice.append(f"\n[和谐] 发现 {len(smooth_transitions)} 个非常和谐的过渡：")
        except:
            advice.append(f"\n[Harmonic] Found {len(smooth_transitions)} very smooth transitions:")
        for idx, title, curr, next_key, score in smooth_transitions[:5]:
            advice.append(f"  • {title[:40]} ({curr} → {next_key}) - 直接混音即可")
    
    if difficult_transitions:
        advice.append(f"\n⚠️ 发现 {len(difficult_transitions)} 个需要技巧的过渡：")
        for idx, title, curr, next_key, score in difficult_transitions[:5]:
            advice.append(f"\n  • {title[:40]} ({curr} → {next_key})")
            advice.append(f"    建议混音手法：")
            
            # 根据调性差异给出建议
            try:
                curr_num = int(curr[:-1])
                next_num = int(next_key[:-1])
                diff = abs(curr_num - next_num)
                
                if diff > 4:
                    advice.append(f"    - 使用Echo/Filter效果器过渡")
                    advice.append(f"    - 在低能量段落（Intro/Outro）混音")
                    advice.append(f"    - 考虑使用Keylock功能微调")
                elif diff > 2:
                    advice.append(f"    - 使用Filter Sweep过渡")
                    advice.append(f"    - 在Breakdown处混入")
                else:
                    advice.append(f"    - 标准混音即可，注意能量衔接")
            except:
                advice.append(f"    - 使用Filter效果器平滑过渡")
                advice.append(f"    - 在低能量段落混音")
    else:
        try:
            advice.append("\n[和谐] 所有过渡都很和谐，可以流畅混音！")
        except:
            advice.append("\n[Harmonic] All transitions are smooth, can mix fluently!")
    
    # BPM过渡建议
    bpm_transitions = []
    for i in range(len(tracks) - 1):
        curr_bpm = tracks[i].get('bpm', 0)
        next_bpm = tracks[i+1].get('bpm', 0)
        if curr_bpm and next_bpm:
            diff = abs(curr_bpm - next_bpm)
            bpm_transitions.append((i, tracks[i].get('title', ''), curr_bpm, next_bpm, diff))
    
    large_bpm_jumps = [t for t in bpm_transitions if t[4] > 8]
    if large_bpm_jumps:
        advice.append(f"\n📊 BPM跨度较大（>8 BPM）的过渡：")
        for idx, title, curr, next_bpm, diff in large_bpm_jumps[:5]:
            advice.append(f"  • {title[:40]}: {curr:.1f} → {next_bpm:.1f} BPM (跨度 {diff:.1f})")
            advice.append(f"    建议：使用Master Tempo功能，或逐步调整BPM")
    
    # 混音点建议
    advice.append(f"\n🎯 精确混音点建议：")
    mix_point_count = 0
    for i in range(len(tracks) - 1):
        curr_track = tracks[i]
        next_track = tracks[i+1]
        
        curr_mix_out = curr_track.get('mix_out_point')
        next_mix_in = next_track.get('mix_in_point')
        
        if curr_mix_out and next_mix_in:
            mix_point_count += 1
            if mix_point_count <= 5:  # 只显示前5个
                try:
                    curr_title = curr_track.get('title', 'Unknown')[:30]
                    next_title = next_track.get('title', 'Unknown')[:30]
                    advice.append(f"  {i+1}. {curr_title} → {next_title}")
                    advice.append(f"     • 从 {curr_title} 的 {curr_mix_out:.1f}秒 开始淡出")
                    advice.append(f"     • 在 {next_title} 的 {next_mix_in:.1f}秒 开始混入")
                    
                    # 计算建议的混音时长
                    bpm_diff = abs(curr_track.get('bpm', 120) - next_track.get('bpm', 120))
                    key_score = get_key_compatibility_flexible(
                        curr_track.get('key', ''), next_track.get('key', '')
                    )
                    
                    if key_score >= 80 and bpm_diff <= 4:
                        mix_duration = "16-32拍（短混音）"
                    elif key_score >= 60 and bpm_diff <= 6:
                        mix_duration = "32-64拍（中混音）"
                    else:
                        mix_duration = "64-128拍（长混音）"
                    advice.append(f"     • 建议混音时长：{mix_duration}")
                except:
                    pass
    
    if mix_point_count == 0:
        advice.append("  （部分歌曲的混音点未检测到，建议手动选择混音点）")
    
    # 效果器推荐
    advice.append(f"\n🎚️ 效果器使用建议：")
    effect_count = 0
    for i in range(min(5, len(tracks) - 1)):
        curr_track = tracks[i]
        next_track = tracks[i+1]
        
        curr_key = curr_track.get('key', '')
        next_key = next_track.get('key', '')
        key_score = get_key_compatibility_flexible(curr_key, next_key)
        bpm_diff = abs(curr_track.get('bpm', 120) - next_track.get('bpm', 120))
        
        if curr_key and next_key and curr_key != "未知" and next_key != "未知":
            try:
                curr_num = int(curr_key[:-1])
                next_num = int(next_key[:-1])
                diff = abs(curr_num - next_num)
                
                effect_count += 1
                next_title = next_track.get('title', 'Unknown')[:30]
                
                if key_score < 60 or diff > 4:
                    advice.append(f"  {i+1}. {next_title}")
                    advice.append(f"     • 推荐效果器：Echo Delay + Low Pass Filter")
                    advice.append(f"     • 参数：Echo Time=1/2拍，Filter Cutoff=20-30%")
                elif diff > 2:
                    advice.append(f"  {i+1}. {next_title}")
                    advice.append(f"     • 推荐效果器：Filter Sweep")
                    advice.append(f"     • 参数：Filter Cutoff从100%降至20%，用时32-64拍")
                elif bpm_diff > 6:
                    advice.append(f"  {i+1}. {next_title}")
                    advice.append(f"     • 推荐效果器：Master Tempo + Reverb")
                    advice.append(f"     • 参数：BPM逐步调整，Reverb=25-30%")
                elif key_score >= 80:
                    advice.append(f"  {i+1}. {next_title}")
                    advice.append(f"     • 推荐效果器：标准混音（可选Subtle Reverb）")
                    advice.append(f"     • 参数：Reverb=15-20%（可选）")
            except:
                pass
    
    if effect_count == 0:
        advice.append("  （所有过渡都很和谐，标准混音即可）")
    
    # 能量曲线建议
    energies = [t.get('energy', 50) for t in tracks]
    if len(energies) > 10:
        avg_energy = sum(energies) / len(energies)
        peak_idx = energies.index(max(energies))
        advice.append(f"\n🎵 能量分析：")
        advice.append(f"  • 平均能量：{avg_energy:.1f}/100")
        advice.append(f"  • 峰值位置：第 {peak_idx + 1} 首 ({tracks[peak_idx].get('title', '')[:30]})")
        if peak_idx < len(tracks) * 0.3:
            advice.append(f"  • 建议：峰值出现较早，可考虑后段加入更高能量歌曲")
        elif peak_idx > len(tracks) * 0.7:
            advice.append(f"  • 建议：能量曲线良好，可继续维持或逐步下降")
    
            advice.append("\n" + "=" * 60)
    
    return "\n".join(advice)

async def create_enhanced_harmonic_sets(playlist_name: str = "流行Boiler Room",
                                        songs_per_set: int = 40,  # 每个Set 40首歌曲
                                        min_songs: int = 25,
                                        max_songs: int = 40,
                                        enable_bridge: bool = False,
                                        enable_bridge_track: bool = True,
                                        is_boutique: bool = False,
                                        is_master: bool = False,
                                        is_live: bool = False,
                                        progress_logger=None):
    """创建增强版调性和谐Set
    
    Args:
        enable_bridge: 启用桥接模式，从曲库补充同风格歌曲（仅限电子乐风格）
        enable_bridge_track: 启用桥接曲自动插入（BPM跨度>15时插入桥接曲）
                            华语/K-Pop/J-Pop播放列表自动禁用
    """
    
    # 检测是否是华语/亚洲流行播放列表，自动禁用桥接曲
    asian_pop_keywords = ['华语', '中文', 'chinese', 'mandarin', 'cpop', 'c-pop',
                          'kpop', 'k-pop', '韩语', 'korean', 'jpop', 'j-pop', '日语', 'japanese']
    playlist_lower = playlist_name.lower()
    is_asian_pop = any(kw in playlist_lower for kw in asian_pop_keywords)
    if is_asian_pop and not is_boutique:
        enable_bridge_track = False
        print(f"[桥接曲] 检测到亚洲流行播放列表，自动禁用桥接曲功能")
    
    db = RekordboxDatabase()
    pyrekordbox_db = Rekordbox6Database()
    
    try:
        try:
            print("正在连接到Rekordbox数据库...")
        except:
            print("Connecting to Rekordbox database...")
        await db.connect()
        try:
            print("连接成功！")
        except:
            print("Connected!")
        
        # 查找播放列表 - 直接使用pyrekordbox查询
        target_playlist = None
        playlist_id = None
        
        # 首先尝试使用ID（如果输入的是数字）
        if playlist_name.isdigit():
            playlist_id = playlist_name
            try:
                # 尝试整数和字符串两种格式
                for test_id in [int(playlist_id), playlist_id]:
                    try:
                        playlist_songs = list(pyrekordbox_db.get_playlist_songs(PlaylistID=test_id))
                        if playlist_songs:
                            # 创建一个虚拟的playlist对象
                            class PlaylistObj:
                                def __init__(self, id, name):
                                    self.id = id
                                    self.name = name
                            target_playlist = PlaylistObj(test_id, f"Playlist {test_id}")
                            playlist_id = test_id
                            break
                    except:
                        continue
            except:
                pass
        
        # 如果ID查询失败，使用MCP数据库查询
        if not target_playlist:
            all_playlists = await db.get_playlists()
            
            # 首先尝试使用ID（如果输入的是数字）
            if playlist_name.isdigit():
                try:
                    playlist_id_str = str(playlist_name)
                    playlist_id_int = int(playlist_name)
                    for p in all_playlists:
                        if (str(p.id) == playlist_id_str or 
                            (isinstance(p.id, int) and p.id == playlist_id_int) or
                            (isinstance(p.id, str) and p.id == playlist_id_str)):
                            target_playlist = p
                            playlist_id = p.id
                            break
                except:
                    pass
            
            # 如果ID匹配失败，尝试名称匹配
            if not target_playlist:
                playlist_name_lower = playlist_name.lower().strip()
                candidates = []
                
                for p in all_playlists:
                    if p.name:
                        try:
                            p_name_lower = p.name.lower().strip()
                            # Exact match
                            if playlist_name_lower == p_name_lower:
                                candidates.append((3, p))
                            # Partial match
                            elif playlist_name_lower in p_name_lower or p_name_lower in playlist_name_lower:
                                candidates.append((1, p))
                        except:
                            pass

                if candidates:
                    # Sort logic: 
                    # 1. Exact match > Partial match (handled by score 3 vs 1)
                    # 2. Integer ID > UUID (Standard Rekordbox vs Imported)
                    # 3. Newer modification date
                    
                    def sort_key(item):
                        score, p = item
                        is_int = 0
                        try:
                            int(p.id)
                            is_int = 1
                        except ValueError:
                            pass
                        mod_time = p.modified_date or ""
                        return (score, is_int, mod_time)

                    candidates.sort(key=sort_key, reverse=True)
                    target_playlist = candidates[0][1]
                    playlist_id = target_playlist.id
                    
                    if len(candidates) > 1:
                        print(f"找到 {len(candidates)} 个匹配列表，自动选择最新/最标准的版本: {target_playlist.name} (ID: {target_playlist.id}, Tracks: {target_playlist.track_count})")
        
        # 如果找不到播放列表对象，但输入的是ID，直接使用ID
        if not target_playlist and playlist_name.isdigit():
            # 尝试整数和字符串两种格式
            for test_id in [int(playlist_name), playlist_name]:
                try:
                    test_songs = list(pyrekordbox_db.get_playlist_songs(PlaylistID=test_id))
                    if test_songs:
                        class PlaylistObj:
                            def __init__(self, id, name):
                                self.id = id
                                self.name = name
                        target_playlist = PlaylistObj(test_id, f"Playlist {test_id}")
                        playlist_id = test_id
                        break
                except:
                    continue
        
        if not target_playlist:
            try:
                safe_name = playlist_name.encode('utf-8', errors='ignore').decode('ascii', errors='ignore')
                print(f"Playlist not found: {safe_name}")
                print("请确认播放列表名称或ID是否正确")
            except:
                print("Playlist not found")
                print("Please confirm the playlist name or ID is correct")
            await db.disconnect()
            return
        
        if not playlist_id:
            playlist_id = target_playlist.id
        
        # Handle Folder logic: If it's a folder, recursively get tracks from children
        if target_playlist.is_folder:
            print(f"检测到 '{target_playlist.name}' 是一个文件夹，正在读取其下所有子列表...")
            try:
                # Recursive function to get all playlist IDs in folder
                def get_child_playlists(parent_id, all_playlists):
                    children = []
                    for p in all_playlists:
                        if p.parent_id == str(parent_id):
                            children.append(p)
                            if p.is_folder:
                                children.extend(get_child_playlists(p.id, all_playlists))
                    return children
                
                # Fetch all playlists first (we need them for tree traversal)
                all_db_playlists = await db.get_playlists()
                all_child_playlists = get_child_playlists(playlist_id, all_db_playlists)
                tracks_raw = []
                seen_ids = set()
                
                for child in all_child_playlists:
                    if child.is_folder: continue
                    child_tracks = await db.get_playlist_tracks(child.id)
                    for t in child_tracks:
                        if t.id not in seen_ids:
                            tracks_raw.append(t)
                            seen_ids.add(t.id)
                            
                print(f"从文件夹 '{target_playlist.name}' 中合并了 {len(tracks_raw)} 首歌曲")
                
            except Exception as e:
                print(f"读取文件夹失败: {e}")
                tracks_raw = []
        else:
            try:
                print(f"找到播放列表: {target_playlist.name}")
            except:
                try:
                    print("找到播放列表")
                except:
                    print("Found playlist")
            
            # 获取歌曲列表
            try:
                # 尝试标准获取
                tracks_raw = await db.get_playlist_tracks(playlist_id)
            except:
                # Fallback: 使用 pyrekordbox 直接获取 (修复 ID 类型问题)
                print(f"[Fallback] 使用 pyrekordbox 直接读取 ID={playlist_id}...")
                try:
                    pid_int = int(playlist_id)
                    playlist_songs = list(pyrekordbox_db.get_playlist_songs(PlaylistID=pid_int))
                except ValueError:
                    # 如果转换失败，尝试直接使用
                    playlist_songs = list(pyrekordbox_db.get_playlist_songs(PlaylistID=playlist_id))
                except Exception as e:
                    print(f"Fallback loading failed: {e}")
                    playlist_songs = []

                tracks_raw = []
                for song in playlist_songs:
                    if getattr(song, 'rb_local_deleted', 0) == 0:
                        content_id = getattr(song, 'ContentID', None)
                        if content_id:
                            content = pyrekordbox_db.get_content(ID=content_id)
                            if content:
                                from rekordbox_mcp.database import Track
                                track = Track(
                                    id=content.ID,
                                    content_uuid=content.UUID,
                                    title=content.Title or "",
                                    artist=content.ArtistName or "",
                                    file_path=content.FilePath or "",
                                    bpm=content.Tempo / 100.0 if content.Tempo else None,
                                    key=content.KeyName or "",
                                    energy=None
                                )
                                tracks_raw.append(track)
        
        if not tracks_raw:
            try:
                print("播放列表为空")
            except:
                print("Playlist is empty")
            await db.disconnect()
            return
        
        try:
            try:
                print(f"DEBUG: 原始加载 tracks_raw 数量: {len(tracks_raw)}")
                for i, t in enumerate(tracks_raw[:5]):
                    print(f"DEBUG: Sample {i+1}: {getattr(t, 'title', 'N/A')} | Path: {getattr(t, 'file_path', 'N/A')}")
            except: pass
            print(f"播放列表中共有 {len(tracks_raw)} 首歌曲")
            
            # 【V3.0 ULTRA+ 修复】添加去重逻辑：按 file_path 去重
            seen_paths = set()
            unique_tracks_raw = []
            for t in tracks_raw:
                file_path = getattr(t, 'file_path', '') or ''
                path_lower = file_path.lower()
                if path_lower and path_lower not in seen_paths:
                    seen_paths.add(path_lower)
                    unique_tracks_raw.append(t)
            
            if len(unique_tracks_raw) < len(tracks_raw):
                print(f"  [去重] 原始: {len(tracks_raw)}首 -> 去重后: {len(unique_tracks_raw)}首")
                tracks_raw = unique_tracks_raw
            else:
                print(f"  [检查] 无重复曲目")
            
            print("\n开始深度分析歌曲...")
            print("=" * 60)
        except:
            print(f"Found {len(tracks_raw)} tracks in playlist")
            print("\nStarting deep analysis...")
            print("=" * 60)
        
        # 加载缓存
        cache = load_cache()
        cache_updated = False
        
        # 深度分析所有歌曲（使用缓存加速 + 并行分析）
        tracks = []
        start_time = datetime.now()
        cached_count = 0
        analyzed_count = 0
        
        # 并行分析函数
        def analyze_single_track(track_idx_track):
            idx, track = track_idx_track
            # 获取真实的 Content ID (对应曲库 ID)
            true_content_id = getattr(track, 'ContentID', None) or getattr(track, 'id', None) or getattr(track, 'ID', None)
            file_path = track.file_path if hasattr(track, 'file_path') else None
            
            if not file_path or not os.path.exists(file_path):
                # 【接口收敛】强制使用标准化追踪工具代替手动猜测
                track_title = getattr(track, 'title', '') or getattr(track, 'Title', '')
                if track_title:
                    found = smart_find_track(track_title)
                    if found:
                        file_path = found[0]
                        print(f"  [RefinedFinder] Redirected to: {file_path}")
                    else:
                        print(f"  [DEBUG] 跳过歌曲: {track_title} (文件不存在且找不回: {file_path})")
                        return (idx, None, False, False)
                else:
                    print(f"  [DEBUG] 跳过 ID={true_content_id} (无路径且无标题)")
                    return (idx, None, False, False)
            
            db_bpm = track.bpm if hasattr(track, 'bpm') and track.bpm else None
            
            ai_data = None # Initialize to avoid NameError
            
            # 检查缓存
            cached_res = get_cached_analysis(file_path, cache) if file_path else None
            
            # 处理增量更新逻辑 (get_cached_analysis 现在可能返回 (analysis, needs_update))
            if isinstance(cached_res, tuple):
                existing_analysis, needs_update = cached_res
            else:
                existing_analysis, needs_update = cached_res, False
                
            is_cached = existing_analysis is not None and not needs_update
            
            if existing_analysis and not needs_update:
                analysis = existing_analysis
            else:
                # 如果是增量更新，传递 existing_analysis
                analysis = deep_analyze_track(file_path, db_bpm, existing_analysis=existing_analysis) if file_path else None
                if analysis and file_path:
                    cache_analysis(file_path, analysis, cache)
                    # 如果之前是空的，算作新分析；如果是增量，算作更新
                    was_analyzed = True if not existing_analysis else True
                else:
                    was_analyzed = False
            
            # 【软件优先策略】优先使用数据库中的原始标记 (Rekordbox Priority)
            db_key = track.key or ""
            detected_key = analysis.get('key') if analysis else None
            
            if db_key and db_key not in ["未知", "Unknown", ""]:
                # 如果数据库有值，优先将其转换为统一的 Camelot 格式
                final_key = convert_open_key_to_camelot(db_key)
            else:
                final_key = detected_key if detected_key else "未知"
            
            # 【Phase 10】读取手动标记的 Cues (Memory & HotCues)
            manual_cues = []
            hotcues_map = {} # Kind -> timestamp
            try:
                cue_query = text("SELECT ID, Kind, InMsec, Comment FROM djmdCue WHERE ContentID = :content_id AND rb_local_deleted = 0")
                # 显式使用 session.connection() 的 execute 以增加稳定性
                with pyrekordbox_db.session.no_autoflush:
                    cue_results = pyrekordbox_db.session.execute(cue_query, {"content_id": true_content_id}).fetchall()
                    for cid, kind, inmsec, comment in cue_results:
                        time_sec = inmsec / 1000.0
                        manual_cues.append({
                            'kind': kind,
                            'time': time_sec,
                            'comment': comment or ""
                        })
                        if 1 <= kind <= 8:
                            hotcues_map[kind] = time_sec
            except Exception as cue_err:
                # 如果还是冲突，这里就是导致“没打点”的断点
                if "concurrent operations" in str(cue_err):
                    print(f"Warning: DB Busy for track {true_content_id}, retrying once...")
                    import time
                    time.sleep(0.1) # 短暂等待重试
                    try:
                        with pyrekordbox_db.session.no_autoflush:
                            cue_results = pyrekordbox_db.session.execute(cue_query, {"content_id": true_content_id}).fetchall()
                            for cid, kind, inmsec, comment in cue_results:
                                time_sec = inmsec / 1000.0
                                manual_cues.append({
                                    'kind': kind,
                                    'time': time_sec,
                                    'comment': comment or ""
                                })
                                if 1 <= kind <= 8:
                                    hotcues_map[kind] = time_sec
                    except: pass
                else:
                    print(f"Warning: Failed to fetch cues for track {true_content_id}: {cue_err}")

            # 【V6.0】语义标签提取 (Semantic Tagging from Comments)
            stags = set()
            VOCAL_KW = ['vocal', 'acapella', 'sing', 'voice', '人声']
            DROP_KW = ['drop', 'hook', 'energy', 'peak', '高潮', '炸']
            for cue in manual_cues:
                comment = cue['comment'].lower()
                if any(kw in comment for kw in VOCAL_KW): stags.add("VOCAL")
                if any(kw in comment for kw in DROP_KW): stags.add("DROP")

            # 进出点优先级逻辑 (A=Start In, B=Full In, C=Start Out, D=End Out)
            # 这是一个典型的“叠加上色”混音逻辑
            hotcue_A = hotcues_map.get(1)
            hotcue_B = hotcues_map.get(2)
            hotcue_C = hotcues_map.get(3)
            hotcue_D = hotcues_map.get(4)
            
            # 基础兼容性：保持 mix_in_point 为 mix 的起点
            final_mix_in = hotcue_A or (analysis.get('mix_in_point') if analysis else None)
            final_mix_out = hotcue_C or (analysis.get('mix_out_point') if analysis else None)
            
            # 计算混音窗口长度 (Mix Windows)
            entry_bars = 0
            exit_bars = 0
            track_bpm = analysis.get('bpm') or db_bpm or 120
            
            if hotcue_A and hotcue_B:
                entry_bars = round(((hotcue_B - hotcue_A) * (track_bpm / 60.0)) / 4.0)
            if hotcue_C and hotcue_D:
                exit_bars = round(((hotcue_D - hotcue_C) * (track_bpm / 60.0)) / 4.0)
            
            # 如果使用了手动打点，标记来源并尝试总结混音规格
            mix_info = ""
            if entry_bars > 0:
                mix_info += f"[Entry: {entry_bars}b] "
            elif hotcue_A:
                mix_info += "[Manual A-In] "
                
            if exit_bars > 0:
                mix_info += f"[Exit: {exit_bars}b] "
            elif hotcue_C:
                mix_info += "[Manual C-Out] "
            
            # 【修复】从文件名提取艺术家（如果数据库中没有）
            artist = track.artist or ""
            title = track.title or ""
            filename = Path(file_path).stem
            
            # 如果数据库有艺术家和标题，直接使用
            if artist and title:
                pass  # 使用数据库的值
            elif not artist and not title:
                # 都没有，从文件名解析
                if ' - ' in filename:
                    parts = filename.split(' - ', 1)
                    artist = parts[0].strip()
                    title = parts[1].strip() if len(parts) > 1 else filename
                elif '-' in filename:
                    parts = filename.split('-', 1)
                    artist = parts[0].strip()
                    title = parts[1].strip() if len(parts) > 1 else filename
                else:
                    title = filename
                    artist = "Unknown"
            elif not artist:
                # 只缺艺术家
                if ' - ' in filename:
                    artist = filename.split(' - ', 1)[0].strip()
                elif '-' in filename:
                    artist = filename.split('-', 1)[0].strip()
                else:
                    artist = "Unknown"
            elif not title:
                # 只缺标题，用文件名
                title = filename
            
            track_dict = {
                'id': true_content_id,
                'content_uuid': getattr(track, 'content_uuid', None),
                'title': title,
                'artist': artist,
                'file_path': file_path,
                'bpm': analysis.get('bpm') if analysis else (db_bpm or 120),
                'key': final_key,
                'energy': analysis.get('energy') if analysis else 50,
                'duration': (ai_data.get('format', {}).get('duration') if ai_data else None) or (analysis.get('duration') if analysis else 180),
                'mix_in_point': final_mix_in,
                'mix_out_point': final_mix_out,
                'hotcue_A': hotcue_A,
                'hotcue_B': hotcue_B,
                'hotcue_C': hotcue_C,
                'hotcue_D': hotcue_D,
                'entry_bars': entry_bars,
                'exit_bars': exit_bars,
                'manual_cues': manual_cues,
                'mix_info': mix_info.strip(),
                'genre': analysis.get('genre') if analysis else None,
                'structure': analysis.get('structure') if analysis else None,
                'vocals': analysis.get('vocals') if analysis else None,
                'drums': analysis.get('drums') if analysis else None,
                # MCP 增强字段
                'audio_quality_kbps': int(ai_data.get('format', {}).get('bitrate', 0)/1000) if ai_data else 0,
                'sample_rate': ai_data.get('format', {}).get('sampleRate') if ai_data else 0,
                # V6.4新增：音频特征深度匹配字段
                'brightness': analysis.get('brightness') if analysis else 0.5,  # 音色明亮度
                'kick_drum_power': analysis.get('kick_drum_power') if analysis else 0.5,  # 底鼓力度
                'sub_bass_level': analysis.get('sub_bass_level') if analysis else 0.5,  # 低音能量
                'dynamic_range_db': analysis.get('dynamic_range_db') if analysis else 10,  # 动态范围
                'valence': analysis.get('valence') if analysis else 0.5,  # 情感效价
                'arousal': analysis.get('arousal') if analysis else 0.5,  # 情感唤醒度
                # V6.4新增：更多深度匹配字段
                'phrase_length': analysis.get('phrase_length') if analysis else 16,  # 乐句长度
                'intro_vocal_ratio': analysis.get('intro_vocal_ratio') if analysis else 0.5,  # 前奏人声比例
                'outro_vocal_ratio': analysis.get('outro_vocal_ratio') if analysis else 0.5,  # 尾奏人声比例
                'busy_score': analysis.get('busy_score') if analysis else 0.5,  # 编曲繁忙度
                'tonal_balance_low': analysis.get('tonal_balance_low') if analysis else 0.5,  # 低频占比
                'tonal_balance_mid': analysis.get('tonal_balance_mid') if analysis else 0.3,  # 中频占比
                'tonal_balance_high': analysis.get('tonal_balance_high') if analysis else 0.1,  # 高频占比
                'hook_strength': analysis.get('hook_strength') if analysis else 0.5,  # Hook强度
                'tags': analysis.get('tags', []) if analysis else [],  # 【V4.0新增】多维智能标签
                'semantic_tags': list(stags) if 'stags' in locals() else [], # V6.0
                'time_signature': analysis.get('time_signature', '4/4') if analysis else '4/4', # V6.2
                'swing_dna': analysis.get('swing_dna', 0.0) if analysis else 0.0, # V6.2
                'spectral_bands': analysis.get('spectral_bands', {}) if analysis else {}, # V6.2
            }

            # 【V5.3 P1】注入 Rekordbox PSSI (Intensity)
            if PHRASE_READER_AVAILABLE and track_dict.get('content_uuid'):
                try:
                    pssi_phrases = PHRASE_READER.get_phrases(track_dict['content_uuid'], bpm=track_dict['bpm'])
                    if pssi_phrases:
                        # 提取前 2 个段落和后 2 个段落的平均强度
                        # 这样做是为了捕捉 Intro 的起步强度和 Outro 的收尾强度
                        intro_ints = [p['intensity'] for p in pssi_phrases[:2] if p.get('intensity') is not None]
                        outro_ints = [p['intensity'] for p in pssi_phrases[-2:] if p.get('intensity') is not None]
                        
                        track_dict['pssi_intensity_intro'] = sum(intro_ints) / len(intro_ints) if intro_ints else 3.0
                        track_dict['pssi_intensity_outro'] = sum(outro_ints) / len(outro_ints) if outro_ints else 3.0
                        track_dict['pssi_data_available'] = True
                except Exception as pssi_err:
                    print(f"Warning: Failed to inject PSSI data: {pssi_err}")
            
            # 【最强大脑：系统串联】生成专业量化 HotCues
            pro_hotcues = {}
            if HOTCUE_GENERATOR_ENABLED and analysis and file_path:
                try:
                    # 组装专家建议点（基于 Sorter 和结构分析的混合决策）
                    target_points = {
                        'mix_in': track_dict['mix_in_point'],
                        'mix_out': track_dict['mix_out_point']
                    }
                    # 如果有 B 点（手动或分析得出），同步传递以辅助生成 B 点标点
                    if track_dict.get('hotcue_B'):
                        target_points['transition_in'] = track_dict['hotcue_B']
                        
                    raw_pro = generate_hotcues(
                        file_path, 
                        bpm=track_dict['bpm'], 
                        duration=track_dict['duration'], 
                        structure=analysis,
                        content_uuid=track_dict.get('content_uuid'),
                        content_id=track_dict.get('id'),
                        custom_mix_points=target_points,
                        track_tags=track_dict.get('track_tags', {})
                    )
                    # 确保提取 hotcues 子字典，保留 PhraseLabel
                    pro_hotcues = raw_pro.get('hotcues', {})
                except Exception as e:
                    print(f"Warning: Pro Hotcue generation failed: {e}")

            track_dict['pro_hotcues'] = pro_hotcues
            
            # 【DEBUG】确认返回
            # print(f"DEBUG: Track {idx} 已准备好: {track_dict['title']}")
            
            return (idx, track_dict, is_cached, (analysis is not None and not is_cached))
        
        # 结果聚合优化
        def collect_results(results_list, idx, track_dict, is_cached, was_analyzed):
            if track_dict:
                results_list.append((idx, track_dict))
                return True
            return False
        
        # 使用多线程并行分析（限制线程数避免过载）
        try:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            max_workers = min(4, len(tracks_raw))  # 最多4个线程
            
            track_results = []
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(analyze_single_track, (idx, track)): (idx, track) 
                          for idx, track in enumerate(tracks_raw, 1)}
                
                completed = 0
                for future in as_completed(futures):
                    completed += 1
                    try:
                        res = future.result()
                        if res and len(res) == 4:
                            idx, track_dict, is_cached, was_analyzed = res
                            if track_dict:
                                track_results.append((idx, track_dict))
                                if is_cached: cached_count += 1
                                if was_analyzed:
                                    analyzed_count += 1
                                    cache_updated = True
                            else:
                                pass # 已打印过滤原因
                        else:
                            print(f"DEBUG: Future {completed} 返回了异常格式: {res}")
                        
                        # 显示进度
                        if completed % 5 == 0 or completed == len(tracks_raw):
                            elapsed = (datetime.now() - start_time).total_seconds()
                            if completed > 0:
                                avg_time = elapsed / completed
                                remaining = (len(tracks_raw) - completed) * avg_time
                                progress_pct = (completed / len(tracks_raw)) * 100
                                try:
                                    print(f"[进度] {completed}/{len(tracks_raw)} ({progress_pct:.1f}%) - 已用时间: {int(elapsed/60)}分{int(elapsed%60)}秒 - 预计剩余: {int(remaining/60)}分{int(remaining%60)}秒")
                                    print(f"  缓存: {cached_count}首 | 新分析: {analyzed_count}首")
                                except:
                                    print(f"[Progress] {completed}/{len(tracks_raw)} ({progress_pct:.1f}%)")
                    except Exception as e:
                        try:
                            print(f"分析失败: {e}")
                        except:
                            pass
            
            # 按原始顺序排序
            track_results.sort(key=lambda x: x[0])
            tracks = [tr[1] for tr in track_results]
            
        except ImportError:
            # 如果concurrent.futures不可用，回退到串行分析
            for idx, track in enumerate(tracks_raw, 1):
                file_path = track.file_path if hasattr(track, 'file_path') else None
                
                if not file_path or not os.path.exists(file_path):
                    try:
                        path_query = text("SELECT Path FROM djmdContent WHERE ID = :content_id")
                        path_result = pyrekordbox_db.session.execute(
                            path_query, {"content_id": track.id}
                        ).fetchone()
                        if path_result and path_result[0]:
                            file_path = path_result[0]
                            if not os.path.exists(file_path):
                                potential_paths = [
                                    os.path.join(r"D:\song", os.path.basename(file_path)),
                                    file_path,
                                ]
                                for pp in potential_paths:
                                    if os.path.exists(pp):
                                        file_path = pp
                                        break
                    except:
                        pass
                
                if not file_path or not os.path.exists(file_path):
                    # print(f"DEBUG: 跳过文件不存在: {file_path}")
                    continue
                
                # 尝试从缓存获取
                db_bpm = track.bpm if hasattr(track, 'bpm') else None
                cached_analysis = get_cached_analysis(file_path, cache)
                is_cached = cached_analysis is not None
                
                if cached_analysis:
                    # 使用缓存结果
                    analysis = cached_analysis
                    cached_count += 1
                else:
                    # 需要重新分析
                    analysis = deep_analyze_track(file_path, db_bpm)
                    if analysis:
                        cache_analysis(file_path, analysis, cache)
                        cache_updated = True
                        analyzed_count += 1
                
                # 优先使用检测到的调性，如果没有则使用数据库中的调性
                detected_key = analysis.get('key') if analysis else None
                db_key = track.key or ""
                final_key = detected_key if detected_key else (db_key if db_key else "未知")
                
                track_dict = {
                    'id': track.id,
                    'title': track.title or "",
                    'artist': track.artist or "",
                    'file_path': file_path,
                    'bpm': analysis.get('bpm') if analysis else (db_bpm or 120),
                    'key': final_key,
                    'energy': analysis.get('energy') if analysis else 50,
                    'duration': analysis.get('duration') if analysis else 180,
                    'mix_in_point': analysis.get('mix_in_point') if analysis else None,
                    'mix_out_point': analysis.get('mix_out_point') if analysis else None,
                    'genre': analysis.get('genre') if analysis else None,
                    'structure': analysis.get('structure') if analysis else None,  # 歌曲结构信息
                    'vocals': analysis.get('vocals') if analysis else None,  # 人声检测结果
                    'drums': analysis.get('drums') if analysis else None,  # 鼓点检测结果
                    # V6.4新增：音频特征深度匹配字段
                    'brightness': analysis.get('brightness') if analysis else 0.5,  # 音色明亮度
                    'kick_drum_power': analysis.get('kick_drum_power') if analysis else 0.5,  # 底鼓力度
                    'sub_bass_level': analysis.get('sub_bass_level') if analysis else 0.5,  # 低音能量
                    'dynamic_range_db': analysis.get('dynamic_range_db') if analysis else 10,  # 动态范围
                    'valence': analysis.get('valence') if analysis else 0.5,  # 情感效价
                    'arousal': analysis.get('arousal') if analysis else 0.5,  # 情感唤醒度
                    # V6.4新增：更多深度匹配字段
                    'phrase_length': analysis.get('phrase_length') if analysis else 16,  # 乐句长度
                    'intro_vocal_ratio': analysis.get('intro_vocal_ratio') if analysis else 0.5,  # 前奏人声比例
                    'outro_vocal_ratio': analysis.get('outro_vocal_ratio') if analysis else 0.5,  # 尾奏人声比例
                    'busy_score': analysis.get('busy_score') if analysis else 0.5,  # 编曲繁忙度
                    'tonal_balance_low': analysis.get('tonal_balance_low') if analysis else 0.5,  # 低频占比
                    'tonal_balance_mid': analysis.get('tonal_balance_mid') if analysis else 0.3,  # 中频占比
                    'tonal_balance_high': analysis.get('tonal_balance_high') if analysis else 0.1,  # 高频占比
                    'hook_strength': analysis.get('hook_strength') if analysis else 0.5,  # Hook强度
                    # V4.1新增：乐句长度（小节数）感知
                    'intro_bars': round((analysis.get('intro_end_time') or analysis.get('mix_in_point') or 0) * (analysis.get('bpm') or 120) / 240) if analysis else 8,
                    'outro_bars': round(((analysis.get('duration') or 180) - (analysis.get('outro_start_time') or analysis.get('mix_out_point') or 180)) * (analysis.get('bpm') or 120) / 240) if analysis else 8,
                    'first_drop_time': analysis.get('first_drop_time') if analysis else None,
                    # V6.1 Pro-Acoustics: 响度与律动偏移
                    'lufs_db': analysis.get('loudness_lufs') if analysis else -10.0,
                    'swing_dna': analysis.get('swing_dna', 0.0) if analysis else 0.0, # V6.2
                    'time_signature': analysis.get('time_signature', '4/4') if analysis else '4/4', # V6.2
                    'spectral_bands': analysis.get('spectral_bands', {}) if analysis else {}, # V6.2
                }
                tracks.append(track_dict)
                
                # 显示进度（每首歌曲或每10首）
                if idx == 1 or idx % 10 == 0 or idx == len(tracks_raw):
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if idx > 0:
                        avg_time_per_track = elapsed / idx
                        remaining = (len(tracks_raw) - idx) * avg_time_per_track
                        progress_pct = (idx / len(tracks_raw)) * 100
                        
                        try:
                            print(f"[进度] {idx}/{len(tracks_raw)} ({progress_pct:.1f}%) - 已用时间: {int(elapsed/60)}分{int(elapsed%60)}秒 - 预计剩余: {int(remaining/60)}分{int(remaining%60)}秒")
                            print(f"  缓存: {cached_count}首 | 新分析: {analyzed_count}首")
                            if idx < len(tracks_raw):
                                status = "[缓存]" if is_cached else "[分析中]"
                                print(f"  {status} {track.title[:50] if track.title else 'Unknown'}...")
                        except:
                            print(f"[Progress] {idx}/{len(tracks_raw)} ({progress_pct:.1f}%) - Elapsed: {int(elapsed/60)}m{int(elapsed%60)}s - Remaining: {int(remaining/60)}m{int(remaining%60)}s")
                            print(f"  Cached: {cached_count} | New: {analyzed_count}")
        
        # 保存缓存
        if cache_updated:
            save_cache(cache)
            try:
                print(f"\n[缓存] 已保存 {analyzed_count} 首新歌曲的分析结果到缓存")
            except:
                print(f"\n[Cache] Saved {analyzed_count} new analysis results")
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        # 【修复】去重：按 ContentID、文件路径和歌曲标题去重
        seen_ids = set()
        seen_paths = set()
        seen_titles = set()
        unique_tracks = []
        for track in tracks:
            tid = track.get('id')
            path = track.get('file_path', '').lower().replace('\\', '/')
            # 用标题+艺术家作为备选标识（处理同一首歌不同路径的情况）
            title_key = f"{track.get('artist', '')}_{track.get('title', '')}".lower().strip()
            
            is_duplicate = False
            if tid and tid in seen_ids:
                is_duplicate = True
            elif path and path in seen_paths:
                is_duplicate = True
            elif title_key and title_key in seen_titles and title_key != 'unknown_unknown' and title_key != '_':
                is_duplicate = True
            
            if not is_duplicate:
                if tid: seen_ids.add(tid)
                if path: seen_paths.add(path)
                if title_key and title_key != 'unknown_unknown' and title_key != '_':
                    seen_titles.add(title_key)
                unique_tracks.append(track)
            else:
                pass # 过滤重复
        
        if len(unique_tracks) < len(tracks):
            print(f"[去重] 移除 {len(tracks) - len(unique_tracks)} 首原始重复记录 (保留 {len(unique_tracks)} 首)")
        tracks = unique_tracks

        # 【V5.1 HOTFIX】Data Sanitization against NoneType crashes
        # 针对 Remix 歌曲可能存在的元数据缺失进行防御性填充
        for t in tracks:
            if t.get('bpm') is None: t['bpm'] = 120.0
            if t.get('energy') is None: t['energy'] = 50.0
            
            # Key 特殊处理：可能是 DjmdKey 对象或 None
            raw_key = t.get('key')
            if raw_key is None:
                t['key'] = '1A'
            elif hasattr(raw_key, 'Name'):  # Handle DjmdKey object
                t['key'] = raw_key.Name if raw_key.Name else '1A'
            elif not isinstance(raw_key, str):
                t['key'] = str(raw_key) if raw_key else '1A'
            # else: it's already a valid string
            
            # Ensure BPM is float
            try: t['bpm'] = float(t['bpm'])
            except: t['bpm'] = 120.0
            # Ensure Energy is float
            try: t['energy'] = float(t['energy'])
            except: t['energy'] = 50.0

        
        try:
            print("=" * 60)
            try:
                print(f"[完成] 分析完成！成功分析 {len(tracks)} 首歌曲")
            except UnicodeEncodeError:
                print(f"[完成] Analysis complete! Successfully analyzed {len(tracks)} tracks")
            try:
                print(f"   总耗时: {int(total_time/60)}分{int(total_time%60)}秒")
            except UnicodeEncodeError:
                print(f"   Total time: {int(total_time/60)}m{int(total_time%60)}s")
            try:
                print(f"\n开始排序和生成Set...")
            except UnicodeEncodeError:
                print(f"\nStarting sorting and set generation...")
            print("=" * 60)
        except:
            print("=" * 60)
            print(f"[完成] Analysis complete! Successfully analyzed {len(tracks)} tracks")
            print(f"   Total time: {int(total_time/60)}m{int(total_time%60)}s")
            print(f"\nStarting sorting and set generation...")
            print("=" * 60)
        
        # ========== 桥接模式：从曲库补充同风格歌曲 ==========
        if enable_bridge:
            try:
                from genre_compatibility import (
                    detect_genre_from_filename,
                    get_compatible_genres,
                    GENRE_FAMILIES,
                    CROSS_FAMILY_COMPATIBILITY
                )
                
                # 只有电子乐风格才启用桥接
                BRIDGEABLE_FAMILIES = ['house_family', 'techno_family', 'breaks_family', 'latin_family', 'trance_family']
                bridgeable_styles = []
                for family in BRIDGEABLE_FAMILIES:
                    bridgeable_styles.extend(GENRE_FAMILIES.get(family, []))
                bridgeable_styles.extend(['house', 'electronic', 'techno'])
                
                # 检测播放列表主导风格
                style_counts = {}
                for track in tracks:
                    style = detect_genre_from_filename(Path(track.get('file_path', '')).stem)
                    style_counts[style] = style_counts.get(style, 0) + 1
                
                dominant_style = max(style_counts.items(), key=lambda x: x[1])[0] if style_counts else 'electronic'
                
                # 只有电子乐风格才桥接
                if dominant_style in bridgeable_styles or dominant_style in ['house', 'electronic', 'techno']:
                    print(f"\n[桥接模式] 主导风格: {dominant_style}")
                    
                    # 加载曲库缓存
                    cache_file = Path("song_analysis_cache.json")
                    if cache_file.exists():
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            all_cache = json.load(f)
                        
                        # 获取兼容风格
                        compatible_styles = get_compatible_genres(dominant_style)
                        compatible_styles.append(dominant_style)
                        compatible_styles.extend(['house', 'electronic'])
                        compatible_styles = list(set(compatible_styles))
                        
                        # 已有歌曲的路径集合
                        existing_paths = {t.get('file_path', '').lower().replace('\\', '/') for t in tracks}
                        
                        # 从缓存中筛选兼容风格的歌曲
                        bridge_candidates = []
                        for hash_key, data in all_cache.items():
                            file_path = data.get('file_path', '')
                            if file_path.lower().replace('\\', '/') in existing_paths:
                                continue  # 跳过已有歌曲
                            analysis = data.get('analysis', {})
                            if not analysis or 'bpm' not in analysis:
                                continue  # 跳过无分析数据的条目
                                
                            style = detect_genre_from_filename(Path(file_path).stem)
                            if style in compatible_styles:
                                bridge_candidates.append({
                                    'file_path': file_path,
                                    'title': Path(file_path).stem,
                                    'artist': 'Unknown',
                                    'bpm': analysis.get('bpm', 0),
                                    'key': analysis.get('key', ''),
                                    'energy': analysis.get('energy', 50),
                                    'duration': analysis.get('duration', 180),
                                    'is_bridge': True,  # 标记为桥接歌曲
                                    'bridge_style': style
                                })
                        
                        print(f"[桥接模式] 找到 {len(bridge_candidates)} 首兼容风格歌曲")
                        
                        # 将桥接歌曲添加到候选池（播放列表歌曲优先）
                        if bridge_candidates:
                            import random
                            random.shuffle(bridge_candidates)
                            # 计算需要补充的数量
                            # 如果播放列表歌曲不足一个完整Set，补充到1.2倍目标数量
                            if len(tracks) < songs_per_set:
                                max_bridge = int(songs_per_set * 1.2) - len(tracks)
                                tracks.extend(bridge_candidates[:max_bridge])
                                print(f"[桥接模式] 歌曲不足，补充 {min(max_bridge, len(bridge_candidates))} 首桥接歌曲")
                            else:
                                print(f"[桥接模式] 播放列表歌曲充足({len(tracks)}首)，无需桥接")
                else:
                    print(f"\n[桥接模式] 风格 {dominant_style} 不适合桥接，跳过")
            except Exception as e:
                print(f"[桥接模式] 错误: {e}")
        
        if is_boutique:
            print("\n[Boutique] 精品单体模式：跳过BPM自动分组，强制合并为单个精品Set")
            # 在精品模式下，我们不分组，直接把所有歌曲当成一条长轴
            # 但我们会先按BPM初排一下，给排序引擎一个好的起始点
            tracks.sort(key=lambda x: x.get('bpm', 0))
            bpm_groups = [tracks]
        else:
            try:
                print("\n[BPM分组] 正在按BPM自动分组...")
            except:
                print("\n[BPM Grouping] Auto-grouping by BPM...")
            
            bpm_groups = auto_group_by_bpm(tracks, max_bpm_range=25.0)
        
        try:
            print(f"[BPM分组] 自动分成 {len(bpm_groups)} 个BPM区间:")
            for i, group in enumerate(bpm_groups, 1):
                label = get_bpm_group_label(group)
                print(f"  - 区间{i}: {label} ({len(group)}首)")
        except:
            print(f"[BPM Grouping] Split into {len(bpm_groups)} BPM ranges")
        
        # 【Phase 8】获取分割配置
        split_cfg = DJ_RULES.get('split', {}) if DJ_RULES else {}
        target_minutes = split_cfg.get('target_duration_minutes', 90.0)
        min_s = split_cfg.get('min_songs', 20)
        max_s = split_cfg.get('max_songs', 60)
        
        # 对每个BPM组进行排序，生成Set
        sets = []
        set_idx = 0
        
        # [PRO UPGRADE] 精品模式探测：如果歌单很大且未显式指定 Master，自动提升为 Master 逻辑以实现全局最优切分
        # [PRO UPGRADE] 精品模式探测：如果开启了双模（Boutique + Live）或歌单很大，自动提升为 Master 逻辑
        is_dual_mode_requested = is_boutique and is_live
        if (is_dual_mode_requested or (is_boutique and any(len(g) > max_s for g in bpm_groups))) and not is_master:
            try:
                print(f"[Boutique] 检测到大型歌单，自动升级为 Master 总线算法以确保全局最优切分...")
            except:
                pass
            is_master = True

        for group_idx, bpm_group in enumerate(bpm_groups):
            if is_master:
                # [Master模式] 核心逻辑：全局排序，后续智能切分
                print(f"[Master] 正在进行全局连贯排序 (共 {len(bpm_group)} 首)...")
                global_sorted_tracks, _, _ = enhanced_harmonic_sort(bpm_group, len(bpm_group), is_boutique=is_boutique)
                
                # 【Boutique 修正】精品模式下，不进行全量切分，而是只取前 30-45 首的最佳组合
                if is_boutique:
                    try:
                        print(f"[Boutique] 精品模式生效：正在从 {len(global_sorted_tracks)} 首候选曲中甄选最佳 Set (目标 30-45 首)...")
                    except:
                        print(f"[Boutique] Mode Active: Selecting best 30-45 tracks from {len(global_sorted_tracks)} candidates...")
                    
                    # 目标范围
                    min_target = 30
                    max_target = 45
                    
                    # 如果总数不足，就全要
                    if len(global_sorted_tracks) <= max_target:
                        print(f"   - 候选不足 {max_target} 首，保留全量 {len(global_sorted_tracks)} 首")
                        final_cut = global_sorted_tracks
                    else:
                        # 智能截断：在 30-45 之间寻找最佳 Outro 点
                        # 扫描区间 [30, 45] (索引 29 到 44)
                        best_cut_idx = max_target
                        max_tail_score = -9999
                        
                        scan_start = min(len(global_sorted_tracks), min_target)
                        scan_end = min(len(global_sorted_tracks), max_target + 1)
                        
                        for i in range(scan_start, scan_end):
                            # 检查切断点的"完结感" (比如是否进入了 Cool-down，或者 key 比较稳)
                            track = global_sorted_tracks[i-1] # 最后一首
                            score = 0
                            
                            # 优先选择 Cool-down 或 Intense 结束
                            phase = track.get('assigned_phase', '')
                            if phase == 'Cool-down': score += 20
                            elif phase == 'Intense': score += 10 # 强力收尾
                            
                            # 检查是否是"桥接曲" (不建议在桥接曲结束)
                            if track.get('is_bridge'): score -= 50
                            
                            if score > max_tail_score:
                                max_tail_score = score
                                best_cut_idx = i
                        
                        print(f"   - 智能截断：选定 {best_cut_idx} 首 (Score: {max_tail_score})")
                        final_cut = global_sorted_tracks[:best_cut_idx]
                    
                    # 【Dual Mode】将 Boutique Set 加入列表，并标记为特殊，但不退出循环
                    # 为了区分，我们在 tracks 列表的第一个元素的 metadata 里打个标，或者外部结构打标
                    # 这里简单的将其作为第一个 Set 加入
                    # 并在第一个 track 注入特殊标记，供 Report 识别
                    if final_cut:
                         final_cut[0]['is_boutique_start'] = True
                    sets.append(final_cut)
                    print(f"[Dual Mode] 已生成 Boutique Highlight Set ({len(final_cut)} tracks). 继续生成全量 Live Sets...")
                    # 以前的 break 被移除，允许继续执行下面的全量切分逻辑
                    # break

                # 开始智能切分 (普通 Live 模式)
                print(f"[Master] 正在寻找最佳切分点 (Pivots)...")
                current_ptr = 0
                while current_ptr < len(global_sorted_tracks):
                    chunk = []
                    dur = 0
                    
                    # 寻找目标长度
                    if is_boutique:
                        # [V6.1.3] 双模优化：凡是开启了精品精选，全量分段自动进入"大块模式" (每段 25-35 首)
                        # 避免产生过多细碎的 Part
                        target_s = max(25, min_s)
                        target_d = max(90 * 60, target_minutes * 60)
                    else:
                        target_s = min_s
                        target_d = target_minutes * 60
                    
                    # 预估歌曲数量
                    est_songs = 0
                    temp_dur = 0
                    for k in range(current_ptr, len(global_sorted_tracks)):
                        temp_dur += global_sorted_tracks[k].get('duration', 180)
                        est_songs += 1
                        if temp_dur >= target_d and est_songs >= min_s:
                            break
                    
                    # 如果剩余歌曲太少，直接打包
                    if len(global_sorted_tracks) - (current_ptr + est_songs) < min_s // 2:
                        est_songs = len(global_sorted_tracks) - current_ptr
                    
                    # 在 est_songs 附近寻找最佳切分点 (窗口 +/- 5)
                    pivot_idx = current_ptr + est_songs
                    if pivot_idx < len(global_sorted_tracks):
                        window_start = max(current_ptr + min_s, pivot_idx - 5)
                        window_end = min(len(global_sorted_tracks) - min_s // 2, pivot_idx + 5)
                        
                        best_p = pivot_idx
                        max_p_score = -9999
                        for w in range(window_start, window_end):
                            # _transition_score 记录的是当前首歌与前一首歌的兼容度
                            # 我们希望切分点之后的 第一首歌 与 切分点之前的 最后一首歌 兼容度最高
                            s_val = global_sorted_tracks[w].get('_transition_score', 0)
                            if s_val > max_p_score:
                                max_p_score = s_val
                                best_p = w
                        pivot_idx = best_p
                    else:
                        pivot_idx = len(global_sorted_tracks)
                    
                    sets.append(global_sorted_tracks[current_ptr:pivot_idx])
                    current_ptr = pivot_idx
            else:
                # [普通模式] 原有的逐个切分排序逻辑
                current_sub_group = []
                current_duration = 0
                
                for i, track in enumerate(bpm_group):
                    track_dur = track.get('duration', 180)
                    current_sub_group.append(track)
                    current_duration += track_dur
                    
                    is_last = (i == len(bpm_group) - 1)
                    reached_duration = (current_duration >= target_minutes * 60)
                    reached_max_songs = (len(current_sub_group) >= max_s)
                    
                    # [PRO FIX] 如果开启了精品模式但没开Master，也要执行智能长度保护，避免生成极短Set
                    # 但是精品模式更推荐开启 is_master = True 来利用全局寻找 Pivot 的能力
                    if (not is_boutique) and ((reached_duration and len(current_sub_group) >= min_s) or reached_max_songs) or is_last:
                        # 长度保护：如果剩余歌曲不够一个完整的Set，则合并到当前Set（除非是最后一个）
                        remaining = len(bpm_group) - (i + 1)
                        if (not is_last) and remaining > 0 and remaining < min_s:
                            continue
                        
                        set_idx += 1
                        label = "精品 Set (Boutique Mode)" if is_boutique else get_bpm_group_label(current_sub_group)
                        try:
                            print(f"正在排序 Set {set_idx} - {label} ({len(current_sub_group)} 首歌曲, 时长: {current_duration/60:.1f}min)...")
                        except:
                            pass
                            
                        sorted_tracks, _, _ = enhanced_harmonic_sort(current_sub_group, len(current_sub_group), is_boutique=is_boutique)
                        sets.append(sorted_tracks)
                        
                        # 重置计数，准备下一个子组
                        current_sub_group = []
                        current_duration = 0
            
            if is_boutique:
                break
        
        # ========== BPM平滑处理：确保每个Set内BPM序列平滑 ==========
        try:
            print("\n[BPM平滑] 正在优化每个Set的BPM序列...")
        except:
            print("\n[BPM Smoothing] Optimizing BPM sequence for each set...")
        
        smoothed_sets = []
        for i, set_tracks in enumerate(sets):
            smoothed = smooth_bpm_sequence(set_tracks)
            smoothed_sets.append(smoothed)
            
            # 计算平滑前后的BPM跳跃次数
            def count_bpm_jumps(tracks, threshold=15):
                jumps = 0
                for j in range(1, len(tracks)):
                    bpm_diff = abs(tracks[j].get('bpm', 0) - tracks[j-1].get('bpm', 0))
                    if bpm_diff > threshold:
                        jumps += 1
                return jumps
            
            before_jumps = count_bpm_jumps(set_tracks)
            after_jumps = count_bpm_jumps(smoothed)
            
            if before_jumps > after_jumps:
                try:
                    print(f"  Set {i+1}: BPM跳跃 {before_jumps} -> {after_jumps} (优化了 {before_jumps - after_jumps} 处)")
                except:
                    print(f"  Set {i+1}: BPM jumps {before_jumps} -> {after_jumps}")
        
        sets = smoothed_sets
        
        # ========== Phase 3: 全局退火优化 (Simulated Annealing) ==========
        if len(sets) > 0:
            try:
                print(f"\n[进化启动] 正在进行全局退火优化 (Phase 3)...")
            except:
                print(f"\n[Evolution] Starting Global Optimization (Phase 3)...")
                
            opt_config = {
                'max_bpm_jump': 8.0,
                'min_key_score': 60.0,
                'active_profile': ACTIVE_PROFILE
            }
            improved_count = optimize_global_sets(sets, opt_config, progress_logger)
            
            if improved_count > 0:
                try:
                    print(f"  [完成] 已成功优化 {improved_count} 个 Set 的全局流向")
                except:
                    print(f"  [Done] Optimized global flow for {improved_count} sets")
            else:
                try:
                    print(f"  [完成] 当前序列已是全局最优或未发现更好排列")
                except:
                    print(f"  [Done] Current sequence is globally optimal")
        
        # ========== 【V6.4新增】自动桥接曲插入：解决BPM跨度过大问题 ==========
        bridge_insertions = []  # 记录所有桥接曲插入信息
        
        # 检查是否启用桥接曲功能（华语/K-Pop/J-Pop自动禁用）
        skip_bridge_track = not enable_bridge_track
        if skip_bridge_track:
            print("\n[桥接曲] 桥接曲功能已禁用（亚洲流行风格）")
        
        try:
            if not skip_bridge_track:
                print("\n[桥接曲] 正在检测BPM跨度过大的位置...")
            
            # 加载缓存以查找桥接曲候选
            cache_file = Path("song_analysis_cache.json")
            all_cache = {}
            if cache_file.exists() and not skip_bridge_track:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    all_cache = json.load(f)
            
            # 获取已使用的歌曲路径（避免重复）
            used_paths = set()
            for set_tracks in sets:
                for track in set_tracks:
                    used_paths.add(track.get('file_path', ''))
            
            # 遍历每个Set，检测并插入桥接曲
            new_sets = []
            for set_idx, set_tracks in enumerate(sets):
                new_set = []
                for i, track in enumerate(set_tracks):
                    new_set.append(track)
                    
                    # 如果禁用桥接曲，跳过检查
                    if skip_bridge_track:
                        continue
                    
                    # 检查与下一首的BPM跨度
                    if i < len(set_tracks) - 1:
                        curr_bpm = track.get('bpm', 0)
                        next_track = set_tracks[i + 1]
                        next_bpm = next_track.get('bpm', 0)
                        
                        if curr_bpm and next_bpm:
                            bpm_diff = abs(curr_bpm - next_bpm)
                            
                            # BPM跨度检测阈值：精品模式8，普通模式15
                            bridge_trigger = 8.0 if is_boutique else 15.0
                            if bpm_diff > bridge_trigger:
                                # 计算理想的桥接BPM（两者中间值）
                                target_bpm = (curr_bpm + next_bpm) / 2
                                curr_key = track.get('key', '')
                                next_key = next_track.get('key', '')
                                
                                # 从缓存中查找最佳桥接曲
                                best_bridge = None
                                best_score = -999
                                best_reasons = []
                                
                                # 导入风格兼容性检查
                                try:
                                    from genre_compatibility import are_genres_compatible, detect_genre_from_filename, get_genre_family
                                    has_genre_check = True
                                except ImportError:
                                    has_genre_check = False
                                
                                # 获取当前歌曲和下一首歌曲的风格（优先文件名检测）
                                curr_genre = detect_genre_from_filename(track.get('file_path', '')) or track.get('genre', '') if has_genre_check else ''
                                next_genre = detect_genre_from_filename(next_track.get('file_path', '')) or next_track.get('genre', '') if has_genre_check else ''
                                
                                for hash_key, data in all_cache.items():
                                    file_path = data.get('file_path', '')
                                    
                                    # 跳过已使用的歌曲
                                    if file_path in used_paths:
                                        continue
                                    
                                    analysis = data.get('analysis', {})
                                    bridge_bpm = analysis.get('bpm', 0)
                                    bridge_key = analysis.get('key', '')
                                    
                                    if not bridge_bpm:
                                        continue
                                    
                                    # 【最重要】0. 风格兼容性检查 - 不兼容直接跳过
                                    if has_genre_check:
                                        # 优先使用文件名检测风格（更准确），其次用缓存中的genre
                                        bridge_genre = detect_genre_from_filename(file_path) or analysis.get('genre', '')
                                        
                                        # 【Phase 9】Vibe-Aware Bridging: 严格限制电子乐与流行乐之间的桥接
                                        # 如果两头都是电子乐家族，桥接曲也必须是电子乐家族
                                        electronic_families = ['house_family', 'techno_family', 'bass_family', 'trance_family', 'breaks_family']
                                        asian_families = ['asian_pop_family']
                                        
                                        curr_fam = get_genre_family(curr_genre)
                                        next_fam = get_genre_family(next_genre)
                                        bridge_fam = get_genre_family(bridge_genre)
                                        
                                        # 规则：如果当前是电子乐，下一首也是电子乐，桥接曲绝对不能是 Asian Pop 或 纯Pop
                                        if curr_fam in electronic_families and next_fam in electronic_families:
                                            if bridge_fam in asian_families or bridge_fam == 'pop_family':
                                                continue # 风格违和，跳过
                                                
                                        # 反之：如果当前是 Asian Pop，桥接曲也应该优先保持在 Pop 范畴
                                        if curr_fam in asian_families:
                                            if bridge_fam in electronic_families:
                                                continue # 风格违和，跳过

                                        # 检查桥接曲与前后两首歌的风格兼容性
                                        if curr_genre and bridge_genre:
                                            compat_result_curr = are_genres_compatible(curr_genre, bridge_genre)
                                            compatible_with_curr = compat_result_curr[0]
                                        else:
                                            compatible_with_curr = True
                                        
                                        if bridge_genre and next_genre:
                                            compat_result_next = are_genres_compatible(bridge_genre, next_genre)
                                            compatible_with_next = compat_result_next[0]
                                        else:
                                            compatible_with_next = True
                                        
                                        # 如果与任一首歌风格不兼容，跳过
                                        if not compatible_with_curr or not compatible_with_next:
                                            continue
                                    
                                    # 计算桥接曲评分
                                    score = 0
                                    reasons = []
                                    
                                    # 风格兼容加分
                                    if has_genre_check and bridge_genre:
                                        reasons.append(f"风格 {bridge_genre} 兼容")
                                        score += 20  # 风格兼容基础分
                                    
                                    # 1. BPM匹配度 - 优先选择BPM接近中间值的歌曲
                                    bpm_to_curr = abs(bridge_bpm - curr_bpm)
                                    bpm_to_next = abs(bridge_bpm - next_bpm)
                                    max_single_gap = max(bpm_to_curr, bpm_to_next)  # 最大单边跨度
                                    
                                    # 桥接曲的BPM应该在两首歌之间，且尽量接近中间值
                                    if min(curr_bpm, next_bpm) <= bridge_bpm <= max(curr_bpm, next_bpm):
                                        # 基础分50，根据与中间值的距离调整
                                        mid_bpm = (curr_bpm + next_bpm) / 2
                                        distance_to_mid = abs(bridge_bpm - mid_bpm)
                                        # 距离中间值越近，分数越高（最高70分）
                                        mid_bonus = max(0, 20 - distance_to_mid)  # 距离0得20分，距离20得0分
                                        score += 50 + mid_bonus
                                        
                                        # 检查是否真正解决了问题（两边跨度都<=12）
                                        if max_single_gap <= 12:
                                            score += 20
                                            reasons.append(f"BPM {bridge_bpm:.1f} 完美桥接（两边跨度都<=12）")
                                        elif max_single_gap <= 15:
                                            score += 10
                                            reasons.append(f"BPM {bridge_bpm:.1f} 在 {curr_bpm:.1f}-{next_bpm:.1f} 之间")
                                        else:
                                            reasons.append(f"BPM {bridge_bpm:.1f} 在范围内但跨度仍较大")
                                    elif bpm_to_curr <= 8 and bpm_to_next <= 8:
                                        score += 30
                                        reasons.append(f"BPM {bridge_bpm:.1f} 接近两首歌")
                                    elif bpm_to_curr <= 12 or bpm_to_next <= 12:
                                        score += 10
                                    else:
                                        continue  # BPM差距太大，跳过
                                    
                                    # 2. 调性兼容性
                                    if bridge_key and curr_key and next_key:
                                        key_score_curr = get_key_compatibility_flexible(curr_key, bridge_key)
                                        key_score_next = get_key_compatibility_flexible(bridge_key, next_key)
                                        avg_key_score = (key_score_curr + key_score_next) / 2
                                        
                                        if avg_key_score >= 80:
                                            score += 30
                                            reasons.append(f"调性 {bridge_key} 与两首歌都和谐")
                                        elif avg_key_score >= 60:
                                            score += 15
                                            reasons.append(f"调性 {bridge_key} 兼容")
                                    
                                    # 3. 能量匹配
                                    curr_energy = track.get('energy', 50)
                                    next_energy = next_track.get('energy', 50)
                                    bridge_energy = analysis.get('energy', 50)
                                    
                                    if min(curr_energy, next_energy) <= bridge_energy <= max(curr_energy, next_energy):
                                        score += 10
                                        reasons.append("能量平滑过渡")
                                    
                                    # 更新最佳桥接曲
                                    if score > best_score:
                                        best_score = score
                                        # 【V7.1 核心强化】透传全量元数据，确保桥接曲也能 PQTZ 对齐
                                        best_bridge = {
                                            'id': data.get('id') or data.get('ContentID'),
                                            'content_uuid': data.get('content_uuid') or data.get('UUID'),
                                            'file_path': file_path,
                                            'title': Path(file_path).stem,
                                            'artist': data.get('artist') or 'Unknown',
                                            'bpm': bridge_bpm,
                                            'key': bridge_key,
                                            'energy': bridge_energy,
                                            'duration': analysis.get('duration', 180),
                                            'structure': analysis.get('structure') or analysis, # 直传结构
                                            'vocals': analysis.get('vocals'),
                                            'is_bridge': True,
                                            'bridge_reason': ' | '.join(reasons)
                                        }
                                        best_reasons = reasons
                                
                                # 如果找到合适的桥接曲，插入
                                # 精品模式要求更严格的分数以确保高质量桥接
                                min_bridge_score = 60 if is_boutique else 40
                                if best_bridge and best_score >= min_bridge_score:
                                    new_set.append(best_bridge)
                                    used_paths.add(best_bridge['file_path'])
                                    
                                    bridge_info = {
                                        'set_idx': set_idx + 1,
                                        'position': i + 1,
                                        'prev_track': track.get('title', 'Unknown')[:30],
                                        'next_track': next_track.get('title', 'Unknown')[:30],
                                        'bridge_track': best_bridge['title'][:30],
                                        'prev_bpm': curr_bpm,
                                        'next_bpm': next_bpm,
                                        'bridge_bpm': best_bridge['bpm'],
                                        'original_gap': bpm_diff,
                                        'new_gap_1': abs(curr_bpm - best_bridge['bpm']),
                                        'new_gap_2': abs(best_bridge['bpm'] - next_bpm),
                                        'reasons': best_reasons
                                    }
                                    bridge_insertions.append(bridge_info)
                                    
                                    print(f"  [Set {set_idx + 1}] 插入桥接曲: {best_bridge['title'][:40]}")
                                    print(f"    原BPM跨度: {bpm_diff:.1f} -> 新跨度: {bridge_info['new_gap_1']:.1f} + {bridge_info['new_gap_2']:.1f}")
                                    print(f"    原因: {best_bridge['bridge_reason']}")
                
                new_sets.append(new_set)
            
            sets = new_sets
            
            # ========== 【V9.2 Protocol】全局去重与最后验证 ==========
            final_unique_sets = []
            global_seen_paths = set()
            duplicate_count = 0
            
            for s_idx, s_tracks in enumerate(sets):
                # [Dual Mode Fix] Set 0 (无论是 Boutique 还是 Live Part 1) 永远拥有豁免权
                # 且如果是 Boutique，它不应该消耗后续 Live Set 的配额，所以不加入 seen_paths
                if s_idx == 0:
                    final_unique_sets.append(s_tracks)
                    continue

                unique_s_tracks = []
                for t in s_tracks:
                    p = t.get('file_path')
                    if p and p in global_seen_paths:
                        duplicate_count += 1
                        continue
                    unique_s_tracks.append(t)
                    if p: global_seen_paths.add(p)
                final_unique_sets.append(unique_s_tracks)
            
            if duplicate_count > 0:
                print(f"[去重] 全局过滤掉 {duplicate_count} 首在不同 Set 中重复出现的歌曲")
            sets = final_unique_sets
            
            if bridge_insertions:
                print(f"\n[桥接曲] 共插入 {len(bridge_insertions)} 首桥接曲")
            elif not skip_bridge_track:
                # 检查是否真的没有大跨度
                has_large_gap = False
                for set_tracks in sets:
                    for i in range(len(set_tracks) - 1):
                        b1 = set_tracks[i].get('bpm', 0)
                        b2 = set_tracks[i+1].get('bpm', 0)
                        if b1 and b2 and abs(b1 - b2) > (8.0 if is_boutique else 15.0):
                            has_large_gap = True
                            break
                    if has_large_gap: break
                
                if has_large_gap:
                    print("[桥接曲] 警告: 检测到大的BPM跨度，但在曲库中未发现满足条件的桥接候选。")
                else:
                    print("[桥接曲] 无需插入桥接曲（所有BPM跨度都在合理范围内）")
        except Exception as e:
            print(f"[桥接曲] 处理时出错: {e}")
        output_dir = Path(r"D:\生成的set")
        output_dir.mkdir(parents=True, exist_ok=True)
                # 确定显示名称
        try:
            playlist_display_name = target_playlist.name if hasattr(target_playlist, 'name') and target_playlist.name else playlist_name
        except:
            playlist_display_name = playlist_name
            
        # ========== [Phase 12.1] 【物理隔离与同步】专家级导出协议 ==========
        # 强制执行：物理复制 + 路径重导 + 装饰标识，确保 RB 100% 刷新标点
        try:
            # 【V9.1 专家级原子化重构】彻底杜绝分析失效与刷新异常
            processed_tracks_map = {} # 记录 original_path -> isolated_path 的映射

            def get_flattened_tracks(input_list):
                result = []
                for item in input_list:
                    if isinstance(item, list): result.extend(get_flattened_tracks(item))
                    elif isinstance(item, dict): result.append(item)
                return result

            # 1. 深度扁平化所有 Set
            sets = [get_flattened_tracks(s) if isinstance(s, list) else [s] for s in sets]

            print(f"\n[V9.1 系统重构] 正在执行全量物理隔离与标点对齐 (Total Isolation)...")
            isolated_audio_root = output_dir / "audio" / playlist_display_name
            isolated_audio_root.mkdir(parents=True, exist_ok=True)

            # 2. 全量预处理逻辑 (原子化循环)
            for set_idx, set_tracks in enumerate(sets):
                set_audio_dir = isolated_audio_root / f"Set_{set_idx + 1}"
                set_audio_dir.mkdir(parents=True, exist_ok=True)
                
                for track in set_tracks:
                    if not isinstance(track, dict): continue
                    
                    # A. 锁定指纹
                    original_file_path = track.get('original_path') or track['file_path']
                    if 'original_path' not in track: track['original_path'] = original_file_path
                    
                    # B. 标点探测 (始终基于原始路径，确保 100% 命中 DB)
                    if HOTCUE_GENERATOR_ENABLED and not track.get('pro_hotcues'):
                        vocal_regions = []
                        if track.get('vocals') and isinstance(track['vocals'], dict):
                            vocal_regions = track['vocals'].get('segments', [])
                            
                        # 计算连通性 (Link Data)
                        link_data = None
                        try:
                            t_idx = set_tracks.index(track)
                            if t_idx < len(set_tracks) - 1:
                                next_t = set_tracks[t_idx+1]
                                if isinstance(next_t, dict):
                                    ni_beats = 32
                                    if next_t.get('structure') and next_t['structure'].get('structure', {}).get('intro'):
                                        ir = next_t['structure']['structure']['intro']
                                        nb = next_t.get('bpm', 128)
                                        if nb > 0:
                                            ni_beats = 32 if int((ir[1]-ir[0])/(60.0/nb)) > 24 else 16
                                    link_data = {'next_title': next_t.get('title', 'Unknown'), 'next_intro_beats': ni_beats}
                        except: pass

                        hcs_res = generate_hotcues(
                            audio_file=original_file_path, 
                            bpm=track.get('bpm'),
                            duration=track.get('duration'),
                            structure=track.get('structure'), 
                            vocal_regions=vocal_regions,
                            content_id=track.get('id'),
                            content_uuid=track.get('content_uuid'),
                            link_data=link_data, 
                            custom_mix_points={'mix_in': track.get('mix_in_point'), 'mix_out': track.get('mix_out_point')},
                        )
                        # 保存完整结果 (含 memory_cues 和 anchor)
                        track['pro_hotcues'] = hcs_res
                        pro_hcs = hcs_res.get('hotcues', {})
                        track['anchor'] = hcs_res.get('anchor', 0.0)
                        
                        # 同步点位到主对象 (V9.2 专家监控)
                        if 'A' in pro_hcs:
                            old_val = track.get('mix_in_point')
                            new_val = pro_hcs['A']['Start']
                            track['mix_in_point'] = new_val
                            if old_val and abs(old_val - new_val) > 2.0:
                                try: print(f"    [对位修正] {track.get('title')[:30]}: Mix-In {old_val:.1f}s -> {new_val:.1f}s")
                                except: pass
                                
                        if 'C' in pro_hcs:
                            old_val = track.get('mix_out_point')
                            new_val = pro_hcs['C']['Start']
                            track['mix_out_point'] = new_val
                            if old_val and abs(old_val - new_val) > 2.0:
                                try: print(f"    [对位修正] {track.get('title')[:30]}: Mix-Out {old_val:.1f}s -> {new_val:.1f}s")
                                except: pass
                        if 'E' in pro_hcs:
                            dep = pro_hcs['E']['Start']
                            track['drop_point'] = dep
                            if 'analysis' not in track: track['analysis'] = {}
                            track['analysis']['drop_point'] = dep
                            # 注入染色段
                            track['vocals'] = track.get('vocals', {}) or {}
                            if isinstance(track['vocals'], dict):
                                track['vocals']['segments'] = track['vocals'].get('segments', []) + [[dep, dep+15]]

                    # C. 物理隔离与 Hash (V9.1 强制刷新方案)
                    if original_file_path in processed_tracks_map:
                        track['file_path'] = processed_tracks_map[original_file_path]
                    else:
                        src = Path(original_file_path)
                        import time, hashlib
                        fh = hashlib.md5(f"{time.time()}_{original_file_path}".encode()).hexdigest()[:6]
                        new_name = f"{src.stem}_{fh}{src.suffix}"
                        dst = set_audio_dir / new_name
                        if src.exists():
                            shutil.copy2(src, dst)
                        
                        path_str = str(dst)
                        track['file_path'] = path_str
                        processed_tracks_map[original_file_path] = path_str

                    # D. 元数据装饰
                    orig_t = track.get('title', 'Unknown')
                    if "✅[AI_FULL" not in str(orig_t):
                        track['title'] = f"{orig_t} ✅[AI_FULL_V9.1]"
                    track['artist'] = f"{track.get('artist', 'Unknown')} [VERIFIED]"
                    track['force_refresh'] = True

            print("  [OK] 全闭环物理隔离与标点注入完成")

            print("  [OK] 物理隔离与标点校准完成")
        except Exception as e:
            print(f"  [Error] 物理隔离预处理失败: {e}")
        
        try:
            try:
                print(f"\n[完成] 所有Set排序完成！共 {len(sets)} 个Set")
            except UnicodeEncodeError:
                print(f"\n[完成] All sets sorted! Total: {len(sets)} sets")
            print("正在生成M3U文件和混音建议...")
        except:
            print("  [完成] All sets sorted! Total: {len(sets)} sets")
            print("Generating M3U files and mixing advice...")
        
        # (output_dir 路径定义已上移至 Phase 12.1 前)
        
        # (playlist_display_name 路径定义已上移至 Phase 12.1 前)
        
        # 删除同播放列表的旧文件（保留 1 小时内的文件以防误删）
        try:
            import time
            current_time = time.time()
            all_files = list(output_dir.glob(f"{playlist_display_name}_*.*"))
            
            for old_file in all_files:
                try:
                    # 如果文件是 1 小时前生成的，则清理
                    if current_time - old_file.stat().st_mtime > 3600:
                        old_file.unlink()
                except:
                    pass
        except:
            pass
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        m3u_file = output_dir / f"{playlist_display_name}_增强调和谐版_{timestamp}.m3u"
        
        # 【V3.0 ULTRA+ 修复】M3U 导出前先去重
        seen_paths = set()
        
        # 生成M3U内容
        m3u_lines = ["#EXTM3U"]
        
        for set_idx, set_tracks in enumerate(sets, 1):
            try:
                print(f"  处理 Set {set_idx}/{len(sets)}...")
            except:
                print(f"  Processing Set {set_idx}/{len(sets)}...")
            
            m3u_lines.append(f"\n# 分割线 - Set {set_idx} ({len(set_tracks)} 首歌曲)")
            
            for track in set_tracks:
                # 【V3.0 ULTRA+ 修复】跳过已去重的曲目
                path = (track.get('file_path') or '').replace('\\', '/').lower()
                if path not in seen_paths:
                    seen_paths.add(path)
                    
                    duration = 0  # M3U不需要精确时长
                    m3u_lines.append(f"#EXTINF:{duration},{track['artist']} - {track['title']}")
                    m3u_lines.append(track['file_path'])
            
            # 如果不是最后一个set，添加过渡歌曲作为分割标识
            if set_idx < len(sets):
                m3u_lines.append(f"\n# ========== Set {set_idx + 1} 结束 | Set {set_idx + 2} 开始 ==========")
                # 使用当前set的最后一首歌作为过渡（重复播放），帮助set之间的平滑过渡
                # 这是专业DJ的做法：用一首歌作为两个set之间的桥梁
                last_track = set_tracks[-1]
                
                # 添加过渡标识和重复的最后一首歌
                m3u_lines.append(f"#EXTINF:{duration},{last_track['artist']} - {last_track['title']} [Set过渡 - 重复播放]")
                m3u_lines.append(last_track['file_path'])
                m3u_lines.append("")  # 空行作为分隔
        
        # 写入M3U文件
        try:
            print("  正在写入M3U文件...")
        except:
            print("  Writing M3U file...")
        with open(m3u_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(m3u_lines))
        
        # ========== 【P0优化】导出CSV文件 ==========
        try:
            from export_set_to_csv import export_set_to_csv, format_key_display
            
            # 为所有歌曲添加优化的调性显示
            all_tracks_for_csv = []
            for set_idx, set_tracks in enumerate(sets, 1):
                for track in set_tracks:
                    track_copy = track.copy()
                    # 优化调性显示（Camelot + Open Key）
                    track_copy['key'] = format_key_display(track.get('key', 'Unknown'))
                    track_copy['set_number'] = set_idx
                    all_tracks_for_csv.append(track_copy)
            
            # 导出CSV
            csv_file = output_dir / f"{playlist_display_name}_增强调性和谐版_{timestamp}.csv"
            export_set_to_csv(all_tracks_for_csv, str(csv_file))
            
            try:
                print(f"  [OK] CSV已导出: {csv_file.name}")
            except:
                print(f"  CSV exported: {csv_file.name}")
        except Exception as e:
            # 如果CSV导出失败，不影响主流程
            try:
                print(f"  警告: CSV导出失败 ({e})")
            except:
                print(f"  Warning: CSV export failed ({e})")
        
        # 生成混音建议报告（文件名已在上面的删除逻辑中处理）
        try:
            print("  正在生成混音建议报告...")
        except:
            print("  Generating mixing advice report...")
        report_file = output_dir / f"{playlist_display_name}_混音建议_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8-sig') as f:
            f.write(f"播放列表：{playlist_display_name}\n")
            f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"共生成 {len(sets)} 个Set\n")
            f.write(f"总歌曲数：{len(tracks)} 首\n")
            if ACTIVE_PROFILE:
                f.write(f"使用进化配置: {ACTIVE_PROFILE.name}\n")
                f.write(f"策略描述: {ACTIVE_PROFILE.description}\n")
            f.write("\n")
            
            # ========== 【进化战略】集成混音雷达报告 ==========
            try:
                # 合并所有 set 的轨道进行总体分析
                all_sorted_tracks = []
                for s in sets:
                    all_sorted_tracks.extend(s)
                
                radar_report = generate_radar_report(all_sorted_tracks)
                f.write("=" * 80 + "\n")
                f.write("质量监控报告 (Mixing Radar)\n")
                f.write("=" * 80 + "\n\n")
                f.write(radar_report)
                f.write("\n\n")
            except Exception as radar_err:
                f.write(f"\n[错误] 无法生成雷达报告: {radar_err}\n\n")

            f.write("=" * 80 + "\n")
            f.write("SET 歌单列表\n")
            f.write("=" * 80 + "\n\n")
            
            # 列出每个Set的完整歌曲列表
            # [Dual Mode Persistence Fix] 即使经过内部处理，如果满足 Boutique 长度特征且是第 1 个 Set，自动识别
            is_dual_mode = any(s and s[0].get('is_boutique_start') for s in sets)
            if not is_dual_mode and len(sets) > 1 and 25 <= len(sets[0]) <= 50:
                 # 冗余检查：如果第一个 Set 长度在精品范围内，且后续还有全量 Set，自动恢复标记
                 is_dual_mode = True
                 if sets[0]: sets[0][0]['is_boutique_start'] = True
            
            for set_idx, set_tracks in enumerate(sets, 1):
                f.write(f"\n{'='*80}\n")
                
                # [Dual Mode] 标题定制
                is_boutique_head = set_idx == 1 and set_tracks and set_tracks[0].get('is_boutique_start')
                if is_boutique_head:
                    title = f"Set {set_idx} [✨ BOUTIQUE HIGHLIGHT 精选] (Best {len(set_tracks)} Tracks)"
                elif is_dual_mode:
                    # 如果开启了双模，且当前不是 Boutique，那就是 Live 全量
                    title = f"Set {set_idx} [🔴 FULL LIVE 全量] (Part {set_idx-1 if is_dual_mode else set_idx}) ({len(set_tracks)} Tracks)"
                else:
                    title = f"Set {set_idx} ({len(set_tracks)} 首歌曲)"
                
                f.write(f"{title}\n")
                f.write(f"{'='*80}\n\n")
                
                for idx, track in enumerate(set_tracks, 1):
                    artist = track.get('artist', 'Unknown')
                    title = track.get('title', 'Unknown')
                    bpm = track.get('bpm', 0)
                    key = track.get('key', '未知')
                    energy = track.get('energy', 0)
                    duration = track.get('duration', 0)
                    mix_in = track.get('mix_in_point')
                    mix_out = track.get('mix_out_point')
                    
                    # 格式化时长显示（超过60秒显示为X分X秒）
                    if duration >= 60:
                        minutes = int(duration // 60)
                        seconds = int(duration % 60)
                        duration_str = f"{duration:.0f}秒 ({minutes}分{seconds}秒)"
                    else:
                        duration_str = f"{duration:.0f}秒"
                    
                    # 格式化混音点显示（超过60秒显示为X分X秒，并显示拍数）
                    def format_time(seconds, bpm_value=None):
                        if seconds is None:
                            return "未检测"
                        
                        # 计算拍数（如果提供了BPM）
                        beats_info = ""
                        if bpm_value and bpm_value > 0:
                            beat_duration = 60.0 / bpm_value
                            beats = int(seconds / beat_duration)
                            bars = beats // 8  # 8拍 = 1个八拍
                            remaining_beats = beats % 8
                            if bars > 0:
                                if remaining_beats == 0:
                                    beats_info = f" ({bars}个八拍)"
                                else:
                                    beats_info = f" ({bars}个八拍{remaining_beats}拍)"
                            elif beats > 0:
                                beats_info = f" ({beats}拍)"
                        
                        if seconds >= 60:
                            minutes = int(seconds // 60)
                            secs = int(seconds % 60)
                            # 三位小数以对齐 XML Start 属性
                            return f"{seconds:.3f}秒 ({minutes}分{secs}秒){beats_info}"
                        return f"{seconds:.3f}秒{beats_info}"
                    
                    # 格式化输出（检查是否为桥接曲）
                    is_bridge = track.get('is_bridge', False)
                    bridge_reason = track.get('bridge_reason', '')
                    
                    # 【P0优化】使用优化的调性显示（Camelot + Open Key）
                    try:
                        from export_set_to_csv import format_key_display
                        key_display = format_key_display(key)
                    except:
                        key_display = key
                    
                    if is_bridge:
                        f.write(f"{idx:2d}. [桥接曲] {artist} - {title}\n")
                        f.write(f"    BPM: {bpm:.1f} | 调性: {key_display} | 能量: {energy:.0f}/100 | 时长: {duration_str}\n")
                        f.write(f"    [自动插入原因] {bridge_reason}\n")
                    else:
                        f.write(f"{idx:2d}. {artist} - {title}\n")
                        f.write(f"    BPM: {bpm:.1f} | 调性: {key_display} | 能量: {energy:.0f}/100 | 时长: {duration_str}\n")
                    
                    # 显示歌曲结构信息（简化版：只显示关键段落）
                    structure = track.get('structure')
                    if structure:
                        # 只显示Intro和Outro的时间点（DJ最关心的混音区域）
                        key_points = []
                        if structure.get('intro'):
                            start, end = structure['intro']
                            key_points.append(f"Intro结束: {format_time(end, bpm)}")
                        if structure.get('outro'):
                            start, end = structure['outro']
                            key_points.append(f"Outro开始: {format_time(start, bpm)}")
                        
                        if key_points:
                            f.write(f"    结构: {' | '.join(key_points)}\n")

                    # 【V9.2 专家级透明度】显示 Pro Hotcues (Rekordbox 标准)
                    pro_hcs = track.get('pro_hotcues', {})
                    if pro_hcs:
                        f.write(f"    ⭐ Pro Hotcues (Rekordbox 协同):\n")
                        for hc_key in ['A', 'B', 'C', 'D', 'E']:
                            if hc_key in pro_hcs:
                                hc = pro_hcs[hc_key]
                                hc_name = hc.get('Name', f"Cue {hc_key}")
                                hc_time = hc.get('Start', 0.0)
                                # 【V9.2.1】显示确切的 Rekordbox 段落名称 (PSSI 驱动)
                                phrase_label = hc.get('PhraseLabel', "[Grid Sync]")
                                f.write(f"      - {hc_name}: {format_time(hc_time, bpm)} {phrase_label}\n")
                    
                    # 显示混音点（根据下一首歌的混入点来判断）
                    # idx是1-based（从1开始），set_tracks是0-based（从0开始）
                    # 当前歌曲：set_tracks[idx - 1]
                    # 下一首歌曲：set_tracks[idx]（如果存在）
                    # 上一首歌曲：set_tracks[idx - 2]（如果idx > 1）
                    
                    # 显示当前歌曲的混入点（显示上一首的混出点）
                    if idx == 1:
                        # 第一首歌曲
                        if mix_in:
                            f.write(f"    🎯 最佳接歌点(Mix-In): {format_time(mix_in, bpm)}\n")
                        else:
                            f.write(f"    🎯 最佳接歌点(Mix-In): 未检测\n")
                    else:
                        # 不是第一首，显示上一首的混出点
                        prev_track = set_tracks[idx - 2]  # 上一首歌曲（idx是1-based，所以idx-2是上一首的索引）
                        prev_mix_out = prev_track.get('mix_out_point')
                        prev_bpm = prev_track.get('bpm', 0)
                        if mix_in:
                            if prev_mix_out:
                                f.write(f"    🎯 最佳接歌点(Mix-In): {format_time(mix_in, bpm)} | 上一首出歌点: {format_time(prev_mix_out, prev_bpm)}\n")
                            else:
                                f.write(f"    🎯 最佳接歌点(Mix-In): {format_time(mix_in, bpm)} | 上一首出歌点: 未检测\n")
                        else:
                            if prev_mix_out:
                                f.write(f"    🎯 最佳接歌点(Mix-In): 未检测 | 建议在上一首出歌点 {format_time(prev_mix_out, prev_bpm)} 后开始混入\n")
                    
                    # 显示当前歌曲的混出点（应该根据下一首的混入点来判断）
                    if idx < len(set_tracks):
                        next_track = set_tracks[idx]  # 下一首歌曲
                        next_mix_in = next_track.get('mix_in_point')
                        next_bpm = next_track.get('bpm', 0)
                        
                        if mix_out:
                            # 如果下一首有混入点，显示当前歌曲的混出点和下一首的混入点
                            if next_mix_in:
                                f.write(f"    🎯 最佳出歌点(Mix-Out): {format_time(mix_out, bpm)} | 下一首接歌点: {format_time(next_mix_in, next_bpm)}\n")
                            else:
                                f.write(f"    🎯 最佳出歌点(Mix-Out): {format_time(mix_out, bpm)} | 下一首接歌点: 未检测\n")
                        else:
                            if next_mix_in:
                                f.write(f"    🎯 最佳出歌点(Mix-Out): 未检测 | 建议在下一首接歌点前 {format_time(next_mix_in, next_bpm)} 开始淡出\n")
                            else:
                                f.write(f"    🎯 最佳出歌点(Mix-Out): 未检测（建议手动选择）\n")
                        
                        # 在歌曲之间显示混音建议（只有需要提示时才显示）
                        if idx < len(set_tracks):
                            # 判断是否需要显示详细建议
                            need_advice = False
                            curr_bpm = track.get('bpm', 0)
                            next_bpm = next_track.get('bpm', 0)
                            curr_key = track.get('key', '')
                            next_key = next_track.get('key', '')
                            
                            bpm_diff = abs(curr_bpm - next_bpm) if curr_bpm and next_bpm else 999
                            key_score = get_key_compatibility_flexible(curr_key, next_key) if curr_key and next_key and curr_key != "未知" and next_key != "未知" else 0
                            
                            # 如果BPM跨度>8或调性兼容性<60，需要显示建议
                            if bpm_diff > 8 or key_score < 60:
                                need_advice = True
                            
                            # 检查人声/鼓点匹配情况
                            curr_vocals = track.get('vocals')
                            next_vocals = next_track.get('vocals')
                            if curr_vocals and next_vocals and mix_out and next_mix_in:
                                # 检查是否是人声混人声（不推荐）
                                current_out_vocals = False
                                for seg_start, seg_end in curr_vocals.get('segments', []):
                                    if seg_start <= mix_out <= seg_end:
                                        current_out_vocals = True
                                        break
                                
                                next_in_vocals = False
                                for seg_start, seg_end in next_vocals.get('segments', []):
                                    if seg_start <= next_mix_in <= seg_end:
                                        next_in_vocals = True
                                        break
                                
                                # 如果是人声混人声，需要显示建议
                                if current_out_vocals and next_in_vocals:
                                    need_advice = True
                            
                            # 【V6.0 Audit】始终显示建议，以便展示审计日志
                            if True: # 原为 need_advice
                                f.write(f"\n    {'─'*70}\n")
                                f.write(f"    📝 混音建议：{title} → {next_track.get('title', 'Unknown')[:30]}\n")
                                f.write(f"    {'─'*70}\n")
                                
                                transition_advice = generate_transition_advice(track, next_track, idx)
                                if transition_advice:
                                    for line in transition_advice:
                                        f.write(line + "\n")
                                else:
                                    f.write("    ✅ 过渡很和谐，标准混音即可\n")
                                f.write("\n")
                            else:
                                # 好接的过渡，只显示一个简单的确认
                                f.write("    ✅ 过渡顺畅，标准混音即可\n\n")
                    else:
                        # 最后一首歌曲，只显示混入点和混出点
                        if mix_in and mix_out:
                            f.write(f"    🎯 最佳接歌点(Mix-In): {format_time(mix_in, bpm)} | 最佳出歌点(Mix-Out): {format_time(mix_out, bpm)}\n")
                        elif mix_in:
                            f.write(f"    🎯 最佳接歌点(Mix-In): {format_time(mix_in, bpm)} | 最佳出歌点(Mix-Out): 未检测\n")
                        elif mix_out:
                            f.write(f"    🎯 最佳接歌点(Mix-In): 未检测 | 最佳出歌点(Mix-Out): {format_time(mix_out, bpm)}\n")
                        else:
                            f.write(f"    🎯 混音点: 未检测（建议手动选择）\n")
                
                # 如果不是最后一个set，添加过渡说明
                if set_idx < len(sets):
                    f.write(f"\n    [过渡] → Set {set_idx + 1} 开始\n")
            
            # ========== [Phase 9] 专业大考报告 Header ==========
            if PROFESSIONAL_AUDIT_ENABLED:
                all_tracks_flat = [t for s in sets for t in s]
                audit = calculate_set_completeness(all_tracks_flat)
                energy_curve = get_energy_curve_summary(all_tracks_flat)
                
                f.write(f"\n{'#'*80}\n")
                f.write(f"### 专业 DJ Set 完整度报告 (Phase 9 Audit)\n")
                f.write(f"{'#'*80}\n")
                f.write(f"总平均得分: {audit['total_score']}/100  | 评级: {audit['rating']}\n")
                f.write(f"能量曲线分析: {energy_curve}\n")
                f.write(f"分项指标:\n")
                f.write(f"  - 调性流转 (Harmonic): {audit['breakdown'].get('harmonic_flow', 0)}/25\n")
                f.write(f"  - BPM 梯度 (Momentum): {audit['breakdown'].get('bpm_stability', 0)}/25\n")
                f.write(f"  - 乐句对齐 (Phrase): {audit['breakdown'].get('phrase_alignment', 0)}/25\n")
                f.write(f"  - 人声安全 (Vocal): {audit['breakdown'].get('vocal_safety', 0)}/25\n")
                f.write(f"{'='*80}\n\n")

            # ========== 桥接曲汇总 ==========
            if bridge_insertions:
                f.write(f"\n\n{'='*80}\n")
                f.write(f"桥接曲汇总 (共 {len(bridge_insertions)} 首自动插入)\n")
                f.write(f"{'='*80}\n\n")
                f.write("以下位置因BPM跨度过大(>15)，系统自动插入了桥接曲：\n\n")
                
                for i, info in enumerate(bridge_insertions, 1):
                    f.write(f"{i}. Set {info['set_idx']} 第 {info['position']} 首后\n")
                    f.write(f"   原过渡: {info['prev_track']} -> {info['next_track']}\n")
                    f.write(f"   原BPM跨度: {info['prev_bpm']:.1f} -> {info['next_bpm']:.1f} (跨度 {info['original_gap']:.1f})\n")
                    f.write(f"   插入桥接曲: {info['bridge_track']}\n")
                    f.write(f"   新BPM跨度: {info['prev_bpm']:.1f} -> {info['bridge_bpm']:.1f} -> {info['next_bpm']:.1f}\n")
                    f.write(f"              (跨度 {info['new_gap_1']:.1f} + {info['new_gap_2']:.1f})\n")
                    f.write(f"   选择原因: {' | '.join(info['reasons'])}\n\n")
        
        
        # [PRO FIX] 确保 clean_name 在 XML 停用后仍然可用（用于 Master 报告）
        clean_name = "".join([c for c in playlist_display_name if c.isalpha() or c.isdigit() or c==' ' or c=='_']).rstrip()
        
        # [DEACTIVATED] 生成 Rekordbox XML (按用户要求停用)
        # try:
        #     print("  正在生成 Rekordbox XML...")
        #     for i, set_tracks in enumerate(sets):
        #         # 【Phase 8】为每首歌生成专业 HotCues (A-G)
        #         if HOTCUE_GENERATOR_ENABLED:
        #             for track in set_tracks:
        #                 # 强鲁棒性校验
        #                 if not isinstance(track, dict): continue
        #                 
        #                 # 如果已经在 [Phase 12.1] 生成过，则跳过以防递归偏移
        #                 if track.get('pro_hotcues'):
        #                     continue
        #
        #         xml_file = output_dir / f"{clean_name}_Set{i+1}_{timestamp}.xml"
        #         export_to_rekordbox_xml(set_tracks, xml_file, playlist_name=f"{clean_name}_Set{i+1}")
        #         try:
        #             print(f"  ✓ XML已导出: {xml_file.name}")
        #         except:
        #             print(f"  XML exported: {xml_file.name}")
        # except Exception as e:
        #     try:
        #         print(f"  无法生成 XML: {e}")
        #     except:
        #         print(f"  XML export failed: {e}")

        try:
            try:
                print("  [完成] 文件生成完成！")
            except UnicodeEncodeError:
                print("  [完成] Files generated!")
        except:
            print("  [完成] Files generated!")
        
        try:
            print(f"\n{'='*60}")
            print("完成！")
            print(f"M3U文件: {m3u_file}")
            print(f"混音建议报告: {report_file}")
            print(f"共生成 {len(sets)} 个Set")
            print(f"{'='*60}")
            
            # ============================================================
            # 【Master 模式】如果启用 Master 模式，生成统一的 Master M3U 和 Master XML
            # ============================================================
            if is_master and sets:
                # 【V3.0 ULTRA+ 修复】去重逻辑：按 file_path 去重
                seen_paths = set()
                master_tracks = []
                for s in sets:
                    for track in s:
                        path = (track.get('file_path') or '').replace('\\', '/').lower()
                        if path and path not in seen_paths:
                            seen_paths.add(path)
                            master_tracks.append(track)
                if seen_paths:
                    print(f"  [去重] Master Set: {len(seen_paths)} 首不重复曲目")

                # 导出 Master M3U
                master_m3u_name = f"{clean_name}_Master_Unified_{timestamp}.m3u"
                master_m3u_path = output_dir / master_m3u_name
                with open(master_m3u_path, "w", encoding="utf-8") as f:
                    f.write("#EXTM3U\n")
                    for track in master_tracks:
                        f.write(f"#EXTINF:{int(track.get('duration', 0))},{track.get('artist', 'Unknown')} - {track.get('title', 'Unknown')}\n")
                        f.write(f"{track.get('file_path', '')}\n")
                
                try:
                    print(f"\n[Master] 已导出全局连贯 Master M3U: {master_m3u_name}")
                except:
                    print(f"\n[Master] Unified M3U exported: {master_m3u_name}")
                
                # 导出 Master XML (包含文件夹结构)
                master_xml_name = f"{clean_name}_Master_Library_{timestamp}.xml"
                master_xml_path = output_dir / master_xml_name
                try:
                    from exporters.xml_exporter import export_multi_sets_to_rekordbox_xml
                    export_multi_sets_to_rekordbox_xml(sets, master_xml_path, playlist_name)
                    print(f"[Master] 已导出 Master Rekordbox XML (含文件夹结构): {master_xml_name}")
                except Exception as e:
                    print(f"[Master] 警告 (非致命): 无法导出 Master XML (可能是路径权限问题): {e}")
                    # 不抛出异常，保持 Exit Code 0

            # 混音建议已显示在歌曲之间，不再打印简要建议
            try:
                print("\n混音建议已显示在歌曲之间")
            except:
                print("\nMixing advice displayed between songs")
        except Exception as e:
            print(f"Error in final report: {e}")

            print(f"Mixing advice report: {report_file}")
            print(f"Generated {len(sets)} sets")
            print(f"{'='*60}")
        
        # 自动打开输出文件夹
        try:
            import subprocess
            import platform
            output_path = str(output_dir.resolve())
            
            if platform.system() == 'Windows':
                subprocess.Popen(f'explorer "{output_path}"')
            elif platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['open', output_path])
            else:  # Linux
                subprocess.Popen(['xdg-open', output_path])
            
            try:
                print(f"\n已自动打开文件夹: {output_path}")
            except:
                print(f"\nOpened folder: {output_path}")
        except Exception as e:
            try:
                print(f"\n无法自动打开文件夹: {e}")
            except:
                print(f"\nFailed to open folder: {e}")
        
        await db.disconnect()
        return sets
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        try:
            await db.disconnect()
        except:
            pass

# ========== 主程序入口 (Entry Point) - 已迁移至文末以确保函数加载顺序 ==========
# 内容原在6576-6656行


# ========== 补充缺失的函数（用于quick_sort_house.py） ==========

def get_file_cache_key(file_path: str) -> Optional[str]:
    """获取文件缓存键"""
    return get_file_hash(file_path)


def is_cache_valid(cached_entry: dict, file_path: str) -> bool:
    """检查缓存是否有效"""
    cached_path = cached_entry.get('file_path', '').replace('\\', '/')
    file_path_str = str(file_path).replace('\\', '/')
    return cached_path == file_path_str


def calculate_transition_risk(current_track: dict, next_track: dict, mix_gap: Optional[float] = None, structure_warning: bool = False) -> tuple:
    """计算曲间风险评分"""
    risk_score = 0
    risk_reasons = []
    
    current_key = current_track.get('key', '')
    next_key = next_track.get('key', '')
    key_score = get_key_compatibility_flexible(current_key, next_key)
    
    if key_score < 50:
        key_clash = (50 - key_score) / 50.0
        risk_score += key_clash * 30
        risk_reasons.append("调性冲突")
    
    current_energy = current_track.get('energy', 50)
    next_energy = next_track.get('energy', 50)
    energy_diff = current_energy - next_energy
    
    if energy_diff > 15:
        energy_drop = min(1.0, (energy_diff - 15) / 30.0)
        risk_score += energy_drop * 20
        risk_reasons.append("能量突降")
    
    mix_point_risk = 0
    if mix_gap is not None:
        if abs(mix_gap) > 20:
            mix_point_risk = 1.0
            risk_reasons.append("混音点间隔异常")
        elif abs(mix_gap) > 18:
            mix_point_risk = 0.5
            risk_reasons.append("混音点间隔较大")
    
    if structure_warning:
        mix_point_risk = max(mix_point_risk, 0.33)
        if "混音点在Verse中间" not in risk_reasons:
            risk_reasons.append("混音点在Verse中间")
    
    risk_score += mix_point_risk * 15

    # ===== 追加：响度/低频/动态范围（轻量风险项，避免“听感断层”）=====
    try:
        from split_config import get_config as _get_cfg
        _cfg = _get_cfg() or {}
    except Exception:
        _cfg = {}
    tr_cfg = (_cfg.get("transition_risk_profile") or {})
    if bool(tr_cfg.get("enabled", True)):
        # 1) LUFS（越接近0越响；差值大容易炸/空）
        l1 = current_track.get("loudness_lufs")
        l2 = next_track.get("loudness_lufs")
        try:
            if isinstance(l1, (int, float)) and isinstance(l2, (int, float)):
                diff = abs(float(l1) - float(l2))
                thr = float(tr_cfg.get("lufs_diff_warn_db", 4.0))
                if diff >= thr:
                    # diff=thr -> 0.5, diff>=2*thr -> 1.0
                    w = float(tr_cfg.get("lufs_diff_risk_weight", 12.0))
                    ratio = min(1.0, max(0.0, (diff - thr) / max(1e-6, thr)))
                    risk_score += ratio * w
                    risk_reasons.append("响度差过大")
        except Exception:
            pass

        # 2) 动态范围（差异大：一首压扁一首很动态，会“感觉不在一个系统”）
        dr1 = current_track.get("dynamic_range_db")
        dr2 = next_track.get("dynamic_range_db")
        try:
            if isinstance(dr1, (int, float)) and isinstance(dr2, (int, float)):
                diff = abs(float(dr1) - float(dr2))
                thr = float(tr_cfg.get("dyn_range_diff_warn_db", 6.0))
                if diff >= thr:
                    w = float(tr_cfg.get("dyn_range_risk_weight", 8.0))
                    ratio = min(1.0, max(0.0, (diff - thr) / max(1e-6, thr)))
                    risk_score += ratio * w
                    risk_reasons.append("动态范围差异")
        except Exception:
            pass

        # 3) 低频骨架（kick/sub）差异：会导致“低频换不干净/突然没底”
        k1 = current_track.get("kick_drum_power")
        k2 = next_track.get("kick_drum_power")
        s1 = current_track.get("sub_bass_level")
        s2 = next_track.get("sub_bass_level")
        try:
            if isinstance(k1, (int, float)) and isinstance(k2, (int, float)) and isinstance(s1, (int, float)) and isinstance(s2, (int, float)):
                diff = max(abs(float(k1) - float(k2)), abs(float(s1) - float(s2)))
                thr = float(tr_cfg.get("lowfreq_mismatch_warn", 0.35))
                if diff >= thr:
                    w = float(tr_cfg.get("lowfreq_risk_weight", 8.0))
                    ratio = min(1.0, max(0.0, (diff - thr) / max(1e-6, thr)))
                    risk_score += ratio * w
                    risk_reasons.append("低频骨架不一致")
        except Exception:
            pass

    risk_score = min(100, risk_score)
    
    if risk_score < 20:
        risk_level = "safe"
    elif risk_score < 40:
        risk_level = "medium"
    else:
        risk_level = "danger"
    
    return (risk_level, risk_score, risk_reasons)


def is_key_transition_allowed(current_key: str, next_key: str, 
                             is_segment_boundary: bool = False,
                             config: dict = None,
                             track: dict = None) -> tuple:
    """
    检查调性过渡是否允许（统一阈值到距离<=3）。
    
    Args:
        current_key: 当前调性（如 "1A"）
        next_key: 下一首调性（如 "4A"）
        is_segment_boundary: 是否为段落边界
        config: 配置字典（可选）
        track: 当前track字典（用于标记置信度）
    
    Returns:
        (allowed: bool, reason: str)
    """
    # 加载配置
    try:
        from core.track_finder import smart_find_track
        from core.cache_manager import load_cache, save_cache_atomic
    except ImportError:
        # Use internal fallback if core not in path
        def smart_find_track(k, **kwargs): return []
        def load_cache(): return {}
        def save_cache_atomic(c, p): pass
    if config is None:
        try:
            from split_config import get_config
            config = get_config()
        except ImportError:
            config = {"key": {"max_allowed_distance": 3, "parse_error_penalty": 0.1}}
    
    key_config = config.get("key", {})
    max_allowed_distance = key_config.get("max_allowed_distance", 3)
    parse_error_penalty = key_config.get("parse_error_penalty", 0.1)
    unknown_key_penalty = key_config.get("unknown_key_penalty", 0.05)
    log_key_transitions = key_config.get("log_key_transitions", True)
    
    # 检查未知调性
    if not current_key or current_key.lower() in ("unknown", "未知", ""):
        if track:
            track['key_confidence'] = track.get('key_confidence', 1.0) - unknown_key_penalty
        return (True, "current key unknown -> allow (low confidence)")
    
    if not next_key or next_key.lower() in ("unknown", "未知", ""):
        if track:
            track['key_confidence'] = track.get('key_confidence', 1.0) - unknown_key_penalty
        return (True, "next key unknown -> allow (low confidence)")
    
    if is_segment_boundary:
        return (True, "segment boundary -> allow")
    
    try:
        # 解析调性数字（支持 "1A", "12B" 等格式）
        curr_num = int(''.join(ch for ch in current_key if ch.isdigit()))
        next_num = int(''.join(ch for ch in next_key if ch.isdigit()))
        
        def circle_distance(a, b):
            """计算5度圈距离（考虑轮盘循环）"""
            direct = abs(a - b)
            wrap = 12 - direct
            return min(direct, wrap)
        
        diff = circle_distance(curr_num, next_num)
        
        # 详细日志
        reason = ""
        if diff == 0:
            reason = "同调"
        elif diff == 1:
            reason = "5度圈相邻"
        elif diff == 2:
            reason = "5度圈隔一个"
        elif diff == 3:
            reason = "5度圈隔两个（需要技巧）"
        else:
            reason = f"非法调性跨越（距离{diff}）"
        
        if log_key_transitions:
            print(f"[调性过渡] {current_key}→{next_key}: {reason} (距离={diff})")
        
        # 判断是否允许（使用配置的阈值）
        if diff <= max_allowed_distance:
            return (True, f"allowed (circle_distance={diff} <= {max_allowed_distance}, {reason})")
        else:
            return (False, f"illegal key transition (circle_distance={diff} > {max_allowed_distance}, {reason})")
    
    except (ValueError, IndexError, AttributeError) as e:
        # 解析失败：允许但标注低置信度
        if track:
            track['key_confidence'] = track.get('key_confidence', 1.0) - parse_error_penalty
        
        error_msg = f"key parse error '{str(e)}' -> allow (low confidence)"
        if log_key_transitions:
            print(f"[调性解析错误] {current_key}→{next_key}: {error_msg}")
        
        return (True, error_msg)


def get_genre_group(genre: str) -> str:
    """将风格归类到组"""
    if not genre:
        return "Unknown"
    
    genre_lower = genre.lower()
    
    if any(keyword in genre_lower for keyword in ['house', 'tech house', 'deep house', 'progressive house']):
        return "H"
    if any(keyword in genre_lower for keyword in ['techno', 'hard techno']):
        return "T"
    if any(keyword in genre_lower for keyword in ['bass', 'trap', 'dubstep', 'dnb', 'drum and bass']):
        return "B"
    if any(keyword in genre_lower for keyword in ['afro', 'latin', 'world', 'baile funk']):
        return "A"
    if any(keyword in genre_lower for keyword in ['breaks', 'breakbeat']):
        return "K"
    
    return "Unknown"


def get_genre_transition_score(current_group: str, next_group: str) -> int:
    """计算风格过渡分数"""
    if current_group == "Unknown" or next_group == "Unknown":
        return 50
    
    if current_group == next_group:
        return 100
    
    if (current_group == "H" and next_group == "A") or (current_group == "A" and next_group == "H"):
        return 70
    if (current_group == "H" and next_group == "T") or (current_group == "T" and next_group == "H"):
        return 70
    
    if (current_group == "H" and next_group == "B") or (current_group == "B" and next_group == "H"):
        return 30
    if (current_group == "A" and next_group == "T") or (current_group == "T" and next_group == "A"):
        return 30
    
    if (current_group == "T" and next_group == "B") or (current_group == "B" and next_group == "T"):
        return 0
    
    return 50


def infer_drum_pattern(bpm: float, genre: str) -> str:
    """基于BPM+风格推断鼓型"""
    if not genre:
        return "4/4"
    
    genre_lower = genre.lower()
    
    if 118 <= bpm <= 130:
        if any(keyword in genre_lower for keyword in ['tech house', 'techno', 'house']):
            return "4/4"
    
    if any(keyword in genre_lower for keyword in ['afro', 'tribal', 'latin']):
        return "afro"
    
    if any(keyword in genre_lower for keyword in ['trap', 'bass', 'dubstep']):
        return "half-time"
    
    if any(keyword in genre_lower for keyword in ['breaks', 'breakbeat']):
        return "breaks"
    
    return "4/4"


def is_drum_pattern_transition_allowed(current_pattern: str, next_pattern: str) -> bool:
    """检查鼓型过渡是否合法"""
    if current_pattern == "4/4" and next_pattern == "4/4":
        return True
    
    if (current_pattern == "4/4" and next_pattern == "afro") or \
       (current_pattern == "afro" and next_pattern == "4/4"):
        return True
    
    if (current_pattern == "4/4" and next_pattern == "breaks") or \
       (current_pattern == "breaks" and next_pattern == "4/4"):
        return True
    
    if (current_pattern == "4/4" and next_pattern == "half-time") or \
       (current_pattern == "half-time" and next_pattern == "4/4"):
        return False
    
    if current_pattern == "half-time" and next_pattern == "half-time":
        return True
    
    return True



# ========== Rekordbox Stems Mashup功能 ==========

def find_stems_mashup_pairs(playlist_name: str, min_score: float = 75.0, max_results: int = 20):
    """
    专为Rekordbox Stems设计的Mashup搜索工具
    复用现有的调性和BPM兼容性函数
    """
    print("=" * 80)
    print("Rekordbox Stems Mashup搜索工具")
    print("=" * 80)
    print()
    
    # 1. 加载歌曲（复用mashup_finder的函数）
    print("[1/3] 加载播放列表...")
    
    # 导入必要的模块
    from pyrekordbox import Rekordbox6Database
    from sqlalchemy import text
    
    # 加载缓存
    cache = load_cache()
    cache_by_path = {}
    for hash_key, data in cache.items():
        if 'file_path' in data:
            fp = data['file_path'].lower().replace('\\', '/')
            cache_by_path[fp] = data.get('analysis', {})
    
    # 加载歌曲
    db = Rekordbox6Database()
    # 1. 加载歌曲
    tracks = []
    
            continue
        
        content_id = getattr(song, 'ContentID', None)
        if not content_id:
            continue
        
        try:
            content = song if hasattr(song, 'Title') else db.get_content(ID=content_id)
            if not content:
                continue
            
            bpm_raw = getattr(content, 'BPM', 0) or 0
            bpm = bpm_raw / 100.0 if bpm_raw > 500 else bpm_raw # 处理 10169 -> 101.69 的逻辑

            key = getattr(content, 'KeyID', '') or ''
            file_path = getattr(content, 'FolderPath', '') or ''
            fp_normalized = file_path.lower().replace('\\', '/')
            
            # 从缓存补充数据
            cached = cache_by_path.get(fp_normalized, {})
            if not bpm or bpm <= 0:
                bpm = cached.get('bpm', 0)
            if not key:
                key = cached.get('key', '')
            
            if bpm and bpm > 0:
                tracks.append({
                    'id': content_id,
                    'title': getattr(content, 'Title', 'Unknown'),
                    'artist': getattr(content, 'ArtistName', None) or 'Unknown',
                    'bpm': float(bpm),
                    'key': key,
                    'file_path': file_path,
                    'vocal_ratio': cached.get('vocal_ratio', 0.5),
                    'energy': cached.get('energy', 50)
                })
        except:
            continue
    
    if not tracks:
        print(f"错误: 播放列表 '{playlist_name}' 中没有可用的歌曲")
        return []
    
    print(f"=> 已加载 {len(tracks)} 首歌曲")
    print()
    
    # 2. 搜索匹配对
    print("[2/3] 搜索Stems混搭组合...")
    
    # 实例化统一评分模型
    from skills.mashup_intelligence.scripts.core import MashupIntelligence
    
    candidates = []
    total_pairs = len(tracks) * (len(tracks) - 1) // 2
    checked = 0
    
    for i, track1 in enumerate(tracks):
        for j, track2 in enumerate(tracks[i+1:], i+1):
            checked += 1
            if checked % 500 == 0:
                print(f"   已检查 {checked}/{total_pairs} 对...")
            
            score, details = mi.calculate_mashup_score(track1, track2)

            
            if score >= min_score:
                candidates.append({
                    'track1': track1,
                    'track2': track2,
                    'score': score,
                    'details': details,
                    'mashup_type': details.get('mashup_type', '标准Stems混搭'),
                    'mi_instance': mi # 供后续生成指南使用
                })
    
    print(f"=> 找到 {len(candidates)} 个高质量匹配对")
    
    # 3. 排序并返回
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates[:max_results]


# 已整合至 MashupIntelligence 类中，删除冗余函数



# 已整合至 MashupIntelligence 类中，删除冗余函数



def save_stems_results(candidates, output_file="stems_mashup_results.txt"):
    """保存Stems搜索结果"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("Rekordbox Stems Mashup搜索结果\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"找到 {len(candidates)} 个推荐组合\n\n")
        
        for i, candidate in enumerate(candidates, 1):
            track1 = candidate['track1']
            track2 = candidate['track2']
            score = candidate['score']
            mashup_type = candidate['mashup_type']
            details = candidate['details']
            
            f.write(f"\n推荐组合 #{i} - 评分: {score:.1f}/100\n")
            f.write(f"混搭类型: {mashup_type}\n")
            f.write("=" * 60 + "\n\n")
            
            # 歌曲信息（使用优化的调性显示）
            try:
                from export_set_to_csv import format_key_display
                key1_display = format_key_display(track1.get('key', '未知'))
                key2_display = format_key_display(track2.get('key', '未知'))
            except:
                key1_display = track1.get('key', '未知')
                key2_display = track2.get('key', '未知')
            
            f.write(f"歌曲A: {track1.get('artist', 'Unknown')} - {track1.get('title', 'Unknown')}\n")
            f.write(f"  BPM: {track1.get('bpm', 0):.1f} | 调性: {key1_display}\n\n")
            
            f.write(f"歌曲B: {track2.get('artist', 'Unknown')} - {track2.get('title', 'Unknown')}\n")
            f.write(f"  BPM: {track2.get('bpm', 0):.1f} | 调性: {key2_display}\n\n")
            
            # 匹配分析
            f.write("匹配分析:\n")
            f.write(f"  BPM: {details.get('bpm_status', 'N/A')}\n")
            f.write(f"  调性: {details.get('key_status', 'N/A')}\n")
            f.write(f"  人声: {details.get('vocal_status', 'N/A')}\n")
            f.write(f"  能量: {details.get('energy_status', 'N/A')}\n\n")
            
            # 使用统一模型生成操作指导
            mi = candidate.get('mi_instance')
            if mi:
                guide = mi.generate_unified_guide(track1, track2, score, details)
                for line in guide:
                    f.write(f"{line}\n")
            
            # 列出具体维度分析
            f.write("\n维度分析:\n")
            for dim, desc in details.items():
                if dim != 'mashup_pattern':
                    f.write(f"  - {dim.upper()}: {desc}\n")

            
            f.write("\n")
    
    print(f"=> 结果已保存到: {output_file}")


# Stems功能已集成到文末的main函数中

if __name__ == "__main__":
    # 检查是否是Stems搜索模式
    if len(sys.argv) > 1 and sys.argv[1] == "--stems":
        # Stems搜索模式
        if len(sys.argv) < 3:
            print("用法: python enhanced_harmonic_set_sorter.py --stems <播放列表名称> [最低分数]")
            print("示例: python enhanced_harmonic_set_sorter.py --stems 华语 75")
            sys.exit(1)
        
        playlist_name = sys.argv[2]
        min_score = float(sys.argv[3]) if len(sys.argv) > 3 else 75.0
        
        print(f"搜索播放列表: {playlist_name}")
        print(f"最低分数: {min_score}")
        print()
        
        candidates = find_stems_mashup_pairs(playlist_name, min_score)
        
        if candidates:
            save_stems_results(candidates)
            print()
            print("🎉 Stems搜索完成！")
            print(f"找到 {len(candidates)} 个推荐组合")
            print("详细指导已保存到: stems_mashup_results.txt")
            print()
            print("使用方法:")
            print("1. 打开Rekordbox")
            print("2. 按照文件中的指导操作")
            print("3. 享受你的Mashup创作！")
        else:
            print("❌ 未找到合适的组合")
            print("建议降低最低分数重试")
    else:
        # 原有的排Set功能
        parser.add_argument('playlist', nargs='?', default='default',
                           help='播放列表名称 (或使用 artist:Name / search:Query 直接搜索)')
        
        # [V6.3] Explicit Search Arguments
        parser.add_argument('--artist', type=str, help='[V6.3] 按照艺人搜索生成 Set')
        parser.add_argument('--query', type=str, help='[V6.3] 按照关键词搜索生成 Set')
        # 【Phase 8】浮动分割：支持按时长浮动，不固定首数
        parser.add_argument('--songs-per-set', type=int, default=None,
                           help='每个Set的歌曲数量（可选，不指定则使用配置文件的浮动规则: 25-40首）')
        parser.add_argument('--preset', type=str, default='default',
                           choices=['club', 'radio', 'warm_up', 'extended', 'default'],
                           help='Set预设类型（club=60min, radio=45min, warm_up=90min, extended=120min）')
        parser.add_argument('--bridge', action='store_true',
                           help='启用桥接模式：从曲库补充同风格歌曲（仅限电子乐风格）')
        parser.add_argument('--boutique', action='store_true',
                           help='精品单体Set模式：不分Set，追求极致平滑过渡，严格限制BPM和调性跳跃')
        parser.add_argument('--master', action='store_true',
                           help='Master总线模式：全局连贯排序，在最优点智能切分Set，并导出统一的Master M3U/XML')
        parser.add_argument('--live', action='store_true',
                           help='直播长Set模式：完整度优先，确保所有歌曲都排进去，无法和谐衔接的歌曲放在Set末尾')
        parser.add_argument('--theme', type=str, default='',
                           help='[Intelligence-V5] 设定 Set 的叙事主题（如：“探索 Y2K 怀旧背景下的女团力量”）')
        
        args = parser.parse_args()
        
        # 【Phase 12】应用叙事主题 [Intelligence-V5]
        if args.theme and NARRATIVE_ENABLED:
            NARRATIVE_PLANNER.set_theme(args.theme)
        
        # 【Phase 8】获取浮动分割配置
        split_cfg = DJ_RULES.get('split', {}) if DJ_RULES else {}
        
        # 如果用户指定了--songs-per-set，优先使用；否则使用配置文件的浮动范围
        if args.songs_per_set:
            effective_songs_per_set = args.songs_per_set
        else:
            effective_songs_per_set = split_cfg.get('ideal_songs_max', 35)
            print(f"[Phase 8] 使用浮动分割: {split_cfg.get('min_songs', 25)}-{split_cfg.get('max_songs', 40)}首/Set")
            print(f"         目标时长: {split_cfg.get('target_duration_minutes', 90)}分钟")
        
        # 精品模式强制单体Set
        if args.boutique:
            print(f"[Boutique] 已启用精品模式，将应用最严格的调性与BPM平滑规则")
            # 不再强制设置 500 首，因为用户希望遵循专业 Set 长度 (25-40首)
            # 如果歌曲较多，应配合 --master 使用智能切分
            if not args.master:
                # 提示用户大歌单建议自动开启智能切分逻辑
                pass 
        
        # [V6.3] Construct effective target name
        target_name = args.playlist
        if args.artist:
            target_name = f"artist:{args.artist}"
        elif args.query:
            target_name = f"search:{args.query}"
            
        asyncio.run(create_enhanced_harmonic_sets(
            playlist_name=target_name,
            songs_per_set=effective_songs_per_set,
            enable_bridge=args.bridge,
            is_boutique=args.boutique,
            is_master=args.master,
            is_live=args.live
        ))
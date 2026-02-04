"""
增强版专业DJ Set排序工具 (V35.21 / V32.0 DSP Core)
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
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / 'core'))
sys.path.insert(0, str(BASE_DIR / 'skills'))
sys.path.insert(0, str(BASE_DIR / 'core' / 'rekordbox-mcp'))
from rekordbox_mcp.models import SearchOptions
from exporters.xml_exporter import export_to_rekordbox_xml

def get_audio_inspector_data(file_path: str) -> Optional[Dict]:
    """使用 mcp-audio-inspector 获取音频元数据 (Node.js)"""
    inspector_path = BASE_DIR / 'mcp-audio-inspector' / 'index.js'
    if not inspector_path.exists():
        return None
    try:
        result = subprocess.run(['node', inspector_path, '--standalone', file_path], capture_output=True, text=True, encoding='utf-8', check=False)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass
    return None
sys.path.insert(0, str(Path(__file__).parent / 'rekordbox-mcp'))
try:
    from rekordbox_mcp.database import RekordboxDatabase
    from rekordbox_mcp.models import SearchOptions
except ImportError as e:
    print(f'导入错误: {e}')

    class RekordboxDatabase:
        pass

    class SearchOptions:
        pass
try:
    from pyrekordbox import Rekordbox6Database
    from sqlalchemy import text
except ImportError as e:
    print(f'导入错误: {e}')
    sys.exit(1)
try:
    from strict_bpm_multi_set_sorter import deep_analyze_track
except:

    def deep_analyze_track(file_path, db_bpm=None):
        return None
try:
    from conflict_monitor_overlay import generate_radar_report
except ImportError:

    def generate_radar_report(tracks):
        return '无法生成雷达报告'
try:
    from skills.cueing_intelligence.scripts.vocal import check_vocal_overlap_at_mix_point, get_recommended_mix_points_avoiding_vocals
    VOCAL_DETECTION_ENABLED = True
except ImportError:
    VOCAL_DETECTION_ENABLED = False

    def check_vocal_overlap_at_mix_point(*args, **kwargs):
        return (0.0, '未安装')

    def get_recommended_mix_points_avoiding_vocals(*args, **kwargs):
        return (None, None, '未安装')
try:
    from skills.rhythmic_energy.scripts.phrase import check_phrase_alignment, suggest_better_phrase_aligned_point, validate_energy_curve, suggest_energy_reorder
    PHRASE_ENERGY_ENABLED = True
except ImportError:
    PHRASE_ENERGY_ENABLED = False

    def check_phrase_alignment(*args, **kwargs):
        return (0.0, '未安装')

    def suggest_better_phrase_aligned_point(*args, **kwargs):
        return (None, '未安装')

    def validate_energy_curve(*args, **kwargs):
        return (True, [])

    def suggest_energy_reorder(tracks):
        return tracks
try:
    from skills.rhythmic_energy.scripts.bpm import validate_bpm_progression, suggest_bpm_reorder, get_bpm_curve_summary
    BPM_PROGRESSIVE_ENABLED = True
except ImportError:
    BPM_PROGRESSIVE_ENABLED = False

    def validate_bpm_progression(*args, **kwargs):
        return (True, [])

    def suggest_bpm_reorder(tracks, phase='auto'):
        return tracks

    def get_bpm_curve_summary(tracks):
        return {}
try:
    from skills.aesthetic_expert.scripts.audit import calculate_set_completeness, get_energy_curve_summary
    PROFESSIONAL_AUDIT_ENABLED = True
except ImportError:
    PROFESSIONAL_AUDIT_ENABLED = False

    def calculate_set_completeness(*args, **kwargs):
        return {'total_score': 0, 'breakdown': {}}

    def get_energy_curve_summary(*args, **kwargs):
        return 'N/A'
try:
    from auto_hotcue_generator import generate_hotcues, hotcues_to_rekordbox_format
    HOTCUE_GENERATOR_ENABLED = True
except ImportError:
    HOTCUE_GENERATOR_ENABLED = False

    def generate_hotcues(*args, **kwargs):
        return {}

    def hotcues_to_rekordbox_format(*args, **kwargs):
        return {}
try:
    from rekordbox_phrase_reader import RekordboxPhraseReader
    PHRASE_READER = RekordboxPhraseReader()
    PHRASE_READER_AVAILABLE = True
except ImportError:
    PHRASE_READER_AVAILABLE = False
    PHRASE_READER = None
try:
    from skills.mashup_intelligence.scripts.core import MashupIntelligence
    MASHUP_INTELLIGENCE = MashupIntelligence()
    MASHUP_ENABLED = True
    print(f'[OK] 已成功挂载 Mashup Intelligence V4 微观引擎')
except ImportError:
    MASHUP_ENABLED = False

    class MashupIntelligence:

        def calculate_mashup_score(self, *args, **kwargs):
            return (0.0, {})
    MASHUP_INTELLIGENCE = MashupIntelligence()
    print(f'[WARN] 无法挂载 Mashup Intelligence，微观评分已降级')
try:
    from skills.aesthetic_expert.scripts.curator import AestheticCurator
    AESTHETIC_CURATOR = AestheticCurator()
    AESTHETIC_ENABLED = True
    print(f'[OK] 已成功挂载 Aesthetic Curator V4 审美引擎')
except ImportError:
    AESTHETIC_ENABLED = False

    class AestheticCurator:

        def calculate_aesthetic_match(self, *args, **kwargs):
            return (70.0, {})

        def get_mix_bible_advice(self, *args, **kwargs):
            return {'technique': 'Standard Mix', 'suggested_duration': '16 bars', 'vibe_target': 'Neutral'}
    AESTHETIC_CURATOR = AestheticCurator()
    print(f'[WARN] 无法挂载 Aesthetic Curator，审美评分已降级')
try:
    from narrative_set_planner import NarrativePlanner
    from skill_intelligence_researcher import IntelligenceResearcher
    RESEARCHER = IntelligenceResearcher()
    NARRATIVE_PLANNER = NarrativePlanner(researcher=RESEARCHER)
    NARRATIVE_ENABLED = True
    print(f'[OK] 已成功挂载 Narrative Planner V5 & Intelligence Researcher')
except ImportError:
    try:
        from skills.skill_intelligence_researcher import IntelligenceResearcher
        from narrative_set_planner import NarrativePlanner
        RESEARCHER = IntelligenceResearcher()
        NARRATIVE_PLANNER = NarrativePlanner(researcher=RESEARCHER)
        NARRATIVE_ENABLED = True
        print(f'[OK] 已成功挂载 Narrative Planner V5 (from skills)')
    except ImportError:
        NARRATIVE_ENABLED = False

        class NarrativePlanner:

            def calculate_narrative_score(self, *args, **kwargs):
                return (0.0, {})

            def get_narrative_advice(self, *args, **kwargs):
                return ''

            def set_theme(self, theme):
                pass
        NARRATIVE_PLANNER = NarrativePlanner()
        RESEARCHER = None
        print(f'[WARN] 无法挂载 Narrative Planner，叙事匹配已停用')
try:
    from blueprinter import SetBlueprinter
    BLUEPRINTER = SetBlueprinter()
    BLUEPRINT_ENABLED = True
    print(f'[OK] 已成功挂载 Set Blueprinter V5 蓝图引擎')
except ImportError:
    try:
        from skills.set_curation_expert.scripts.blueprinter import SetBlueprinter
        BLUEPRINTER = SetBlueprinter()
        BLUEPRINT_ENABLED = True
        print(f'[OK] 已成功挂载 Set Blueprinter V5 (from skills)')
    except ImportError:
        BLUEPRINT_ENABLED = False

        class SetBlueprinter:

            def get_phase_target(self, progress):
                return (40, 70, 'General', {})
        BLUEPRINTER = SetBlueprinter()
        print(f'[WARN] 无法挂载 Set Blueprinter，将使用硬编码阶段')
try:
    from core.cache_manager import DEFAULT_CACHE_PATH
    CACHE_FILE = Path(DEFAULT_CACHE_PATH)
except ImportError:
    CACHE_FILE = Path(__file__).parent / 'song_analysis_cache.json'
ANALYZER_VERSION = 'v1.2-pro-dimensions'
DEFAULT_MODEL_VERSIONS = {'genre': 'g1.0', 'key': 'k1.0', 'bpm': 'b1.0', 'energy': 'e1.0', 'vocal': 'v1.0'}
try:
    import evolution_config
    ACTIVE_PROFILE = evolution_config.PROFILES[evolution_config.DEFAULT_PROFILE]
except Exception as e:
    print(f'警告: 无法加载进化配置，将使用默认权重: {e}')
    ACTIVE_PROFILE = None
try:
    from config.split_config import get_config
    DJ_RULES = get_config()
    print(f'[OK] 已加载 dj_rules.yaml 配置'.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
except Exception as e:
    print(f'警告: 无法加载 dj_rules.yaml，将使用默认值: {e}')
    DJ_RULES = {}
try:
    from global_optimization_engine import optimize_global_sets
except ImportError:

    def optimize_global_sets(sets, config, progress_logger=None):
        return 0

def _lock_file_handle(f):
    """跨平台文件锁（简单独占锁），避免并发写坏缓存"""
    try:
        if os.name == 'nt':
            import msvcrt
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
            except OSError:
                f.seek(0, os.SEEK_END)
                if f.tell() == 0:
                    f.write('\x00')
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
        if os.name == 'nt':
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
    if 'r' in mode and (not path.exists()):
        yield None
        return
    f = open(path, mode, encoding='utf-8')
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

    def verify_file_exists(p):
        return os.path.exists(p)

def load_cache():
    """加载分析缓存（加文件锁，避免并发读取/写入冲突）"""
    try:
        if not CACHE_FILE.exists():
            return {}
        with _locked_file(CACHE_FILE, 'r') as f:
            if f is None:
                return {}
            data = json.load(f)
            return data
    except Exception:
        return {}

def save_cache_atomic(cache_data, cache_file):
    """原子性保存缓存，防止并发写入损坏文件"""
    import tempfile
    cache_path = Path(cache_file)
    temp_fd, temp_path = tempfile.mkstemp(dir=cache_path.parent, suffix='.tmp')
    try:
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
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
        sanitized = make_json_serializable(cache)
        save_cache_atomic(sanitized, CACHE_FILE)
    except Exception as e:
        print(f'❌ 缓存保存失败: {e}')

def get_cached_analysis(file_path: str, cache: dict):
    """从缓存获取分析结果（极致兼容）"""
    if not file_path:
        return None
    file_path_str = str(file_path).replace('\\', '/')
    file_hash = get_file_hash(file_path_str)
    if file_hash and file_hash in cache:
        cached = cache[file_hash]
        if isinstance(cached, dict):
            return cached.get('analysis')
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
        return (False, False)
    if file_path_str:
        cached_path = cached.get('file_path', '').replace('\\', '/')
        if cached_path != file_path_str:
            return (False, False)
    analyzer_ver = cached.get('analyzer_version')
    if analyzer_ver == ANALYZER_VERSION:
        analysis = cached.get('analysis', {})
        if 'language' in analysis and 'kick_hardness' in analysis and ('true_start_sec' in analysis):
            return (True, False)
        else:
            return (True, True)
    if analyzer_ver == 'v1.1-cachekey-mixability-prep' or analyzer_ver is None:
        return (True, True)
    return (False, False)

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
        return (False, 'entry_missing')
    analyzer_ver = cached_entry.get('analyzer_version')
    if analyzer_ver != ANALYZER_VERSION:
        return (False, f'analyzer_version_mismatch:{analyzer_ver}')
    cached_model_versions = cached_entry.get('model_versions', {})
    if cached_model_versions:
        for key in ['genre', 'key', 'bpm']:
            if key in DEFAULT_MODEL_VERSIONS:
                if cached_model_versions.get(key) != DEFAULT_MODEL_VERSIONS[key]:
                    return (False, f'model_version_mismatch:{key}')
    if file_path_str:
        cached_path = cached_entry.get('file_path', '').replace('\\', '/')
        if cached_path != file_path_str.replace('\\', '/'):
            return (False, 'path_mismatch')
        cached_mtime = cached_entry.get('mtime')
        cached_size = cached_entry.get('size')
        if cached_mtime is not None and cached_size is not None:
            try:
                stat = os.stat(file_path_str)
                if stat.st_mtime != cached_mtime:
                    return (False, 'mtime_mismatch')
                if stat.st_size != cached_size:
                    return (False, 'size_mismatch')
            except OSError:
                pass
    return (True, 'valid')

def get_file_hash(file_path):
    """获取文件的唯一标识（路径+修改时间）"""
    try:
        file_path_str = str(file_path).replace('\\', '/').lower()
        stat = os.stat(file_path_str)
        key_base = f'{file_path_str}|{stat.st_mtime_ns}|{stat.st_size}'
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
            cache[file_hash] = {'file_path': file_path_str, 'mtime': stat.st_mtime, 'size': stat.st_size, 'analyzer_version': ANALYZER_VERSION, 'model_versions': DEFAULT_MODEL_VERSIONS, 'analysis': make_json_serializable(analysis), 'timestamp': datetime.now().isoformat(), 'artist': analysis.get('artist', 'Unknown'), 'title': analysis.get('title', 'Unknown'), 'bpm': analysis.get('bpm', 120.0)}
            save_cache(cache)
        except Exception as e:
            print(f'Warning: Failed to cache analysis for {file_path_str}: {e}')
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
        return '未知'
    if isinstance(open_key, (int, float)):
        return '未知'
    if not isinstance(open_key, str):
        try:
            open_key = str(open_key)
        except Exception:
            return '未知'
    open_key = open_key.strip()
    if not open_key or open_key == '未知':
        return '未知'
    if open_key.isdigit() and len(open_key) >= 3:
        return '未知'
    if len(open_key) >= 2 and open_key[-1] in ['A', 'B']:
        try:
            int(open_key[:-1])
            return open_key
        except ValueError:
            pass
    try:
        if open_key.endswith('m'):
            num = int(open_key[:-1])
            if 1 <= num <= 12:
                return f'{num}A'
        elif open_key.endswith('d'):
            num = int(open_key[:-1])
            if 1 <= num <= 12:
                return f'{num}B'
    except (ValueError, IndexError):
        pass
    return '未知'

def detect_key_system(key: str) -> str:
    """
    检测调性系统类型
    
    Returns:
        str: "camelot", "open_key", "unknown"
    """
    if not key or key == '未知':
        return 'unknown'
    if len(key) >= 2 and (key.endswith('m') or key.endswith('d')):
        try:
            num = int(key[:-1])
            if 1 <= num <= 12:
                return 'open_key'
        except ValueError:
            pass
    if len(key) >= 2 and key[-1] in ['A', 'B']:
        try:
            num = int(key[:-1])
            if 1 <= num <= 12:
                return 'camelot'
        except ValueError:
            pass
    return 'unknown'

def auto_group_by_bpm(tracks: List[Dict], max_bpm_range: float=25.0) -> List[List[Dict]]:
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
    tracks_with_bpm = [t for t in tracks if t.get('bpm') and t.get('bpm') > 0]
    tracks_without_bpm = [t for t in tracks if not t.get('bpm') or t.get('bpm') <= 0]
    if not tracks_with_bpm:
        return [tracks] if tracks else []
    sorted_tracks = sorted(tracks_with_bpm, key=lambda t: t.get('bpm', 0))
    groups = []
    current_group = [sorted_tracks[0]]
    group_min_bpm = sorted_tracks[0].get('bpm', 0)
    for track in sorted_tracks[1:]:
        track_bpm = track.get('bpm', 0)
        if track_bpm - group_min_bpm > max_bpm_range:
            groups.append(current_group)
            current_group = [track]
            group_min_bpm = track_bpm
        else:
            current_group.append(track)
    if current_group:
        groups.append(current_group)
    if tracks_without_bpm:
        mid_group_idx = 0
        for i, group in enumerate(groups):
            avg_bpm = sum((t.get('bpm', 0) for t in group)) / len(group)
            if 100 <= avg_bpm <= 130:
                mid_group_idx = i
                break
        groups[mid_group_idx].extend(tracks_without_bpm)
    merged_groups = []
    for group in groups:
        if len(group) < 5 and merged_groups:
            prev_bpms = [t.get('bpm', 0) for t in merged_groups[-1] if t.get('bpm')]
            curr_bpms = [t.get('bpm', 0) for t in group if t.get('bpm')]
            if prev_bpms and curr_bpms:
                bpm_gap = min(curr_bpms) - max(prev_bpms)
                if bpm_gap <= 15:
                    merged_groups[-1].extend(group)
                    continue
            else:
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
    bpms = [t.get('bpm', 0) for t in tracks if t.get('bpm')]
    if not bpms:
        return tracks
    median_bpm = sorted(bpms)[len(bpms) // 2]
    start_track = min(tracks, key=lambda t: abs(t.get('bpm', 0) - median_bpm))
    result = [start_track]
    remaining = [t for t in tracks if t != start_track]
    while remaining:
        current = result[-1]
        current_bpm = current.get('bpm', 0)
        current_key = current.get('key', '')
        best_track = None
        best_score = float('inf')
        for track in remaining:
            track_bpm = track.get('bpm', 0)
            track_key = track.get('key', '')
            bpm_diff = abs(track_bpm - current_bpm)
            key_score = get_key_compatibility_flexible(current_key, track_key)
            key_penalty = (100 - key_score) / 10
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
        return 'Empty'
    bpms = [t.get('bpm', 0) for t in group if t.get('bpm')]
    if not bpms:
        return 'Unknown BPM'
    min_bpm = min(bpms)
    max_bpm = max(bpms)
    avg_bpm = sum(bpms) / len(bpms)
    if avg_bpm < 90:
        tempo_label = '慢歌'
    elif avg_bpm < 115:
        tempo_label = '中慢速'
    elif avg_bpm < 130:
        tempo_label = '中速'
    elif avg_bpm < 145:
        tempo_label = '中快速'
    elif avg_bpm < 165:
        tempo_label = '快歌'
    else:
        tempo_label = '超快'
    return f'{tempo_label} ({min_bpm:.0f}-{max_bpm:.0f} BPM)'

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
    if not current_key or current_key == '未知' or (not next_key) or (next_key == '未知'):
        return 50
    current_key = convert_open_key_to_camelot(current_key)
    next_key = convert_open_key_to_camelot(next_key)
    try:
        curr_num = int(current_key[:-1])
        curr_letter = current_key[-1]
        next_num = int(next_key[:-1])
        next_letter = next_key[-1]
        if current_key == next_key:
            return 100
        if curr_num == next_num and curr_letter != next_letter:
            return 100

        def circle_distance(a, b):
            """计算Camelot轮盘上的5度圈距离（考虑循环）"""
            direct = abs(a - b)
            wrap = 12 - direct
            return min(direct, wrap)
        diff = circle_distance(curr_num, next_num)
        if diff == 1:
            if curr_letter == next_letter:
                return 95
            else:
                return 85
        if diff == 2:
            if curr_letter == next_letter:
                return 85
            else:
                return 75
        if diff <= 4:
            if curr_letter == next_letter:
                return 70
            else:
                return 60
        if diff == 5:
            if curr_letter == next_letter:
                return 45
            else:
                return 35
        if diff == 6:
            if curr_letter == next_letter:
                return 30
            else:
                return 20
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
        return 100
    elif diff <= 4:
        return 90
    elif diff <= 6:
        return 80
    elif diff <= 8:
        return 70
    elif diff <= 12:
        return 60
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
    profile_a = track_a.get('energy_profile', {})
    profile_b = track_b.get('energy_profile', {})
    std_a = profile_a.get('onset_std', None)
    std_b = profile_b.get('onset_std', None)
    if std_a is None or std_b is None:
        return 0.5
    std_diff = abs(std_a - std_b)
    similarity = 1.0 - min(std_diff, 1.0)
    return similarity

def optimize_mix_points_with_windows(current_track: dict, next_track: dict) -> Tuple[float, float]:
    """
    【P1优化】使用mixable_windows优化混音点选择
    
    Returns:
        (optimized_mix_out, optimized_mix_in)
    """
    curr_mix_out = current_track.get('mix_out_point')
    next_mix_in = next_track.get('mix_in_point')
    curr_windows = current_track.get('mixable_windows', [])
    next_windows = next_track.get('mixable_windows', [])
    if not curr_windows or not next_windows:
        return (curr_mix_out, next_mix_in)
    try:
        best_mix_out = curr_mix_out
        best_out_score = 0
        for window in curr_windows:
            if len(window) >= 3:
                start, end, quality = (window[0], window[1], window[2])
                if curr_mix_out:
                    distance = abs((start + end) / 2 - curr_mix_out)
                    score = quality / (1 + distance / 10)
                    if score > best_out_score:
                        best_out_score = score
                        best_mix_out = (start + end) / 2
        best_mix_in = next_mix_in
        best_in_score = 0
        for window in next_windows:
            if len(window) >= 3:
                start, end, quality = (window[0], window[1], window[2])
                if next_mix_in is not None:
                    distance = abs((start + end) / 2 - next_mix_in)
                    score = quality / (1 + distance / 10)
                    if score > best_in_score:
                        best_in_score = score
                        best_mix_in = (start + end) / 2
        return (best_mix_out, best_mix_in)
    except Exception:
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
    curr_beat_offset = current_track.get('downbeat_offset', 0)
    next_beat_offset = next_track.get('downbeat_offset', 0)
    curr_duration = current_track.get('duration', 0)
    curr_mix_out = current_track.get('mix_out_point', curr_duration * 0.85)
    next_mix_in = next_track.get('mix_in_point', 0)
    curr_time_sig = current_track.get('time_signature', '4/4')
    next_time_sig = next_track.get('time_signature', '4/4')
    curr_beats_per_bar = current_track.get('beats_per_bar', 4)
    next_beats_per_bar = next_track.get('beats_per_bar', 4)
    if curr_bpm <= 0 or next_bpm <= 0 or curr_duration <= 0:
        return (0.0, 50.0)

    def _normalize_offset(track_offset, bpm):
        if track_offset is None:
            return None
        offset_val = float(track_offset)
        if abs(offset_val) < 5.0 and bpm > 0:
            return offset_val * float(bpm) / 60.0
        return offset_val
    curr_off_beats = _normalize_offset(curr_beat_offset, curr_bpm)
    next_off_beats = _normalize_offset(next_beat_offset, next_bpm)
    bpm_diff = abs(curr_bpm - next_bpm)
    if bpm_diff > 5:
        return (999.0, 0.0)
    if curr_time_sig != next_time_sig:
        pass
    curr_mix_out_time = curr_mix_out
    next_mix_in_time = next_mix_in
    if curr_off_beats is not None and curr_off_beats != 0:
        curr_beat_time = curr_off_beats % curr_beats_per_bar * (60.0 / curr_bpm)
        curr_mix_out_beat_offset = (curr_mix_out_time - curr_beat_time) % (60.0 / curr_bpm)
    else:
        curr_mix_out_beat_offset = curr_mix_out_time % (60.0 / curr_bpm)
    if next_off_beats is not None and next_off_beats != 0:
        next_beat_time = next_off_beats % next_beats_per_bar * (60.0 / next_bpm)
        next_mix_in_beat_offset = (next_mix_in_time - next_beat_time) % (60.0 / next_bpm)
    else:
        next_mix_in_beat_offset = next_mix_in_time % (60.0 / next_bpm)
    curr_beats = curr_mix_out_beat_offset / (60.0 / curr_bpm)
    next_beats = next_mix_in_beat_offset / (60.0 / next_bpm)
    beat_offset_diff = abs(curr_beats - next_beats)
    if curr_time_sig != next_time_sig:
        beat_offset_diff *= 1.2
    if beat_offset_diff <= 0.5:
        alignment_score = 100.0
    elif beat_offset_diff <= 1.0:
        alignment_score = 90.0
    elif beat_offset_diff <= 2.0:
        alignment_score = 70.0
    elif beat_offset_diff <= 4.0:
        alignment_score = 40.0
    else:
        alignment_score = 0.0
    beatgrid_fix_hints = {}
    needs_manual_alignment = False
    try:
        from beatgrid_fix_helper import calculate_phase_shift_correction
        fix_result = calculate_phase_shift_correction(current_track, next_track)
        if fix_result.get('needs_manual_alignment'):
            needs_manual_alignment = True
        current_fix = fix_result.get('current_track_fix', {})
        next_fix = fix_result.get('next_track_fix', {})
        if current_fix.get('hint_text'):
            beatgrid_fix_hints['current'] = current_fix['hint_text']
        if next_fix.get('hint_text'):
            beatgrid_fix_hints['next'] = next_fix['hint_text']
        if fix_result.get('recommendation'):
            beatgrid_fix_hints['recommendation'] = fix_result['recommendation']
    except ImportError:
        pass
    except Exception:
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
        return (0.0, 50.0)
    bpm_diff = abs(curr_bpm - next_bpm)
    if bpm_diff > 5:
        return (999.0, 0.0)
    if curr_first_drop is None:
        curr_first_drop = curr_duration * 0.35
    if next_first_drop is None:
        next_first_drop = next_track.get('duration', 180) * 0.35
    curr_drop_distance = curr_first_drop - curr_mix_out
    next_drop_distance = next_first_drop - next_mix_in
    curr_beats = curr_drop_distance / (60.0 / curr_bpm)
    next_beats = next_drop_distance / (60.0 / next_bpm)
    drop_offset_diff = abs(curr_beats - next_beats)
    if drop_offset_diff <= 4.0:
        alignment_score = 100.0
    elif drop_offset_diff <= 8.0:
        alignment_score = 80.0
    elif drop_offset_diff <= 16.0:
        alignment_score = 60.0
    elif drop_offset_diff <= 32.0:
        alignment_score = 30.0
    else:
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
    profile_a = track_a.get('energy_profile') or {}
    profile_b = track_b.get('energy_profile') or {}
    mfcc_a = profile_a.get('mfcc_mean', None) if isinstance(profile_a, dict) else None
    mfcc_b = profile_b.get('mfcc_mean', None) if isinstance(profile_b, dict) else None
    if mfcc_a is None or mfcc_b is None:
        return 0.5
    try:
        mfcc_a = np.array(mfcc_a)
        mfcc_b = np.array(mfcc_b)
        if mfcc_a.shape != mfcc_b.shape:
            return 0.5
        dot_product = np.dot(mfcc_a, mfcc_b)
        norm_a = np.linalg.norm(mfcc_a)
        norm_b = np.linalg.norm(mfcc_b)
        if norm_a == 0 or norm_b == 0:
            return 0.5
        similarity = dot_product / (norm_a * norm_b)
        similarity = max(0.0, min(1.0, similarity))
        return float(similarity)
    except Exception:
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
        return (0, False)
    curr_duration = current_track.get('duration', 0)
    next_duration = next_track.get('duration', 0)
    if curr_duration == 0 or next_duration == 0:
        return (0, False)
    curr_mix_start = curr_duration * 0.7
    next_mix_end = next_duration * 0.3
    overlap_ratio = calculate_vocal_overlap(curr_vocal, next_vocal, curr_mix_start, curr_duration, 0, next_mix_end)
    if overlap_ratio > 0.5:
        return (-30, True)
    elif overlap_ratio > 0.3:
        return (-15, True)
    else:
        return (0, False)

def calculate_vocal_overlap(curr_vocal: List[Tuple[float, float]], next_vocal: List[Tuple[float, float]], curr_start: float, curr_end: float, next_start: float, next_end: float) -> float:
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
    curr_vocal_in_mix = []
    for start, end in curr_vocal:
        if end > curr_start and start < curr_end:
            overlap_start = max(start, curr_start)
            overlap_end = min(end, curr_end)
            curr_vocal_in_mix.append((overlap_start, overlap_end))
    next_vocal_in_mix = []
    for start, end in next_vocal:
        if end > next_start and start < next_end:
            overlap_start = max(start, next_start)
            overlap_end = min(end, next_end)
            next_vocal_in_mix.append((overlap_start, overlap_end))
    if not curr_vocal_in_mix or not next_vocal_in_mix:
        return 0.0
    curr_vocal_duration = sum((end - start for start, end in curr_vocal_in_mix))
    next_vocal_duration = sum((end - start for start, end in next_vocal_in_mix))
    min_vocal_duration = min(curr_vocal_duration, next_vocal_duration)
    if min_vocal_duration == 0:
        return 0.0
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
    phase_map = {'Warm-up': 0, 'Build-up': 1, 'Peak': 2, 'Intense': 3, 'Cool-down': 4}
    return phase_map.get(phase_name, 1)

def check_phase_constraint(current_phase_num: int, candidate_phase_num: int, max_phase_reached: int, in_cool_down: bool) -> tuple:
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
    if in_cool_down:
        if candidate_phase_num < 4:
            return (False, -200)
        return (True, 0)
    if current_phase_num == 3:
        if candidate_phase_num != 4:
            return (False, -150)
        return (True, 0)
    if candidate_phase_num < current_phase_num:
        if max_phase_reached < 2:
            return (True, -30)
        else:
            return (False, -100)
    if candidate_phase_num > max_phase_reached + 1:
        return (True, -20)
    return (True, 0)

def get_energy_phase_target(current_position: float, total_tracks: int, current_bpm: float=None, current_energy: float=None, sorted_tracks: List[Dict]=None, current_track: Dict=None) -> tuple:
    """
    根据当前位置强制分配能量阶段（V5优化：按位置硬分配）
    返回: (min_energy, max_energy, phase_name)
    
    【V5优化】强制按Set位置分配阶段，确保每个Set都有完整的能量曲线
    - 不再依赖歌曲实际能量值，而是强制按位置分配
    - 确保每个Set都有Warm-up → Build-up → Peak → Cooldown结构
    """
    if sorted_tracks is None:
        sorted_tracks = []
    progress = (current_position + 1) / max(total_tracks or 1, 1)
    if BLUEPRINT_ENABLED:
        base_min, base_max, phase_name, _ = BLUEPRINTER.get_phase_target(progress)
    elif progress <= 0.2:
        base_min, base_max, phase_name = (30, 55, 'Warm-up')
    elif progress <= 0.4:
        base_min, base_max, phase_name = (50, 70, 'Build-up')
    elif progress <= 0.75:
        base_min, base_max, phase_name = (65, 85, 'Peak')
    elif progress <= 0.9:
        base_min, base_max, phase_name = (70, 90, 'Sustain')
    else:
        base_min, base_max, phase_name = (45, 70, 'Cool-down')
    if len(sorted_tracks) > 0:
        recent_energies = [t.get('energy') for t in sorted_tracks[-5:] if t.get('energy') is not None]
        avg_recent_energy = sum(recent_energies) / len(recent_energies) if recent_energies else 50
        max_energy_reached = max([t.get('energy') for t in sorted_tracks if t.get('energy') is not None], default=50)
        if (avg_recent_energy or 0) >= 65 and progress > 0.25 and (progress < 0.9) and (phase_name in ['Warm-up', 'Build-up']):
            phase_name = 'Peak'
            base_min, base_max = (65, 85)
        elif (avg_recent_energy or 0) >= 50 and progress > 0.1 and (progress < 0.9) and (phase_name == 'Warm-up'):
            phase_name = 'Build-up'
            base_min, base_max = (50, 70)
        if (max_energy_reached or 0) >= 70 and progress > 0.5 and (progress < 0.9) and (phase_name in ['Warm-up', 'Build-up', 'Peak']):
            if progress > 0.6:
                phase_name = 'Sustain'
                base_min, base_max = (70, 90)
            elif progress > 0.4:
                phase_name = 'Peak'
                base_min, base_max = (65, 85)
        if progress >= 0.9 and (max_energy_reached or 0) < 85:
            phase_name = 'Cool-down'
            base_min, base_max = (45, 70)
    if current_bpm is not None and current_bpm > 0:
        is_fast_song = False
        is_slow_song = False
        if current_bpm > 130:
            is_fast_song = True
        elif current_bpm < 100:
            is_slow_song = True
        elif 100 <= current_bpm <= 130:
            if current_energy is not None and current_energy > 70:
                is_fast_song = True
            elif current_energy is not None and current_energy < 40:
                is_slow_song = True
        if current_track:
            groove_density = current_track.get('groove_density', 0.5)
            perc_ratio = current_track.get('perc_ratio', 0.5)
            if groove_density > 0.6 and perc_ratio > 0.4:
                is_fast_song = True
            elif groove_density < 0.4 and perc_ratio < 0.3:
                is_slow_song = True
        elif sorted_tracks and len(sorted_tracks) > 0:
            current_track_info = None
            for track in sorted_tracks:
                if track.get('bpm', 0) == current_bpm:
                    current_track_info = track
                    break
            if current_track_info:
                groove_density = current_track_info.get('groove_density', 0.5)
                perc_ratio = current_track_info.get('perc_ratio', 0.5)
                if groove_density > 0.6 and perc_ratio > 0.4:
                    is_fast_song = True
                elif groove_density < 0.4 and perc_ratio < 0.3:
                    is_slow_song = True
        if is_fast_song:
            if phase_name == 'Warm-up' and progress > 0.05:
                phase_name = 'Build-up'
                base_min, base_max = (50, 70)
            elif phase_name == 'Cool-down' and progress < 0.95:
                if progress < 0.85:
                    phase_name = 'Intense'
                    base_min, base_max = (70, 90)
        elif is_slow_song:
            if phase_name in ['Peak', 'Intense'] and progress < 0.5:
                phase_name = 'Build-up'
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
    next_bpm = track.get('bpm') or 0
    curr_bpm_safe = current_bpm or 0
    if next_bpm > 0 and curr_bpm_safe > 0:
        bpm_diff = abs(curr_bpm_safe - next_bpm)
        bpm_change = next_bpm - curr_bpm_safe
    else:
        bpm_diff = 999.0
        bpm_change = 0
    score = 0
    metrics = {'bpm_diff': bpm_diff, 'bpm_change': bpm_change, 'key_score': None, 'percussive_diff': None, 'dyn_var_diff': None, 'style_penalty': False, 'rhythm_penalty': False, 'phase_penalty': False, 'missing_profile': False, 'fallback': False, 'beat_offset_diff': None, 'drop_offset_diff': None, 'mi_score': 0.0, 'mi_details': {}, 'ae_score': 70.0, 'ae_details': {}, 'narrative_score': 0.0, 'narrative_details': {}, 'audit_trace': []}

    def add_trace(key, val, impact, msg=''):
        metrics['audit_trace'].append({'dim': key, 'val': val, 'score': impact, 'reason': msg})
    if MASHUP_ENABLED and current_track:
        mi_result = MASHUP_INTELLIGENCE.calculate_mashup_score(current_track, track, mode='set_sorting')
        mi_score = mi_result[0] if mi_result and mi_result[0] is not None else 0.0
        mi_details = mi_result[1] if mi_result and len(mi_result) > 1 else {}
        metrics['mi_score'] = mi_score
        metrics['mi_details'] = mi_details
        score += mi_score * 0.3
        if 'bass_clash' in mi_details:
            add_trace('Spectral Masking', 'Bass Clash', -50, mi_details['bass_clash'])
        if mi_score < 40 and (not is_boutique):
            score -= 50
        elif mi_score < 30:
            score -= 150
    if AESTHETIC_ENABLED and current_track:
        ae_score, ae_details = AESTHETIC_CURATOR.calculate_aesthetic_match(current_track, track)
        metrics['ae_score'] = ae_score
        metrics['ae_details'] = ae_details
        pass
    if NARRATIVE_ENABLED and current_track:
        nr_score, nr_details = NARRATIVE_PLANNER.calculate_narrative_score(current_track, track)
        metrics['narrative_score'] = nr_score
        metrics['narrative_details'] = nr_details
        pass
    bpm_weight = 1.0
    if ACTIVE_PROFILE:
        bpm_weight = ACTIVE_PROFILE.weights.get('bpm_match', 100) / 100.0
    if is_boutique:
        if bpm_diff > 8.0:
            return (-500000, track, {'boutique_rejected': 'bpm_delta_too_high'})
        key_score_pre = get_key_compatibility_flexible(current_track.get('key', ''), track.get('key', ''))
        if key_score_pre < 80:
            return (-400000, track, {'boutique_rejected': 'key_incompatible'})
        if track.get('energy', 50) > current_track.get('energy', 50) + 30:
            return (-300000, track, {'boutique_rejected': 'energy_jump_too_high'})
    current_ts = current_track.get('time_signature', '4/4')
    next_ts = track.get('time_signature', '4/4')
    if current_ts != next_ts:
        score -= 500
        metrics['meter_clash'] = f'{current_ts} vs {next_ts}'
        add_trace('Meter Compatibility', 0, -500, f'拍号冲突: {current_ts} 接 {next_ts}')
        if is_boutique:
            return (-600000, track, {'boutique_rejected': 'meter_clash'})
    else:
        add_trace('Meter Compatibility', 100, 0, f'拍号一致: {current_ts}')
    curr_swing = current_track.get('swing_dna', 0.0)
    next_swing = track.get('swing_dna', 0.0)
    swing_diff = abs(curr_swing - next_swing)
    swing_score_impact = 0
    if swing_diff is not None:
        if swing_diff < 0.15:
            swing_score_impact = 20
            score += swing_score_impact
        elif swing_diff > 0.4:
            swing_score_impact = -40
            score += swing_score_impact
        add_trace('Groove Consistency', f'diff:{swing_diff:.2f}', swing_score_impact, f'Swing DNA 匹配度')
    if bpm_diff <= 2:
        score += 100 * bpm_weight
    elif bpm_diff <= 4:
        if bpm_change > 0:
            score += 90 * bpm_weight
        elif bpm_change == 0:
            score += 85 * bpm_weight
        else:
            score += 60 * bpm_weight
    elif bpm_diff <= 6:
        if bpm_change > 0:
            score += 70 * bpm_weight
        elif bpm_change == 0:
            score += 50 * bpm_weight
        else:
            score += 20 * bpm_weight
    elif bpm_diff <= 8:
        if bpm_change > 0:
            score += 50 * bpm_weight
        elif bpm_change == 0:
            score += 30 * bpm_weight
        else:
            score -= 20 * bpm_weight
    elif bpm_diff <= 10:
        if bpm_change > 0:
            score += 30 * bpm_weight
        elif bpm_change == 0:
            score += 10 * bpm_weight
        else:
            score -= 60 * bpm_weight
    elif bpm_diff <= 12:
        if bpm_change > 0:
            score += 10 * bpm_weight
        else:
            score -= 80 * bpm_weight
    elif bpm_diff <= 16:
        if bpm_change > 0:
            score -= 20 * bpm_weight
        else:
            score -= 100 * bpm_weight
    elif bpm_diff <= 20:
        if bpm_change > 0:
            score -= 60 * bpm_weight
        else:
            score -= 150 * bpm_weight
    elif bpm_diff <= 30:
        score -= 200 * bpm_weight
    else:
        score -= 300 * bpm_weight
    add_trace('BPM Compatibility', bpm_diff, score, f'Diff: {bpm_diff:.1f}, Change: {bpm_change:.1f}')
    key_score = get_key_compatibility_flexible(current_track.get('key', ''), track.get('key', ''))
    metrics['key_score'] = key_score
    add_trace('Key Harmony', key_score, key_score * 0.4, f'Harmonic compatibility')
    current_key = current_track.get('key', '')
    next_key = track.get('key', '')
    key_distance = None
    if current_key and next_key:
        try:
            curr_num = int(current_key[:-1]) if current_key[:-1].isdigit() else None
            next_num = int(next_key[:-1]) if next_key[:-1].isdigit() else None
            if curr_num and next_num:
                dist1 = abs(next_num - curr_num)
                dist2 = 12 - dist1
                key_distance = min(dist1, dist2)
        except:
            pass
    current_style = current_track.get('style_hint', '').lower() if current_track.get('style_hint') else ''
    next_style = track.get('style_hint', '').lower() if track.get('style_hint') else ''
    current_genre = current_track.get('genre', '').lower() if current_track.get('genre') else ''
    next_genre = track.get('genre', '').lower() if track.get('genre') else ''
    is_fast_switch = False
    if any((keyword in current_style or keyword in next_style for keyword in ['tech', 'hard', 'fast', 'dance'])):
        is_fast_switch = True
    if any((keyword in current_genre or keyword in next_genre for keyword in ['tech house', 'hard trance', 'hardstyle'])):
        is_fast_switch = True
    if current_track.get('energy', 50) > 70 or track.get('energy', 50) > 70:
        is_fast_switch = True
    if ACTIVE_PROFILE:
        key_weight = ACTIVE_PROFILE.weights.get('key_match', 0.3)
    elif is_fast_switch:
        key_weight = 0.2
    elif key_score >= 100:
        key_weight = 0.3
    elif key_score >= 95:
        key_weight = 0.25
    elif key_score >= 85:
        key_weight = 0.22
    else:
        key_weight = 0.2
    score += key_score * key_weight
    if key_distance is not None:
        if key_distance >= 5:
            score -= 50
            metrics['key_distance_penalty'] = key_distance
            metrics['needs_technique'] = True
        elif key_distance >= 4:
            score -= 30
            metrics['key_distance_penalty'] = key_distance
        elif key_distance >= 3:
            score -= 15
            metrics['key_distance_penalty'] = key_distance
    if key_score < 40:
        score -= 30
        metrics['key_incompatible'] = True
    elif key_score < 60:
        score -= 15
        metrics['key_incompatible'] = True
    current_key = current_track.get('key', '')
    next_key = track.get('key', '')
    if current_key and next_key and (current_key == next_key) and (current_key != '未知'):
        if len(sorted_tracks) > 0:
            prev_key = sorted_tracks[-1].get('key', '') if len(sorted_tracks) > 0 else ''
            if prev_key == current_key:
                score -= 3
    current_lufs = current_track.get('loudness_lufs')
    if current_lufs is None:
        current_lufs = current_track.get('lufs_db', -10.0)
    next_lufs = track.get('loudness_lufs')
    if next_lufs is None:
        next_lufs = track.get('lufs_db', -10.0)
    if current_lufs is not None and next_lufs is not None:
        try:
            c_lufs = float(current_lufs)
            n_lufs = float(next_lufs)
            lufs_diff = abs(c_lufs - n_lufs)
            lufs_score = 0
            if lufs_diff > 6.0:
                lufs_score = -80
                metrics['lufs_penalty'] = True
            elif lufs_diff > 4.5:
                lufs_score = -40 * (lufs_diff / 4.5)
                metrics['lufs_penalty'] = True
            elif lufs_diff > 2.5:
                lufs_score = -10
            score += lufs_score
            add_trace('Acoustics (LUFS)', n_lufs, lufs_score, f'Diff: {lufs_diff:.1f}dB ({c_lufs:.1f}->{n_lufs:.1f})')
            metrics['lufs_db'] = n_lufs
        except:
            pass
    current_swing = current_track.get('swing_dna', 0.0)
    next_swing = track.get('swing_dna', 0.0)
    if current_swing is not None and next_swing is not None:
        try:
            c_swing = float(current_swing)
            n_swing = float(next_swing)
            swing_diff = abs(c_swing - n_swing)
            swing_score = 0
            if swing_diff > 0.35:
                swing_score = -100
                metrics['rhythm_clash'] = True
            elif swing_diff > 0.2:
                swing_score = -30
            elif swing_diff < 0.05:
                swing_score = 20
            score += swing_score
            if swing_diff > 0.1 or swing_score != 0:
                add_trace('Rhythm (Swing)', n_swing, swing_score, f'Groove Diff: {swing_diff:.2f}')
            metrics['swing_dna'] = n_swing
        except:
            pass
    energy = track.get('energy', 50)
    current_energy = current_track.get('energy', 50)
    if min_energy is not None and max_energy is not None:
        target_center = (min_energy + max_energy) / 2.0
        energy_target_diff = abs(energy - target_center)
        energy_phase_score = max(0.0, 1.0 - energy_target_diff / 40.0)
        energy_phase_weight = 0.2
        if energy_phase_score is None:
            energy_phase_score = 0.0
        score += energy_phase_score * 100 * energy_phase_weight
        metrics['energy_phase_score'] = energy_phase_score
        metrics['energy_phase_match'] = energy_target_diff <= 20
    else:
        metrics['energy_phase_score'] = 0.5
        metrics['energy_phase_match'] = False
    if min_energy is not None and energy < min_energy:
        energy_shortage = min_energy - energy
        if phase_name in ['Build-up', 'Peak', 'Sustain']:
            if energy_shortage >= 15:
                score -= 300
                metrics['energy_shortage_severe'] = energy_shortage
            elif energy_shortage >= 10:
                score -= 200
                metrics['energy_shortage_severe'] = energy_shortage
            elif energy_shortage >= 5:
                score -= 100
                metrics['energy_shortage_medium'] = energy_shortage
            else:
                score -= 50
                metrics['energy_shortage_light'] = energy_shortage
    energy_drop = current_energy - energy
    if phase_name not in ['Cool-down', 'Outro', 'Reset']:
        if energy_drop > 50:
            score -= 200
            metrics['energy_drop_severe'] = energy_drop
        elif energy_drop > 35:
            score -= 120
            metrics['energy_drop_severe'] = energy_drop
        elif energy_drop > 25:
            score -= 70
            metrics['energy_drop_medium'] = energy_drop
        elif energy_drop > 15:
            score -= 35
            metrics['energy_drop_light'] = energy_drop
        elif energy_drop > 8:
            score -= 15
            metrics['energy_drop_minor'] = energy_drop
        elif energy_drop > 3:
            score -= 8
            metrics['energy_drop_minor'] = energy_drop
    elif energy_drop > 10:
        score += 15
        metrics['energy_drop_cooldown_bonus'] = energy_drop
    energy_diff = abs(energy - current_energy)
    if phase_name in ['Build-up', 'Peak']:
        max_energy_score = 40
        energy_weights = {5: 40, 10: 27, 15: 13, 20: 7}
    else:
        max_energy_score = 30
        energy_weights = {5: 30, 10: 20, 15: 10, 20: 5}
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
    curr_intensity = current_track.get('pssi_intensity_outro')
    next_intensity = track.get('pssi_intensity_intro')
    if curr_intensity is not None and next_intensity is not None:
        intensity_diff = abs(curr_intensity - next_intensity)
        if intensity_diff <= 1:
            score += 15
            metrics['pssi_intensity_match'] = 'excellent'
            add_trace('PSSI Intensity', intensity_diff, 15, 'Excellent flow')
            add_trace('PSSI', intensity_diff, 15, 'Excellent flow')
        elif intensity_diff <= 2:
            score += 7
            metrics['pssi_intensity_match'] = 'good'
            add_trace('PSSI', intensity_diff, 7, 'Smooth flow')
        else:
            score -= 10
            metrics['pssi_intensity_match'] = 'jump'
            add_trace('PSSI', intensity_diff, -10, 'Intensity jump penalty')
    curr_brightness = current_track.get('brightness', 0.5)
    next_brightness = track.get('brightness', 0.5)
    brightness_diff = abs(curr_brightness - next_brightness)
    if brightness_diff <= 0.15:
        score += 8
        metrics['timbre_match'] = 'consistent'
        add_trace('Timbre/Brightness', brightness_diff, 8, 'Close match')
    elif brightness_diff > 0.4:
        score -= 5
        metrics['timbre_match'] = 'contrast'
    curr_low = current_track.get('tonal_balance_low', 0.5)
    next_low = track.get('tonal_balance_low', 0.5)
    if abs(curr_low - next_low) <= 0.1:
        score += 5
        metrics['spectrum_match_low'] = 'pass'
        add_trace('Spectral Balance (Low)', abs(curr_low - next_low), 5, 'Bass consistency')
    curr_busy = current_track.get('busy_score', 0.5)
    next_busy = track.get('busy_score', 0.5)
    busy_diff = abs(curr_busy - next_busy)
    if busy_diff <= 0.2:
        score += 7
        metrics['complexity_match'] = 'balanced'
    elif busy_diff > 0.5:
        score -= 5
        metrics['complexity_match'] = 'abrupt'
    if 'VOCAL' in track.get('semantic_tags', []) and current_track.get('outro_vocal_ratio', 0) > 0.3:
        score -= 10
        metrics['semantic_conflict'] = 'vocal_overlap'
    if 'DROP' in track.get('semantic_tags', []) and current_track.get('energy', 50) > 70:
        score += 10
        metrics['semantic_bonus'] = 'energy_surge'
    if min_energy <= energy <= max_energy:
        score += 5
    elif energy < min_energy:
        if phase_name in ['Warm-up', 'Cool-down']:
            score += 3
        else:
            score += 1
    elif phase_name in ['Peak', 'Intense']:
        score += 3
    elif phase_name == 'Cool-down':
        score -= 5
    else:
        score += 1
    rhythm_similarity = compare_rhythm_similarity(current_track, track)
    if rhythm_similarity > 0.8:
        score += 10
    elif rhythm_similarity < 0.4:
        score -= 5
    curr_lufs = current_track.get('lufs_db', -10.0)
    next_lufs = track.get('lufs_db', -10.0)
    lufs_diff = abs(curr_lufs - next_lufs)
    if lufs_diff <= 2.0:
        score += 10
        metrics['gain_match'] = 'perfect'
        add_trace('Acoustics (LUFS)', lufs_diff, 10, 'Loudness consistent')
    elif lufs_diff > 4.5:
        score -= 15
        metrics['gain_match'] = 'jump'
        add_trace('Acoustics (LUFS)', lufs_diff, -15, 'Loudness jump penalty')
    curr_swing = current_track.get('swing_offset', 0.0)
    next_swing = track.get('swing_offset', 0.0)
    swing_diff = abs(curr_swing - next_swing)
    if curr_swing < 0.1 and next_swing > 0.3 or (curr_swing > 0.3 and next_swing < 0.1):
        score -= 12
        metrics['groove_conflict'] = 'swing_mismatch'
        add_trace('Rhythm (Swing)', swing_diff, -12, 'Swing vs Straight conflict')
    elif swing_diff <= 0.15:
        score += 8
        metrics['groove_conflict'] = 'synchronized'
        add_trace('Rhythm (Swing)', swing_diff, 8, 'Groove synchronized')
    current_genre = current_track.get('genre', '').lower()
    next_genre = track.get('genre', '').lower()

    def get_rhythm_group_from_genre(genre_str: str) -> str:
        """根据Genre字符串判断律动组"""
        genre_lower = genre_str.lower()
        four_on_floor_keywords = ['house', 'deep house', 'tech house', 'progressive house', 'techno', 'trance', 'hard trance', 'electro house', 'edm', 'minimal', 'acid house', 'chicago house', 'detroit techno']
        for keyword in four_on_floor_keywords:
            if keyword in genre_lower:
                return 'four_on_floor'
        breakbeat_keywords = ['breaks', 'breakbeat', 'uk garage', 'speed garage', 'drum and bass', 'jungle', 'dnb', 'd&b', 'garage']
        for keyword in breakbeat_keywords:
            if keyword in genre_lower:
                return 'breakbeat'
        half_time_keywords = ['trap', 'dubstep', 'bass music', 'future bass', 'riddim', 'brostep', 'chillstep']
        for keyword in half_time_keywords:
            if keyword in genre_lower:
                return 'half_time'
        latin_keywords = ['afro', 'afro house', 'latin', 'tribal', 'baile funk', 'reggaeton', 'dembow', 'moombahton']
        for keyword in latin_keywords:
            if keyword in genre_lower:
                return 'latin'
        return 'four_on_floor'
    current_rhythm_group = get_rhythm_group_from_genre(current_genre)
    next_rhythm_group = get_rhythm_group_from_genre(next_genre)
    current_drum_pattern = current_track.get('drum_pattern', 'unknown')
    next_drum_pattern = track.get('drum_pattern', 'unknown')
    if current_drum_pattern == 'trap' and current_rhythm_group != 'half_time':
        metrics['rhythm_warning'] = 'audio_genre_mismatch_trap_current'
        score -= 20
    if next_drum_pattern == 'trap' and next_rhythm_group != 'half_time':
        metrics['rhythm_warning'] = 'audio_genre_mismatch_trap_next'
        score -= 20
    if current_rhythm_group != next_rhythm_group:
        if current_rhythm_group == 'half_time' and next_rhythm_group == 'four_on_floor' or (current_rhythm_group == 'four_on_floor' and next_rhythm_group == 'half_time'):
            score -= 80
            metrics['rhythm_conflict'] = f'{current_rhythm_group}_vs_{next_rhythm_group}'
            metrics['rhythm_conflict_severity'] = 'severe'
        elif current_rhythm_group == 'breakbeat' and next_rhythm_group == 'four_on_floor' or (current_rhythm_group == 'four_on_floor' and next_rhythm_group == 'breakbeat'):
            score -= 40
            metrics['rhythm_conflict'] = f'{current_rhythm_group}_vs_{next_rhythm_group}'
            metrics['rhythm_conflict_severity'] = 'medium'
        elif current_rhythm_group == 'latin' and next_rhythm_group == 'four_on_floor' or (current_rhythm_group == 'four_on_floor' and next_rhythm_group == 'latin'):
            score -= 15
            metrics['rhythm_transition'] = f'{current_rhythm_group}_vs_{next_rhythm_group}'
            metrics['rhythm_conflict_severity'] = 'light'
        else:
            score -= 25
            metrics['rhythm_conflict'] = f'{current_rhythm_group}_vs_{next_rhythm_group}'
            metrics['rhythm_conflict_severity'] = 'medium'
    else:
        metrics['rhythm_match'] = current_rhythm_group
    try:
        from genre_compatibility import are_genres_compatible
        curr_genre = current_track.get('detected_genre', '')
        next_genre = track.get('detected_genre', '')
        try:
            from split_config import get_config as _get_cfg
            _cfg = _get_cfg() or {}
            min_conf = float((_cfg.get('genre_profile') or {}).get('min_confidence_for_sort', 0.85))
        except Exception:
            min_conf = 0.85
        try:
            curr_conf = float(current_track.get('detected_genre_confidence', 0.0) or 0.0)
        except Exception:
            curr_conf = 0.0
        try:
            next_conf = float(track.get('detected_genre_confidence', 0.0) or 0.0)
        except Exception:
            next_conf = 0.0
        if curr_genre and next_genre and (curr_conf >= min_conf) and (next_conf >= min_conf):
            is_compatible, compat_score, reason = are_genres_compatible(curr_genre, next_genre)
            if is_compatible:
                compat_score_safe = compat_score if compat_score is not None else 0
                genre_bonus = compat_score_safe * 0.27
                score += genre_bonus
                metrics['genre_compatible'] = True
                metrics['genre_compat_score'] = compat_score
                metrics['genre_reason'] = reason
            else:
                score -= 20
                metrics['genre_compatible'] = False
                metrics['genre_conflict'] = f'{curr_genre} vs {next_genre}'
                metrics['genre_reason'] = reason
        else:
            metrics['genre_compatible'] = None
    except ImportError:
        pass
    current_style_block = current_track.get('_style_block')
    next_style_block = track.get('_style_block')
    if current_style_block and next_style_block:
        if current_style_block == next_style_block:
            score += 14
            metrics['style_block_match'] = True
        else:
            similar_styles = {'house': ['house_generic'], 'house_generic': ['house'], 'afro': ['latin'], 'latin': ['afro']}
            is_similar = False
            if current_style_block in similar_styles:
                if next_style_block in similar_styles[current_style_block]:
                    is_similar = True
                    score += 4
            if not is_similar:
                score -= 5
            metrics['style_block_match'] = False
            metrics['style_transition'] = f'{current_style_block} → {next_style_block}'
    elif current_style_block or next_style_block:
        metrics['style_block_match'] = None
    else:
        current_genre_tag = current_track.get('genre_tag', '')
        next_genre_tag = track.get('genre_tag', '')
        if current_genre_tag and next_genre_tag:
            if current_genre_tag == next_genre_tag:
                score += 3
                metrics['genre_match'] = True
            else:
                score -= 2
                metrics['genre_match'] = False
    mfcc_similarity = compare_mfcc_similarity(current_track, track)
    if mfcc_similarity > 0.8:
        score += 10
        metrics['mfcc_similarity'] = mfcc_similarity
    elif mfcc_similarity < 0.4:
        score -= 10
        metrics['mfcc_similarity'] = mfcc_similarity
        metrics['timbre_penalty'] = True
    else:
        metrics['mfcc_similarity'] = mfcc_similarity
    curr_brightness = current_track.get('brightness', 0.5)
    next_brightness = track.get('brightness', 0.5)
    if curr_brightness > 0 and next_brightness > 0:
        brightness_diff = abs(curr_brightness - next_brightness)
        if brightness_diff <= 0.1:
            score += 8
            metrics['brightness_match'] = 'excellent'
        elif brightness_diff <= 0.2:
            score += 4
            metrics['brightness_match'] = 'good'
        elif brightness_diff > 0.4:
            score -= 6
            metrics['brightness_match'] = 'poor'
            metrics['brightness_diff'] = brightness_diff
    curr_kick = current_track.get('kick_drum_power', 0.5)
    next_kick = track.get('kick_drum_power', 0.5)
    curr_sub = current_track.get('sub_bass_level', 0.5)
    next_sub = track.get('sub_bass_level', 0.5)
    if curr_kick > 0 and next_kick > 0:
        kick_diff = abs(curr_kick - next_kick)
        sub_diff = abs(curr_sub - next_sub)
        bass_diff = (kick_diff + sub_diff) / 2
        if bass_diff <= 0.1:
            score += 10
            metrics['bass_match'] = 'excellent'
        elif bass_diff <= 0.2:
            score += 5
            metrics['bass_match'] = 'good'
        elif bass_diff > 0.35:
            score -= 8
            metrics['bass_match'] = 'poor'
            metrics['bass_diff'] = bass_diff
    curr_dr = current_track.get('dynamic_range_db', 10)
    next_dr = track.get('dynamic_range_db', 10)
    if curr_dr > 0 and next_dr > 0:
        dr_diff = abs(curr_dr - next_dr)
        if dr_diff <= 3:
            score += 6
            metrics['dynamic_match'] = 'excellent'
        elif dr_diff <= 6:
            score += 2
            metrics['dynamic_match'] = 'good'
        elif dr_diff > 10:
            score -= 5
            metrics['dynamic_match'] = 'poor'
            metrics['dynamic_diff'] = dr_diff
    curr_valence = current_track.get('valence', 0.5)
    next_valence = track.get('valence', 0.5)
    curr_arousal = current_track.get('arousal', 0.5)
    next_arousal = track.get('arousal', 0.5)
    valence_valid = (curr_valence != 1.0 or next_valence != 1.0) and (curr_valence > 0 and next_valence > 0)
    arousal_valid = (curr_arousal != 1.0 or next_arousal != 1.0) and (curr_arousal > 0 and next_arousal > 0)
    if valence_valid and arousal_valid:
        valence_diff = abs(curr_valence - next_valence)
        arousal_diff = abs(curr_arousal - next_arousal)
        emotion_diff = (valence_diff + arousal_diff) / 2
        if emotion_diff <= 0.15:
            score += 8
            metrics['emotion_match'] = 'excellent'
        elif emotion_diff <= 0.25:
            score += 4
            metrics['emotion_match'] = 'good'
        elif emotion_diff > 0.4:
            score -= 6
            metrics['emotion_match'] = 'poor'
            metrics['emotion_diff'] = emotion_diff
    curr_phrase = current_track.get('phrase_length', 16)
    next_phrase = track.get('phrase_length', 16)
    if curr_phrase > 0 and next_phrase > 0:
        if curr_phrase == next_phrase:
            score += 6
            metrics['phrase_match'] = 'exact'
        elif curr_phrase % next_phrase == 0 or next_phrase % curr_phrase == 0:
            score += 3
            metrics['phrase_match'] = 'multiple'
        else:
            score -= 3
            metrics['phrase_match'] = 'mismatch'
    curr_outro_vocal = current_track.get('outro_vocal_ratio', 0.5)
    next_intro_vocal = track.get('intro_vocal_ratio', 0.5)
    vocal_base_score = 8
    vocal_conflict_penalty = 5
    if ACTIVE_PROFILE:
        vocal_conflict_penalty = ACTIVE_PROFILE.weights.get('vocal_conflict_penalty', 5)
    if curr_outro_vocal is not None and next_intro_vocal is not None:
        if curr_outro_vocal < 0.3 and next_intro_vocal < 0.3:
            score += vocal_base_score
            metrics['vocal_transition'] = 'perfect'
        elif curr_outro_vocal < 0.3 or next_intro_vocal < 0.3:
            score += vocal_base_score / 2
            metrics['vocal_transition'] = 'good'
        elif curr_outro_vocal > 0.7 and next_intro_vocal > 0.7:
            score -= vocal_conflict_penalty
            metrics['vocal_transition'] = 'conflict'
    curr_busy = current_track.get('busy_score', 0.5)
    next_busy = track.get('busy_score', 0.5)
    if curr_busy > 0 and next_busy > 0:
        busy_diff = abs(curr_busy - next_busy)
        if busy_diff <= 0.1:
            score += 6
            metrics['busy_match'] = 'excellent'
        elif busy_diff <= 0.2:
            score += 3
            metrics['busy_match'] = 'good'
        elif busy_diff > 0.35:
            score -= 4
            metrics['busy_match'] = 'poor'
    curr_low = current_track.get('tonal_balance_low', 0.5)
    curr_mid = current_track.get('tonal_balance_mid', 0.3)
    curr_high = current_track.get('tonal_balance_high', 0.1)
    next_low = track.get('tonal_balance_low', 0.5)
    next_mid = track.get('tonal_balance_mid', 0.3)
    next_high = track.get('tonal_balance_high', 0.1)
    if curr_low > 0 and next_low > 0:
        tonal_diff = abs(curr_low - next_low) * 0.5 + abs(curr_mid - next_mid) * 0.3 + abs(curr_high - next_high) * 0.2
        if tonal_diff <= 0.1:
            score += 6
            metrics['tonal_match'] = 'excellent'
        elif tonal_diff <= 0.2:
            score += 3
            metrics['tonal_match'] = 'good'
        elif tonal_diff > 0.35:
            score -= 4
            metrics['tonal_match'] = 'poor'
    curr_hook = current_track.get('hook_strength', 0.5)
    next_hook = track.get('hook_strength', 0.5)
    if curr_hook > 0 and next_hook > 0:
        hook_diff = abs(curr_hook - next_hook)
        if hook_diff <= 0.15:
            score += 4
            metrics['hook_match'] = 'good'
        elif hook_diff > 0.4:
            score -= 3
            metrics['hook_match'] = 'poor'
    phase_hint = track.get('phase_hint')
    if isinstance(phase_hint, str):
        phase_hint = phase_hint.strip().lower()
        if phase_hint == phase_name.lower():
            score += 3
    return (score, track, metrics)

def enhanced_harmonic_sort(tracks: List[Dict], target_count: int=40, progress_logger=None, debug_reporter=None, is_boutique: bool=False, is_live: bool=False) -> Tuple[List[Dict], List[Dict], Dict]:
    """
    增强版调性和谐排序（灵活版 + 能量曲线管理 + 时长平衡 + 艺术家分布）
    注重调性兼容性，但允许一定灵活性
    
    性能优化版本：
    - 限制候选池大小（只计算BPM最接近的N首）
    - 使用堆维护候选（避免全量排序）
    - 早期剪枝（快速排除不合适候选）
    """
    if not tracks:
        return ([], [], {})
    filtered_tracks = []
    abnormal_tracks = []
    for track in tracks:
        duration = track.get('duration', 0)
        if 30 <= duration <= 600:
            filtered_tracks.append(track)
        else:
            abnormal_tracks.append(track)
            if progress_logger:
                title = track.get('title', 'Unknown')[:40]
                progress_logger.log(f'过滤异常时长: {title} ({duration:.1f}秒)', console=False)
    if abnormal_tracks and progress_logger:
        progress_logger.log(f'已过滤 {len(abnormal_tracks)} 首异常时长歌曲', console=True)
    tracks = filtered_tracks
    if not tracks:
        return ([], [], {})
    for track in tracks:
        track['_used'] = False
        track['transition_hint'] = None
        track['transition_warnings'] = track.get('transition_warnings') or []
        if 'assigned_phase' in track:
            track.pop('assigned_phase')
    sorted_tracks = []
    conflict_tracks: List[Dict] = []
    junk_drawer = []
    remaining_tracks = tracks.copy()
    energies = [t.get('energy') for t in remaining_tracks if isinstance(t.get('energy'), (int, float))]
    bpms = [t.get('bpm') for t in remaining_tracks if isinstance(t.get('bpm'), (int, float)) and t.get('bpm')]
    target_energy = statistics.median(energies) if energies else 55
    target_bpm = statistics.median(bpms) if bpms else 122
    start_track = min(remaining_tracks, key=lambda t: (abs(t.get('energy', target_energy) - target_energy), abs((t.get('bpm') or target_bpm) - target_bpm)))
    sorted_tracks.append(start_track)
    remaining_tracks.remove(start_track)
    start_track['_used'] = True
    start_bpm = start_track.get('bpm', 0)
    start_energy = start_track.get('energy', 50)
    start_key = start_track.get('key', '')
    if start_energy < 50:
        start_phase = 'Warm-up'
    elif start_energy < 65:
        start_phase = 'Build-up'
    elif start_energy < 80:
        start_phase = 'Peak'
    elif start_energy < 90:
        start_phase = 'Intense'
    else:
        start_phase = 'Intense'
    if start_energy < 65:
        start_phase = 'Warm-up'
    start_track['assigned_phase'] = start_phase
    current_phase_num = get_phase_number(start_phase)
    max_phase_reached = current_phase_num
    in_cool_down = start_phase == 'Cool-down'
    current_track = start_track
    max_iterations = len(tracks) * 2
    iteration = 0
    if len(tracks) > 200:
        CANDIDATE_POOL_SIZE = 80
    elif len(tracks) > 100:
        CANDIDATE_POOL_SIZE = 60
    elif len(tracks) > 50:
        CANDIDATE_POOL_SIZE = 50
    else:
        CANDIDATE_POOL_SIZE = min(30, len(tracks) // 2)
    CONFLICT_SCORE_THRESHOLD = -999999
    SEVERE_SCORE_THRESHOLD = -999999

    def has_unused_tracks():
        """检查是否还有未使用的歌曲"""
        return any((not t.get('_used') for t in remaining_tracks))
    debug_rounds = []
    debug_candidate_scores = []
    debug_backtrack_logs = []
    debug_conflict_logs = []
    debug_candidate_pool_sizes = []
    debug_selection_score_details = []
    debug_fallback_logs = []
    actual_target = target_count if is_boutique else len(tracks)
    while has_unused_tracks() and iteration < max_iterations:
        iteration += 1
        if is_boutique and len(sorted_tracks) >= actual_target:
            if progress_logger:
                progress_logger.log(f'✨ [精品回馈] 已达到目标曲目数 ({actual_target})，停止生成。', console=True)
            break
        round_debug = {'round': iteration, 'current_track': {'title': current_track.get('title', 'Unknown'), 'bpm': current_track.get('bpm', 0), 'key': current_track.get('key', 'Unknown'), 'energy': current_track.get('energy', 50), 'phase': current_track.get('assigned_phase', 'Unknown'), 'file_path': current_track.get('file_path', 'Unknown')}, 'remaining_count': len([t for t in remaining_tracks if not t.get('_used')]), 'sorted_count': len(sorted_tracks), 'candidates': []}
        current_bpm = current_track.get('bpm', 0)
        current_energy = current_track.get('energy', 50)
        min_energy, max_energy, phase_name = get_energy_phase_target(len(sorted_tracks), len(tracks), current_bpm, current_energy, sorted_tracks, current_track)
        if current_track.get('assigned_phase'):
            current_phase_num = get_phase_number(current_track.get('assigned_phase'))
        bpm_candidates = []
        for track in remaining_tracks:
            try:
                if track.get('_used'):
                    continue
                next_bpm = track.get('bpm', 0)
                bpm_diff = abs(current_bpm - next_bpm) if current_bpm > 0 and next_bpm > 0 else 0
                energy = track.get('energy', 50)
                energy_diff = abs(energy - current_track.get('energy', 50))
                key_score = get_key_compatibility_flexible(current_track.get('key', ''), track.get('key', ''))
                style_match = 0
                current_style_block = current_track.get('_style_block')
                track_style_block = track.get('_style_block')
                if current_style_block and track_style_block:
                    if current_style_block == track_style_block:
                        style_match = 1
                bpm_candidates.append((bpm_diff, -style_match, energy_diff, key_score, track))
            except Exception:
                continue
        bpm_candidates.sort(key=lambda x: (x[0], x[1], x[2], -x[3]))
        candidate_tracks = [t for _, _, _, _, t in bpm_candidates if not t.get('_used')]
        current_style_block = current_track.get('_style_block')
        if current_style_block and candidate_tracks:
            same_style_tracks = [t for t in candidate_tracks if t.get('_style_block') == current_style_block]
            if same_style_tracks:
                other_tracks = [t for t in candidate_tracks if t.get('_style_block') != current_style_block]
                candidate_tracks = same_style_tracks + other_tracks
        candidate_results = []
        for track in candidate_tracks:
            try:
                if track.get('_used'):
                    continue
                next_bpm = track.get('bpm') or 0
                curr_bpm_safe = current_bpm or 0
                if next_bpm > 0 and curr_bpm_safe > 0:
                    bpm_diff = abs(curr_bpm_safe - next_bpm)
                else:
                    bpm_diff = 999.0
                metrics = {'bpm_diff': bpm_diff, 'key_score': None, 'percussive_diff': None, 'dyn_var_diff': None, 'style_penalty': False, 'rhythm_penalty': False, 'phase_penalty': False, 'missing_profile': False, 'fallback': False, 'bpm_confidence': None, 'key_confidence': None, 'groove_density_diff': None, 'spectral_centroid_diff': None, 'drum_pattern_mismatch': False, 'boutique_penalty': 0}
                boutique_penalty = 0
                if is_boutique:
                    k_score = get_key_compatibility_flexible(current_track.get('key', ''), track.get('key', '')) or 0
                    track_energy = track.get('energy') or 50
                    curr_track_energy = current_track.get('energy') or 50
                    energy_diff = abs(track_energy - curr_track_energy)
                    if (bpm_diff or 0) <= 8.0 and k_score >= 90 and (energy_diff <= 25):
                        boutique_penalty = 0
                    elif (bpm_diff or 0) <= 12.0 and k_score >= 75:
                        boutique_penalty = 150
                    else:
                        boutique_penalty = 500
                    score = -boutique_penalty
                if is_boutique and boutique_penalty > 0:
                    metrics['boutique_penalty'] = boutique_penalty
                bpm_score = get_bpm_compatibility_flexible(current_bpm, next_bpm)
                bpm_change = (next_bpm or 0) - (current_bpm or 0)
                current_energy = current_track.get('energy') or 50
                next_energy = track.get('energy') or 50
                energy_diff = next_energy - current_energy
                is_breakdown_transition = bpm_change < 0 and energy_diff < -5
                if bpm_diff <= 2:
                    if bpm_change >= 0:
                        score += 100
                    elif is_breakdown_transition:
                        score += 90
                    else:
                        score += 80
                elif bpm_diff <= 4:
                    if bpm_change >= 0:
                        score += 80
                    elif is_breakdown_transition:
                        score += 60
                    else:
                        score += 50
                elif bpm_diff <= 6:
                    if bpm_change >= 0:
                        score += 60
                    elif is_breakdown_transition:
                        score += 30
                    else:
                        score += 20
                elif bpm_diff <= 8:
                    if bpm_change >= 0:
                        score += 40
                    elif is_breakdown_transition:
                        score += 10
                    else:
                        score -= 20
                elif bpm_diff <= 10:
                    if bpm_change >= 0:
                        score += 20
                    elif is_breakdown_transition:
                        score -= 20
                    else:
                        score -= 60
                elif bpm_diff <= 12:
                    if bpm_change >= 0:
                        score += 5
                    else:
                        score -= 100
                elif bpm_diff <= 16:
                    if bpm_change >= 0:
                        score -= 20
                    else:
                        score -= 150
                elif bpm_diff <= 20:
                    if bpm_change >= 0:
                        score -= 60
                    else:
                        score -= 200
                elif bpm_diff <= 30:
                    if bpm_change >= 0:
                        score -= 100
                    else:
                        score -= 250
                elif bpm_change >= 0:
                    score -= 160
                else:
                    score -= 300
                key_score = get_key_compatibility_flexible(current_track.get('key', ''), track.get('key', '')) or 0
                metrics['key_score'] = key_score
                current_style = current_track.get('style_hint', '').lower() if current_track.get('style_hint') else ''
                next_style = track.get('style_hint', '').lower() if track.get('style_hint') else ''
                current_genre = current_track.get('genre', '').lower() if current_track.get('genre') else ''
                next_genre = track.get('genre', '').lower() if track.get('genre') else ''
                is_fast_switch = False
                if any((keyword in current_style or keyword in next_style for keyword in ['tech', 'hard', 'fast', 'dance'])):
                    is_fast_switch = True
                if any((keyword in current_genre or keyword in next_genre for keyword in ['tech house', 'hard trance', 'hardstyle'])):
                    is_fast_switch = True
                if current_track.get('energy', 50) > 70 or track.get('energy', 50) > 70:
                    is_fast_switch = True
                current_key = current_track.get('key', '')
                next_key = track.get('key', '')
                key_distance = None
                if current_key and next_key:
                    try:
                        curr_num = int(current_key[:-1]) if current_key[:-1].isdigit() else None
                        next_num = int(next_key[:-1]) if next_key[:-1].isdigit() else None
                        if curr_num and next_num:
                            dist1 = abs(next_num - curr_num)
                            dist2 = 12 - dist1
                            key_distance = min(dist1, dist2)
                    except:
                        key_distance = None
                if is_fast_switch:
                    key_weight = 0.2
                elif key_score >= 100:
                    key_weight = 0.3
                elif key_score >= 95:
                    key_weight = 0.25
                elif key_score >= 85:
                    key_weight = 0.22
                else:
                    key_weight = 0.2
                score += key_score * key_weight
                if key_distance is not None:
                    if key_distance >= 5:
                        score -= 50
                        metrics['key_distance_penalty'] = key_distance
                        metrics['needs_technique'] = True
                    elif key_distance >= 4:
                        score -= 30
                        metrics['key_distance_penalty'] = key_distance
                    elif key_distance >= 3:
                        score -= 15
                        metrics['key_distance_penalty'] = key_distance
                if key_score < 40:
                    score -= 10
                elif key_score < 60:
                    score -= 5
                current_key = current_track.get('key', '')
                next_key = track.get('key', '')
                if current_key and next_key and (current_key == next_key) and (current_key != '未知'):
                    if len(sorted_tracks) > 0:
                        prev_key = sorted_tracks[-1].get('key', '') if len(sorted_tracks) > 0 else ''
                        if prev_key == current_key:
                            score -= 3
                        else:
                            pass
                energy = track.get('energy') or 50
                current_energy = current_track.get('energy') or 50
                energy_diff = abs((energy or 50) - (current_energy or 50))
                if phase_name in ['Build-up', 'Peak']:
                    max_energy_score = 40
                    energy_weights = {5: 40, 10: 27, 15: 13, 20: 7}
                else:
                    max_energy_score = 30
                    energy_weights = {5: 30, 10: 20, 15: 10, 20: 5}
                if energy_diff <= 5:
                    score += energy_weights[5] or 0
                elif energy_diff <= 10:
                    score += energy_weights[10] or 0
                elif energy_diff <= 15:
                    score += energy_weights[15] or 0
                elif energy_diff <= 20:
                    score += energy_weights[20] or 0
                else:
                    score -= 5
                candidate_phase = get_energy_phase_target(len(sorted_tracks) + 1, len(tracks), next_bpm, energy, sorted_tracks, track)[2]
                candidate_phase_num = get_phase_number(candidate_phase)
                is_valid_phase, phase_penalty = check_phase_constraint(current_phase_num, candidate_phase_num, max_phase_reached, in_cool_down)
                if not is_valid_phase:
                    score += phase_penalty or 0
                    metrics['phase_constraint_violation'] = True
                elif phase_penalty < 0:
                    score += phase_penalty or 0
                    metrics['phase_constraint_warning'] = True
                if sorted_tracks and len(sorted_tracks) > 0:
                    recent_phases = [t.get('assigned_phase') for t in sorted_tracks[-5:] if t.get('assigned_phase')]
                    recent_energies = [t.get('energy') for t in sorted_tracks[-5:] if t.get('energy') is not None]
                    if recent_phases and recent_energies:
                        last_phase = recent_phases[-1]
                        last_phase_num = get_phase_number(last_phase)
                        candidate_phase_num = get_phase_number(candidate_phase)
                        max_energy_reached = max(recent_energies) if recent_energies else 50
                        energy_regression = max_energy_reached - energy if energy < max_energy_reached else 0
                        if last_phase_num >= 2 and candidate_phase_num < last_phase_num and (candidate_phase != 'Cool-down'):
                            if energy_regression <= 5:
                                score -= 20
                                metrics['energy_regression_penalty'] = 'minor'
                            elif energy_regression <= 10:
                                score -= 50
                                metrics['energy_regression_penalty'] = 'moderate'
                            else:
                                score -= 100
                                metrics['energy_regression_penalty'] = 'severe'
                if min_energy <= energy <= max_energy:
                    score += 5
                elif energy < min_energy:
                    if phase_name in ['Warm-up', 'Cool-down']:
                        score += 3
                    else:
                        score += 1
                elif phase_name in ['Peak', 'Intense']:
                    score += 3
                elif phase_name == 'Cool-down':
                    score -= 5
                else:
                    score += 1
                curr_tension = current_track.get('tension_curve')
                next_tension = track.get('tension_curve')
                if curr_tension and next_tension and (len(curr_tension) > 2) and (len(next_tension) > 2):
                    try:
                        curr_tail = curr_tension[-int(len(curr_tension) * 0.3):]
                        next_head = next_tension[:int(len(next_tension) * 0.3)]
                        curr_trend = (curr_tail[-1] - curr_tail[0]) / len(curr_tail) if len(curr_tail) > 1 else 0
                        next_trend = (next_head[-1] - next_head[0]) / len(next_head) if len(next_head) > 1 else 0
                        curr_direction = 'up' if curr_trend > 0.01 else 'down' if curr_trend < -0.01 else 'flat'
                        next_direction = 'up' if next_trend > 0.01 else 'down' if next_trend < -0.01 else 'flat'
                        if candidate_phase in ['Warm-up', 'Build-up']:
                            if curr_direction == 'up' and next_direction == 'up':
                                score += 10
                                metrics['tension_match'] = 'rising_phase_rising_tension'
                            elif curr_direction == 'up' and next_direction == 'down':
                                score -= 15
                                metrics['tension_conflict'] = 'rising_phase_falling_tension'
                            elif curr_direction == 'flat' or next_direction == 'flat':
                                score += 3
                                metrics['tension_match'] = 'neutral'
                        elif candidate_phase in ['Peak', 'Intense']:
                            if curr_direction == 'flat' and next_direction == 'flat':
                                score += 10
                                metrics['tension_match'] = 'peak_phase_stable_tension'
                            elif curr_direction == 'up' and next_direction == 'up':
                                score += 5
                                metrics['tension_match'] = 'peak_phase_rising_tension'
                            elif curr_direction == 'down' and next_direction == 'down':
                                score -= 5
                                metrics['tension_warning'] = 'peak_phase_falling_tension'
                            elif curr_direction == 'flat' or next_direction == 'flat':
                                score += 3
                                metrics['tension_match'] = 'neutral'
                        elif candidate_phase == 'Cool-down':
                            if curr_direction == 'down' and next_direction == 'down':
                                score += 10
                                metrics['tension_match'] = 'cooldown_phase_falling_tension'
                            elif curr_direction == 'up' and next_direction == 'down':
                                score += 5
                                metrics['tension_match'] = 'cooldown_phase_natural_transition'
                            elif curr_direction == 'down' and next_direction == 'up':
                                score -= 10
                                metrics['tension_conflict'] = 'cooldown_phase_rising_tension'
                            elif curr_direction == 'flat' or next_direction == 'flat':
                                score += 3
                                metrics['tension_match'] = 'neutral'
                        elif curr_direction == next_direction:
                            score += 5
                            metrics['tension_match'] = 'same_direction'
                        elif curr_direction == 'flat' or next_direction == 'flat':
                            score += 3
                            metrics['tension_match'] = 'neutral'
                    except Exception:
                        pass
                rhythm_similarity = compare_rhythm_similarity(current_track, track)
                if rhythm_similarity > 0.8:
                    score += 15
                    metrics['rhythm_similarity'] = rhythm_similarity
                elif rhythm_similarity < 0.4:
                    score -= 10
                    metrics['rhythm_similarity'] = rhythm_similarity
                    metrics['rhythm_penalty'] = True
                else:
                    metrics['rhythm_similarity'] = rhythm_similarity
                phase_hint = track.get('phase_hint')
                if isinstance(phase_hint, str):
                    phase_hint = phase_hint.strip().lower()
                    current_phase = phase_name.lower()
                    if phase_hint == current_phase:
                        score += 15
                    elif phase_hint == 'warm-up' and current_phase in {'build-up', 'peak', 'intense'} or (phase_hint == 'cool-down' and current_phase in {'peak', 'intense'}):
                        score -= 30
                        metrics['phase_penalty'] = True
                    elif phase_hint != current_phase:
                        score -= 12
                        metrics['phase_penalty'] = True
                energy_val = energy if energy is not None else 50
                current_energy_val = current_track.get('energy') or 50
                energy_diff = energy_val - current_energy_val
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
                    metrics['percussive_diff'] = percussive_diff
                    if percussive_diff < 0.2:
                        score += 5
                    elif percussive_diff > 0.5:
                        score -= 15
                    else:
                        score += (1 - percussive_diff) * 5
                    curr_dyn_var = curr_profile.get('dynamic_variance', 0)
                    next_dyn_var = next_profile.get('dynamic_variance', 0)
                    dyn_var_diff = abs(curr_dyn_var - next_dyn_var)
                    metrics['dyn_var_diff'] = dyn_var_diff
                    if dyn_var_diff < 0.1:
                        score += 3
                    elif dyn_var_diff > 0.3:
                        score -= 8
                else:
                    metrics['missing_profile'] = True
                curr_style = current_track.get('style_hint')
                next_style = track.get('style_hint')
                curr_rhythm = current_track.get('rhythm_hint') or current_track.get('time_signature')
                next_rhythm = track.get('rhythm_hint') or track.get('time_signature')
                if curr_style and next_style:
                    if curr_style == next_style:
                        score += 5
                    elif curr_style in ['ballad', 'slow'] and next_style in ['eurobeat', 'fast', 'dance']:
                        score -= 20
                        metrics['style_penalty'] = True
                    elif curr_style in ['eurobeat', 'fast', 'dance'] and next_style in ['ballad', 'slow']:
                        score -= 15
                        metrics['style_penalty'] = True
                        if phase_name == 'Cool-down':
                            score += 10
                    else:
                        score -= 5
                        metrics['style_penalty'] = True
                if curr_rhythm and next_rhythm:
                    if curr_rhythm == next_rhythm:
                        score += 3
                    elif curr_rhythm == '3/4' and next_rhythm == '4/4' or (curr_rhythm == '4/4' and next_rhythm == '3/4'):
                        score -= 10
                        metrics['rhythm_penalty'] = True
                    else:
                        score -= 5
                        metrics['rhythm_penalty'] = True
                curr_bpm_conf = current_track.get('bpm_confidence')
                next_bpm_conf = track.get('bpm_confidence')
                if curr_bpm_conf is not None and next_bpm_conf is not None:
                    avg_bpm_conf = (curr_bpm_conf + next_bpm_conf) / 2.0
                    if avg_bpm_conf < 0.5:
                        score -= int((0.5 - avg_bpm_conf) * 20)
                        metrics['low_bpm_confidence'] = avg_bpm_conf
                    elif avg_bpm_conf > 0.8:
                        score += int((avg_bpm_conf - 0.8) * 10)
                        metrics['high_bpm_confidence'] = avg_bpm_conf
                curr_key_conf = current_track.get('key_confidence')
                next_key_conf = track.get('key_confidence')
                if curr_key_conf is not None and next_key_conf is not None:
                    avg_key_conf = (curr_key_conf + next_key_conf) / 2.0
                    if avg_key_conf < 0.5:
                        score -= int((0.5 - avg_key_conf) * 16)
                        metrics['low_key_confidence'] = avg_key_conf
                    elif avg_key_conf > 0.8:
                        score += int((avg_key_conf - 0.8) * 10)
                        metrics['high_key_confidence'] = avg_key_conf
                if next_bpm_conf is not None and next_bpm_conf < 0.6:
                    track['_low_bpm_confidence'] = True
                    track['_suggest_echo_out'] = True
                    metrics['low_bpm_confidence_hard'] = next_bpm_conf
                curr_profile_for_groove = current_track.get('energy_profile', {})
                next_profile_for_groove = track.get('energy_profile', {})
                curr_groove = curr_profile_for_groove.get('groove_density') if curr_profile_for_groove else None
                next_groove = next_profile_for_groove.get('groove_density') if next_profile_for_groove else None
                if curr_groove is not None and next_groove is not None:
                    groove_diff = abs(curr_groove - next_groove)
                    metrics['groove_density_diff'] = groove_diff
                    if groove_diff < 0.15:
                        score += 5
                        metrics['groove_match'] = True
                    elif groove_diff < 0.25:
                        score += 2
                        metrics['groove_match'] = True
                    elif groove_diff > 0.5:
                        score -= 3
                        metrics['groove_mismatch'] = True
                curr_profile_for_spectral = current_track.get('energy_profile', {})
                next_profile_for_spectral = track.get('energy_profile', {})
                curr_spectral = curr_profile_for_spectral.get('spectral_centroid_mean') if curr_profile_for_spectral else None
                next_spectral = next_profile_for_spectral.get('spectral_centroid_mean') if next_profile_for_spectral else None
                if curr_spectral is not None and next_spectral is not None:
                    spectral_diff = abs(curr_spectral - next_spectral)
                    metrics['spectral_centroid_diff'] = spectral_diff
                    normalized_diff = spectral_diff / 4000.0
                    if normalized_diff < 0.1:
                        score += 3
                        metrics['spectral_match'] = True
                    elif normalized_diff < 0.2:
                        score += 1
                        metrics['spectral_match'] = True
                beat_result = calculate_beat_alignment(current_track, track)
                if len(beat_result) >= 4:
                    beat_offset_diff, beat_alignment_score, beatgrid_fix_hints, needs_manual_align = beat_result
                else:
                    beat_offset_diff, beat_alignment_score = beat_result[:2]
                    beatgrid_fix_hints = {}
                    needs_manual_align = False
                drop_offset_diff, drop_alignment_score = calculate_drop_alignment(current_track, track)
                metrics['beat_offset_diff'] = beat_offset_diff
                metrics['drop_offset_diff'] = drop_offset_diff
                metrics['beat_alignment_score'] = beat_alignment_score
                metrics['drop_alignment_score'] = drop_alignment_score
                avg_bpm_conf_for_alignment = (curr_bpm_conf + next_bpm_conf) / 2.0 if curr_bpm_conf is not None and next_bpm_conf is not None else 0.0
                is_bpm_conf_acceptable = avg_bpm_conf_for_alignment is not None and avg_bpm_conf_for_alignment >= 0.85
                curr_downbeat_offset = current_track.get('downbeat_offset', None)
                next_downbeat_offset = track.get('downbeat_offset', None)
                has_real_beat_offset = curr_downbeat_offset is not None and curr_downbeat_offset != 0 or (next_downbeat_offset is not None and next_downbeat_offset != 0)
                if bpm_diff is not None and bpm_diff <= 3 and is_bpm_conf_acceptable and has_real_beat_offset:
                    if beat_offset_diff is not None:
                        if beat_offset_diff <= 0.5:
                            score += 20
                        elif beat_offset_diff <= 1.0:
                            score += 15
                        elif beat_offset_diff <= 2.0:
                            score += 10
                        elif beat_offset_diff <= 4.0:
                            score += 5
                        elif beat_offset_diff <= 8.0:
                            score -= 5
                        else:
                            score -= 10
                elif bpm_diff > 3:
                    pass
                elif not is_bpm_conf_acceptable:
                    pass
                elif not has_real_beat_offset:
                    pass
                curr_drop = current_track.get('first_drop_time')
                next_drop = track.get('first_drop_time')
                has_drop_info = curr_drop is not None and next_drop is not None
                is_bpm_conf_high = avg_bpm_conf_for_alignment >= 0.9
                if bpm_diff <= 2 and is_bpm_conf_high and has_drop_info:
                    if drop_offset_diff is not None:
                        if drop_offset_diff <= 4.0:
                            score += 20
                        elif drop_offset_diff <= 8.0:
                            score += 15
                        elif drop_offset_diff <= 16.0:
                            score += 10
                try:
                    from mix_compatibility_scorer import calculate_mix_compatibility_score
                    mix_score, mix_metrics = calculate_mix_compatibility_score(current_track, track)
                    mix_score_safe = mix_score if mix_score is not None else 0
                    score += mix_score_safe * 0.08
                    metrics['mix_compatibility_score'] = mix_score
                    metrics['mix_compatibility_metrics'] = mix_metrics
                    if mix_metrics.get('drop_clash'):
                        metrics['mix_warning_drop_clash'] = True
                    if mix_metrics.get('beat_offset_large'):
                        metrics['mix_warning_beat_offset'] = True
                except (ImportError, Exception):
                    pass
                vocal_result = check_vocal_conflict(current_track, track)
                vocal_penalty = vocal_result[0] if vocal_result and vocal_result[0] is not None else 0
                has_vocal_conflict = vocal_result[1] if vocal_result and len(vocal_result) > 1 else False
                score += vocal_penalty or 0
                metrics['vocal_conflict_penalty'] = vocal_penalty
                metrics['has_vocal_conflict'] = has_vocal_conflict
                ae_result = AESTHETIC_CURATOR.calculate_aesthetic_match(current_track, track)
                aesthetic_score = ae_result[0] if ae_result and ae_result[0] is not None else 0.0
                aesthetic_details = ae_result[1] if ae_result and len(ae_result) > 1 else {}
                score += aesthetic_score * 0.15
                metrics['aesthetic_score'] = aesthetic_score
                metrics['aesthetic_details'] = aesthetic_details
                mi_result = MASHUP_INTELLIGENCE.calculate_mashup_score(current_track, track)
                mashup_score = mi_result[0] if mi_result and mi_result[0] is not None else 0.0
                mashup_details = mi_result[1] if mi_result and len(mi_result) > 1 else {}
                score += mashup_score * 0.15
                metrics['mashup_score'] = mashup_score
                metrics['mashup_details'] = mashup_details
                phrase_parity_bonus = 0
                curr_outro_bars = current_track.get('outro_bars', 8)
                next_intro_bars = track.get('intro_bars', 8)
                if curr_outro_bars == next_intro_bars:
                    phrase_parity_bonus = 25
                    score += phrase_parity_bonus or 0
                    metrics['phrase_parity_bonus'] = phrase_parity_bonus
                vocal_synergy_bonus = 0
                curr_v_ratio = current_track.get('outro_vocal_ratio') or 0.5
                next_v_ratio = track.get('intro_vocal_ratio') or 0.5
                if curr_v_ratio > 0.7 and next_v_ratio < 0.3 or (curr_v_ratio < 0.3 and next_v_ratio > 0.7):
                    vocal_synergy_bonus = 20
                    score += vocal_synergy_bonus or 0
                    metrics['vocal_synergy_bonus'] = vocal_synergy_bonus
                    metrics['mashup_sweet_spot'] = True
                drop_align_bonus = 0
                next_drop = track.get('first_drop_time')
                if next_drop:
                    drop_align_bonus = 5
                    score += drop_align_bonus or 0
                    metrics['drop_align_bonus'] = drop_align_bonus
                optimized_mix_out, optimized_mix_in = optimize_mix_points_with_windows(current_track, track)
                if optimized_mix_out is not None and optimized_mix_in is not None:
                    metrics['mix_points_optimized'] = True
                    metrics['optimized_mix_out'] = optimized_mix_out
                    metrics['optimized_mix_in'] = optimized_mix_in
                    curr_mix_out = optimized_mix_out
                    next_mix_in = optimized_mix_in
                else:
                    curr_mix_out = current_track.get('mix_out_point')
                    next_mix_in = track.get('mix_in_point')
                curr_duration = current_track.get('duration', 0)
                curr_structure = current_track.get('structure', {})
                next_structure = track.get('structure', {})
                if curr_mix_out is not None and next_mix_in is not None and (curr_duration is not None and curr_duration > 0):
                    mix_gap = next_mix_in - (curr_duration - curr_mix_out)
                    metrics['mix_gap'] = mix_gap
                    curr_mix_out_in_verse = False
                    next_mix_in_in_verse = False
                    if curr_structure:
                        verses = curr_structure.get('verse', [])
                        for verse in verses:
                            if verse[0] is not None and verse[1] is not None and (curr_mix_out is not None) and (verse[0] < curr_mix_out < verse[1]):
                                curr_mix_out_in_verse = True
                                break
                    if next_structure:
                        verses = next_structure.get('verse', [])
                        for verse in verses:
                            if verse[0] is not None and verse[1] is not None and (next_mix_in is not None) and (verse[0] < next_mix_in < verse[1]):
                                next_mix_in_in_verse = True
                                break
                    if curr_mix_out_in_verse or next_mix_in_in_verse:
                        metrics['structure_warning'] = True
                if metrics.get('has_vocal_conflict'):
                    score *= 0.6
                    metrics['v3_vocal_shield_active'] = True
                curr_low = current_track.get('energy_profile', {}).get('low_energy', 0)
                next_low = track.get('energy_profile', {}).get('low_energy', 0)
                if curr_low > 0.6 and next_low > 0.6:
                    metrics['bass_swap_required'] = True
                    metrics['bass_swap_reason'] = f'双轨低频对撞 (Low Energy: {curr_low:.1f}/{next_low:.1f})'
                curr_swing = current_track.get('swing_ratio') or current_track.get('analysis', {}).get('swing_ratio', 0.0)
                next_swing = track.get('swing_ratio') or track.get('analysis', {}).get('swing_ratio', 0.0)
                if abs(float(curr_swing) - float(next_swing)) > 0.4:
                    score -= 25
                    metrics['swing_mismatch_penalty'] = True
                curr_synth = current_track.get('synthesis_type') or current_track.get('analysis', {}).get('synthesis_type')
                next_synth = track.get('synthesis_type') or track.get('analysis', {}).get('synthesis_type')
                if curr_synth and next_synth and (curr_synth != next_synth):
                    score -= 15
                    metrics['synthesis_jump_penalty'] = True
                candidate_results.append({'track': track, 'score': score, 'metrics': metrics})
                if debug_reporter:
                    candidate_debug = {'track': {'title': track.get('title', 'Unknown'), 'bpm': track.get('bpm', 0), 'key': track.get('key', 'Unknown'), 'energy': track.get('energy', 50), 'file_path': track.get('file_path', 'Unknown'), 'duration': track.get('duration', 0), 'first_drop_time': track.get('first_drop_time'), 'mix_in_point': track.get('mix_in_point'), 'beat_offset': track.get('beat_offset'), 'structure': track.get('structure', {}), 'energy_profile': track.get('energy_profile', {})}, 'total_score': score, 'scores': {'bpm_score': metrics.get('bpm_diff') or 0, 'bpm_change': (track.get('bpm') or 0) - (current_bpm or 0) if (current_bpm or 0) > 0 else 0, 'key_score': metrics.get('key_score', 0), 'energy_score': metrics.get('energy_diff', 0), 'energy_phase': phase_name, 'drop_alignment': metrics.get('drop_alignment', None), 'beat_alignment': metrics.get('beat_offset_diff', None), 'mix_gap': metrics.get('mix_gap', None), 'percussive_diff': metrics.get('percussive_diff', None), 'dyn_var_diff': metrics.get('dyn_var_diff', None), 'style_penalty': metrics.get('style_penalty', False), 'rhythm_penalty': metrics.get('rhythm_penalty', False), 'phase_penalty': metrics.get('phase_penalty', False), 'missing_profile': metrics.get('missing_profile', False)}, 'details': {'current_track_bpm': current_bpm, 'current_track_key': current_track.get('key', 'Unknown'), 'current_track_energy': current_track.get('energy', 50), 'current_track_phase': current_track.get('assigned_phase', 'Unknown'), 'target_phase': phase_name, 'target_energy_range': (min_energy, max_energy), 'all_metrics': metrics.copy()}}
                    debug_candidate_scores.append(candidate_debug)
                    round_debug['candidates'].append({'title': track.get('title', 'Unknown')[:50], 'score': score, 'bpm': track.get('bpm', 0), 'key': track.get('key', 'Unknown'), 'energy': track.get('energy', 50)})
            except Exception:
                continue
        candidate_results.sort(key=lambda item: item['score'], reverse=True)
        has_close_bpm_option = any((item['metrics'].get('bpm_diff') is not None and item['metrics']['bpm_diff'] <= 16 for item in candidate_results))
        if not candidate_results:
            if remaining_tracks:
                fallback_track = None
                for t in remaining_tracks:
                    if not t.get('_used'):
                        fallback_track = t
                        break
                if fallback_track:
                    if debug_reporter:
                        debug_fallback_logs.append({'tier': 'Tier1', 'round': iteration, 'reason': '没有候选结果，使用fallback', 'selected_track': {'title': fallback_track.get('title', 'Unknown'), 'bpm': fallback_track.get('bpm', 0), 'key': fallback_track.get('key', 'Unknown'), 'energy': fallback_track.get('energy', 50)}, 'details': {'candidate_count': len(candidate_results), 'remaining_count': len([t for t in remaining_tracks if not t.get('_used')])}})
                    fallback_track['_used'] = True
                    fallback_energy = fallback_track.get('energy', 50)
                    progress = len(sorted_tracks) / max(len(tracks), 1)
                    if fallback_energy < 45:
                        phase_name = 'Warm-up'
                    elif fallback_energy < 60:
                        phase_name = 'Build-up'
                    elif fallback_energy < 75:
                        phase_name = 'Peak'
                    elif fallback_energy < 85:
                        phase_name = 'Intense'
                    else:
                        phase_name = 'Intense'
                    if progress >= 0.9 and fallback_energy < 80:
                        phase_name = 'Cool-down'
                    fallback_track['assigned_phase'] = phase_name
                    fallback_track['transition_warnings'] = fallback_track.get('transition_warnings') or []
                    sorted_tracks.append(fallback_track)
                    remaining_tracks.remove(fallback_track)
                    current_track = fallback_track
                    if progress_logger:
                        progress_logger.log(f'Fallback添加: {fallback_track.get('title', 'Unknown')[:40]}', console=True)
                    continue
            break
        remaining_count_check = len(remaining_tracks) - sum((1 for t in remaining_tracks if t.get('_used')))
        target_count_val = target_count if target_count is not None else 0
        is_closure_phase_check = len(sorted_tracks) >= target_count_val - 2 or remaining_count_check <= 2
        if is_closure_phase_check:
            for item in candidate_results:
                track = item['track']
                if track.get('_is_closure_candidate', False):
                    closure_bonus = track.get('_closure_score', 0)
                    if closure_bonus > 0:
                        bonus = min(50, closure_bonus * 0.5)
                        item['score'] += bonus
        candidate_results.sort(key=lambda x: x['score'], reverse=True)
        QUALITY_FLOOR = 40
        best_result = None
        for result in candidate_results:
            if not result['track'].get('_used'):
                if result['score'] >= QUALITY_FLOOR:
                    best_result = result
                    break
        if best_result is None and is_boutique:
            for result in candidate_results:
                if not result['track'].get('_used'):
                    best_result = result
                    if progress_logger:
                        progress_logger.log(f'⚠️ [精品降级] 为了连贯性接受次优解: {best_result['track'].get('title', 'Unknown')[:30]} (分数: {best_result['score']:.1f})', console=False)
                    break
            if best_result is None:
                if progress_logger:
                    progress_logger.log('⚠️ [精品回馈] 彻底无法找到任何可用候选，提前终止生成。', console=True)
                break
        if best_result is None and is_live and has_unused_tracks():
            if not candidate_results:
                misfit = next((t for t in remaining_tracks if not t.get('_used')))
                misfit['_used'] = True
                junk_drawer.append(misfit)
                remaining_tracks.remove(misfit)
                if progress_logger:
                    progress_logger.log(f'📦 [直播残差] 歌曲无法衔接，暂存至末尾: {misfit.get('title')[:30]}', console=True)
                continue
        if best_result is None and candidate_results:
            for result in candidate_results:
                if not result['track'].get('_used'):
                    best_result = result
                    if progress_logger:
                        progress_logger.log(f'[降级衔接] 质量不足但强制链入: {best_result['track'].get('title', 'Unknown')[:30]} (分数: {best_result['score']:.1f})', console=False)
                    break
        if best_result is None and has_unused_tracks():
            continue
        if best_result is None:
            if progress_logger and (not has_unused_tracks()):
                progress_logger.log(f'排序完成或无可用歌选', console=False)
            break
        if not has_close_bpm_option:
            best_bpm_diff = best_result['metrics'].get('bpm_diff')
            if best_bpm_diff is not None and best_bpm_diff <= 30:
                best_result['metrics']['force_accept'] = True
        best_track = best_result['track']
        best_score = best_result['score']
        metrics = best_result['metrics'].copy()
        if best_track.get('_is_closure_candidate', False):
            best_track['_is_closure'] = True
            best_track.pop('_is_closure_candidate', None)
            best_track.pop('_closure_score', None)
        reasons = []
        bpm_diff = metrics.get('bpm_diff')
        if bpm_diff is not None and bpm_diff > 12:
            reasons.append(f'BPM跨度 {bpm_diff:.1f}')
        key_score = metrics.get('key_score')
        if key_score is not None and key_score < 45:
            reasons.append(f'调性兼容度低({key_score:.0f})')
        percussive_diff = metrics.get('percussive_diff')
        if percussive_diff is not None and percussive_diff > 0.45:
            reasons.append('快慢歌差异大')
        dyn_var_diff = metrics.get('dyn_var_diff')
        if dyn_var_diff is not None and dyn_var_diff > 0.35:
            reasons.append('动态变化差异大')
        if metrics.get('style_penalty'):
            reasons.append('风格不匹配')
        if metrics.get('rhythm_penalty'):
            reasons.append('节奏型不匹配')
        if metrics.get('phase_penalty'):
            reasons.append('能量阶段与手动标注冲突')
        if metrics.get('structure_warning'):
            reasons.append('混音点在Verse中间（不推荐）')
        if len(sorted_tracks) % 10 == 0:
            remaining = len(remaining_tracks) - 1
            if target_count is not None and target_count > 0:
                print(f'  排序进度: {len(sorted_tracks)}/{target_count} ({len(sorted_tracks) * 100 // target_count}%) | 剩余: {remaining}首 | 候选池: {len(candidate_tracks)}首')
            else:
                print(f'  排序进度: {len(sorted_tracks)} (Target Unknown) | 剩余: {remaining}首 | 候选池: {len(candidate_tracks)}首')
        if len(sorted_tracks) >= 2 and key_score_val is not None and (key_score_val < 85):
            backtrack_depth = min(2, len(sorted_tracks))
            best_backtrack_score = best_score
            best_backtrack_track = best_track
            best_backtrack_metrics = metrics
            for backtrack_idx in range(1, backtrack_depth + 1):
                if backtrack_idx >= len(sorted_tracks):
                    break
                backtrack_track = sorted_tracks[-backtrack_idx]
                backtrack_bpm = backtrack_track.get('bpm') or 0
                current_track_bpm = best_track.get('bpm') or 0
                for candidate in candidate_tracks:
                    if candidate.get('_used') or candidate == best_track:
                        continue
                    candidate_bpm = candidate.get('bpm') or 0
                    candidate_bpm_diff = abs(backtrack_bpm - candidate_bpm) if backtrack_bpm is not None and candidate_bpm is not None else 999
                    if candidate_bpm_diff > 8:
                        pass
                    candidate_key_score = get_key_compatibility_flexible(backtrack_track.get('key', ''), candidate.get('key', ''))
                    key_improvement = candidate_key_score - key_score_val
                    bpm_penalty = 0
                    if candidate_bpm_diff > 6:
                        bpm_penalty = (candidate_bpm_diff - 6) * 2
                    if key_improvement >= 15 - bpm_penalty:
                        backtrack_score = best_score
                        key_improvement = (candidate_key_score - key_score_val) * 0.5
                        backtrack_score += key_improvement
                        if bpm_diff is not None and candidate_bpm_diff > bpm_diff:
                            backtrack_score -= (candidate_bpm_diff - bpm_diff) * 2
                        if bpm_diff is not None and backtrack_score > best_backtrack_score + 5:
                            best_backtrack_score = backtrack_score
                            best_backtrack_track = candidate
                            candidate_metrics = None
                            for res in candidate_results:
                                if res['track'] == candidate:
                                    candidate_metrics = res['metrics'].copy()
                                    break
                            if candidate_metrics:
                                best_backtrack_metrics = candidate_metrics
                                best_backtrack_metrics.update({'backtracked': True, 'backtrack_depth': backtrack_idx})
                            else:
                                best_backtrack_metrics = {'bpm_diff': candidate_bpm_diff, 'key_score': candidate_key_score, 'backtracked': True, 'backtrack_depth': backtrack_idx, 'audit_trace': []}
                            break
            if best_backtrack_track != best_track and best_backtrack_metrics.get('backtracked'):
                if debug_reporter:
                    backtrack_debug = {'round': iteration, 'reason': f'调性兼容性不足 (key_score={key_score_val:.0f} < 85)', 'depth': best_backtrack_metrics.get('backtrack_depth', 0), 'original_track': {'title': best_track.get('title', 'Unknown'), 'key': best_track.get('key', 'Unknown'), 'key_score': key_score_val}, 'backtrack_track': {'title': backtrack_track.get('title', 'Unknown'), 'key': backtrack_track.get('key', 'Unknown')}, 'selected_track': {'title': best_backtrack_track.get('title', 'Unknown'), 'key': best_backtrack_track.get('key', 'Unknown'), 'key_score': best_backtrack_metrics.get('key_score', 0)}, 'key_improvement': best_backtrack_metrics.get('key_score', 0) - key_score_val, 'process': [f'回溯到位置 -{best_backtrack_metrics.get('backtrack_depth', 0)}', f'原选择: {best_track.get('title', 'Unknown')[:40]} (key_score={key_score_val:.0f})', f'新选择: {best_backtrack_track.get('title', 'Unknown')[:40]} (key_score={best_backtrack_metrics.get('key_score', 0):.0f})', f'调性分提升: {best_backtrack_metrics.get('key_score', 0) - key_score_val:.0f}']}
                    debug_backtrack_logs.append(backtrack_debug)
                if best_backtrack_metrics.get('backtrack_depth', 0) > 0:
                    pass
                best_track = best_backtrack_track
                best_score = best_backtrack_score
                metrics = best_backtrack_metrics
                if progress_logger:
                    progress_logger.log(f'局部回溯：选择调性兼容性更好的歌曲（调性分提升 {best_backtrack_metrics.get('key_score', 0) - key_score_val:.0f}分）', console=False)
        if best_track.get('_used'):
            if progress_logger:
                progress_logger.log(f'警告：尝试添加已使用的歌曲 {best_track.get('title', 'Unknown')[:40]}，跳过', console=True)
            continue
        if best_track in remaining_tracks:
            remaining_tracks.remove(best_track)
        best_track['_used'] = True
        force_accept = bool(metrics.get('force_accept'))
        bpm_diff = metrics.get('bpm_diff')
        key_score_val = metrics.get('key_score')
        major_penalties = 0
        if bpm_diff is not None and bpm_diff > 30:
            major_penalties += 3
        elif bpm_diff is not None and bpm_diff > 20:
            major_penalties += 1
        if key_score_val is not None and key_score_val < 40:
            major_penalties += 1
        if metrics.get('rhythm_penalty'):
            major_penalties += 1
        if metrics.get('style_penalty'):
            major_penalties += 1
        if metrics.get('phase_penalty'):
            major_penalties += 1
        is_conflict = False
        is_conflict = False
        if bpm_diff is not None and bpm_diff > 30:
            if 'BPM超大跨度' not in reasons:
                reasons.append(f'BPM超大跨度 {bpm_diff:.1f}（无法直接混音）')
        if debug_reporter and (major_penalties >= 3 or (bpm_diff is not None and bpm_diff > 30) or (key_score_val is not None and key_score_val < 40)):
            conflict_debug = {'round': iteration, 'reason': ' | '.join(reasons) if reasons else '综合评分低', 'tracks': [{'title': best_track.get('title', 'Unknown'), 'file_path': best_track.get('file_path', 'Unknown'), 'bpm': best_track.get('bpm', 0), 'key': best_track.get('key', 'Unknown'), 'energy': best_track.get('energy', 50), 'conflict_reason': ' | '.join(reasons) if reasons else 'Unknown', 'score': best_score, 'major_penalties': major_penalties}]}
            debug_conflict_logs.append(conflict_debug)
        if is_conflict:
            if not reasons:
                reasons.append('综合得分偏低或兼容性不足')
            best_track['_is_conflict'] = True
            best_track['_conflict_reasons'] = reasons
        else:
            best_track['_is_conflict'] = False
        if reasons:
            warnings = best_track.get('transition_warnings') or []
            warnings.extend([r for r in reasons if r not in warnings])
            best_track['transition_warnings'] = warnings
        mix_gap_val = metrics.get('mix_gap')
        if mix_gap_val is not None and (not -8.0 <= mix_gap_val <= 16.0):
            warnings = best_track.get('transition_warnings') or []
            gap_msg = f'混音点间隔 {mix_gap_val:.1f}s'
            if gap_msg not in warnings:
                warnings.append(gap_msg)
            best_track['transition_warnings'] = warnings
        best_energy = best_track.get('energy', 50)
        progress = len(sorted_tracks) / max(len(tracks), 1)
        if best_energy < 45:
            best_phase = 'Warm-up'
        elif best_energy < 60:
            best_phase = 'Build-up'
        elif best_energy < 75:
            best_phase = 'Peak'
        elif best_energy < 85:
            best_phase = 'Intense'
        else:
            best_phase = 'Intense'
        if progress >= 0.9 and best_energy < 80:
            best_phase = 'Cool-down'
        best_phase_num = get_phase_number(best_phase)
        current_phase_num = best_phase_num
        if best_phase_num > max_phase_reached:
            max_phase_reached = best_phase_num
        if best_phase == 'Cool-down':
            in_cool_down = True
        best_track['assigned_phase'] = best_phase
        best_track['_transition_score'] = best_score
        best_track['_transition_metrics'] = metrics.copy()
        best_track['audit_trace'] = metrics.get('audit_trace', [])
        if metrics.get('mix_points_optimized'):
            opt_out = metrics.get('optimized_mix_out')
            opt_in = metrics.get('optimized_mix_in')
            if len(sorted_tracks) > 0 and opt_out is not None:
                sorted_tracks[-1]['mix_out_point'] = opt_out
            if opt_in is not None:
                best_track['mix_in_point'] = opt_in
        if best_track not in sorted_tracks:
            sorted_tracks.append(best_track)
        else:
            if progress_logger:
                progress_logger.log(f'严重错误：尝试重复添加歌曲 {best_track.get('title', 'Unknown')[:40]}，已跳过', console=True)
            continue
        current_track = best_track
        if debug_reporter:
            round_debug['selected_track'] = {'title': best_track.get('title', 'Unknown'), 'bpm': best_track.get('bpm', 0), 'key': best_track.get('key', 'Unknown'), 'energy': best_track.get('energy', 50), 'phase': best_track.get('assigned_phase', 'Unknown'), 'score': best_score, 'reasons': reasons.copy() if reasons else []}
            round_debug['candidate_count'] = len(candidate_results)
            debug_rounds.append(round_debug)
            debug_candidate_pool_sizes.append({'round': iteration, 'pool_size': len(candidate_tracks), 'remaining': len([t for t in remaining_tracks if not t.get('_used')]), 'selected_track': {'title': best_track.get('title', 'Unknown'), 'bpm': best_track.get('bpm', 0), 'key': best_track.get('key', 'Unknown')}})
            debug_selection_score_details.append({'round': iteration, 'track': {'title': best_track.get('title', 'Unknown'), 'bpm': best_track.get('bpm', 0), 'key': best_track.get('key', 'Unknown'), 'energy': best_track.get('energy', 50)}, 'total_score': best_score, 'scores': {'key_score': metrics.get('key_score', 0), 'bpm_score': get_bpm_compatibility_flexible(current_bpm, best_track.get('bpm', 0)), 'bpm_diff': metrics.get('bpm_diff', 0), 'energy_score': abs(best_track.get('energy', 50) - current_energy), 'style_score': 0, 'drop_score': 0, 'drop_alignment': metrics.get('drop_alignment', None), 'beat_alignment': metrics.get('beat_offset_diff', None)}})
        remaining_count = len(remaining_tracks) - sum((1 for t in remaining_tracks if t.get('_used')))
        is_closure_phase = len(sorted_tracks) >= target_count - 2 or remaining_count <= 2
        if is_closure_phase and remaining_count > 0:
            current_track = sorted_tracks[-1]
            current_bpm = current_track.get('bpm', 0)
            current_energy = current_track.get('energy', 50)
            closure_candidates = [t for t in remaining_tracks if not t.get('_used')]
            if closure_candidates:
                best_closure_track = None
                best_closure_score = -999999
                for candidate in closure_candidates:
                    candidate_bpm = candidate.get('bpm', 0)
                    candidate_key = candidate.get('key', '')
                    candidate_energy = candidate.get('energy', 50)
                    closure_score = 0
                    if current_bpm > 0 and candidate_bpm > 0:
                        bpm_diff = current_bpm - candidate_bpm
                        if 0 <= bpm_diff <= 5:
                            closure_score += 20
                        elif bpm_diff < 0:
                            closure_score -= 15
                        elif bpm_diff > 10:
                            closure_score -= 10
                    if start_key and start_key != '未知' and candidate_key and (candidate_key != '未知'):
                        key_score_to_start = get_key_compatibility_flexible(start_key, candidate_key)
                        if key_score_to_start >= 100:
                            closure_score += 40
                        elif key_score_to_start >= 80:
                            closure_score += 30
                        elif key_score_to_start >= 60:
                            closure_score += 15
                    if 50 <= candidate_energy <= 75:
                        energy_diff = current_energy - candidate_energy
                        if 0 <= energy_diff <= 15:
                            closure_score += 15
                        elif energy_diff < 0:
                            closure_score -= 10
                    elif candidate_energy > 75:
                        closure_score -= 5
                    key_score_current = get_key_compatibility_flexible(current_track.get('key', ''), candidate_key)
                    closure_score += key_score_current * 0.1
                    bpm_diff_current = abs(current_bpm - candidate_bpm) if current_bpm > 0 and candidate_bpm > 0 else 999
                    if bpm_diff_current <= 10:
                        closure_score += (10 - bpm_diff_current) * 2
                    if closure_score > best_closure_score:
                        best_closure_score = closure_score
                        best_closure_track = candidate
                if best_closure_track and best_closure_score > 0:
                    best_closure_track['_closure_score'] = best_closure_score
                    best_closure_track['_is_closure_candidate'] = True
                    if progress_logger:
                        closure_reasons = []
                        if start_key and start_key != '未知':
                            key_score = get_key_compatibility_flexible(start_key, best_closure_track.get('key', ''))
                            if key_score >= 80:
                                closure_reasons.append(f'调性回到起始调({start_key})')
                        if (current_bpm or 0) > 0 and (best_closure_track.get('bpm') or 0) > 0:
                            bpm_diff = (current_bpm or 0) - (best_closure_track.get('bpm') or 0)
                            if 0 <= bpm_diff <= 5:
                                closure_reasons.append(f'BPM略低({bpm_diff:.1f})')
                        if closure_reasons:
                            progress_logger.log(f'尾曲候选：{best_closure_track.get('title', '未知')} ({' | '.join(closure_reasons)})', console=False)
    if not is_boutique:
        unused_remaining = [t for t in remaining_tracks if not t.get('_used')]
        total_input = len(tracks)
        total_sorted = len(sorted_tracks)
        total_unused = len(unused_remaining)
        if progress_logger:
            progress_logger.log(f'[V4调试] 排序循环结束：输入 {total_input} 首，已排序 {total_sorted} 首，剩余未使用 {total_unused} 首', console=True)
        if unused_remaining:
            if progress_logger:
                progress_logger.log(f'循环结束后，发现 {len(unused_remaining)} 首未处理的歌曲，将强制添加到末尾', console=True)
            if sorted_tracks:
                last_track = sorted_tracks[-1]
                unused_remaining.sort(key=lambda t: (-get_key_compatibility_flexible(last_track.get('key', ''), t.get('key', '')), -get_bpm_compatibility_flexible(last_track.get('bpm', 0), t.get('bpm', 0))))
            else:
                unused_remaining.sort(key=lambda t: t.get('bpm', 0))
            for idx, track in enumerate(unused_remaining, start=len(sorted_tracks)):
                track['_used'] = True
                track_bpm = track.get('bpm') or 0
                track_energy = track.get('energy') or 50
                progress = idx / max(total_input or 1, 1)
                if track_energy < 45:
                    phase_name = 'Warm-up'
                elif track_energy < 60:
                    phase_name = 'Build-up'
                elif track_energy < 75:
                    phase_name = 'Peak'
                elif track_energy < 85:
                    phase_name = 'Intense'
                else:
                    phase_name = 'Intense'
                if progress >= 0.9 and track_energy < 80:
                    phase_name = 'Cool-down'
                track['assigned_phase'] = phase_name
                track['_conflict_reasons'] = ['循环结束后添加（未在正常排序中处理）']
            sorted_tracks.extend(unused_remaining)
            if progress_logger:
                progress_logger.log(f'[V4调试] 已强制添加 {len(unused_remaining)} 首剩余歌曲，当前总数：{len(sorted_tracks)} 首（应等于输入 {len(tracks)} 首）', console=True)
                if len(sorted_tracks) != len(tracks):
                    progress_logger.log(f'[V4警告] 歌曲数量不匹配！输入 {len(tracks)} 首，但排序后只有 {len(sorted_tracks)} 首（缺失 {len(tracks) - len(sorted_tracks)} 首）', console=True)
    conflict_count = sum((1 for t in sorted_tracks if t.get('_conflict', False)))
    if False and conflict_tracks:
        import re
        insertable_conflicts = []
        final_conflicts = []
        for conflict_track in conflict_tracks:
            conflict_reasons = conflict_track.get('_conflict_reasons', [])
            bpm_span = None
            for reason in conflict_reasons:
                if 'BPM超大跨度' in reason:
                    try:
                        numbers = re.findall('\\d+\\.?\\d*', reason)
                        if numbers:
                            bpm_span = float(numbers[0])
                            break
                    except:
                        pass
                elif 'BPM跨度' in reason and '超大' not in reason:
                    try:
                        numbers = re.findall('\\d+\\.?\\d*', reason)
                        if numbers:
                            bpm_span = float(numbers[0])
                            break
                    except:
                        pass
            if bpm_span is None:
                conflict_bpm = conflict_track.get('bpm', 0)
                if conflict_bpm > 0 and sorted_tracks:
                    min_bpm_diff = min((abs(conflict_bpm - t.get('bpm', 0)) for t in sorted_tracks if t.get('bpm', 0) > 0))
                    if min_bpm_diff < 20:
                        bpm_span = min_bpm_diff
            if bpm_span is not None and bpm_span < 20:
                insertable_conflicts.append((bpm_span, conflict_track))
            else:
                final_conflicts.append(conflict_track)
        insertable_conflicts.sort(key=lambda x: x[0])
        for bpm_span, conflict_track in insertable_conflicts:
            conflict_bpm = conflict_track.get('bpm', 0)
            conflict_bpm = conflict_track.get('bpm') or 0
            if conflict_bpm <= 0:
                final_conflicts.append(conflict_track)
                continue
            best_insert_idx = len(sorted_tracks)
            best_score = float('-inf')
            conflict_key = conflict_track.get('key', '')
            for idx, track in enumerate(sorted_tracks):
                track_bpm = track.get('bpm') or 0
                if track_bpm > 0:
                    bpm_diff = abs(conflict_bpm - track_bpm)
                    if bpm_diff < 20:
                        prev_bpm = sorted_tracks[idx - 1].get('bpm', 0) if idx > 0 else 0
                        next_bpm = sorted_tracks[idx + 1].get('bpm', 0) if idx + 1 < len(sorted_tracks) else 0
                        can_insert = True
                        if prev_bpm > 0 and abs(conflict_bpm - prev_bpm) > 20:
                            can_insert = False
                        if next_bpm > 0 and abs(conflict_bpm - next_bpm) > 20:
                            can_insert = False
                        if can_insert:
                            score = 0
                            score -= bpm_diff * 2
                            track_key = track.get('key', '')
                            if conflict_key and track_key and (conflict_key != '未知') and (track_key != '未知'):
                                key_score = get_key_compatibility_flexible(conflict_key, track_key)
                                score += key_score * 0.5
                            if idx > 0:
                                prev_key = sorted_tracks[idx - 1].get('key', '')
                                if conflict_key and prev_key and (conflict_key != '未知') and (prev_key != '未知'):
                                    prev_key_score = get_key_compatibility_flexible(prev_key, conflict_key)
                                    score += prev_key_score * 0.3
                            if score > best_score:
                                best_score = score
                                best_insert_idx = idx + 1
            if best_insert_idx < len(sorted_tracks):
                sorted_tracks.insert(best_insert_idx, conflict_track)
                conflict_track['_inserted'] = True
                conflict_track['_conflict'] = False
                if progress_logger:
                    progress_logger.log(f'插入BPM相近冲突歌曲（跨度{bpm_span:.1f}）：{conflict_track.get('title', 'Unknown')[:40]}', console=False)
            else:
                final_conflicts.append(conflict_track)
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
    if len(sorted_tracks) > 10 and progress_logger:
        progress_logger.log('开始全局调性优化...', console=False)
    optimized_tracks = optimize_key_connections_global(sorted_tracks, progress_logger)
    marked_conflicts = [t for t in optimized_tracks if t.get('_is_conflict', False)]
    if junk_drawer:
        if progress_logger:
            progress_logger.log(f'[质量屏障] 正在追加 {len(junk_drawer)} 首低兼容度歌曲到末尾备选区...', console=True)
        for misfit in junk_drawer:
            misfit['assigned_phase'] = 'Extra (Misfit)'
            if optimized_tracks:
                misfit['_transition_score'] = -50
            optimized_tracks.append(misfit)
    if len(optimized_tracks) != len(tracks):
        if progress_logger:
            progress_logger.log(f'警告：输出歌曲数 ({len(optimized_tracks)}) 不等于输入歌曲数 ({len(tracks)})，缺失 {len(tracks) - len(optimized_tracks)} 首', console=True)
    metrics = {'n_input': len(tracks), 'n_output': len(optimized_tracks), 'conflict_count': len(marked_conflicts), 'rounds': len(debug_rounds), 'backtrack_count': len(debug_backtrack_logs), 'conflict_count_debug': len(debug_conflict_logs)}
    if len(optimized_tracks) > 10:
        if not validate_energy_curve(optimized_tracks):
            if progress_logger:
                progress_logger.log('⚠️ 能量曲线验证失败，进行自动修正', console=True)
            optimized_tracks = fix_energy_curve(optimized_tracks, progress_logger)
    return (optimized_tracks, marked_conflicts, metrics)

def validate_energy_curve(sorted_tracks: List[Dict]) -> bool:
    """
    【V6优化P3.1】验证能量曲线是否符合 Warm-up → Peak → Cool-down
    
    Returns:
        bool: True表示能量曲线完整，False表示需要修正
    """
    if len(sorted_tracks) < 5:
        return True
    phases = [t.get('assigned_phase') for t in sorted_tracks if t.get('assigned_phase')]
    if not phases:
        return False
    has_peak = any((p in ['Peak', 'Sustain', 'Intense', 'Bang'] for p in phases))
    last_10_percent = phases[-max(1, len(phases) // 10):]
    has_cooldown = any((p in ['Cool-down', 'Reset', 'Outro'] for p in last_10_percent))
    first_20_percent = phases[:max(1, len(phases) // 5)]
    has_warmup = any((p in ['Warm-up', 'Build-up'] for p in first_20_percent))
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
        return tracks
    fixed_tracks = tracks.copy()
    total = len(fixed_tracks)
    max_energy_track = max(fixed_tracks, key=lambda t: t.get('energy', 50))
    max_energy_idx = fixed_tracks.index(max_energy_track)
    if max_energy_track.get('assigned_phase') not in ['Peak', 'Sustain', 'Intense', 'Bang']:
        max_energy_track['assigned_phase'] = 'Peak'
        if progress_logger:
            progress_logger.log(f'✅ 修正：第{max_energy_idx + 1}首（能量{max_energy_track.get('energy', 0)}）标记为Peak', console=False)
    last_10_percent = fixed_tracks[-max(1, total // 10):]
    for i, track in enumerate(last_10_percent):
        track_idx = fixed_tracks.index(track)
        if track.get('energy', 50) < 85:
            if track.get('assigned_phase') not in ['Cool-down', 'Reset', 'Outro']:
                track['assigned_phase'] = 'Cool-down'
                if progress_logger:
                    progress_logger.log(f'✅ 修正：第{track_idx + 1}首（能量{track.get('energy', 0)}）标记为Cool-down', console=False)
    first_20_percent = fixed_tracks[:max(1, total // 5)]
    for i, track in enumerate(first_20_percent):
        track_idx = fixed_tracks.index(track)
        if track.get('assigned_phase') not in ['Warm-up', 'Build-up']:
            if track.get('energy', 50) < 55:
                track['assigned_phase'] = 'Warm-up'
            else:
                track['assigned_phase'] = 'Build-up'
            if progress_logger:
                progress_logger.log(f'✅ 修正：第{track_idx + 1}首（能量{track.get('energy', 0)}）标记为{track['assigned_phase']}', console=False)
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
    window_size = min(10, len(optimized) // 4)
    if window_size < 3:
        return tracks
    max_move_distance = 2
    improvements = 0
    step_size = max(1, window_size // 2)
    for start_idx in range(0, len(optimized) - window_size, step_size):
        end_idx = min(start_idx + window_size, len(optimized))
        window = optimized[start_idx:end_idx]
        if len(window) < 3:
            continue
        for i in range(1, len(window) - 1):
            current_track = window[i]
            prev_track = window[i - 1]
            next_track = window[i + 1]
            current_bpm = current_track.get('bpm', 0)
            prev_bpm = prev_track.get('bpm', 0)
            next_bpm = next_track.get('bpm', 0)
            prev_key_score = get_key_compatibility_flexible(prev_track.get('key', ''), current_track.get('key', ''))
            next_key_score = get_key_compatibility_flexible(current_track.get('key', ''), next_track.get('key', ''))
            current_total_score = prev_key_score + next_key_score
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
                bpm_swap_penalty = 0
                if swap_bpm_diff > 4:
                    bpm_swap_penalty = (swap_bpm_diff - 4) * 5
                if swap_offset < 0:
                    new_prev_track = window[swap_idx - 1] if swap_idx > 0 else prev_track
                    new_prev_key_score = get_key_compatibility_flexible(new_prev_track.get('key', ''), current_track.get('key', ''))
                    new_next_key_score = get_key_compatibility_flexible(current_track.get('key', ''), swap_track.get('key', ''))
                    swap_total_score = new_prev_key_score + new_next_key_score
                else:
                    new_prev_key_score = get_key_compatibility_flexible(prev_track.get('key', ''), swap_track.get('key', ''))
                    new_next_track = window[swap_idx + 1] if swap_idx < len(window) - 1 else next_track
                    new_next_key_score = get_key_compatibility_flexible(swap_track.get('key', ''), new_next_track.get('key', ''))
                    swap_total_score = new_prev_key_score + new_next_key_score
                swap_total_score -= bpm_swap_penalty
                if swap_total_score > best_swap_score + 20:
                    best_swap_idx = swap_idx
                    best_swap_score = swap_total_score
            if best_swap_idx is not None:
                actual_i = start_idx + i
                actual_swap_idx = start_idx + best_swap_idx
                optimized[actual_i], optimized[actual_swap_idx] = (optimized[actual_swap_idx], optimized[actual_i])
                improvements += 1
                if progress_logger and improvements % 5 == 0:
                    progress_logger.log(f'全局优化：已优化 {improvements} 处调性连接', console=False)
        optimized[start_idx:end_idx] = window
    if progress_logger and improvements > 0:
        progress_logger.log(f'全局调性优化完成：共优化 {improvements} 处调性连接', console=False)
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
    if curr_key and next_key and (curr_key != '未知') and (next_key != '未知'):
        key_score = get_key_compatibility_flexible(curr_key, next_key)
        if key_score >= 95:
            advice.append(f'    ✅ 调性过渡：{curr_key} → {next_key} （完美和谐，直接混音即可）')
        elif key_score >= 85:
            advice.append(f'    ✅ 调性过渡：{curr_key} → {next_key} （非常和谐，直接混音即可）')
        elif key_score >= 70:
            advice.append(f'    ⚠️ 调性过渡：{curr_key} → {next_key} （较和谐，标准混音即可）')
        else:
            try:
                curr_num = int(curr_key[:-1])
                next_num = int(next_key[:-1])
                diff = abs(curr_num - next_num)
                advice.append(f'    ⚠️ 调性过渡：{curr_key} → {next_key} （需要技巧）')
                if diff > 4:
                    advice.append(f'       • 建议混音手法：使用Echo/Filter效果器过渡')
                    advice.append(f'       • 在低能量段落（Intro/Outro）混音')
                    advice.append(f'       • 考虑使用Keylock功能微调')
                elif diff > 2:
                    advice.append(f'       • 建议混音手法：使用Filter Sweep过渡')
                    advice.append(f'       • 在Breakdown处混入')
                else:
                    advice.append(f'       • 建议混音手法：标准混音即可，注意能量衔接')
            except:
                advice.append(f'       • 建议混音手法：使用Filter效果器平滑过渡')
                advice.append(f'       • 在低能量段落混音')
    if curr_mix_out is not None and next_mix_in is not None and (curr_bpm > 0):
        beats_per_bar = 4
        phrase_len_beats = 16 * beats_per_bar
        is_phrase_aligned = int(next_mix_in * next_bpm / 60) % 32 <= 1
        if is_phrase_aligned:
            advice.append(f'    📏 乐句对齐 (Phrasing): ✅ 完美乐句点进入 (对齐 32 拍)')
        else:
            advice.append(f'    📏 乐句对齐 (Phrasing): ⚠️ 进歌点非标准乐句起始，建议手动对齐 Beatgrid')
    curr_low = curr_track.get('tonal_balance_low', 0.5)
    next_low = next_track.get('tonal_balance_low', 0.5)
    if abs(curr_low - next_low) > 0.3:
        advice.append(f'    🎚️ 频段审计 (EQ): {('下一首低频较重，建议提前 Cut Bass' if next_low > curr_low else '上一首低频较厚，建议使用 Bass Swap 技巧')}')
    curr_vocal = curr_track.get('vocal_ratio', 0.5)
    next_vocal = next_track.get('vocal_ratio', 0.5)
    if curr_vocal > 0.7 and next_vocal > 0.7:
        advice.append(f'    🗣️ 人声预警 (Vocal Clash): ⚠️ 双重人声冲突风险！建议其中一轨关闭 Vocal Stem')
    if MASHUP_ENABLED:
        try:
            m_score, m_details = MASHUP_INTELLIGENCE.calculate_mashup_score(curr_track, next_track)
            if m_score >= 85:
                guide = MASHUP_INTELLIGENCE.generate_unified_guide(curr_track, next_track, m_score, m_details)
                advice.append(f'    🔥 极品 MASHUP 机会 (Neural Match: {m_score:.1f}/100):')
                advice.append(f'       • 策略: {m_details.get('mashup_pattern', '实时互补混音')}')
                sweet_spots = MASHUP_INTELLIGENCE.get_mashup_sweet_spots(curr_track, next_track)
                if sweet_spots.get('can_mashup'):
                    for spot in sweet_spots['best_spots']:
                        advice.append(f'       • 甜点: {spot['type']} @ {spot['timestamp']:.1f}s - {spot['reason']}')
                if 'cultural_affinity' in m_details:
                    advice.append(f'       • 契合点: {m_details['cultural_affinity']}')
                advice.append(f'       • 操作: {(guide[2] if len(guide) > 2 else '尝试 Stems 分离混音')}')
            curr_outro_bars = curr_track.get('outro_bars', 8)
            next_intro_bars = next_track.get('intro_bars', 8)
            advice.append(f'    📏 物理量化: A-Outro [{curr_outro_bars} Bars] | B-Intro [{next_intro_bars} Bars]')
            if curr_outro_bars == next_intro_bars:
                advice.append(f'       ✅ 乐句完美对齐 ({curr_outro_bars}x{next_intro_bars})，律动无缝切换')
            if 'bass_clash' in m_details:
                advice.append(f'    🎚️ 频谱预警 (Spectral): {m_details['bass_clash']}')
        except:
            pass
    curr_ts = curr_track.get('time_signature', '4/4')
    next_ts = next_track.get('time_signature', '4/4')
    if curr_ts != next_ts:
        advice.append(f'    ⚠️ 节奏冲突 (Meter Clash): {curr_ts} vs {next_ts} (混音极度危险，建议硬切)')
    if AESTHETIC_ENABLED:
        ae_advice = AESTHETIC_CURATOR.get_mix_bible_advice(curr_track, next_track)
        advice.append(f'    🎨 审美策展 (Aesthetic Guide):')
        advice.append(f'       • 推荐手法: {ae_advice['technique']}')
        advice.append(f'       • 建议时长: {ae_advice['suggested_duration']}')
        advice.append(f'       • 核心氛围: {ae_advice['vibe_target']}')
    if NARRATIVE_ENABLED:
        nr_advice = NARRATIVE_PLANNER.get_narrative_advice(curr_track, next_track)
        advice.append(f'    📖 叙事连贯 (Narrative Link):')
        advice.append(f'       • 音乐学背景: {nr_advice}')
    if curr_bpm and next_bpm:
        bpm_diff = abs(curr_bpm - next_bpm)
        if bpm_diff > 15:
            advice.append(f'    ⚠️ BPM跨度：{curr_bpm:.1f} → {next_bpm:.1f} BPM （跨度 {bpm_diff:.1f}，超过15）')
            advice.append(f'       • 建议：使用Master Tempo功能，或逐步调整BPM')
        elif bpm_diff > 12:
            advice.append(f'    ⚠️ BPM跨度：{curr_bpm:.1f} → {next_bpm:.1f} BPM （跨度 {bpm_diff:.1f}，接近上限）')
            advice.append(f'       • 建议：使用Master Tempo功能，或逐步调整BPM')
        elif bpm_diff > 8:
            advice.append(f'    📊 BPM过渡：{curr_bpm:.1f} → {next_bpm:.1f} BPM （跨度 {bpm_diff:.1f}）')
            advice.append(f'       • 建议：注意BPM变化，可以逐步调整')
        elif bpm_diff > 4:
            advice.append(f'    📊 BPM过渡：{curr_bpm:.1f} → {next_bpm:.1f} BPM （跨度 {bpm_diff:.1f}）')
            advice.append(f'       • 建议：注意BPM变化，可以逐步调整')
    curr_exit_bars = curr_track.get('exit_bars', 0)
    next_entry_bars = next_track.get('entry_bars', 0)
    curr_struct = curr_track.get('structure', {})
    next_struct = next_track.get('structure', {})
    if curr_track.get('hotcue_C') or next_track.get('hotcue_A'):
        advice.append(f'    🎯 专业层叠混音 (Transition Guard):')
        if curr_track.get('hotcue_C') and next_track.get('hotcue_A'):
            advice.append(f'       • 动作：让 [上一首 C点] 对齐 [这一首 A点]')
            if curr_exit_bars > 0 and next_entry_bars > 0:
                if curr_exit_bars == next_entry_bars:
                    advice.append(f'       • ✅ 黄金层叠：{curr_exit_bars}b 乐句完美同步')
                else:
                    advice.append(f'       • ⚠️ 长度差：出歌{curr_exit_bars}b vs 进歌{next_entry_bars}b (注意调整衰减速度)')
            advice.append(f'       • 节点：上一首到 {chr(ord('A') + 3)}点(D) 时，此首应在 {chr(ord('A') + 1)}点(B) 完成统治')
        elif curr_track.get('hotcue_C'):
            fallback_bars = curr_exit_bars if curr_exit_bars > 0 else 16
            advice.append(f'       • 建议：上一首出歌窗口 {fallback_bars}b，建议下一首在该长度前开始进场')
            if next_track.get('mix_in_point'):
                advice.append(f'       • AI 匹配：已自动将下一首 A点 锚定在 AI Mix-In')
        elif next_track.get('hotcue_A'):
            fallback_bars = next_entry_bars if next_entry_bars > 0 else 16
            advice.append(f'       • 建议：这一首进歌窗口 {fallback_bars}b，请在上一首结束前至少 {fallback_bars}b 处切入')
    if next_track.get('hotcue_A') and next_struct:
        struct_pts = []
        if isinstance(next_struct, dict) and 'structure' in next_struct:
            for pts in next_struct['structure'].values():
                if isinstance(pts, list):
                    struct_pts.extend(pts)
                elif isinstance(pts, (int, float)):
                    struct_pts.append(pts)
        a_point = next_track['hotcue_A']
        is_aligned = any((abs(a_point - p) < 0.5 for p in struct_pts))
        if not is_aligned and struct_pts:
            advice.append(f'    ⚠️ 乐句偏移：手动A点未对齐 AI 乐句起始点，建议检查节拍对齐 (Grid Check)')
    curr_genre = curr_track.get('genre', '').lower()
    next_genre = next_track.get('genre', '').lower()

    def get_rhythm_group_from_genre(genre_str: str) -> str:
        """根据Genre字符串判断律动组"""
        genre_lower = genre_str.lower()
        four_on_floor_keywords = ['house', 'deep house', 'tech house', 'progressive house', 'techno', 'trance', 'hard trance', 'electro house', 'edm', 'minimal', 'acid house', 'chicago house', 'detroit techno']
        for keyword in four_on_floor_keywords:
            if keyword in genre_lower:
                return 'four_on_floor'
        breakbeat_keywords = ['breaks', 'breakbeat', 'uk garage', 'speed garage', 'drum and bass', 'jungle', 'dnb', 'd&b', 'garage']
        for keyword in breakbeat_keywords:
            if keyword in genre_lower:
                return 'breakbeat'
        half_time_keywords = ['trap', 'dubstep', 'bass music', 'future bass', 'riddim', 'brostep', 'chillstep']
        for keyword in half_time_keywords:
            if keyword in genre_lower:
                return 'half_time'
        latin_keywords = ['afro', 'afro house', 'latin', 'tribal', 'baile funk', 'reggaeton', 'dembow', 'moombahton']
        for keyword in latin_keywords:
            if keyword in genre_lower:
                return 'latin'
        return 'four_on_floor'
    curr_rhythm_group = get_rhythm_group_from_genre(curr_genre)
    next_rhythm_group = get_rhythm_group_from_genre(next_genre)
    if curr_rhythm_group != next_rhythm_group:
        curr_genre_display = curr_track.get('genre', 'Unknown')
        next_genre_display = next_track.get('genre', 'Unknown')
        if curr_rhythm_group == 'half_time' or next_rhythm_group == 'half_time':
            advice.append(f'    ⚠️ 律动变化：{curr_genre_display} → {next_genre_display}')
            advice.append(f'       • 律动类型：{curr_rhythm_group} → {next_rhythm_group}')
            advice.append(f'       • 建议：需要快速切换（8-16拍内完成）')
            advice.append(f'       • 技巧：在Breakdown或Drop前快速切换，使用Filter/Echo Out过渡')
        elif curr_rhythm_group == 'breakbeat' or next_rhythm_group == 'breakbeat':
            advice.append(f'    ⚠️ 律动变化：{curr_genre_display} → {next_genre_display}')
            advice.append(f'       • 律动类型：{curr_rhythm_group} → {next_rhythm_group}')
            advice.append(f'       • 建议：在Breakdown处过渡，避免鼓点重叠')
        elif curr_rhythm_group == 'latin' or next_rhythm_group == 'latin':
            advice.append(f'    ℹ️ 风格变化：{curr_genre_display} → {next_genre_display}')
            advice.append(f'       • 律动类型：{curr_rhythm_group} → {next_rhythm_group}')
            advice.append(f'       • 建议：可以过渡，注意律动感的变化')
        else:
            advice.append(f'    ℹ️ 风格变化：{curr_genre_display} → {next_genre_display}')
            advice.append(f'       • 律动类型：{curr_rhythm_group} → {next_rhythm_group}')
    curr_vocals = curr_track.get('vocals')
    next_vocals = next_track.get('vocals')
    curr_drums = curr_track.get('drums')
    next_drums = next_track.get('drums')
    if curr_mix_out and next_mix_in and curr_vocals and next_vocals:
        current_out_vocals = False
        for seg_start, seg_end in curr_vocals.get('segments', []):
            if seg_start <= curr_mix_out <= seg_end:
                current_out_vocals = True
                break
        next_in_vocals = False
        for seg_start, seg_end in next_vocals.get('segments', []):
            if seg_start <= next_mix_in <= seg_end:
                next_in_vocals = True
                break
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
        if current_out_vocals and next_in_vocals:
            advice.append(f'    ⚠️ 混音元素：人声 → 人声 （不推荐）')
            advice.append(f'       • 建议：调整混音点，避免人声重叠')
            advice.append(f'       • 理想情况：人声混鼓点/旋律，或鼓点混人声')
        elif current_out_vocals and (not next_in_vocals):
            if next_in_drums:
                advice.append(f'    ✅ 混音元素：人声 → 鼓点 （推荐）')
            else:
                advice.append(f'    ✅ 混音元素：人声 → 旋律/乐器 （推荐）')
        elif not current_out_vocals and next_in_vocals:
            if current_out_drums:
                advice.append(f'    ✅ 混音元素：鼓点 → 人声 （推荐）')
            else:
                advice.append(f'    ✅ 混音元素：旋律/乐器 → 人声 （推荐）')
        elif current_out_drums and next_in_drums:
            advice.append(f'    ✅ 混音元素：鼓点 → 鼓点 （可以）')
    if curr_mix_out and next_mix_in:
        bpm_diff = abs(curr_bpm - next_bpm) if curr_bpm and next_bpm else 0
        key_score = get_key_compatibility_flexible(curr_key, next_key) if curr_key and next_key else 50
        if key_score >= 80 and bpm_diff <= 4:
            mix_duration = '16-32拍（短混音）'
        elif key_score >= 60 and bpm_diff <= 6:
            mix_duration = '32-64拍（中混音）'
        else:
            mix_duration = '64-128拍（长混音）'
        advice.append(f'    🎯 混音点建议：')
        advice.append(f'       • 从 {curr_title} 的 {curr_mix_out:.1f}秒 开始淡出')
        advice.append(f'       • 在 {next_title} 的 {next_mix_in:.1f}秒 开始混入')
        advice.append(f'       • 建议混音时长：{mix_duration}')
    if curr_key and next_key and (curr_key != '未知') and (next_key != '未知'):
        key_score = get_key_compatibility_flexible(curr_key, next_key)
        bpm_diff = abs(curr_bpm - next_bpm) if curr_bpm and next_bpm else 0
        try:
            curr_num = int(curr_key[:-1])
            next_num = int(next_key[:-1])
            diff = abs(curr_num - next_num)
            advice.append(f'    🎚️ 效果器推荐：')
            if key_score < 60 or diff > 4:
                advice.append(f'       • Echo Delay + Low Pass Filter')
                advice.append(f'       • 参数：Echo Time=1/2拍，Filter Cutoff=20-30%')
            elif diff > 2:
                advice.append(f'       • Filter Sweep')
                advice.append(f'       • 参数：Filter Cutoff从100%降至20%，用时32-64拍')
            elif bpm_diff > 6:
                advice.append(f'       • Master Tempo + Reverb')
                advice.append(f'       • 参数：BPM逐步调整，Reverb=25-30%')
            elif key_score >= 80:
                advice.append(f'       • 标准混音（可选Subtle Reverb）')
                advice.append(f'       • 参数：Reverb=15-20%（可选）')
            else:
                advice.append(f'       • 标准混音即可')
        except:
            pass
    v3_metrics = next_track.get('_transition_metrics', {})
    if v3_metrics.get('bass_swap_required'):
        advice.append(f'    🔊 低音相位审计 (Bass Phase Guard):')
        advice.append(f'       • 🔴 警告：{v3_metrics.get('bass_swap_reason', '双轨低频对撞')}')
        advice.append(f'       • 建议：强制执行 [Bass Swap / Low Cut] 过渡')
    if v3_metrics.get('v3_vocal_shield_active'):
        advice.append(f'    🗣️ 人声避让协议 (Vocal Shield):')
        advice.append(f'       • 🔴 警告：建议混音区域存在人声碰撞 (Vocal Clash)')
        advice.append(f'       • 建议：在此处使用 Quick Cut 或等上一首人声彻底结束后再推高电平')
    if v3_metrics.get('groove_conflict') == 'swing_mismatch' or v3_metrics.get('swing_mismatch_penalty'):
        advice.append(f'    🥁 律动不匹配 (Swing Mismatch):')
        advice.append(f'       • 🔴 警告：直拍 (Straight) 与摇摆 (Swing) 律动跨合，容易产生节奏打架')
        advice.append(f'       • 建议：避免在鼓点段落长混，使用 Quick Cut 或 Wait for Breakdown')
    if MASHUP_ENABLED:
        archetype = MASHUP_INTELLIGENCE.get_mashup_archetype(curr_track, next_track)
        if archetype:
            advice.append(f'\n   🍳 [顶级配方] {archetype['name']}:')
            for step in archetype['steps']:
                advice.append(f'      - {step}')
            advice.append(f'      💡 原理: {archetype['rationale']}')
    audit_trace = next_track.get('audit_trace', [])
    if not audit_trace and '_transition_metrics' in next_track:
        audit_trace = next_track['_transition_metrics'].get('audit_trace', [])
    if audit_trace:
        advice.append(f'\n    🔍 [V6.0 系统审计] 决策链路追踪 (Audit Trace):')
        for log in audit_trace:
            dim = log.get('dim', 'Unknown')
            val = log.get('val', 0.0)
            score_impact = log.get('score', 0)
            reason = log.get('reason', '')
            icon = '📈' if score_impact > 0 else '📉'
            sign = '+' if score_impact > 0 else ''
            advice.append(f'       • {icon} {dim}: {val:.2f} | 影响: {sign}{score_impact} ({reason})')
    return advice

def generate_mixing_advice(tracks: List[Dict]) -> str:
    """生成混音建议（保留用于兼容性）"""
    if not tracks:
        return ''
    advice = []
    key_transitions = []
    for i in range(len(tracks) - 1):
        curr_key = tracks[i].get('key', '')
        next_key = tracks[i + 1].get('key', '')
        if curr_key and next_key and (curr_key != '未知') and (next_key != '未知'):
            key_score = get_key_compatibility_flexible(curr_key, next_key)
            key_transitions.append((i, tracks[i].get('title', ''), curr_key, next_key, key_score))
    difficult_transitions = [t for t in key_transitions if t[4] < 60]
    smooth_transitions = [t for t in key_transitions if t[4] >= 80]
    advice.append('=' * 60)
    advice.append('混音建议')
    advice.append('=' * 60)
    if smooth_transitions:
        try:
            advice.append(f'\n[和谐] 发现 {len(smooth_transitions)} 个非常和谐的过渡：')
        except:
            advice.append(f'\n[Harmonic] Found {len(smooth_transitions)} very smooth transitions:')
        for idx, title, curr, next_key, score in smooth_transitions[:5]:
            advice.append(f'  • {title[:40]} ({curr} → {next_key}) - 直接混音即可')
    if difficult_transitions:
        advice.append(f'\n⚠️ 发现 {len(difficult_transitions)} 个需要技巧的过渡：')
        for idx, title, curr, next_key, score in difficult_transitions[:5]:
            advice.append(f'\n  • {title[:40]} ({curr} → {next_key})')
            advice.append(f'    建议混音手法：')
            try:
                curr_num = int(curr[:-1])
                next_num = int(next_key[:-1])
                diff = abs(curr_num - next_num)
                if diff > 4:
                    advice.append(f'    - 使用Echo/Filter效果器过渡')
                    advice.append(f'    - 在低能量段落（Intro/Outro）混音')
                    advice.append(f'    - 考虑使用Keylock功能微调')
                elif diff > 2:
                    advice.append(f'    - 使用Filter Sweep过渡')
                    advice.append(f'    - 在Breakdown处混入')
                else:
                    advice.append(f'    - 标准混音即可，注意能量衔接')
            except:
                advice.append(f'    - 使用Filter效果器平滑过渡')
                advice.append(f'    - 在低能量段落混音')
    else:
        try:
            advice.append('\n[和谐] 所有过渡都很和谐，可以流畅混音！')
        except:
            advice.append('\n[Harmonic] All transitions are smooth, can mix fluently!')
    bpm_transitions = []
    for i in range(len(tracks) - 1):
        curr_bpm = tracks[i].get('bpm', 0)
        next_bpm = tracks[i + 1].get('bpm', 0)
        if curr_bpm and next_bpm:
            diff = abs(curr_bpm - next_bpm)
            bpm_transitions.append((i, tracks[i].get('title', ''), curr_bpm, next_bpm, diff))
    large_bpm_jumps = [t for t in bpm_transitions if t[4] > 8]
    if large_bpm_jumps:
        advice.append(f'\n📊 BPM跨度较大（>8 BPM）的过渡：')
        for idx, title, curr, next_bpm, diff in large_bpm_jumps[:5]:
            advice.append(f'  • {title[:40]}: {curr:.1f} → {next_bpm:.1f} BPM (跨度 {diff:.1f})')
            advice.append(f'    建议：使用Master Tempo功能，或逐步调整BPM')
    advice.append(f'\n🎯 精确混音点建议：')
    mix_point_count = 0
    for i in range(len(tracks) - 1):
        curr_track = tracks[i]
        next_track = tracks[i + 1]
        curr_mix_out = curr_track.get('mix_out_point')
        next_mix_in = next_track.get('mix_in_point')
        if curr_mix_out and next_mix_in:
            mix_point_count += 1
            if mix_point_count <= 5:
                try:
                    curr_title = curr_track.get('title', 'Unknown')[:30]
                    next_title = next_track.get('title', 'Unknown')[:30]
                    advice.append(f'  {i + 1}. {curr_title} → {next_title}')
                    advice.append(f'     • 从 {curr_title} 的 {curr_mix_out:.1f}秒 开始淡出')
                    advice.append(f'     • 在 {next_title} 的 {next_mix_in:.1f}秒 开始混入')
                    bpm_diff = abs(curr_track.get('bpm', 120) - next_track.get('bpm', 120))
                    key_score = get_key_compatibility_flexible(curr_track.get('key', ''), next_track.get('key', ''))
                    if key_score >= 80 and bpm_diff <= 4:
                        mix_duration = '16-32拍（短混音）'
                    elif key_score >= 60 and bpm_diff <= 6:
                        mix_duration = '32-64拍（中混音）'
                    else:
                        mix_duration = '64-128拍（长混音）'
                    advice.append(f'     • 建议混音时长：{mix_duration}')
                except:
                    pass
    if mix_point_count == 0:
        advice.append('  （部分歌曲的混音点未检测到，建议手动选择混音点）')
    advice.append(f'\n🎚️ 效果器使用建议：')
    effect_count = 0
    for i in range(min(5, len(tracks) - 1)):
        curr_track = tracks[i]
        next_track = tracks[i + 1]
        curr_key = curr_track.get('key', '')
        next_key = next_track.get('key', '')
        key_score = get_key_compatibility_flexible(curr_key, next_key)
        bpm_diff = abs(curr_track.get('bpm', 120) - next_track.get('bpm', 120))
        if curr_key and next_key and (curr_key != '未知') and (next_key != '未知'):
            try:
                curr_num = int(curr_key[:-1])
                next_num = int(next_key[:-1])
                diff = abs(curr_num - next_num)
                effect_count += 1
                next_title = next_track.get('title', 'Unknown')[:30]
                if key_score < 60 or diff > 4:
                    advice.append(f'  {i + 1}. {next_title}')
                    advice.append(f'     • 推荐效果器：Echo Delay + Low Pass Filter')
                    advice.append(f'     • 参数：Echo Time=1/2拍，Filter Cutoff=20-30%')
                elif diff > 2:
                    advice.append(f'  {i + 1}. {next_title}')
                    advice.append(f'     • 推荐效果器：Filter Sweep')
                    advice.append(f'     • 参数：Filter Cutoff从100%降至20%，用时32-64拍')
                elif bpm_diff > 6:
                    advice.append(f'  {i + 1}. {next_title}')
                    advice.append(f'     • 推荐效果器：Master Tempo + Reverb')
                    advice.append(f'     • 参数：BPM逐步调整，Reverb=25-30%')
                elif key_score >= 80:
                    advice.append(f'  {i + 1}. {next_title}')
                    advice.append(f'     • 推荐效果器：标准混音（可选Subtle Reverb）')
                    advice.append(f'     • 参数：Reverb=15-20%（可选）')
            except:
                pass
    if effect_count == 0:
        advice.append('  （所有过渡都很和谐，标准混音即可）')
    energies = [t.get('energy', 50) for t in tracks]
    if len(energies) > 10:
        avg_energy = sum(energies) / len(energies)
        peak_idx = energies.index(max(energies))
        advice.append(f'\n🎵 能量分析：')
        advice.append(f'  • 平均能量：{avg_energy:.1f}/100')
        advice.append(f'  • 峰值位置：第 {peak_idx + 1} 首 ({tracks[peak_idx].get('title', '')[:30]})')
        if peak_idx < len(tracks) * 0.3:
            advice.append(f'  • 建议：峰值出现较早，可考虑后段加入更高能量歌曲')
        elif peak_idx > len(tracks) * 0.7:
            advice.append(f'  • 建议：能量曲线良好，可继续维持或逐步下降')
            advice.append('\n' + '=' * 60)
    return '\n'.join(advice)

async def create_enhanced_harmonic_sets(playlist_name: str='流行Boiler Room', songs_per_set: int=40, min_songs: int=25, max_songs: int=40, enable_bridge: bool=False, enable_bridge_track: bool=True, is_boutique: bool=False, is_master: bool=False, is_live: bool=False, preset: str='default', progress_logger=None):
    """创建增强版调性和谐Set
    
    Args:
        enable_bridge: 启用桥接模式，从曲库补充同风格歌曲（仅限电子乐风格）
        enable_bridge_track: 启用桥接曲自动插入（BPM跨度>15时插入桥接曲）
                            华语/K-Pop/J-Pop播放列表自动禁用
    """
    asian_pop_keywords = ['华语', '中文', 'chinese', 'mandarin', 'cpop', 'c-pop', 'kpop', 'k-pop', '韩语', 'korean', 'jpop', 'j-pop', '日语', 'japanese']
    playlist_lower = playlist_name.lower()
    is_asian_pop = any((kw in playlist_lower for kw in asian_pop_keywords))
    if is_asian_pop and (not is_boutique):
        enable_bridge_track = False
        print(f'[桥接曲] 检测到亚洲流行播放列表，自动禁用桥接曲功能')
    db = RekordboxDatabase()
    pyrekordbox_db = Rekordbox6Database()
    try:
        try:
            print('正在连接到Rekordbox数据库...')
        except:
            print('Connecting to Rekordbox database...')
        await db.connect()
        try:
            print('连接成功！')
        except:
            print('Connected!')
        with open('d:/anti/sorter_debug.log', 'a', encoding='utf-8') as dbg_log:
            dbg_log.write(f"DEBUG: Entering logic with playlist_name='{playlist_name}'\n")

        class MockPlaylist:

            def __init__(self, name):
                self.id = 'SEARCH_RESULT'
                self.name = name
                self.is_folder = False
                self.parent_id = None
                self.track_count = 0
        if playlist_name.startswith('artist:'):
            artist_query = playlist_name.split(':', 1)[1]
            print(f"模式: 按艺术家搜索 '{artist_query}'")
            tracks_raw = await db.search_tracks(SearchOptions(artist=artist_query))
            target_playlist = MockPlaylist(f'Artist: {artist_query}')
            playlist_id = 'SEARCH_RESULT'
        elif playlist_name.startswith('search:'):
            query = playlist_name.split(':', 1)[1]
            print(f"模式: 按关键词搜索 '{query}'")
            with open('d:/anti/sorter_debug.log', 'a', encoding='utf-8') as dbg_log:
                dbg_log.write(f"DEBUG: Query value: '{query}'\n")
            tracks_raw = await db.search_tracks(SearchOptions(query=query))
            with open('d:/anti/sorter_debug.log', 'a', encoding='utf-8') as dbg_log:
                dbg_log.write(f"DEBUG: Found {len(tracks_raw)} tracks with query '{query}'\n")
            safe_query = query.replace(':', '_').replace('/', '_').replace('\\', '_')
            target_playlist = MockPlaylist(f'Search_{safe_query}')
            playlist_id = 'SEARCH_RESULT'
        else:
            target_playlist = None
            playlist_id = None
            if playlist_name.isdigit():
                playlist_id = playlist_name
                try:
                    for test_id in [int(playlist_id), playlist_id]:
                        try:
                            playlist_songs = list(pyrekordbox_db.get_playlist_songs(PlaylistID=test_id))
                            if playlist_songs:

                                class PlaylistObj:

                                    def __init__(self, id, name):
                                        self.id = id
                                        self.name = name
                                target_playlist = PlaylistObj(test_id, f'Playlist {test_id}')
                                playlist_id = test_id
                                break
                        except:
                            continue
                except:
                    pass
            if not target_playlist:
                all_playlists = await db.get_playlists()
                if playlist_name.isdigit():
                    try:
                        playlist_id_str = str(playlist_name)
                        playlist_id_int = int(playlist_name)
                        for p in all_playlists:
                            if str(p.id) == playlist_id_str or (isinstance(p.id, int) and p.id == playlist_id_int) or (isinstance(p.id, str) and p.id == playlist_id_str):
                                target_playlist = p
                                playlist_id = p.id
                                break
                    except:
                        pass
                if not target_playlist:
                    playlist_name_lower = playlist_name.lower().strip()
                    candidates = []
                    for p in all_playlists:
                        if p.name:
                            try:
                                p_name_lower = p.name.lower().strip()
                                if playlist_name_lower == p_name_lower:
                                    candidates.append((3, p))
                                elif playlist_name_lower in p_name_lower or p_name_lower in playlist_name_lower:
                                    candidates.append((1, p))
                            except:
                                pass
                    if candidates:

                        def sort_key(item):
                            score, p = item
                            is_int = 0
                            try:
                                int(p.id)
                                is_int = 1
                            except ValueError:
                                pass
                            mod_time = p.modified_date or ''
                            return (score, is_int, mod_time)
                        candidates.sort(key=sort_key, reverse=True)
                        target_playlist = candidates[0][1]
                        playlist_id = target_playlist.id
                        if len(candidates) > 1:
                            print(f'找到 {len(candidates)} 个匹配列表，自动选择最新/最标准的版本: {target_playlist.name} (ID: {target_playlist.id}, Tracks: {target_playlist.track_count})')
            if not target_playlist and playlist_name.isdigit():
                for test_id in [int(playlist_name), playlist_name]:
                    try:
                        test_songs = list(pyrekordbox_db.get_playlist_songs(PlaylistID=test_id))
                        if test_songs:

                            class PlaylistObj:

                                def __init__(self, id, name):
                                    self.id = id
                                    self.name = name
                            target_playlist = PlaylistObj(test_id, f'Playlist {test_id}')
                            playlist_id = test_id
                            break
                    except:
                        continue
            if not target_playlist:
                try:
                    safe_name = playlist_name.encode('utf-8', errors='ignore').decode('ascii', errors='ignore')
                    print(f'Playlist not found: {safe_name}')
                    print('请确认播放列表名称或ID是否正确')
                except:
                    print('Playlist not found')
                    print('Please confirm the playlist name or ID is correct')
                await db.disconnect()
                return
            if hasattr(target_playlist, 'is_folder') and target_playlist.is_folder:
                pass
            else:
                pass
        if 'tracks_raw' not in locals():
            tracks_raw = []
        if 'tracks_raw' not in locals():
            if not playlist_id:
                playlist_id = target_playlist.id
        if playlist_id == 'SEARCH_RESULT':
            pass
        elif getattr(target_playlist, 'is_folder', False):
            print(f"检测到 '{target_playlist.name}' 是一个文件夹，正在读取其下所有子列表...")
            try:

                def get_child_playlists(parent_id, all_playlists):
                    children = []
                    for p in all_playlists:
                        if p.parent_id == str(parent_id):
                            children.append(p)
                            if getattr(p, 'is_folder', False):
                                children.extend(get_child_playlists(p.id, all_playlists))
                    return children
                all_db_playlists = await db.get_playlists()
                all_child_playlists = get_child_playlists(playlist_id, all_db_playlists)
                tracks_raw = []
                seen_ids = set()
                for child in all_child_playlists:
                    if child.is_folder:
                        continue
                    child_tracks = await db.get_playlist_tracks(child.id)
                    for t in child_tracks:
                        if t.id not in seen_ids:
                            tracks_raw.append(t)
                            seen_ids.add(t.id)
                print(f"从文件夹 '{target_playlist.name}' 中合并了 {len(tracks_raw)} 首歌曲")
            except Exception as e:
                print(f'读取文件夹失败: {e}')
                tracks_raw = []
        else:
            try:
                print(f'找到播放列表: {target_playlist.name}')
            except:
                try:
                    print('找到播放列表')
                except:
                    print('Found playlist')
            try:
                tracks_raw = await db.get_playlist_tracks(playlist_id)
            except:
                print(f'[Fallback] 使用 pyrekordbox 直接读取 ID={playlist_id}...')
                try:
                    pid_int = int(playlist_id)
                    playlist_songs = list(pyrekordbox_db.get_playlist_songs(PlaylistID=pid_int))
                except ValueError:
                    playlist_songs = list(pyrekordbox_db.get_playlist_songs(PlaylistID=playlist_id))
                except Exception as e:
                    print(f'Fallback loading failed: {e}')
                    playlist_songs = []
                tracks_raw = []
                for song in playlist_songs:
                    if getattr(song, 'rb_local_deleted', 0) == 0:
                        content_id = getattr(song, 'ContentID', None)
                        if content_id:
                            content = pyrekordbox_db.get_content(ID=content_id)
                            if content:
                                from rekordbox_mcp.database import Track
                                track = Track(id=content.ID, content_uuid=content.UUID, title=content.Title or '', artist=content.ArtistName or '', file_path=content.FilePath or '', bpm=content.Tempo / 100.0 if content.Tempo else None, key=content.KeyName or '', energy=None)
                                tracks_raw.append(track)
        if not tracks_raw:
            try:
                print('播放列表为空')
            except:
                print('Playlist is empty')
            await db.disconnect()
            return
        try:
            try:
                print(f'DEBUG: 原始加载 tracks_raw 数量: {len(tracks_raw)}')
                for i, t in enumerate(tracks_raw[:5]):
                    print(f'DEBUG: Sample {i + 1}: {getattr(t, 'title', 'N/A')} | Path: {getattr(t, 'file_path', 'N/A')}')
            except:
                pass
            print(f'播放列表中共有 {len(tracks_raw)} 首歌曲')
            seen_paths = set()
            unique_tracks_raw = []
            for t in tracks_raw:
                file_path = getattr(t, 'file_path', '') or ''
                path_lower = file_path.lower().replace('\\', '/')
                if '/生成的set/' in path_lower:
                    continue
                if path_lower and path_lower not in seen_paths:
                    seen_paths.add(path_lower)
                    unique_tracks_raw.append(t)
            if len(unique_tracks_raw) < len(tracks_raw):
                print(f'  [去重] 原始: {len(tracks_raw)}首 -> 去重后: {len(unique_tracks_raw)}首')
                tracks_raw = unique_tracks_raw
            else:
                print(f'  [检查] 无重复曲目')
            print('\n开始深度分析歌曲...')
            print('=' * 60)
        except:
            print(f'Found {len(tracks_raw)} tracks in playlist')
            print('\nStarting deep analysis...')
            print('=' * 60)
        cache = load_cache()
        cache_updated = False
        tracks = []
        start_time = datetime.now()
        cached_count = 0
        analyzed_count = 0

        def analyze_single_track(track_idx_track):
            idx, track = track_idx_track
            true_content_id = getattr(track, 'ContentID', None) or getattr(track, 'id', None) or getattr(track, 'ID', None)
            file_path = track.file_path if hasattr(track, 'file_path') else None
            if not file_path or not os.path.exists(file_path):
                track_title = getattr(track, 'title', '') or getattr(track, 'Title', '')
                if track_title:
                    found = smart_find_track(track_title)
                    if found:
                        file_path = found[0]
                        print(f'  [RefinedFinder] Redirected to: {file_path}')
                    else:
                        print(f'  [DEBUG] 跳过歌曲: {track_title} (文件不存在且找不回: {file_path})')
                        return (idx, None, False, False)
                else:
                    print(f'  [DEBUG] 跳过 ID={true_content_id} (无路径且无标题)')
                    return (idx, None, False, False)
            db_bpm = track.bpm if hasattr(track, 'bpm') and track.bpm else None
            ai_data = None
            cached_res = get_cached_analysis(file_path, cache) if file_path else None
            if isinstance(cached_res, tuple):
                existing_analysis, needs_update = cached_res
            else:
                existing_analysis, needs_update = (cached_res, False)
            is_cached = existing_analysis is not None and (not needs_update)
            if existing_analysis and (not needs_update):
                analysis = existing_analysis
            else:
                analysis = deep_analyze_track(file_path, db_bpm, existing_analysis=existing_analysis) if file_path else None
                if analysis and file_path:
                    cache_analysis(file_path, analysis, cache)
                    was_analyzed = True if not existing_analysis else True
                else:
                    was_analyzed = False
            db_key = track.key or ''
            detected_key = analysis.get('key') if analysis else None
            if db_key and db_key not in ['未知', 'Unknown', '']:
                final_key = convert_open_key_to_camelot(db_key)
            else:
                final_key = detected_key if detected_key else '未知'
            manual_cues = []
            hotcues_map = {}
            try:
                cue_query = text('SELECT ID, Kind, InMsec, Comment FROM djmdCue WHERE ContentID = :content_id AND rb_local_deleted = 0')
                with pyrekordbox_db.session.no_autoflush:
                    cue_results = pyrekordbox_db.session.execute(cue_query, {'content_id': true_content_id}).fetchall()
                    for cid, kind, inmsec, comment in cue_results:
                        time_sec = inmsec / 1000.0
                        manual_cues.append({'kind': kind, 'time': time_sec, 'comment': comment or ''})
                        if 1 <= kind <= 8:
                            hotcues_map[kind] = time_sec
            except Exception as cue_err:
                if 'concurrent operations' in str(cue_err):
                    print(f'Warning: DB Busy for track {true_content_id}, retrying once...')
                    import time
                    time.sleep(0.1)
                    try:
                        with pyrekordbox_db.session.no_autoflush:
                            cue_results = pyrekordbox_db.session.execute(cue_query, {'content_id': true_content_id}).fetchall()
                            for cid, kind, inmsec, comment in cue_results:
                                time_sec = inmsec / 1000.0
                                manual_cues.append({'kind': kind, 'time': time_sec, 'comment': comment or ''})
                                if 1 <= kind <= 8:
                                    hotcues_map[kind] = time_sec
                    except:
                        pass
                else:
                    print(f'Warning: Failed to fetch cues for track {true_content_id}: {cue_err}')
            stags = set()
            VOCAL_KW = ['vocal', 'acapella', 'sing', 'voice', '人声']
            DROP_KW = ['drop', 'hook', 'energy', 'peak', '高潮', '炸']
            for cue in manual_cues:
                comment = cue['comment'].lower()
                if any((kw in comment for kw in VOCAL_KW)):
                    stags.add('VOCAL')
                if any((kw in comment for kw in DROP_KW)):
                    stags.add('DROP')
            hotcue_A = hotcues_map.get(1)
            hotcue_B = hotcues_map.get(2)
            hotcue_C = hotcues_map.get(3)
            hotcue_D = hotcues_map.get(4)
            final_mix_in = hotcue_A or (analysis.get('mix_in_point') if analysis else None)
            final_mix_out = hotcue_C or (analysis.get('mix_out_point') if analysis else None)
            entry_bars = 0
            exit_bars = 0
            track_bpm = analysis.get('bpm') or db_bpm or 120
            if hotcue_A and hotcue_B:
                entry_bars = round((hotcue_B - hotcue_A) * (track_bpm / 60.0) / 4.0)
            if hotcue_C and hotcue_D:
                exit_bars = round((hotcue_D - hotcue_C) * (track_bpm / 60.0) / 4.0)
            mix_info = ''
            if entry_bars > 0:
                mix_info += f'[Entry: {entry_bars}b] '
            elif hotcue_A:
                mix_info += '[Manual A-In] '
            if exit_bars > 0:
                mix_info += f'[Exit: {exit_bars}b] '
            elif hotcue_C:
                mix_info += '[Manual C-Out] '
            artist = track.artist or ''
            title = track.title or ''
            filename = Path(file_path).stem
            if artist and title:
                pass
            elif not artist and (not title):
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
                    artist = 'Unknown'
            elif not artist:
                if ' - ' in filename:
                    artist = filename.split(' - ', 1)[0].strip()
                elif '-' in filename:
                    artist = filename.split('-', 1)[0].strip()
                else:
                    artist = 'Unknown'
            elif not title:
                title = filename
            track_dict = {'id': true_content_id, 'content_uuid': getattr(track, 'content_uuid', None), 'title': title, 'artist': artist, 'file_path': file_path, 'bpm': analysis.get('bpm') if analysis else db_bpm or 120, 'key': final_key, 'energy': analysis.get('energy') if analysis else 50, 'duration': (ai_data.get('format', {}).get('duration') if ai_data else None) or (analysis.get('duration') if analysis else 180), 'mix_in_point': final_mix_in, 'mix_out_point': final_mix_out, 'hotcue_A': hotcue_A, 'hotcue_B': hotcue_B, 'hotcue_C': hotcue_C, 'hotcue_D': hotcue_D, 'entry_bars': entry_bars, 'exit_bars': exit_bars, 'manual_cues': manual_cues, 'mix_info': mix_info.strip(), 'genre': analysis.get('genre') if analysis else None, 'structure': analysis.get('structure') if analysis else None, 'vocals': analysis.get('vocals') if analysis else None, 'drums': analysis.get('drums') if analysis else None, 'audio_quality_kbps': int(ai_data.get('format', {}).get('bitrate', 0) / 1000) if ai_data else 0, 'sample_rate': ai_data.get('format', {}).get('sampleRate') if ai_data else 0, 'brightness': analysis.get('brightness') if analysis else 0.5, 'kick_drum_power': analysis.get('kick_drum_power') if analysis else 0.5, 'sub_bass_level': analysis.get('sub_bass_level') if analysis else 0.5, 'dynamic_range_db': analysis.get('dynamic_range_db') if analysis else 10, 'valence': analysis.get('valence') if analysis else 0.5, 'arousal': analysis.get('arousal') if analysis else 0.5, 'phrase_length': analysis.get('phrase_length') if analysis else 16, 'intro_vocal_ratio': analysis.get('intro_vocal_ratio') if analysis else 0.5, 'outro_vocal_ratio': analysis.get('outro_vocal_ratio') if analysis else 0.5, 'busy_score': analysis.get('busy_score') if analysis else 0.5, 'tonal_balance_low': analysis.get('tonal_balance_low') if analysis else 0.5, 'tonal_balance_mid': analysis.get('tonal_balance_mid') if analysis else 0.3, 'tonal_balance_high': analysis.get('tonal_balance_high') if analysis else 0.1, 'hook_strength': analysis.get('hook_strength') if analysis else 0.5, 'tags': analysis.get('tags', []) if analysis else [], 'semantic_tags': list(stags) if 'stags' in locals() else [], 'time_signature': analysis.get('time_signature', '4/4') if analysis else '4/4', 'swing_dna': analysis.get('swing_dna', 0.0) if analysis else 0.0, 'spectral_bands': analysis.get('spectral_bands', {}) if analysis else {}}
            if PHRASE_READER_AVAILABLE and track_dict.get('content_uuid'):
                try:
                    pssi_phrases = PHRASE_READER.get_phrases(track_dict['content_uuid'], bpm=track_dict['bpm'])
                    if pssi_phrases:
                        intro_ints = [p['intensity'] for p in pssi_phrases[:2] if p.get('intensity') is not None]
                        outro_ints = [p['intensity'] for p in pssi_phrases[-2:] if p.get('intensity') is not None]
                        track_dict['pssi_intensity_intro'] = sum(intro_ints) / len(intro_ints) if intro_ints else 3.0
                        track_dict['pssi_intensity_outro'] = sum(outro_ints) / len(outro_ints) if outro_ints else 3.0
                        track_dict['pssi_data_available'] = True
                except Exception as pssi_err:
                    print(f'Warning: Failed to inject PSSI data: {pssi_err}')
            pro_hotcues = {}
            if HOTCUE_GENERATOR_ENABLED and analysis and file_path:
                try:
                    target_points = {'mix_in': track_dict['mix_in_point'], 'mix_out': track_dict['mix_out_point']}
                    if track_dict.get('hotcue_B'):
                        target_points['transition_in'] = track_dict['hotcue_B']
                    raw_pro = generate_hotcues(file_path, bpm=track_dict['bpm'], duration=track_dict['duration'], structure=analysis, content_uuid=track_dict.get('content_uuid'), content_id=track_dict.get('id'), custom_mix_points=target_points, track_tags=track_dict.get('track_tags', {}))
                    pro_hotcues = raw_pro.get('hotcues', {})
                except Exception as e:
                    print(f'Warning: Pro Hotcue generation failed: {e}')
            track_dict['pro_hotcues'] = pro_hotcues
            return (idx, track_dict, is_cached, analysis is not None and (not is_cached))

        def collect_results(results_list, idx, track_dict, is_cached, was_analyzed):
            if track_dict:
                results_list.append((idx, track_dict))
                return True
            return False
        try:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            max_workers = min(4, len(tracks_raw))
            track_results = []
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(analyze_single_track, (idx, track)): (idx, track) for idx, track in enumerate(tracks_raw, 1)}
                completed = 0
                for future in as_completed(futures):
                    completed += 1
                    try:
                        res = future.result()
                        if res and len(res) == 4:
                            idx, track_dict, is_cached, was_analyzed = res
                            if track_dict:
                                track_results.append((idx, track_dict))
                                if is_cached:
                                    cached_count += 1
                                if was_analyzed:
                                    analyzed_count += 1
                                    cache_updated = True
                            else:
                                pass
                        else:
                            print(f'DEBUG: Future {completed} 返回了异常格式: {res}')
                        if completed % 5 == 0 or completed == len(tracks_raw):
                            elapsed = (datetime.now() - start_time).total_seconds()
                            if completed > 0:
                                avg_time = elapsed / completed
                                remaining = (len(tracks_raw) - completed) * avg_time
                                progress_pct = completed / len(tracks_raw) * 100
                                try:
                                    print(f'[进度] {completed}/{len(tracks_raw)} ({progress_pct:.1f}%) - 已用时间: {int(elapsed / 60)}分{int(elapsed % 60)}秒 - 预计剩余: {int(remaining / 60)}分{int(remaining % 60)}秒')
                                    print(f'  缓存: {cached_count}首 | 新分析: {analyzed_count}首')
                                except:
                                    print(f'[Progress] {completed}/{len(tracks_raw)} ({progress_pct:.1f}%)')
                    except Exception as e:
                        try:
                            print(f'分析失败: {e}')
                        except:
                            pass
            track_results.sort(key=lambda x: x[0])
            tracks = [tr[1] for tr in track_results]
        except ImportError:
            for idx, track in enumerate(tracks_raw, 1):
                file_path = track.file_path if hasattr(track, 'file_path') else None
                if not file_path or not os.path.exists(file_path):
                    try:
                        path_query = text('SELECT Path FROM djmdContent WHERE ID = :content_id')
                        path_result = pyrekordbox_db.session.execute(path_query, {'content_id': track.id}).fetchone()
                        if path_result and path_result[0]:
                            file_path = path_result[0]
                            if not os.path.exists(file_path):
                                potential_paths = [os.path.join('D:\\song', os.path.basename(file_path)), file_path]
                                for pp in potential_paths:
                                    if os.path.exists(pp):
                                        file_path = pp
                                        break
                    except:
                        pass
                if not file_path or not os.path.exists(file_path):
                    continue
                db_bpm = track.bpm if hasattr(track, 'bpm') else None
                cached_analysis = get_cached_analysis(file_path, cache)
                is_cached = cached_analysis is not None
                if cached_analysis:
                    analysis = cached_analysis
                    cached_count += 1
                else:
                    analysis = deep_analyze_track(file_path, db_bpm)
                    if analysis:
                        cache_analysis(file_path, analysis, cache)
                        cache_updated = True
                        analyzed_count += 1
                detected_key = analysis.get('key') if analysis else None
                db_key = track.key or ''
                final_key = detected_key if detected_key else db_key if db_key else '未知'
                track_dict = {'id': track.id, 'title': track.title or '', 'artist': track.artist or '', 'file_path': file_path, 'bpm': analysis.get('bpm') if analysis else db_bpm or 120, 'key': final_key, 'energy': analysis.get('energy') if analysis else 50, 'duration': analysis.get('duration') if analysis else 180, 'mix_in_point': analysis.get('mix_in_point') if analysis else None, 'mix_out_point': analysis.get('mix_out_point') if analysis else None, 'genre': analysis.get('genre') if analysis else None, 'structure': analysis.get('structure') if analysis else None, 'vocals': analysis.get('vocals') if analysis else None, 'drums': analysis.get('drums') if analysis else None, 'brightness': analysis.get('brightness') if analysis else 0.5, 'kick_drum_power': analysis.get('kick_drum_power') if analysis else 0.5, 'sub_bass_level': analysis.get('sub_bass_level') if analysis else 0.5, 'dynamic_range_db': analysis.get('dynamic_range_db') if analysis else 10, 'valence': analysis.get('valence') if analysis else 0.5, 'arousal': analysis.get('arousal') if analysis else 0.5, 'phrase_length': analysis.get('phrase_length') if analysis else 16, 'intro_vocal_ratio': analysis.get('intro_vocal_ratio') if analysis else 0.5, 'outro_vocal_ratio': analysis.get('outro_vocal_ratio') if analysis else 0.5, 'busy_score': analysis.get('busy_score') if analysis else 0.5, 'tonal_balance_low': analysis.get('tonal_balance_low') if analysis else 0.5, 'tonal_balance_mid': analysis.get('tonal_balance_mid') if analysis else 0.3, 'tonal_balance_high': analysis.get('tonal_balance_high') if analysis else 0.1, 'hook_strength': analysis.get('hook_strength') if analysis else 0.5, 'intro_bars': round((analysis.get('intro_end_time') or analysis.get('mix_in_point') or 0) * (analysis.get('bpm') or 120) / 240) if analysis else 8, 'outro_bars': round(((analysis.get('duration') or 180) - (analysis.get('outro_start_time') or analysis.get('mix_out_point') or 180)) * (analysis.get('bpm') or 120) / 240) if analysis else 8, 'first_drop_time': analysis.get('first_drop_time') if analysis else None, 'lufs_db': analysis.get('loudness_lufs') if analysis else -10.0, 'swing_dna': analysis.get('swing_dna', 0.0) if analysis else 0.0, 'time_signature': analysis.get('time_signature', '4/4') if analysis else '4/4', 'spectral_bands': analysis.get('spectral_bands', {}) if analysis else {}}
                tracks.append(track_dict)
                if idx == 1 or idx % 10 == 0 or idx == len(tracks_raw):
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if idx > 0:
                        avg_time_per_track = elapsed / idx
                        remaining = (len(tracks_raw) - idx) * avg_time_per_track
                        progress_pct = idx / len(tracks_raw) * 100
                        try:
                            print(f'[进度] {idx}/{len(tracks_raw)} ({progress_pct:.1f}%) - 已用时间: {int(elapsed / 60)}分{int(elapsed % 60)}秒 - 预计剩余: {int(remaining / 60)}分{int(remaining % 60)}秒')
                            print(f'  缓存: {cached_count}首 | 新分析: {analyzed_count}首')
                            if idx < len(tracks_raw):
                                status = '[缓存]' if is_cached else '[分析中]'
                                print(f'  {status} {(track.title[:50] if track.title else 'Unknown')}...')
                        except:
                            print(f'[Progress] {idx}/{len(tracks_raw)} ({progress_pct:.1f}%) - Elapsed: {int(elapsed / 60)}m{int(elapsed % 60)}s - Remaining: {int(remaining / 60)}m{int(remaining % 60)}s')
                            print(f'  Cached: {cached_count} | New: {analyzed_count}')
        if cache_updated:
            save_cache(cache)
            try:
                print(f'\n[缓存] 已保存 {analyzed_count} 首新歌曲的分析结果到缓存')
            except:
                print(f'\n[Cache] Saved {analyzed_count} new analysis results')
        total_time = (datetime.now() - start_time).total_seconds()
        seen_ids = set()
        seen_paths = set()
        seen_titles = set()
        unique_tracks = []
        for track in tracks:
            tid = track.get('id')
            path = track.get('file_path', '').lower().replace('\\', '/')
            title_key = f'{track.get('artist', '')}_{track.get('title', '')}'.lower().strip()
            is_duplicate = False
            if tid and tid in seen_ids:
                is_duplicate = True
            elif path and path in seen_paths:
                is_duplicate = True
            elif title_key and title_key in seen_titles and (title_key != 'unknown_unknown') and (title_key != '_'):
                is_duplicate = True
            if not is_duplicate:
                if tid:
                    seen_ids.add(tid)
                if path:
                    seen_paths.add(path)
                if title_key and title_key != 'unknown_unknown' and (title_key != '_'):
                    seen_titles.add(title_key)
                unique_tracks.append(track)
            else:
                pass
        if len(unique_tracks) < len(tracks):
            print(f'[去重] 移除 {len(tracks) - len(unique_tracks)} 首原始重复记录 (保留 {len(unique_tracks)} 首)')
        tracks = unique_tracks
        for t in tracks:
            if t.get('bpm') is None:
                t['bpm'] = 120.0
            if t.get('energy') is None:
                t['energy'] = 50.0
            raw_key = t.get('key')
            if raw_key is None:
                t['key'] = '1A'
            elif hasattr(raw_key, 'Name'):
                t['key'] = raw_key.Name if raw_key.Name else '1A'
            elif not isinstance(raw_key, str):
                t['key'] = str(raw_key) if raw_key else '1A'
            try:
                t['bpm'] = float(t['bpm'])
            except:
                t['bpm'] = 120.0
            try:
                t['energy'] = float(t['energy'])
            except:
                t['energy'] = 50.0
        try:
            print('=' * 60)
            try:
                print(f'[完成] 分析完成！成功分析 {len(tracks)} 首歌曲')
            except UnicodeEncodeError:
                print(f'[完成] Analysis complete! Successfully analyzed {len(tracks)} tracks')
            try:
                print(f'   总耗时: {int(total_time / 60)}分{int(total_time % 60)}秒')
            except UnicodeEncodeError:
                print(f'   Total time: {int(total_time / 60)}m{int(total_time % 60)}s')
            try:
                print(f'\n开始排序和生成Set...')
            except UnicodeEncodeError:
                print(f'\nStarting sorting and set generation...')
            print('=' * 60)
        except:
            print('=' * 60)
            print(f'[完成] Analysis complete! Successfully analyzed {len(tracks)} tracks')
            print(f'   Total time: {int(total_time / 60)}m{int(total_time % 60)}s')
            print(f'\nStarting sorting and set generation...')
            print('=' * 60)
        if enable_bridge:
            try:
                from genre_compatibility import detect_genre_from_filename, get_compatible_genres, GENRE_FAMILIES, CROSS_FAMILY_COMPATIBILITY
                BRIDGEABLE_FAMILIES = ['house_family', 'techno_family', 'breaks_family', 'latin_family', 'trance_family']
                bridgeable_styles = []
                for family in BRIDGEABLE_FAMILIES:
                    bridgeable_styles.extend(GENRE_FAMILIES.get(family, []))
                bridgeable_styles.extend(['house', 'electronic', 'techno'])
                style_counts = {}
                for track in tracks:
                    style = detect_genre_from_filename(Path(track.get('file_path', '')).stem)
                    style_counts[style] = style_counts.get(style, 0) + 1
                dominant_style = max(style_counts.items(), key=lambda x: x[1])[0] if style_counts else 'electronic'
                if dominant_style in bridgeable_styles or dominant_style in ['house', 'electronic', 'techno']:
                    print(f'\n[桥接模式] 主导风格: {dominant_style}')
                    cache_file = Path('song_analysis_cache.json')
                    if cache_file.exists():
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            all_cache = json.load(f)
                        compatible_styles = get_compatible_genres(dominant_style)
                        compatible_styles.append(dominant_style)
                        compatible_styles.extend(['house', 'electronic'])
                        compatible_styles = list(set(compatible_styles))
                        existing_paths = {t.get('file_path', '').lower().replace('\\', '/') for t in tracks}
                        bridge_candidates = []
                        for hash_key, data in all_cache.items():
                            file_path = data.get('file_path', '')
                            if file_path.lower().replace('\\', '/') in existing_paths:
                                continue
                            analysis = data.get('analysis', {})
                            if not analysis or 'bpm' not in analysis:
                                continue
                            style = detect_genre_from_filename(Path(file_path).stem)
                            if style in compatible_styles:
                                bridge_candidates.append({'file_path': file_path, 'title': Path(file_path).stem, 'artist': 'Unknown', 'bpm': analysis.get('bpm', 0), 'key': analysis.get('key', ''), 'energy': analysis.get('energy', 50), 'duration': analysis.get('duration', 180), 'is_bridge': True, 'bridge_style': style})
                        print(f'[桥接模式] 找到 {len(bridge_candidates)} 首兼容风格歌曲')
                        if bridge_candidates:
                            import random
                            random.shuffle(bridge_candidates)
                            if len(tracks) < songs_per_set:
                                max_bridge = int(songs_per_set * 1.2) - len(tracks)
                                tracks.extend(bridge_candidates[:max_bridge])
                                print(f'[桥接模式] 歌曲不足，补充 {min(max_bridge, len(bridge_candidates))} 首桥接歌曲')
                            else:
                                print(f'[桥接模式] 播放列表歌曲充足({len(tracks)}首)，无需桥接')
                else:
                    print(f'\n[桥接模式] 风格 {dominant_style} 不适合桥接，跳过')
            except Exception as e:
                print(f'[桥接模式] 错误: {e}')
        if is_boutique:
            print('\n[Boutique] 精品单体模式：跳过BPM自动分组，强制合并为单个精品Set')
            tracks.sort(key=lambda x: x.get('bpm', 0))
            bpm_groups = [tracks]
        else:
            try:
                print('\n[BPM分组] 正在按BPM自动分组...')
            except:
                print('\n[BPM Grouping] Auto-grouping by BPM...')
            bpm_groups = auto_group_by_bpm(tracks, max_bpm_range=25.0)
        try:
            print(f'[BPM分组] 自动分成 {len(bpm_groups)} 个BPM区间:')
            for i, group in enumerate(bpm_groups, 1):
                label = get_bpm_group_label(group)
                print(f'  - 区间{i}: {label} ({len(group)}首)')
        except:
            print(f'[BPM Grouping] Split into {len(bpm_groups)} BPM ranges')
        split_cfg = DJ_RULES.get('split', {}) if DJ_RULES else {}
        target_minutes = split_cfg.get('target_duration_minutes', 90.0)
        min_s = split_cfg.get('min_songs', 20)
        max_s = split_cfg.get('max_songs', 60)
        preset_map = {'club': (60.0, 15, 45), 'radio': (45.0, 10, 30), 'warm_up': (90.0, 20, 50), 'extended': (120.0, 30, 80), 'default': (target_minutes, min_s, max_s)}
        if preset in preset_map:
            target_minutes, min_s, max_s = preset_map[preset]
            try:
                print(f"[Preset] 应用预设 '{preset}': 目标 {target_minutes}分钟, {min_s}-{max_s}首")
            except:
                pass
        sets = []
        set_idx = 0
        is_dual_mode_requested = is_boutique and is_live
        if (is_dual_mode_requested or (is_boutique and any((len(g) > max_s for g in bpm_groups)))) and (not is_master):
            try:
                print(f'[Boutique] 检测到大型歌单，自动升级为 Master 总线算法以确保全局最优切分...')
            except:
                pass
            is_master = True
        for group_idx, bpm_group in enumerate(bpm_groups):
            if is_master:
                print(f'[Master] 正在进行全局连贯排序 (共 {len(bpm_group)} 首)...')
                global_sorted_tracks, _, _ = enhanced_harmonic_sort(bpm_group, len(bpm_group), is_boutique=is_boutique)
                if is_boutique:
                    try:
                        print(f'[Boutique] 精品模式生效：正在从 {len(global_sorted_tracks)} 首候选曲中甄选最佳 Set (目标 30-45 首)...')
                    except:
                        print(f'[Boutique] Mode Active: Selecting best 30-45 tracks from {len(global_sorted_tracks)} candidates...')
                    min_target = 30
                    max_target = 45
                    if len(global_sorted_tracks) <= max_target:
                        print(f'   - 候选不足 {max_target} 首，保留全量 {len(global_sorted_tracks)} 首')
                        final_cut = global_sorted_tracks
                    else:
                        best_cut_idx = max_target
                        max_tail_score = -9999
                        scan_start = min(len(global_sorted_tracks), min_target)
                        scan_end = min(len(global_sorted_tracks), max_target + 1)
                        for i in range(scan_start, scan_end):
                            track = global_sorted_tracks[i - 1]
                            score = 0
                            phase = track.get('assigned_phase', '')
                            if phase == 'Cool-down':
                                score += 20
                            elif phase == 'Intense':
                                score += 10
                            if track.get('is_bridge'):
                                score -= 50
                            if score > max_tail_score:
                                max_tail_score = score
                                best_cut_idx = i
                        print(f'   - 智能截断：选定 {best_cut_idx} 首 (Score: {max_tail_score})')
                        final_cut = global_sorted_tracks[:best_cut_idx]
                    if final_cut:
                        final_cut[0]['is_boutique_start'] = True
                    sets.append(final_cut)
                    print(f'[Dual Mode] 已生成 Boutique Highlight Set ({len(final_cut)} tracks). 继续生成全量 Live Sets...')
                print(f'[Master] 正在寻找最佳切分点 (Pivots)...')
                current_ptr = 0
                while current_ptr < len(global_sorted_tracks):
                    chunk = []
                    dur = 0
                    if is_boutique:
                        target_s = max(25, min_s or 0)
                        target_d = max(90 * 60, (target_minutes or 0) * 60)
                    else:
                        target_s = min_s or 0
                        target_d = (target_minutes or 0) * 60
                    est_songs = 0
                    temp_dur = 0
                    for k in range(current_ptr, len(global_sorted_tracks)):
                        temp_dur += global_sorted_tracks[k].get('duration', 180)
                        est_songs += 1
                        if temp_dur >= target_d and est_songs >= (min_s or 0):
                            break
                    if len(global_sorted_tracks) - (current_ptr + est_songs) < (min_s or 0) // 2:
                        est_songs = len(global_sorted_tracks) - current_ptr
                    pivot_idx = current_ptr + est_songs
                    if pivot_idx < len(global_sorted_tracks):
                        window_start = max(current_ptr + (min_s or 25), pivot_idx - 5)
                        window_end = min(len(global_sorted_tracks) - (min_s or 25) // 2, pivot_idx + 5)
                        best_p = pivot_idx
                        max_p_score = -9999
                        for w in range(window_start, window_end):
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
                current_sub_group = []
                current_duration = 0
                for i, track in enumerate(bpm_group):
                    track_dur = track.get('duration', 180)
                    current_sub_group.append(track)
                    current_duration += track_dur
                    is_last = i == len(bpm_group) - 1
                    reached_duration = current_duration >= (target_minutes or 0) * 60
                    reached_max_songs = len(current_sub_group) >= (max_s or 999)
                    if not is_boutique and (reached_duration and len(current_sub_group) >= min_s or reached_max_songs) or is_last:
                        remaining = len(bpm_group) - (i + 1)
                        if not is_last and remaining > 0 and (remaining < min_s):
                            continue
                        set_idx += 1
                        label = '精品 Set (Boutique Mode)' if is_boutique else get_bpm_group_label(current_sub_group)
                        try:
                            print(f'正在排序 Set {set_idx} - {label} ({len(current_sub_group)} 首歌曲, 时长: {current_duration / 60:.1f}min)...')
                        except:
                            pass
                        sorted_tracks, _, _ = enhanced_harmonic_sort(current_sub_group, len(current_sub_group), is_boutique=is_boutique)
                        sets.append(sorted_tracks)
                        current_sub_group = []
                        current_duration = 0
            if is_boutique:
                break
        try:
            print('\n[BPM平滑] 正在优化每个Set的BPM序列...')
        except:
            print('\n[BPM Smoothing] Optimizing BPM sequence for each set...')
        smoothed_sets = []
        for i, set_tracks in enumerate(sets):
            smoothed = smooth_bpm_sequence(set_tracks)
            smoothed_sets.append(smoothed)

            def count_bpm_jumps(tracks, threshold=15):
                jumps = 0
                for j in range(1, len(tracks)):
                    bpm_diff = abs(tracks[j].get('bpm', 0) - tracks[j - 1].get('bpm', 0))
                    if bpm_diff > threshold:
                        jumps += 1
                return jumps
            before_jumps = count_bpm_jumps(set_tracks)
            after_jumps = count_bpm_jumps(smoothed)
            if before_jumps > after_jumps:
                try:
                    print(f'  Set {i + 1}: BPM跳跃 {before_jumps} -> {after_jumps} (优化了 {before_jumps - after_jumps} 处)')
                except:
                    print(f'  Set {i + 1}: BPM jumps {before_jumps} -> {after_jumps}')
        sets = smoothed_sets
        if len(sets) > 0:
            try:
                print(f'\n[进化启动] 正在进行全局退火优化 (Phase 3)...')
            except:
                print(f'\n[Evolution] Starting Global Optimization (Phase 3)...')
            opt_config = {'max_bpm_jump': 8.0, 'min_key_score': 60.0, 'active_profile': ACTIVE_PROFILE}
            improved_count = optimize_global_sets(sets, opt_config, progress_logger)
            if improved_count > 0:
                try:
                    print(f'  [完成] 已成功优化 {improved_count} 个 Set 的全局流向')
                except:
                    print(f'  [Done] Optimized global flow for {improved_count} sets')
            else:
                try:
                    print(f'  [完成] 当前序列已是全局最优或未发现更好排列')
                except:
                    print(f'  [Done] Current sequence is globally optimal')
        bridge_insertions = []
        skip_bridge_track = not enable_bridge_track
        if skip_bridge_track:
            print('\n[桥接曲] 桥接曲功能已禁用（亚洲流行风格）')
        try:
            if not skip_bridge_track:
                print('\n[桥接曲] 正在检测BPM跨度过大的位置...')
            cache_file = Path('song_analysis_cache.json')
            all_cache = {}
            if cache_file.exists() and (not skip_bridge_track):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    all_cache = json.load(f)
            used_paths = set()
            for set_tracks in sets:
                for track in set_tracks:
                    used_paths.add(track.get('file_path', ''))
            new_sets = []
            for set_idx, set_tracks in enumerate(sets):
                new_set = []
                for i, track in enumerate(set_tracks):
                    new_set.append(track)
                    if skip_bridge_track:
                        continue
                    if i < len(set_tracks) - 1:
                        curr_bpm = track.get('bpm', 0)
                        next_track = set_tracks[i + 1]
                        next_bpm = next_track.get('bpm', 0)
                        if curr_bpm and next_bpm:
                            bpm_diff = abs(curr_bpm - next_bpm)
                            bridge_trigger = 8.0 if is_boutique else 15.0
                            if bpm_diff > bridge_trigger:
                                target_bpm = (curr_bpm + next_bpm) / 2
                                curr_key = track.get('key', '')
                                next_key = next_track.get('key', '')
                                best_bridge = None
                                best_score = -999
                                best_reasons = []
                                try:
                                    from genre_compatibility import are_genres_compatible, detect_genre_from_filename, get_genre_family
                                    has_genre_check = True
                                except ImportError:
                                    has_genre_check = False
                                curr_genre = detect_genre_from_filename(track.get('file_path', '')) or track.get('genre', '') if has_genre_check else ''
                                next_genre = detect_genre_from_filename(next_track.get('file_path', '')) or next_track.get('genre', '') if has_genre_check else ''
                                for hash_key, data in all_cache.items():
                                    file_path = data.get('file_path', '')
                                    if file_path in used_paths:
                                        continue
                                    analysis = data.get('analysis', {})
                                    bridge_bpm = analysis.get('bpm', 0)
                                    bridge_key = analysis.get('key', '')
                                    if not bridge_bpm:
                                        continue
                                    if has_genre_check:
                                        bridge_genre = detect_genre_from_filename(file_path) or analysis.get('genre', '')
                                        electronic_families = ['house_family', 'techno_family', 'bass_family', 'trance_family', 'breaks_family']
                                        asian_families = ['asian_pop_family']
                                        curr_fam = get_genre_family(curr_genre)
                                        next_fam = get_genre_family(next_genre)
                                        bridge_fam = get_genre_family(bridge_genre)
                                        if curr_fam in electronic_families and next_fam in electronic_families:
                                            if bridge_fam in asian_families or bridge_fam == 'pop_family':
                                                continue
                                        if curr_fam in asian_families:
                                            if bridge_fam in electronic_families:
                                                continue
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
                                        if not compatible_with_curr or not compatible_with_next:
                                            continue
                                    score = 0
                                    reasons = []
                                    if has_genre_check and bridge_genre:
                                        reasons.append(f'风格 {bridge_genre} 兼容')
                                        score += 20
                                    bpm_to_curr = abs(bridge_bpm - curr_bpm)
                                    bpm_to_next = abs(bridge_bpm - next_bpm)
                                    max_single_gap = max(bpm_to_curr, bpm_to_next)
                                    if min(curr_bpm, next_bpm) <= bridge_bpm <= max(curr_bpm, next_bpm):
                                        mid_bpm = (curr_bpm + next_bpm) / 2
                                        distance_to_mid = abs(bridge_bpm - mid_bpm)
                                        mid_bonus = max(0, 20 - distance_to_mid)
                                        score += 50 + mid_bonus
                                        if max_single_gap <= 12:
                                            score += 20
                                            reasons.append(f'BPM {bridge_bpm:.1f} 完美桥接（两边跨度都<=12）')
                                        elif max_single_gap <= 15:
                                            score += 10
                                            reasons.append(f'BPM {bridge_bpm:.1f} 在 {curr_bpm:.1f}-{next_bpm:.1f} 之间')
                                        else:
                                            reasons.append(f'BPM {bridge_bpm:.1f} 在范围内但跨度仍较大')
                                    elif bpm_to_curr <= 8 and bpm_to_next <= 8:
                                        score += 30
                                        reasons.append(f'BPM {bridge_bpm:.1f} 接近两首歌')
                                    elif bpm_to_curr <= 12 or bpm_to_next <= 12:
                                        score += 10
                                    else:
                                        continue
                                    if bridge_key and curr_key and next_key:
                                        key_score_curr = get_key_compatibility_flexible(curr_key, bridge_key) or 0
                                        key_score_next = get_key_compatibility_flexible(bridge_key, next_key) or 0
                                        avg_key_score = (key_score_curr + key_score_next) / 2
                                        if avg_key_score >= 80:
                                            score += 30
                                            reasons.append(f'调性 {bridge_key} 与两首歌都和谐')
                                        elif avg_key_score >= 60:
                                            score += 15
                                            reasons.append(f'调性 {bridge_key} 兼容')
                                    curr_energy = track.get('energy', 50)
                                    next_energy = next_track.get('energy', 50)
                                    bridge_energy = analysis.get('energy', 50)
                                    if min(curr_energy, next_energy) <= bridge_energy <= max(curr_energy, next_energy):
                                        score += 10
                                        reasons.append('能量平滑过渡')
                                    if score > best_score:
                                        best_score = score
                                        best_bridge = {'id': data.get('id') or data.get('ContentID'), 'content_uuid': data.get('content_uuid') or data.get('UUID'), 'file_path': file_path, 'title': Path(file_path).stem, 'artist': data.get('artist') or 'Unknown', 'bpm': bridge_bpm, 'key': bridge_key, 'energy': bridge_energy, 'duration': analysis.get('duration', 180), 'structure': analysis.get('structure') or analysis, 'vocals': analysis.get('vocals'), 'is_bridge': True, 'bridge_reason': ' | '.join(reasons)}
                                        best_reasons = reasons
                                min_bridge_score = 60 if is_boutique else 40
                                if best_bridge and best_score >= min_bridge_score:
                                    new_set.append(best_bridge)
                                    used_paths.add(best_bridge['file_path'])
                                    bridge_info = {'set_idx': set_idx + 1, 'position': i + 1, 'prev_track': track.get('title', 'Unknown')[:30], 'next_track': next_track.get('title', 'Unknown')[:30], 'bridge_track': best_bridge['title'][:30], 'prev_bpm': curr_bpm, 'next_bpm': next_bpm, 'bridge_bpm': best_bridge['bpm'], 'original_gap': bpm_diff, 'new_gap_1': abs(curr_bpm - best_bridge['bpm']), 'new_gap_2': abs(best_bridge['bpm'] - next_bpm), 'reasons': best_reasons}
                                    bridge_insertions.append(bridge_info)
                                    print(f'  [Set {set_idx + 1}] 插入桥接曲: {best_bridge['title'][:40]}')
                                    print(f'    原BPM跨度: {bpm_diff:.1f} -> 新跨度: {bridge_info['new_gap_1']:.1f} + {bridge_info['new_gap_2']:.1f}')
                                    print(f'    原因: {best_bridge['bridge_reason']}')
                new_sets.append(new_set)
            sets = new_sets
            final_unique_sets = []
            global_seen_paths = set()
            duplicate_count = 0
            for s_idx, s_tracks in enumerate(sets):
                if s_idx == 0:
                    final_unique_sets.append(s_tracks)
                    for t in s_tracks:
                        p = t.get('file_path')
                        if p:
                            global_seen_paths.add(p)
                    continue
                unique_s_tracks = []
                for t in s_tracks:
                    p = t.get('file_path')
                    if p and p in global_seen_paths:
                        duplicate_count += 1
                        continue
                    unique_s_tracks.append(t)
                    if p:
                        global_seen_paths.add(p)
                final_unique_sets.append(unique_s_tracks)
            if duplicate_count > 0:
                print(f'[去重] 全局过滤掉 {duplicate_count} 首在不同 Set 中重复出现的歌曲')
            sets = final_unique_sets
            if bridge_insertions:
                print(f'\n[桥接曲] 共插入 {len(bridge_insertions)} 首桥接曲')
            elif not skip_bridge_track:
                has_large_gap = False
                for set_tracks in sets:
                    for i in range(len(set_tracks) - 1):
                        b1 = set_tracks[i].get('bpm', 0)
                        b2 = set_tracks[i + 1].get('bpm', 0)
                        if b1 and b2 and (abs(b1 - b2) > (8.0 if is_boutique else 15.0)):
                            has_large_gap = True
                            break
                    if has_large_gap:
                        break
                if has_large_gap:
                    print('[桥接曲] 警告: 检测到大的BPM跨度，但在曲库中未发现满足条件的桥接候选。')
                else:
                    print('[桥接曲] 无需插入桥接曲（所有BPM跨度都在合理范围内）')
        except Exception as e:
            print(f'[桥接曲] 处理时出错: {e}')
        output_dir = Path('D:\\生成的set')
        output_dir.mkdir(parents=True, exist_ok=True)
        try:
            playlist_display_name = target_playlist.name if hasattr(target_playlist, 'name') and target_playlist.name else playlist_name
        except:
            playlist_display_name = playlist_name
        try:
            processed_tracks_map = {}

            def get_flattened_tracks(input_list):
                result = []
                for item in input_list:
                    if isinstance(item, list):
                        result.extend(get_flattened_tracks(item))
                    elif isinstance(item, dict):
                        result.append(item)
                return result
            sets = [get_flattened_tracks(s) if isinstance(s, list) else [s] for s in sets]
            print(f'\n[V36.0 系统优化] 正在锁定曲库路径并同步标点...')
            for set_idx, set_tracks in enumerate(sets):
                for track in set_tracks:
                    if not isinstance(track, dict):
                        continue
                    raw_path = track.get('original_path') or track.get('file_path', '')
                    original_file_path = str(Path(raw_path).resolve())
                    track['original_path'] = original_file_path
                    track['file_path'] = original_file_path
                    if HOTCUE_GENERATOR_ENABLED and (not track.get('pro_hotcues')):
                        vocal_regions = []
                        if track.get('vocals') and isinstance(track['vocals'], dict):
                            vocal_regions = track['vocals'].get('segments', [])
                        link_data = None
                        try:
                            t_idx = set_tracks.index(track)
                            if t_idx < len(set_tracks) - 1:
                                next_t = set_tracks[t_idx + 1]
                                if isinstance(next_t, dict):
                                    ni_beats = 32
                                    if next_t.get('structure') and next_t['structure'].get('structure', {}).get('intro'):
                                        ir = next_t['structure']['structure']['intro']
                                        nb = next_t.get('bpm', 128)
                                        if nb > 0:
                                            ni_beats = 32 if int((ir[1] - ir[0]) / (60.0 / nb)) > 24 else 16
                                    link_data = {'next_title': next_t.get('title', 'Unknown'), 'next_intro_beats': ni_beats}
                        except:
                            pass
                        hcs_res = generate_hotcues(audio_file=original_file_path, bpm=track.get('bpm'), duration=track.get('duration'), structure=track.get('structure'), vocal_regions=vocal_regions, content_id=track.get('id'), content_uuid=track.get('content_uuid'), link_data=link_data, custom_mix_points={'mix_in': track.get('mix_in_point'), 'mix_out': track.get('mix_out_point')})
                        track['pro_hotcues'] = hcs_res
                        pro_hcs = hcs_res.get('hotcues', {})
                        track['anchor'] = hcs_res.get('anchor', 0.0)
                        if 'A' in pro_hcs:
                            old_val = track.get('mix_in_point')
                            new_val = pro_hcs['A']['Start']
                            track['mix_in_point'] = new_val
                            if old_val and abs(old_val - new_val) > 2.0:
                                try:
                                    print(f'    [对位修正] {track.get('title')[:30]}: Mix-In {old_val:.1f}s -> {new_val:.1f}s')
                                except:
                                    pass
                        if 'C' in pro_hcs:
                            old_val = track.get('mix_out_point')
                            new_val = pro_hcs['C']['Start']
                            track['mix_out_point'] = new_val
                            if old_val and abs(old_val - new_val) > 2.0:
                                try:
                                    print(f'    [对位修正] {track.get('title')[:30]}: Mix-Out {old_val:.1f}s -> {new_val:.1f}s')
                                except:
                                    pass
                        if 'E' in pro_hcs:
                            dep = pro_hcs['E']['Start']
                            track['drop_point'] = dep
                            if 'analysis' not in track:
                                track['analysis'] = {}
                            track['analysis']['drop_point'] = dep
                            track['vocals'] = track.get('vocals', {}) or {}
                            if isinstance(track['vocals'], dict):
                                track['vocals']['segments'] = track['vocals'].get('segments', []) + [[dep, dep + 15]]
                    try:
                        normalized_path = str(Path(original_file_path).resolve())
                        track['file_path'] = normalized_path
                        track['original_path'] = normalized_path
                    except:
                        track['file_path'] = original_file_path
                    track['force_refresh'] = False
            print('  [OK] 全闭环物理隔离与标点注入完成')
            print('  [OK] 物理隔离与标点校准完成')
        except Exception as e:
            print(f'  [Error] 物理隔离预处理失败: {e}')
        try:
            try:
                print(f'\n[完成] 所有Set排序完成！共 {len(sets)} 个Set')
            except UnicodeEncodeError:
                print(f'\n[完成] All sets sorted! Total: {len(sets)} sets')
            print('正在生成M3U文件和混音建议...')
        except:
            print('  [完成] All sets sorted! Total: {len(sets)} sets')
            print('Generating M3U files and mixing advice...')
        try:
            import time
            current_time = time.time()
            all_files = list(output_dir.glob(f'{playlist_display_name}_*.*'))
            for old_file in all_files:
                try:
                    if current_time - old_file.stat().st_mtime > 3600:
                        old_file.unlink()
                except:
                    pass
        except:
            pass
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        m3u_file = output_dir / f'{playlist_display_name}_增强调和谐版_{timestamp}.m3u'
        seen_paths = set()
        m3u_lines = ['#EXTM3U']
        for set_idx, set_tracks in enumerate(sets, 1):
            try:
                print(f'  处理 Set {set_idx}/{len(sets)}...')
            except:
                print(f'  Processing Set {set_idx}/{len(sets)}...')
            m3u_lines.append(f'\n# 分割线 - Set {set_idx} ({len(set_tracks)} 首歌曲)')
            for track in set_tracks:
                original_path = track.get('original_path') or track.get('file_path', '')
                try:
                    normalized_path = str(Path(original_path).resolve())
                except:
                    normalized_path = original_path
                path_key = normalized_path.lower()
                if path_key not in seen_paths:
                    seen_paths.add(path_key)
                    duration = 0
                    m3u_lines.append(f'#EXTINF:{duration},{track['artist']} - {track['title']}')
                    m3u_lines.append(normalized_path)
            if set_idx < len(sets):
                m3u_lines.append(f'\n# ========== Set {set_idx + 1} 结束 | Set {set_idx + 2} 开始 ==========')
                last_track = set_tracks[-1]
                m3u_lines.append(f'#EXTINF:{duration},{last_track['artist']} - {last_track['title']} [Set过渡 - 重复播放]')
                m3u_lines.append(last_track['file_path'])
                m3u_lines.append('')
        try:
            print('  正在写入M3U文件...')
        except:
            print('  Writing M3U file...')
        with open(m3u_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(m3u_lines))
        try:
            from export_set_to_csv import export_set_to_csv, format_key_display
            all_tracks_for_csv = []
            for set_idx, set_tracks in enumerate(sets, 1):
                for track in set_tracks:
                    track_copy = track.copy()
                    track_copy['key'] = format_key_display(track.get('key', 'Unknown'))
                    track_copy['set_number'] = set_idx
                    all_tracks_for_csv.append(track_copy)
            csv_file = output_dir / f'{playlist_display_name}_增强调性和谐版_{timestamp}.csv'
            export_set_to_csv(all_tracks_for_csv, str(csv_file))
            try:
                print(f'  [OK] CSV已导出: {csv_file.name}')
            except:
                print(f'  CSV exported: {csv_file.name}')
        except Exception as e:
            try:
                print(f'  警告: CSV导出失败 ({e})')
            except:
                print(f'  Warning: CSV export failed ({e})')
        try:
            print('  正在生成混音建议报告...')
        except:
            print('  Generating mixing advice report...')
        report_file = output_dir / f'{playlist_display_name}_混音建议_{timestamp}.txt'
        with open(report_file, 'w', encoding='utf-8-sig') as f:
            f.write(f'播放列表：{playlist_display_name}\n')
            f.write(f'生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n')
            f.write(f'共生成 {len(sets)} 个Set\n')
            f.write(f'总歌曲数：{len(tracks)} 首\n')
            if ACTIVE_PROFILE:
                f.write(f'使用进化配置: {ACTIVE_PROFILE.name}\n')
                f.write(f'策略描述: {ACTIVE_PROFILE.description}\n')
            f.write('\n')
            try:
                all_sorted_tracks = []
                for s in sets:
                    all_sorted_tracks.extend(s)
                radar_report = generate_radar_report(all_sorted_tracks)
                f.write('=' * 80 + '\n')
                f.write('质量监控报告 (Mixing Radar)\n')
                f.write('=' * 80 + '\n\n')
                f.write(radar_report)
                f.write('\n\n')
            except Exception as radar_err:
                f.write(f'\n[错误] 无法生成雷达报告: {radar_err}\n\n')
            f.write('=' * 80 + '\n')
            f.write('SET 歌单列表\n')
            f.write('=' * 80 + '\n\n')
            is_dual_mode = any((s and s[0].get('is_boutique_start') for s in sets))
            if not is_dual_mode and len(sets) > 1 and (25 <= len(sets[0]) <= 50):
                is_dual_mode = True
                if sets[0]:
                    sets[0][0]['is_boutique_start'] = True
            for set_idx, set_tracks in enumerate(sets, 1):
                f.write(f'\n{'=' * 80}\n')
                is_boutique_head = set_idx == 1 and set_tracks and set_tracks[0].get('is_boutique_start')
                if is_boutique_head:
                    title = f'Set {set_idx} [✨ BOUTIQUE HIGHLIGHT 精选] (Best {len(set_tracks)} Tracks)'
                elif is_dual_mode:
                    title = f'Set {set_idx} [🔴 FULL LIVE 全量] (Part {(set_idx - 1 if is_dual_mode else set_idx)}) ({len(set_tracks)} Tracks)'
                else:
                    title = f'Set {set_idx} ({len(set_tracks)} 首歌曲)'
                f.write(f'{title}\n')
                f.write(f'{'=' * 80}\n\n')
                for idx, track in enumerate(set_tracks, 1):
                    artist = track.get('artist', 'Unknown')
                    title = track.get('title', 'Unknown')
                    bpm = track.get('bpm', 0)
                    key = track.get('key', '未知')
                    energy = track.get('energy', 0)
                    duration = track.get('duration', 0)
                    mix_in = track.get('mix_in_point')
                    mix_out = track.get('mix_out_point')
                    if duration >= 60:
                        minutes = int(duration // 60)
                        seconds = int(duration % 60)
                        duration_str = f'{duration:.0f}秒 ({minutes}分{seconds}秒)'
                    else:
                        duration_str = f'{duration:.0f}秒'

                    def format_time(seconds, bpm_value=None):
                        if seconds is None:
                            return '未检测'
                        beats_info = ''
                        if bpm_value and bpm_value > 0:
                            beat_duration = 60.0 / bpm_value
                            beats = int(seconds / beat_duration)
                            bars = beats // 8
                            remaining_beats = beats % 8
                            if bars > 0:
                                if remaining_beats == 0:
                                    beats_info = f' ({bars}个八拍)'
                                else:
                                    beats_info = f' ({bars}个八拍{remaining_beats}拍)'
                            elif beats > 0:
                                beats_info = f' ({beats}拍)'
                        if seconds >= 60:
                            minutes = int(seconds // 60)
                            secs = int(seconds % 60)
                            return f'{seconds:.3f}秒 ({minutes}分{secs}秒){beats_info}'
                        return f'{seconds:.3f}秒{beats_info}'
                    is_bridge = track.get('is_bridge', False)
                    bridge_reason = track.get('bridge_reason', '')
                    try:
                        from export_set_to_csv import format_key_display
                        key_display = format_key_display(key)
                    except:
                        key_display = key
                    if is_bridge:
                        f.write(f'{idx:2d}. [桥接曲] {artist} - {title}\n')
                        f.write(f'    BPM: {bpm:.1f} | 调性: {key_display} | 能量: {energy:.0f}/100 | 时长: {duration_str}\n')
                        f.write(f'    [自动插入原因] {bridge_reason}\n')
                    else:
                        f.write(f'{idx:2d}. {artist} - {title}\n')
                        f.write(f'    BPM: {bpm:.1f} | 调性: {key_display} | 能量: {energy:.0f}/100 | 时长: {duration_str}\n')
                    structure = track.get('structure')
                    if structure:
                        key_points = []
                        if structure.get('intro'):
                            start, end = structure['intro']
                            key_points.append(f'Intro结束: {format_time(end, bpm)}')
                        if structure.get('outro'):
                            start, end = structure['outro']
                            key_points.append(f'Outro开始: {format_time(start, bpm)}')
                        if key_points:
                            f.write(f'    结构: {' | '.join(key_points)}\n')
                    pro_hcs = track.get('pro_hotcues', {})
                    if pro_hcs:
                        f.write(f'    ⭐ Pro Hotcues (Rekordbox 协同):\n')
                        for hc_key in ['A', 'B', 'C', 'D', 'E']:
                            if hc_key in pro_hcs:
                                hc = pro_hcs[hc_key]
                                hc_name = hc.get('Name', f'Cue {hc_key}')
                                hc_time = hc.get('Start', 0.0)
                                phrase_label = hc.get('PhraseLabel', '[Grid Sync]')
                                f.write(f'      - {hc_name}: {format_time(hc_time, bpm)} {phrase_label}\n')
                    if idx == 1:
                        if mix_in:
                            f.write(f'    🎯 最佳接歌点(Mix-In): {format_time(mix_in, bpm)}\n')
                        else:
                            f.write(f'    🎯 最佳接歌点(Mix-In): 未检测\n')
                    else:
                        prev_track = set_tracks[idx - 2]
                        prev_mix_out = prev_track.get('mix_out_point')
                        prev_bpm = prev_track.get('bpm', 0)
                        if mix_in:
                            if prev_mix_out:
                                f.write(f'    🎯 最佳接歌点(Mix-In): {format_time(mix_in, bpm)} | 上一首出歌点: {format_time(prev_mix_out, prev_bpm)}\n')
                            else:
                                f.write(f'    🎯 最佳接歌点(Mix-In): {format_time(mix_in, bpm)} | 上一首出歌点: 未检测\n')
                        elif prev_mix_out:
                            f.write(f'    🎯 最佳接歌点(Mix-In): 未检测 | 建议在上一首出歌点 {format_time(prev_mix_out, prev_bpm)} 后开始混入\n')
                    if idx < len(set_tracks):
                        next_track = set_tracks[idx]
                        next_mix_in = next_track.get('mix_in_point')
                        next_bpm = next_track.get('bpm', 0)
                        if mix_out:
                            if next_mix_in:
                                f.write(f'    🎯 最佳出歌点(Mix-Out): {format_time(mix_out, bpm)} | 下一首接歌点: {format_time(next_mix_in, next_bpm)}\n')
                            else:
                                f.write(f'    🎯 最佳出歌点(Mix-Out): {format_time(mix_out, bpm)} | 下一首接歌点: 未检测\n')
                        elif next_mix_in:
                            f.write(f'    🎯 最佳出歌点(Mix-Out): 未检测 | 建议在下一首接歌点前 {format_time(next_mix_in, next_bpm)} 开始淡出\n')
                        else:
                            f.write(f'    🎯 最佳出歌点(Mix-Out): 未检测（建议手动选择）\n')
                        if idx < len(set_tracks):
                            need_advice = False
                            curr_bpm = track.get('bpm', 0)
                            next_bpm = next_track.get('bpm', 0)
                            curr_key = track.get('key', '')
                            next_key = next_track.get('key', '')
                            bpm_diff = abs(curr_bpm - next_bpm) if curr_bpm and next_bpm else 999
                            key_score = get_key_compatibility_flexible(curr_key, next_key) if curr_key and next_key and (curr_key != '未知') and (next_key != '未知') else 0
                            if bpm_diff > 8 or key_score < 60:
                                need_advice = True
                            curr_vocals = track.get('vocals')
                            next_vocals = next_track.get('vocals')
                            if curr_vocals and next_vocals and mix_out and next_mix_in:
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
                                if current_out_vocals and next_in_vocals:
                                    need_advice = True
                            if True:
                                f.write(f'\n    {'─' * 70}\n')
                                f.write(f'    📝 混音建议：{title} → {next_track.get('title', 'Unknown')[:30]}\n')
                                f.write(f'    {'─' * 70}\n')
                                transition_advice = generate_transition_advice(track, next_track, idx)
                                if transition_advice:
                                    for line in transition_advice:
                                        f.write(line + '\n')
                                else:
                                    f.write('    ✅ 过渡很和谐，标准混音即可\n')
                                f.write('\n')
                            else:
                                f.write('    ✅ 过渡顺畅，标准混音即可\n\n')
                    elif mix_in and mix_out:
                        f.write(f'    🎯 最佳接歌点(Mix-In): {format_time(mix_in, bpm)} | 最佳出歌点(Mix-Out): {format_time(mix_out, bpm)}\n')
                    elif mix_in:
                        f.write(f'    🎯 最佳接歌点(Mix-In): {format_time(mix_in, bpm)} | 最佳出歌点(Mix-Out): 未检测\n')
                    elif mix_out:
                        f.write(f'    🎯 最佳接歌点(Mix-In): 未检测 | 最佳出歌点(Mix-Out): {format_time(mix_out, bpm)}\n')
                    else:
                        f.write(f'    🎯 混音点: 未检测（建议手动选择）\n')
                if set_idx < len(sets):
                    f.write(f'\n    [过渡] → Set {set_idx + 1} 开始\n')
            if PROFESSIONAL_AUDIT_ENABLED:
                all_tracks_flat = [t for s in sets for t in s]
                audit = calculate_set_completeness(all_tracks_flat)
                energy_curve = get_energy_curve_summary(all_tracks_flat)
                f.write(f'\n{'#' * 80}\n')
                f.write(f'### 专业 DJ Set 完整度报告 (Phase 9 Audit)\n')
                f.write(f'{'#' * 80}\n')
                f.write(f'总平均得分: {audit['total_score']}/100  | 评级: {audit['rating']}\n')
                f.write(f'能量曲线分析: {energy_curve}\n')
                f.write(f'分项指标:\n')
                f.write(f'  - 调性流转 (Harmonic): {audit['breakdown'].get('harmonic_flow', 0)}/25\n')
                f.write(f'  - BPM 梯度 (Momentum): {audit['breakdown'].get('bpm_stability', 0)}/25\n')
                f.write(f'  - 乐句对齐 (Phrase): {audit['breakdown'].get('phrase_alignment', 0)}/25\n')
                f.write(f'  - 人声安全 (Vocal): {audit['breakdown'].get('vocal_safety', 0)}/25\n')
                f.write(f'{'=' * 80}\n\n')
            if bridge_insertions:
                f.write(f'\n\n{'=' * 80}\n')
                f.write(f'桥接曲汇总 (共 {len(bridge_insertions)} 首自动插入)\n')
                f.write(f'{'=' * 80}\n\n')
                f.write('以下位置因BPM跨度过大(>15)，系统自动插入了桥接曲：\n\n')
                for i, info in enumerate(bridge_insertions, 1):
                    f.write(f'{i}. Set {info['set_idx']} 第 {info['position']} 首后\n')
                    f.write(f'   原过渡: {info['prev_track']} -> {info['next_track']}\n')
                    f.write(f'   原BPM跨度: {info['prev_bpm']:.1f} -> {info['next_bpm']:.1f} (跨度 {info['original_gap']:.1f})\n')
                    f.write(f'   插入桥接曲: {info['bridge_track']}\n')
                    f.write(f'   新BPM跨度: {info['prev_bpm']:.1f} -> {info['bridge_bpm']:.1f} -> {info['next_bpm']:.1f}\n')
                    f.write(f'              (跨度 {info['new_gap_1']:.1f} + {info['new_gap_2']:.1f})\n')
                    f.write(f'   选择原因: {' | '.join(info['reasons'])}\n\n')
        clean_name = ''.join([c for c in playlist_display_name if c.isalpha() or c.isdigit() or c == ' ' or (c == '_')]).rstrip()
        try:
            print('  正在生成 Rekordbox XML (PRO 模式)...')
            for i, set_tracks in enumerate(sets):
                xml_file = output_dir / f'{clean_name}_Set{i + 1}_{timestamp}.xml'
                export_to_rekordbox_xml(set_tracks, xml_file, playlist_name=f'{clean_name}_Set{i + 1}')
                try:
                    print(f'  ✓ XML已导出: {xml_file.name}')
                except:
                    print(f'  XML exported: {xml_file.name}')
        except Exception as e:
            try:
                print(f'  无法生成 XML: {e}')
            except:
                print(f'  XML export failed: {e}')
        try:
            try:
                print('  [完成] 文件生成完成！')
            except UnicodeEncodeError:
                print('  [完成] Files generated!')
        except:
            print('  [完成] Files generated!')
        try:
            print(f'\n{'=' * 60}')
            print('完成！')
            print(f'M3U文件: {m3u_file}')
            print(f'混音建议报告: {report_file}')
            print(f'共生成 {len(sets)} 个Set')
            print(f'{'=' * 60}')
            if is_master and sets:
                seen_paths = set()
                master_tracks = []
                for s in sets:
                    for track in s:
                        path = (track.get('file_path') or '').replace('\\', '/').lower()
                        if path and path not in seen_paths:
                            seen_paths.add(path)
                            master_tracks.append(track)
                if seen_paths:
                    print(f'  [去重] Master Set: {len(seen_paths)} 首不重复曲目')
                master_m3u_name = f'{clean_name}_Master_Unified_{timestamp}.m3u'
                master_m3u_path = output_dir / master_m3u_name
                with open(master_m3u_path, 'w', encoding='utf-8') as f:
                    f.write('#EXTM3U\n')
                    for track in master_tracks:
                        f.write(f'#EXTINF:{int(track.get('duration', 0))},{track.get('artist', 'Unknown')} - {track.get('title', 'Unknown')}\n')
                        f.write(f'{track.get('file_path', '')}\n')
                try:
                    print(f'\n[Master] 已导出全局连贯 Master M3U: {master_m3u_name}')
                except:
                    print(f'\n[Master] Unified M3U exported: {master_m3u_name}')
                master_xml_name = f'{clean_name}_Master_Library_{timestamp}.xml'
                master_xml_path = output_dir / master_xml_name
                try:
                    from exporters.xml_exporter import export_multi_sets_to_rekordbox_xml
                    export_multi_sets_to_rekordbox_xml(sets, master_xml_path, playlist_name)
                    print(f'[Master] 已导出 Master Rekordbox XML (含文件夹结构): {master_xml_name}')
                except Exception as e:
                    print(f'[Master] 警告 (非致命): 无法导出 Master XML (可能是路径权限问题): {e}')
            try:
                print('\n混音建议已显示在歌曲之间')
            except:
                print('\nMixing advice displayed between songs')
        except Exception as e:
            print(f'Error in final report: {e}')
            print(f'Mixing advice report: {report_file}')
            print(f'Generated {len(sets)} sets')
            print(f'{'=' * 60}')
        try:
            import subprocess
            import platform
            output_path = str(output_dir.resolve())
            if platform.system() == 'Windows':
                subprocess.Popen(f'explorer "{output_path}"')
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', output_path])
            else:
                subprocess.Popen(['xdg-open', output_path])
            try:
                print(f'\n已自动打开文件夹: {output_path}')
            except:
                print(f'\nOpened folder: {output_path}')
        except Exception as e:
            try:
                print(f'\n无法自动打开文件夹: {e}')
            except:
                print(f'\nFailed to open folder: {e}')
        await db.disconnect()
        return sets
    except Exception as e:
        print(f'错误: {e}')
        import traceback
        traceback.print_exc()
        try:
            await db.disconnect()
        except:
            pass

def get_file_cache_key(file_path: str) -> Optional[str]:
    """获取文件缓存键"""
    return get_file_hash(file_path)

def is_cache_valid(cached_entry: dict, file_path: str) -> bool:
    """检查缓存是否有效"""
    cached_path = cached_entry.get('file_path', '').replace('\\', '/')
    file_path_str = str(file_path).replace('\\', '/')
    return cached_path == file_path_str

def calculate_transition_risk(current_track: dict, next_track: dict, mix_gap: Optional[float]=None, structure_warning: bool=False) -> tuple:
    """计算曲间风险评分"""
    risk_score = 0
    risk_reasons = []
    current_key = current_track.get('key', '')
    next_key = next_track.get('key', '')
    key_score = get_key_compatibility_flexible(current_key, next_key)
    if key_score is not None and key_score < 50:
        key_clash = (50 - key_score) / 50.0
        risk_score += key_clash * 30
        risk_reasons.append('调性冲突')
    current_energy = current_track.get('energy') or 50
    next_energy = next_track.get('energy') or 50
    energy_diff = current_energy - next_energy
    if energy_diff is not None and energy_diff > 15:
        energy_drop = min(1.0, (energy_diff - 15) / 30.0)
        risk_score += energy_drop * 20
        risk_reasons.append('能量突降')
    mix_point_risk = 0
    if mix_gap is not None:
        if abs(mix_gap) > 20:
            mix_point_risk = 1.0
            risk_reasons.append('混音点间隔异常')
        elif abs(mix_gap) > 18:
            mix_point_risk = 0.5
            risk_reasons.append('混音点间隔较大')
    if structure_warning:
        mix_point_risk = max(mix_point_risk, 0.33)
        if '混音点在Verse中间' not in risk_reasons:
            risk_reasons.append('混音点在Verse中间')
    risk_score += mix_point_risk * 15
    try:
        from split_config import get_config as _get_cfg
        _cfg = _get_cfg() or {}
    except Exception:
        _cfg = {}
    tr_cfg = _cfg.get('transition_risk_profile') or {}
    if bool(tr_cfg.get('enabled', True)):
        l1 = current_track.get('loudness_lufs')
        l2 = next_track.get('loudness_lufs')
        try:
            if isinstance(l1, (int, float)) and isinstance(l2, (int, float)):
                diff = abs(float(l1) - float(l2))
                thr = float(tr_cfg.get('lufs_diff_warn_db', 4.0))
                if diff >= thr:
                    w = float(tr_cfg.get('lufs_diff_risk_weight', 12.0))
                    ratio = min(1.0, max(0.0, (diff - thr) / max(1e-06, thr)))
                    risk_score += ratio * w
                    risk_reasons.append('响度差过大')
        except Exception:
            pass
        dr1 = current_track.get('dynamic_range_db')
        dr2 = next_track.get('dynamic_range_db')
        try:
            if isinstance(dr1, (int, float)) and isinstance(dr2, (int, float)):
                diff = abs(float(dr1) - float(dr2))
                thr = float(tr_cfg.get('dyn_range_diff_warn_db', 6.0))
                if diff >= thr:
                    w = float(tr_cfg.get('dyn_range_risk_weight', 8.0))
                    ratio = min(1.0, max(0.0, (diff - thr) / max(1e-06, thr)))
                    risk_score += ratio * w
                    risk_reasons.append('动态范围差异')
        except Exception:
            pass
        k1 = current_track.get('kick_drum_power')
        k2 = next_track.get('kick_drum_power')
        s1 = current_track.get('sub_bass_level')
        s2 = next_track.get('sub_bass_level')
        try:
            if isinstance(k1, (int, float)) and isinstance(k2, (int, float)) and isinstance(s1, (int, float)) and isinstance(s2, (int, float)):
                diff = max(abs(float(k1) - float(k2)), abs(float(s1) - float(s2)))
                thr = float(tr_cfg.get('lowfreq_mismatch_warn', 0.35))
                if diff >= thr:
                    w = float(tr_cfg.get('lowfreq_risk_weight', 8.0))
                    ratio = min(1.0, max(0.0, (diff - thr) / max(1e-06, thr)))
                    risk_score += ratio * w
                    risk_reasons.append('低频骨架不一致')
        except Exception:
            pass
    risk_score = min(100, risk_score)
    if risk_score < 20:
        risk_level = 'safe'
    elif risk_score < 40:
        risk_level = 'medium'
    else:
        risk_level = 'danger'
    return (risk_level, risk_score, risk_reasons)

def is_key_transition_allowed(current_key: str, next_key: str, is_segment_boundary: bool=False, config: dict=None, track: dict=None) -> tuple:
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
    try:
        from core.track_finder import smart_find_track
        from core.cache_manager import load_cache, save_cache_atomic
    except ImportError:

        def smart_find_track(k, **kwargs):
            return []

        def load_cache():
            return {}

        def save_cache_atomic(c, p):
            pass
    if config is None:
        try:
            from split_config import get_config
            config = get_config()
        except ImportError:
            config = {'key': {'max_allowed_distance': 3, 'parse_error_penalty': 0.1}}
    key_config = config.get('key', {})
    max_allowed_distance = key_config.get('max_allowed_distance', 3)
    parse_error_penalty = key_config.get('parse_error_penalty', 0.1)
    unknown_key_penalty = key_config.get('unknown_key_penalty', 0.05)
    log_key_transitions = key_config.get('log_key_transitions', True)
    if not current_key or current_key.lower() in ('unknown', '未知', ''):
        if track:
            track['key_confidence'] = track.get('key_confidence', 1.0) - unknown_key_penalty
        return (True, 'current key unknown -> allow (low confidence)')
    if not next_key or next_key.lower() in ('unknown', '未知', ''):
        if track:
            track['key_confidence'] = track.get('key_confidence', 1.0) - unknown_key_penalty
        return (True, 'next key unknown -> allow (low confidence)')
    if is_segment_boundary:
        return (True, 'segment boundary -> allow')
    try:
        curr_num = int(''.join((ch for ch in current_key if ch.isdigit())))
        next_num = int(''.join((ch for ch in next_key if ch.isdigit())))

        def circle_distance(a, b):
            """计算5度圈距离（考虑轮盘循环）"""
            direct = abs(a - b)
            wrap = 12 - direct
            return min(direct, wrap)
        diff = circle_distance(curr_num, next_num)
        reason = ''
        if diff == 0:
            reason = '同调'
        elif diff == 1:
            reason = '5度圈相邻'
        elif diff == 2:
            reason = '5度圈隔一个'
        elif diff == 3:
            reason = '5度圈隔两个（需要技巧）'
        else:
            reason = f'非法调性跨越（距离{diff}）'
        if log_key_transitions:
            print(f'[调性过渡] {current_key}→{next_key}: {reason} (距离={diff})')
        if diff <= max_allowed_distance:
            return (True, f'allowed (circle_distance={diff} <= {max_allowed_distance}, {reason})')
        else:
            return (False, f'illegal key transition (circle_distance={diff} > {max_allowed_distance}, {reason})')
    except (ValueError, IndexError, AttributeError) as e:
        if track:
            track['key_confidence'] = track.get('key_confidence', 1.0) - parse_error_penalty
        error_msg = f"key parse error '{str(e)}' -> allow (low confidence)"
        if log_key_transitions:
            print(f'[调性解析错误] {current_key}→{next_key}: {error_msg}')
        return (True, error_msg)

def get_genre_group(genre: str) -> str:
    """将风格归类到组"""
    if not genre:
        return 'Unknown'
    genre_lower = genre.lower()
    if any((keyword in genre_lower for keyword in ['house', 'tech house', 'deep house', 'progressive house'])):
        return 'H'
    if any((keyword in genre_lower for keyword in ['techno', 'hard techno'])):
        return 'T'
    if any((keyword in genre_lower for keyword in ['bass', 'trap', 'dubstep', 'dnb', 'drum and bass'])):
        return 'B'
    if any((keyword in genre_lower for keyword in ['afro', 'latin', 'world', 'baile funk'])):
        return 'A'
    if any((keyword in genre_lower for keyword in ['breaks', 'breakbeat'])):
        return 'K'
    return 'Unknown'

def get_genre_transition_score(current_group: str, next_group: str) -> int:
    """计算风格过渡分数"""
    if current_group == 'Unknown' or next_group == 'Unknown':
        return 50
    if current_group == next_group:
        return 100
    if current_group == 'H' and next_group == 'A' or (current_group == 'A' and next_group == 'H'):
        return 70
    if current_group == 'H' and next_group == 'T' or (current_group == 'T' and next_group == 'H'):
        return 70
    if current_group == 'H' and next_group == 'B' or (current_group == 'B' and next_group == 'H'):
        return 30
    if current_group == 'A' and next_group == 'T' or (current_group == 'T' and next_group == 'A'):
        return 30
    if current_group == 'T' and next_group == 'B' or (current_group == 'B' and next_group == 'T'):
        return 0
    return 50

def infer_drum_pattern(bpm: float, genre: str) -> str:
    """基于BPM+风格推断鼓型"""
    if not genre:
        return '4/4'
    genre_lower = genre.lower()
    if 118 <= bpm <= 130:
        if any((keyword in genre_lower for keyword in ['tech house', 'techno', 'house'])):
            return '4/4'
    if any((keyword in genre_lower for keyword in ['afro', 'tribal', 'latin'])):
        return 'afro'
    if any((keyword in genre_lower for keyword in ['trap', 'bass', 'dubstep'])):
        return 'half-time'
    if any((keyword in genre_lower for keyword in ['breaks', 'breakbeat'])):
        return 'breaks'
    return '4/4'

def is_drum_pattern_transition_allowed(current_pattern: str, next_pattern: str) -> bool:
    """检查鼓型过渡是否合法"""
    if current_pattern == '4/4' and next_pattern == '4/4':
        return True
    if current_pattern == '4/4' and next_pattern == 'afro' or (current_pattern == 'afro' and next_pattern == '4/4'):
        return True
    if current_pattern == '4/4' and next_pattern == 'breaks' or (current_pattern == 'breaks' and next_pattern == '4/4'):
        return True
    if current_pattern == '4/4' and next_pattern == 'half-time' or (current_pattern == 'half-time' and next_pattern == '4/4'):
        return False
    if current_pattern == 'half-time' and next_pattern == 'half-time':
        return True
    return True

def find_stems_mashup_pairs(playlist_name: str, min_score: float=75.0, max_results: int=20):
    """
    专为Rekordbox Stems设计的Mashup搜索工具
    复用现有的调性和BPM兼容性函数
    """
    print('=' * 80)
    print('Rekordbox Stems Mashup搜索工具')
    print('=' * 80)
    print()
    print('[1/3] 加载播放列表...')
    from pyrekordbox import Rekordbox6Database
    from sqlalchemy import text
    cache = load_cache()
    cache_by_path = {}
    for hash_key, data in cache.items():
        if 'file_path' in data:
            fp = data['file_path'].lower().replace('\\', '/')
            cache_by_path[fp] = data.get('analysis', {})
    playlist = db.session.execute(text('SELECT * FROM DJMDPlaylist WHERE Name = :name'), {'name': playlist_name}).fetchone()
    if not playlist:
        print(f"警告: 找不到播放列表 '{playlist_name}'")
        return []
    try:
        playlist_id = getattr(playlist, 'ID', playlist[0] if isinstance(playlist, (list, tuple)) else None)
        songs = db.get_playlist_songs(playlist_id)
    except:
        print(f"警告: 无法获取播放列表 '{playlist_name}' 的歌曲内容")
        return []
    for song in songs:
        content_id = getattr(song, 'ContentID', None)
        if not content_id:
            continue
        try:
            content = song if hasattr(song, 'Title') else db.get_content(ID=content_id)
            if not content:
                continue
            bpm_raw = getattr(content, 'BPM', 0) or 0
            bpm = bpm_raw / 100.0 if bpm_raw > 500 else bpm_raw
            key = getattr(content, 'KeyID', '') or ''
            file_path = getattr(content, 'FolderPath', '') or ''
            fp_normalized = file_path.lower().replace('\\', '/')
            cached = cache_by_path.get(fp_normalized, {})
            if not bpm or bpm <= 0:
                bpm = cached.get('bpm', 0)
            if not key:
                key = cached.get('key', '')
            if bpm and bpm > 0:
                tracks.append({'id': content_id, 'title': getattr(content, 'Title', 'Unknown'), 'artist': getattr(content, 'ArtistName', None) or 'Unknown', 'bpm': float(bpm), 'key': key, 'file_path': file_path, 'vocal_ratio': cached.get('vocal_ratio', 0.5), 'energy': cached.get('energy', 50)})
        except:
            continue
    if not tracks:
        print(f"错误: 播放列表 '{playlist_name}' 中没有可用的歌曲")
        return []
    print(f'=> 已加载 {len(tracks)} 首歌曲')
    print()
    print('[2/3] 搜索Stems混搭组合...')
    from skills.mashup_intelligence.scripts.core import MashupIntelligence
    candidates = []
    total_pairs = len(tracks) * (len(tracks) - 1) // 2
    checked = 0
    for i, track1 in enumerate(tracks):
        for j, track2 in enumerate(tracks[i + 1:], i + 1):
            checked += 1
            if checked % 500 == 0:
                print(f'   已检查 {checked}/{total_pairs} 对...')
            score, details = mi.calculate_mashup_score(track1, track2)
            if score >= min_score:
                candidates.append({'track1': track1, 'track2': track2, 'score': score, 'details': details, 'mashup_type': details.get('mashup_type', '标准Stems混搭'), 'mi_instance': mi})
    print(f'=> 找到 {len(candidates)} 个高质量匹配对')
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates[:max_results]

def save_stems_results(candidates, output_file='stems_mashup_results.txt'):
    """保存Stems搜索结果"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('=' * 80 + '\n')
        f.write('Rekordbox Stems Mashup搜索结果\n')
        f.write('=' * 80 + '\n\n')
        f.write(f'找到 {len(candidates)} 个推荐组合\n\n')
        for i, candidate in enumerate(candidates, 1):
            track1 = candidate['track1']
            track2 = candidate['track2']
            score = candidate['score']
            mashup_type = candidate['mashup_type']
            details = candidate['details']
            f.write(f'\n推荐组合 #{i} - 评分: {score:.1f}/100\n')
            f.write(f'混搭类型: {mashup_type}\n')
            f.write('=' * 60 + '\n\n')
            try:
                from export_set_to_csv import format_key_display
                key1_display = format_key_display(track1.get('key', '未知'))
                key2_display = format_key_display(track2.get('key', '未知'))
            except:
                key1_display = track1.get('key', '未知')
                key2_display = track2.get('key', '未知')
            f.write(f'歌曲A: {track1.get('artist', 'Unknown')} - {track1.get('title', 'Unknown')}\n')
            f.write(f'  BPM: {track1.get('bpm', 0):.1f} | 调性: {key1_display}\n\n')
            f.write(f'歌曲B: {track2.get('artist', 'Unknown')} - {track2.get('title', 'Unknown')}\n')
            f.write(f'  BPM: {track2.get('bpm', 0):.1f} | 调性: {key2_display}\n\n')
            f.write('匹配分析:\n')
            f.write(f'  BPM: {details.get('bpm_status', 'N/A')}\n')
            f.write(f'  调性: {details.get('key_status', 'N/A')}\n')
            f.write(f'  人声: {details.get('vocal_status', 'N/A')}\n')
            f.write(f'  能量: {details.get('energy_status', 'N/A')}\n\n')
            mi = candidate.get('mi_instance')
            if mi:
                guide = mi.generate_unified_guide(track1, track2, score, details)
                for line in guide:
                    f.write(f'{line}\n')
            f.write('\n维度分析:\n')
            for dim, desc in details.items():
                if dim != 'mashup_pattern':
                    f.write(f'  - {dim.upper()}: {desc}\n')
            f.write('\n')
    print(f'=> 结果已保存到: {output_file}')
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--stems':
        if len(sys.argv) < 3:
            print('用法: python enhanced_harmonic_set_sorter.py --stems <播放列表名称> [最低分数]')
            print('示例: python enhanced_harmonic_set_sorter.py --stems 华语 75')
            sys.exit(1)
        playlist_name = sys.argv[2]
        min_score = float(sys.argv[3]) if len(sys.argv) > 3 else 75.0
        print(f'搜索播放列表: {playlist_name}')
        print(f'最低分数: {min_score}')
        print()
        candidates = find_stems_mashup_pairs(playlist_name, min_score)
        if candidates:
            save_stems_results(candidates)
            print()
            print('🎉 Stems搜索完成！')
            print(f'找到 {len(candidates)} 个推荐组合')
            print('详细指导已保存到: stems_mashup_results.txt')
            print()
            print('使用方法:')
            print('1. 打开Rekordbox')
            print('2. 按照文件中的指导操作')
            print('3. 享受你的Mashup创作！')
        else:
            print('❌ 未找到合适的组合')
            print('建议降低最低分数重试')
    else:
        parser = argparse.ArgumentParser(description='增强版专业DJ Set排序工具')
        parser.add_argument('playlist', nargs='?', default='default', help='播放列表名称 (或使用 artist:Name / search:Query 直接搜索)')
        parser.add_argument('--artist', type=str, help='[V6.3] 按照艺人搜索生成 Set')
        parser.add_argument('--query', type=str, help='[V6.3] 按照关键词搜索生成 Set')
        parser.add_argument('--songs-per-set', type=int, default=None, help='每个Set的歌曲数量（可选，不指定则使用配置文件的浮动规则: 25-40首）')
        parser.add_argument('--preset', type=str, default='default', choices=['club', 'radio', 'warm_up', 'extended', 'default'], help='Set预设类型（club=60min, radio=45min, warm_up=90min, extended=120min）')
        parser.add_argument('--bridge', action='store_true', help='启用桥接模式：从曲库补充同风格歌曲（仅限电子乐风格）')
        parser.add_argument('--boutique', action='store_true', help='精品单体Set模式：不分Set，追求极致平滑过渡，严格限制BPM和调性跳跃')
        parser.add_argument('--master', action='store_true', help='Master总线模式：全局连贯排序，在最优点智能切分Set，并导出统一的Master M3U/XML')
        parser.add_argument('--live', action='store_true', help='直播长Set模式：完整度优先，确保所有歌曲都排进去，无法和谐衔接的歌曲放在Set末尾')
        parser.add_argument('--theme', type=str, default='', help='[Intelligence-V5] 设定 Set 的叙事主题（如：“探索 Y2K 怀旧背景下的女团力量”）')
        args = parser.parse_args()
        if args.theme and NARRATIVE_ENABLED:
            NARRATIVE_PLANNER.set_theme(args.theme)
        split_cfg = DJ_RULES.get('split', {}) if DJ_RULES else {}
        if args.songs_per_set:
            effective_songs_per_set = args.songs_per_set
        else:
            effective_songs_per_set = split_cfg.get('ideal_songs_max', 35)
            print(f'[Phase 8] 使用浮动分割: {split_cfg.get('min_songs', 25)}-{split_cfg.get('max_songs', 40)}首/Set')
            print(f'         目标时长: {split_cfg.get('target_duration_minutes', 90)}分钟')
        if args.boutique:
            print(f'[Boutique] 已启用精品模式，将应用最严格的调性与BPM平滑规则')
            if not args.master:
                pass
        target_name = args.playlist
        if args.artist:
            target_name = f'artist:{args.artist}'
        elif args.query:
            target_name = f'search:{args.query}'
        try:
            import traceback
            asyncio.run(create_enhanced_harmonic_sets(playlist_name=target_name, songs_per_set=effective_songs_per_set, enable_bridge=args.bridge, is_boutique=args.boutique, is_master=args.master, is_live=args.live, preset=args.preset))
        except Exception:
            with open('traceback.txt', 'w', encoding='utf-8') as f:
                traceback.print_exc(file=f)
            sys.exit(1)
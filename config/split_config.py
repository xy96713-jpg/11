#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Set分割与排序配置管理
所有阈值和参数集中管理，避免硬编码
"""

# 默认配置
DEFAULT_CONFIG = {
    # 能量结构策略（单峰/多峰段落）
    # - single_peak：默认更稳，减少“无意图的能量回摆”，更贴近录制型叙事结构
    # - multi_peak：允许 2-3 个峰，但要求峰间存在“明确回落区”（连续下降一小段），段落切点可用更激进转场
    "energy_profile": {
        "mode": "single_peak",  # "single_peak" | "multi_peak" | "auto"
        "max_peaks": 3,
        # 在锐评/评分里判定“回落区”的条件（multi_peak 才使用）
        "micro_cooldown_min_len": 2,      # 至少连续下降2首
        "micro_cooldown_min_drop": 12.0,  # 总下降≥12（能量值口径）
        # 能量倒退阈值：在非 Cool-down / 非回落区，下一首比上一首低超过该值视为“倒退”
        "regression_threshold": 10.0,
        # 段落切点允许更激进转场（用于文案提示/风险解释）
        "allow_aggressive_on_boundary": True,
    },

    # 风格标签（V6.5）门控配置：避免 filename 兜底误判引发“负优化”
    "genre_profile": {
        "min_confidence_for_sort": 0.85,  # 低于该阈值时，排序器不使用 detected_genre 做冲突扣分
    },

    # 角色(Role)配置：默认只用于提示/报告，不强制重排（避免负优化）
    "role_profile": {
        "enabled": True,
        "min_confidence_to_use": 0.80,   # 达到该置信度才用于“建议/标注”
        "write_to_cache": True,
    },

    # 过渡风险：响度/低频/动态范围（默认轻量计入风险，不强制重排）
    "transition_risk_profile": {
        "enabled": True,
        "lufs_diff_warn_db": 4.0,
        "lufs_diff_risk_weight": 12.0,  # 0-100风险分的加权上限（按比例）
        "dyn_range_diff_warn_db": 6.0,
        "dyn_range_risk_weight": 8.0,
        "lowfreq_mismatch_warn": 0.35,  # kick/sub 的归一化差值阈值
        "lowfreq_risk_weight": 8.0,
    },
    # 调性兼容性配置
    "key": {
        "max_allowed_distance": 3,  # 5度圈最大允许距离（默认3）
        "parse_error_penalty": 0.1,  # key格式解析失败时的置信度降权
        "unknown_key_penalty": 0.05,  # 未知调性的置信度降权
    },
    
    # BPM兼容性配置
    "bpm": {
        "direct_tolerance": 15.0,  # 直接BPM差值的容忍度
        "half_double_tolerance": 5.0,  # half-time/double-time判断的容忍度
        "max_jump_in_set": 25.0,  # Set内最大BPM跳跃（用于分割判断）
        "ramp_tolerance": 20.0,  # BPM爬坡时的容忍度（提速时）
    },
    
    # Set分割配置（方案C：混合策略 - 基于音乐结构的智能分割）
    "split": {
        "target_duration_minutes": 90.0,  # 目标Set时长（分钟）
        "min_songs": 25,  # 最小25首（硬约束：25-40首）
        "ideal_songs_min": 30,  # 建议最小值30首
        "ideal_songs_max": 35,  # 建议最大值35首
        "max_songs": 40,  # 最大40首（硬约束：25-40首）
        "max_duration": 180.0,  # 最大3小时（极端情况）
        "min_set_duration_force": 25.0,  # 最小Set强制时长（低于此长度不因兼容性分割）
        "respect_sort_order": True,  # 是否尊重排序顺序（只按时长切，不硬切调性/BPM）
        
        # 【修复P3】新增参数化配置
        "bpm_ramp_tolerance": 20.0,  # 提速时的BPM容忍度
        "overlap_fast_bpm": 0.8,  # 快歌混音重叠时间（分钟，BPM>150）
        "overlap_slow_bpm": 1.5,  # 慢歌混音重叠时间（分钟，BPM<115）
        "overlap_standard": 1.2,  # 标准混音重叠时间（分钟，115-150 BPM）
        "bpm_segment_low": 110,  # BPM分段阈值：低速度（<110）
        "bpm_segment_mid": 130,  # BPM分段阈值：中速度（110-130）
        "bpm_segment_mid_high": 150,  # BPM分段阈值：中高速度（130-150）
        
        # 方案C：基于音乐结构的分割参数
        "energy_low_threshold": 40,  # 能量低谷阈值（低于此值可以考虑分割）
        "energy_trend_window": 10,  # 能量趋势分析窗口（最近N首）
        "style_change_weight": 0.8,  # 风格转换权重（0-1）
        "bpm_segment_change_weight": 0.7,  # BPM段落转换权重（0-1）
        "enable_music_based_split": True,  # 启用基于音乐结构的分割
    },
    
    # 桥接曲配置（V4集成）
    "bridge": {
        "enabled": True,
        "max_candidates": 8,      # 桥接曲候选数
        "insert_threshold": 0.65, # 匹配度阈值（65分，从V4的68%调整为65分制）
        "rhythm_weight": 0.35,    # 节奏型权重（35分/100分）
        "key_weight": 0.25,       # 调性权重（25分/100分）
        "bpm_weight": 0.20,       # BPM权重（20分/100分）
        "energy_weight": 0.15,    # 能量权重（15分/100分，保留当前系统优势）
        "mfcc_weight": 0.05,      # MFCC权重（5分/100分，降低）
    },
    
    # 大BPM跳检测配置
    "split_on_large_bpm_jump": {
        "enabled": False,  # 只检测不自动处理（最安全）
        "threshold": 20,   # 阈值20 BPM
        "half_double_check": True,  # 检查half/double关系
    },
    
    # 分析质量问题标注
    "analysis": {
        "recheck_beatgrid_on_warn": True,  # 检测到问题时标注
        "beatgrid_offset_threshold": 10.0,  # 超过10拍视为异常
        "auto_reanalyze": False,  # 先不自动重跑（耗时）
        "drop_confidence_threshold": 0.3,  # DROP置信度阈值
    },
    
    # BPM平滑配置
    "bpm_smoothing": {
        "enabled": False,  # 默认禁用（避免破坏排序）
        "max_diff": 10.0,  # 最大允许BPM差值
        "hard_limit": 12.0,  # 硬限制（超过此值记录警告）
        "respect_sort_order": True,  # 是否尊重排序顺序（只检测不调整）
    },
    
    # 日志配置
    "logging": {
        "show_context_tracks": 0,  # 【OOM修复】不显示上下文，减少输出（原值：3）
        "log_bpm_half_double": False,  # 【OOM修复】不记录BPM日志，减少输出（原值：True）
        "log_key_transitions": False,  # 【OOM修复】不记录调性过渡日志，减少输出（原值：True）
    },
    
    # 去重配置
    "dedup": {
        "use_file_hash": True,  # 是否使用文件hash去重
        "normalize_path": True,  # 是否标准化路径
        "check_hash_at_end": True,  # 文件hash检查放在最后（性能优化）
    },
    
    # 高级功能配置（默认禁用）
    "groove": {
        "enabled": False,  # Groove Pattern分析
        "weight": 5.0,
    },
    "vocal_conflict": {
        "enabled": False,  # 人声段落避冲突
        "penalty": 20.0,
    },
    "valence": {
        "enabled": False,  # 情绪滑动窗口
        "threshold": 0.4,
        "penalty": 10.0,
    },
    "drop_alignment": {
        "enabled": False,  # Drop结构对齐
        "32_bar_bonus": 15.0,
        "16_bar_bonus": 10.0,
    },
    "energy_wave": {
        "enabled": False,  # 能量波形成型
        "enforce_pattern": True,
    },
}


def get_config(custom_config: dict = None) -> dict:
    """
    获取配置（合并自定义配置）
    
    Args:
        custom_config: 自定义配置字典，会覆盖默认值
    
    Returns:
        合并后的配置字典
    """
    import copy
    config = copy.deepcopy(DEFAULT_CONFIG)
    
    # 尝试加载 dj_rules.yaml
    try:
        import yaml
        from pathlib import Path
        # 尝试不同路径
        candidates = [
            Path("run_rekordbox_system/config/dj_rules.yaml"),
            Path("config/dj_rules.yaml"),
        ]
        
        rules_config = None
        for p in candidates:
            if p.exists():
                try:
                    with open(p, 'r', encoding='utf-8') as f:
                        rules_config = yaml.safe_load(f)
                    if rules_config:
                        # print(f"✅ Loaded rules from {p}")
                        break
                except Exception:
                    pass
        
        if rules_config:
            # 深度合并 rules_config 到 config
            def deep_merge_rules(base, override):
                for key, value in override.items():
                    if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                        deep_merge_rules(base[key], value)
                    else:
                        base[key] = value
            deep_merge_rules(config, rules_config)
    except Exception as e:
        # 此时可能无法打印日志，忽略错误
        pass
    
    if custom_config:
        # 深度合并
        def deep_merge(base, override):
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
        
        deep_merge(config, custom_config)

    # ===== 环境变量轻量覆盖（方便不改YAML也能切策略）=====
    # DJ_ENERGY_MODE=single_peak|multi_peak
    # DJ_ENERGY_WAVE=1 强制开启能量波浪（即使 single_peak）
    try:
        import os
        mode = os.environ.get("DJ_ENERGY_MODE")
        if mode:
            mode = str(mode).strip().lower()
            if mode in ("single_peak", "multi_peak", "auto"):
                config.setdefault("energy_profile", {})
                config["energy_profile"]["mode"] = mode
        wave = os.environ.get("DJ_ENERGY_WAVE")
        if wave is not None and str(wave).strip() != "":
            config.setdefault("energy_wave", {})
            config["energy_wave"]["enabled"] = bool(int(str(wave).strip()))
    except Exception:
        pass
    
    return config


def get_config_from_yaml(config_file: str = None) -> dict:
    """
    从YAML文件加载配置
    
    Args:
        config_file: 配置文件路径（可选）
    
    Returns:
        配置字典
    """
    if not config_file:
        config_file = "config/split_config.yaml"
    
    try:
        import yaml
        from pathlib import Path
        config_path = Path(config_file)
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f)
                return get_config(yaml_config)
    except ImportError:
        # yaml模块不存在，返回默认配置
        pass
    except FileNotFoundError:
        # 文件不存在，返回默认配置
        pass
    except Exception as e:
        print(f"⚠️ 加载配置文件失败: {e}，使用默认配置")
    
    return get_config()





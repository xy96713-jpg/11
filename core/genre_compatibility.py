#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业DJ风格兼容性知识库
基于专业DJ实践经验，定义哪些风格可以混在一起

参考来源：
- Beatport风格分类
- Discogs风格树
- 专业DJ论坛（DJ TechTools, Reddit r/DJs）
- Boiler Room / Mixmag Set分析
"""

# ============================================================================
# 风格兼容性矩阵（专业DJ知识）
# ============================================================================

# 风格家族定义（同一家族内的风格可以自由混合）
GENRE_FAMILIES = {
    # House家族（120-130 BPM）
    'house_family': [
        'deep_house',      # Deep House (120-125 BPM)
        'tech_house',      # Tech House (124-128 BPM)
        'house',           # House (120-130 BPM)
        'progressive_house', # Progressive House (126-132 BPM)
        'funky_house',     # Funky House (120-128 BPM)
        'disco_house',     # Disco House (118-125 BPM)
        'afro_house',      # Afro House (118-125 BPM)
        'soulful_house',   # Soulful House (118-125 BPM)
        'jackin_house',    # Jackin House (124-128 BPM)
        'bass_house',      # Bass House (124-130 BPM)
        'uk_garage',       # UK Garage (130-140 BPM)
    ],
    
    # Techno家族（125-145 BPM）
    'techno_family': [
        'techno',          # Techno (130-140 BPM)
        'minimal_techno',  # Minimal Techno (125-135 BPM)
        'melodic_techno',  # Melodic Techno (120-130 BPM)
        'hard_techno',     # Hard Techno (140-150 BPM)
        'industrial_techno', # Industrial Techno (135-145 BPM)
        'acid_techno',     # Acid Techno (130-145 BPM)
        'detroit_techno',  # Detroit Techno (125-135 BPM)
        'dub_techno',      # Dub Techno (120-130 BPM)
    ],
    
    # Bass Music家族（140-175 BPM）
    'bass_family': [
        'dubstep',         # Dubstep (140 BPM)
        'drum_and_bass',   # Drum & Bass (170-180 BPM)
        'jungle',          # Jungle (160-180 BPM)
        'uk_bass',         # UK Bass (130-140 BPM)
        'future_bass',     # Future Bass (140-160 BPM)
        'trap',            # Trap (140 BPM)
        'grime',           # Grime (140 BPM)
    ],
    
    # Latin/Baile家族（125-145 BPM）
    'latin_family': [
        'baile_funk',      # Baile Funk (130-145 BPM)
        'reggaeton',       # Reggaeton (90-100 BPM)
        'dembow',          # Dembow (115-125 BPM)
        'guaracha',        # Guaracha (128-135 BPM)
        'latin_house',     # Latin House (125-130 BPM)
        'moombahton',      # Moombahton (108-115 BPM)
    ],
    
    # Pop/Commercial家族（100-130 BPM）
    'pop_family': [
        'pop',             # Pop (100-130 BPM)
        'dance_pop',       # Dance Pop (118-130 BPM)
        'electro_pop',     # Electro Pop (118-130 BPM)
        'synth_pop',       # Synth Pop (110-130 BPM)
    ],
    
    # Hip-Hop家族（80-115 BPM）
    'hiphop_family': [
        'hip_hop',         # Hip-Hop (80-115 BPM)
        'trap',            # Trap (140 BPM half-time = 70 BPM)
        'r_and_b',         # R&B (60-100 BPM)
        'jersey_club',     # Jersey Club (130-140 BPM)
    ],
    
    # 亚洲流行家族
    'asian_pop_family': [
        'kpop',            # K-Pop (100-130 BPM)
        'jpop',            # J-Pop (100-140 BPM)
        'chinese_pop',     # C-Pop (80-130 BPM)
        'mandopop',        # Mandopop (80-130 BPM)
        'cantopop',        # Cantopop (80-130 BPM)
    ],
    
    # Trance家族（130-150 BPM）
    'trance_family': [
        'trance',          # Trance (130-145 BPM)
        'progressive_trance', # Progressive Trance (128-138 BPM)
        'uplifting_trance', # Uplifting Trance (136-142 BPM)
        'psytrance',       # Psytrance (140-150 BPM)
        'hard_trance',     # Hard Trance (140-150 BPM)
    ],
    
    # Breaks家族（120-140 BPM）
    'breaks_family': [
        'breakbeat',       # Breakbeat (120-140 BPM)
        'big_beat',        # Big Beat (120-140 BPM)
        'nu_skool_breaks', # Nu Skool Breaks (125-140 BPM)
        'electro',         # Electro (125-135 BPM)
    ],
}

# ============================================================================
# 跨家族兼容性（专业DJ常用的风格过渡）
# ============================================================================

# 定义哪些家族之间可以混合（基于BPM和氛围相似性）
CROSS_FAMILY_COMPATIBILITY = {
    # House家族可以和以下家族混合
    'house_family': [
        'techno_family',   # House ↔ Techno（经典组合，BPM接近）
        'breaks_family',   # House ↔ Breaks（节奏相似）
        'latin_family',    # House ↔ Latin（Afro House桥接）
    ],
    
    # Techno家族可以和以下家族混合
    'techno_family': [
        'house_family',    # Techno ↔ House（经典组合）
        'trance_family',   # Techno ↔ Trance（BPM接近）
        'breaks_family',   # Techno ↔ Breaks（工业风格桥接）
    ],
    
    # Bass家族可以和以下家族混合
    'bass_family': [
        'hiphop_family',   # Bass ↔ Hip-Hop（Trap桥接）
        'breaks_family',   # Bass ↔ Breaks（节奏相似）
    ],
    
    # Latin家族可以和以下家族混合
    'latin_family': [
        'house_family',    # Latin ↔ House（Latin House桥接）
        'hiphop_family',   # Latin ↔ Hip-Hop（Reggaeton桥接）
        'pop_family',      # Latin ↔ Pop（商业拉丁）
    ],
    
    # Pop家族可以和以下家族混合
    'pop_family': [
        'house_family',    # Pop ↔ House（Dance Pop桥接）
        'hiphop_family',   # Pop ↔ Hip-Hop（常见组合）
        'asian_pop_family', # Pop ↔ Asian Pop（风格相似）
    ],
    
    # Hip-Hop家族可以和以下家族混合
    'hiphop_family': [
        'bass_family',     # Hip-Hop ↔ Bass（Trap桥接）
        'pop_family',      # Hip-Hop ↔ Pop（常见组合）
        'latin_family',    # Hip-Hop ↔ Latin（Reggaeton桥接）
    ],
    
    # 亚洲流行家族可以和以下家族混合
    # 注意：华语/K-Pop/J-Pop不能和电子乐桥接（专业DJ规范）
    'asian_pop_family': [
        'pop_family',      # Asian Pop ↔ Pop（风格相似）
        # 'house_family',  # 已移除：Asian Pop不能和电子乐混
    ],
    
    # Trance家族可以和以下家族混合
    'trance_family': [
        'techno_family',   # Trance ↔ Techno（BPM接近）
        'house_family',    # Trance ↔ House（Progressive桥接）
    ],
    
    # Breaks家族可以和以下家族混合
    'breaks_family': [
        'house_family',    # Breaks ↔ House（节奏相似）
        'techno_family',   # Breaks ↔ Techno（工业风格）
        'bass_family',     # Breaks ↔ Bass（节奏相似）
    ],
}

# ============================================================================
# 专业DJ风格过渡建议
# ============================================================================

# 定义最佳过渡路径（从A风格到B风格的推荐桥接风格）
TRANSITION_BRIDGES = {
    # House → Techno 过渡
    ('house', 'techno'): ['tech_house', 'minimal_techno'],
    ('deep_house', 'techno'): ['tech_house', 'melodic_techno'],
    
    # Techno → House 过渡
    ('techno', 'house'): ['tech_house', 'progressive_house'],
    ('techno', 'deep_house'): ['melodic_techno', 'dub_techno'],
    
    # House → Trance 过渡
    ('house', 'trance'): ['progressive_house', 'progressive_trance'],
    ('progressive_house', 'trance'): ['progressive_trance'],
    
    # Hip-Hop → House 过渡
    ('hip_hop', 'house'): ['jersey_club', 'bass_house'],
    ('trap', 'house'): ['bass_house', 'uk_bass'],
    
    # Latin → House 过渡
    ('baile_funk', 'house'): ['latin_house', 'afro_house'],
    ('reggaeton', 'house'): ['moombahton', 'latin_house'],
    
    # K-Pop → House 过渡
    ('kpop', 'house'): ['dance_pop', 'electro_pop'],
    
    # Bass → Techno 过渡
    ('dubstep', 'techno'): ['uk_bass', 'industrial_techno'],
    ('drum_and_bass', 'techno'): ['breakbeat', 'hard_techno'],
}

# ============================================================================
# BPM范围定义
# ============================================================================

GENRE_BPM_RANGES = {
    # House家族
    'deep_house': (118, 125),
    'tech_house': (124, 130),
    'house': (120, 130),
    'progressive_house': (126, 132),
    'funky_house': (120, 128),
    'disco_house': (118, 125),
    'afro_house': (118, 125),
    'soulful_house': (118, 125),
    'jackin_house': (124, 128),
    'bass_house': (124, 130),
    'uk_garage': (130, 140),
    
    # Techno家族
    'techno': (130, 140),
    'minimal_techno': (125, 135),
    'melodic_techno': (120, 130),
    'hard_techno': (140, 150),
    'industrial_techno': (135, 145),
    'acid_techno': (130, 145),
    'detroit_techno': (125, 135),
    'dub_techno': (120, 130),
    
    # Bass家族
    'dubstep': (138, 142),
    'drum_and_bass': (170, 180),
    'jungle': (160, 180),
    'uk_bass': (130, 140),
    'future_bass': (140, 160),
    'trap': (135, 145),
    'grime': (138, 142),
    
    # Latin家族
    'baile_funk': (130, 145),
    'reggaeton': (88, 100),
    'dembow': (115, 125),
    'guaracha': (128, 135),
    'latin_house': (125, 130),
    'moombahton': (108, 115),
    
    # Pop家族
    'pop': (100, 130),
    'dance_pop': (118, 130),
    'electro_pop': (118, 130),
    'synth_pop': (110, 130),
    
    # Hip-Hop家族
    'hip_hop': (80, 115),
    'r_and_b': (60, 100),
    'jersey_club': (130, 140),
    
    # 亚洲流行
    'kpop': (100, 130),
    'jpop': (100, 140),
    'chinese_pop': (80, 130),
    
    # Trance家族
    'trance': (130, 145),
    'progressive_trance': (128, 138),
    'uplifting_trance': (136, 142),
    'psytrance': (140, 150),
    'hard_trance': (140, 150),
    
    # Breaks家族
    'breakbeat': (120, 140),
    'big_beat': (120, 140),
    'nu_skool_breaks': (125, 140),
    'electro': (125, 135),
}

# ============================================================================
# 风格识别关键词
# ============================================================================

GENRE_KEYWORDS = {
    # House家族
    'deep_house': ['deep house', 'deep', 'soulful', 'jazzy house'],
    'tech_house': ['tech house', 'tech', 'techy', 'toolroom'],
    'house': ['house', 'club', 'dancefloor'],
    'progressive_house': ['progressive', 'prog house', 'anjuna'],
    'funky_house': ['funky', 'funk house', 'disco'],
    'disco_house': ['disco', 'nu disco', 'nu-disco'],
    'afro_house': ['afro', 'afro house', 'tribal'],
    'bass_house': ['bass house', 'uk bass', 'night bass'],
    'uk_garage': ['uk garage', 'ukg', '2-step', 'garage'],
    
    # Techno家族
    'techno': ['techno', 'berlin', 'warehouse'],
    'minimal_techno': ['minimal', 'micro', 'click'],
    'melodic_techno': ['melodic techno', 'melodic', 'afterlife', 'tale of us'],
    'hard_techno': ['hard techno', 'industrial', 'rave'],
    'acid_techno': ['acid', '303', 'tb-303'],
    
    # Bass家族
    'dubstep': ['dubstep', 'brostep', 'riddim'],
    'drum_and_bass': ['drum and bass', 'dnb', 'd&b', 'jungle'],
    'future_bass': ['future bass', 'future', 'flume'],
    'trap': ['trap', 'edm trap', 'festival trap'],
    
    # Latin家族
    'baile_funk': ['baile', 'funk', 'brazilian', 'favela'],
    'reggaeton': ['reggaeton', 'perreo', 'dembow'],
    'guaracha': ['guaracha', 'aleteo', 'zapateo'],
    'latin_house': ['latin house', 'latino', 'salsa house'],
    
    # Pop家族
    'pop': ['pop', 'mainstream', 'radio'],
    'dance_pop': ['dance pop', 'edm pop', 'commercial'],
    'electro_pop': ['electro pop', 'synth pop', 'synthwave'],
    
    # Hip-Hop家族
    'hip_hop': ['hip hop', 'hip-hop', 'rap', 'hiphop'],
    'jersey_club': ['jersey', 'jersey club', 'baltimore'],
    'r_and_b': ['r&b', 'rnb', 'r and b', 'soul'],
    
    # 亚洲流行
    'kpop': ['kpop', 'k-pop', 'korean', 'bts', 'blackpink', 'twice', 'ive', 
             'aespa', 'newjeans', 'stayc', 'itzy', 'le sserafim', 'nmixx', 
             'i-dle', 'illit', 'xg', 'akmu', 'bigbang', 'exo', 'nct'],
    'jpop': ['jpop', 'j-pop', 'japanese', 'anime', 'vocaloid'],
    'chinese_pop': ['cpop', 'c-pop', 'mandopop', 'cantopop'],
    
    # Trance家族
    'trance': ['trance', 'uplifting', 'vocal trance'],
    'progressive_trance': ['progressive trance', 'prog trance'],
    'psytrance': ['psytrance', 'psy', 'goa', 'full on'],
    
    # Breaks家族
    'breakbeat': ['breakbeat', 'breaks', 'break'],
    'electro': ['electro', 'electro house', 'complextro'],
}

# ============================================================================
# 华语流行子风格细分系统
# ============================================================================

# 华语子风格定义
CHINESE_SUBGENRES = {
    # 中国风 (Chinese Traditional Fusion)
    'chinese_traditional': {
        'keywords': ['中国风', '古风', '国风', '戏腔', '京剧', '二胡', '琵琶', '古筝',
                     '青花瓷', '东风破', '菊花台', '兰亭序', '烟花易冷', '发如雪',
                     '千里之外', '霍元甲', '双截棍', '龙拳', '本草纲目', '蛇舞'],
        'artists': ['周杰伦', '方文山', '李玉刚', '霍尊', '戴荃', '河图', '银临'],
        'mood': 'artistic',  # 艺术性强
        'energy_range': (30, 70),
    },
    
    # 华语R&B/Soul
    'chinese_rnb': {
        'keywords': ['r&b', 'rnb', 'soul', '灵魂', '节奏蓝调', 'neo-soul',
                     '慢摇', '情歌', '抒情'],
        'artists': ['陶喆', '方大同', '王力宏', '林俊杰', '周杰伦', '曹格', 
                    '黄立行', '潘玮柏', '罗志祥', '周汤豪', '瘦子e.so',
                    '蛋堡', '顽童mj116', '热狗', 'mc hotdog'],
        'mood': 'smooth',  # 平滑流畅
        'energy_range': (30, 60),
    },
    
    # 华语Hip-Hop/说唱
    'chinese_hiphop': {
        'keywords': ['说唱', 'rap', 'hiphop', 'hip-hop', 'freestyle', 'flow',
                     'trap', 'drill', '嘻哈', '饶舌'],
        'artists': ['周杰伦', '潘玮柏', '热狗', 'mc hotdog', '顽童mj116', 
                    '蛋堡', '瘦子e.so', 'gai', 'pg one', 'bridge', 'vava',
                    '法老', '艾热', '杨和苏', '刘聪', '万妮达', '王以太',
                    '那吾克热', 'jony j', 'tizzy t', '小鬼', '王琳凯'],
        'mood': 'energetic',  # 有能量
        'energy_range': (50, 85),
    },
    
    # 华语舞曲/电子
    'chinese_dance': {
        'keywords': ['舞曲', 'dance', 'edm', 'remix', 'club', '电音', '电子',
                     'disco', '迪斯科', 'house', 'techno'],
        'artists': ['蔡依林', '罗志祥', '潘玮柏', '王心凌', '萧亚轩', 
                    '张韶涵', '杨丞琳', 'by2', 's.h.e', '飞轮海'],
        'mood': 'upbeat',  # 欢快
        'energy_range': (60, 90),
    },
    
    # 华语抒情/情歌
    'chinese_ballad': {
        'keywords': ['情歌', '抒情', '慢歌', '伤感', '思念', '分手', '失恋',
                     '想你', '爱你', '等你', '离开', '回忆', '眼泪', '心痛'],
        'artists': ['张学友', '刘德华', '张信哲', '周传雄', '光良', '品冠',
                    '梁静茹', '戴佩妮', '刘若英', '范玮琪', '陈绮贞',
                    '徐佳莹', '田馥甄', '魏如萱', '蔡健雅', '孙燕姿'],
        'mood': 'emotional',  # 情感丰富
        'energy_range': (20, 50),
    },
    
    # 华语摇滚
    'chinese_rock': {
        'keywords': ['摇滚', 'rock', 'band', '乐队', '吉他', 'guitar', 
                     'punk', '朋克', 'metal', '金属'],
        'artists': ['五月天', 'mayday', '伍佰', '信', '动力火车', '苏打绿',
                    '告五人', '茄子蛋', '草东没有派对', '落日飞车',
                    '万能青年旅店', '新裤子', '痛仰', '逃跑计划', '鹿先森'],
        'mood': 'intense',  # 强烈
        'energy_range': (50, 90),
    },
    
    # 华语民谣/独立
    'chinese_folk': {
        'keywords': ['民谣', 'folk', '独立', 'indie', '木吉他', 'acoustic',
                     '清新', '文艺', '小清新'],
        'artists': ['陈绮贞', '魏如萱', '徐佳莹', '蔡健雅', '卢广仲',
                    '李宗盛', '罗大佑', '周华健', '李健', '朴树', '许巍',
                    '宋冬野', '马頔', '陈粒', '房东的猫', '花粥'],
        'mood': 'gentle',  # 温柔
        'energy_range': (20, 50),
    },
}

# 华语子风格兼容性矩阵
CHINESE_SUBGENRE_COMPATIBILITY = {
    'chinese_traditional': {
        'chinese_traditional': 100,  # 同类型
        'chinese_rnb': 40,           # 中国风和R&B差异大
        'chinese_hiphop': 60,        # 周杰伦式中国风说唱可以
        'chinese_dance': 30,         # 差异很大
        'chinese_ballad': 50,        # 都有艺术性
        'chinese_rock': 40,          # 差异大
        'chinese_folk': 50,          # 都有传统元素
    },
    'chinese_rnb': {
        'chinese_traditional': 40,
        'chinese_rnb': 100,
        'chinese_hiphop': 85,        # R&B和Hip-Hop很搭
        'chinese_dance': 60,         # 可以混
        'chinese_ballad': 70,        # 都是慢歌系
        'chinese_rock': 30,          # 差异大
        'chinese_folk': 50,          # 都比较柔和
    },
    'chinese_hiphop': {
        'chinese_traditional': 60,   # 中国风说唱
        'chinese_rnb': 85,           # 经典组合
        'chinese_hiphop': 100,
        'chinese_dance': 75,         # 都有节奏感
        'chinese_ballad': 30,        # 差异大
        'chinese_rock': 50,          # 有些可以
        'chinese_folk': 30,          # 差异大
    },
    'chinese_dance': {
        'chinese_traditional': 30,
        'chinese_rnb': 60,
        'chinese_hiphop': 75,
        'chinese_dance': 100,
        'chinese_ballad': 30,        # 差异大
        'chinese_rock': 50,          # 摇滚舞曲
        'chinese_folk': 20,          # 差异很大
    },
    'chinese_ballad': {
        'chinese_traditional': 50,
        'chinese_rnb': 70,
        'chinese_hiphop': 30,
        'chinese_dance': 30,
        'chinese_ballad': 100,
        'chinese_rock': 40,          # 摇滚情歌
        'chinese_folk': 80,          # 都是慢歌
    },
    'chinese_rock': {
        'chinese_traditional': 40,
        'chinese_rnb': 30,
        'chinese_hiphop': 50,
        'chinese_dance': 50,
        'chinese_ballad': 40,
        'chinese_rock': 100,
        'chinese_folk': 60,          # 民谣摇滚
    },
    'chinese_folk': {
        'chinese_traditional': 50,
        'chinese_rnb': 50,
        'chinese_hiphop': 30,
        'chinese_dance': 20,
        'chinese_ballad': 80,
        'chinese_rock': 60,
        'chinese_folk': 100,
    },
}

# 华语歌手列表（用于识别华语流行）
CHINESE_ARTISTS = [
    # 台湾歌手
    '王心凌', '蔡依林', '林俊杰', '周杰伦', '张惠妹', '孙燕姿',
    '李玟', '蔡琴', '王菲', '曹格', '陈奕迅', 'twins', 'f.i.r',
    '张学友', '刘德华', '黎明', '郭富城', '邓紫棋', '华晨宇',
    '周深', '毛不易', '李荣浩', '林宥嘉', '萧敬腾', '杨丞琳', '罗志祥',
    '潘玮柏', '王力宏', '陶喆', '方大同', '张韶涵', '梁静茹', '戴佩妮',
    '五月天', 'mayday', 's.h.e', '飞轮海', '棒棒堂', 'lollipop',
    '蔡健雅', '陈绮贞', '魏如萱', '徐佳莹', '田馥甄', 'hebe',
    '张信哲', '任贤齐', '伍佰', '苏打绿', '告五人', '茄子蛋',
    '徐怀钰', '黄湘怡', '孙盛希', '葛仲珊', '刘若英', '孔令奇',
    '范玮琪', '光良', '品冠', '动力火车', '信', '阿信', '怪兽',
    '萧亚轩', '温岚', '戴爱玲', '张智成', '许茹芸', '许美静',
    '张宇', '游鸿明', '周传雄', '张洪量', '童安格',
    '费玉清', '邓丽君', '凤飞飞', '蔡幸娟', '高胜美', '叶倩文',
    '林忆莲', '关淑怡', '彭羚', '陈慧娴', '陈慧琳', '郑秀文',
    '容祖儿', '谢安琪', '杨千嬅', '何韵诗', '卫兰', '泳儿',
    '黄立行', '陈绮贞',
    # 大陆歌手
    '那英', '刘欢', '韩红', '谭晶', '宋祖英',
    '汪峰', '许巍', '朴树', '李健', '张杰',
    '张艺兴', '鹿晗',
    '吴亦凡', '黄子韬', '王嘉尔', 'jackson wang',
    # 组合
    'tfboys', 'snh48', 'by2', 'she', 's.h.e',
]

# 日语歌手/关键词列表
JAPANESE_ARTISTS = [
    '安室奈美恵', 'あむろ', 'なみえ', 'サザン', 'オールスターズ',
    'perfume', 'きゃりーぱみゅぱみゅ', 'kyary', 'babymetal',
    '宇多田ヒカル', 'utada', '浜崎あゆみ', 'ayumi', '倖田來未', 'koda kumi',
    'yoasobi', 'ado', 'kenshi yonezu', '米津玄師', 'eve', 'vaundy',
    'jpop', 'j-pop', 'japanese',
]

# ============================================================================
# 风格兼容性检查函数
# ============================================================================

def get_genre_family(genre: str) -> str:
    """获取风格所属的家族"""
    genre_lower = genre.lower().replace('-', '_').replace(' ', '_')
    
    for family, genres in GENRE_FAMILIES.items():
        if genre_lower in genres:
            return family
    
    return 'unknown'


def are_genres_compatible(genre_a: str, genre_b: str) -> tuple:
    """
    检查两个风格是否兼容
    
    Returns:
        (is_compatible, compatibility_score, reason)
        - is_compatible: 是否兼容
        - compatibility_score: 兼容度分数 (0-100)
        - reason: 原因说明
    """
    # 特殊处理：华语子风格之间的兼容性
    chinese_subgenres = list(CHINESE_SUBGENRES.keys()) + ['chinese_pop']
    
    if genre_a in chinese_subgenres and genre_b in chinese_subgenres:
        # 两首都是华语歌，使用子风格兼容性矩阵
        compat_score = get_chinese_subgenre_compatibility(genre_a, genre_b)
        is_compat = compat_score >= 60
        
        if compat_score >= 80:
            return (True, compat_score, f"华语子风格兼容: {genre_a} + {genre_b}")
        elif compat_score >= 60:
            return (True, compat_score, f"华语子风格可混: {genre_a} + {genre_b}")
        else:
            return (False, compat_score, f"华语子风格冲突: {genre_a} vs {genre_b}")
    
    # 华语子风格和其他风格的兼容性
    # 注意：华语/K-Pop/J-Pop不能和电子乐桥接（专业DJ规范）
    if genre_a in chinese_subgenres or genre_b in chinese_subgenres:
        chinese_genre = genre_a if genre_a in chinese_subgenres else genre_b
        other_genre = genre_b if genre_a in chinese_subgenres else genre_a
        
        # 华语歌只能和华语歌或Pop混，不能和电子乐混
        other_family = get_genre_family(other_genre)
        if other_family == 'pop_family':
            return (True, 60, f"华语可混Pop: {chinese_genre} + {other_genre}")
        
        # 华语歌和电子乐不兼容（包括华语舞曲）
        return (False, 30, f"华语和电子风格差异大: {chinese_genre} vs {other_genre}")
    
    family_a = get_genre_family(genre_a)
    family_b = get_genre_family(genre_b)
    
    # 同一家族：完全兼容
    if family_a == family_b:
        return (True, 100, f"同一风格家族: {family_a}")
    
    # 跨家族兼容性检查
    if family_a in CROSS_FAMILY_COMPATIBILITY:
        if family_b in CROSS_FAMILY_COMPATIBILITY[family_a]:
            return (True, 80, f"跨家族兼容: {family_a} ↔ {family_b}")
    
    if family_b in CROSS_FAMILY_COMPATIBILITY:
        if family_a in CROSS_FAMILY_COMPATIBILITY[family_b]:
            return (True, 80, f"跨家族兼容: {family_b} ↔ {family_a}")
    
    # 不兼容
    return (False, 20, f"风格不兼容: {family_a} vs {family_b}")


def get_transition_bridge(genre_from: str, genre_to: str) -> list:
    """获取从A风格到B风格的推荐桥接风格"""
    key = (genre_from.lower(), genre_to.lower())
    
    if key in TRANSITION_BRIDGES:
        return TRANSITION_BRIDGES[key]
    
    # 反向查找
    reverse_key = (genre_to.lower(), genre_from.lower())
    if reverse_key in TRANSITION_BRIDGES:
        return TRANSITION_BRIDGES[reverse_key]
    
    return []


def has_chinese_characters(text: str) -> bool:
    """检查文本是否包含中文字符"""
    import re
    # 匹配中文字符（包括简体和繁体）
    chinese_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')
    return bool(chinese_pattern.search(text))


def has_japanese_characters(text: str) -> bool:
    """检查文本是否包含日文字符（平假名、片假名）"""
    import re
    # 匹配日文平假名和片假名
    japanese_pattern = re.compile(r'[\u3040-\u309f\u30a0-\u30ff]')
    return bool(japanese_pattern.search(text))


def has_korean_characters(text: str) -> bool:
    """检查文本是否包含韩文字符"""
    import re
    # 匹配韩文字符
    korean_pattern = re.compile(r'[\uac00-\ud7af\u1100-\u11ff]')
    return bool(korean_pattern.search(text))


def detect_chinese_subgenre(filename: str, title: str = '') -> str:
    """
    检测华语歌曲的子风格
    
    Returns:
        子风格名称，如 'chinese_traditional', 'chinese_rnb', 'chinese_hiphop' 等
    """
    text = f"{filename} {title}".lower()
    
    # 按优先级检测子风格
    subgenre_scores = {}
    
    for subgenre, info in CHINESE_SUBGENRES.items():
        score = 0
        
        # 关键词匹配
        for keyword in info.get('keywords', []):
            if keyword.lower() in text:
                score += 10
        
        # 歌手匹配
        for artist in info.get('artists', []):
            if artist.lower() in text:
                score += 5
        
        if score > 0:
            subgenre_scores[subgenre] = score
    
    # 返回得分最高的子风格
    if subgenre_scores:
        return max(subgenre_scores, key=subgenre_scores.get)
    
    # 默认返回华语流行
    return 'chinese_pop'


def get_chinese_subgenre_compatibility(subgenre1: str, subgenre2: str) -> int:
    """
    获取两个华语子风格的兼容度
    
    Returns:
        兼容度分数 (0-100)
    """
    if subgenre1 == subgenre2:
        return 100
    
    # 查找兼容性矩阵
    if subgenre1 in CHINESE_SUBGENRE_COMPATIBILITY:
        if subgenre2 in CHINESE_SUBGENRE_COMPATIBILITY[subgenre1]:
            return CHINESE_SUBGENRE_COMPATIBILITY[subgenre1][subgenre2]
    
    # 反向查找
    if subgenre2 in CHINESE_SUBGENRE_COMPATIBILITY:
        if subgenre1 in CHINESE_SUBGENRE_COMPATIBILITY[subgenre2]:
            return CHINESE_SUBGENRE_COMPATIBILITY[subgenre2][subgenre1]
    
    # 默认中等兼容
    return 50


def detect_genre_from_filename(filename: str) -> str:
    """
    从文件名检测风格
    
    优先级：
    1. 中文字符 → 检测华语子风格
    2. 华语歌手 → 检测华语子风格
    3. 日文字符 → jpop
    4. 日语歌手 → jpop
    5. 韩文字符 → kpop
    6. K-Pop歌手 → kpop
    7. 风格关键词 → 对应风格
    8. remix/edit → house
    9. 默认 → electronic
    """
    name_lower = filename.lower()
    
    # 1. 检查中文字符（最可靠的华语检测）
    if has_chinese_characters(filename):
        # 进一步检测华语子风格
        return detect_chinese_subgenre(filename)
    
    # 2. 检查华语歌手
    for artist in CHINESE_ARTISTS:
        if artist.lower() in name_lower:
            return detect_chinese_subgenre(filename)
    
    # 3. 检查日文字符
    if has_japanese_characters(filename):
        return 'jpop'
    
    # 4. 检查日语歌手
    for artist in JAPANESE_ARTISTS:
        if artist.lower() in name_lower:
            return 'jpop'
    
    # 5. 检查韩文字符
    if has_korean_characters(filename):
        return 'kpop'
    
    # 6. 检查K-Pop关键词
    for keyword in GENRE_KEYWORDS.get('kpop', []):
        if keyword.lower() in name_lower:
            return 'kpop'
    
    # 7. 检查其他风格关键词
    for genre, keywords in GENRE_KEYWORDS.items():
        if genre in ['kpop', 'jpop', 'chinese_pop']:
            continue  # 已经检查过
        for keyword in keywords:
            if keyword.lower() in name_lower:
                return genre
    
    # 8. 检查remix/edit关键词（通常是electronic/house）
    electronic_keywords = ['remix', 'edit', 'bootleg', 'flip', 'rework', 'mix']
    if any(kw in name_lower for kw in electronic_keywords):
        return 'house'
    
    # 9. 默认
    return 'electronic'


def get_compatible_genres(genre: str) -> list:
    """获取与指定风格兼容的所有风格"""
    family = get_genre_family(genre)
    
    if family == 'unknown':
        return []
    
    # 同家族风格
    compatible = list(GENRE_FAMILIES.get(family, []))
    
    # 跨家族兼容风格
    if family in CROSS_FAMILY_COMPATIBILITY:
        for compatible_family in CROSS_FAMILY_COMPATIBILITY[family]:
            compatible.extend(GENRE_FAMILIES.get(compatible_family, []))
    
    return list(set(compatible))


# ============================================================================
# 测试
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("专业DJ风格兼容性知识库测试")
    print("=" * 80)
    print()
    
    # 测试风格检测
    test_files = [
        "王心凌 - happy loving",
        "蔡依林 - 独占神话",
        "ive - after like",
        "newjeans - super shy",
        "tech house my hump5 (polovich edit)",
        "sade - smooth operator (gean brazy baile funk remix)",
        "kanye west - power (skim edit)",
        "安室奈美恵 - baby don't cry",
    ]
    
    print("风格检测测试：")
    for filename in test_files:
        genre = detect_genre_from_filename(filename)
        print(f"  {filename[:40]:40s} → {genre}")
    print()
    
    # 测试风格兼容性
    test_pairs = [
        ('deep_house', 'tech_house'),
        ('deep_house', 'techno'),
        ('house', 'kpop'),
        ('baile_funk', 'house'),
        ('trap', 'dubstep'),
    ]
    
    print("风格兼容性测试：")
    for genre_a, genre_b in test_pairs:
        is_compat, score, reason = are_genres_compatible(genre_a, genre_b)
        status = "✅" if is_compat else "❌"
        print(f"  {status} {genre_a} ↔ {genre_b}: {score}/100 ({reason})")
    print()
    
    # 测试过渡桥接
    print("过渡桥接测试：")
    bridges = get_transition_bridge('house', 'techno')
    print(f"  House → Techno: {bridges}")
    bridges = get_transition_bridge('hip_hop', 'house')
    print(f"  Hip-Hop → House: {bridges}")

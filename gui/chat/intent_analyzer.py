# gui/chat/intent_analyzer.py
"""意图分析模块 - 从用户输入中提取意图和关键词"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class IntentResult:
    """意图分析结果"""
    type: str  # text_to_image, image_to_image, couple_generation, chat
    prompt: str = ""
    negative: str = ""
    keywords: Dict = field(default_factory=dict)
    original_text: str = ""
    is_continuation: bool = False
    llm_enhanced: bool = False
    params: Dict = field(default_factory=dict)
    confidence: float = 0.0
    content_filtered: bool = False
    safe_alternatives: List[str] = field(default_factory=list)


class IntentAnalyzer:
    """意图分析器"""
    
    # ===== 关键词映射 =====
    ANIMAL_KEYWORDS = ['猫', '狗', '兔', '鸟', '鱼', '马', '鹿', '熊', '熊猫', '老虎', '狮子']
    LANDSCAPE_KEYWORDS = ['风景', '山水', '日落', '日出', '大海', '山川', '森林', '花园']
    COUPLE_KEYWORDS = ['和', '与', '一起', '两人', '双人', '情侣', 'couple', 'together']
    CONTINUATION_KEYWORDS = ['再来', '继续', '换一个', '换一张', '再生成', 'another', 'continue']
    
    def __init__(self):
        self._unsafe_detector = UnsafeContentDetector()
    
    def analyze(self, text: str, has_image: bool = False, 
                has_multiple_images: bool = False) -> IntentResult:
        """
        分析用户输入意图
        """
        text_lower = text.lower()
        
        # 1. 检测不安全内容
        is_unsafe, keywords = self._unsafe_detector.detect(text)
        if is_unsafe:
            return self._handle_unsafe_content(text, keywords)
        
        # 2. 检测双人合成意图
        if has_multiple_images and self._is_couple_intent(text):
            return self._analyze_couple_intent(text)
        
        # 3. 分类意图
        classification = self._classify_intent(text, has_image)
        
        # 4. 提取关键词
        keywords = self._extract_keywords(text)
        
        # 5. 检测是否延续
        is_continuation = self._is_continuation(text)
        
        return IntentResult(
            type=classification["type"],
            keywords=keywords,
            original_text=text,
            is_continuation=is_continuation,
            confidence=classification.get("confidence", 0.5),
        )
    
    def _is_couple_intent(self, text: str) -> bool:
        """检测是否为双人合成意图"""
        return any(k in text.lower() for k in self.COUPLE_KEYWORDS)
    
    def _classify_intent(self, text: str, has_image: bool) -> Dict:
        """分类意图"""
        text_lower = text.lower()
        
        edit_indicators = ['变成', '改为', '换成', '改成', '换', '改', '修改', '调整']
        style_indicators = ['风格', '画风', '质感', '样式', 'styl']
        image_descriptors = ['在沙滩', '在海边', '在花园', '在森林', '在城市']
        
        has_edit = any(k in text_lower for k in edit_indicators)
        has_style = any(k in text_lower for k in style_indicators)
        has_description = any(k in text_lower for k in image_descriptors)
        explicit_gen = any(k in text_lower for k in ['生成', '画', '创建', 'create', 'generate'])
        
        if has_image and (has_edit or has_style):
            return {"type": "image_to_image", "confidence": 0.9}
        if has_image and has_description:
            return {"type": "image_to_image", "confidence": 0.6}
        if explicit_gen or has_description or len(text) > 5:
            return {"type": "text_to_image", "confidence": 0.8}
        return {"type": "chat", "confidence": 0.3}
    
    def _extract_keywords(self, text: str) -> Dict:
        """提取关键词"""
        text_lower = text.lower()
        
        return {
            "genders": self._extract_genders(text_lower),
            "clothes": self._extract_clothes(text_lower),
            "colors": self._extract_colors(text_lower),      # ✅ 新增
            "scenes": self._extract_scenes(text_lower),
            "styles": self._extract_styles(text_lower),
            "poses": self._extract_poses(text_lower),
            "expressions": self._extract_expressions(text_lower),
            "lighting": self._extract_lighting(text_lower),
        }
    
    def _extract_genders(self, text: str) -> List[str]:
        """提取性别"""
        genders = []
        if any(k in text for k in ['女', '美女', '女孩', '女性']):
            genders.append("1girl")
        if any(k in text for k in ['男', '帅哥', '男孩', '男性']):
            genders.append("1boy")
        if any(k in text for k in ['情侣', '双人', '两人', 'couple']):
            genders.append("1girl, 1boy")
        return genders
    
    def _extract_clothes(self, text: str) -> List[str]:
        """提取服装"""
        clothes_map = {
            '裙子': 'dress', '礼服': 'evening gown', '旗袍': 'qipao',
            '汉服': 'hanfu', '和服': 'kimono', '泳衣': 'swimsuit',
            '比基尼': 'bikini', '内衣': 'lingerie', '婚纱': 'wedding dress'
        }
        return [en for cn, en in clothes_map.items() if cn in text]
    
    def _extract_colors(self, text: str) -> List[str]:  # ✅ 新增方法
        """提取颜色"""
        colors_map = {
            '白色': 'white', '黑色': 'black', '红色': 'red', '蓝色': 'blue',
            '绿色': 'green', '粉色': 'pink', '紫色': 'purple', '黄色': 'yellow',
            '金色': 'golden', '银色': 'silver', '透明': 'transparent',
            '裸色': 'nude', '橙色': 'orange', '灰色': 'gray', '棕色': 'brown',
            '彩色': 'colorful', '渐变': 'gradient'
        }
        return [en for cn, en in colors_map.items() if cn in text]
    
    def _extract_scenes(self, text: str) -> List[str]:
        """提取场景"""
        scenes_map = {
            '沙滩': 'beach', '海滩': 'beach', '海边': 'ocean',
            '卧室': 'bedroom', '花园': 'garden', '森林': 'forest',
            '城市': 'city', '办公室': 'office', '日落': 'sunset',
            '星空': 'starry sky', '雨中': 'rainy', '雪地': 'snowy',
            '花海': 'flower field'
        }
        return [en for cn, en in scenes_map.items() if cn in text]
    
    def _extract_styles(self, text: str) -> List[str]:
        """提取风格"""
        styles_map = {
            '动漫': 'anime style', '油画': 'oil painting style',
            '水彩': 'watercolor style', '素描': 'sketch style',
            '写实': 'photorealistic', '赛博朋克': 'cyberpunk style',
            '暗黑': 'dark style', '梦幻': 'dreamy style',
            '复古': 'vintage style', '古风': 'traditional Chinese style',
            '唯美': 'aesthetic style', '可爱': 'cute style',
            '性感': 'sexy style', '优雅': 'elegant style'
        }
        return [en for cn, en in styles_map.items() if cn in text]
    
    def _extract_poses(self, text: str) -> List[str]:
        """提取姿势"""
        poses_map = {
            '站立': 'standing', '坐': 'sitting', '躺': 'lying',
            '蹲': 'squatting', '跪': 'kneeling', '弯腰': 'bending over',
            '回头': 'looking back', '侧身': 'side view',
            '奔跑': 'running', '走路': 'walking', '跳舞': 'dancing',
            '拥抱': 'hugging', '接吻': 'kissing', '仰头': 'looking up',
            '低头': 'looking down'
        }
        return [en for cn, en in poses_map.items() if cn in text]
    
    def _extract_expressions(self, text: str) -> List[str]:
        """提取表情"""
        exp_map = {
            '微笑': 'smiling', '大笑': 'laughing', '严肃': 'serious',
            '忧郁': 'melancholy', '诱惑': 'seductive', '害羞': 'shy',
            '惊讶': 'surprised', '愤怒': 'angry', '悲伤': 'sad',
            '深情': 'affectionate', '温柔': 'gentle expression'
        }
        return [en for cn, en in exp_map.items() if cn in text]
    
    def _extract_lighting(self, text: str) -> List[str]:
        """提取灯光"""
        lighting_map = {
            '自然光': 'natural lighting', '暖光': 'warm lighting',
            '冷光': 'cold lighting', '柔光': 'soft lighting',
            '逆光': 'backlighting', '阳光': 'sunlight',
            '月光': 'moonlight', '烛光': 'candlelight',
            '霓虹': 'neon lighting', '黄昏': 'golden hour',
            '黎明': 'dawn light'
        }
        return [en for cn, en in lighting_map.items() if cn in text]
    
    def _is_continuation(self, text: str) -> bool:
        """检测是否为延续性指令"""
        return any(k in text.lower() for k in self.CONTINUATION_KEYWORDS)
    
    def _analyze_couple_intent(self, text: str) -> IntentResult:
        """分析双人合成意图"""
        # 提取动作
        action = "standing together"
        action_map = {
            '拥抱': 'hugging each other',
            '牵手': 'holding hands',
            '接吻': 'kissing',
            '依偎': 'cuddling',
            '并肩': 'standing side by side',
            '背靠背': 'back to back',
            '跳舞': 'dancing together',
            '对视': 'looking at each other',
        }
        for cn, en in action_map.items():
            if cn in text:
                action = en
                break
        
        # 构建提示词
        prompt = f"1woman and 1man, {action}, couple, romantic, masterpiece, best quality, photorealistic"
        
        return IntentResult(
            type="couple_generation",
            prompt=prompt,
            original_text=text,
            params={"action": action},
            confidence=0.9
        )
    
    def _handle_unsafe_content(self, text: str, keywords: List[str]) -> IntentResult:
        """处理不安全内容"""
        safe_alternatives = self._get_safe_alternatives(text)
        return IntentResult(
            type="text_to_image",
            prompt=safe_alternatives[0] if safe_alternatives else "",
            original_text=text,
            content_filtered=True,
            safe_alternatives=safe_alternatives,
            confidence=0.5
        )
    
    def _get_safe_alternatives(self, text: str) -> List[str]:
        """获取安全替代提示词"""
        text_lower = text.lower()
        
        alternatives = {
            "romantic": [
                "couple hugging in sunset, romantic atmosphere, artistic photography, masterpiece, best quality",
                "lovers embracing, intimate moment, soft lighting, elegant, 8k, highly detailed",
            ],
            "passionate": [
                "passionate embrace, intense emotion, dramatic lighting, artistic photography",
                "lovers in bed, morning light, intimate atmosphere, artistic nude, soft focus",
            ],
            "dancing": [
                "couple dancing, elegant movement, beautiful dress, romantic atmosphere",
                "ballroom dance, passionate tango, dramatic lighting, stunning composition"
            ]
        }
        
        if '拥抱' in text_lower or 'hug' in text_lower:
            category = "romantic"
        elif '接吻' in text_lower or 'kiss' in text_lower:
            category = "passionate"
        elif '跳舞' in text_lower or 'dance' in text_lower:
            category = "dancing"
        else:
            category = "romantic"
        
        return alternatives.get(category, alternatives["romantic"])


class UnsafeContentDetector:
    """不安全内容检测器"""
    
    UNSAFE_KEYWORDS = [
        '阴茎', '阴道', '插入', '性交', '做爱', '操', '干', '肏',
        '射精', '高潮', '精液', '阴蒂', '口交', '肛交', '自慰',
        '手淫', '淫荡', '色情', '全裸', '一丝不挂',
        'penis', 'vagina', 'insert', 'intercourse', 'sexual', 'fuck',
        'sperm', 'ejaculate', 'orgasm', 'clitoris', 'oral sex',
        'anal sex', 'masturbate', 'porn', 'naked', 'nude',
        'hardcore', 'explicit', 'xxx', 'sex scene', 'sex',
    ]
    
    def detect(self, text: str) -> Tuple[bool, List[str]]:
        """检测不安全内容"""
        text_lower = text.lower()
        matched = [kw for kw in self.UNSAFE_KEYWORDS if kw in text_lower]
        return len(matched) > 0, matched
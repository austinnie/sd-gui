# gui/chat/utils/safety.py
"""安全/NSFW 工具"""


class SafetyChecker:
    """安全检查器"""
    
    UNSAFE_KEYWORDS = [
        '阴茎', '阴道', '插入', '性交', '做爱', '操', '干', '肏',
        '射精', '高潮', '精液', '阴蒂', '口交', '肛交', '自慰',
        '手淫', '淫荡', '色情', '全裸', '一丝不挂',
        'penis', 'vagina', 'insert', 'intercourse', 'sexual', 'fuck',
        'sperm', 'ejaculate', 'orgasm', 'clitoris', 'oral sex',
        'anal sex', 'masturbate', 'porn', 'naked', 'nude',
        'hardcore', 'explicit', 'xxx', 'sex scene', 'sex',
    ]
    
    @staticmethod
    def check_unsafe_content(text: str) -> tuple:
        """检查不安全内容"""
        text_lower = text.lower()
        matched = [kw for kw in SafetyChecker.UNSAFE_KEYWORDS if kw in text_lower]
        return len(matched) > 0, matched
    
    @staticmethod
    def get_safe_alternatives(text: str) -> list:
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
# gui/chat/context_manager.py
"""对话上下文管理器"""

from typing import Dict, List, Optional
from datetime import datetime


class ContextManager:
    """对话上下文管理器"""
    
    def __init__(self):
        self.conversation_history: List[Dict] = []
        self.user_preferences: Dict = {
            "style": None,
            "scene": None,
            "gender": None,
            "quality": "high",
        }
        self.last_prompt: Optional[str] = None
        self.last_intent_type: Optional[str] = None
        self.last_generated_image: Optional[str] = None
    
    def update(self, intent: Dict, result: Dict = None):
        """更新上下文"""
        self.last_intent_type = intent.get("type")
        self.last_prompt = intent.get("prompt")
        
        if result and result.get("image_path"):
            self.last_generated_image = result.get("image_path")
        
        keywords = intent.get("keywords", {})
        if keywords.get("styles"):
            self.user_preferences["style"] = keywords["styles"][0]
        if keywords.get("scenes"):
            self.user_preferences["scene"] = keywords["scenes"][0]
        if keywords.get("genders"):
            gender = keywords["genders"][0]
            self.user_preferences["gender"] = "女性" if "girl" in gender else "男性"
        
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "intent": intent,
            "result": result
        })
    
    def get_summary(self) -> str:
        """获取上下文摘要"""
        if not self.conversation_history:
            return ""
        
        summary_parts = []
        
        prefs = []
        if self.user_preferences.get("style"):
            prefs.append(f"风格偏好: {self.user_preferences['style']}")
        if self.user_preferences.get("scene"):
            prefs.append(f"场景偏好: {self.user_preferences['scene']}")
        if self.user_preferences.get("gender"):
            prefs.append(f"性别偏好: {self.user_preferences['gender']}")
        
        if prefs:
            summary_parts.append("📌 用户偏好: " + ", ".join(prefs))
        
        if self.last_prompt:
            summary_parts.append(f"📝 上次提示词: {self.last_prompt[:50]}...")
        
        user_msgs = [m for m in self.conversation_history if m.get("intent", {}).get("original_text")]
        if user_msgs:
            summary_parts.append(f"💬 已对话 {len(user_msgs)} 轮")
        
        return "\n".join(summary_parts) if summary_parts else "无上下文"
    
    def has_context(self) -> bool:
        """是否有上下文"""
        return len(self.conversation_history) > 0 or self.last_prompt is not None
    
    def clear(self):
        """清空上下文"""
        self.conversation_history = []
        self.user_preferences = {"style": None, "scene": None, "gender": None, "quality": "high"}
        self.last_prompt = None
        self.last_intent_type = None
        self.last_generated_image = None
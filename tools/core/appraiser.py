# tools/core/appraiser.py
"""AI 鉴赏系统"""

import os
import sys
import requests

CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from tools.config import AI_APPRECIATION_ENGINE


class Appraiser:
    """AI 鉴赏器"""
    
    def __init__(self):
        self._blip_processor = None
        self._blip_model = None
        self._blip_loaded = False
    
    def appraise(self, image_path: str, prompt: str) -> str:
        """
        对图片进行鉴赏
        返回鉴赏文字
        """
        engine = AI_APPRECIATION_ENGINE
        
        if engine == "prompt":
            print(f"   📝 鉴赏引擎: 仅使用提示词")
            return prompt
        
        # 加载 BLIP
        self._ensure_blip_loaded()
        
        # 获取 BLIP 描述
        caption = self._get_blip_caption(image_path)
        if not caption:
            caption = prompt
        
        # LLM 增强
        if engine == "llm" and self._llm_available():
            enhanced = self._enhance_with_llm(caption)
            if enhanced:
                return enhanced
        
        return caption
    
    def _ensure_blip_loaded(self):
        """确保 BLIP 模型已加载"""
        if self._blip_loaded:
            return
        
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
            
            base_blip_path = r"E:\hf_cache\.cache\hub\models--Salesforce--blip-image-captioning-large"
            snapshots_path = os.path.join(base_blip_path, "snapshots")
            
            if os.path.exists(snapshots_path):
                subfolders = [f for f in os.listdir(snapshots_path) 
                             if os.path.isdir(os.path.join(snapshots_path, f))]
                if subfolders:
                    cached_dir = os.path.join(snapshots_path, subfolders[0])
                    print(f"   📦 加载 BLIP 模型 ({cached_dir})...")
                    self._blip_processor = BlipProcessor.from_pretrained(cached_dir)
                    self._blip_model = BlipForConditionalGeneration.from_pretrained(cached_dir)
                    self._blip_loaded = True
                    print(f"   ✅ BLIP 模型加载完成")
                    return
            
            print(f"   ⚠️ 本地 BLIP 加载失败")
            self._blip_loaded = False
            
        except Exception as e:
            print(f"   ⚠️ BLIP 加载失败: {e}")
            self._blip_loaded = False
    
    def _get_blip_caption(self, image_path: str) -> str:
        """获取 BLIP 描述"""
        if not self._blip_loaded or self._blip_model is None:
            return None
        
        try:
            from PIL import Image
            image = Image.open(image_path).convert('RGB')
            inputs = self._blip_processor(image, return_tensors="pt")
            out = self._blip_model.generate(**inputs, max_length=80, num_beams=3, repetition_penalty=1.1)
            caption = self._blip_processor.decode(out[0], skip_special_tokens=True)
            print(f"   📝 BLIP 基础描述: {caption[:60]}...")
            return caption
        except Exception as e:
            print(f"   ⚠️ BLIP 推理失败: {e}")
            return None
    
    def _llm_available(self) -> bool:
        """检查 LLM 是否可用"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def _enhance_with_llm(self, caption: str) -> str:
        """使用 LLM 增强描述"""
        try:
            llm_prompt = f"""
请将以下图片描述转换为一段优美、带有艺术鉴赏性的中文赏析（约100字）：
图片描述：{caption}

要求：
1. 包含对人物服装、神态、材质质感的描写。
2. 强调这是一件极具收藏价值的作品。
3. 语言风格：优雅、专业、适合作为社交媒体发帖文案。
"""
            print(f"   ⏳ 正在请求 Ollama 润色...")
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "qwen2.5:1.5b", "prompt": llm_prompt, "stream": False},
                timeout=45
            )
            if response.status_code == 200:
                result = response.json().get("response", caption)
                print(f"   ✅ LLM 润色完成！")
                return result
        except Exception as e:
            print(f"   ⚠️ Ollama 连接失败: {e}")
        return None


# 全局实例
appraiser = Appraiser()
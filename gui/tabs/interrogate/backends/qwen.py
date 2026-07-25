# gui/tabs/interrogate/backends/qwen.py
"""Qwen-VL 反推后端"""

import torch
from PIL import Image
from .base import InterrogateBackend

_qwen_model = None
_qwen_processor = None


class QwenBackend(InterrogateBackend):
    """Qwen-VL 详细描述模式"""
    
    def interrogate(self, image_path: str, **kwargs) -> str:
        global _qwen_model, _qwen_processor
        
        if self.tab.cancel_interrogate:
            return "已取消"
        
        if _qwen_model is None:
            try:
                from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
                model_name = "Qwen/Qwen2-VL-2B-Instruct"
                _qwen_processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
                _qwen_model = Qwen2VLForConditionalGeneration.from_pretrained(
                    model_name, device_map="cpu", torch_dtype=torch.float16
                )
            except Exception as e:
                return f"Qwen-VL 加载失败: {e}"
        
        image = Image.open(image_path).convert('RGB')
        if max(image.size) > 1024:
            image.thumbnail((1024, 1024))
        
        if self.tab.cancel_interrogate:
            return "已取消"
        
        messages = [{
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": "请详细描述这张图片中的人物，包括：性别、年龄、发型、发色、脸型、五官特征、服装、表情、背景、光线、氛围。用中文回答。"}
            ]
        }]
        
        inputs = _qwen_processor(
            text=_qwen_processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True),
            images=image,
            return_tensors="pt"
        )
        
        with torch.no_grad():
            outputs = _qwen_model.generate(
                **inputs,
                max_new_tokens=300,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.1,
            )
        
        result = _qwen_processor.decode(outputs[0], skip_special_tokens=True)
        
        if "assistant" in result.lower():
            parts = result.lower().split("assistant")
            result = parts[-1].strip()
            if result.startswith(":"):
                result = result[1:].strip()
        
        return result
# core/janus/understand.py
"""
Janus-Pro 理解模式 - 图生文
"""

import os
import torch
from typing import Optional
from datetime import datetime
from PIL import Image


from utils.logger import get_logger

logger = get_logger(__name__)
class JanusUnderstand:
    """Janus-Pro 图片理解器 - 图生文"""
    
    def __init__(self):
        self._model = None
        self._processor = None
        self._tokenizer = None
        self._loaded = False
    
    def _log(self, msg: str):
        logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    
    def _ensure_loaded(self):
        if self._loaded:
            return
        from .loader import janus_loader
        if not janus_loader.is_loaded():
            janus_loader.load(model_name="1B")
        self._model = janus_loader.get_model()
        self._processor = janus_loader.get_processor()
        self._tokenizer = janus_loader.get_tokenizer()
        self._loaded = True
        self._log("✅ Janus 理解模式已就绪")
    
    def analyze(
        self,
        image_path: str,
        question: str = "请描述这张图片",
        temperature: float = 0.8,
        max_tokens: int = 512,
        progress_callback: Optional[callable] = None
    ) -> str:
        self._ensure_loaded()
        
        if self._model is None:
            return "❌ 模型未加载"
        
        if not os.path.exists(image_path):
            return f"❌ 图片不存在: {image_path}"
        
        self._log(f"🔍 分析: {os.path.basename(image_path)}")
        
        if progress_callback:
            progress_callback(0.1, "📖 加载图片...")
        
        try:
            from janus.utils.io import load_pil_images
            import torch
            
            image = Image.open(image_path).convert('RGB')
            
            conversation = [
                {
                    "role": "User",
                    "content": f"<image_placeholder>\n{question}",
                    "images": [image_path],
                },
                {"role": "Assistant", "content": ""},
            ]
            
            if progress_callback:
                progress_callback(0.3, "🔄 处理输入...")
            
            pil_images = load_pil_images(conversation)
            
            prepare_inputs = self._processor(
                conversations=conversation,
                images=pil_images,
                force_batchify=True
            )
            
            if hasattr(prepare_inputs, 'to'):
                prepare_inputs = prepare_inputs.to("cpu")
            
            if progress_callback:
                progress_callback(0.5, "🧠 推理中...")
            
            with torch.no_grad():
                inputs_embeds = self._model.prepare_inputs_embeds(**prepare_inputs)
                outputs = self._model.language_model.generate(
                    inputs_embeds=inputs_embeds,
                    attention_mask=prepare_inputs.attention_mask,
                    pad_token_id=self._tokenizer.eos_token_id,
                    bos_token_id=self._tokenizer.bos_token_id,
                    eos_token_id=self._tokenizer.eos_token_id,
                    max_new_tokens=max_tokens,
                    do_sample=(temperature > 0),
                    temperature=temperature if temperature > 0 else 1.0,
                    use_cache=True,
                )
            
            if progress_callback:
                progress_callback(0.8, "📝 解码输出...")
            
            answer = self._tokenizer.decode(
                outputs[0].cpu().tolist(),
                skip_special_tokens=True
            )
            
            print("=" * 60)
            logger.info(f"📝 分析结果:")
            print(answer)
            print("=" * 60)
    
            if progress_callback:
                progress_callback(1.0, "✅ 完成")
            
            return answer.strip()
            
        except Exception as e:
            self._log(f"❌ 分析失败: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ 分析失败: {str(e)}"
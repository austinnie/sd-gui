# core/janus/chat.py
"""
Janus-Pro 对话模式 - 文生文
"""

import torch
import time
from typing import Optional, Dict, Tuple
from datetime import datetime


from utils.logger import get_logger, info, warning, error, debug

logger = get_logger(__name__)
class JanusChat:
    """Janus-Pro 对话器 - 纯文本多轮对话"""
    
    def __init__(self):
        self._model = None
        self._processor = None
        self._tokenizer = None
        self._loaded = False
        self._history = []
    
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
        self._log("✅ Janus 对话模式已就绪")
    
    def clear_history(self):
        self._history = []
        self._log("🗑️ 对话历史已清空")
    
    def get_history(self) -> list:
        return self._history.copy()
    
    def chat(
        self,
        user_input: str,
        temperature: float = 0.7,
        max_new_tokens: int = 256,
        progress_callback: Optional[callable] = None,
        system_prompt: Optional[str] = None
    ) -> Tuple[str, Dict]:
        self._ensure_loaded()
        
        if self._model is None:
            return "❌ 模型未加载", {"error": "模型未加载"}
        
        start_time = time.time()
        
        if progress_callback:
            progress_callback(0.2, "🔄 准备对话...")
        
        conversation = []
        
        if system_prompt:
            conversation.append({"role": "User", "content": system_prompt, "images": []})
            conversation.append({"role": "Assistant", "content": "好的，我明白了。"})
        
        for msg in self._history:
            conversation.append({
                "role": "User" if msg["role"] == "user" else "Assistant",
                "content": msg["content"],
                "images": [],
            })
        
        conversation.append({"role": "User", "content": user_input, "images": []})
        conversation.append({"role": "Assistant", "content": ""})
        
        self._log(f"👤 用户: {user_input[:50]}...")
        
        if progress_callback:
            progress_callback(0.4, "🧠 推理中...")
        
        try:
            prepare_inputs = self._processor(
                conversations=conversation,
                images=[],
                force_batchify=True
            )
            
            if hasattr(prepare_inputs, 'to'):
                prepare_inputs = prepare_inputs.to("cpu")
            
            eos_token_id = getattr(self._tokenizer, 'eos_token_id', None)
            pad_token_id = getattr(self._tokenizer, 'pad_token_id', None)
            bos_token_id = getattr(self._tokenizer, 'bos_token_id', None)
            
            if pad_token_id is None:
                pad_token_id = eos_token_id
            if eos_token_id is None:
                eos_token_id = 2
                pad_token_id = 2
            
            with torch.no_grad():
                inputs_embeds = self._model.prepare_inputs_embeds(**prepare_inputs)
                outputs = self._model.language_model.generate(
                    inputs_embeds=inputs_embeds,
                    attention_mask=prepare_inputs.attention_mask,
                    pad_token_id=pad_token_id,
                    bos_token_id=bos_token_id,
                    eos_token_id=eos_token_id,
                    max_new_tokens=max_new_tokens,
                    do_sample=(temperature > 0),
                    temperature=temperature if temperature > 0 else 1.0,
                    repetition_penalty=1.15,
                    use_cache=True,
                )
            
            reply = self._tokenizer.decode(
                outputs[0].cpu().tolist(),
                skip_special_tokens=True
            )
            
            reply = reply.strip()
            for prefix in ["Assistant:", "助手:", "assistant:"]:
                if reply.startswith(prefix):
                    reply = reply[len(prefix):].strip()
            
            self._history.append({"role": "user", "content": user_input})
            self._history.append({"role": "assistant", "content": reply})
            
            elapsed = time.time() - start_time
            
            self._log(f"✅ 回复完成，耗时 {elapsed:.2f}s")
            self._log(f"📝 回复: {reply[:100]}...")
            
            if progress_callback:
                progress_callback(1.0, "✅ 完成")
            
            return reply, {
                "elapsed": elapsed,
                "history_length": len(self._history),
            }
            
        except Exception as e:
            self._log(f"❌ 对话失败: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ 错误: {str(e)}", {"error": str(e)}
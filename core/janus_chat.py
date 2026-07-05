# core/janus_chat.py
"""
Janus-Pro 对话模式 - 文生文
多轮对话，不涉及图片
"""

import torch
import time
from typing import Optional, Dict, List, Tuple
from datetime import datetime


class JanusChat:
    """Janus-Pro 对话器 - 纯文本多轮对话"""
    
    def __init__(self):
        self._model = None
        self._processor = None
        self._tokenizer = None
        self._loaded = False
        self._history = []  # 对话历史
    
    def _log(self, msg: str):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    
    def _ensure_loaded(self):
        """延迟加载模型"""
        if self._loaded:
            return
        
        from .janus_loader import janus_loader
        
        if not janus_loader.is_loaded():
            janus_loader.load(model_name="1B")
        
        self._model = janus_loader.get_model()
        self._processor = janus_loader.get_processor()
        self._tokenizer = janus_loader.get_tokenizer()
        
        self._loaded = True
        self._log("✅ Janus 对话模式已就绪")
    
    def clear_history(self):
        """清空对话历史"""
        self._history = []
        self._log("🗑️ 对话历史已清空")
    
    def chat(
        self,
        user_input: str,
        temperature: float = 0.8,
        max_new_tokens: int = 512,
        progress_callback: Optional[callable] = None,
        system_prompt: Optional[str] = None
    ) -> Tuple[str, Dict]:
        """
        多轮对话 - 纯文本
        
        参数:
            user_input: 用户输入
            temperature: 温度
            max_new_tokens: 最大生成 token 数
            progress_callback: 进度回调
            system_prompt: 系统提示词（可选）
        
        返回:
            (回复内容, 元数据)
        """
        self._ensure_loaded()
        
        if self._model is None:
            return "❌ 模型未加载", {"error": "模型未加载"}
        
        start_time = time.time()
        
        if progress_callback:
            progress_callback(0.2, "🔄 准备对话...")
        
        # ✅ 构建对话（纯文本，无图片）
        conversation = []
        
        # 系统提示词
        if system_prompt:
            conversation.append({
                "role": "User",
                "content": system_prompt,
                "images": [],
            })
            conversation.append({
                "role": "Assistant",
                "content": "好的，我明白了。",
            })
        
        # 添加历史
        for msg in self._history:
            conversation.append({
                "role": "User" if msg["role"] == "user" else "Assistant",
                "content": msg["content"],
                "images": [],
            })
        
        # 添加当前用户输入
        conversation.append({
            "role": "User",
            "content": user_input,
            "images": [],
        })
        conversation.append({
            "role": "Assistant",
            "content": "",
        })
        
        self._log(f"👤 用户: {user_input[:50]}...")
        
        if progress_callback:
            progress_callback(0.4, "🧠 推理中...")
        
        try:
            # ✅ 处理输入（纯文本，images=[]）
            prepare_inputs = self._processor(
                conversations=conversation,
                images=[],
                force_batchify=True
            )
            
            if hasattr(prepare_inputs, 'to'):
                prepare_inputs = prepare_inputs.to("cpu")
            
            # ✅ 获取 token IDs
            eos_token_id = getattr(self._tokenizer, 'eos_token_id', None)
            pad_token_id = getattr(self._tokenizer, 'pad_token_id', None)
            bos_token_id = getattr(self._tokenizer, 'bos_token_id', None)
            
            if pad_token_id is None:
                pad_token_id = eos_token_id
            if eos_token_id is None:
                eos_token_id = 2
                pad_token_id = 2
            
            # ✅ 生成
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
                    repetition_penalty=1.1,  # 🆕 添加重复惩罚，防止重复
                    use_cache=True,
                )
            
            # ✅ 解码
            reply = self._tokenizer.decode(
                outputs[0].cpu().tolist(),
                skip_special_tokens=True
            )
            
            # 清理回复
            reply = reply.strip()
            for prefix in ["Assistant:", "助手:", "assistant:"]:
                if reply.startswith(prefix):
                    reply = reply[len(prefix):].strip()
            
            # 保存历史
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
                "temperature": temperature,
                "max_new_tokens": max_new_tokens,
            }
            
        except Exception as e:
            self._log(f"❌ 对话失败: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ 错误: {str(e)}", {"error": str(e)}


# 全局实例 - 延迟加载
janus_chat = JanusChat()
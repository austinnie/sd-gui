# core/janus_analyzer.py
"""
Janus-Pro 图片分析器 - 延迟加载
只在第一次调用 analyze() 时才加载模型
"""

import sys
import os
from typing import Optional
from datetime import datetime

# 添加官方 janus-repo 到路径
JANUS_REPO_PATH = r"E:\SD_OpenVINO\models\janus\janus-repo"
if JANUS_REPO_PATH not in sys.path:
    sys.path.insert(0, JANUS_REPO_PATH)


class JanusAnalyzer:
    """Janus-Pro 图片分析器 - 延迟加载"""
    
    def __init__(self):
        self._vl_chat_processor = None
        self._vl_gpt = None
        self._tokenizer = None
        self._loaded = False
        self._load_error = None
    
    def _log(self, msg: str):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    
    def _ensure_loaded(self):
        """确保模型已加载 - 只在第一次调用时加载"""
        if self._loaded:
            return
        
        if self._load_error:
            raise RuntimeError(f"模型加载失败: {self._load_error}")
        
        self._log("📦 加载 Janus 官方模型...")
        
        try:
            import torch
            from transformers import AutoModelForCausalLM
            from janus.models import VLChatProcessor
            
            model_path = "deepseek-ai/Janus-1.3B"
            local_path = r"E:\SD_OpenVINO\models\janus\janus-pro-1b"
            if os.path.exists(local_path):
                model_path = local_path
            
            self._log(f"   模型路径: {model_path}")
            
            self._vl_chat_processor = VLChatProcessor.from_pretrained(model_path)
            self._tokenizer = self._vl_chat_processor.tokenizer
            self._log("   ✅ Processor 加载完成")
            
            self._vl_gpt = AutoModelForCausalLM.from_pretrained(
                model_path,
                trust_remote_code=True,
                torch_dtype=torch.bfloat16,
            )
            self._vl_gpt = self._vl_gpt.to(torch.bfloat16).to("cpu").eval()
            
            self._loaded = True
            self._log("✅ Janus 官方模型加载完成")
            
        except Exception as e:
            self._log(f"❌ 加载失败: {e}")
            import traceback
            traceback.print_exc()
            self._load_error = str(e)
            raise RuntimeError(f"模型加载失败: {e}")
    
    def analyze(
        self,
        image_path: str,
        question: str,
        temperature: float = 0.8,
        max_tokens: int = 512,
        progress_callback: Optional[callable] = None
    ) -> str:
        """分析图片 - 首次调用时自动加载模型"""
        self._ensure_loaded()
        
        self._log(f"🔍 开始分析: {image_path}")
        self._log(f"📝 问题: {question[:50]}...")
        
        if progress_callback:
            progress_callback(0.1, "📖 加载图片...")
        
        try:
            from janus.utils.io import load_pil_images
            import torch
            
            conversation = [
                {
                    "role": "User",
                    "content": f"<image_placeholder>\n{question}",
                    "images": [image_path],
                },
                {"role": "Assistant", "content": ""},
            ]
            
            self._log("   📖 加载图片...")
            if progress_callback:
                progress_callback(0.3, "🔄 处理输入...")
            
            pil_images = load_pil_images(conversation)
            self._log(f"   ✅ 图片加载完成: {len(pil_images)} 张")
            
            self._log("   🔄 处理输入...")
            prepare_inputs = self._vl_chat_processor(
                conversations=conversation,
                images=pil_images,
                force_batchify=True
            )
            
            if hasattr(prepare_inputs, 'to'):
                prepare_inputs = prepare_inputs.to("cpu")
            
            self._log("   ✅ 输入处理完成")
            
            if progress_callback:
                progress_callback(0.5, "🧠 推理中...")
            
            self._log("   🧠 推理中...")
            with torch.no_grad():
                inputs_embeds = self._vl_gpt.prepare_inputs_embeds(**prepare_inputs)
                
                outputs = self._vl_gpt.language_model.generate(
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
            
            self._log("   ✅ 推理完成")
            
            if progress_callback:
                progress_callback(0.8, "📝 解码输出...")
            
            self._log("   📝 解码输出...")
            generated_tokens = outputs[0].cpu().numpy().tolist()
            answer = self._tokenizer.decode(generated_tokens, skip_special_tokens=True)
            
            self._log(f"   ✅ 解码完成，长度: {len(answer)} 字符")
            self._log(f"📝 结果: {answer[:200]}...")
            
            if progress_callback:
                progress_callback(1.0, "✅ 完成")
            
            return answer
            
        except Exception as e:
            self._log(f"❌ 分析失败: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ 分析失败: {str(e)}"


# 全局实例 - 延迟加载，导入时不加载模型
janus_analyzer = JanusAnalyzer()
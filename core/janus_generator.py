# core/janus_generator.py
"""
Janus-Pro 生成模式 - 文生图

⚠️ 注意: Janus 是多模态理解模型，文生图功能非常有限。
建议使用 SD 文生图获得更好效果。
"""

import torch
import time
from typing import Optional, Tuple, Dict
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont


class JanusGenerator:
    """Janus-Pro 文生图（功能有限）"""
    
    def __init__(self):
        self._model = None
        self._processor = None
        self._tokenizer = None
        self._loaded = False
    
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
        self._log("✅ Janus 生成模式已就绪")
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.8,
        max_new_tokens: int = 2048,
        seed: Optional[int] = None,
        negative_prompt: str = "",
        progress_callback: Optional[callable] = None,
        **kwargs
    ) -> Tuple[Image.Image, Dict]:
        """
        文生图 - 功能有限
        
        ⚠️ Janus 是理解模型，文生图质量一般
        建议使用 SD 文生图获得更好效果
        """
        self._ensure_loaded()
        
        if self._model is None:
            return self._create_error_image("模型未加载"), {"error": "模型未加载"}
        
        if seed is not None:
            torch.manual_seed(seed)
        
        full_prompt = self._build_prompt(prompt, negative_prompt)
        start_time = time.time()
        
        if progress_callback:
            progress_callback(0.2, "🔄 准备生成...")
        
        self._log(f"📝 提示词: {full_prompt[:80]}...")
        
        # 构建对话（文生图格式 - 无图片）
        conversation = [
            {
                "role": "User",
                "content": full_prompt,
                "images": [],
            },
            {"role": "Assistant", "content": ""},
        ]
        
        try:
            # 处理输入
            prepare_inputs = self._processor(
                conversations=conversation,
                images=[],
                force_batchify=True
            )
            
            if hasattr(prepare_inputs, 'to'):
                prepare_inputs = prepare_inputs.to("cpu")
            
            self._log("✅ 输入处理完成")
            
        except Exception as e:
            self._log(f"⚠️ 处理失败: {e}")
            # 备选：使用 tokenizer
            try:
                text = f"<|User|>{full_prompt}<|Assistant|>"
                inputs = self._tokenizer(
                    text,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=512
                )
                prepare_inputs = inputs.to("cpu")
                self._log("✅ 使用 tokenizer 备选方案")
            except Exception as e2:
                self._log(f"❌ 所有输入处理失败: {e2}")
                return self._create_error_image(str(e2)), {"error": str(e2), "elapsed": time.time() - start_time}
        
        if progress_callback:
            progress_callback(0.4, "🧠 推理中...")
        
        # 获取 token IDs
        eos_token_id = getattr(self._tokenizer, 'eos_token_id', None)
        pad_token_id = getattr(self._tokenizer, 'pad_token_id', None)
        bos_token_id = getattr(self._tokenizer, 'bos_token_id', None)
        
        if pad_token_id is None:
            pad_token_id = eos_token_id
        if eos_token_id is None:
            eos_token_id = 2
            pad_token_id = 2
        
        try:
            # 生成
            with torch.no_grad():
                if hasattr(self._model, 'prepare_inputs_embeds'):
                    inputs_embeds = self._model.prepare_inputs_embeds(**prepare_inputs)
                    
                    if hasattr(self._model, 'language_model'):
                        outputs = self._model.language_model.generate(
                            inputs_embeds=inputs_embeds,
                            attention_mask=prepare_inputs.attention_mask,
                            do_sample=(temperature > 0),
                            temperature=temperature if temperature > 0 else 1.0,
                            max_new_tokens=max_new_tokens,
                            pad_token_id=pad_token_id,
                            bos_token_id=bos_token_id,
                            eos_token_id=eos_token_id,
                            use_cache=True,
                            **kwargs
                        )
                    else:
                        raise RuntimeError("模型没有 language_model 属性")
                else:
                    outputs = self._model.generate(
                        **prepare_inputs,
                        do_sample=(temperature > 0),
                        temperature=temperature if temperature > 0 else 1.0,
                        max_new_tokens=max_new_tokens,
                        pad_token_id=pad_token_id,
                        bos_token_id=bos_token_id,
                        eos_token_id=eos_token_id,
                        use_cache=True,
                        **kwargs
                    )
            
            if progress_callback:
                progress_callback(0.8, "🎨 解码输出...")
            
            # 解码
            answer = self._tokenizer.decode(
                outputs[0].cpu().tolist(),
                skip_special_tokens=True
            )
            
            self._log(f"📝 输出长度: {len(answer)} 字符")
            self._log(f"📝 输出预览: {answer[:200]}...")
            
            # 创建包含文本的图片
            image = self._create_text_image(answer, full_prompt)
            
        except Exception as e:
            self._log(f"❌ 生成失败: {e}")
            import traceback
            traceback.print_exc()
            return self._create_error_image(str(e)), {"error": str(e), "elapsed": time.time() - start_time}
        
        elapsed = time.time() - start_time
        
        metadata = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "temperature": temperature,
            "max_new_tokens": max_new_tokens,
            "seed": seed,
            "elapsed": elapsed,
            "model": "Janus-Pro",
            "device": "cpu",
            "output_text": answer if 'answer' in locals() else "",
            "note": "Janus 文生图功能有限，建议使用 SD 文生图"
        }
        
        self._log(f"✅ 生成完成，耗时 {elapsed:.2f} 秒")
        
        if progress_callback:
            progress_callback(1.0, "✅ 生成完成")
        
        return image, metadata
    
    def _build_prompt(self, positive: str, negative: str) -> str:
        if negative:
            return f"{positive}, avoid: {negative}"
        return positive
    
    def _create_text_image(self, answer: str, prompt: str = "") -> Image.Image:
        """创建包含文本的图片"""
        lines = answer.split('\n')
        line_count = max(1, len(lines))
        height = min(800, max(400, line_count * 22 + 80))
        width = 768
        
        img = Image.new('RGB', (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = ImageFont.load_default()
        
        # 提示框
        draw.rectangle([(0, 0), (width, 35)], fill=(50, 50, 150))
        draw.text((10, 8), "🤖 Janus-Pro 生成结果", fill=(255, 255, 255), font=font)
        
        # ⚠️ 提示
        draw.text((10, 42), "⚠️ Janus 文生图功能有限，建议使用 SD 文生图", fill=(200, 100, 0), font=font)
        
        prompt_display = prompt[:80] + "..." if len(prompt) > 80 else prompt
        draw.text((10, 62), f"📝 提示词: {prompt_display}", fill=(100, 100, 100), font=font)
        
        draw.line([(10, 82), (width-10, 82)], fill=(200, 200, 200), width=1)
        
        y = 92
        for line in lines[:40]:
            if len(line) > 75:
                words = line.split()
                current = ""
                for word in words:
                    if len(current) + len(word) < 75:
                        current += word + " "
                    else:
                        draw.text((10, y), current, fill=(0, 0, 0), font=font)
                        y += 20
                        current = word + " "
                if current:
                    draw.text((10, y), current, fill=(0, 0, 0), font=font)
                    y += 20
            else:
                draw.text((10, y), line, fill=(0, 0, 0), font=font)
                y += 20
            
            if y > height - 40:
                break
        
        draw.text((10, height-20), "💡 建议使用 Stable Diffusion 文生图获得更好效果", fill=(150, 150, 150), font=font)
        
        return img
    
    def _create_error_image(self, error_msg: str) -> Image.Image:
        """创建错误提示图片"""
        img = Image.new('RGB', (512, 256), color=(255, 220, 220))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        draw.text((20, 80), "❌ 生成失败", fill=(200, 0, 0), font=font)
        draw.text((20, 120), error_msg[:60], fill=(100, 0, 0), font=font)
        draw.text((20, 160), "建议使用 SD 文生图", fill=(100, 100, 100), font=font)
        
        return img


# 全局实例 - 延迟加载
janus_generator = JanusGenerator()
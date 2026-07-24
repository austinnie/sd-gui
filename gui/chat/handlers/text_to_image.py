# gui/chat/handlers/text_to_image.py
"""文生图处理器"""

import os
import tempfile
from datetime import datetime
from PIL import Image

from .base_handler import BaseHandler


class TextToImageHandler(BaseHandler):
    """文生图处理器"""
    
    def handle(self, intent):
        """处理文生图"""
        if self.tab._is_loading_model:
            self._append_message("assistant", "⏳ 模型正在加载中，请稍候...")
            return

        if not self.app.model_manager.is_sd_loaded:
            self._append_message("assistant", "📦 正在自动加载模型...")
            self.tab._pending_intent = intent
            if not self.tab._ensure_model_loaded():
                return
            self._append_message("assistant", "⏳ 模型加载中，请稍候再试...")
            return

        # 获取提示词
        if intent.llm_enhanced:
            prompt = intent.prompt
            negative = intent.negative or self.negative_templates["default"]
            prompt = self._clean_prompt_for_sd(prompt)
        else:
            prompt = intent.prompt or ""
            negative = intent.negative or self.negative_templates["default"]
            if intent.is_continuation and self.context_manager.last_prompt:
                prompt = self._enhance_with_context(prompt)

        prompt = self._clean_prompt_for_sd(prompt)

        print("\n" + "=" * 60)
        print(f"📊 [文生图] 提示词: {prompt}")
        print("=" * 60 + "\n")

        params = self._estimate_params(prompt)
        self._update_status(f"🎨 生成中... (尺寸: {params['width']}x{params['height']})", 0.1)

        try:
            pipe, model_path, lora_path, task_id = self._get_pipeline(f"txt_{datetime.now().strftime('%H%M%S')}")
            
            if pipe is None:
                self._append_message("assistant", "❌ 无法获取 Pipeline")
                return

            seed = self._get_seed()
            generator = self._get_generator(seed)

            result = pipe(
                prompt=prompt,
                negative_prompt=negative,
                num_inference_steps=params["steps"],
                guidance_scale=params["cfg"],
                height=params["height"],
                width=params["width"],
                generator=generator,
                num_images_per_prompt=1
            )

            filepath = self._save_image(result.images[0], prompt)
            self._release_pipeline(model_path, lora_path, task_id)

            self._append_message("assistant", f"✅ 图片已生成！\n📁 {os.path.basename(filepath)}")
            self._update_status("✅ 生成完成", 1.0)

            # 更新上下文
            self.context_manager.update(vars(intent), {"image_path": filepath, "prompt": prompt})

        except Exception as e:
            self._append_message("assistant", f"❌ 生成失败: {str(e)}")
            self._update_status("❌ 生成失败", 0)
            import traceback
            traceback.print_exc()
            self.tab._pending_intent = None

    def _estimate_params(self, prompt: str) -> dict:
        """估算参数"""
        prompt_lower = prompt.lower()

        is_portrait = any(k in prompt_lower for k in ['portrait', 'headshot', 'close up', 'face', '头像', '特写'])
        is_full_body = any(k in prompt_lower for k in ['full body', 'standing', '全身', '站立'])
        is_landscape = any(k in prompt_lower for k in ['landscape', 'scenery', '风景', '山水'])
        is_couple = any(k in prompt_lower for k in ['couple', 'two people', '双人', '情侣'])

        if is_portrait:
            width, height = 512, 640
        elif is_full_body:
            width, height = 512, 768
        elif is_landscape:
            width, height = 896, 512
        elif is_couple:
            width, height = 640, 896
        else:
            width, height = 512, 768

        steps = self.tab.chat_steps_var.get()
        cfg = self.tab.chat_cfg_var.get()

        return {"width": width, "height": height, "steps": steps, "cfg": cfg}

    def _enhance_with_context(self, prompt: str) -> str:
        """使用上下文增强提示词"""
        if not self.context_manager.last_prompt:
            return prompt
        if len(prompt.split(',')) < 3:
            parts = self.context_manager.last_prompt.split(',')
            subject_tag = parts[0] if parts else "1girl"
            return f"{subject_tag}, {prompt}"
        return prompt
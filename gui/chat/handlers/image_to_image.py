# gui/chat/handlers/image_to_image.py
"""图生图处理器"""

import random
from datetime import datetime
from PIL import Image

from .base_handler import BaseHandler


from utils.logger import get_logger

logger = get_logger(__name__)
class ImageToImageHandler(BaseHandler):
    """图生图处理器"""
    
    def handle(self, intent):
        """处理图生图"""
        if self.tab.uploaded_image is None:
            self._append_message("assistant", "❌ 请先上传一张图片")
            return

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

        prompt = intent.prompt
        image_features = self._analyze_image_features(self.tab.uploaded_image_path)

        params = intent.params or self._optimize_parameters(prompt, image_features)

        # 检查 ControlNet
        use_controlnet = self.tab.controlnet_manager.controlnet_enabled
        if use_controlnet and self.tab.controlnet_manager.is_available:
            control_image = self._get_control_image()
            if control_image:
                self._handle_controlnet(prompt, control_image, intent, params)
                return

        self._do_image_to_image(prompt, intent, params, image_features)

    def _do_image_to_image(self, prompt, intent, params, image_features):
        """执行图生图"""
        try:
            pipe, model_path, lora_path, task_id = self._get_pipeline(f"img_{datetime.now().strftime('%H%M%S')}")
            
            if pipe is None:
                self._append_message("assistant", "❌ 无法获取 Pipeline")
                return

            init_image = self.tab.uploaded_image.copy().convert('RGB')
            w, h = init_image.size

            new_w = ((w + 31) // 64) * 64
            new_h = ((h + 31) // 64) * 64
            if new_w != w or new_h != h:
                init_image = init_image.resize((new_w, new_h))

            max_size = 1024
            if max(new_w, new_h) > max_size:
                scale = max_size / max(new_w, new_h)
                new_w = int(new_w * scale)
                new_h = int(new_h * scale)
                new_w = ((new_w + 31) // 64) * 64
                new_h = ((new_h + 31) // 64) * 64
                init_image = init_image.resize((new_w, new_h))

            preserve_parts = self.prompt_builder.build_preserve_parts(image_features, intent.original_text)
            full_prompt = self.prompt_builder.merge_with_features(prompt, preserve_parts)

            seed = self._get_seed()
            generator = self._get_generator(seed)
            negative = self.tab._last_negative or self.negative_templates["default"]

            result = pipe(
                prompt=full_prompt,
                negative_prompt=negative,
                image=init_image,
                strength=params.get("strength", 0.35),
                num_inference_steps=params["steps"],
                guidance_scale=params["cfg"],
                generator=generator,
                num_images_per_prompt=1
            )

            filepath = self._save_image(result.images[0], prompt, "edit")
            self._release_pipeline(model_path, lora_path, task_id)

            self._append_message("assistant", f"✅ 图片已修改完成！\n📁 {os.path.basename(filepath)}")
            self._update_status("✅ 修改完成", 1.0)
            self.context_manager.update(vars(intent), {"image_path": filepath, "prompt": prompt})

        except Exception as e:
            self._append_message("assistant", f"❌ 修改失败: {str(e)}")
            self._update_status("❌ 修改失败", 0)
            import traceback
            traceback.print_exc()

    def _handle_controlnet(self, prompt, control_image, intent, params):
        """ControlNet 生成"""
        try:
            if self.tab.controlnet_pipe is None:
                self.tab.controlnet_manager.setup()
                if not self.tab.controlnet_manager.is_available:
                    self._do_image_to_image(prompt, intent, params, {})
                    return

            pipe = self.tab.controlnet_pipe
            init_image = Image.open(self.tab.uploaded_image_path).convert('RGB')
            w, h = init_image.size
            new_w = ((w + 31) // 64) * 64
            new_h = ((h + 31) // 64) * 64
            if new_w != w or new_h != h:
                init_image = init_image.resize((new_w, new_h), Image.Resampling.LANCZOS)

            max_size = 1024
            if max(new_w, new_h) > max_size:
                scale = max_size / max(new_w, new_h)
                new_w = int(new_w * scale)
                new_h = int(new_h * scale)
                new_w = ((new_w + 31) // 64) * 64
                new_h = ((new_h + 31) // 64) * 64
                init_image = init_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
                control_image = control_image.resize((new_w, new_h), Image.Resampling.LANCZOS)

            seed = self._get_seed()
            generator = self._get_generator(seed)

            result = pipe(
                prompt=prompt,
                negative_prompt=self.negative_templates["default"],
                image=init_image,
                control_image=control_image,
                strength=params.get("strength", 0.4),
                num_inference_steps=params["steps"],
                guidance_scale=params["cfg"],
                generator=generator,
                controlnet_conditioning_scale=0.80,
                num_images_per_prompt=1,
            )

            filepath = self._save_image(result.images[0], prompt, "controlnet")
            self._append_message("assistant", f"✅ ControlNet 生成完成！\n📁 {os.path.basename(filepath)}")
            self._update_status("✅ 生成完成", 1.0)
            self.context_manager.update(vars(intent), {"image_path": filepath, "prompt": prompt})

        except Exception as e:
            self._append_message("assistant", f"❌ ControlNet 生成失败: {str(e)}")
            self._do_image_to_image(prompt, intent, params, {})

    def _get_control_image(self):
        """获取控制图"""
        from utils.controlnet import preprocess_image_for_controlnet
        
        selected = self.tab.controlnet_type_var.get()
        controlnet_type = selected.split(" ")[0] if " " in selected else "openpose"
        
        return preprocess_image_for_controlnet(
            self.tab.uploaded_image_path,
            controlnet_type=controlnet_type,
            output_size=(512, 512)
        )

    def _analyze_image_features(self, image_path: str) -> dict:
        """分析图片特征"""
        try:
            import cv2
            import numpy as np

            img = cv2.imread(image_path)
            if img is None:
                return {}

            h, w = img.shape[:2]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=8, minSize=(30, 30))
            valid_faces = [(x, y, fw, fh) for (x, y, fw, fh) in faces if fw > 40 and fh > 40]

            is_full_body = True
            if valid_faces:
                x, y, fw, fh = max(valid_faces, key=lambda f: f[2] * f[3])
                face_ratio = (fw * fh) / (w * h)
                if face_ratio > 0.15:
                    is_full_body = False

            brightness = np.mean(gray)

            return {
                "has_face": len(valid_faces) > 0,
                "face_count": len(valid_faces),
                "is_full_body": is_full_body,
                "is_portrait": not is_full_body and len(valid_faces) > 0,
                "is_landscape": w > h * 1.2,
                "width": w,
                "height": h,
                "is_bright": brightness > 150,
                "is_dark": brightness < 80,
                "aspect_ratio": w / h,
                "is_realistic": True,
            }
        except Exception as e:
            logger.info(f"⚠️ 分析图片失败: {e}")
            return {}

    def _optimize_parameters(self, prompt: str, image_features: dict = None) -> dict:
        """优化参数"""
        prompt_lower = prompt.lower()
        params = {}

        if any(k in prompt_lower for k in ['快速', '快', 'quick', 'fast']):
            params["steps"] = 8
        elif any(k in prompt_lower for k in ['高质量', 'high quality', 'masterpiece']):
            params["steps"] = 30
        else:
            params["steps"] = 12

        if any(k in prompt_lower for k in ['写实', 'realistic']):
            params["cfg"] = 8.0
        elif any(k in prompt_lower for k in ['动漫', 'anime']):
            params["cfg"] = 6.5
        else:
            params["cfg"] = 7.5

        if any(k in prompt_lower for k in ['微调', 'slight']):
            params["strength"] = 0.25
        elif any(k in prompt_lower for k in ['大幅', 'major']):
            params["strength"] = 0.55
        else:
            params["strength"] = 0.40

        if image_features and image_features.get("has_face"):
            params["strength"] = min(params["strength"], 0.35)

        return params
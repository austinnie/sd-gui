# gui/chat/handlers/couple_handler.py
"""双人合成处理器"""

import random
import cv2
import numpy as np
from datetime import datetime
from PIL import Image

from .base_handler import BaseHandler


from utils.logger import get_logger

logger = get_logger(__name__)
class CoupleHandler(BaseHandler):
    """双人合成处理器"""
    
    def handle(self, intent):
        """处理双人合成"""
        if len(self.tab.uploaded_images) < 2:
            self._append_message("assistant", "❌ 请上传两张图片（一男一女）")
            return

        self._append_message("system", "👫 正在合成双人图片...")

        try:
            prompt = intent.prompt
            action = getattr(intent, 'action', 'standing together')

            pose_image = self._extract_couple_pose(
                self.tab.uploaded_image_paths[0],
                self.tab.uploaded_image_paths[1]
            )

            if pose_image:
                self._append_message("system", "🦴 已提取双人姿态图")
                params = intent.params or {}
                # 使用图生图处理器的 ControlNet 方法
                from .image_to_image import ImageToImageHandler
                handler = ImageToImageHandler(self.tab)
                handler._handle_controlnet(prompt, pose_image, intent, params)
            else:
                self._append_message("system", "⚠️ 姿态提取失败，使用普通图生图")
                self._handle_couple_img2img(intent)

        except Exception as e:
            self._append_message("assistant", f"❌ 双人合成失败: {str(e)}")
            import traceback
            traceback.print_exc()

    def _extract_couple_pose(self, img1_path: str, img2_path: str):
        """提取双人姿态"""
        try:
            try:
                from controlnet_aux import OpenPoseDetector
                detector = OpenPoseDetector.from_pretrained("lllyasviel/ControlNet")

                img1 = cv2.imread(img1_path)
                img2 = cv2.imread(img2_path)

                pose1 = detector(img1, output_type="pil")
                pose2 = detector(img2, output_type="pil")

                return self._merge_pose_images(pose1, pose2)

            except ImportError:
                logger.info(f"   ⚠️ controlnet_aux 未安装，使用备用方案")

            # 备用方案：Canny 边缘检测
            img1 = cv2.imread(img1_path)
            img2 = cv2.imread(img2_path)

            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

            edges1 = cv2.Canny(gray1, 50, 150)
            edges2 = cv2.Canny(gray2, 50, 150)

            combined = np.hstack([edges1, edges2])
            return Image.fromarray(combined)

        except Exception as e:
            logger.info(f"⚠️ 双人姿态提取失败: {e}")
            return None

    def _merge_pose_images(self, pose1, pose2):
        """合并姿态图"""
        w1, h1 = pose1.size
        w2, h2 = pose2.size

        if h1 != h2:
            if h1 > h2:
                pose2 = pose2.resize((int(w2 * h1 / h2), h1))
            else:
                pose1 = pose1.resize((int(w1 * h2 / h1), h2))

        combined = Image.new('RGB', (pose1.width + pose2.width, pose1.height))
        combined.paste(pose1, (0, 0))
        combined.paste(pose2, (pose1.width, 0))

        return combined

    def _handle_couple_img2img(self, intent):
        """双人图生图"""
        try:
            pipe, model_path, lora_path, task_id = self._get_pipeline(f"couple_{datetime.now().strftime('%H%M%S')}")
            
            if pipe is None:
                self._append_message("assistant", "❌ 无法获取 Pipeline")
                return

            img1 = self.tab.uploaded_images[0].convert('RGB')
            img2 = self.tab.uploaded_images[1].convert('RGB')

            h1, w1 = img1.size
            h2, w2 = img2.size
            target_h = min(h1, h2, 512)

            img1 = img1.resize((int(w1 * target_h / h1), target_h))
            img2 = img2.resize((int(w2 * target_h / h2), target_h))

            combined = Image.new('RGB', (img1.width + img2.width, target_h))
            combined.paste(img1, (0, 0))
            combined.paste(img2, (img1.width, 0))

            prompt = intent.prompt
            params = intent.params or {}

            seed = self._get_seed()
            generator = self._get_generator(seed)

            result = pipe(
                prompt=prompt,
                negative_prompt=self.negative_templates["default"],
                image=combined,
                strength=0.5,
                num_inference_steps=params.get("steps", 20),
                guidance_scale=params.get("cfg", 7.5),
                generator=generator,
                num_images_per_prompt=1
            )

            filepath = self._save_image(result.images[0], prompt, "couple")
            self._release_pipeline(model_path, lora_path, task_id)

            self._append_message("assistant", f"✅ 双人合成完成！\n📁 {os.path.basename(filepath)}")

        except Exception as e:
            self._append_message("assistant", f"❌ 双人合成失败: {str(e)}")
            import traceback
            traceback.print_exc()
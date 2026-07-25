#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
水印去除工具 - 组合多种方法去除图片水印
支持: 负面提示词强化 | OpenCV后处理 | 深度学习检测
"""

import os
import cv2
import numpy as np
from PIL import Image
import torch
from typing import Optional, Tuple, List


from utils.logger import get_logger

logger = get_logger(__name__)
class WatermarkRemover:
    """水印去除器 - 组合多种方法"""
    
    def __init__(self):
        self.methods = {
            "negative_prompt": self._enhance_negative_prompt,
            "opencv_inpaint": self._remove_with_inpaint,
            "opencv_blur": self._remove_with_blur,
            "ai_detection": self._remove_with_ai,
        }
        self._ai_model = None
    
    # ==================== 方法1: 负面提示词强化 ====================
    def _enhance_negative_prompt(self, base_negative: str, strength: str = "medium") -> str:
        """
        生成增强的负面提示词，用于在生成阶段避免水印
        
        参数:
            base_negative: 基础负面提示词
            strength: 强度 (light, medium, strong, extreme)
        
        返回:
            增强后的负面提示词
        """
        watermark_terms = {
            "light": [
                "watermark", "text", "signature"
            ],
            "medium": [
                "watermark", "text", "signature", "logo", "copyright", 
                "stamp", "watermarked", "brand"
            ],
            "strong": [
                "watermark", "text", "signature", "logo", "copyright", 
                "stamp", "watermarked", "brand", "label", "caption",
                "water mark", "sign", "writing", "overlay"
            ],
            "extreme": [
                "watermark", "text", "signature", "logo", "copyright", 
                "stamp", "watermarked", "brand", "label", "caption",
                "water mark", "sign", "writing", "overlay", "font",
                "lettering", "inscription", "marking", "watermark text",
                "watermarked image", "copyright symbol"
            ]
        }
        
        existing_terms = [t.strip() for t in base_negative.split(',')]
        existing_set = set(t.lower() for t in existing_terms)
        
        new_terms = watermark_terms.get(strength, watermark_terms["medium"])
        for term in new_terms:
            if term.lower() not in existing_set:
                existing_terms.append(term)
                existing_set.add(term.lower())
        
        return ", ".join(existing_terms)
    
    # ==================== 方法2: OpenCV 图像修复 ====================
    def _remove_with_inpaint(self, image: np.ndarray, method: str = "telea") -> np.ndarray:
        """
        使用 OpenCV 图像修复去除水印
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        _, mask1 = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        
        edges = cv2.Canny(gray, 50, 150)
        kernel = np.ones((3, 3), np.uint8)
        mask2 = cv2.dilate(edges, kernel, iterations=2)
        
        mask = cv2.bitwise_or(mask1, mask2)
        
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        inpaint_method = cv2.INPAINT_TELEA if method == "telea" else cv2.INPAINT_NS
        result = cv2.inpaint(image, mask, 5, inpaint_method)
        
        return result
    
    # ==================== 方法3: OpenCV 模糊处理 ====================
    def _remove_with_blur(self, image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
        """
        使用自适应模糊去除水印
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        _, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
        
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
        
        result = image.copy()
        
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            width = stats[i, cv2.CC_STAT_WIDTH]
            height = stats[i, cv2.CC_STAT_HEIGHT]
            
            if 50 < area < 5000 and (width / height > 3 or height / width > 3):
                region_mask = (labels == i).astype(np.uint8) * 255
                region_mask = cv2.dilate(region_mask, np.ones((3, 3), np.uint8), iterations=2)
                
                blurred = cv2.GaussianBlur(result, (kernel_size, kernel_size), 0)
                result = np.where(region_mask[:, :, np.newaxis] > 0, blurred, result)
        
        return result
    
    # ==================== 方法4: AI 检测 ====================
    def _remove_with_ai(self, image: np.ndarray) -> np.ndarray:
        """
        使用 AI 模型检测并去除水印
        """
        try:
            from transformers import pipeline
            
            if self._ai_model is None:
                self._ai_model = pipeline(
                    "image-segmentation",
                    model="facebook/detr-resnet-50-panoptic",
                    device=0 if torch.cuda.is_available() else -1
                )
            
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            results = self._ai_model(pil_image)
            
            mask = np.zeros((image.shape[0], image.shape[1]), dtype=np.uint8)
            
            for r in results:
                if r.get('label') in ['text', 'logo', 'sign']:
                    seg = r.get('mask')
                    if seg is not None:
                        seg_np = np.array(seg.resize((image.shape[1], image.shape[0])))
                        mask[seg_np > 0.5] = 255
            
            if np.sum(mask) > 0:
                mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=2)
                result = cv2.inpaint(image, mask, 5, cv2.INPAINT_TELEA)
                return result
            
            return image
            
        except ImportError:
            logger.info(f"⚠️ AI 检测模式需要 transformers 和 torch")
            return image
        except Exception as e:
            logger.info(f"⚠️ AI 检测失败: {e}")
            return image
    
    # ==================== 组合方法 ====================
    def remove_watermark(
        self, 
        image: Image.Image, 
        methods: List[str] = None,
        strength: str = "medium",
        auto_detect: bool = True
    ) -> Image.Image:
        """
        组合多种方法去除水印
        """
        if methods is None:
            methods = ["opencv_inpaint", "opencv_blur"]
        
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        has_watermark = True
        if auto_detect:
            has_watermark = self._detect_watermark(img_cv)
        
        if not has_watermark:
            return image
        
        results = []
        
        for method in methods:
            if method == "opencv_inpaint":
                try:
                    result = self._remove_with_inpaint(img_cv.copy())
                    results.append(result)
                except Exception as e:
                    logger.info(f"⚠️ Inpaint 方法失败: {e}")
            
            elif method == "opencv_blur":
                try:
                    result = self._remove_with_blur(img_cv.copy())
                    results.append(result)
                except Exception as e:
                    logger.info(f"⚠️ Blur 方法失败: {e}")
            
            elif method == "ai_detection":
                try:
                    result = self._remove_with_ai(img_cv.copy())
                    results.append(result)
                except Exception as e:
                    logger.info(f"⚠️ AI 方法失败: {e}")
        
        if results:
            best = self._select_best_result(results)
            result_rgb = cv2.cvtColor(best, cv2.COLOR_BGR2RGB)
            return Image.fromarray(result_rgb)
        
        return image
    
    # ==================== 辅助方法 ====================
    def _detect_watermark(self, image: np.ndarray) -> bool:
        """检测图片是否包含水印"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        white_ratio = np.sum(binary > 0) / (gray.shape[0] * gray.shape[1])
        
        edges = cv2.Canny(gray, 50, 150)
        edge_ratio = np.sum(edges > 0) / (gray.shape[0] * gray.shape[1])
        
        kernel_h = np.ones((1, 10), np.uint8)
        kernel_v = np.ones((10, 1), np.uint8)
        
        horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_h)
        vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_v)
        
        text_features = np.sum(horizontal > 0) + np.sum(vertical > 0)
        text_ratio = text_features / (gray.shape[0] * gray.shape[1])
        
        conditions = [
            white_ratio > 0.01 and white_ratio < 0.1,
            edge_ratio > 0.05,
            text_ratio > 0.001
        ]
        
        return sum(conditions) >= 2
    
    def _select_best_result(self, results: List[np.ndarray]) -> np.ndarray:
        """从多个结果中选择最佳的一个"""
        best = results[0]
        best_score = float('inf')
        
        for img in results:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_count = np.sum(edges > 0)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            score = edge_count - laplacian_var * 0.01
            
            if score < best_score:
                best_score = score
                best = img
        
        return best
    
    # ==================== 外部调用接口 ====================
    
    def get_enhanced_negative(self, base_negative: str, strength: str = "medium") -> str:
        """
        获取增强的负面提示词
        """
        return self._enhance_negative_prompt(base_negative, strength)
    
    def get_negative_prompt_enhancement(self, strength: str = "medium") -> str:
        """
        获取负面提示词的增强部分
        """
        return self._enhance_negative_prompt("", strength)


# ==================== 便捷函数 ====================

def remove_watermark_from_file(
    filepath: str, 
    output_path: Optional[str] = None,
    methods: List[str] = None,
    strength: str = "medium",
    auto_detect: bool = True
) -> str:
    """
    从文件去除水印
    """
    remover = WatermarkRemover()
    
    try:
        image = Image.open(filepath).convert('RGB')
        result = remover.remove_watermark(
            image, 
            methods=methods,
            strength=strength,
            auto_detect=auto_detect
        )
        
        if output_path is None:
            base, ext = os.path.splitext(filepath)
            output_path = f"{base}_clean{ext}"
        
        result.save(output_path, quality=95)
        logger.info(f"✅ 水印已去除: {output_path}")
        return output_path
        
    except Exception as e:
        logger.info(f"❌ 水印去除失败: {e}")
        return filepath


if __name__ == "__main__":
    test_file = "test.png"
    if os.path.exists(test_file):
        remove_watermark_from_file(test_file)
# gui/chat/utils/image_analyzer.py
"""图片分析工具"""

import cv2
import numpy as np


class ImageAnalyzer:
    """图片分析器"""
    
    @staticmethod
    def analyze_features(image_path: str) -> dict:
        """分析图片特征"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                return {}

            h, w = img.shape[:2]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # 检测人脸
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=8, minSize=(30, 30))
            valid_faces = [(x, y, fw, fh) for (x, y, fw, fh) in faces if fw > 40 and fh > 40]

            # 判断是否为全身照
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
            print(f"⚠️ 分析图片失败: {e}")
            return {}
    
    @staticmethod
    def extract_pose(image_path: str):
        """提取姿态图"""
        try:
            from controlnet_aux import OpenPoseDetector
            
            img = cv2.imread(image_path)
            if img is None:
                return None
            
            detector = OpenPoseDetector.from_pretrained("lllyasviel/ControlNet")
            return detector(img, output_type="pil")
        except Exception as e:
            print(f"⚠️ 姿态提取失败: {e}")
            return None
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
螟ｧ逅遏ｳ髮募ワ荳鍋畑 - 驟咲ｽｮ譁莉ｶ逕滓仙勣 (螳梧紛迚 - 14荳ｪ蝨ｺ譎ｯ)
謾ｯ謖∬ｪ蜉ｨ蛻譫仙崟迚迚ｹ蠕ïｼ梧耳闕先怙菴ｳ蜿よ焚
謾ｯ謖∬ｪ蜉ｨ譽豬区ｧ蛻ｫ
"""

import sys
import io

# 笨 蠑ｺ蛻ｶ stdout 菴ｿ逕ｨ UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    
import sys
import os
import json
import argparse
from datetime import datetime
from PIL import Image

# ==================== 扈滉ｸ郛灘ｭ倡岼蠖 ====================
CACHE_ROOT = r"E:\hf_cache\.cache"
os.environ['DEEPFACE_HOME'] = os.path.join(CACHE_ROOT, "deepface")
os.makedirs(os.environ['DEEPFACE_HOME'], exist_ok=True)

# 蟆晁ｯ募ｯｼ蜈･ deepfaceïｼ亥庄騾会ｼ
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
    print(f"笨 deepface 蟾ｲ蜉 霓ｽïｼ檎ｼ灘ｭ倡岼蠖: {os.environ['DEEPFACE_HOME']}")
except ImportError:
    DEEPFACE_AVAILABLE = False
    print("笞 ïｸ deepface 譛ｪ螳芽｣ïｼ梧ｧ蛻ｫ譽豬句ｰ菴ｿ逕ｨ鮟倩ｮ､蛟ｼ")
    print("   螳芽｣: pip install deepface")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def detect_gender(image_path):
    """
    閾ｪ蜉ｨ譽豬句崟迚荳ｭ莠ｺ迚ｩ逧諤ｧ蛻ｫ
    
    霑泌屓:
        "male" 謌 "female"
    """
    if not DEEPFACE_AVAILABLE:
        return "female"
    
    try:
        result = DeepFace.analyze(
            img_path=image_path, 
            actions=['gender'], 
            enforce_detection=False  # 蜊ｳ菴ｿ譽豬倶ｸ榊芦莠ｺ閼ｸ荵溯ｿ泌屓扈捺棡
        )
        
        # DeepFace 蜿ｯ閭ｽ霑泌屓蛻苓｡ｨ謌門ｭ怜ｸ
        if isinstance(result, list):
            result = result[0]
        
        gender = result.get('gender', {})
        if isinstance(gender, dict):
            man_score = gender.get('Man', 0)
            woman_score = gender.get('Woman', 0)
            detected = 'male' if man_score > woman_score else 'female'
            print(f"   ð洫 諤ｧ蛻ｫ譽豬: {detected} (Man: {man_score:.1%}, Woman: {woman_score:.1%})")
            return detected
        else:
            return "female"
            
    except Exception as e:
        print(f"   笞 ïｸ 諤ｧ蛻ｫ譽豬句､ｱ雍･: {e}ïｼ碁ｻ倩ｮ､菴ｿ逕ｨ female")
        return "female"


def analyze_image(image_path):
    """
    閾ｪ蜉ｨ蛻譫仙崟迚迚ｹ蠕ïｼ梧耳闕先怙菴ｳ蜿よ焚
    
    霑泌屓:
        dict: {
            "strength": 謗ｨ闕仙ｼｺ蠎ｦ,
            "max_strength": 謗ｨ闕先怙螟ｧ蠑ｺ蠎ｦ,
            "type": 蝗ｾ迚邀ｻ蝙,
            "gender": 譽豬句芦逧諤ｧ蛻ｫ,
            "confidence": 鄂ｮ菫｡蠎ｦ
        }
    """
    result = {
        "strength": 0.25,
        "max_strength": 0.30,
        "type": "unknown",
        "gender": "female",
        "confidence": 0.0
    }
    
    try:
        # 1. 譽豬区ｧ蛻ｫ
        result["gender"] = detect_gender(image_path)
        
        # 2. 蛻譫仙ｮｽ鬮俶ｯ
        img = Image.open(image_path)
        w, h = img.size
        aspect_ratio = w / h
        
        if aspect_ratio > 1.3:
            if aspect_ratio > 1.8:
                result.update({
                    "strength": 0.18,
                    "max_strength": 0.25,
                    "type": "wide_multi",
                    "confidence": 0.7
                })
            else:
                result.update({
                    "strength": 0.22,
                    "max_strength": 0.28,
                    "type": "wide",
                    "confidence": 0.6
                })
        elif aspect_ratio < 0.75:
            if aspect_ratio < 0.6:
                result.update({
                    "strength": 0.25,
                    "max_strength": 0.30,
                    "type": "full_body",
                    "confidence": 0.7
                })
            else:
                result.update({
                    "strength": 0.30,
                    "max_strength": 0.35,
                    "type": "portrait",
                    "confidence": 0.75
                })
        else:
            if 0.9 < aspect_ratio < 1.1:
                result.update({
                    "strength": 0.20,
                    "max_strength": 0.25,
                    "type": "seated_or_couple",
                    "confidence": 0.6
                })
            else:
                result.update({
                    "strength": 0.25,
                    "max_strength": 0.30,
                    "type": "medium",
                    "confidence": 0.5
                })
                
    except Exception as e:
        print(f"   笞 ïｸ 蝗ｾ迚蛻譫仙､ｱ雍･: {e}ïｼ御ｽｿ逕ｨ鮟倩ｮ､蜿よ焚")
    
    return result


class MarbleConfigGenerator:
    """螟ｧ逅遏ｳ髮募ワ荳鍋畑驟咲ｽｮ逕滓仙勣"""
    
    def __init__(self):
        self.config_dir = os.path.join(os.path.dirname(__file__), "output", "configs")
        os.makedirs(self.config_dir, exist_ok=True)
        self.results = {"single": [], "couple": []}

    # ===== 縲先眠蠅槭大惠霑咎㈹豺ｻ蜉 邊ｾ邂蜃ｽ謨ｰ =====
    def _shorten_for_clip(self, text, max_len=300):
        """
        邊ｾ邂謠千､ｺ隸堺ｻ･騾ょｺ CLIP 77 token 髯仙宛
        謖蛾怜捷蛻蜑ｲïｼ悟悉驥搾ｼ御ｼ伜井ｿ晉蕗驥崎ｦ∫噪隸
        
        蜿よ焚:
            text: 蜴溷ｧ区署遉ｺ隸
            max_len: 譛螟ｧ蟄礼ｬｦ髟ｿ蠎ｦ (蟒ｺ隶ｮ 300)
        
        霑泌屓:
            邊ｾ邂蜷守噪謠千､ｺ隸
        """
        if not text or len(text) <= max_len:
            return text
        
        # 謖蛾怜捷蛻蜑ｲ
        parts = [p.strip() for p in text.split(',') if p.strip()]
        
        # 蜴ｻ驥
        seen = set()
        unique_parts = []
        for p in parts:
            if p not in seen:
                seen.add(p)
                unique_parts.append(p)
        
        # 謖蛾柄蠎ｦ謗貞ｺ擾ｼ磯柄逧譖ｴ蜈ｷ菴難ｼ御ｼ伜井ｿ晉蕗ïｼ
        unique_parts.sort(key=lambda x: len(x), reverse=True)
        
        # 譫蟒ｺ扈捺棡ïｼ碁剞蛻ｶ髟ｿ蠎ｦ
        result = []
        current_len = 0
        for part in unique_parts:
            add_len = len(part) + 2  # +2 for ", "
            if current_len + add_len <= max_len:
                result.append(part)
                current_len += add_len
            else:
                # 螯よ棡蠖灘燕驛ｨ蛻螟ｪ髟ｿïｼ悟ｰ晁ｯ墓穐譁ｭ
                remaining = max_len - current_len
                if remaining > 10:
                    # 蜿門燕蜃 荳ｪ隸
                    words = part.split()
                    truncated = ' '.join(words[:remaining // 10])
                    if truncated and len(truncated) > 5:
                        result.append(truncated + "...")
                break
        
        shortened = ', '.join(result)
        if len(shortened) < len(text):
            print(f"   笨ゑｸ 謠千､ｺ隸榊ｷｲ邊ｾ邂: {len(text)} -> {len(shortened)} 蟄礼ｬｦ")
        
        return shortened if result else text[:max_len]
    
    def _count_tokens(self, text):
        """邊礼払隶｡邂 token 謨ｰïｼCLIP 郤ｦ 1-2 token/隸搾ｼ"""
        if not text:
            return 0
        # 豈丈ｸｪ隸咲ｺｦ 1-2 tokenïｼ悟刈 2 荳ｪ迚ｹ谿 token
        return len(text.split()) + 2
        
    def generate_marble_scenes(self, target_image=None, target_gender="auto", base_strength=0.25):
        """
        逕滓仙､ｧ逅遏ｳ髮募ワ蝨ｺ譎ｯ驟咲ｽｮ - 14荳ｪ蝨ｺ譎ｯïｼ亥性霄ｺ蟋ｿ+謗･蜷ｻïｼ
        
        蜿よ焚:
            target_image: 逶ｮ譬蝗ｾ迚霍ｯ蠕ïｼ育畑莠手ｪ蜉ｨ蛻譫撰ｼ
            target_gender: 諤ｧ蛻ｫ ("male", "female", "auto")
            base_strength: 蝓ｺ遑蠑ｺ蠎ｦïｼ井ｼ夊｢ｫ閾ｪ蜉ｨ蛻譫占ｦ逶厄ｼ
        """
        # 閾ｪ蜉ｨ蛻譫仙崟迚
        analysis = {}
        if target_image and os.path.exists(target_image):
            analysis = analyze_image(target_image)
            print(f"   ð沒 蝗ｾ迚蛻譫千ｻ捺棡: {analysis}")
        else:
            analysis = {
                "strength": base_strength,
                "max_strength": min(base_strength + 0.05, 0.40),
                "type": "default",
                "gender": "female",
                "confidence": 0.0
            }
        
        # 笨 遑ｮ螳壽ｧ蛻ｫ
        if target_gender == "auto":
            detected_gender = analysis.get("gender", "female")
        else:
            detected_gender = target_gender
        
        print(f"   ð洫 譛扈井ｽｿ逕ｨ諤ｧ蛻ｫ: {detected_gender}")
        
        # 譬ｹ謐ｮ蛻譫千ｻ捺棡隹謨ｴ蜷蝨ｺ譎ｯ逧蠑ｺ蠎ｦ
        base_s = analysis.get("strength", 0.25)
        
        # 蠑ｺ蠎ｦ隹謨ｴ隗蛻
        if analysis.get("type") in ["portrait", "full_body"]:
            s_high = base_s + 0.05
            s_low = base_s - 0.02
            s_very_low = base_s - 0.05
            s_extreme_low = base_s - 0.08
        elif analysis.get("type") in ["seated_or_couple", "wide_multi"]:
            s_high = base_s - 0.03
            s_low = base_s - 0.08
            s_very_low = base_s - 0.12
            s_extreme_low = base_s - 0.15
        else:
            s_high = base_s
            s_low = base_s - 0.03
            s_very_low = base_s - 0.06
            s_extreme_low = base_s - 0.09
        
        # 髯仙宛闌蝗ｴ
        s_high = max(0.15, min(0.40, s_high))
        s_low = max(0.12, min(0.35, s_low))
        s_very_low = max(0.10, min(0.30, s_very_low))
        s_extreme_low = max(0.08, min(0.25, s_extreme_low))
        
        # 笨 譬ｹ謐ｮ諤ｧ蛻ｫ逕滓先署遉ｺ隸
        if detected_gender == "male":
            base_prompt = "a man turned into a flawless pure white marble statue, full body, full length, entire figure, same man, same face, same body shape, same pose, same composition, masculine"
            gender_negative = "woman, female, feminine, breasts, curvy, soft features, girly"
            pronoun = "he"
        else:
            base_prompt = "a beautiful woman turned into a flawless pure white marble statue, full body, full length, entire figure, same woman, same face, same features, feminine figure, elegant pose"
            gender_negative = "man, male, masculine, beard, mustache, muscular, broad shoulders, masculine features, bodybuilder"
            pronoun = "she"
        
        marble_quality = "pure white marble, flawless stone, no color, monochrome white, classical sculpture, highly detailed stone texture, matte finish, no shine, 8k, photorealistic, masterpiece"
        marble_quality_enhanced = "pure white marble, flawless stone, no color, monochrome white, classical sculpture, intricate carving details, smooth stone texture, matte finish, no shine, 8k, photorealistic, masterpiece, high contrast, dramatic shadows"
        
        # 蜈ｬ蜈ｱ negative 隸
        neg_common = "worst quality, low quality, deformed, blurry, ugly"
        neg_no_color = "color, painting, cartoon, 3d render, shiny, glossy, wet, oil, plastic, wax, colored, warm tones, beige, yellow, gray"
        neg_no_skin = "skin, flesh, clothes, fabric"
        neg_no_shadow = "shadow, dark, underexposed"
        neg_multi = "messy, cluttered, chaotic"
        neg_crop = "cropped, partial, close-up, face only, head only"  # 笨 譁ｰ蠅橸ｼ夐亟豁｢蜿ｪ逕滓仙､ｴ蜒
        
        scenes = [
            # ==================== 蜊穂ｺｺ蝨ｺ譎ｯ (9荳ｪ) ====================
            {
                "name": "蜊穂ｺｺ螟ｧ逅遏ｳ_螻募糸",
                "prompt": f"{base_prompt}, {marble_quality}, museum gallery, soft lighting, marble pedestal, white background",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_crop},{gender_negative}",
                "width": 768,
                "height": 1024,
                "strength": s_high
            },
            {
                "name": "蜊穂ｺｺ螟ｧ逅遏ｳ_螳ｫ谿ｿ",
                "prompt": f"{base_prompt}, {marble_quality}, grand classical palace, ornate columns, marble floor, dramatic spotlight, chandelier",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow},{neg_crop}, {gender_negative}",
                "width": 1024,
                "height": 768,
                "strength": s_high - 0.02
            },
            {
                "name": "蜊穂ｺｺ螟ｧ逅遏ｳ_蝮仙ｧｿ",
                "prompt": f"{base_prompt}, {marble_quality_enhanced}, sitting on marble throne, classical Greek sculpture, museum, regal pose",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_multi}, {neg_crop},{gender_negative}",
                "width": 1024,
                "height": 1024,
                "strength": s_low
            },
            {
                "name": "蜊穂ｺｺ螟ｧ逅遏ｳ_萓ｧ霄ｫ",
                "prompt": f"{base_prompt}, {marble_quality}, side profile, elegant pose, classical art, marble pedestal, profile view",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, front view,{neg_crop}, {gender_negative}",
                "width": 768,
                "height": 1024,
                "strength": s_low + 0.03
            },
            {
                "name": "蜊穂ｺｺ螟ｧ逅遏ｳ_蜈ｨ霄ｫ",
                "prompt": f"{base_prompt}, {marble_quality_enhanced}, full body standing, heroic pose, classical sculpture, museum gallery, marble pedestal",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, cropped, partial, {neg_crop},{gender_negative}",
                "width": 768,
                "height": 1024,
                "strength": s_low
            },
            {
                "name": "蜊穂ｺｺ螟ｧ逅遏ｳ_蜊願ｺｫ迚ｹ蜀",
                "prompt": f"{base_prompt}, {marble_quality_enhanced}, bust sculpture, close-up, detailed face, classical art, museum display, white marble",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_crop},{gender_negative}",
                "width": 768,
                "height": 1024,
                "strength": s_high
            },
            {
                "name": "蜊穂ｺｺ螟ｧ逅遏ｳ_闃ｱ蝗ｭ",
                "prompt": f"{base_prompt}, {marble_quality}, classical garden setting, ancient ruins, ivy, soft sunlight, marble pedestal, outdoor sculpture",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, overgrown, moss, {neg_crop},{gender_negative}",
                "width": 1024,
                "height": 768,
                "strength": s_high - 0.02
            },
            {
                "name": "蜊穂ｺｺ螟ｧ逅遏ｳ_蜉ｨ諤",
                "prompt": f"{base_prompt}, {marble_quality_enhanced}, dynamic pose, movement, classical sculpture, museum, dramatic lighting, action",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, static, stiff, {neg_crop},{gender_negative}",
                "width": 1024,
                "height": 1024,
                "strength": s_low
            },
            {
                "name": "蜊穂ｺｺ螟ｧ逅遏ｳ_霄ｺ蟋ｿ",
                "prompt": f"{base_prompt}, {marble_quality_enhanced}, lying down, reclining pose, sleeping beauty, classical sculpture, marble bed, museum, peaceful expression, elegant drapery, soft lighting",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_multi}, standing, sitting, upright, {neg_crop},{gender_negative}",
                "width": 1024,
                "height": 768,
                "strength": s_very_low
            },

            # ==================== 蜿御ｺｺ蝨ｺ譎ｯ (5荳ｪ) ====================
            {
                "name": "蜿御ｺｺ螟ｧ逅遏ｳ_諡･謚ｱ",
                "prompt": f"a man and a woman couple turned into flawless pure white marble statues, intimate embrace, {marble_quality_enhanced}, romantic pose, museum hall, marble pedestal, dramatic lighting, masterpiece, heterosexual couple",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_multi},{neg_crop}, same gender, two women, two men, lesbian, gay",
                "width": 1024,
                "height": 1024,
                "strength": s_very_low
            },
            {
                "name": "蜿御ｺｺ螟ｧ逅遏ｳ_豺ｱ諠蟇ｹ隗",
                "prompt": f"a man and a woman couple turned into pure white marble statues, holding hands, looking at each other, {marble_quality_enhanced}, classical art, palace exhibition, glowing light, high detail, romantic atmosphere, heterosexual couple",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_multi}, {neg_crop},same gender, two women, two men, lesbian, gay",
                "width": 1024,
                "height": 768,
                "strength": s_very_low
            },
            {
                "name": "蜿御ｺｺ螟ｧ逅遏ｳ_蟷ｶ閧ｩ",
                "prompt": f"a man and a woman couple turned into pure white marble statues, standing side by side, {marble_quality_enhanced}, classical sculpture, museum gallery, marble pedestals, elegant, formal, heterosexual couple",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_multi}, {neg_crop},same gender, two women, two men, lesbian, gay",
                "width": 1024,
                "height": 768,
                "strength": s_very_low + 0.02
            },
            {
                "name": "蜿御ｺｺ螟ｧ逅遏ｳ_闊櫁ｹ",
                "prompt": f"a man and a woman couple turned into pure white marble statues, dancing together, elegant pose, {marble_quality_enhanced}, classical art, museum, dramatic lighting, graceful movement, masterpiece, heterosexual couple",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_multi}, stiff, static, {neg_crop},same gender, two women, two men, lesbian, gay",
                "width": 1024,
                "height": 1024,
                "strength": s_very_low
            },
            {
                "name": "蜿御ｺｺ螟ｧ逅遏ｳ_謗･蜷ｻ",
                "prompt": f"a man and a woman couple turned into pure white marble statues, kissing, romantic kiss, intimate moment, {marble_quality_enhanced}, classical sculpture, museum, marble pedestal, dramatic lighting, passionate, masterpiece, heterosexual couple, love",
                "negative": f"{neg_common}, {neg_no_skin}, {neg_no_color}, {neg_no_shadow}, {neg_multi}, {neg_crop},ugly, distorted, inappropriate, explicit, same gender, two women, two men, lesbian, gay",
                "width": 1024,
                "height": 1024,
                "strength": s_extreme_low
            },
        ]

        # ===== 縲先眠蠅槭大惠霑咎㈹邊ｾ邂謇譛牙惻譎ｯ逧謠千､ｺ隸 =====
        for scene in scenes:
            if "prompt" in scene:
                scene["prompt"] = self._shorten_for_clip(scene["prompt"], max_len=300)
                # 譽譟･ token 謨ｰ蟷ｶ謇灘魂隴ｦ蜻
                token_count = self._count_tokens(scene["prompt"])
                if token_count > 75:
                    print(f"   笞 ïｸ {scene['name']} token 謨ｰ: {token_count}ïｼ悟庄閭ｽ陲ｫ謌ｪ譁ｭ")
            
            if "negative" in scene:
                scene["negative"] = self._shorten_for_clip(scene["negative"], max_len=250)
            
        self.results["single"] = scenes
        return scenes

    def export_config(self,
                      target_image: str,
                      model_path: str = "../models/sd-v1-5/aiiiiii01_v10.safetensors",
                      strength: float = None,
                      max_strength: float = None,
                      gender: str = "auto",
                      cfg: float = 7.5,
                      steps: int = 25,
                      output_file: str = None,
                      scene_count: int = 14) -> str:
        """
        蟇ｼ蜃ｺ荳ｺ marble_batch_config.json
        
        蜿よ焚:
            target_image: 逶ｮ譬蝗ｾ迚霍ｯ蠕
            strength: 謇句勘謖螳壼ｼｺ蠎ｦïｼ亥ｦよ棡荳ｺ Noneïｼ悟呵ｪ蜉ｨ蛻譫撰ｼ
            max_strength: 謇句勘謖螳壽怙螟ｧ蠑ｺ蠎ｦ
            gender: 諤ｧ蛻ｫ ("male", "female", "auto")
            cfg: CFG Scale
            steps: 謗ｨ逅豁･謨ｰ
            output_file: 霎灘ｺ譁莉ｶ蜷
            scene_count: 蝨ｺ譎ｯ謨ｰ驥 (6, 12, 謌 14)
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.config_dir, f"marble_batch_config_{timestamp}.json")

        # 閾ｪ蜉ｨ蛻譫仙崟迚
        analysis = analyze_image(target_image)
        print(f"\n   ð沒 蝗ｾ迚蛻譫千ｻ捺棡:")
        print(f"      邀ｻ蝙: {analysis.get('type', 'unknown')}")
        print(f"      諤ｧ蛻ｫ: {analysis.get('gender', 'unknown')}")
        print(f"      謗ｨ闕仙ｼｺ蠎ｦ: {analysis.get('strength', 0.25)}")
        print(f"      鄂ｮ菫｡蠎ｦ: {analysis.get('confidence', 0):.0%}")
        
        # 遑ｮ螳壽ｧ蛻ｫ
        if gender == "auto":
            detected_gender = analysis.get("gender", "female")
        else:
            detected_gender = gender
        print(f"   ð洫 譛扈井ｽｿ逕ｨ諤ｧ蛻ｫ: {detected_gender}")
        
        # 螯よ棡逕ｨ謌ｷ謖螳壻ｺ strengthïｼ御ｽｿ逕ｨ逕ｨ謌ｷ謖螳夂噪蛟ｼ
        if strength is None:
            auto_strength = analysis.get("strength", 0.25)
            if analysis.get("type") == "portrait":
                auto_strength = 0.30
            elif analysis.get("type") == "full_body":
                auto_strength = 0.28
            elif analysis.get("type") == "seated_or_couple":
                auto_strength = 0.20
            elif analysis.get("type") == "wide_multi":
                auto_strength = 0.18
            strength = auto_strength
        
        if max_strength is None:
            max_strength = min(strength + 0.05, 0.40)

        print(f"\n   笞呻ｸ  譛扈亥盾謨ｰ:")
        print(f"      strength: {strength}")
        print(f"      max_strength: {max_strength}")
        print(f"      gender: {detected_gender}")
        print(f"      cfg: {cfg}")
        print(f"      steps: {steps}")
        print(f"      scene_count: {scene_count}")

        # 逕滓仙惻譎ｯ驟咲ｽｮïｼ井ｼ 蜈･譽豬句芦逧諤ｧ蛻ｫïｼ
        self.generate_marble_scenes(
            target_image=target_image, 
            target_gender=detected_gender,
            base_strength=strength
        )

        # 譬ｹ謐ｮ scene_count 騾画叫蝨ｺ譎ｯ
        all_scenes = self.results["single"]
        if scene_count == 6:
            selected_scenes = all_scenes[:6]
        elif scene_count == 12:
            selected_scenes = all_scenes[:12]
        else:
            selected_scenes = all_scenes

        # 譫蟒ｺ螳梧紛驟咲ｽｮ
        config = {
            "model_path": model_path,
            "target_image": target_image,
            "output_dir": "./output/batch_marble",
            "strength": strength,
            "max_strength": max_strength,
            "gender": detected_gender,
            "cfg": cfg,
            "steps": steps,
            "scene_count": scene_count,
            "analysis": analysis,
            "jobs": selected_scenes
        }

        # 遑ｮ菫晄ｯ丈ｸｪ job 驛ｽ譛 strength
        for job in config["jobs"]:
            if "strength" not in job:
                job["strength"] = strength

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        print(f"\n笨 螟ｧ逅遏ｳ驟咲ｽｮ蟾ｲ逕滓: {output_file}")
        print(f"   ð沒 蜈ｱ {len(config['jobs'])} 荳ｪ螟ｧ逅遏ｳ髮募ワ莉ｻ蜉｡")
        
        # 謇灘魂蜷蝨ｺ譎ｯ逧蠑ｺ蠎ｦ蛻蟶
        strengths = {}
        for job in config["jobs"]:
            s = job.get("strength", strength)
            name = job.get("name", "unknown")
            strengths[name] = s
        
        print(f"   ð沒 蜷蝨ｺ譎ｯ蠑ｺ蠎ｦ:")
        for name, s in strengths.items():
            print(f"      {name}: {s:.2f}")
        
        return output_file


def main():
    parser = argparse.ArgumentParser(
        description="螟ｧ逅遏ｳ髮募ワ - 驟咲ｽｮ譁莉ｶ逕滓仙勣 (螳梧紛迚 - 14荳ｪ蝨ｺ譎ｯ)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
遉ｺ萓:
  # 閾ｪ蜉ｨ譽豬区ｧ蛻ｫïｼ檎函謌14荳ｪ蝨ｺ譎ｯ
  python gen_config_marble.py --target-image "output/good/photo.png"
  
  # 謇句勘謖螳壽ｧ蛻ｫïｼ郁ｦ逶冶ｪ蜉ｨ譽豬具ｼ
  python gen_config_marble.py --target-image "output/good/photo.png" --gender male
  
  # 蜿ｪ逕滓12荳ｪ蝨ｺ譎ｯ
  python gen_config_marble.py --target-image "output/good/photo.png" --scenes 12
  
  # 譟･逵句崟迚蛻譫千ｻ捺棡ïｼ井ｸ咲函謌宣咲ｽｮïｼ
  python gen_config_marble.py --target-image "output/good/photo.png" --dry-run
        """
    )
    parser.add_argument("--target-image", type=str, required=True,
                        help="蝗ｾ逕溷崟逶ｮ譬蝗ｾ迚霍ｯ蠕")
    parser.add_argument("--output", type=str, default=None, 
                        help="霎灘ｺ譁莉ｶ蜷搾ｼ磯ｻ倩ｮ､閾ｪ蜉ｨ逕滓撰ｼ")
    parser.add_argument("--model", type=str,
                        default="../models/sd-v1-5/aiiiiii01_v10.safetensors",
                        help="蝓ｺ遑讓｡蝙玖ｷｯ蠕")
    parser.add_argument("--strength", type=float, default=None,
                        help="驥咲ｻ伜ｼｺ蠎ｦ (0.10-0.45)ïｼ御ｸ肴欠螳壼呵ｪ蜉ｨ蛻譫")
    parser.add_argument("--max-strength", type=float, default=None,
                        help="譛螟ｧ蠑ｺ蠎ｦ髯仙宛ïｼ御ｸ肴欠螳壼呵ｪ蜉ｨ隶｡邂")
    parser.add_argument("--gender", type=str, default="auto", choices=["auto", "male", "female"],
                        help="諤ｧ蛻ｫ: auto(閾ｪ蜉ｨ譽豬), male, female (鮟倩ｮ､ auto)")
    parser.add_argument("--cfg", type=float, default=7.5,
                        help="CFG Scale (謗ｨ闕 7.0-8.0)")
    parser.add_argument("--steps", type=int, default=25,
                        help="謗ｨ逅豁･謨ｰ (謗ｨ闕 20-30)")
    parser.add_argument("--scenes", type=int, default=14, choices=[6, 12, 14],
                        help="蝨ｺ譎ｯ謨ｰ驥: 6, 12, 謌 14 (鮟倩ｮ､ 14)")
    parser.add_argument("--dry-run", action="store_true",
                        help="莉蛻譫仙崟迚ïｼ御ｸ咲函謌宣咲ｽｮ")

    args = parser.parse_args()

    if not os.path.exists(args.target_image):
        print(f"笶 逶ｮ譬蝗ｾ迚荳榊ｭ伜惠: {args.target_image}")
        return

    # 螯よ棡譏ｯ dry-runïｼ悟宵蛻譫仙崟迚
    if args.dry_run:
        print("\nð沐 蝗ｾ迚蛻譫先ｨ｡蠑")
        print("=" * 60)
        analysis = analyze_image(args.target_image)
        print(f"\nð沒 蛻譫千ｻ捺棡:")
        print(f"   蝗ｾ迚霍ｯ蠕: {args.target_image}")
        print(f"   邀ｻ蝙: {analysis.get('type', 'unknown')}")
        print(f"   諤ｧ蛻ｫ: {analysis.get('gender', 'unknown')}")
        print(f"   謗ｨ闕仙ｼｺ蠎ｦ: {analysis.get('strength', 0.25)}")
        print(f"   鄂ｮ菫｡蠎ｦ: {analysis.get('confidence', 0):.0%}")
        print("\nð汳｡ 霑占｡御ｻ･荳句多莉､逕滓宣咲ｽｮ:")
        print(f"   python gen_config_marble.py --target-image \"{args.target_image}\"")
        return

    # 逕滓宣咲ｽｮ
    generator = MarbleConfigGenerator()
    generator.export_config(
        target_image=args.target_image,
        model_path=args.model,
        strength=args.strength,
        max_strength=args.max_strength,
        gender=args.gender,
        cfg=args.cfg,
        steps=args.steps,
        output_file=args.output,
        scene_count=args.scenes
    )


if __name__ == "__main__":
    main()

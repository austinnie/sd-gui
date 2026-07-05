#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
场景管理器 - 管理场景配置
"""

import json
import os
from typing import Dict, List, Optional, Any


class SceneManager:
    """场景管理器"""
    
    def __init__(self, config_path: str = "scene_patterns.json"):
        self.config_path = config_path
        self.scene_config = None
        self._default_negative = ""
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        possible_paths = [
            self.config_path,
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "scene_patterns.json"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scene_patterns.json")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.config_path = path
                break
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.scene_config = json.load(f)
                #print(f"✅ 已加载场景配置: {self.config_path}")
                
                scenes = self.scene_config.get("scenes", {})
                for scene_name, scene_data in scenes.items():
                    default_config = scene_data.get("默认配置", {})
                    if default_config.get("negative_prompt"):
                        self._default_negative = default_config["negative_prompt"]
                        break
                return
            except Exception as e:
                print(f"❌ 加载场景配置失败: {e}")
        
        self._create_default_config()
    
    def _create_default_config(self):
        """创建默认配置（包含完整数据）"""
        self.scene_config = self._get_default_scene_config()
        self.save_config()
    
    def _get_default_scene_config(self) -> dict:
        """获取默认场景配置"""
        return {
            "scenes": {
                "两人亲密场景": {
                    "categories": {
                        "基本姿势": {
                            "standing_together": {
                                "prompt": "standing together, side by side, both fully visible",
                                "negative": "cropped, partial view"
                            },
                            "hugging": {
                                "prompt": "hugging, arms wrapped around each other, embracing, both fully visible",
                                "negative": "cropped, partial view"
                            },
                            "kissing": {
                                "prompt": "kissing, passionate kiss, lips touching, intimate moment, both fully visible",
                                "negative": "cropped, partial view"
                            },
                            "sitting_embrace": {
                                "prompt": "sitting embrace, one on lap, arms wrapped, intimate, both fully visible",
                                "negative": "cropped, partial view"
                            },
                            "lying_down": {
                                "prompt": "lying together, horizontal position, cuddling, intimate, both fully visible",
                                "negative": "cropped, partial view"
                            },
                            "man_behind_woman": {
                                "prompt": "man standing behind woman, protective embrace, both fully visible",
                                "negative": "cropped, partial view"
                            },
                            "woman_on_lap": {
                                "prompt": "woman sitting on man's lap, arms around neck, intimate, both fully visible",
                                "negative": "cropped, partial view"
                            }
                        },
                        "亲密程度": {
                            "platonic": {
                                "prompt": "friendly, platonic, just friends, casual",
                                "negative": "intimate, romantic, sexual"
                            },
                            "romantic": {
                                "prompt": "romantic, loving, affectionate, tender moment",
                                "negative": "platonic, casual"
                            },
                            "passionate": {
                                "prompt": "passionate, intense, fiery romance, deep connection",
                                "negative": "gentle, soft"
                            },
                            "kissing": {
                                "prompt": "kissing, making out, lip lock, passionate kiss",
                                "negative": "no kissing, platonic"
                            },
                            "hugging": {
                                "prompt": "hugging, embracing, holding each other tight",
                                "negative": "distant, apart"
                            },
                            "cuddling": {
                                "prompt": "cuddling, snuggling, close embrace, warm",
                                "negative": "distant, apart"
                            }
                        },
                        "视角": {
                            "front_view": {
                                "prompt": "front view, both faces visible, looking at camera",
                                "negative": "side view, back view"
                            },
                            "profile_view": {
                                "prompt": "profile view, side view, both visible from side",
                                "negative": "front view"
                            },
                            "from_behind": {
                                "prompt": "from behind, back view, intimate perspective",
                                "negative": "front view"
                            },
                            "overhead": {
                                "prompt": "overhead view, top down, bird's eye view",
                                "negative": "ground level"
                            },
                            "close_up": {
                                "prompt": "close up, intimate details, faces close",
                                "negative": "wide shot"
                            }
                        },
                        "环境氛围": {
                            "bedroom": {
                                "prompt": "bedroom, cozy, intimate, soft lighting, bed visible",
                                "negative": "public place, outdoors"
                            },
                            "restaurant": {
                                "prompt": "restaurant, romantic dinner, candlelight, elegant setting",
                                "negative": "bedroom, casual"
                            },
                            "beach": {
                                "prompt": "beach, sunset, romantic seaside, waves, sand",
                                "negative": "indoor, city"
                            },
                            "park": {
                                "prompt": "park, nature, trees, grass, romantic outdoor setting",
                                "negative": "indoor, city"
                            },
                            "cafe": {
                                "prompt": "cafe, intimate coffee shop, cozy atmosphere",
                                "negative": "formal, restaurant"
                            },
                            "garden": {
                                "prompt": "garden, flowers, romantic setting, nature",
                                "negative": "indoor, urban"
                            },
                            "living_room": {
                                "prompt": "living room, comfortable home, couch, cozy",
                                "negative": "public place"
                            }
                        },
                        "服装状态": {
                            "casual": {
                                "prompt": "casual clothes, comfortable, everyday wear, both fully clothed",
                                "negative": "nude, formal"
                            },
                            "formal": {
                                "prompt": "formal wear, elegant dress, suit, sophisticated",
                                "negative": "casual, nude"
                            },
                            "lingerie": {
                                "prompt": "lingerie, intimate wear, lace, seductive, both in underwear",
                                "negative": "fully clothed, nude"
                            },
                            "nude": {
                                "prompt": "nude, naked, no clothes, intimate, artistic nudity",
                                "negative": "clothed, lingerie"
                            },
                            "partially_dressed": {
                                "prompt": "partially dressed, semi-nude, revealing, suggestive",
                                "negative": "fully clothed, fully nude"
                            },
                            "swimsuit": {
                                "prompt": "swimsuit, bikini, swimwear, beach attire",
                                "negative": "clothed, nude"
                            }
                        },
                        "情感表达": {
                            "romantic_love": {
                                "prompt": "romantic love, deep affection, looking into each other's eyes",
                                "negative": "angry, sad"
                            },
                            "passionate_desire": {
                                "prompt": "passionate desire, intense attraction, longing gaze",
                                "negative": "platonic, indifferent"
                            },
                            "tender_care": {
                                "prompt": "tender care, gentle touch, nurturing, warm",
                                "negative": "rough, intense"
                            },
                            "playful_love": {
                                "prompt": "playful love, laughing together, joyful, lighthearted",
                                "negative": "serious, intense"
                            },
                            "deep_connection": {
                                "prompt": "deep connection, soulmates, intimate bond, profound",
                                "negative": "shallow, casual"
                            },
                            "seductive": {
                                "prompt": "seductive, sensual, alluring, tempting",
                                "negative": "innocent, naive"
                            }
                        }
                    },
                    "默认配置": {
                        "negative_prompt": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, watermark, text, mutated hands, fused fingers, too many fingers, bad hands, missing fingers, extra digits, bad feet, cropped, out of frame, cut off at knees, cut off at waist, headshot only, close up only"
                    }
                }
            },
            "组合模板": {
                "浪漫晚餐": {
                    "basic_pose": "hugging",
                    "intimacy_level": "romantic",
                    "view_angle": "front_view",
                    "environment": "restaurant",
                    "clothing": "formal",
                    "emotion": "romantic_love",
                    "prompt_suffix": "candlelight dinner, wine glasses, romantic atmosphere"
                },
                "海滩日落": {
                    "basic_pose": "standing_together",
                    "intimacy_level": "romantic",
                    "view_angle": "profile_view",
                    "environment": "beach",
                    "clothing": "casual",
                    "emotion": "tender_care",
                    "prompt_suffix": "sunset, golden hour, ocean waves, warm glow"
                },
                "深情拥抱": {
                    "basic_pose": "hugging",
                    "intimacy_level": "hugging",
                    "view_angle": "front_view",
                    "environment": "bedroom",
                    "clothing": "casual",
                    "emotion": "deep_connection",
                    "prompt_suffix": "soft lighting, intimate atmosphere"
                },
                "激情热吻": {
                    "basic_pose": "kissing",
                    "intimacy_level": "passionate",
                    "view_angle": "close_up",
                    "environment": "bedroom",
                    "clothing": "casual",
                    "emotion": "passionate_desire",
                    "prompt_suffix": "intense passion, closed eyes, romantic mood"
                },
                "公园漫步": {
                    "basic_pose": "standing_together",
                    "intimacy_level": "romantic",
                    "view_angle": "front_view",
                    "environment": "park",
                    "clothing": "casual",
                    "emotion": "playful_love",
                    "prompt_suffix": "sunlight through trees, nature, peaceful"
                },
                "居家温馨": {
                    "basic_pose": "sitting_embrace",
                    "intimacy_level": "cuddling",
                    "view_angle": "front_view",
                    "environment": "living_room",
                    "clothing": "casual",
                    "emotion": "tender_care",
                    "prompt_suffix": "cozy home, relaxed atmosphere, comfortable"
                }
            }
        }
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.scene_config, f, ensure_ascii=False, indent=2)
            print(f"✅ 已保存场景配置: {self.config_path}")
        except Exception as e:
            print(f"❌ 保存场景配置失败: {e}")
    
    def get_categories(self, scene_name: str = "两人亲密场景") -> Dict:
        """获取场景的分类"""
        scene = self.scene_config.get("scenes", {}).get(scene_name, {})
        return scene.get("categories", {})
    
    def get_category_items(self, scene_name: str, category_name: str) -> Dict:
        """获取分类下的项目"""
        categories = self.get_categories(scene_name)
        return categories.get(category_name, {})
    
    def get_item_prompt(self, scene_name: str, category_name: str, item_key: str) -> str:
        """获取项目的prompt"""
        items = self.get_category_items(scene_name, category_name)
        item = items.get(item_key, {})
        return item.get("prompt", "")
    
    def get_item_negative(self, scene_name: str, category_name: str, item_key: str) -> str:
        """获取项目的negative"""
        items = self.get_category_items(scene_name, category_name)
        item = items.get(item_key, {})
        return item.get("negative", "")
    

    def build_prompt(self, selections: dict) -> tuple:
        """
        根据选择构建提示词 - 精简版
        """
        # 基础质量词（精简）
        quality = "masterpiece, best quality, realistic, 8k"
        
        # ✅ 统一使用正确的键名
        category_map = {
            "basic_pose": "姿势",
            "intimacy_level": "亲密程度", 
            "view_angle": "视角",
            "environment": "环境",
            "clothing": "服装",
            "emotion": "情感",
            "body_features_man": "男士特征",      # ✅ 修正
            "body_features_woman": "女士特征"     # ✅ 修正
        }
        
        # ✅ 优先级顺序（与 category_map 的键一致）
        order = ["basic_pose", "intimacy_level", "view_angle", "environment", "clothing", "emotion", "body_features_man", "body_features_woman"]
        
        # ✅ 收集选择的词条（去重，并限制数量）
        selected_parts = []
        seen = set()
        
        selected_count = 0
        max_selections = 6  # ✅ 限制数量，避免提示词过长
        
        for key in order:
            if selected_count >= max_selections:
                break
            if key in selections and selections[key]:
                value = selections[key].strip()
                if value and value not in seen:
                    seen.add(value)
                    # ✅ 如果 value 太长，截断
                    if len(value) > 50:
                        value = value[:50]
                    selected_parts.append(value)
                    selected_count += 1
        
        # ✅ 自定义后缀（限制长度）
        custom_suffix = selections.get("custom_suffix", "").strip()
        if custom_suffix and selected_count < max_selections:
            # 分割成多个关键词
            suffix_parts = custom_suffix.split('，')
            for part in suffix_parts[:2]:  # 最多取2个
                part = part.strip()
                if part and part not in seen and len(part) < 20:
                    selected_parts.append(part)
                    seen.add(part)
        
        # ✅ 构建提示词
        if selected_parts:
            prompt = f"{quality}, {', '.join(selected_parts)}"
        else:
            prompt = quality
        
        # ✅ 最终长度限制
        if len(prompt) > 200:
            prompt = prompt[:200]
            last_comma = prompt.rfind(',')
            if last_comma > 100:
                prompt = prompt[:last_comma]
        
        # 负面提示词（精简）
        negative = "worst quality, low quality, ugly, deformed, blurry, nsfw"
        
        return prompt, negative
    

    def get_template(self, template_name: str) -> Dict:
        """获取模板配置"""
        templates = self.scene_config.get("组合模板", {})
        template = templates.get(template_name, {})
        
        selections = {}
        # ✅ 添加 body_features_man 和 body_features_woman
        for key in ["basic_pose", "intimacy_level", "view_angle", "environment", "clothing", "emotion", "body_features_man", "body_features_woman"]:
            selections[key] = template.get(key, "")
        
        selections["custom_suffix"] = template.get("prompt_suffix", "")
        return selections
    
    def get_all_templates(self) -> List[str]:
        """获取所有模板名称"""
        return list(self.scene_config.get("组合模板", {}).keys())
    
    def add_template(self, name: str, config: Dict):
        """添加模板"""
        if "组合模板" not in self.scene_config:
            self.scene_config["组合模板"] = {}
        self.scene_config["组合模板"][name] = config
        self.save_config()
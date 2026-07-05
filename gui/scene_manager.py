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
        """加载配置 - 兼容新旧格式"""
        possible_paths = [
            self.config_path,
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "scene_patterns.json"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.config_path = path
                break
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.scene_config = json.load(f)
                
                # ✅ 检测是新格式还是旧格式
                if "scenes" in self.scene_config:
                    scenes = self.scene_config.get("scenes", {})
                    # 如果是旧格式（中文键名），自动转换
                    if "两人亲密场景" in scenes:
                        self._migrate_old_config()
                return
            except Exception as e:
                print(f"❌ 加载场景配置失败: {e}")
        
        self._create_default_config()

    def _migrate_old_config(self):
        """将旧格式转换为新格式"""
        old_scene = self.scene_config.get("scenes", {}).get("两人亲密场景", {})
        old_categories = old_scene.get("categories", {})
        old_templates = self.scene_config.get("组合模板", {})
        
        new_categories = {}
        key_map = {
            "基本姿势": "pose",
            "亲密程度": "intimacy",
            "视角": "view_angle",
            "环境氛围": "environment",
            "服装状态": "clothing",
            "情感表达": "emotion",
            "男士特征": "male_features",
            "女士特征": "female_features"
        }
        
        for old_key, new_key in key_map.items():
            if old_key in old_categories:
                new_categories[new_key] = old_categories[old_key]
        
        new_templates = {}
        for name, template in old_templates.items():
            new_templates[name] = {
                "pose": template.get("basic_pose", ""),
                "intimacy": template.get("intimacy_level", ""),
                "view_angle": template.get("view_angle", ""),
                "environment": template.get("environment", ""),
                "clothing": template.get("clothing", ""),
                "emotion": template.get("emotion", ""),
                "male_features": template.get("body_features_man", ""),
                "female_features": template.get("body_features_woman", ""),
                "suffix": template.get("prompt_suffix", "")
            }
        
        self.scene_config = {
            "scenes": {
                "couple_intimate": {
                    "categories": new_categories,
                    "defaults": old_scene.get("默认配置", {})
                }
            },
            "templates": new_templates,
            "character_templates": self.scene_config.get("人物组合模板", {})
        }
        
        # 保存迁移后的配置
        self.save_config()
        print("✅ 场景配置已自动迁移到新格式")
    
    def _create_default_config(self):
        """创建默认配置（包含完整数据）"""
        self.scene_config = self._get_default_scene_config()
        self.save_config()
    

    def _get_default_scene_config(self) -> dict:
        """获取默认场景配置 - 新格式英文版"""
        return {
            "scenes": {
                "couple_intimate": {
                    "categories": {
                        "pose": {
                            "standing_embrace": {
                                "name": "Standing Embrace",
                                "prompt": "standing embrace, hugging",
                                "negative": "cropped"
                            },
                            "sitting_embrace": {
                                "name": "Sitting Embrace",
                                "prompt": "sitting embrace, lap sitting",
                                "negative": "cropped"
                            },
                            "lying_down": {
                                "name": "Lying Down",
                                "prompt": "lying down, cuddling",
                                "negative": "cropped"
                            },
                            "bent_over": {
                                "name": "Bent Over",
                                "prompt": "bent over, from behind",
                                "negative": "standing upright"
                            },
                            "missionary": {
                                "name": "Missionary",
                                "prompt": "missionary",
                                "negative": "from behind"
                            },
                            "cowgirl": {
                                "name": "Cowgirl",
                                "prompt": "cowgirl",
                                "negative": "man on top"
                            },
                            "reverse_cowgirl": {
                                "name": "Reverse Cowgirl",
                                "prompt": "reverse cowgirl",
                                "negative": "face to face"
                            },
                            "spooning": {
                                "name": "Spooning",
                                "prompt": "spooning, from behind",
                                "negative": "face to face"
                            },
                            "standing_from_behind": {
                                "name": "Standing from Behind",
                                "prompt": "standing from behind",
                                "negative": "face to face"
                            },
                            "oral_man": {
                                "name": "Oral (Male)",
                                "prompt": "oral, blowjob",
                                "negative": "woman receiving"
                            },
                            "oral_woman": {
                                "name": "Oral (Female)",
                                "prompt": "oral, cunnilingus",
                                "negative": "man receiving"
                            },
                            "sixty_nine": {
                                "name": "69",
                                "prompt": "69 position",
                                "negative": "one sided"
                            }
                        },
                        "intimacy": {
                            "tender": {
                                "name": "Tender",
                                "prompt": "tender, gentle, soft",
                                "negative": "rough, intense"
                            },
                            "passionate": {
                                "name": "Passionate",
                                "prompt": "passionate, intense, kissing",
                                "negative": "gentle"
                            },
                            "lovemaking": {
                                "name": "Lovemaking",
                                "prompt": "lovemaking, intimate sex",
                                "negative": "rough, hardcore"
                            },
                            "hardcore": {
                                "name": "Hardcore",
                                "prompt": "hardcore, rough sex",
                                "negative": "gentle, slow"
                            },
                            "bdsm": {
                                "name": "BDSM",
                                "prompt": "bdsm, bondage, dominant",
                                "negative": "vanilla"
                            },
                            "group_sex": {
                                "name": "Group Sex",
                                "prompt": "threesome, group sex",
                                "negative": "one on one"
                            }
                        },
                        "view_angle": {
                            "front_view": {
                                "name": "Front View",
                                "prompt": "front view",
                                "negative": "back view"
                            },
                            "profile_view": {
                                "name": "Side View",
                                "prompt": "side view, profile",
                                "negative": "front view"
                            },
                            "from_behind": {
                                "name": "From Behind",
                                "prompt": "from behind",
                                "negative": "front view"
                            },
                            "overhead_view": {
                                "name": "Top View",
                                "prompt": "overhead view, birdseye",
                                "negative": "bottom view"
                            },
                            "closeup_penetration": {
                                "name": "Closeup Penetration",
                                "prompt": "closeup on penetration",
                                "negative": "full body"
                            },
                            "closeup_faces": {
                                "name": "Closeup Faces",
                                "prompt": "closeup on faces",
                                "negative": "full body"
                            }
                        },
                        "environment": {
                            "bedroom": {
                                "name": "Bedroom",
                                "prompt": "in bedroom, soft bed",
                                "negative": "outdoor"
                            },
                            "hotel": {
                                "name": "Hotel",
                                "prompt": "in hotel room",
                                "negative": "home"
                            },
                            "bathroom": {
                                "name": "Bathroom",
                                "prompt": "in bathroom, shower",
                                "negative": "bedroom"
                            },
                            "nature_outdoor": {
                                "name": "Outdoor Nature",
                                "prompt": "outdoor, forest, nature",
                                "negative": "indoor"
                            },
                            "beach": {
                                "name": "Beach",
                                "prompt": "on beach, ocean",
                                "negative": "indoor"
                            },
                            "car": {
                                "name": "Car",
                                "prompt": "in car, backseat",
                                "negative": "outdoor"
                            },
                            "office": {
                                "name": "Office",
                                "prompt": "in office, desk",
                                "negative": "home"
                            },
                            "public": {
                                "name": "Public",
                                "prompt": "public place, risky",
                                "negative": "private"
                            }
                        },
                        "clothing": {
                            "fully_dressed": {
                                "name": "Fully Dressed",
                                "prompt": "fully clothed",
                                "negative": "nude"
                            },
                            "partially_dressed": {
                                "name": "Partially Dressed",
                                "prompt": "partially dressed, clothes undone",
                                "negative": "fully nude"
                            },
                            "underwear": {
                                "name": "Underwear",
                                "prompt": "in underwear",
                                "negative": "clothed, nude"
                            },
                            "lingerie": {
                                "name": "Lingerie",
                                "prompt": "in lingerie, lace",
                                "negative": "regular underwear"
                            },
                            "nude": {
                                "name": "Nude",
                                "prompt": "nude, naked",
                                "negative": "clothed"
                            },
                            "costume": {
                                "name": "Costume",
                                "prompt": "in costume, cosplay",
                                "negative": "regular clothes"
                            }
                        },
                        "emotion": {
                            "romantic_love": {
                                "name": "Romantic Love",
                                "prompt": "romantic, loving",
                                "negative": "angry, sad"
                            },
                            "passionate_desire": {
                                "name": "Passionate Desire",
                                "prompt": "passionate desire, longing",
                                "negative": "cold"
                            },
                            "seductive": {
                                "name": "Seductive",
                                "prompt": "seductive, tempting",
                                "negative": "innocent"
                            },
                            "submissive": {
                                "name": "Submissive",
                                "prompt": "submissive, yielding",
                                "negative": "dominant"
                            },
                            "dominant": {
                                "name": "Dominant",
                                "prompt": "dominant, controlling",
                                "negative": "submissive"
                            },
                            "pain_pleasure": {
                                "name": "Pain and Pleasure",
                                "prompt": "pain and pleasure, masochistic",
                                "negative": "comfortable"
                            }
                        },
                        "male_features": {
                            "muscular": {
                                "name": "Muscular",
                                "prompt": "muscular, buff",
                                "negative": "slim, fat"
                            },
                            "average": {
                                "name": "Average",
                                "prompt": "average build",
                                "negative": "muscular"
                            },
                            "hairy": {
                                "name": "Hairy",
                                "prompt": "hairy, chest hair",
                                "negative": "smooth"
                            },
                            "slim": {
                                "name": "Slim",
                                "prompt": "slim, lean",
                                "negative": "muscular, fat"
                            },
                            "smooth": {
                                "name": "Smooth",
                                "prompt": "smooth, shaved",
                                "negative": "hairy"
                            }
                        },
                        "female_features": {
                            "large_breasts": {
                                "name": "Large Breasts",
                                "prompt": "large breasts, big chest",
                                "negative": "small chest"
                            },
                            "small_breasts": {
                                "name": "Small Breasts",
                                "prompt": "small breasts, petite chest",
                                "negative": "large chest"
                            },
                            "curvy": {
                                "name": "Curvy",
                                "prompt": "curvy, hourglass",
                                "negative": "slim"
                            },
                            "slim": {
                                "name": "Slim",
                                "prompt": "slim, slender",
                                "negative": "curvy"
                            },
                            "pear": {
                                "name": "Pear Shape",
                                "prompt": "pear shape, wide hips",
                                "negative": "hourglass"
                            }
                        }
                    },
                    "defaults": {
                        "pose": "missionary",
                        "intimacy": "lovemaking",
                        "view_angle": "profile_view",
                        "environment": "bedroom",
                        "clothing": "nude",
                        "emotion": "passionate_desire",
                        "male_features": "average",
                        "female_features": "curvy",
                        "width": 640,
                        "height": 896,
                        "steps": 20,
                        "cfg": 7.0
                    }
                }
            },
            "templates": {
                "romantic_bedroom": {
                    "pose": "missionary",
                    "intimacy": "lovemaking",
                    "view_angle": "profile_view",
                    "environment": "bedroom",
                    "clothing": "nude",
                    "emotion": "romantic_love",
                    "male_features": "average",
                    "female_features": "curvy",
                    "suffix": "romantic, soft lighting, intimate"
                },
                "passionate_bathroom": {
                    "pose": "standing_from_behind",
                    "intimacy": "hardcore",
                    "view_angle": "from_behind",
                    "environment": "bathroom",
                    "clothing": "nude",
                    "emotion": "passionate_desire",
                    "male_features": "muscular",
                    "female_features": "curvy",
                    "suffix": "steamy, wet, intense"
                },
                "car_adventure": {
                    "pose": "cowgirl",
                    "intimacy": "passionate",
                    "view_angle": "front_view",
                    "environment": "car",
                    "clothing": "partially_dressed",
                    "emotion": "seductive",
                    "male_features": "average",
                    "female_features": "slim",
                    "suffix": "risky, adventurous, cramped"
                },
                "bdsm_scene": {
                    "pose": "bent_over",
                    "intimacy": "bdsm",
                    "view_angle": "from_behind",
                    "environment": "bedroom",
                    "clothing": "lingerie",
                    "emotion": "dominant",
                    "male_features": "muscular",
                    "female_features": "curvy",
                    "suffix": "leather, bondage, power exchange"
                },
                "threesome": {
                    "pose": "missionary",
                    "intimacy": "group_sex",
                    "view_angle": "front_view",
                    "environment": "bedroom",
                    "clothing": "nude",
                    "emotion": "passionate_desire",
                    "male_features": "muscular",
                    "female_features": "curvy",
                    "suffix": "three bodies, multiple hands"
                },
                "beach_sunset": {
                    "pose": "spooning",
                    "intimacy": "tender",
                    "view_angle": "profile_view",
                    "environment": "beach",
                    "clothing": "nude",
                    "emotion": "romantic_love",
                    "male_features": "average",
                    "female_features": "slim",
                    "suffix": "golden sunset, ocean waves"
                },
                "office_forbidden": {
                    "pose": "bent_over",
                    "intimacy": "passionate",
                    "view_angle": "from_behind",
                    "environment": "office",
                    "clothing": "partially_dressed",
                    "emotion": "seductive",
                    "male_features": "smooth",
                    "female_features": "pear",
                    "suffix": "on desk, forbidden, risky"
                },
                "sixty_nine": {
                    "pose": "sixty_nine",
                    "intimacy": "lovemaking",
                    "view_angle": "profile_view",
                    "environment": "bedroom",
                    "clothing": "nude",
                    "emotion": "passionate_desire",
                    "male_features": "average",
                    "female_features": "curvy",
                    "suffix": "mutual pleasure, simultaneous"
                },
                "hardcore_from_behind": {
                    "pose": "standing_from_behind",
                    "intimacy": "hardcore",
                    "view_angle": "from_behind",
                    "environment": "bedroom",
                    "clothing": "nude",
                    "emotion": "passionate_desire",
                    "male_features": "muscular",
                    "female_features": "curvy",
                    "suffix": "deep penetration, intense"
                },
                "cowgirl_dominant": {
                    "pose": "cowgirl",
                    "intimacy": "passionate",
                    "view_angle": "front_view",
                    "environment": "bedroom",
                    "clothing": "nude",
                    "emotion": "dominant",
                    "male_features": "hairy",
                    "female_features": "slim",
                    "suffix": "woman on top, in control"
                }
            },
            "character_templates": {
                "chinese_qipao": {
                    "positive": "masterpiece, best quality, photorealistic, 8k, beautiful Chinese woman, wearing qipao, asian face, in garden, full body, natural lighting",
                    "negative": "worst quality, low quality, deformed, blurry, bad anatomy, watermark"
                },
                "japanese_kimono": {
                    "positive": "masterpiece, best quality, realistic, 8k, beautiful Japanese woman, wearing kimono, asian features, zen garden, cherry blossoms, full body, soft sunlight",
                    "negative": "worst quality, low quality, deformed, blurry, bad anatomy, watermark"
                },
                "korean_hanbok": {
                    "positive": "masterpiece, best quality, photorealistic, 8k, beautiful Korean woman, wearing hanbok, Korean palace background, full body, elegant",
                    "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy"
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
        quality = "masterpiece, best quality, realistic, 8k"

        # ✅ 亲密场景默认添加男人和女人
        base_subject = "man and woman, heterosexual couple"
    
        # ✅ 直接使用新键名，不做映射
        order = ["pose", "intimacy", "view_angle", "environment", "clothing", "emotion", "male_features", "female_features"]
        
        selected_parts = []
        seen = set()
        selected_count = 0
        max_selections = 5  # 限制数量，确保不超过 77 token
        
        for key in order:
            if selected_count >= max_selections:
                break
            if key in selections and selections[key]:
                value = selections[key].strip()
                if value and value not in seen:
                    seen.add(value)
                    if len(value) > 50:
                        value = value[:50]
                    selected_parts.append(value)
                    selected_count += 1
        
        # 自定义后缀
        custom_suffix = selections.get("suffix", "").strip()
        if custom_suffix and selected_count < max_selections:
            suffix_parts = custom_suffix.split(',')
            for part in suffix_parts[:2]:
                part = part.strip()
                if part and part not in seen and len(part) < 20:
                    selected_parts.append(part)
                    seen.add(part)
        
        if selected_parts:
            prompt = f"{quality}, {', '.join(selected_parts)}"
        else:
            prompt = quality
        
        # 最终长度限制
        if len(prompt) > 200:
            prompt = prompt[:200]
            last_comma = prompt.rfind(',')
            if last_comma > 100:
                prompt = prompt[:last_comma]
        
        negative = "worst quality, low quality, ugly, deformed, blurry, bad anatomy"
        
        return prompt, negative
    

    def get_template(self, template_name: str) -> Dict:
        """获取模板配置"""
        templates = self.scene_config.get("templates", {})
        template = templates.get(template_name, {})
        
        selections = {}
        # ✅ 使用新键名
        for key in ["pose", "intimacy", "view_angle", "environment", "clothing", "emotion", "male_features", "female_features"]:
            selections[key] = template.get(key, "")
        
        selections["suffix"] = template.get("suffix", "")
        return selections
    
    def get_all_templates(self) -> List[str]:
        """获取所有模板名称"""
        return list(self.scene_config.get("templates", {}).keys())
        
    def add_template(self, name: str, config: Dict):
        """添加模板 - 使用新格式"""
        if "templates" not in self.scene_config:
            self.scene_config["templates"] = {}
        
        # ✅ 如果传入的是旧格式（含 basic_pose, intimacy_level 等），转换为新格式
        new_config = {}
        
        # 新格式键名映射
        key_map = {
            "basic_pose": "pose",
            "intimacy_level": "intimacy",
            "view_angle": "view_angle",
            "environment": "environment",
            "clothing": "clothing",
            "emotion": "emotion",
            "body_features_man": "male_features",
            "body_features_woman": "female_features",
            "prompt_suffix": "suffix"
        }
        
        # 检查是旧格式还是新格式
        is_old_format = any(k in config for k in ["basic_pose", "intimacy_level", "prompt_suffix"])
        
        if is_old_format:
            # 旧格式 → 新格式转换
            for old_key, new_key in key_map.items():
                if old_key in config:
                    new_config[new_key] = config[old_key]
            # 保留其他字段
            for k, v in config.items():
                if k not in key_map:
                    new_config[k] = v
        else:
            # 已经是新格式，直接使用
            new_config = config
        
        self.scene_config["templates"][name] = new_config
        self.save_config()
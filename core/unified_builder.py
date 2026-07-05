#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一提示词构建器 - 融合原有 scene_patterns.json 和新框架
"""

import json
import os
from typing import Dict, List, Tuple


class UnifiedPromptBuilder:
    """统一提示词构建器"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.load_configs()
    
    def load_configs(self):
        """加载所有配置"""
        self.persons_config = self._load_json("templates/persons.json")
        self.scenes_config = self._load_json("templates/scenes.json")
        self.relationships_config = self._load_json("templates/relationships.json")
        
        old_scene_path = os.path.join(os.path.dirname(self.base_dir), "scene_patterns.json")
        if os.path.exists(old_scene_path):
            with open(old_scene_path, 'r', encoding='utf-8') as f:
                old_config = json.load(f)
            self.old_scene_config = old_config.get("scenes", {}).get("两人亲密场景", {})
        else:
            self.old_scene_config = {}
    
    def _load_json(self, path):
        full_path = os.path.join(self.base_dir, path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def build_couple_prompt_enhanced(self,
                                     person1: Dict,
                                     person2: Dict,
                                     scene_name: str = "两人亲密场景",
                                     selections: Dict = None) -> Tuple[str, str]:
        """
        增强版双人提示词构建 - 使用原有场景配置
        """
        prompt_parts = []
        negative_parts = []
        
        prompt_parts.append("masterpiece, best quality, 8k")
        
        p1_prompt, p1_neg = self._build_person_prompt(person1)
        p2_prompt, p2_neg = self._build_person_prompt(person2)
        
        if p1_prompt:
            prompt_parts.append(p1_prompt)
        if p2_prompt:
            prompt_parts.append(p2_prompt)
        
        if selections:
            categories = self.old_scene_config.get("categories", {})
            
            if "basic_pose" in selections:
                pose_key = selections["basic_pose"]
                pose_data = categories.get("基本姿势", {}).get(pose_key, {})
                if pose_data.get("prompt"):
                    prompt_parts.append(pose_data["prompt"])
                if pose_data.get("negative"):
                    negative_parts.append(pose_data["negative"])
            
            if "intimacy_level" in selections:
                intimacy_key = selections["intimacy_level"]
                intimacy_data = categories.get("亲密程度", {}).get(intimacy_key, {})
                if intimacy_data.get("prompt"):
                    prompt_parts.append(intimacy_data["prompt"])
            
            if "view_angle" in selections:
                angle_key = selections["view_angle"]
                angle_data = categories.get("视角", {}).get(angle_key, {})
                if angle_data.get("prompt"):
                    prompt_parts.append(angle_data["prompt"])
            
            if "environment" in selections:
                env_key = selections["environment"]
                env_data = categories.get("环境氛围", {}).get(env_key, {})
                if env_data.get("prompt"):
                    prompt_parts.append(env_data["prompt"])
            
            if "clothing" in selections:
                clothing_key = selections["clothing"]
                clothing_data = categories.get("服装状态", {}).get(clothing_key, {})
                if clothing_data.get("prompt"):
                    prompt_parts.append(clothing_data["prompt"])
            
            if "emotion" in selections:
                emotion_key = selections["emotion"]
                emotion_data = categories.get("情感表达", {}).get(emotion_key, {})
                if emotion_data.get("prompt"):
                    prompt_parts.append(emotion_data["prompt"])
        
        general_negative = "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, watermark, text, mutated hands"
        
        all_negative = general_negative
        if negative_parts:
            all_negative += ", " + ", ".join(negative_parts)
        
        if self.old_scene_config.get("默认配置"):
            default_neg = self.old_scene_config["默认配置"].get("negative_prompt", "")
            if default_neg:
                all_negative += ", " + default_neg
        
        full_prompt = ", ".join(prompt_parts)
        
        return full_prompt, all_negative
    
    def _build_person_prompt(self, person: Dict) -> Tuple[str, str]:
        """构建单个人物提示词"""
        parts = []
        
        age = person.get("age", "adult")
        age_config = self.persons_config.get("年龄", {}).get(age, {})
        if age_config.get("prompt"):
            parts.append(age_config["prompt"])
        
        gender = person.get("gender", "female")
        gender_config = self.persons_config.get("性别", {}).get(gender, {})
        if gender_config.get("prompt"):
            parts.append(gender_config["prompt"])
        
        ethnicity = person.get("ethnicity", "chinese")
        for cat in ["种族_亚洲", "种族_欧洲", "种族_美洲", "种族_非洲", "种族_中东"]:
            if ethnicity in self.persons_config.get(cat, {}):
                eth_config = self.persons_config[cat][ethnicity]
                if eth_config.get("prompt"):
                    parts.append(eth_config["prompt"])
                break
        
        clothing = person.get("clothing", "casual")
        clothing_config = self.persons_config.get("服装", {}).get(clothing, {})
        if clothing_config.get("prompt"):
            parts.append(clothing_config["prompt"])
        
        return ", ".join(parts), ""
    
    def get_old_scene_categories(self) -> Dict:
        """获取原有场景的所有分类选项"""
        return self.old_scene_config.get("categories", {})
    
    def get_old_templates(self) -> Dict:
        """获取原有场景的组合模板"""
        return self.old_scene_config.get("组合模板", {})


# 全局实例
unified_builder = UnifiedPromptBuilder()
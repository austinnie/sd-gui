#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
人物构建器 - 生成各种人物描述
支持: 不同年龄、性别、种族、体型、发型、发色、服装、表情、姿势、职业
"""

import json
import os
from typing import Dict, List, Optional, Tuple


class PersonBuilder:
    """人物构建器 - 生成单个人物的提示词"""
    
    def __init__(self, templates_path: str = None):
        if templates_path is None:
            templates_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
        self.templates_path = templates_path
        self.persons_config = self._load_config("persons.json")
        self.scenes_config = self._load_config("scenes.json")
    
    def _load_config(self, filename: str) -> dict:
        """加载配置文件"""
        path = os.path.join(self.templates_path, filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def get_all_options(self, category: str) -> List[str]:
        """获取某个分类的所有选项"""
        return list(self.persons_config.get(category, {}).keys())
    
    def build_person_prompt(self,
                            age: str = "adult",
                            gender: str = "female",
                            ethnicity: str = "chinese",
                            body_type: str = "slim",
                            hair_style: str = "long_straight",
                            hair_color: str = "black",
                            clothing: str = "casual",
                            expression: str = "happy",
                            pose: str = "standing",
                            profession: str = None,
                            custom_features: List[str] = None,
                            include_quality: bool = True) -> Tuple[str, str]:
        """
        构建单个人物的提示词
        
        参数:
            age: 年龄 (baby, child, boy, girl, teen, young_adult, adult, middle_aged, senior, elderly)
            gender: 性别 (male, female, non_binary)
            ethnicity: 种族/国籍 (chinese, japanese, korean, indian, british, russian, american, etc.)
            body_type: 体型 (slim, average, athletic, muscular, curvy, plus_size, skinny)
            hair_style: 发型
            hair_color: 发色
            clothing: 服装
            expression: 表情
            pose: 姿势
            profession: 职业/身份
            custom_features: 自定义特征列表
            include_quality: 是否包含质量词
        
        返回:
            (prompt, negative_prompt)
        """
        prompt_parts = []
        negative_parts = []
        
        # 基础质量
        if include_quality:
            prompt_parts.append("masterpiece, best quality, 8k, highly detailed")
        
        # 年龄
        age_config = self.persons_config.get("年龄", {}).get(age, {})
        if age_config.get("prompt"):
            prompt_parts.append(age_config["prompt"])
        if age_config.get("negative"):
            negative_parts.append(age_config["negative"])
        
        # 性别
        gender_config = self.persons_config.get("性别", {}).get(gender, {})
        if gender_config.get("prompt"):
            prompt_parts.append(gender_config["prompt"])
        if gender_config.get("negative"):
            negative_parts.append(gender_config["negative"])
        
        # 体型
        body_config = self.persons_config.get("体型", {}).get(body_type, {})
        if body_config.get("prompt"):
            prompt_parts.append(body_config["prompt"])
        if body_config.get("negative"):
            negative_parts.append(body_config["negative"])
        
        # 种族特征
        ethnicity_config = {}
        for category in ["种族_亚洲", "种族_欧洲", "种族_美洲", "种族_非洲", "种族_中东"]:
            if ethnicity in self.persons_config.get(category, {}):
                ethnicity_config = self.persons_config[category][ethnicity]
                break
        
        if ethnicity_config.get("prompt"):
            prompt_parts.append(ethnicity_config["prompt"])
        if ethnicity_config.get("negative"):
            negative_parts.append(ethnicity_config["negative"])
        
        # 发型
        hair_style_config = self.persons_config.get("发型", {}).get(hair_style, {})
        if hair_style_config.get("prompt"):
            prompt_parts.append(hair_style_config["prompt"])
        
        # 发色
        hair_color_config = self.persons_config.get("发色", {}).get(hair_color, {})
        if hair_color_config.get("prompt"):
            prompt_parts.append(hair_color_config["prompt"])
        
        # 服装
        clothing_config = self.persons_config.get("服装", {}).get(clothing, {})
        if clothing_config.get("prompt"):
            prompt_parts.append(clothing_config["prompt"])
        if clothing_config.get("negative"):
            negative_parts.append(clothing_config["negative"])
        
        # 表情
        expression_config = self.persons_config.get("表情", {}).get(expression, {})
        if expression_config.get("prompt"):
            prompt_parts.append(expression_config["prompt"])
        
        # 姿势
        pose_config = self.persons_config.get("姿势", {}).get(pose, {})
        if pose_config.get("prompt"):
            prompt_parts.append(pose_config["prompt"])
        
        # 职业
        if profession:
            prof_config = self.persons_config.get("职业/身份", {}).get(profession, {})
            if prof_config.get("prompt"):
                prompt_parts.append(prof_config["prompt"])
        
        # 自定义特征
        if custom_features:
            prompt_parts.extend(custom_features)
        
        # 完整提示词
        full_prompt = ", ".join(prompt_parts)
        
        # 通用负面提示词
        general_negative = "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, malformed limbs, missing arms, missing legs, watermark, text, mutated hands, fused fingers, too many fingers, bad hands, missing fingers, extra digits, bad feet, cropped, out of frame"
        
        all_negative = general_negative
        if negative_parts:
            all_negative += ", " + ", ".join(negative_parts)
        
        return full_prompt, all_negative
    
    def build_scene_prompt(self,
                           scene_type: str = "studio",
                           scene: str = "bedroom",
                           lighting: str = "soft",
                           quality: str = "photorealistic",
                           composition: str = "full_body") -> str:
        """构建场景提示词"""
        prompt_parts = []
        
        # 画质
        quality_config = self.scenes_config.get("画质", {}).get(quality, {})
        if quality_config.get("prompt"):
            prompt_parts.append(quality_config["prompt"])
        
        # 场景类型
        scene_type_config = self.scenes_config.get("场景类型", {}).get(scene_type, {})
        if scene_type_config.get("prompt"):
            prompt_parts.append(scene_type_config["prompt"])
        
        # 具体场景
        scene_config = self.scenes_config.get("具体场景", {}).get(scene, {})
        if scene_config.get("prompt"):
            prompt_parts.append(scene_config["prompt"])
        
        # 灯光
        lighting_config = self.scenes_config.get("灯光", {}).get(lighting, {})
        if lighting_config.get("prompt"):
            prompt_parts.append(lighting_config["prompt"])
        
        # 构图
        composition_config = self.scenes_config.get("构图", {}).get(composition, {})
        if composition_config.get("prompt"):
            prompt_parts.append(composition_config["prompt"])
        
        return ", ".join(prompt_parts)


class CoupleBuilder:
    """双人构建器 - 生成情侣/双人场景"""
    
    def __init__(self, templates_path: str = None):
        if templates_path is None:
            templates_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
        self.templates_path = templates_path
        self.relationships_config = self._load_config("relationships.json")
        self.scenes_config = self._load_config("scenes.json")
        self.person_builder = PersonBuilder(templates_path)
    
    def _load_config(self, filename: str) -> dict:
        path = os.path.join(self.templates_path, filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def build_couple_prompt(self,
                            person1_config: Dict,
                            person2_config: Dict,
                            relationship: str = "romantic",
                            pose: str = "standing_together",
                            intimacy: str = "romantic",
                            scene: str = "bedroom",
                            lighting: str = "warm",
                            quality: str = "photorealistic",
                            composition: str = "full_body",
                            custom_actions: List[str] = None) -> Tuple[str, str]:
        """
        构建双人场景提示词
        """
        prompt_parts = []
        negative_parts = []
        
        # 画质
        quality_config = self.scenes_config.get("画质", {}).get(quality, {})
        if quality_config.get("prompt"):
            prompt_parts.append(quality_config["prompt"])
        
        # 构图
        composition_config = self.scenes_config.get("构图", {}).get(composition, {})
        if composition_config.get("prompt"):
            prompt_parts.append(composition_config["prompt"])
        
        # 关系类型
        rel_type_config = self.relationships_config.get("关系类型", {}).get(relationship, {})
        if rel_type_config.get("prompt"):
            prompt_parts.append(rel_type_config["prompt"])
        
        # 亲密程度
        intimacy_config = self.relationships_config.get("亲密程度", {}).get(intimacy, {})
        if intimacy_config.get("prompt"):
            prompt_parts.append(intimacy_config["prompt"])
        if intimacy_config.get("negative"):
            negative_parts.append(intimacy_config["negative"])
        
        # 双人姿势
        pose_config = self.relationships_config.get("姿势_双人", {}).get(pose, {})
        if pose_config.get("prompt"):
            prompt_parts.append(pose_config["prompt"])
        
        # 场景
        scene_config = self.scenes_config.get("具体场景", {}).get(scene, {})
        if scene_config.get("prompt"):
            prompt_parts.append(scene_config["prompt"])
        
        # 灯光
        lighting_config = self.scenes_config.get("灯光", {}).get(lighting, {})
        if lighting_config.get("prompt"):
            prompt_parts.append(lighting_config["prompt"])
        
        # 构建两个人物的描述
        prompt1, neg1 = self.person_builder.build_person_prompt(include_quality=False, **person1_config)
        prompt2, neg2 = self.person_builder.build_person_prompt(include_quality=False, **person2_config)
        
        if neg1:
            negative_parts.append(neg1)
        if neg2:
            negative_parts.append(neg2)
        
        if prompt1:
            prompt_parts.append(prompt1)
        if prompt2:
            prompt_parts.append(prompt2)
        
        if custom_actions:
            prompt_parts.extend(custom_actions)
        
        full_prompt = ", ".join(prompt_parts)
        
        general_negative = "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, watermark, text, mutated hands, fused fingers"
        all_negative = general_negative
        if negative_parts:
            all_negative += ", " + ", ".join(negative_parts)
        
        return full_prompt, all_negative


class GroupBuilder:
    """多人构建器 - 生成多人场景"""
    
    def __init__(self, templates_path: str = None):
        if templates_path is None:
            templates_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
        self.templates_path = templates_path
        self.relationships_config = self._load_config("relationships.json")
        self.scenes_config = self._load_config("scenes.json")
        self.person_builder = PersonBuilder(templates_path)
    
    def _load_config(self, filename: str) -> dict:
        path = os.path.join(self.templates_path, filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def build_group_prompt(self,
                           persons_configs: List[Dict],
                           relationship: str = "family",
                           pose: str = "group_standing",
                           family_type: str = None,
                           scene: str = "park",
                           lighting: str = "natural",
                           quality: str = "photorealistic",
                           composition: str = "wide_shot") -> Tuple[str, str]:
        """
        构建多人场景提示词
        """
        prompt_parts = []
        negative_parts = []
        
        quality_config = self.scenes_config.get("画质", {}).get(quality, {})
        if quality_config.get("prompt"):
            prompt_parts.append(quality_config["prompt"])
        
        composition_config = self.scenes_config.get("构图", {}).get(composition, {})
        if composition_config.get("prompt"):
            prompt_parts.append(composition_config["prompt"])
        
        rel_type_config = self.relationships_config.get("关系类型", {}).get(relationship, {})
        if rel_type_config.get("prompt"):
            prompt_parts.append(rel_type_config["prompt"])
        
        if family_type:
            family_config = self.relationships_config.get("家庭关系", {}).get(family_type, {})
            if family_config.get("prompt"):
                prompt_parts.append(family_config["prompt"])
        
        pose_config = self.relationships_config.get("姿势_多人", {}).get(pose, {})
        if pose_config.get("prompt"):
            prompt_parts.append(pose_config["prompt"])
        
        scene_config = self.scenes_config.get("具体场景", {}).get(scene, {})
        if scene_config.get("prompt"):
            prompt_parts.append(scene_config["prompt"])
        
        lighting_config = self.scenes_config.get("灯光", {}).get(lighting, {})
        if lighting_config.get("prompt"):
            prompt_parts.append(lighting_config["prompt"])
        
        person_count = len(persons_configs)
        if person_count == 2:
            prompt_parts.append("two people")
        elif person_count == 3:
            prompt_parts.append("three people")
        elif person_count == 4:
            prompt_parts.append("four people")
        elif person_count > 4:
            prompt_parts.append(f"{person_count} people")
        
        full_prompt = ", ".join(prompt_parts)
        
        general_negative = "worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, watermark, text, mutated hands, fused fingers"
        
        return full_prompt, general_negative
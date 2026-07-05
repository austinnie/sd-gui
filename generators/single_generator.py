#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
单人生成器 - 生成单个人物的图片
"""

import sys
import os
from typing import Dict, Optional, Tuple

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.person_builder import PersonBuilder
from core.prompt_engine import prompt_engine


class SingleGenerator:
    """单人生成器"""
    
    def __init__(self, gui_instance=None):
        """
        初始化
        
        参数:
            gui_instance: GUI 实例（用于实际生成图片）
        """
        self.gui = gui_instance
        self.builder = PersonBuilder()
    
    def generate(self,
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
                scene: str = "studio",
                lighting: str = "soft",
                quality: str = "photorealistic",
                composition: str = "full_body",
                custom_features: list = None) -> Tuple[str, str]:
        """
        生成单个人物的提示词
        
        返回:
            (prompt, negative_prompt)
        """
        # 构建人物提示词
        prompt, negative = self.builder.build_person_prompt(
            age=age,
            gender=gender,
            ethnicity=ethnicity,
            body_type=body_type,
            hair_style=hair_style,
            hair_color=hair_color,
            clothing=clothing,
            expression=expression,
            pose=pose,
            profession=profession,
            custom_features=custom_features,
            include_quality=False
        )
        
        # 添加场景提示词
        scene_prompt = self.builder.build_scene_prompt(
            scene_type="studio" if scene == "studio" else "indoor",
            scene=scene,
            lighting=lighting,
            quality=quality,
            composition=composition
        )
        
        # 合并
        full_prompt = prompt_engine.combine_prompts([prompt, scene_prompt])
        
        # 添加基础质量
        full_prompt = prompt_engine.add_quality_tags(full_prompt, quality)
        
        # 优化
        full_prompt = prompt_engine.optimize_prompt(full_prompt)
        
        return full_prompt, negative
    
    def generate_all_ethnicities(self, gender: str = "female", output_callback=None):
        """生成所有种族的人物"""
        ethnicities = self.builder.get_all_options("种族_亚洲") + \
                      self.builder.get_all_options("种族_欧洲") + \
                      self.builder.get_all_options("种族_美洲") + \
                      self.builder.get_all_options("种族_非洲") + \
                      self.builder.get_all_options("种族_中东")
        
        results = []
        for ethnicity in ethnicities:
            prompt, negative = self.generate(
                age="adult",
                gender=gender,
                ethnicity=ethnicity,
                clothing="casual"
            )
            results.append({
                "ethnicity": ethnicity,
                "gender": gender,
                "prompt": prompt,
                "negative": negative
            })
            
            if output_callback:
                output_callback(f"✅ {gender}_{ethnicity}")
        
        return results
    
    def generate_all_ages(self, gender: str = "female", ethnicity: str = "chinese", output_callback=None):
        """生成所有年龄段的人物"""
        ages = self.builder.get_all_options("年龄")
        
        results = []
        for age in ages:
            prompt, negative = self.generate(
                age=age,
                gender=gender,
                ethnicity=ethnicity,
                clothing="casual"
            )
            results.append({
                "age": age,
                "gender": gender,
                "ethnicity": ethnicity,
                "prompt": prompt,
                "negative": negative
            })
            
            if output_callback:
                output_callback(f"✅ {ethnicity}_{gender}_{age}")
        
        return results


# 全局单人生成器实例
single_generator = SingleGenerator()
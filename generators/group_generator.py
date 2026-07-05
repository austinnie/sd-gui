#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多人生成器 - 生成多人场景的图片
"""

import sys
import os
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.person_builder import GroupBuilder
from core.prompt_engine import prompt_engine


class GroupGenerator:
    """多人生成器"""
    
    def __init__(self, gui_instance=None):
        self.gui = gui_instance
        self.builder = GroupBuilder()
    
    def generate(self,
                persons_configs: List[Dict],
                relationship: str = "family",
                family_type: str = None,
                pose: str = "group_standing",
                scene: str = "park",
                lighting: str = "natural",
                quality: str = "photorealistic",
                composition: str = "wide_shot") -> Tuple[str, str]:
        """
        生成多人场景提示词
        """
        prompt, negative = self.builder.build_group_prompt(
            persons_configs=persons_configs,
            relationship=relationship,
            family_type=family_type,
            pose=pose,
            scene=scene,
            lighting=lighting,
            quality=quality,
            composition=composition
        )
        
        prompt = prompt_engine.optimize_prompt(prompt)
        
        return prompt, negative
    
    def generate_family(self, ethnicity: str = "chinese", output_callback=None):
        """生成家庭照"""
        results = []
        
        # 核心家庭 (父母+两个孩子)
        prompt, negative = self.generate(
            persons_configs=[
                {"age": "adult", "gender": "male", "ethnicity": ethnicity},
                {"age": "adult", "gender": "female", "ethnicity": ethnicity},
                {"age": "child", "gender": "boy", "ethnicity": ethnicity},
                {"age": "child", "gender": "girl", "ethnicity": ethnicity}
            ],
            relationship="family",
            family_type="nuclear_family",
            scene="park"
        )
        results.append({
            "type": f"{ethnicity}_nuclear_family",
            "prompt": prompt,
            "negative": negative
        })
        
        # 三代同堂
        prompt2, negative2 = self.generate(
            persons_configs=[
                {"age": "elderly", "gender": "male", "ethnicity": ethnicity},
                {"age": "elderly", "gender": "female", "ethnicity": ethnicity},
                {"age": "adult", "gender": "male", "ethnicity": ethnicity},
                {"age": "adult", "gender": "female", "ethnicity": ethnicity},
                {"age": "child", "gender": "boy", "ethnicity": ethnicity},
                {"age": "child", "gender": "girl", "ethnicity": ethnicity}
            ],
            relationship="family",
            family_type="three_generations",
            scene="garden"
        )
        results.append({
            "type": f"{ethnicity}_three_generations",
            "prompt": prompt2,
            "negative": negative2
        })
        
        if output_callback:
            output_callback(f"✅ {ethnicity} family generated")
        
        return results


group_generator = GroupGenerator()
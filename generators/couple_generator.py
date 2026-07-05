#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
双人生成器 - 生成情侣/双人场景的图片
"""

import sys
import os
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.person_builder import CoupleBuilder
from core.prompt_engine import prompt_engine


class CoupleGenerator:
    """双人生成器"""
    
    def __init__(self, gui_instance=None):
        self.gui = gui_instance
        self.builder = CoupleBuilder()
    
    def generate(self,
                person1: Dict,
                person2: Dict,
                relationship: str = "couple",
                intimacy: str = "romantic",
                pose: str = "standing_together",
                scene: str = "bedroom",
                lighting: str = "warm",
                quality: str = "photorealistic",
                composition: str = "full_body",
                custom_actions: List[str] = None) -> Tuple[str, str]:
        """
        生成双人场景提示词
        """
        prompt, negative = self.builder.build_couple_prompt(
            person1_config=person1,
            person2_config=person2,
            relationship=relationship,
            intimacy=intimacy,
            pose=pose,
            scene=scene,
            lighting=lighting,
            quality=quality,
            composition=composition,
            custom_actions=custom_actions
        )
        
        # 优化
        prompt = prompt_engine.optimize_prompt(prompt)
        
        return prompt, negative
    
    def generate_cross_cultural_couples(self, output_callback=None):
        """生成跨文化情侣组合"""
        asian_ethnicities = ["chinese", "japanese", "korean"]
        western_ethnicities = ["british", "american", "russian", "french"]
        
        results = []
        
        for asian in asian_ethnicities:
            for western in western_ethnicities:
                # 亚洲女 + 西方男
                prompt1, neg1 = self.generate(
                    person1={"gender": "female", "ethnicity": asian, "age": "adult", "clothing": "elegant"},
                    person2={"gender": "male", "ethnicity": western, "age": "adult", "clothing": "formal"},
                    relationship="couple",
                    intimacy="romantic",
                    scene="restaurant"
                )
                results.append({
                    "type": f"{asian}_female_{western}_male",
                    "prompt": prompt1,
                    "negative": neg1
                })
                
                # 亚洲男 + 西方女
                prompt2, neg2 = self.generate(
                    person1={"gender": "male", "ethnicity": asian, "age": "adult", "clothing": "formal"},
                    person2={"gender": "female", "ethnicity": western, "age": "adult", "clothing": "elegant"},
                    relationship="couple",
                    intimacy="romantic",
                    scene="restaurant"
                )
                results.append({
                    "type": f"{asian}_male_{western}_female",
                    "prompt": prompt2,
                    "negative": neg2
                })
                
                if output_callback:
                    output_callback(f"✅ {asian} + {western}")
        
        return results


couple_generator = CoupleGenerator()
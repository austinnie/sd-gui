#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文生图批量 - 配置文件生成器
自动生成 txt2img_batch_config.json
保存位置: output/configs/txt2img_batch_config_时间戳.json
"""

import json
import os
import sys
import argparse
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.person_builder import PersonBuilder
from generators.single_generator import SingleGenerator


class Txt2ImgConfigGenerator:
    """文生图配置文件生成器 - 基于人物模板生成配置"""
    
    def __init__(self):
        # 将配置保存到 output/configs/ 下
        self.output_dir = os.path.join(os.path.dirname(__file__), "output", "configs")
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.single_gen = SingleGenerator()
        self.builder = PersonBuilder()
        self.results = {
            "single": [],
            "couple": [],
            "group": []
        }
    
    def run_single_batch(self, 
                         ethnicities: list = None,
                         genders: list = None,
                         ages: list = None) -> list:
        """生成单人配置"""
        if ethnicities is None:
            ethnicities = self.builder.get_all_options("种族_亚洲")[:5] + \
                         self.builder.get_all_options("种族_欧洲")[:3]
        
        if genders is None:
            genders = ["female", "male"]
        
        if ages is None:
            ages = ["young_adult", "adult", "middle_aged"]
        
        results = []
        for ethnicity in ethnicities:
            for gender in genders:
                for age in ages:
                    prompt, negative = self.single_gen.generate(
                        age=age,
                        gender=gender,
                        ethnicity=ethnicity,
                        clothing="casual",
                        quality="photorealistic"
                    )
                    
                    results.append({
                        "name": f"{ethnicity}_{gender}_{age}",
                        "prompt": prompt,
                        "negative": negative,
                        "width": 512,
                        "height": 768
                    })
        
        self.results["single"] = results
        return results
    
    def export_config(self, 
                      model_path: str = "../models/sd-v1-5/aiiiiii01_v10.safetensors",
                      cfg: float = 7.5,
                      steps: int = 25,
                      output_file: str = None) -> str:
        """导出为 txt2img_batch_config.json"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.output_dir, f"txt2img_batch_config_{timestamp}.json")
        
        config = {
            "model_path": model_path,
            "output_dir": "./output/batch_txt2img",
            "cfg": cfg,
            "steps": steps,
            "jobs": []
        }
        
        # 合并所有结果
        for item in self.results.get("single", []):
            config["jobs"].append(item)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 文生图配置已生成: {output_file}")
        print(f"   📊 共 {len(config['jobs'])} 个任务")
        print("\n📌 下一步运行命令:")
        print(f"   python batch_txt2img_generator.py -c {output_file}")
        return output_file


def main():
    parser = argparse.ArgumentParser(description="文生图批量 - 配置文件生成器")
    parser.add_argument("--output", type=str, default=None, help="输出文件名 (默认自动生成)")
    parser.add_argument("--model", type=str, 
                        default="../models/sd-v1-5/aiiiiii01_v10.safetensors", 
                        help="基础模型路径")
    parser.add_argument("--cfg", type=float, default=7.5, help="CFG Scale")
    parser.add_argument("--steps", type=int, default=25, help="推理步数")
    
    args = parser.parse_args()
    
    generator = Txt2ImgConfigGenerator()
    generator.run_single_batch()
    generator.export_config(
        model_path=args.model,
        cfg=args.cfg,
        steps=args.steps,
        output_file=args.output
    )


if __name__ == "__main__":
    main()
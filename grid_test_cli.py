# grid_test_cli.py - 命令行网格测试工具（完整版）
"""
功能对标 GUI 网格测试的命令行版本
支持 JSON 配置文件、SD/SDXL/Janus 模型、多维度测试
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from typing import Optional, List, Dict, Any

from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionXLPipeline,
    StableDiffusionInpaintPipeline,
    EulerDiscreteScheduler  # ✅ 添加
)

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
import gc
from diffusers import StableDiffusionPipeline


# ========== 模型扫描 ==========

def scan_models():
    """扫描 models 目录下的所有模型"""
    from config.app_config import app_config
    model_paths = app_config.paths.get_resolved_model_paths()
    
    models = {}
    # SD 1.5 模型
    if len(model_paths) > 0 and os.path.exists(model_paths[0]):
        for f in os.listdir(model_paths[0]):
            if f.endswith('.safetensors') or f.endswith('.ckpt'):
                models[f] = {"path": os.path.join(model_paths[0], f), "type": "sd", "subtype": "SD 1.5"}
    # SDXL 模型
    if len(model_paths) > 1 and os.path.exists(model_paths[1]):
        for f in os.listdir(model_paths[1]):
            if f.endswith('.safetensors') or f.endswith('.ckpt'):
                models[f] = {"path": os.path.join(model_paths[1], f), "type": "sd", "subtype": "SDXL"}
    return models


def list_models():
    """列出所有可用模型"""
    models = scan_models()
    if not models:
        print("⚠️ 未找到任何模型文件")
        return
    
    print("\n📦 可用模型列表:")
    print("-" * 70)
    print(f"  {'#':3} {'类型':8} {'名称':40} {'大小':10}")
    print("-" * 70)
    for i, (name, info) in enumerate(sorted(models.items()), 1):
        size_mb = os.path.getsize(info["path"]) // (1024 * 1024)
        type_label = info["subtype"]
        print(f"  {i:3} [{type_label:6}] {name[:38]:38} {size_mb:>6}MB")
    print("-" * 70)
    print(f"  共 {len(models)} 个模型\n")


def find_model(model_name: str) -> Optional[str]:
    """根据名称查找模型路径"""
    models = scan_models()
    for name, info in models.items():
        if name == model_name or name.startswith(model_name):
            return info["path"]
        if model_name in name:
            return info["path"]
    return None


# ========== 网格运行器 ==========

class GridRunnerCLI:
    """命令行网格测试运行器 - 支持 SD/SDXL/Janus"""
    
    def __init__(self):
        self.pipe = None
        self.model_type = "sd"
        self.is_running = False
        self.cancel = False
    
    def load_model(self, model_path: str, model_type: str = "sd"):
        """加载模型"""
        self.model_type = model_type
        
        if model_type == "janus":
            return self._load_janus_model()
        else:
            return self._load_sd_model(model_path)
    
    def _load_sd_model(self, model_path: str):
        """加载 SD/SDXL 模型"""
        if self.pipe is None:
            print(f"📦 加载 SD 模型: {os.path.basename(model_path)}")
            
            # 检测模型类型
            is_sdxl = "sdxl" in model_path.lower()
            
            self.pipe = StableDiffusionPipeline.from_single_file(
                model_path,
                torch_dtype=torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
                use_safetensors=True,
                low_cpu_mem_usage=True,
            )
            self.pipe = self.pipe.to("cpu")
            self.pipe.enable_vae_slicing()
            self.pipe.enable_attention_slicing()
            

            # ✅ 使用 EulerDiscreteScheduler
            self.pipe.scheduler = EulerDiscreteScheduler.from_config(self.pipe.scheduler.config)
            print("✅ 使用 EulerDiscreteScheduler (稳定调度器)")
        
            
            model_label = "SDXL" if is_sdxl else "SD 1.5"
            print(f"✅ {model_label} 模型加载完成")
        return self.pipe
    
    def _load_janus_model(self):
        """加载 Janus-Pro 模型"""
        from core.janus_loader import janus_loader
        
        if not janus_loader.is_loaded():
            print("📦 加载 Janus-Pro-1B 模型...")
            success = janus_loader.load(model_name="1B")
            if success:
                print("✅ Janus-Pro 模型加载完成")
                self.pipe = janus_loader.get_model()
                return self.pipe
            else:
                print("❌ Janus-Pro 模型加载失败")
                return None
        else:
            print("✅ Janus-Pro 模型已加载")
            self.pipe = janus_loader.get_model()
            return self.pipe
    
    def _generate_sd_one(self, params: Dict, seed_offset: int = 0):
        """生成单张 SD/SDXL 图片"""
        steps = params.get('steps', 25)
        cfg = params.get('cfg', 7.5)
        width = params.get('width', 512)
        height = params.get('height', 768)
        seed = params.get('seed', 42) + seed_offset
        hires = params.get('hires', False)
        prompt = params.get('prompt', 'masterpiece, best quality, highly detailed, a beautiful woman')
        negative = params.get('negative', 'worst quality, low quality, ugly, deformed, blurry')
        
        generator = torch.Generator("cpu").manual_seed(seed)
        
        if hires:
            # 高清修复：两阶段生成
            low_res_w = max(512, width // 2)
            low_res_h = max(512, height // 2)
            low_res_w = ((low_res_w + 31) // 64) * 64
            low_res_h = ((low_res_h + 31) // 64) * 64
            
            result = self.pipe(
                prompt=prompt,
                negative_prompt=negative,
                num_inference_steps=steps,
                guidance_scale=cfg,
                height=low_res_h,
                width=low_res_w,
                generator=generator,
            )
            low_img = result.images[0]
            
            generator2 = torch.Generator("cpu").manual_seed(seed + 1000)
            result = self.pipe(
                prompt=prompt,
                negative_prompt=negative,
                image=low_img,
                strength=0.4,
                num_inference_steps=steps,
                guidance_scale=cfg,
                height=height,
                width=width,
                generator=generator2,
            )
        else:
            result = self.pipe(
                prompt=prompt,
                negative_prompt=negative,
                num_inference_steps=steps,
                guidance_scale=cfg,
                height=height,
                width=width,
                generator=generator,
            )
        
        return result.images[0]
    
    def _generate_janus_one(self, params: Dict, seed_offset: int = 0):
        """生成单张 Janus 图片"""
        from core.janus_generator import janus_generator
        
        prompt = params.get('prompt', 'masterpiece, best quality, a beautiful woman')
        negative = params.get('negative', '')
        temperature = params.get('temperature', 0.8)
        max_tokens = params.get('max_tokens', 2048)
        seed = params.get('seed', 42) + seed_offset
        
        image, _ = janus_generator.generate(
            prompt=prompt,
            negative_prompt=negative,
            temperature=temperature,
            max_new_tokens=max_tokens,
            seed=seed
        )
        return image
    
    def generate_one(self, params: Dict, seed_offset: int = 0):
        """生成单张图片（自动判断模型类型）"""
        if self.model_type == "janus":
            return self._generate_janus_one(params, seed_offset)
        else:
            return self._generate_sd_one(params, seed_offset)
    
    def run_grid(self, config: Dict, progress_callback=None):
        """运行网格测试"""
        grid = config.get('grid', [])
        total = len(grid)
        
        # 加载模型（如果是 SD 类型，需要模型路径）
        model_type = config.get('model_type', 'sd')
        if model_type == "janus":
            self.load_model(None, "janus")
        else:
            model_path = config.get('model')
            if model_path:
                self.load_model(model_path, "sd")
        
        # 创建输出目录
        output_dir = config.get('output_dir', './output/grid_tests')
        os.makedirs(output_dir, exist_ok=True)
        
        # 全局默认值
        global_prompt = config.get('prompt', '')
        global_negative = config.get('negative', '')
        
        results = []
        self.is_running = True
        self.cancel = False
        
        for idx, item in enumerate(grid):
            if self.cancel:
                print("⏹️ 已取消")
                break
            
            name = item.get('name', f'组合_{idx+1}')
            params = item.get('params', {})
            
            # 合并全局提示词
            if 'prompt' not in params and global_prompt:
                params['prompt'] = global_prompt
            if 'negative' not in params and global_negative:
                params['negative'] = global_negative
            
            # 进度回调
            if progress_callback:
                progress_callback(idx + 1, total, name)
            
            print(f"\n[{idx+1}/{total}] {name}")
            print(f"  参数: {params}")
            
            try:
                start = time.time()
                image = self.generate_one(params, idx)
                
                # 保存
                filename = f"{idx+1:03d}_{name.replace(' ', '_')}.png"
                filepath = os.path.join(output_dir, filename)
                image.save(filepath)
                
                elapsed = time.time() - start
                print(f"  ✅ 完成! 耗时: {elapsed:.1f}秒")
                print(f"  💾 {filename}")
                
                results.append({
                    "name": name,
                    "params": params,
                    "file": filename,
                    "time": elapsed,
                    "success": True,
                })
                
            except Exception as e:
                print(f"  ❌ 失败: {e}")
                results.append({
                    "name": name,
                    "params": params,
                    "file": None,
                    "time": None,
                    "success": False,
                    "error": str(e),
                })
            
            gc.collect()
        
        self.is_running = False
        return results


# ========== 主函数 ==========

def load_config(config_path: str) -> Dict:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def print_config_info(config: Dict):
    """打印配置信息"""
    print("\n" + "=" * 60)
    print(f"📋 配置: {config.get('name', '未命名')}")
    print(f"   描述: {config.get('description', '无')}")
    print(f"   模型类型: {config.get('model_type', 'sd')}")
    print(f"   模型: {config.get('model', '未指定')}")
    print(f"   组合数: {len(config.get('grid', []))}")
    print("=" * 60)


def save_report(output_dir: str, config: Dict, results: List, model_path: str):
    """保存测试报告"""
    success = sum(1 for r in results if r.get('success', False))
    
    report = {
        "config": {
            "name": config.get('name', '未命名'),
            "model_type": config.get('model_type', 'sd'),
            "model": model_path,
        },
        "timestamp": datetime.now().isoformat(),
        "total": len(results),
        "success": success,
        "failed": len(results) - success,
        "results": results,
    }
    
    report_path = os.path.join(output_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 报告已保存: {report_path}")
    return report_path


def progress_callback(current, total, name):
    """进度回调"""
    percent = (current / total) * 100
    bar = "█" * int(percent // 2) + "░" * (50 - int(percent // 2))
    print(f"\r  进度: [{bar}] {percent:.1f}% ({current}/{total}) - {name}", end="")


def run_from_config(config_path: str, output_dir: Optional[str] = None, 
                    model_override: Optional[str] = None, interactive: bool = False,
                    quick: bool = False):
    """从配置文件运行测试"""
    
    # 加载配置
    config = load_config(config_path)
    print_config_info(config)
    
    # 覆盖模型路径
    if model_override:
        config['model'] = model_override
    
    # 交互式选择模型
    if interactive:
        model_path = select_model_interactive()
        if model_path:
            config['model'] = model_path
    
    # 快速模式：只取前几个组合
    if quick and len(config.get('grid', [])) > 5:
        config['grid'] = config['grid'][:5]
        print(f"⚡ 快速模式: 只测试前 5 个组合")
    
    # 覆盖输出目录
    if output_dir:
        config['output_dir'] = output_dir
    
    # 创建运行器
    runner = GridRunnerCLI()
    
    # 运行测试
    print(f"\n🚀 开始测试...")
    print(f"   输出目录: {config.get('output_dir', './output/grid_tests')}")
    print("-" * 60)
    
    results = runner.run_grid(config, progress_callback)
    
    # 保存报告
    output_dir_final = config.get('output_dir', './output/grid_tests')
    save_report(output_dir_final, config, results, config.get('model', 'unknown'))
    
    # 统计
    success = sum(1 for r in results if r.get('success', False))
    total = len(results)
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print(f"   ✅ 成功: {success}/{total}")
    print(f"   ❌ 失败: {total - success}/{total}")
    print(f"   📁 输出目录: {os.path.abspath(output_dir_final)}")
    print("=" * 60)
    
    # 自动打开文件夹
    try:
        if os.path.exists(output_dir_final):
            os.startfile(output_dir_final)
    except:
        pass


def create_template_config(output_dir: str = None):
    """创建配置模板"""
    if output_dir is None:
        output_dir = "grid_configs"
    os.makedirs(output_dir, exist_ok=True)
    
    template = {
        "name": "我的测试",
        "description": "描述这个测试的目的",
        "model_type": "sd",
        "model": "../models/sd-v1-5/aiiiiii01_v10.safetensors",
        "prompt": "masterpiece, best quality, highly detailed, sharp focus, a beautiful Asian woman, wearing elegant dress, full body shot, detailed face, natural lighting",
        "negative": "worst quality, low quality, ugly, deformed, blurry, bad anatomy, watermark, text, signature",
        "output_dir": "./output/grid_tests/my_test",
        "grid": [
            {
                "name": "标准参数",
                "params": {
                    "steps": 20,
                    "cfg": 7.5,
                    "width": 512,
                    "height": 768,
                    "seed": 42,
                    "hires": False
                }
            },
            {
                "name": "高细节",
                "params": {
                    "steps": 30,
                    "cfg": 8.0,
                    "width": 512,
                    "height": 768,
                    "seed": 43,
                    "hires": False
                }
            },
            {
                "name": "高清修复",
                "params": {
                    "steps": 25,
                    "cfg": 7.5,
                    "width": 512,
                    "height": 768,
                    "seed": 44,
                    "hires": True
                }
            },
            {
                "name": "大尺寸",
                "params": {
                    "steps": 25,
                    "cfg": 7.5,
                    "width": 640,
                    "height": 960,
                    "seed": 45,
                    "hires": False
                }
            }
        ]
    }
    
    filepath = os.path.join(output_dir, "template_config.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 配置模板已创建: {filepath}")
    return filepath


def find_config_files(config_dir: str = "grid_configs"):
    """查找所有配置文件"""
    if not os.path.exists(config_dir):
        return []
    
    files = []
    for f in os.listdir(config_dir):
        if f.endswith('.json'):
            files.append(os.path.join(config_dir, f))
    return sorted(files)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="命令行网格测试工具 - 功能对标 GUI 版本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用配置文件运行
  python grid_test_cli.py -c grid_configs/my_config.json

  # 快速模式（只测试前5个组合）
  python grid_test_cli.py -c grid_configs/my_config.json --quick

  # 交互式选择模型
  python grid_test_cli.py -c grid_configs/my_config.json --interactive

  # 指定输出目录
  python grid_test_cli.py -c grid_configs/my_config.json -o ./output/test

  # 列出所有模型
  python grid_test_cli.py --list

  # 创建配置模板
  python grid_test_cli.py --create-template
        """
    )
    
    parser.add_argument("-c", "--config", type=str, help="配置文件路径")
    parser.add_argument("-o", "--output", type=str, help="输出目录（覆盖配置文件中的设置）")
    parser.add_argument("-m", "--model", type=str, help="指定模型路径（覆盖配置文件中的设置）")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互式选择模型")
    parser.add_argument("--quick", "-q", action="store_true", help="快速模式（只测试前5个组合）")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有可用模型")
    parser.add_argument("--create-template", "-t", action="store_true", help="创建配置模板")
    parser.add_argument("--list-configs", action="store_true", help="列出所有配置文件")
    
    args = parser.parse_args()
    
    # 列出模型
    if args.list:
        list_models()
        return
    
    # 创建模板
    if args.create_template:
        create_template_config()
        return
    
    # 列出配置文件
    if args.list_configs:
        files = find_config_files()
        if files:
            print("\n📋 可用配置文件:")
            print("-" * 60)
            for f in files:
                try:
                    with open(f, 'r', encoding='utf-8') as file:
                        config = json.load(file)
                    name = config.get('name', '未命名')
                    grid_count = len(config.get('grid', []))
                    print(f"  {os.path.basename(f)}")
                    print(f"      名称: {name}, 组合数: {grid_count}")
                except:
                    print(f"  {os.path.basename(f)} (无法读取)")
            print("-" * 60)
        else:
            print("⚠️ 未找到配置文件，请先运行 --create-template 创建模板")
        return
    
    # 必须有配置文件
    if not args.config:
        print("❌ 请指定配置文件路径 (-c/--config)")
        print("   或使用 --create-template 创建模板")
        print("   或使用 --list-configs 查看可用配置文件")
        parser.print_help()
        return
    
    # 检查配置文件是否存在
    if not os.path.exists(args.config):
        print(f"❌ 配置文件不存在: {args.config}")
        return
    
    # 运行测试
    run_from_config(
        config_path=args.config,
        output_dir=args.output,
        model_override=args.model,
        interactive=args.interactive,
        quick=args.quick,
    )


if __name__ == "__main__":
    main()
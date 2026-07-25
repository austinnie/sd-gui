#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重绘强度批量测试工具
自动测试不同强度组合，找出最佳参数
"""

import os
import json
import time
import shutil
from datetime import datetime
from PIL import Image
from typing import List, Dict, Optional, Tuple
import torch
from diffusers import StableDiffusionImg2ImgPipeline, EulerDiscreteScheduler


from utils.logger import get_logger

logger = get_logger(__name__)
class StrengthTester:
    """重绘强度批量测试器"""
    
    def __init__(self, app=None):
        self.app = app
        self.results = []
        self.cancel = False
        
    def generate_test_configs(self, base_strength: float = 0.3) -> List[Dict]:
        """
        生成测试配置列表
        
        参数:
            base_strength: 基础强度，会围绕它生成多个测试值
        
        返回:
            测试配置列表
        """
        # 围绕基础强度生成测试值
        test_strengths = []
        
        # 精细测试（围绕基础值 ±0.2）
        for i in range(-4, 5):
            s = base_strength + i * 0.05
            if 0.15 <= s <= 0.80:  # 限制范围
                test_strengths.append(round(s, 2))
        
        # 如果基础值附近测试点不够，补充边界值
        if 0.15 not in test_strengths:
            test_strengths.append(0.15)
        if 0.80 not in test_strengths:
            test_strengths.append(0.80)
        
        test_strengths = sorted(set(test_strengths))
        
        configs = []
        for strength in test_strengths:
            # 根据强度自动调整步数
            if strength < 0.25:
                steps = 25
            elif strength < 0.40:
                steps = 30
            elif strength < 0.60:
                steps = 35
            else:
                steps = 40
            
            configs.append({
                "name": f"s{strength:.2f}_st{steps}",
                "strength": strength,
                "steps": steps,
                "cfg": 7.5,
                "seed": 42,
                "description": f"强度 {strength:.2f}, 步数 {steps}"
            })
        
        return configs
    
    def auto_detect_strength(self, image_path: str, prompt: str = "") -> float:
        """
        根据图片内容自动推荐强度
        
        参数:
            image_path: 图片路径
            prompt: 提示词（用于辅助判断）
        
        返回:
            推荐强度
        """
        try:
            img = Image.open(image_path)
            w, h = img.size
            
            # 1. 根据宽高比判断
            aspect_ratio = w / h
            
            if aspect_ratio > 1.5:
                # 横图（风景/多人）
                base_strength = 0.25
            elif aspect_ratio < 0.6:
                # 竖图（全身照）
                base_strength = 0.35
            else:
                # 方图/半身照
                base_strength = 0.30
            
            # 2. 根据提示词调整
            if prompt:
                prompt_lower = prompt.lower()
                if any(k in prompt_lower for k in ['nude', 'naked', '裸体', '去衣']):
                    base_strength += 0.15
                if any(k in prompt_lower for k in ['换衣', '换装', 'change clothes']):
                    base_strength += 0.05
                if any(k in prompt_lower for k in ['细节', 'detailed', '高清']):
                    base_strength -= 0.05
            
            # 限制范围
            return max(0.15, min(0.70, base_strength))
            
        except Exception as e:
            logger.info(f"⚠️ 自动检测强度失败: {e}")
            return 0.35
    
    def run_test(self, image_path: str, prompt: str, negative: str = "",
                 base_strength: Optional[float] = None,
                 output_dir: str = "./output/strength_tests",
                 progress_callback=None) -> Dict:
        """
        运行批量强度测试
        
        参数:
            image_path: 测试图片路径
            prompt: 正面提示词
            negative: 负面提示词
            base_strength: 基础强度（None 则自动检测）
            output_dir: 输出目录
            progress_callback: 进度回调
        
        返回:
            测试结果
        """
        self.cancel = False
        self.results = []
        
        # 自动检测基础强度
        if base_strength is None:
            base_strength = self.auto_detect_strength(image_path, prompt)
            logger.info(f"📊 自动检测基础强度: {base_strength:.2f}")
        
        # 生成测试配置
        configs = self.generate_test_configs(base_strength)
        total = len(configs)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🧪 批量强度测试")
        logger.info(f"   图片: {os.path.basename(image_path)}")
        logger.info(f"   基础强度: {base_strength:.2f}")
        logger.info(f"   测试数量: {total}")
        logger.info(f"{'='*60}\n")
        
        # 创建输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_dir = os.path.join(output_dir, f"test_{timestamp}")
        os.makedirs(test_dir, exist_ok=True)
        
        # 复制原图到测试目录
        shutil.copy2(image_path, os.path.join(test_dir, "original.png"))
        
        # 执行测试
        start_time = time.time()
        
        for idx, config in enumerate(configs):
            if self.cancel:
                logger.info(f"⏹️ 已取消")
                break
            
            if progress_callback:
                progress_callback(idx + 1, total, config["description"])
            
            logger.info(f"\n[{idx+1}/{total}] 测试: {config['description']}")
            
            result = self._test_single(
                image_path=image_path,
                prompt=prompt,
                negative=negative,
                config=config,
                output_dir=test_dir,
                index=idx
            )
            
            self.results.append(result)
            
            # 小间隔，避免内存问题
            time.sleep(0.5)
        
        elapsed = time.time() - start_time
        
        # 生成报告
        report = self._generate_report(test_dir, elapsed)
        
        print("\n" + "="*60)
        logger.info(f"✅ 测试完成！")
        logger.info(f"   耗时: {elapsed:.1f}秒")
        logger.info(f"   测试数: {len(self.results)}")
        logger.info(f"   输出目录: {test_dir}")
        print("="*60)
        
        return {
            "test_dir": test_dir,
            "results": self.results,
            "report": report,
            "elapsed": elapsed,
            "total": len(self.results)
        }
    
    def _test_single(self, image_path: str, prompt: str, negative: str,
                     config: Dict, output_dir: str, index: int) -> Dict:
        """测试单个强度配置"""
        
        # 检查是否有可用的 pipeline
        if self.app is None or self.app.pipeline is None:
            return {
                "config": config,
                "success": False,
                "error": "未加载模型",
                "filepath": None
            }
        
        try:
            pipe = self.app.pipeline
            
            # 重置调度器
            if hasattr(pipe, 'scheduler') and isinstance(pipe.scheduler, EulerDiscreteScheduler):
                pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
            
            # 加载图片
            init_image = Image.open(image_path).convert('RGB')
            
            # 尺寸处理
            w, h = init_image.size
            width = ((w + 31) // 64) * 64
            height = ((h + 31) // 64) * 64
            if w != width or h != height:
                init_image = init_image.resize((width, height), Image.Resampling.LANCZOS)
            
            # 生成
            generator = torch.Generator("cpu").manual_seed(config.get("seed", 42))
            
            result = pipe(
                prompt=prompt,
                negative_prompt=negative,
                image=init_image,
                strength=config["strength"],
                num_inference_steps=config["steps"],
                guidance_scale=config["cfg"],
                generator=generator,
            )
            
            # 保存图片
            filename = f"{index+1:02d}_{config['name']}.png"
            filepath = os.path.join(output_dir, filename)
            result.images[0].save(filepath)
            
            # 清理
            del result
            del generator
            
            return {
                "config": config,
                "success": True,
                "error": None,
                "filepath": filepath,
                "filename": filename
            }
            
        except Exception as e:
            logger.info(f"   ❌ 失败: {e}")
            return {
                "config": config,
                "success": False,
                "error": str(e),
                "filepath": None
            }
    
    def _generate_report(self, output_dir: str, elapsed: float) -> Dict:
        """生成测试报告"""
        # 统计
        success_count = sum(1 for r in self.results if r["success"])
        failed_count = len(self.results) - success_count
        
        # 找出最优配置（按成功率排序）
        best_configs = []
        for r in self.results:
            if r["success"]:
                best_configs.append({
                    "strength": r["config"]["strength"],
                    "steps": r["config"]["steps"],
                    "filepath": r["filepath"]
                })
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.results),
            "success_count": success_count,
            "failed_count": failed_count,
            "elapsed_seconds": elapsed,
            "best_configs": best_configs,
            "all_results": self.results
        }
        
        # 保存 JSON 报告
        report_path = os.path.join(output_dir, "report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 生成 HTML 报告
        html_path = os.path.join(output_dir, "report.html")
        self._generate_html_report(html_path, report)
        
        return report
    
    def _generate_html_report(self, html_path: str, report: Dict):
        """生成 HTML 报告"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>强度测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat {{ background: #e8f5e9; padding: 15px; border-radius: 8px; flex: 1; text-align: center; }}
        .stat .number {{ font-size: 28px; font-weight: bold; color: #2e7d32; }}
        .stat .label {{ font-size: 14px; color: #666; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; margin-top: 20px; }}
        .card {{ background: white; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .card img {{ width: 100%; height: auto; display: block; }}
        .card .info {{ padding: 10px; text-align: center; }}
        .card .info .strength {{ font-weight: bold; color: #333; }}
        .card .info .steps {{ color: #666; font-size: 12px; }}
        .success {{ border-color: #4CAF50; }}
        .failed {{ border-color: #f44336; opacity: 0.6; }}
        .best {{ border: 3px solid #ff9800; }}
        .recommend {{ background: #fff3e0; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ff9800; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 重绘强度测试报告</h1>
        <p>生成时间: {report['timestamp']}</p>
        
        <div class="stats">
            <div class="stat">
                <div class="number">{report['total_tests']}</div>
                <div class="label">总测试数</div>
            </div>
            <div class="stat">
                <div class="number">{report['success_count']}</div>
                <div class="label">成功</div>
            </div>
            <div class="stat">
                <div class="number">{report['failed_count']}</div>
                <div class="label">失败</div>
            </div>
            <div class="stat">
                <div class="number">{report['elapsed_seconds']:.1f}s</div>
                <div class="label">总耗时</div>
            </div>
        </div>
        
        <div class="recommend">
            <strong>💡 推荐配置</strong><br>
            根据测试结果，建议从以下配置开始尝试：
            <ul>
"""
        # 添加推荐配置
        best = report.get('best_configs', [])
        for i, cfg in enumerate(best[:5]):
            html += f"<li>强度 {cfg['strength']:.2f}, 步数 {cfg['steps']} - {cfg['filepath']}</li>"
        
        html += """
            </ul>
        </div>
        
        <h2>📊 测试结果</h2>
        <div class="grid">
"""
        
        # 添加所有图片
        for r in report.get('all_results', []):
            status_class = "success" if r["success"] else "failed"
            if r["success"] and r["filepath"]:
                filename = os.path.basename(r["filepath"])
                strength = r["config"]["strength"]
                steps = r["config"]["steps"]
                html += f"""
            <div class="card {status_class}">
                <img src="{filename}" alt="强度 {strength:.2f}" loading="lazy">
                <div class="info">
                    <div class="strength">强度: {strength:.2f}</div>
                    <div class="steps">步数: {steps}</div>
                </div>
            </div>
"""
            else:
                html += f"""
            <div class="card failed">
                <div class="info">
                    <div class="strength">❌ {r['config']['strength']:.2f}</div>
                    <div class="steps">失败</div>
                </div>
            </div>
"""
        
        html += """
        </div>
    </div>
</body>
</html>
"""
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"   📄 HTML 报告: {html_path}")
    
    def cancel_test(self):
        """取消测试"""
        self.cancel = True


# ==================== 便捷函数 ====================

def run_strength_test(app, image_path: str, prompt: str, negative: str = "",
                       base_strength: Optional[float] = None,
                       output_dir: str = "./output/strength_tests",
                       progress_callback=None) -> Dict:
    """
    便捷函数：运行强度测试
    
    参数:
        app: SDApp 实例
        image_path: 图片路径
        prompt: 正面提示词
        negative: 负面提示词
        base_strength: 基础强度（自动检测）
        output_dir: 输出目录
        progress_callback: 进度回调
    
    返回:
        测试结果
    """
    tester = StrengthTester(app)
    return tester.run_test(
        image_path=image_path,
        prompt=prompt,
        negative=negative,
        base_strength=base_strength,
        output_dir=output_dir,
        progress_callback=progress_callback
    )
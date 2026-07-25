# gui/tabs/lora_manager/analyzer.py
"""LoRA 分析器 - 扫描和分析 LoRA 文件"""

import os
import json
import torch
import gc
import shutil
import re
from collections import defaultdict
from datetime import datetime


class LoraAnalyzer:
    """LoRA 分析器"""
    
    def __init__(self, tab):
        self.tab = tab
        self.app = tab.app
        self.cancel_operation = False
    
    def analyze(self, image_dir: str, top_k: int = 30, progress_callback=None) -> tuple:
        """分析 LoRA 评分"""
        try:
            import open_clip
            from PIL import Image
            
            self.tab._append_analyze_log("📦 正在加载 CLIP 模型...")
            
            model, _, preprocess = open_clip.create_model_and_transforms(
                'ViT-B-32', pretrained='laion2b_s34b_b79k'
            )
            tokenizer = open_clip.get_tokenizer('ViT-B-32')
            
            positive_texts = [
                "a sexy woman", "a beautiful woman", "large breasts", 
                "seductive pose", "hot female"
            ]
            negative_texts = [
                "a man", "a boy", "a child", "ugly", "clothed in heavy coat"
            ]
            
            with torch.no_grad():
                pos_tokens = tokenizer(positive_texts)
                pos_embeddings = model.encode_text(pos_tokens)
                pos_embeddings /= pos_embeddings.norm(dim=-1, keepdim=True)
                positive_score = pos_embeddings.mean(dim=0)
                
                neg_tokens = tokenizer(negative_texts)
                neg_embeddings = model.encode_text(neg_tokens)
                neg_embeddings /= neg_embeddings.norm(dim=-1, keepdim=True)
                negative_score = neg_embeddings.mean(dim=0)
            
            self.tab._append_analyze_log(f"📁 扫描目录: {image_dir}")
            
            files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            total = len(files)
            
            lora_scores = defaultdict(list)
            
            for idx, filename in enumerate(files):
                if self.cancel_operation:
                    self.tab._append_analyze_log("⏹️ 已取消扫描")
                    break
                
                if progress_callback:
                    progress_callback((idx + 1) / total, f"扫描中 {idx+1}/{total}")
                
                try:
                    image_path = os.path.join(image_dir, filename)
                    image = preprocess(Image.open(image_path).convert('RGB')).unsqueeze(0)
                    
                    with torch.no_grad():
                        image_features = model.encode_image(image)
                        image_features /= image_features.norm(dim=-1, keepdim=True)
                        score = (image_features @ positive_score).item() - (image_features @ negative_score).item()
                        
                        lora_name = filename.split('_')[0] if '_' in filename else filename
                        lora_scores[lora_name].append(score)
                except Exception as e:
                    continue
            
            if self.cancel_operation:
                return [], []
            
            avg_scores = {k: sum(v)/len(v) for k, v in lora_scores.items()}
            sorted_loras = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)
            top_loras = [name for name, _ in sorted_loras[:top_k]]
            
            return sorted_loras, top_loras
            
        except Exception as e:
            self.tab._append_analyze_log(f"❌ 扫描失败: {e}")
            import traceback
            traceback.print_exc()
            return [], []
    
    def extract_high_loras(self, top_loras: list, image_dir: str, extract_dir: str, progress_callback=None) -> int:
        """提取高分 LoRA 图片"""
        try:
            os.makedirs(extract_dir, exist_ok=True)
            
            files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            copied = 0
            
            for idx, filename in enumerate(files):
                if self.cancel_operation:
                    break
                
                if progress_callback:
                    progress_callback((idx + 1) / len(files), f"提取中 {idx+1}/{len(files)}")
                
                candidate_name = filename.split('_')[0]
                if candidate_name in top_loras:
                    src = os.path.join(image_dir, filename)
                    dst = os.path.join(extract_dir, filename)
                    shutil.copy2(src, dst)
                    copied += 1
            
            return copied
            
        except Exception as e:
            self.tab._append_analyze_log(f"❌ 提取失败: {e}")
            return 0
    
    def filter_low_loras(self, top_loras: list, test_dir: str, progress_callback=None) -> int:
        """过滤低分 LoRA"""
        try:
            keep_names = set(top_loras)
            files = [f for f in os.listdir(test_dir) if f.endswith('.safetensors')]
            to_delete = []
            
            for filename in files:
                kept = False
                for name in keep_names:
                    if name in filename:
                        kept = True
                        break
                if not kept:
                    to_delete.append(filename)
            
            deleted = 0
            for idx, filename in enumerate(to_delete):
                if self.cancel_operation:
                    break
                
                if progress_callback:
                    progress_callback((idx + 1) / len(to_delete), f"删除中 {idx+1}/{len(to_delete)}")
                
                filepath = os.path.join(test_dir, filename)
                try:
                    os.remove(filepath)
                    deleted += 1
                    if idx % 5 == 0:
                        self.tab._append_analyze_log(f"   🗑️ 已删除: {filename}")
                except:
                    pass
            
            return deleted
            
        except Exception as e:
            self.tab._append_analyze_log(f"❌ 过滤失败: {e}")
            return 0
    
    def rename_loras(self, top_loras: list, test_dir: str, progress_callback=None) -> int:
        """重命名 LoRA"""
        try:
            files = [f for f in os.listdir(test_dir) if f.endswith('.safetensors')]
            renamed = 0
            
            for idx, target_name in enumerate(top_loras, 1):
                if self.cancel_operation:
                    break
                
                if progress_callback:
                    progress_callback(idx / len(top_loras), f"重命名 {idx}/{len(top_loras)}")
                
                clean_name = re.sub(r'[\\/*?:"<>|]', '_', target_name)
                new_filename = f"{idx:02d}_{clean_name}.safetensors"
                new_path = os.path.join(test_dir, new_filename)
                
                if os.path.exists(new_path):
                    continue
                
                found = False
                for old_filename in files:
                    if old_filename.startswith(f"{idx:02d}_"):
                        found = True
                        break
                    if target_name in old_filename:
                        old_path = os.path.join(test_dir, old_filename)
                        try:
                            os.rename(old_path, new_path)
                            renamed += 1
                            found = True
                            files.remove(old_filename)
                            self.tab._append_analyze_log(f"   ✅ [{idx:02d}] {old_filename} -> {new_filename}")
                            break
                        except:
                            pass
                
                if not found:
                    self.tab._append_analyze_log(f"   ⚠️ [{idx:02d}] 未找到匹配: {target_name}")
            
            return renamed
            
        except Exception as e:
            self.tab._append_analyze_log(f"❌ 重命名失败: {e}")
            return 0
    
    def sync_loras(self, test_dir: str, sd15_dir: str, sdxl_dir: str, progress_callback=None) -> tuple:
        """同步 LoRA 到对应目录"""
        try:
            os.makedirs(sd15_dir, exist_ok=True)
            os.makedirs(sdxl_dir, exist_ok=True)
            
            files = [f for f in os.listdir(test_dir) if f.endswith('.safetensors')]
            
            sd15_copied = 0
            sdxl_copied = 0
            unknown = 0
            
            for idx, filename in enumerate(files):
                if self.cancel_operation:
                    break
                
                if progress_callback:
                    progress_callback((idx + 1) / len(files), f"同步中 {idx+1}/{len(files)}")
                
                filepath = os.path.join(test_dir, filename)
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                
                if size_mb < 200:
                    dst_dir = sd15_dir
                    sd15_copied += 1
                elif size_mb >= 200:
                    dst_dir = sdxl_dir
                    sdxl_copied += 1
                else:
                    unknown += 1
                    continue
                
                dst_path = os.path.join(dst_dir, filename)
                if not os.path.exists(dst_path):
                    shutil.copy2(filepath, dst_path)
            
            return sd15_copied, sdxl_copied, unknown
            
        except Exception as e:
            self.tab._append_analyze_log(f"❌ 同步失败: {e}")
            return 0, 0, 0
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LoRA 图片性感度分析器 + 提取器
"""

import os
import shutil
import torch
from PIL import Image
import open_clip
from collections import defaultdict

# ==================== 配置 ====================
IMAGE_DIR = r"output/all_images"
OUTPUT_FILE = r"output/high_sex_lora_list.txt"
EXTRACT_DIR = r"output/selected_high_loras"  # 复制图片到此目录
TOP_K = 30  # 只复制前 30 个 LoRA 的图片
# ===============================================

def load_clip_model():
    print("📦 正在加载 CLIP 模型...")
    model, _, preprocess = open_clip.create_model_and_transforms(
        'ViT-B-32', pretrained='laion2b_s34b_b79k'
    )
    tokenizer = open_clip.get_tokenizer('ViT-B-32')
    return model, preprocess, tokenizer

def main():
    model, preprocess, tokenizer = load_clip_model()
    
    positive_texts = [
        "a sexy woman", "a beautiful woman", "large breasts", "seductive pose", "hot female"
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

    print(f"📁 扫描 {IMAGE_DIR} 中的图片...")
    files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    lora_scores = defaultdict(list)

    for filename in files:
        try:
            image_path = os.path.join(IMAGE_DIR, filename)
            image = preprocess(Image.open(image_path).convert('RGB')).unsqueeze(0)
            
            with torch.no_grad():
                image_features = model.encode_image(image)
                image_features /= image_features.norm(dim=-1, keepdim=True)
                
                score = (image_features @ positive_score).item() - (image_features @ negative_score).item()
                
                lora_name = filename.split('_')[0]
                lora_scores[lora_name].append(score)
        except Exception as e:
            continue

    avg_scores = {k: sum(v)/len(v) for k, v in lora_scores.items()}
    sorted_loras = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)
    top_loras = [name for name, _ in sorted_loras[:TOP_K]]

    # ==================== 保存名字列表 ====================
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("=== 高分 LoRA 排行 ===\n\n")
        for i, (lora, score) in enumerate(sorted_loras[:TOP_K], 1):
            f.write(f"{i:02d}. {lora} (评分: {score:.4f})\n")
            print(f"{i:02d}. {lora}")
    print(f"\n✅ 列表已保存到 {OUTPUT_FILE}")

    # ==================== 复制图片到单独目录 ====================
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    copied = 0
    for filename in files:
        # 取出前缀（LoRA 名字）
        candidate_name = filename.split('_')[0]
        if candidate_name in top_loras:
            src = os.path.join(IMAGE_DIR, filename)
            dst = os.path.join(EXTRACT_DIR, filename)
            shutil.copy2(src, dst)
            copied += 1
    
    print(f"\n🖼️ 已将前 {TOP_K} 个 LoRA 对应的 {copied} 张图片复制到:")
    print(f"   {EXTRACT_DIR}")
    print("\n✅ 所有操作完成！")

if __name__ == "__main__":
    main()
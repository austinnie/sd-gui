#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
利用现有 open_clip_torch 过滤高性感 LoRA
"""

import os
import torch
from PIL import Image
import open_clip

# ==================== 配置 ====================
IMAGE_DIR = r"output/all_images"  # 请确保这个路径正确
OUTPUT_FILE = r"output/high_sex_lora_list.txt"
TOP_K = 30
# ===============================================

def main():
    print("📦 正在加载现有的 CLIP 模型...")
    # 这行代码会直接调用您 venv 里的 open_clip_torch
    model, _, preprocess = open_clip.create_model_and_transforms(
        'ViT-B-32', pretrained='laion2b_s34b_b79k'
    )
    tokenizer = open_clip.get_tokenizer('ViT-B-32')
    
    positive_texts = ["a sexy woman", "a beautiful woman", "large breasts", "seductive pose"]
    negative_texts = ["a man", "a boy", "a child", "ugly", "clothed in heavy coat"]

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
    lora_scores = {}

    for filename in files:
        try:
            image_path = os.path.join(IMAGE_DIR, filename)
            image = preprocess(Image.open(image_path).convert('RGB')).unsqueeze(0)
            
            with torch.no_grad():
                image_features = model.encode_image(image)
                image_features /= image_features.norm(dim=-1, keepdim=True)
                
                score = (image_features @ positive_score).item() - (image_features @ negative_score).item()
                
                lora_name = filename.split('_')[0]
                if lora_name not in lora_scores:
                    lora_scores[lora_name] = []
                lora_scores[lora_name].append(score)
        except:
            continue

    avg_scores = {k: sum(v)/len(v) for k, v in lora_scores.items()}
    sorted_loras = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("=== 高分 LoRA 排行 ===\n\n")
        for i, (lora, score) in enumerate(sorted_loras[:TOP_K], 1):
            f.write(f"{i:02d}. {lora} (评分: {score:.4f})\n")
            print(f"{i:02d}. {lora}")

    print(f"\n✅ 完成！前 {TOP_K} 个 LoRA 已保存到 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
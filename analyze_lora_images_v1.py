#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LoRA 图片性感度分析器
读取 collect_images.py 生成的 all_images 目录，
用 AI 分析图片的“性感指数”，并过滤出高分的 LoRA。
"""

import os
import torch
from PIL import Image
import open_clip
from collections import defaultdict

# ==================== 配置 ====================
IMAGE_DIR = r"E:\SD_OpenVINO\v8_universal_generator\output\all_images"
OUTPUT_FILE = r"E:\SD_OpenVINO\v8_universal_generator\output\high_sex_lora_list.txt"
TOP_K = 30  # 只输出分数最高的前 30 个 LoRA
# ===============================================

def load_clip_model():
    """加载 CLIP 模型（通常在 CPU 上运行，大约占用 2GB 内存）"""
    print("📦 正在加载 CLIP 评分模型...")
    model, _, preprocess = open_clip.create_model_and_transforms(
        'ViT-B-32', pretrained='laion2b_s34b_b79k'
    )
    tokenizer = open_clip.get_tokenizer('ViT-B-32')
    return model, preprocess, tokenizer

def score_images_clip(image_dir, model, preprocess, tokenizer):
    """
    用 CLIP 给图片打分。
    通过对比图片与 "a sexy woman"、"a beautiful woman" 的相似度来打分。
    """
    model.eval()
    # 定义一组“正面”描述词，让模型寻找这些特征
    positive_texts = [
        "a sexy woman", 
        "a beautiful woman", 
        "large breasts", 
        "seductive pose",
        "hot female"
    ]
    
    # 定义一组“负面”描述词，用来排除不想要的
    negative_texts = [
        "a man", 
        "a boy", 
        "a child", 
        "ugly",
        "clothed in heavy coat"
    ]

    # 编码文本
    with torch.no_grad():
        pos_tokens = tokenizer(positive_texts)
        pos_embeddings = model.encode_text(pos_tokens)
        pos_embeddings /= pos_embeddings.norm(dim=-1, keepdim=True)
        positive_score = pos_embeddings.mean(dim=0)  # 取平均值作为“性感标准”

        neg_tokens = tokenizer(negative_texts)
        neg_embeddings = model.encode_text(neg_tokens)
        neg_embeddings /= neg_embeddings.norm(dim=-1, keepdim=True)
        negative_score = neg_embeddings.mean(dim=0)

    lora_scores = defaultdict(list)
    
    print(f"📁 开始扫描目录: {image_dir}")
    files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    for idx, filename in enumerate(files):
        if idx % 10 == 0:
            print(f"   ⏳ 已处理 {idx}/{len(files)} 张图片...")
            
        try:
            image_path = os.path.join(image_dir, filename)
            image = preprocess(Image.open(image_path).convert('RGB')).unsqueeze(0)
            
            with torch.no_grad():
                image_features = model.encode_image(image)
                image_features /= image_features.norm(dim=-1, keepdim=True)
                
                # 计算相似度
                similarity_pos = (image_features @ positive_score).item()
                similarity_neg = (image_features @ negative_score).item()
                
                # 综合得分 (越高越好)
                final_score = similarity_pos - similarity_neg
                
                # 提取文件名中的 LoRA 名字
                # 假设文件名格式为: LoRA名字_原文件名.png
                lora_name = filename.split('_')[0] if '_' in filename else filename
                
                lora_scores[lora_name].append(final_score)
                
        except Exception as e:
            # 跳过坏图片
            continue

    # 计算每个 LoRA 的平均分
    avg_scores = {k: sum(v)/len(v) for k, v in lora_scores.items()}
    
    # 按分数从高到低排序
    sorted_loras = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_loras

def save_results(sorted_loras, top_k=30):
    """保存最高分的 LoRA 名字到文件"""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("=== 性感/高分 LoRA 排行榜 ===\n\n")
        for i, (lora, score) in enumerate(sorted_loras[:top_k], 1):
            line = f"{i:02d}. {lora} (评分: {score:.4f})\n"
            print(line.strip())
            f.write(line)
    
    print(f"\n✅ 结果已保存至: {OUTPUT_FILE}")

if __name__ == "__main__":
    try:
        model, preprocess, tokenizer = load_clip_model()
        scores = score_images_clip(IMAGE_DIR, model, preprocess, tokenizer)
        save_results(scores, TOP_K)
    except Exception as e:
        print(f"❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\n按回车键退出...")
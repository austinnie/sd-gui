import os
import shutil
from pathlib import Path
from PIL import Image

def convert_webp_to_png(source_path, target_path):
    """
    将 WebP 转换为 PNG（保留透明背景，文件较大）
    """
    try:
        img = Image.open(source_path)
        
        # 处理透明通道
        if img.mode in ('RGBA', 'LA', 'P'):
            # 创建白色背景
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            if img.mode == 'RGBA':
                background.paste(img, mask=img.split()[-1])
            else:
                background.paste(img)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        img.save(target_path, 'PNG', optimize=True)
        return True
    except Exception as e:
        print(f"  ❌ PNG转换失败: {e}")
        return False

def convert_webp_to_jpg(source_path, target_path, quality=90):
    """
    将 WebP 转换为 JPG（文件更小，适合上传）
    quality: 图片质量 1-100，默认90
    """
    try:
        img = Image.open(source_path)
        
        # JPG 不支持透明通道，需要填充背景
        if img.mode in ('RGBA', 'LA', 'P'):
            # 创建白色背景
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            if img.mode == 'RGBA':
                background.paste(img, mask=img.split()[-1])
            else:
                background.paste(img)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        img.save(target_path, 'JPEG', quality=quality, optimize=True)
        return True
    except Exception as e:
        print(f"  ❌ JPG转换失败: {e}")
        return False

def collect_images(source_dir, target_dir, convert_format='jpg'):
    """
    收集并转换图片
    convert_format: 'jpg' 或 'png'，选择转换格式
    """
    # 支持的图片格式
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
    
    # 创建目标目录
    Path(target_dir).mkdir(parents=True, exist_ok=True)
    
    used_names = set()
    copied_count = 0
    converted_count = 0
    skip_count = 0
    
    # 根据选择的格式设置转换函数和扩展名
    if convert_format.lower() == 'png':
        convert_func = convert_webp_to_png
        new_ext = '.png'
        format_name = 'PNG'
    else:  # 默认 JPG
        convert_func = convert_webp_to_jpg
        new_ext = '.jpg'
        format_name = 'JPG'
    
    print(f"📌 转换格式: {format_name}")
    print("-" * 50)
    
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            ext = Path(file).suffix.lower()
            if ext in image_extensions:
                source_path = Path(root) / file
                
                # 获取相对路径
                rel_path = Path(root).relative_to(source_dir)
                if rel_path == Path('.'):
                    folder_name = ''
                else:
                    folder_name = '_'.join(rel_path.parts) + '_'
                
                # 处理扩展名
                if ext == '.webp':
                    # WebP 需要转换
                    final_ext = new_ext
                    is_webp = True
                else:
                    # 其他格式保持原扩展名
                    final_ext = ext
                    is_webp = False
                
                # 构造新文件名
                original_name = Path(file).stem
                new_filename = f"{folder_name}{original_name}{final_ext}"
                
                # 处理重名
                counter = 1
                final_filename = new_filename
                while final_filename in used_names:
                    final_filename = f"{folder_name}{original_name}_{counter}{final_ext}"
                    counter += 1
                
                used_names.add(final_filename)
                target_path = Path(target_dir) / final_filename
                
                # 复制或转换
                if is_webp:
                    print(f"🔄 转换: {file} -> {final_filename}")
                    if convert_func(source_path, target_path):
                        converted_count += 1
                        copied_count += 1
                    else:
                        skip_count += 1
                else:
                    shutil.copy2(source_path, target_path)
                    copied_count += 1
                    print(f"📄 复制: {file} -> {final_filename}")
    
    print("-" * 50)
    print(f"✅ 完成！")
    print(f"   - 共处理 {copied_count} 张图片")
    print(f"   - 其中转换 WebP: {converted_count} 张")
    print(f"   - 保存到: {target_dir}")
    return copied_count

if __name__ == "__main__":
    source = r"E:\SD_OpenVINO\v8_universal_generator\output\lora_previews"
    target = r"E:\SD_OpenVINO\v8_universal_generator\output\all_images"
    
    # 🎯 在这里选择转换格式
    # 选项1: 转 JPG（推荐，文件小，上传快）
    collect_images(source, target, convert_format='jpg')
    
    # 选项2: 转 PNG（保留透明背景，文件大）
    # collect_images(source, target, convert_format='png')
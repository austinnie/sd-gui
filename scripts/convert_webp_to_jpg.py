# scripts/convert_webp_to_jpg.py
import os
from PIL import Image

def convert_webp_to_jpg_safely(root_dir):
    print(f"🔍 正在扫描目录: {root_dir}")
    converted_count = 0
    skipped_count = 0

    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith('.webp'):
                webp_path = os.path.join(root, file)
                base_name = os.path.splitext(file)[0]
                
                # 默认目标：同名的 jpg
                jpg_path = os.path.join(root, base_name + '.jpg')
                
                # 🛡️ 安全检测：如果同名 JPG 已经存在，修改 WEBP 转换后的文件名！
                if os.path.exists(jpg_path):
                    jpg_path = os.path.join(root, base_name + '_webp.jpg')
                    print(f"   ⚠️ 发现同名 JPG，WEBP 将转为: {os.path.basename(jpg_path)}")

                try:
                    # 打开 WebP 并另存为 JPG
                    with Image.open(webp_path) as img:
                        # 确保是 RGB 模式 (否则保存会报错)
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        img.save(jpg_path, 'JPEG', quality=92)
                    
                    # 删除原 WebP 文件
                    os.remove(webp_path)
                    converted_count += 1
                    print(f"   ✅ 转换成功并删除原文件: {file}")
                except Exception as e:
                    print(f"   ❌ 转换失败: {webp_path} - 错误: {e}")

    print(f"\n✅ 全部完成！共转换了 {converted_count} 张 WebP 图片。")

if __name__ == "__main__":
    # 默认扫描 scripts 上一级目录下的 tools/output
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    output_root = os.path.join(project_root, "tools", "output")

    if not os.path.exists(output_root):
        print(f"❌ 未找到输出目录: {output_root}")
    else:
        convert_webp_to_jpg_safely(output_root)
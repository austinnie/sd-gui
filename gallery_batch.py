import os

# 这里列出你想要同时生成的画廊风格
STYLES = [
    "marble_statue",
    "bronze_statue",
    "golden_buddha",
    "jade_deer"
]

print("🎨 开始批量生成 AI 画廊系列...")
for style in STYLES:
    print(f"\n{'='*40}")
    print(f"🖼️ 生成: {style}")
    # 👇 注意这里的改动：前面加了 tools\
    os.system(f"python tools\\generate.py {style}")
print("\n✅ 画廊系列全部生成完毕！")
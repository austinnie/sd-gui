================================================================================
  通用人物生成器 v5 - Stable Diffusion 桌面GUI版
================================================================================

【项目简介】
基于 Stable Diffusion 的桌面 GUI 应用程序，集成通用人物生成器。
支持：文生图、图生图、图片反推、通用生成、批量生成等。

【主要功能】
  📝 文生图      - 标准文本生成图片
  🖼️ 图生图      - 基于图片生成新图片
  🔍 图片反推    - 从图片提取提示词（TAG/CLIP/BLIP/Combined）
  🌍 通用生成器  - 人物模板快速生成（单人/双人）
  📦 批量生成    - 批量生成各种人物组合配置

【环境要求】
  - Python 3.9 或更高版本
  - Windows 10/11（推荐）
  - 至少 8GB 内存（推荐 16GB）
  - 约 10GB 可用磁盘空间（含模型）

【快速开始】
  1. 双击 setup_env.bat 创建虚拟环境并安装依赖
  2. 将 SD 模型文件放到 models/ 目录
  3. 双击 run.bat 启动程序
  4. 在 GUI 中加载模型，开始生成

【手动安装】
  1. 创建虚拟环境:
     python -m venv venv
     venv\Scripts\activate

  2. 安装依赖:
     pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
     pip install diffusers transformers accelerate
     pip install opencv-python pillow psutil
     pip install clip-interrogator

  3. 启动程序:
     python main.py

【目录结构】
  v5_universal_generator/
  ├── main.py              - 程序入口
  ├── gui/                 - GUI 界面模块
  ├── config/              - 配置文件
  ├── core/                - 核心逻辑
  ├── generators/          - 生成器
  ├── templates/           - 人物/场景模板
  ├── utils/               - 工具函数
  ├── venv/                - 虚拟环境
  └── outputs/             - 图片输出目录

【配置文件】
  gui_config.json         - GUI 配置（模型路径、参数、内存优化）
  scene_patterns.json     - 场景模式配置
  templates/persons.json  - 人物模板
  templates/scenes.json   - 场景模板

【常用命令】
  python main.py                           - 启动 GUI
  python batch_generator.py --mode all    - 批量生成
  python collect.py                        - 收集项目文件（用于诊断）

【支持的反推后端】
  TAG       - 快速标签模式（ViT-Base/ViT-Large/CLIP-B-32）
  CLIP      - 详细风格标签（ViT-L-14）
  BLIP      - 自然语言描述（BLIP-base/BLIP-large）
  Combined  - BLIP + CLIP 组合模式

【注意事项】
  1. 模型文件放到 models/ 目录（SD 1.5 或 SDXL）
  2. 模型需 >= 2GB，程序会自动扫描
  3. CPU 模式速度较慢，建议使用 GPU
  4. 首次使用反推功能会自动下载模型（约 1-3GB）
  5. 重命名项目目录后，运行 auto_fix_venv.py 修复虚拟环境路径

【故障排除】
  - ModuleNotFoundError: 运行 pip install -r requirements.txt
  - 内存不足: gui_config.json 中启用 use_half_precision
  - VAE 尺寸错误: 确保图片尺寸是 64 的倍数
  - 虚拟环境路径错误: 运行 auto_fix_venv.py

【更新日志】
  v5 (2026-06-19)
  - 新增通用生成器（人物模板生成）
  - 新增 BLIP/CLIP 反推后端
  - 新增组合反推模式
  - 新增热重载模块功能
  - 新增虚拟环境路径自动修复工具
  - 新增提示词构造器
  - 优化水印去除功能

================================================================================
# Stable Diffusion 桌面GUI版

基于 Stable Diffusion 的桌面 GUI 应用程序，集成通用人物生成器。

---

## ✨ 主要功能

| 功能 | 说明 |
|------|------|
| 📝 文生图 | 标准文本生成图片 |
| 🖼️ 图生图 | 基于图片生成新图片 |
| 🔍 图片反推 | 从图片提取提示词（TAG/CLIP/BLIP/Combined/LLM） |
| 🌍 通用生成器 | 人物模板快速生成（单人/双人） |
| 💑 亲密文生图 | 快速生成两人亲密场景 |
| 🧪 网格测试 | 批量参数测试 |
| 🔧 流水线 | 风格转换步骤流水线 |
| 💬 智能生图 | AI 对话式生图 |
| 🔧 LoRA 管理 | LoRA 批量测试、分析、管理 |

---

## 📋 环境要求

- **Python**: 3.9 或更高版本
- **系统**: Windows 10/11（推荐）
- **内存**: 至少 8GB（推荐 16GB）
- **磁盘**: 约 10GB 可用空间（含模型）

---

## 🚀 快速开始

### 方式一：自动安装

```bash
# 1. 运行环境安装脚本
python scripts/env_setup.py

# 2. 将 SD 模型文件放到 models/ 目录

# 3. 启动程序
python main.py
```

### 方式二：手动安装

```bash
# 1. 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 将 SD 模型文件放到 models/ 目录

# 4. 启动程序
python main.py
```

---

## 📁 目录结构

```
sd_gui/
├── main.py              # 程序入口
├── gui/                 # GUI 界面模块
│   ├── app.py           # 主应用程序
│   ├── tabs/            # 标签页
│   ├── chat/            # 智能会话
│   └── components/      # UI 组件
├── core/                # 核心逻辑
│   ├── pipeline/        # 流水线处理
│   ├── janus/           # Janus-Pro 模型
│   └── ...
├── config/              # 配置模块
├── utils/               # 工具函数
│   └── controlnet/      # ControlNet 模块
├── services/            # 服务模块
├── scripts/             # 工具脚本
├── data/                # 数据文件
│   ├── configs/         # 配置文件
│   └── templates/       # 提示词模板
├── models/              # SD 模型文件
└── output/              # 图片输出目录
```

---

## ⚙️ 配置文件

| 文件 | 说明 |
|------|------|
| `data/configs/gui_config.json` | GUI 配置（模型路径、参数、内存优化） |
| `data/configs/nsfw_config.json` | NSFW 内容控制配置 |
| `data/configs/scene_patterns.json` | 场景模式配置 |
| `data/templates/persons.json` | 人物模板 |
| `data/templates/scenes.json` | 场景模板 |

---

## 🔍 支持的反推后端

| 后端 | 说明 |
|------|------|
| TAG | 快速标签模式（ViT-Base/ViT-Large/CLIP-B-32） |
| CLIP | 详细风格标签（ViT-L-14） |
| BLIP | 自然语言描述（BLIP-base/BLIP-large） |
| Combined | BLIP + CLIP 组合模式 |
| LLM | BLIP + LLM 增强模式 |

---

## 📝 常用命令

```bash
# 启动 GUI
python main.py

# 环境检测
python scripts/env_check.py

# ControlNet 环境检测
python scripts/env_check_controlnet_simple.py

# 项目打包
python scripts/code_package.py

# 收集项目文件（诊断用）
python scripts/code_collect.py
```

---

## ⚠️ 注意事项

1. **模型文件**：放到 `models/` 目录（支持 SD 1.5 或 SDXL）
2. **模型大小**：需 >= 2GB，程序会自动扫描
3. **CPU 模式**：速度较慢，建议使用 GPU
4. **首次使用**：反推功能会自动下载模型（约 1-3GB）
5. **内存**：如果内存不足，可在 `gui_config.json` 中启用 `use_half_precision`

---

## 🐛 故障排除

| 问题 | 解决方案 |
|------|----------|
| ModuleNotFoundError | `pip install -r requirements.txt` |
| 内存不足 | `gui_config.json` 中启用 `use_half_precision` |
| VAE 尺寸错误 | 确保图片尺寸是 64 的倍数 |
| ControlNet 加载失败 | 运行 `python scripts/env_check_controlnet_simple.py` |

---

## 📜 更新日志

### v8 (2026-07-26)

- 重构 ControlNet 模块，支持中文路径
- 新增强制重载功能，支持资源清理
- 优化内存管理，修复内存泄漏
- 新增图片后期处理（水印去除、EXIF 注入、照片真实化）
- 流水线支持完整后期处理
- 修复唯美风格场景数显示

### v5 (2026-06-19)

- 新增通用生成器（人物模板生成）
- 新增 BLIP/CLIP 反推后端
- 新增组合反推模式
- 新增热重载模块功能
- 新增提示词构造器
- 优化水印去除功能

---

## 📄 许可证

MIT License

---

**Happy Generating! 🎨**
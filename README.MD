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




#更新版的说明

项目概览
这是一个基于 Stable Diffusion 的桌面 GUI 应用程序，集成通用人物生成器，支持文生图、图生图、图片反推、流水线风格转换、LoRA 管理、智能对话生图等多种功能。

一、GUI 模块 (gui/)

1.1 主应用 (gui/app.py)
功能	说明
模型管理	加载/切换 SD 1.5 / SDXL / Janus-Pro 模型（互斥加载）
LoRA 管理	加载/卸载 LoRA，显示兼容性状态
VAE 管理	加载/卸载 VAE 模型
内存监控	实时显示内存使用，支持手动清理
热重载	普通重载 + 强制重载（清理资源后重载）
状态栏	显示当前模型、内存、进度等信息

1.2 标签页 (gui/tabs/)
标签页	功能	文件
📝 文生图	输入提示词生成图片，支持模板、批量生成	txt2img/
🖼️ 图生图	基于上传图片修改，支持 ControlNet、遮罩编辑	img2img/
🔍 图片反推	从图片提取提示词（TAG/CLIP/BLIP/Combined/LLM）	interrogate/
🌍 通用生成器	单人/双人模板快速生成	universal_tab.py
💑 亲密文生图	快速生成两人亲密场景	scene_tab.py
🤖 Janus-Pro	图生文/文生图/对话（纯 CPU）	janus_tab.py
🧪 网格测试	批量参数组合测试	grid_test_tab.py
🔧 流水线	风格转换步骤流水线（50+ 风格）	pipeline_tab.py
🔧 LoRA 管理	LoRA 批量测试、分析、管理	lora_manager/
💬 智能生图	AI 对话式生图（Ollama + LLM）	chat_tab.py

1.3 聊天模块 (gui/chat/)
组件	功能
intent_analyzer.py	意图分析（文生图/图生图/对话）
llm_client.py	LLM 客户端（Ollama）
prompt_builder.py	提示词构建
context_manager.py	对话上下文管理
lora_manager.py	LoRA 管理
controlnet_manager.py	ControlNet 管理
handlers/	生成处理器（文生图/图生图/双人合成/对话）
ui/	聊天 UI

1.4 组件 (gui/components/)
组件	功能
memory_monitor.py	内存监控 + 自动清理
progress_bar.py	进度条
image_preview.py	图片预览
params_panel.py	共享参数面板（步数/CFG/尺寸/种子/调度器/水印去除/后期处理）
nsfw_panel.py	NSFW 内容控制
lora_info_viewer.py	LoRA 信息查看器
batch_panel.py	批量生成面板

二、核心模块 (core/)
模块	功能
person_builder.py	人物构建器（年龄/性别/种族/体型/发型/服装/表情/姿势）
prompt_engine.py	提示词引擎（组合/优化/添加质量标签）
nsfw_filter.py	NSFW 内容过滤
grid_runner.py	网格测试运行器（支持 SD + Janus）
unified_builder.py	统一提示词构建器

2.1 流水线 (core/pipeline/)
组件	功能
pipeline.py	流水线核心
step.py	步骤基类
runner.py	流水线运行器
batch_runner.py	批量流水线运行器
presets.py	内置流水线配置（50+ 风格）
base_step.py	风格转换步骤基类
scene_counter.py	场景数统计
steps/	50+ 风格转换步骤
支持的风格类别：

类别	风格示例
风格转换	水彩、水墨、素描、赛博朋克、蒸汽波、3D渲染
场景主题	海滩、森林、太空、古堡、婚纱
服装造型	洛丽塔、和服、晚礼服、复古、电影质感
多人场景	情侣水彩、情侣油画、家庭素描、朋友聚会、团队照片
宗教神话	道门仙人、画中仙水墨、金身佛像、唐三彩、敦煌壁画、瓷器、兵马俑
西方神系	奥林匹斯众神、希腊英雄、古希腊神庙、北欧神话、古罗马帝国、中世纪骑士
宗教神系	上帝造物主、天使天军、伊斯兰神圣、古埃及神话
印度神话	印度教三大主神、印度史诗、印度神庙、生殖崇拜
中国神话	中国上古神话、中国民间神话
古风汉服	古风汉服、赛博古风
雕像材质	大理石雕像、大理石瑜伽、青铜雕像

2.2 Janus-Pro (core/janus/)
组件	功能
loader.py	模型加载器
understand.py	图生文（图片理解）
generate.py	文生图（功能有限）
chat.py	文生文（对话）

三、配置模块 (config/)
文件	功能
app_config.py	应用配置（路径/生成参数/内存/UI/模型/Janus）
config_manager.py	统一配置管理器
config_loader.py	配置加载器（兼容旧 API）
nsfw_config.py	NSFW 配置
janus_config.py	Janus-Pro 配置
schema.py	配置 Schema 验证

四、工具模块 (utils/)
模块	功能
watermark_remover.py	水印去除
imagemeta_cleaner.py	元数据清理
exif_injector.py	EXIF 信息注入
photo_realistic.py	照片真实化（噪点/暗角/锐化）
image_post_processor.py	统一图片后期处理
scheduler_factory.py	调度器工厂
strength_tester.py	强度测试
pipeline_pool.py	Pipeline 池（复用）
vae_utils.py	VAE 工具
controlnet/	ControlNet 模块（单层/多层/预处理）
image_cache.py	图片缓存
module_discovery.py	模块发现
performance.py	性能监控
logger.py	日志系统

五、服务模块 (services/)
文件	功能
llm_service.py	LLM 服务（Ollama）
ollama_service.py	Ollama 服务（兼容旧接口）
prompt_template_service.py	提示词模板服务
cache_config.py	统一缓存配置

六、生成器 (generators/)
文件	功能
single_generator.py	单人生成器
couple_generator.py	双人生成器
group_generator.py	多人生成器

七、Tools 目录 (tools/)
7.1 核心文件
文件	功能
generate.py	通用生成器（支持图生图/文生图，分层+扁平提示词）
config.py	全局配置（模型/LoRA/采样器/消除AI痕迹）
prompts_config.py	提示词配置加载器

7.2 提示词库 (prompts/ + prompts_new/)
类别	风格示例
每日壁纸	清纯、性感、古风、赛博朋克、婚纱、骑士
动漫	动漫爱爱（40场景）、赛璐璐风格
国风	水墨、白描、敦煌、汉服、旗袍
自然场景	海滩、森林、太空、古堡、极光、黄道十二宫
机甲	白模机甲、高达、变形金刚、攻壳机动队
线稿	老虎、龙、仙鹤、锦鲤、十二生肖
世界艺术	齐白石、唐伯虎、印度细密画、波斯细密画、日本浮世绘春宫图
中国神话	道教仙人、金身佛像、敦煌飞天、山海经异兽
西方神话	奥林匹斯众神、北欧神话、古埃及神话
奢侈品	珠宝、名表、跑车、包包

7.3 辅助脚本
文件	功能
photo_to_sketch.py	图片转素描
pre_resize.py	图片缩小器
anime_figure_generate.py	动漫手办生成
gallery_batch.py	画廊批量生成

八、脚本工具 (scripts/)
文件	功能
code_collect.py	项目文件收集（诊断用）
code_package.py	项目打包
env_check.py	环境检测
env_check_controlnet_simple.py	ControlNet 环境检测
env_setup.py	环境安装
model_index.py	模型索引生成
lora_index.py	LoRA 索引生成
switch_model.py	模型切换工具
switch_lora.py	LoRA 切换工具
organize_output.py	输出目录整理
convert_webp_to_jpg.py	WebP 转 JPG
test_import.py	导入测试

九、功能总览表
功能	说明	入口
文生图	输入提示词生成图片	GUI 文生图标签页
图生图	上传图片修改	GUI 图生图标签页
图片反推	从图片提取提示词	GUI 反推标签页
通用生成器	人物模板快速生成	GUI 通用生成器标签页
亲密文生图	两人亲密场景	GUI 亲密文生图标签页
Janus-Pro	图生文/文生图/对话	GUI Janus-Pro 标签页
网格测试	批量参数测试	GUI 网格测试标签页
流水线	50+ 风格转换	GUI 流水线标签页
LoRA 管理	批量测试/分析	GUI LoRA 管理标签页
智能生图	AI 对话式生图	GUI 智能生图标签页
CLI 生成	命令行快速生成	tools/generate.py
模型管理	加载/切换 SD/SDXL/Janus	主界面状态栏
LoRA 加载	加载/卸载 LoRA	主界面 LoRA 选择器
内存监控	实时监控 + 清理	主界面状态栏
热重载	普通/强制重载	主界面重载按钮

代码和 模型放在同一级别目录 （代码有配置文件，可以改配置文件来使用不同的sd、sdxl模型，以及lora模型）

E:\SD_OpenVINO\models
2026/08/05  22:50    <DIR>          .
2026/08/11  20:58    <DIR>          ..
2026/07/13  07:43    <DIR>          all_lora
2026/07/30  12:04    <DIR>          codeformer
2026/08/06  00:00    <DIR>          exiftool-13.59_64
2026/08/05  22:50        11,183,675 exiftool-13.59_64.zip
2026/07/30  11:24    <DIR>          gfpgan
2026/06/21  17:18    <DIR>          janus
2026/07/13  07:30            11,975 organize_lora.py
2026/08/07  19:42    <DIR>          sd-v1-5
2026/08/05  22:33    <DIR>          sd-v1-5-ov-int8
2026/08/07  22:33    <DIR>          sd15-lora
2026/07/03  14:25    <DIR>          sdxl
2026/07/13  08:06    <DIR>          sdxl-lora
2026/07/04  22:35    <DIR>          test_lora
2026/07/08  05:32    <DIR>          vae

新增tools，独立于GUI，非常强大（支持文生图，图生图，模型选择，各种参数指定，请结合ollama+LLM自动生成描述词，并生成word文件，插入图片+描述，可以直接发表到微信公众号）

(venv) E:\SD_OpenVINO\v8_universal_generator>python tools\generate.py gallery_elegant_safe --img2img --steps 20 -n 5
📁 PROJECT_ROOT: E:\SD_OpenVINO\v8_universal_generator
20:44:17 [INFO] logger - 📁 日志目录: logs
20:44:17 [INFO] logger - 📄 日志文件: logs\app_20260811.log
20:44:17 [INFO] logger - 📊 日志级别: INFO
20:44:17 [INFO] config.app_config - ✅ 已加载配置: data/configs/gui_config.json
20:44:17 [INFO] config.app_config -
📁 解析后的路径:
20:44:17 [INFO] config.app_config -    Janus 1B: E:\SD_OpenVINO\models\janus\janus-pro-1b
20:44:17 [INFO] config.app_config -    Janus 7B: E:\SD_OpenVINO\models\janus\janus-pro-7b
20:44:17 [INFO] config.app_config -    输出目录: E:\SD_OpenVINO\v8_universal_generator\output

20:44:17 [INFO] config.nsfw_config - ✅ NSFW 配置已加载: 等级=safe
20:44:17 [INFO] config.janus_config - ✅ 已加载 Janus 配置: data/configs/janus_config.json
20:44:17 [INFO] config.janus_config -
📁 Janus 配置路径:
20:44:17 [INFO] config.janus_config -    Janus 1B: E:\SD_OpenVINO\models\janus\janus-pro-1b
20:44:17 [INFO] config.janus_config -    Janus 7B: E:\SD_OpenVINO\models\janus\janus-pro-7b
20:44:17 [INFO] config.janus_config -    输出目录: E:\SD_OpenVINO\v8_universal_generator\output\janus
E:\SD_OpenVINO\v8_universal_generator\venv\Lib\site-packages\diffusers\utils\outputs.py:63: FutureWarning: `torch.utils._pytree._register_pytree_node` is deprecated. Please use `torch.utils._pytree.register_pytree_node` instead.
  torch.utils._pytree._register_pytree_node(
E:\SD_OpenVINO\v8_universal_generator\venv\Lib\site-packages\diffusers\utils\outputs.py:63: FutureWarning: `torch.utils._pytree._register_pytree_node` is deprecated. Please use `torch.utils._pytree.register_pytree_node` instead.
  torch.utils._pytree._register_pytree_node(
E:\SD_OpenVINO\v8_universal_generator\venv\Lib\site-packages\huggingface_hub\file_download.py:1150: FutureWarning: `resume_download` is deprecated and will be removed in version 1.0.0. Downloads always resume when possible. If you want to force a new download, use `force_download=True`.
  warnings.warn(

🤖 智能推荐: anytimeRealistic_v10 (1.99GB, 标签: realistic)
🎨 采样器类型: DPM++ 2M Karras
🔄 推荐步数: 20

╔═══════════════════════════════════════════════╗
║  📦 模型配置信息                              ║
╠═══════════════════════════════════════════════╣
║  模式: smart
║  模型: anytimeRealistic_v10.safetensors
║  大小: 1.99 GB
║  标签: realistic
║  OpenVINO: False
║  可用模型: 22 个
║  LoRA 激活: 1 个
╚═══════════════════════════════════════════════╝

📊 STEPS = 25
📷 AI_CAMERA = sony_a7iv

🛡️ [安全模式] 默认只加载安全的新版提示词库 (prompts_new)...

✅ 已加载新版提示词: 56 个

🎯 系统最终合并加载了 56 个可用风格。
ℹ️ 消除AI痕迹已启用 (相机: sony_a7iv, 强度: light)

[AI预处理] 检测并去除图片水印...
⚠️ 检测到水印，正在使用 OpenCV 修复去除...
✅ 水印去除完成！

[系统] 正在加载 AI 模型...
⚡ [配置] 使用普通模型模式
   📂 模型路径: E:\SD_OpenVINO\models\sd-v1-5\anytimeRealistic_v10.safetensors
✅ 普通模型加载成功！
   📦 准备加载 1 个 LoRA...
      🔗 加载 LoRA 1: MechaGirlFigure_v1.safetensors (权重: 0.7)
      ✅ 全部 1 个 LoRA 加载成功！
   🎛️ 正在加载采样器: DPM++ 2M Karras...
   ✅ 采样器加载完成！
[系统] 模型管道已就绪！

🎯 正在生成风格: gallery_elegant_safe -> 优雅画廊_知性清纯
📊 模式: 分层 (13×3×1=39种组合)
📊 本次共生成 5 张图片（用户指定）
   ├─ 主体: 13 种
   ├─ 风格: 3 种
   └─ 情绪: 1 种
   └─ 💡 注: 从 39 种组合中随机选 5 张
⚙️ 步数: 命令行指定为 20 步
📁 已创建子文件夹: 0001 (存放第 1 - 5 张)

📊 共 5 张图片，将分到 1 个子文件夹中（每 5 张一组）

生成进度:   0%|                                                                                       | 0/5 [00:00<?, ?it/s]
🔄 进度：第 1/5 张 [分层] → 子文件夹 0001
   📁 [追踪 1] 调用 generate_style 前，目标路径: E:\SD_OpenVINO\v8_universal_generator\tools\output\优雅画廊_知性清纯_20260811_204456\0001\gallery_elegant_safe_01.png

==================================================
📊 [调试] 参数详情:
  ├─ 图生图强度 (strength): 0.35
  ├─ 照片真实化强度 (AI_STRENGTH): light
  ├─ 紫边模拟强度 (AI_CHROMATIC_STRENGTH): 0.05
  ├─ 消除AI痕迹 (REMOVE_AI_TRACES): True
  └─ 迭代步数 (steps): 20
==================================================

[图生图] gallery_elegant_safe_01.png (448x768)
🛡️ [安全模式] 策略: 过滤 (移除露骨词汇)
   🧠 已添加解剖约束: natural body position, correct anatomy, realistic hands and feet
[20:44:56] 提示词: a stunning Canadian woman, wearing a cream stretch lace blouse, posing in an art...
  步数: 20
100%|███████████████████████████████████████████████████████████████████████████████████████| 20/20 [10:19<00:00, 30.96s/it]
📷 消除AI痕迹处理...████████████████████████████████████████████████████████████████████████| 20/20 [10:19<00:00, 36.61s/it]
20:55:40 [INFO] utils.imagemeta_cleaner - ✅ [方法2] 已转换为 JPG，元数据已清除: E:\SD_OpenVINO\v8_universal_generator\tools\output\优雅画廊_知性清纯_20260811_204456\0001\gallery_elegant_safe_01.jpg
   ✅ 元数据已清除 -> JPG
20:55:40 [INFO] utils.photo_realistic - 📷 真实化处理: ISO=200, F=2.8, 焦距=50mm
20:55:40 [INFO] utils.photo_realistic -    📷 添加暗角
20:55:41 [INFO] utils.photo_realistic -    📷 添加镜头畸变 (焦距 50mm -> 强度 0.0050)
20:55:41 [INFO] utils.photo_realistic -    📷 添加锐化
20:55:41 [INFO] utils.photo_realistic - ✅ 图片已保存: E:\SD_OpenVINO\v8_universal_generator\tools\output\优雅画廊_知性清纯_20260811_204456\0001\gallery_elegant_safe_01.jpg

生成进度:  20%|███████████████▌                                                              | 1/5 [11:46<47:07, 706.93s/it]Token indices sequence length is longer than the specified maximum sequence length for this model (86 > 77). Running this sequence through the model will result in indexing errors
The following part of your input was truncated because CLIP can only handle sequences up to 77 tokens: ['position, correct anatomy, realistic hands and feet']
   ✅ 照片真实化完成 (强度: light)
   🔬 模拟紫边...
      ✅ 紫边模拟完成 (强度: 0.05)
   ✂️ 轻微裁剪...
      ✅ 轻微裁剪完成 (裁切: 0.5%, 位置: 1,3)
   📝 已生成提示词记录: gallery_elegant_safe_01.txt
   ✅ [追踪 2] generate_style 返回的路径 (initial): E:\SD_OpenVINO\v8_universal_generator\tools\output\优雅画廊_知性清纯_20260811_204456\0001\gallery_elegant_safe_01.jpg
   ✅ [追踪 2] 备份路径 (saved_img_file): E:\SD_OpenVINO\v8_universal_generator\tools\output\优雅画廊_知性清纯_20260811_204456\0001\gallery_elegant_safe_01.jpg
   🧠 鉴赏引擎: 正在加载 llm 后端...
   🔍 [追踪 3] 即将传递给后端进行推理的图片路径: E:\SD_OpenVINO\v8_universal_generator\tools\output\优雅画廊_知性清纯_20260811_204456\0001\gallery_elegant_safe_01.jpg
   🧠 鉴赏引擎: 使用本地目录加载 BLIP + Ollama 润色
   📦 首次使用，正在加载 BLIP 模型 (E:\hf_cache\.cache\hub\models--Salesforce--blip-image-captioning-large\snapshots\353689b859fcf0523410b1806dace5fb46ecdf41)...
   ✅ BLIP 模型加载完成！
   📝 BLIP 基础描述: sexy woman in white lingerie posing in front of a painting...
   ⏳ 正在请求 Ollama (qwen2.5:1.5b) 润色...
   ✅ LLM 润色完成！
   ✅ llm 后端推理完成
   🛡️ [终极绝对防御] 路径严重偏离正常输出目录！强制重定向！
   ✅ [已重定向] 新路径: E:\SD_OpenVINO\v8_universal_generator\tools\output\优雅画廊_知性清纯_20260811_204456\0001

🔄 进度：第 2/5 张 [分层] → 子文件夹 0001
   📁 [追踪 1] 调用 generate_style 前，目标路径: E:\SD_OpenVINO\v8_universal_generator\tools\output\优雅画廊_知性清纯_20260811_204456\0001\gallery_elegant_safe_02.png

==================================================
📊 [调试] 参数详情:
  ├─ 图生图强度 (strength): 0.35
  ├─ 照片真实化强度 (AI_STRENGTH): light
  ├─ 紫边模拟强度 (AI_CHROMATIC_STRENGTH): 0.05
  ├─ 消除AI痕迹 (REMOVE_AI_TRACES): True
  └─ 迭代步数 (steps): 20
==================================================

[图生图] gallery_elegant_safe_02.png (448x768)
🛡️ [安全模式] 策略: 过滤 (移除露骨词汇)
   🧠 已添加解剖约束: natural body position, correct anatomy, realistic hands and feet
[20:56:43] 提示词: a stunning Japanese woman, long straight hair, wearing a semi-sheer white floral...
  步数: 20
100%|███████████████████████████████████████████████████████████████████████████████████████| 20/20 [14:54<00:00, 44.73s/it]
📷 消除AI痕迹处理...████████████████████████████████████████████████████████████████████████| 20/20 [14:54<00:00, 80.17s/it]
21:12:12 [INFO] utils.imagemeta_cleaner - ✅ [方法2] 已转换为 JPG，元数据已清除: E:\SD_OpenVINO\v8_universal_generator\tools\output\优雅画廊_知性清纯_20260811_204456\0001\gallery_elegant_safe_02.jpg
   ✅ 元数据已清除 -> JPG
21:12:12 [INFO] utils.photo_realistic - 📷 真实化处理: ISO=200, F=2.8, 焦距=50mm
21:12:12 [INFO] utils.photo_realistic -    📷 添加暗角
21:12:13 [INFO] utils.photo_realistic -    📷 添加镜头畸变 (焦距 50mm -> 强度 0.0050)
21:12:13 [INFO] utils.photo_realistic -    📷 添加锐化
21:12:13 [INFO] utils.photo_realistic - ✅ 图片已保存: E:\SD_OpenVINO\v8_universal_generator\tools\output\优雅画廊_知性清纯_20260811_204456\0001\gallery_elegant_safe_02.jpg

生成进度:  40%|███████████████████████████████▏                                              | 2/5 [28:16<43:39, 873.07s/it]The following part of your input was truncated because CLIP can only handle sequences up to 77 tokens: ['natural body position, correct anatomy, realistic hands and feet']
   ✅ 照片真实化完成 (强度: light)
   🔬 模拟紫边...
      ✅ 紫边模拟完成 (强度: 0.05)
   ✂️ 轻微裁剪...
      ✅ 轻微裁剪完成 (裁切: 0.4%, 位置: 1,2)
   📝 已生成提示词记录: gallery_elegant_safe_02.txt
   ✅ [追踪 2] generate_style 返回的路径 (initial): E:\SD_OpenVINO\v8_universal_generator\tools\output\优雅画廊_知性清纯_20260811_204456\0001\gallery_elegant_safe_02.jpg
   ✅ [追踪 2] 备份路径 (saved_img_file): E:\SD_OpenVINO\v8_universal_generator\tools\output\优雅画廊_知性清纯_20260811_204456\0001\gallery_elegant_safe_02.jpg
   🧠 鉴赏引擎: 正在加载 llm 后端...
   🔍 [追踪 3] 即将传递给后端进行推理的图片路径: E:\SD_OpenVINO\v8_universal_generator\tools\output\优雅画廊_知性清纯_20260811_204456\0001\gallery_elegant_safe_02.jpg
   🧠 鉴赏引擎: 使用本地目录加载 BLIP + Ollama 润色
   📝 BLIP 基础描述: there is a woman with long black hair standing in front of a...
   ⏳ 正在请求 Ollama (qwen2.5:1.5b) 润色...
   ✅ LLM 润色完成！
   ✅ llm 后端推理完成

🔄 进度：第 3/5 张 [分层] → 子文件夹 0001
   📁 [追踪 1] 调用 generate_style 前，目标路径: E:\SD_OpenVINO\v8_universal_generator\tools\output\优雅画廊_知性清纯_20260811_204456\0001\gallery_elegant_safe_03.png

==================================================
📊 [调试] 参数详情:
  ├─ 图生图强度 (strength): 0.35
  ├─ 照片真实化强度 (AI_STRENGTH): light
  ├─ 紫边模拟强度 (AI_CHROMATIC_STRENGTH): 0.05
  ├─ 消除AI痕迹 (REMOVE_AI_TRACES): True
  └─ 迭代步数 (steps): 20
==================================================

[图生图] gallery_elegant_safe_03.png (448x768)
🛡️ [安全模式] 策略: 过滤 (移除露骨词汇)
   🧠 已添加解剖约束: natural body position, correct anatomy, realistic hands and feet
[21:13:12] 提示词: a pure Chinese girl with wavy black hair, wearing a white lace knit short-sleeve...
  步数: 20
100%|███████████████████████████████████████████████████████████████████████████████████████| 20/20 [14:30<00:00, 43.51s/it]
📷 消除AI痕迹处理...████████████████████████████████████████████████████████████████████████| 20/20 [14:30<00:00, 53.88s/it]
21:28:22 [INFO] utils.imagemeta_cleaner - ✅ [方法2] 已转换为 JPG，元数据已清除: E:\SD_OpenVINO\v8_universal_generator\tools\output\优雅画廊_知性清纯_20260811_204456\0001\gallery_elegant_safe_03.jpg
   ✅ 元数据已清除 -> JPG
21:28:22 [INFO] utils.photo_realistic - 📷 真实化处理: ISO=200, F=2.8, 焦距=50mm
21:28:22 [INFO] utils.photo_realistic -    📷 添加暗角
21:28:23 [INFO] utils.photo_realistic -    📷 添加镜头畸变 (焦距 50mm -> 强度 0.0050)
21:28:23 [INFO] utils.photo_realistic -    📷 添加锐化
21:28:23 [INFO] utils.photo_realistic - ✅ 图片已保存: E:\SD_OpenVINO\v8_universal_generator\tools\output\优雅画廊_知性清纯_20260811_204456\0001\gallery_elegant_safe_03.jpg

生成进度:  60%|██████████████████████████████████████████████▊                               | 3/5 [44:42<30:49, 924.58s/it]   ✅ 照片真实化完成 (强度: light)
   🔬 模拟紫边...
      ✅ 紫边模拟完成 (强度: 0.05)
   ✂️ 轻微裁剪...
      ✅ 轻微裁剪完成 (裁切: 0.3%, 位置: 3,1)
   📝 已生成提示词记录: gallery_elegant_safe_03.txt
   ✅ [追踪 2] generate_style 返回的路径 (initial): E:\SD_OpenVINO\v8_universal_generator\tools\output\优雅画廊_知性清纯_20260811_204456\0001\gallery_elegant_safe_03.jpg
   ✅ [追踪 2] 备份路径 (saved_img_file): E:\SD_OpenVINO\v8_universal_generator\tools\output\优雅画廊_知性清纯_20260811_204456\0001\gallery_elegant_safe_03.jpg
   🧠 鉴赏引擎: 正在加载 llm 后端...
   🔍 [追踪 3] 即将传递给后端进行推理的图片路径: E:\SD_OpenVINO\v8_universal_generator\tools\output\优雅画廊_知性清纯_20260811_204456\0001\gallery_elegant_safe_03.jpg
   🧠 鉴赏引擎: 使用本地目录加载 BLIP + Ollama 润色
   📝 BLIP 基础描述: asian woman in white top and white pants posing for a pictur...
   ⏳ 正在请求 Ollama (qwen2.5:1.5b) 润色...
   ✅ LLM 润色完成！
   ✅ llm 后端推理完成

🔄 进度：第 4/5 张 [分层] → 子文件夹 0001
   📁 [追踪 1] 调用 generate_style 前，目标路径: E:\SD_OpenVINO\v8_universal_generator\tools\output\优雅画廊_知性清纯_20260811_204456\0001\gallery_elegant_safe_04.png

==================================================
📊 [调试] 参数详情:
  ├─ 图生图强度 (strength): 0.35
  ├─ 照片真实化强度 (AI_STRENGTH): light
  ├─ 紫边模拟强度 (AI_CHROMATIC_STRENGTH): 0.05
  ├─ 消除AI痕迹 (REMOVE_AI_TRACES): True
  └─ 迭代步数 (steps): 20
==================================================

[图生图] gallery_elegant_safe_04.png (448x768)
🛡️ [安全模式] 策略: 过滤 (移除露骨词汇)
[21:29:38] 提示词: a beautiful Korean girl with flawless skin, wearing a cream lace crop top and wh...
  步数: 20

最后产物是 图片+描述+word文档
E:\SD_OpenVINO\v8_universal_generator\tools\output\优雅画廊_知性清纯_精准复刻_20260811_172437\0001

2026/08/11  17:33    <DIR>          .
2026/08/11  17:24    <DIR>          ..
2026/08/11  17:28            68,701 gallery_elegant_safe_01.jpg
2026/08/11  17:28             1,364 gallery_elegant_safe_01.txt
2026/08/11  17:32            66,314 gallery_elegant_safe_02.jpg
2026/08/11  17:32             1,472 gallery_elegant_safe_02.txt
2026/08/11  17:33           172,817 公众号草稿.docx
2026/08/11  17:33             1,436 点评.txt


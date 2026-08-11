# Stable Diffusion 桌面GUI版 / 通用人物生成器

基于 Stable Diffusion 的桌面 GUI 应用程序，集成通用人物生成器，支持文生图、图生图、图片反推、流水线风格转换、LoRA 管理、智能对话生图等多种功能。


## 项目概览

项目位置: E:\SD_OpenVINO\v8_universal_generator

模型位置: E:\SD_OpenVINO\models\（与代码同级目录，通过配置文件切换不同模型）


## 环境要求

Python: 3.9 或更高版本
系统: Windows 10/11（推荐）
内存: 至少 8GB（推荐 16GB）
磁盘: 约 10GB 可用空间（含模型）


## 快速开始

创建虚拟环境:
python -m venv venv
venv\Scripts\activate

安装依赖:
pip install -r requirements.txt

启动 GUI:
python main.py

命令行工具:
python tools/generate.py <风格名称> [选项]

命令行示例:
python tools/generate.py gallery_elegant_safe --img2img --steps 20 -n 5

python tools/generate.py pure_serene --txt2img -n 3

python tools/generate.py mecha_blueprint --img2img --input my_photo.jpg -n 2

python tools/generate.py babata_poses --use-old -n 3


## 目录结构

```text
v8_universal_generator/
├── main.py
├── gui/
│   ├── app.py
│   ├── tabs/
│   ├── chat/
│   └── components/
├── core/
│   ├── pipeline/
│   ├── janus/
│   ├── person_builder.py
│   ├── prompt_engine.py
│   └── nsfw_filter.py
├── config/
│   ├── app_config.py
│   ├── config_manager.py
│   ├── nsfw_config.py
│   └── janus_config.py
├── utils/
│   ├── controlnet/
│   ├── watermark_remover.py
│   ├── imagemeta_cleaner.py
│   ├── exif_injector.py
│   ├── photo_realistic.py
│   └── pipeline_pool.py
├── services/
│   ├── llm_service.py
│   └── prompt_template_service.py
├── generators/
│   ├── single_generator.py
│   ├── couple_generator.py
│   └── group_generator.py
├── tools/
│   ├── generate.py
│   ├── config.py
│   ├── prompts_config.py
│   ├── prompts/
│   ├── prompts_new/
│   ├── photo_to_sketch.py
│   ├── pre_resize.py
│   └── output/
├── scripts/
│   ├── code_collect.py
│   ├── code_package.py
│   ├── env_check.py
│   ├── model_index.py
│   ├── lora_index.py
│   └── switch_model.py
├── data/
│   ├── configs/
│   └── templates/
└── output/
```


## GUI 模块

主应用 (gui/app.py):
- 模型管理: 加载/切换 SD 1.5 / SDXL / Janus-Pro 模型（互斥加载）
- LoRA 管理: 加载/卸载 LoRA，显示兼容性状态
- VAE 管理: 加载/卸载 VAE 模型
- 内存监控: 实时显示内存使用，支持手动清理
- 热重载: 普通重载 + 强制重载（清理资源后重载）
- 状态栏: 显示当前模型、内存、进度等信息

标签页 (gui/tabs/):
- 文生图: 标准文本生成图片，支持模板、批量生成
- 图生图: 基于图片生成新图片，支持 ControlNet、遮罩编辑
- 图片反推: 从图片提取提示词，支持 TAG/CLIP/BLIP/Combined/LLM
- 通用生成器: 人物模板快速生成，支持单人/双人
- 亲密文生图: 快速生成两人亲密场景
- Janus-Pro: 图生文/文生图/对话，纯 CPU 运行
- 网格测试: 批量参数组合测试，支持 SD + Janus
- 流水线: 风格转换步骤流水线（50+ 风格）
- LoRA 管理: LoRA 批量测试、分析、管理
- 智能生图: AI 对话式生图（Ollama + LLM）

聊天模块 (gui/chat/):
- intent_analyzer.py: 意图分析（文生图/图生图/对话）
- llm_client.py: LLM 客户端（Ollama）
- prompt_builder.py: 提示词构建
- context_manager.py: 对话上下文管理
- handlers/: 生成处理器（文生图/图生图/双人合成/对话）

UI 组件 (gui/components/):
- memory_monitor.py: 内存监控 + 自动清理
- params_panel.py: 共享参数面板（步数/CFG/尺寸/种子/调度器/水印去除/后期处理）
- nsfw_panel.py: NSFW 内容控制
- lora_info_viewer.py: LoRA 信息查看器
- batch_panel.py: 批量生成面板


## 命令行工具 (tools/)

核心文件:
- generate.py: 通用生成器（支持图生图/文生图，分层+扁平提示词，自动生成 Word 文档）
- config.py: 全局配置（模型/LoRA/采样器/消除AI痕迹）
- prompts_config.py: 提示词配置加载器

命令行选项:
- -n, --count: 生成数量
- --img2img, --i2i: 图生图模式（默认）
- --txt2img, --t2i: 文生图模式
- --steps: 迭代步数
- --input: 指定参考图路径
- --use-old: 使用旧版提示词库

输出产物:
- *.jpg: 生成的图片
- *.txt: 提示词记录
- 点评.txt: AI 鉴赏文字
- 公众号草稿.docx: 可直接导入公众号的 Word 文档（含图片 + 描述）

辅助脚本:
- photo_to_sketch.py: 图片转素描
- pre_resize.py: 图片缩小器
- anime_figure_generate.py: 动漫手办生成
- gallery_batch.py: 画廊批量生成


## 核心模块 (core/)

- person_builder.py: 人物构建器（年龄/性别/种族/体型/发型/服装/表情/姿势）
- prompt_engine.py: 提示词引擎（组合/优化/添加质量标签）
- nsfw_filter.py: NSFW 内容过滤
- grid_runner.py: 网格测试运行器（支持 SD + Janus）
- unified_builder.py: 统一提示词构建器

Janus-Pro (core/janus/):
- loader.py: 模型加载器
- understand.py: 图生文（图片理解）
- generate.py: 文生图（功能有限）
- chat.py: 文生文（对话）


## 配置模块 (config/)

- app_config.py: 应用配置（路径/生成参数/内存/UI/模型/Janus）
- config_manager.py: 统一配置管理器
- config_loader.py: 配置加载器（兼容旧 API）
- nsfw_config.py: NSFW 配置
- janus_config.py: Janus-Pro 配置
- schema.py: 配置 Schema 验证

配置文件:
- data/configs/gui_config.json: GUI 配置（模型路径、参数、内存优化）
- data/configs/nsfw_config.json: NSFW 内容控制配置
- data/configs/scene_patterns.json: 场景模式配置
- data/templates/persons.json: 人物模板
- data/templates/scenes.json: 场景模板


## 工具模块 (utils/)

- watermark_remover.py: 水印去除
- imagemeta_cleaner.py: 元数据清理
- exif_injector.py: EXIF 信息注入
- photo_realistic.py: 照片真实化（噪点/暗角/锐化）
- image_post_processor.py: 统一图片后期处理
- scheduler_factory.py: 调度器工厂
- strength_tester.py: 强度测试
- pipeline_pool.py: Pipeline 池（复用）
- vae_utils.py: VAE 工具
- controlnet/: ControlNet 模块（单层/多层/预处理）
- image_cache.py: 图片缓存
- module_discovery.py: 模块发现
- performance.py: 性能监控
- logger.py: 日志系统


## 脚本工具 (scripts/)

- code_collect.py: 项目文件收集（诊断用）
- code_package.py: 项目打包
- env_check.py: 环境检测
- env_check_controlnet_simple.py: ControlNet 环境检测
- env_setup.py: 环境安装
- model_index.py: 模型索引生成
- lora_index.py: LoRA 索引生成
- switch_model.py: 模型切换工具
- switch_lora.py: LoRA 切换工具
- organize_output.py: 输出目录整理
- convert_webp_to_jpg.py: WebP 转 JPG
- test_import.py: 导入测试


## 流水线风格 (core/pipeline/)

组件:
- pipeline.py: 流水线核心
- step.py: 步骤基类
- runner.py: 流水线运行器
- batch_runner.py: 批量流水线运行器
- presets.py: 内置流水线配置（50+ 风格）
- base_step.py: 风格转换步骤基类
- scene_counter.py: 场景数统计
- steps/: 50+ 风格转换步骤

支持的风格类别:
- 风格转换: 水彩、水墨、素描、赛博朋克、蒸汽波、3D渲染
- 场景主题: 海滩、森林、太空、古堡、婚纱
- 服装造型: 洛丽塔、和服、晚礼服、复古、电影质感
- 多人场景: 情侣水彩、情侣油画、家庭素描、朋友聚会、团队照片
- 宗教神话: 道门仙人、画中仙水墨、金身佛像、唐三彩、敦煌壁画、瓷器、兵马俑
- 西方神系: 奥林匹斯众神、希腊英雄、古希腊神庙、北欧神话、古罗马帝国、中世纪骑士
- 宗教神系: 上帝造物主、天使天军、伊斯兰神圣、古埃及神话
- 印度神话: 印度教三大主神、印度史诗、印度神庙、生殖崇拜
- 中国神话: 中国上古神话、中国民间神话
- 古风汉服: 古风汉服、赛博古风
- 雕像材质: 大理石雕像、大理石瑜伽、青铜雕像


## 提示词库 (tools/prompts_new/)

共 56 个风格:

- 每日壁纸: 清纯、性感、古风、赛博朋克、婚纱、骑士
- 动漫: 动漫爱爱（40场景）、赛璐璐风格
- 国风: 水墨、白描、敦煌、汉服、旗袍
- 自然场景: 海滩、森林、太空、古堡、极光、黄道十二宫
- 机甲: 白模机甲、高达、变形金刚、攻壳机动队
- 线稿: 老虎、龙、仙鹤、锦鲤、十二生肖
- 世界艺术: 齐白石、唐伯虎、印度细密画、波斯细密画、日本浮世绘
- 中国神话: 道教仙人、金身佛像、敦煌飞天、山海经异兽
- 西方神话: 奥林匹斯众神、北欧神话、古埃及神话
- 奢侈品: 珠宝、名表、跑车、包包


## 功能总览

- 文生图: GUI 文生图标签页
- 图生图: GUI 图生图标签页
- 图片反推: GUI 反推标签页
- 通用生成器: GUI 通用生成器标签页
- 亲密文生图: GUI 亲密文生图标签页
- Janus-Pro: GUI Janus-Pro 标签页
- 网格测试: GUI 网格测试标签页
- 流水线: GUI 流水线标签页
- LoRA 管理: GUI LoRA 管理标签页
- 智能生图: GUI 智能生图标签页
- CLI 生成: tools/generate.py
- 模型管理: 主界面状态栏
- LoRA 加载: 主界面 LoRA 选择器
- 内存监控: 主界面状态栏
- 热重载: 主界面重载按钮


## 支持的反推后端

- TAG: 快速标签模式（ViT-Base/ViT-Large/CLIP-B-32）
- CLIP: 详细风格标签（ViT-L-14）
- BLIP: 自然语言描述（BLIP-base/BLIP-large）
- Combined: BLIP + CLIP 组合模式
- LLM: BLIP + LLM 增强模式


## 注意事项

1. 模型文件放到 models/ 目录（支持 SD 1.5 或 SDXL）
2. 模型大小需 >= 2GB，程序会自动扫描
3. CPU 模式速度较慢，建议使用 GPU
4. 首次使用时反推功能会自动下载模型（约 1-3GB）
5. 内存不足时可在配置中启用 use_half_precision
6. 模型与代码同级目录: E:\SD_OpenVINO\models\ 与 E:\SD_OpenVINO\v8_universal_generator\


## 故障排除

- ModuleNotFoundError: pip install -r requirements.txt
- 内存不足: 配置中启用 use_half_precision
- VAE 尺寸错误: 确保图片尺寸是 64 的倍数
- ControlNet 加载失败: 运行 python scripts/env_check_controlnet_simple.py


## 更新日志

v8 (2026-07-26):
- 重构 ControlNet 模块，支持中文路径
- 新增强制重载功能，支持资源清理
- 优化内存管理，修复内存泄漏
- 新增图片后期处理（水印去除、EXIF 注入、照片真实化）
- 流水线支持完整后期处理
- 修复唯美风格场景数显示

v5 (2026-06-19):
- 新增通用生成器（人物模板生成）
- 新增 BLIP/CLIP 反推后端
- 新增组合反推模式
- 新增热重载模块功能
- 新增提示词构造器
- 优化水印去除功能


## 许可证

MIT License


Happy Generating! 🎨

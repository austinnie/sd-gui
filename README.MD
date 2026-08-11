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

更新日志
根据提交记录整理的主要版本更新：

v8 (2026-08-11)
核心变更
移除 IP-Adapter 支持：因升级组件成本过高，暂时移除 IP-Adapter 相关功能

修复 IP-Adapter 权重挂载问题：修复图生图分支中 set_ip_adapter_scale 调用导致的 AttributeError

模型与 LoRA 管理
智能模型管理系统：自动扫描并索引所有 SD1.5 模型，支持 smart/legacy/manual 三种模式

LoRA 智能管理系统：自动索引 183 个 LoRA，支持标签分类、评分排序

模型路径统一：修复 generate.py 模型加载路径问题，统一使用 config.py 配置

图生图增强
动态采样器配置：新增 SCHEDULER_TYPE 控制，自动匹配最佳步数

新增提示词风格：gallery_elegant_safe 画廊纯净人像风格

修复图生图强度传递：修复多轮生成中 strength 参数错误传递问题

路径安全防御
终极路径防御机制：强制校验输出路径归属，防止被 BLIP 缓存路径污染

BLIP 懒加载：仅在首次进入 LLM 分支时加载模型，避免循环污染

流水线与场景
修复 ControlNet 内存泄漏：流水线默认关闭 ControlNet，内存稳定在 5-8GB

新增唯美风格 Step：16 种唯美场景（风景/人物/意境）

ControlNet 中文路径支持：修复中文文件名/路径处理失败问题

流水线后期处理支持：水印去除、元数据清理、EXIF 注入、照片真实化

性能优化
内存监控与自动清理：超过阈值自动触发 GC，释放 Pipeline 池

图片 LRU 缓存：支持缓存命中统计

启动计时与性能监控：记录各阶段耗时

架构重构
BaseStyleStep 基类：统一 30+ 个 Step 文件，代码量减少 60-70%

ControlNet 模块拆分：600+ 行拆分为 7 个独立模块

Tabs 模块化：txt2img/img2img/interrogate/lora_manager 全部拆分

统一日志系统：替换所有 print() 为 logging，支持彩色输出

配置验证模块：新增 schema.py 进行配置校验

提示词与模板
安全模式重构：新增 prompts_new 安全线稿库，20+ 安全风格

提示词模板拆分：228 个模板按主题拆分为 9 个分类 JSON

新增 50+ 风格配置：涵盖世界艺术史、奢侈品设计、国粹名家等

佛经书法字画：新增 calligraphy_art 风格，含 52 句佛经经典

核聚变反应堆四阶段：极简线稿 → 拆解图 → 3D 白模 → 投产场景

AI 鉴赏系统
多后端鉴赏系统：支持 tag/blip/combined/llm/prompt 五种后端

LLM 后端增强：BLIP 描述 + Ollama 增强为 SD 提示词格式

Word 草稿自动生成：python-docx 实现图片+文案自动排版

BLIP 本地缓存修复：自动定位 snapshots 文件夹下的真实模型文件

后期处理增强
独立模块化处理：各滤镜独立按序执行，单步失败不影响出图

真实噪点：基于 ISO 的噪声模型（高斯+散粒噪声）

紫边模拟：真实镜头色散特征

指纹混淆：微小透视扭曲破坏像素规律

轻微裁剪：随机位置裁剪后缩放回原尺寸

命令行工具
模型切换：switch_model.py 支持 smart/legacy/manual 三种模式

LoRA 切换：switch_lora.py 支持 --list/--active/--set/--status 命令

generate.py 增强：新增 --txt2img/--img2img 模式切换

v7 (2026-08-08)
AI 鉴赏全链路
多后端鉴赏系统：tag/blip/combined/llm/prompt 五种后端

Word 草稿自动生成：图片+鉴赏文案自动排版

BLIP 懒加载：首次加载后复用，避免内存泄漏

智能文案降级：BLIP 返回标签时降级使用原提示词

路径防御
终极路径防御机制：强制校验输出路径归属

修复 BLIP 缓存污染：防止 snapshots 哈希目录覆盖输出路径

图生图修复
修复 final_strength 传递：正确传递命令行解析后的强度值

修复多轮生成路径污染：每轮重新校验 current_subfolder

v6 (2026-08-05 ~ 2026-08-06)
模型加载重构
OpenVINO 与普通模型物理隔离：if/else 分离，解决库冲突

统一模型路径变量：修复普通模式无法加载模型的问题

后期处理模块化
独立按序执行：各滤镜互不影响，单步失败继续执行

真实噪点：基于 ISO 的噪声模型

紫边模拟：真实镜头色散特征

指纹混淆：微小透视扭曲

轻微裁剪：随机位置裁剪

EXIF 注入容错：防止 exiftool 缺失导致失败

素描风格自动检测
自动检测关键词：sketch, pencil, lineart, 素描, 线稿等

检测到后跳过相机相关处理

图片自动分组
每 5 张放入独立子文件夹

描述文件自动跟随移动

v5 (2026-07-26 ~ 2026-08-04)
核心架构
BaseStyleStep 基类：30+ Step 统一继承，代码量减少 60-70%

Pipeline 模块化：runner/batch_runner/presets/scene_counter 独立

Tabs 模块化拆分：txt2img/img2img/interrogate/lora_manager/chat 全部模块化

统一日志系统：彩色输出 + 文件日志

配置验证模块：schema.py 类型检查

ControlNet
模块拆分：600+ 行拆为 7 个模块

中文路径支持：自动转临时英文路径

多层 ControlNet 支持：UI 可配置单层/多层

缓存优化：每个步骤只加载一次，所有场景复用

内存管理
PipelinePool：统一管理 pipeline 实例，引用计数

内存监控：显示使用量，自动触发 GC

强制清理：释放 Pipeline 池和图片缓存

热重载内存优化：重载前清理资源

提示词库
安全模式重构：prompts_new 安全线稿库，20+ 安全风格

模板拆分：228 个模板按主题拆分为 9 个分类

新增 50+ 风格：世界艺术史、奢侈品设计、国粹名家

佛经书法字画：52 句佛经经典

生成增强
进度条 + 时间戳：tqdm 实时显示

元数据记录：自动生成 .txt 日志文件

安全模式策略：simple/filter 两种策略

解剖约束自动添加：复杂姿势/多人/翅膀场景自动增强提示词

v4 (2026-07-12 ~ 2026-07-26)
流水线系统
批量生成支持：流水线批量处理

预设配置管理：presets.py 统一管理

场景计数动态获取：从步骤类实际读取

取消功能：独立取消标志，批量生成支持取消

ControlNet 集成：流水线支持 ControlNet

新增 Step
唯美风格：16 种场景（风景/人物/意境）

赛博汉服：汉服 + 赛博朋克融合

大理石瑜伽：16 种体式

青铜瑜伽：瑜伽体式青铜化

动漫爱爱：40 种场景

去衣：28 种场景

提示词服务
PromptTemplateService：统一管理所有模板

TemplateSelector：通用组件，可嵌入任何 Tab

分类按主题拆分：beauty.json 拆为 9 个子分类

v3 (2026-07-06 ~ 2026-07-12)
LLM 与智能生图
Ollama 集成：意图分析、关键词提取、提示词增强

会话模式：上下文记忆功能

原图特征分析：分析后增强提示词

Chat Tab 重构：拆分为 5 个独立模块

图生图增强
模板选择器支持：自动填充正负面提示词

预览功能：实时预览生成结果

NSFW 过滤器：安全过滤

Scheduler 工厂：支持多调度器切换

超分辨率
图片超分支持：提升输出质量

内存优化
PipelinePool：统一管理，支持引用计数

释放策略：使用后自动释放

v2 (2026-07-05 ~ 2026-07-06)
初始功能完善
NSFW 过滤：安全配置

水印去除：集成 watermark-removal

照片真实化：暗角/锐化/噪点

EXIF 注入：伪装相机拍摄

CLIP/BLIP 反推：提示词反推

热重载：模块动态重载

v1 (2026-07-05 之前)
初始版本
SD1.5/SDXL 模型支持

LoRA 加载与切换

文生图/图生图基础功能

基础提示词库


## 许可证

MIT License


Happy Generating! 🎨

# gui/reloader.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
热重载器 - 支持模块热重载
"""

import importlib
import sys
import os
import tkinter as tk
from tkinter import messagebox
from typing import List, Optional
import gc
import time  # ✅ 添加这行

from utils.logger import get_logger

logger = get_logger(__name__)

class Reloader:
    """热重载器"""
    
    # 需要重载的模块列表
    MODULES_TO_RELOAD = [
        # GUI 组件
        "gui.components.memory_monitor",
        "gui.components.progress_bar",
        "gui.components.image_preview",
        "gui.components.params_panel",
        "gui.components.batch_panel",
        "gui.components.nsfw_panel",
        "gui.components.lora_info_viewer",
        
        # GUI 标签页
        "gui.tabs.base_tab",

        "gui.tabs.txt2img",
        "gui.tabs.txt2img.tab",
        "gui.tabs.txt2img.ui",
        "gui.tabs.txt2img.generator",
        "gui.tabs.txt2img.batch",
        "gui.tabs.txt2img.templates",
        "gui.tabs.txt2img.utils",
        "gui.tabs.txt2img.callbacks",

        "gui.tabs.img2img",
        "gui.tabs.img2img.tab",
        "gui.tabs.img2img.ui",
        "gui.tabs.img2img.generator",
        "gui.tabs.img2img.batch",
        "gui.tabs.img2img.mask_editor",
        "gui.tabs.img2img.controlnet",
        "gui.tabs.img2img.utils",
        "gui.tabs.img2img.callbacks",

        # ✅ 新代码
        "gui.tabs.interrogate",
        "gui.tabs.interrogate.tab",
        "gui.tabs.interrogate.ui",
        "gui.tabs.interrogate.backends",
        "gui.tabs.interrogate.backends.base",
        "gui.tabs.interrogate.backends.tag",
        "gui.tabs.interrogate.backends.clip",
        "gui.tabs.interrogate.backends.blip",
        "gui.tabs.interrogate.backends.combined",
        "gui.tabs.interrogate.backends.qwen",

        "gui.tabs.universal_tab",
        "gui.tabs.scene_tab",
        "gui.tabs.janus_tab",
        "gui.tabs.grid_test_tab",
        "gui.tabs.pipeline_tab",

        # ✅ 添加新条目
        "gui.tabs.lora_manager",
        "gui.tabs.lora_manager.tab",
        "gui.tabs.lora_manager.ui",
        "gui.tabs.lora_manager.test_runner",
        "gui.tabs.lora_manager.analyzer",
        "gui.tabs.lora_manager.utils",

        "gui.tabs.chat_tab",
        
        # GUI Chat 模块
        "gui.chat",
        "gui.chat.intent_analyzer",
        "gui.chat.llm_client",
        "gui.chat.prompt_builder",
        "gui.chat.context_manager",
        "gui.chat.lora_manager",
        "gui.chat.controlnet_manager",
        "gui.chat.ollama_manager",
        "gui.chat.handlers",
        "gui.chat.utils",
        "gui.chat.ui",
        
        # GUI 管理
        "gui.scene_manager",
        "gui.model_manager",
        "gui.model_loader",
        "gui.ui_builder",
        "gui.lora_handler",
        "gui.vae_handler",
        "gui.reloader",
        
        # Core 模块
        "core.janus_loader",
        "core.janus_generator",
        "core.janus_analyzer",
        "core.janus_chat",
        "core.grid_runner",
        "core.nsfw_filter",
        "core.pipeline",
        "core.pipeline.step",
        "core.pipeline.pipeline",
        "core.pipeline.steps",
        
        # Config 模块
        "config.nsfw_config",
        "config.app_config",
        "config.janus_config",
        
        # Utils 模块
        "utils",
        "utils.watermark_remover",
        "utils.imagemeta_cleaner",
        "utils.exif_injector",
        "utils.photo_realistic",
        "utils.image_post_processor",
        "utils.scheduler_factory",
        "utils.strength_tester",
        "utils.scheduler_fix",
        "utils.pipeline_pool",
        "utils.vae_utils",
        "utils.controlnet",

        # ✅ 新增
        "services.llm_service",
        "services.ollama_service",   
        "services.cache_config",        
    ]
    
    def __init__(self, app):
        self.app = app
        self._is_reloading = False

    # ============================================================
    # ✅ 新增：UI 状态采集与恢复
    # ============================================================
    def _capture_ui_state(self) -> dict:
        """重载前，采集所有 Tab 和主界面参数的状态快照"""
        snapshot = {}
        app = self.app

        # 1. 采集主面板共享参数（步数、CFG、尺寸、种子等）
        if hasattr(app, 'params_panel'):
            p = app.params_panel
            snapshot['main_params'] = {
                'steps': p.steps_var.get(),
                'cfg': p.cfg_var.get(),
                'seed': p.seed_var.get(),
                'width': p.width_var.get(),
                'height': p.height_var.get(),
                'num_images': p.num_images_var.get(),
                'hires_fix': p.hires_fix_var.get(),
                'hires_scale': p.hires_scale_var.get(),
                'hires_denoise': p.hires_denoise_var.get(),
                'scheduler': p.scheduler_var.get(),
                # 水印与后期处理
                'remove_watermark': p.remove_watermark_var.get(),
                'watermark_strength': p.watermark_strength_var.get(),
                'clear_metadata': p.clear_metadata_var.get(),
                'inject_exif': p.inject_exif_var.get(),
                'realistic': p.realistic_var.get(),
                'camera': p.camera_var.get(),
            }

        # 2. 采集特定 Tab 的专属参数
        if hasattr(app, 'chat_tab') and app.chat_tab:
            snapshot['chat_tab'] = {
                'quality_mode': app.chat_tab.quality_mode_var.get(),
                'llm_enabled': app.chat_tab.llm_enabled_var.get(),
                'safe_mode': app.chat_tab.safe_mode_var.get(),
            }
        
        if hasattr(app, 'img2img_tab') and app.img2img_tab:
            snapshot['img2img_tab'] = {
                'strength': app.img2img_tab.strength_var.get(),
                'per_image': app.img2img_tab.per_image_var.get(),
                'use_inpaint': app.img2img_tab.use_inpaint_var.get(),
                'use_controlnet': app.img2img_tab.use_controlnet_var.get(),
                'controlnet_combo': app.img2img_tab.controlnet_combo_var.get(),
            }
        
        if hasattr(app, 'txt2img_tab') and app.txt2img_tab:
            snapshot['txt2img_tab'] = {
                'template_category': app.txt2img_tab.template_category_var.get(),
                'template_name': app.txt2img_tab.template_var.get(),
            }

        if hasattr(app, 'pipeline_tab') and app.pipeline_tab:
            snapshot['pipeline_tab'] = {
                'pipeline_name': app.pipeline_tab.pipeline_var.get(),
                'strength': app.pipeline_tab.strength_var.get(),
                'steps': app.pipeline_tab.steps_var.get(),
                'cfg': app.pipeline_tab.cfg_var.get(),
                'scenes_limit': app.pipeline_tab.scenes_limit_var.get(),
                'use_controlnet': app.pipeline_tab.use_controlnet_var.get(),
                'controlnet_type': app.pipeline_tab.controlnet_type_var.get(),
            }

        return snapshot

    def _restore_ui_state(self, snapshot: dict):
        """重载后，将状态快照注入回新的 UI 组件"""
        if not snapshot:
            return
        app = self.app

        # 1. 恢复主面板参数
        if 'main_params' in snapshot and hasattr(app, 'params_panel'):
            p = app.params_panel
            params = snapshot['main_params']
            # 使用安全设置，防止参数越界，与你的 app_config 联动
            p.steps_var.set(params.get('steps', p.steps_var.get()))
            p.cfg_var.set(params.get('cfg', p.cfg_var.get()))
            p.seed_var.set(params.get('seed', p.seed_var.get()))
            p.width_var.set(params.get('width', p.width_var.get()))
            p.height_var.set(params.get('height', p.height_var.get()))
            p.num_images_var.set(params.get('num_images', p.num_images_var.get()))
            p.hires_fix_var.set(params.get('hires_fix', p.hires_fix_var.get()))
            p.hires_scale_var.set(params.get('hires_scale', p.hires_scale_var.get()))
            p.hires_denoise_var.set(params.get('hires_denoise', p.hires_denoise_var.get()))
            p.scheduler_var.set(params.get('scheduler', p.scheduler_var.get()))
            
            p.remove_watermark_var.set(params.get('remove_watermark', p.remove_watermark_var.get()))
            p.watermark_strength_var.set(params.get('watermark_strength', p.watermark_strength_var.get()))
            p.clear_metadata_var.set(params.get('clear_metadata', p.clear_metadata_var.get()))
            p.inject_exif_var.set(params.get('inject_exif', p.inject_exif_var.get()))
            p.realistic_var.set(params.get('realistic', p.realistic_var.get()))
            p.camera_var.set(params.get('camera', p.camera_var.get()))

        # 2. 恢复 ChatTab 状态
        if 'chat_tab' in snapshot and hasattr(app, 'chat_tab') and app.chat_tab:
            params = snapshot['chat_tab']
            app.chat_tab.quality_mode_var.set(params.get('quality_mode', '快速'))
            app.chat_tab.llm_enabled_var.set(params.get('llm_enabled', True))
            app.chat_tab.safe_mode_var.set(params.get('safe_mode', True))
            # 触发 UI 的联动更新（手动调用 UI 更新方法）
            if hasattr(app.chat_tab, '_set_quality_mode'):
                app.chat_tab._set_quality_mode(app.chat_tab.quality_mode_var.get())

        # 3. 恢复 Img2ImgTab 状态
        if 'img2img_tab' in snapshot and hasattr(app, 'img2img_tab') and app.img2img_tab:
            params = snapshot['img2img_tab']
            app.img2img_tab.strength_var.set(params.get('strength', 0.35))
            app.img2img_tab.per_image_var.set(params.get('per_image', 1))
            app.img2img_tab.use_inpaint_var.set(params.get('use_inpaint', False))
            app.img2img_tab.use_controlnet_var.set(params.get('use_controlnet', False))
            app.img2img_tab.controlnet_combo_var.set(params.get('controlnet_combo', '姿态+边缘+深度'))

        # 4. 恢复 PipelineTab 状态
        if 'pipeline_tab' in snapshot and hasattr(app, 'pipeline_tab') and app.pipeline_tab:
            params = snapshot['pipeline_tab']
            # 因为 combo 的下拉列表需要重新刷新，这里用 after 延迟设置，防止列表未填充
            def set_pipeline_params():
                app.pipeline_tab.pipeline_var.set(params.get('pipeline_name', ''))
                app.pipeline_tab.strength_var.set(params.get('strength', 0.35))
                app.pipeline_tab.steps_var.set(params.get('steps', 25))
                app.pipeline_tab.cfg_var.set(params.get('cfg', 7.0))
                app.pipeline_tab.scenes_limit_var.set(params.get('scenes_limit', '全部'))
                app.pipeline_tab.use_controlnet_var.set(params.get('use_controlnet', False))
                app.pipeline_tab.controlnet_type_var.set(params.get('controlnet_type', 'canny'))
                
                if hasattr(app.pipeline_tab, '_update_info'):
                    app.pipeline_tab._update_info()
                    
            self.app.root.after(50, set_pipeline_params)
            
    # ============================================================
    # ✅ 新增：检查任务 + 强制重载入口
    # ============================================================
    
    def reload_all(self, force: bool = False):
        """
        执行完整热重载
        
        参数:
            force: 是否强制重载（会先清理资源）
        """
        if self._is_reloading:
            self.app.update_status("⏳ 正在重载中，请等待...")
            return

        # ✅ 1. 重载前：快照保存
        snapshot = self._capture_ui_state()
        
        # ✅ 检查是否有任务正在运行
        if not force and self._has_running_tasks():
            if not messagebox.askyesno(
                "任务正在运行",
                "检测到有生成任务正在运行，重载可能会导致任务中断。\n\n"
                "是否继续？"
            ):
                return
        
        self._is_reloading = True
        
        # ✅ 如果是强制重载，先清理资源
        if force:
            self._cleanup_before_reload()
        
        self.app.update_status("🔄 正在重载模块...")
        print("\n" + "=" * 70)
        logger.info(f"🔄 开始{'强制' if force else ''}热重载模块")
        print("=" * 70)
        
        # 第一步：重载配置模块
        if not self._reload_config_modules():
            self._is_reloading = False
            return
        
        # 第二步：自举 - 重载 ModuleDiscovery
        self._reload_module_discovery()
        
        # 第三步：发现所有模块
        modules_to_reload = self._discover_modules()
        if not modules_to_reload:
            self._is_reloading = False
            return
        
        # 第四步：重载业务模块
        reloaded, failed = self._reload_business_modules(modules_to_reload)
        
        # 第五步：重建 UI
        self._rebuild_ui()

        # ✅ 2. 重载后：注入状态恢复
        self._restore_ui_state(snapshot)
        
        # 显示结果
        self._show_reload_result(reloaded, failed, force)
        
        # ✅ 如果是强制重载，最终清理
        if force:
            self._final_cleanup()
        
        self._is_reloading = False

    # ============================================================
    # ✅ 新增：检查任务
    # ============================================================
    
    def _has_running_tasks(self) -> bool:
        """检查是否有任务正在运行"""
        # 检查文生图
        if hasattr(self.app, 'txt2img_tab') and self.app.txt2img_tab:
            if hasattr(self.app.txt2img_tab, 'is_generating') and self.app.txt2img_tab.is_generating:
                return True
        
        # 检查图生图
        if hasattr(self.app, 'img2img_tab') and self.app.img2img_tab:
            if hasattr(self.app.img2img_tab, 'is_generating') and self.app.img2img_tab.is_generating:
                return True
        
        # 检查流水线
        if hasattr(self.app, 'pipeline_tab') and self.app.pipeline_tab:
            if hasattr(self.app.pipeline_tab, 'is_running') and self.app.pipeline_tab.is_running:
                return True
        
        # 检查 Janus
        if hasattr(self.app, 'janus_tab') and self.app.janus_tab:
            if hasattr(self.app.janus_tab, 'is_generating') and self.app.janus_tab.is_generating:
                return True
        
        # 检查聊天
        if hasattr(self.app, 'chat_tab') and self.app.chat_tab:
            if hasattr(self.app.chat_tab, 'is_generating') and self.app.chat_tab.is_generating:
                return True
        
        # 检查网格测试
        if hasattr(self.app, 'grid_test_tab') and self.app.grid_test_tab:
            if hasattr(self.app.grid_test_tab, 'is_running') and self.app.grid_test_tab.is_running:
                return True
        
        return False


    # ============================================================
    # ✅ 新增：强制重载清理
    # ============================================================
    
    def _cleanup_before_reload(self):
        """重载前清理资源（强制重载使用）"""
        logger.info("🧹 强制重载：开始清理资源...")
        
        # 1. 取消所有正在运行的任务
        self._cancel_all_tasks()
        
        # 2. 等待任务完全停止
        time.sleep(1)
        
        # 3. 清理 Pipeline 池
        try:
            from utils.pipeline_pool import pipeline_pool
            status = pipeline_pool.get_status()
            if status.get('active_count', 0) > 0:
                logger.info(f"   🗑️ 清理 Pipeline 池 ({status['active_count']} 个实例)")
                for key, data in list(pipeline_pool._pipelines.items()):
                    pipe = data.get('pipe')
                    if pipe is not None:
                        try:
                            if hasattr(pipe, 'to'):
                                pipe.to("cpu")
                            del pipe
                        except:
                            pass
                pipeline_pool._pipelines.clear()
                logger.info("   ✅ Pipeline 池已清空")
        except Exception as e:
            logger.debug(f"   ⚠️ Pipeline 池清理失败: {e}")
        
        # 4. 清理图片缓存
        try:
            from utils.image_cache import image_cache
            cache_size = len(image_cache._cache)
            if cache_size > 0:
                logger.info(f"   🗑️ 清理图片缓存 ({cache_size} 张)")
                image_cache.clear()
        except Exception as e:
            logger.debug(f"   ⚠️ 图片缓存清理失败: {e}")
        
        # 5. 卸载当前模型
        if hasattr(self.app, 'model_manager'):
            if self.app.model_manager.is_sd_loaded:
                logger.info("   🗑️ 卸载 SD 模型")
                self.app.model_manager.unload_sd()
            elif self.app.model_manager.is_janus_loaded:
                logger.info("   🗑️ 卸载 Janus 模型")
                self.app.model_manager.unload_janus()
        
        # 6. 垃圾回收
        for _ in range(5):
            gc.collect()
        
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
        except:
            pass
        
        gc.collect()
        
        from gui.components.memory_monitor import get_memory_usage
        logger.info(f"   ✅ 资源清理完成，当前内存: {get_memory_usage():.1f} GB")
    

    def _cancel_all_tasks(self):
        """取消所有正在运行的任务"""
        logger.info("   ⏹️ 取消所有正在运行的任务...")
        
        # ===== 1. 取消文生图 =====
        if hasattr(self.app, 'txt2img_tab') and self.app.txt2img_tab:
            try:
                self.app.txt2img_tab.cancel_generation = True
                self.app.txt2img_tab.is_generating = False
                self.app.txt2img_tab.batch_running = False
                logger.info("      ✅ 文生图已取消")
            except Exception as e:
                logger.debug(f"      ⚠️ 文生图取消失败: {e}")
        
        # ===== 2. 取消图生图 =====
        if hasattr(self.app, 'img2img_tab') and self.app.img2img_tab:
            try:
                self.app.img2img_tab.cancel_generation = True
                self.app.img2img_tab.is_generating = False
                logger.info("      ✅ 图生图已取消")
            except Exception as e:
                logger.debug(f"      ⚠️ 图生图取消失败: {e}")
        
        # ===== 3. 取消流水线 =====
        if hasattr(self.app, 'pipeline_tab') and self.app.pipeline_tab:
            try:
                self.app.pipeline_tab.cancel_flag = True
                self.app.pipeline_tab.is_running = False
                logger.info("      ✅ 流水线已取消")
            except Exception as e:
                logger.debug(f"      ⚠️ 流水线取消失败: {e}")
        
        # ===== 4. 取消 Janus =====
        if hasattr(self.app, 'janus_tab') and self.app.janus_tab:
            try:
                if hasattr(self.app.janus_tab, 'cancel_generation'):
                    self.app.janus_tab.cancel_generation = True
                    self.app.janus_tab.is_generating = False
                    logger.info("      ✅ Janus 已取消")
            except Exception as e:
                logger.debug(f"      ⚠️ Janus 取消失败: {e}")
        
        # ===== 5. 取消聊天 =====
        if hasattr(self.app, 'chat_tab') and self.app.chat_tab:
            try:
                if hasattr(self.app.chat_tab, 'cancel_generation'):
                    self.app.chat_tab.cancel_generation = True
                    self.app.chat_tab.is_generating = False
                    logger.info("      ✅ 聊天已取消")
            except Exception as e:
                logger.debug(f"      ⚠️ 聊天取消失败: {e}")
        
        # ===== 6. 取消网格测试 =====
        if hasattr(self.app, 'grid_test_tab') and self.app.grid_test_tab:
            try:
                if hasattr(self.app.grid_test_tab, 'is_running') and self.app.grid_test_tab.is_running:
                    if hasattr(self.app.grid_test_tab, 'runner'):
                        self.app.grid_test_tab.runner.cancel_run()
                    self.app.grid_test_tab.is_running = False
                    logger.info("      ✅ 网格测试已取消")
            except Exception as e:
                logger.debug(f"      ⚠️ 网格测试取消失败: {e}")
        
        # ===== 7. 取消通用生成器 =====
        if hasattr(self.app, 'universal_tab') and self.app.universal_tab:
            try:
                if hasattr(self.app.universal_tab, 'cancel_generation'):
                    self.app.universal_tab.cancel_generation = True
                    self.app.universal_tab.is_generating = False
                    logger.info("      ✅ 通用生成器已取消")
            except Exception as e:
                logger.debug(f"      ⚠️ 通用生成器取消失败: {e}")
        
        # ===== 8. 取消场景生成 =====
        if hasattr(self.app, 'scene_tab') and self.app.scene_tab:
            try:
                if hasattr(self.app.scene_tab, 'cancel_generation'):
                    self.app.scene_tab.cancel_generation = True
                    self.app.scene_tab.is_generating = False
                    logger.info("      ✅ 场景生成已取消")
            except Exception as e:
                logger.debug(f"      ⚠️ 场景生成取消失败: {e}")
        
        # ===== 9. 强制等待任务停止 =====
        time.sleep(0.5)
        
        # ===== 10. 二次确认：强制重置所有生成状态 =====
        try:
            # 重置所有 Tab 的生成状态
            for tab_name in ['txt2img_tab', 'img2img_tab', 'pipeline_tab', 
                             'janus_tab', 'chat_tab', 'grid_test_tab',
                             'universal_tab', 'scene_tab']:
                if hasattr(self.app, tab_name):
                    tab = getattr(self.app, tab_name)
                    if tab:
                        if hasattr(tab, 'is_generating'):
                            tab.is_generating = False
                        if hasattr(tab, 'cancel_generation'):
                            tab.cancel_generation = True
                        if hasattr(tab, 'is_running'):
                            tab.is_running = False
        except Exception as e:
            logger.debug(f"      ⚠️ 重置状态失败: {e}")
        
        logger.info("   ✅ 所有任务已取消")
    
    def _final_cleanup(self):
        """强制重载后的最终清理"""
        logger.info("🧹 强制重载完成，执行最终清理...")
        
        for _ in range(3):
            gc.collect()
        
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except:
            pass
        
        from gui.components.memory_monitor import get_memory_usage
        logger.info(f"   ✅ 最终清理完成，当前内存: {get_memory_usage():.1f} GB")
    
    # ============================================================
    # ✅ 修改：显示重载结果（支持 force 参数）
    # ============================================================
    
    def _show_reload_result(self, reloaded: List[str], failed: List[str], force: bool = False):
        """显示重载结果"""
        print("\n" + "=" * 70)
        logger.info(f"📊 {'强制' if force else ''}热重载结果统计:")
        logger.info(f"   ✅ 成功: {len(reloaded)} 个模块")
        if failed:
            logger.info(f"   ❌ 失败: {len(failed)} 个模块")
            logger.info(f"      {', '.join(failed[:5])}{'...' if len(failed) > 5 else ''}")
        print("=" * 70)
        
        status_msg = f"✅ {'强制' if force else ''}热重载完成！已重载 {len(reloaded)} 个模块"
        if failed:
            status_msg += f" (⚠️ {len(failed)} 个失败)"
        self.app.update_status(status_msg)
        
        if failed:
            messagebox.showwarning(
                "部分模块重载失败",
                f"有 {len(failed)} 个模块重载失败:\n\n"
                f"{', '.join(failed[:10])}\n\n"
                f"请查看控制台输出获取详细信息。"
            )
        else:
            # ✅ 非强制重载时自动重载模型
            if not force:
                self._auto_reload_model_after_reload()
    
    # ============================================================
    # ✅ 兼容旧接口
    # ============================================================
    
    def reload(self):
        """兼容旧接口 - 普通重载"""
        self.reload_all(force=False)
        
    def _reload_config_modules(self) -> bool:
        """重载配置模块"""
        logger.info(f"\n📦 第一步: 重载配置模块")
        
        config_modules = [
            'config.app_config',
            'config.nsfw_config',
            'config.janus_config',
        ]
        
        for mod_name in config_modules:
            try:
                if mod_name in sys.modules:
                    importlib.reload(sys.modules[mod_name])
                    logger.info(f"   ✅ 重载: {mod_name}")
            except Exception as e:
                logger.info(f"   ❌ 重载失败 {mod_name}: {e}")
                return False
        
        # 更新配置到 UI
        try:
            from config.app_config import AppConfig
            AppConfig.reload()
            self.app.params_panel.set_params(
                steps=AppConfig.get_instance().generation.steps["default"],
                cfg=AppConfig.get_instance().generation.cfg["default"]
            )
            logger.info(f"   ✅ 配置已更新到 UI")
        except Exception as e:
            logger.info(f"   ⚠️ 配置更新失败: {e}")
        
        return True
    
    def _reload_module_discovery(self):
        """自举：重载 ModuleDiscovery"""
        logger.info(f"\n📦 第二步: 自举 - 重载 ModuleDiscovery")
        
        try:
            if 'utils.module_discovery' in sys.modules:
                importlib.reload(sys.modules['utils.module_discovery'])
                logger.info(f"   ✅ 自举成功: ModuleDiscovery 已重载")
        except Exception as e:
            logger.info(f"   ⚠️ 自举失败: {e}")
    
    def _discover_modules(self) -> Optional[List[str]]:
        """发现所有模块"""
        logger.info(f"\n📦 第三步: 发现所有模块")
        
        try:
            from utils.module_discovery import ModuleDiscovery
            all_modules = ModuleDiscovery.discover(force=True)
            logger.info(f"   📋 发现 {len(all_modules)} 个模块")
            
            categories = {}
            for mod in all_modules:
                category = mod.split('.')[0] if '.' in mod else 'other'
                categories[category] = categories.get(category, 0) + 1
            
            for cat, count in categories.items():
                logger.info(f"      - {cat}: {count} 个模块")
            
            return all_modules
            
        except Exception as e:
            logger.info(f"   ❌ 模块发现失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _reload_business_modules(self, all_modules: List[str]) -> tuple:
        """重载业务模块"""
        logger.info(f"\n📦 第四步: 重载业务模块")
        
        already_reloaded = {
            'config.app_config', 'config.nsfw_config', 'config.janus_config',
            'utils.module_discovery'
        }
        
        exclude_modules = {
            'app', 'main', '__init__', '__main__',
        }
        
        modules_to_reload = [
            m for m in all_modules
            if m not in already_reloaded
            and m.split('.')[-1] not in exclude_modules
            and not m.endswith('.test')
            and not m.endswith('.tests')
        ]
        
        logger.info(f"   📋 需要重载的业务模块: {len(modules_to_reload)} 个")
        
        reloaded = []
        failed = []
        
        for mod_name in modules_to_reload:
            try:
                if mod_name in sys.modules:
                    importlib.reload(sys.modules[mod_name])
                    reloaded.append(mod_name)
                else:
                    pass
            except Exception as e:
                logger.info(f"   ❌ 重载失败 {mod_name}: {e}")
                failed.append(mod_name)
        
        # 重新注册流水线步骤
        try:
            from core.pipeline import register_all_steps
            register_all_steps()
            logger.info(f"   ✅ 流水线步骤已重新注册")
        except Exception as e:
            logger.info(f"   ⚠️ 流水线步骤注册失败: {e}")
        
        return reloaded, failed
    
    def _rebuild_ui(self):
        """重建 UI"""
        logger.info(f"\n📦 第五步: 重建 UI 组件")
        logger.info(f"   🔨 重建 UI 组件:")
        
        try:
            parent_frame = self.app.params_panel.frame.master
            self.app.params_panel.rebuild(parent_frame)
            logger.info(f"      ✅ 参数面板重建完成")
        except Exception as e:
            logger.info(f"      ❌ 参数面板重建失败: {e}")
        
        try:
            self._recreate_tabs()
            logger.info(f"      ✅ 标签页重建完成")
        except Exception as e:
            logger.info(f"      ❌ 标签页重建失败: {e}")
        
        try:
            self._recreate_nsfw_panel()
            logger.info(f"      ✅ NSFW 面板重建完成")
        except Exception as e:
            logger.info(f"      ⚠️ NSFW 面板重建失败: {e}")
        
        # 重新布局
        try:
            param_frame = self.app.params_panel.get_frame()
            if param_frame and hasattr(self.app, 'notebook'):
                param_frame.pack_forget()
                param_frame.pack(
                    side=tk.TOP, fill=tk.X, padx=10, pady=5,
                    before=self.app.notebook
                )
                logger.info(f"      ✅ 参数面板重定位完成")
        except Exception as e:
            logger.info(f"      ⚠️ 参数面板重定位失败: {e}")
        
        try:
            if hasattr(self.app, 'nsfw_panel') and self.app.nsfw_panel:
                nsfw_frame = self.app.nsfw_panel.get_frame()
                if nsfw_frame and hasattr(self.app, 'notebook'):
                    nsfw_frame.pack_forget()
                    nsfw_frame.pack(
                        side=tk.TOP, fill=tk.X, padx=10, pady=5,
                        before=self.app.notebook
                    )
                    logger.info(f"      ✅ NSFW 面板重定位完成")
        except Exception as e:
            logger.info(f"      ⚠️ NSFW 面板重定位失败: {e}")
        
        try:
            self.app._update_model_ui()
            logger.info(f"      ✅ 模型状态已更新")
        except Exception as e:
            logger.info(f"      ⚠️ 模型状态更新失败: {e}")
        
        try:
            if hasattr(self.app, '_update_lora_list'):
                self.app._update_lora_list()
                logger.info(f"      ✅ LoRA 列表已刷新")
        except Exception as e:
            logger.info(f"      ⚠️ LoRA 列表刷新失败: {e}")
        
        try:
            if hasattr(self.app, '_refresh_lora_viewer'):
                self.app._refresh_lora_viewer()
                logger.info(f"      ✅ LoRA 信息查看器已刷新")
        except Exception as e:
            logger.info(f"      ⚠️ LoRA 信息查看器刷新失败: {e}")
        
        try:
            self.app.root.update_idletasks()
            logger.info(f"      ✅ UI 刷新完成")
        except:
            pass
    
    def _recreate_tabs(self):
        """重建标签页"""
        from gui.tabs.txt2img import Txt2ImgTab
        from gui.tabs.img2img import Img2ImgTab
        from gui.tabs.interrogate import InterrogateTab
        from gui.tabs.universal_tab import UniversalTab
        from gui.tabs.scene_tab import SceneTab
        from gui.tabs.janus_tab import JanusTab
        from gui.tabs.grid_test_tab import GridTestTab
        from gui.tabs.pipeline_tab import PipelineTab
        from gui.tabs.chat_tab import ChatTab
        
        from gui.tabs.lora_manager import LoraManagerTab
       
                
        for tab in self.app.notebook.tabs():
            try:
                self.app.notebook.forget(tab)
            except:
                pass
        
        self.app.txt2img_tab = Txt2ImgTab(self.app.notebook, self.app)
        self.app.notebook.add(self.app.txt2img_tab.get_frame(), text="📝 文生图")
        
        self.app.scene_tab = SceneTab(self.app.notebook, self.app)
        self.app.notebook.add(self.app.scene_tab.get_frame(), text="💑 亲密文生图")
        
        self.app.universal_tab = UniversalTab(self.app.notebook, self.app)
        self.app.notebook.add(self.app.universal_tab.get_frame(), text="🌍 通用生成器")
        
        self.app.img2img_tab = Img2ImgTab(self.app.notebook, self.app)
        self.app.notebook.add(self.app.img2img_tab.get_frame(), text="🖼️ 图生图")
        
        self.app.interrogate_tab = InterrogateTab(self.app.notebook, self.app)
        self.app.notebook.add(self.app.interrogate_tab.get_frame(), text="🔍 图片反推")
        
        self.app.janus_tab = JanusTab(self.app.notebook, self.app, self.app.model_manager)
        self.app.notebook.add(self.app.janus_tab.get_frame(), text="🤖 Janus-Pro")
        
        self.app.grid_test_tab = GridTestTab(self.app.notebook, self.app)
        self.app.notebook.add(self.app.grid_test_tab.frame, text="🧪 网格测试")
        
        self.app.pipeline_tab = PipelineTab(self.app.notebook, self.app)
        self.app.notebook.add(self.app.pipeline_tab.get_frame(), text="🔧 流水线")
        
        self.app.lora_manager_tab = LoraManagerTab(self.app.notebook, self.app)
        self.app.notebook.add(self.app.lora_manager_tab.get_frame(), text="🔧 LoRA 管理")
        
        self.app.chat_tab = ChatTab(self.app.notebook, self.app)
        self.app.notebook.add(self.app.chat_tab.get_frame(), text="💬 智能生图")
    
    def _recreate_nsfw_panel(self):
        """重建 NSFW 面板"""
        import importlib
        import sys
        
        try:
            if hasattr(self.app, 'nsfw_panel') and self.app.nsfw_panel:
                old_frame = self.app.nsfw_panel.get_frame()
                if old_frame and old_frame.winfo_exists():
                    old_frame.destroy()
        except Exception as e:
            pass
        
        try:
            for mod_name in ["gui.components.nsfw_panel", "core.nsfw_filter", "config.nsfw_config"]:
                if mod_name in sys.modules:
                    importlib.reload(sys.modules[mod_name])
        except Exception as e:
            pass
        
        try:
            from gui.components.nsfw_panel import NSFWPanel
            main_frame = self.app.scrollable_frame
            self.app.nsfw_panel = NSFWPanel(main_frame, self.app)
            nsfw_frame = self.app.nsfw_panel.get_frame()
            
            if hasattr(self.app, 'notebook') and self.app.notebook:
                nsfw_frame.pack(
                    side=tk.TOP, fill=tk.X, padx=10, pady=5,
                    before=self.app.notebook
                )
        except Exception as e:
            logger.info(f"   ❌ NSFW 面板重建失败: {e}")
    
     

    # gui/reloader.py
    def _auto_reload_model_after_reload(self):
        """热重载后自动重新加载模型 - 先清理再加载"""
        if not hasattr(self.app, 'model_manager'):
            return
        
        if not hasattr(self.app, 'model_var'):
            return
        
        model_name = self.app.model_var.get()
        if not model_name or model_name not in self.app.checkpoint_paths:
            if hasattr(self.app, '_last_model_path') and self.app._last_model_path:
                model_name = os.path.basename(self.app._last_model_path)
                model_path = self.app._last_model_path
            else:
                return
        else:
            model_path = self.app.checkpoint_paths[model_name]
        
        self.app.update_status(f"🔄 自动重新加载模型: {model_name[:40]}...")
        
        import threading
        def load_thread():
            # ✅ 先强制清理内存
            from gui.components.memory_monitor import force_memory_cleanup
            force_memory_cleanup()
            
            def progress_cb(value, msg):
                self.app.root.after(0, lambda: self.app.update_progress(value, msg))
            
            success = self.app.model_manager.load_sd(
                model_path, model_name, progress_cb
            )
            if success:
                self.app.root.after(0, lambda: self.app.update_status(f"✅ 模型已重新加载: {model_name[:40]}..."))
                self.app.root.after(0, self.app._update_model_ui)
                self.app.root.after(0, self.app._update_lora_list)
            else:
                self.app.root.after(0, lambda: self.app.update_status("❌ 模型自动加载失败，请手动加载"))
        
        threading.Thread(target=load_thread, daemon=True).start()
    
        

  

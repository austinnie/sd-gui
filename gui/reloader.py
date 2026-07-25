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


from utils.logger import get_logger, info, warning, error, debug

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
    
    def reload_all(self):
        """执行完整热重载"""
        self.app.update_status("🔄 正在重载模块...")
        print("\n" + "=" * 70)
        logger.info(f"🔄 开始热重载模块 (自举 + 两步重载法)")
        print("=" * 70)
        
        # 第一步：重载配置模块
        if not self._reload_config_modules():
            return
        
        # 第二步：自举 - 重载 ModuleDiscovery
        self._reload_module_discovery()
        
        # 第三步：发现所有模块
        modules_to_reload = self._discover_modules()
        if not modules_to_reload:
            return
        
        # 第四步：重载业务模块
        reloaded, failed = self._reload_business_modules(modules_to_reload)
        
        # 第五步：重建 UI
        self._rebuild_ui()
        
        # 显示结果
        self._show_reload_result(reloaded, failed)
    
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
    
    def _show_reload_result(self, reloaded: List[str], failed: List[str]):
        """显示重载结果"""
        print("\n" + "=" * 70)
        logger.info(f"📊 热重载结果统计:")
        logger.info(f"   ✅ 成功: {len(reloaded)} 个模块")
        if failed:
            logger.info(f"   ❌ 失败: {len(failed)} 个模块")
            logger.info(f"      {', '.join(failed[:5])}{'...' if len(failed) > 5 else ''}")
        print("=" * 70)
        
        status_msg = f"✅ 热重载完成！已重载 {len(reloaded)} 个模块"
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
        # ✅ 热重载完成后自动重新加载模型
        self._auto_reload_model_after_reload()
        

    def _auto_reload_model_after_reload(self):
        """热重载后自动重新加载模型"""
        if not hasattr(self.app, 'model_manager'):
            return
        
        # 从 UI 获取当前选择的模型
        if not hasattr(self.app, 'model_var'):
            return
        
        model_name = self.app.model_var.get()
        if not model_name or model_name not in self.app.checkpoint_paths:
            # 没有选择模型，尝试使用 _last_model_path
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
    
        
    def _reload_modules(self):
        """热重载模块"""
        self.reloader.reload_all()
  

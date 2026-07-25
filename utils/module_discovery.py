# utils/module_discovery.py
"""
模块自动发现工具 - 支持变更检测和热重载
"""

import os
import sys
import time
from typing import List, Set, Dict, Optional, Any
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)
# 注意：不要在这里导入项目内部模块，避免循环依赖
# 所有导入都在方法内部进行


class ModuleDiscovery:
    """自动发现并管理项目模块"""
    
    # 需要扫描的根包
    ROOT_PACKAGES = ['gui', 'core', 'utils', 'config']
    
    # 需要排除的模块名（完全匹配）
    EXCLUDE_MODULES = {
        'app', 'main', '__init__', '__main__',
        'setup', 'test', 'tests', 'conftest',
        'module_discovery',  # 自己排除自己（由自举机制处理）
    }
    
    # 需要排除的目录
    EXCLUDE_DIRS = {
        '__pycache__', '.git', '.idea', 'venv', 'env',
        'node_modules', 'dist', 'build', '.pytest_cache',
        'tests', 'test',  # 测试目录
    }
    
    # 缓存
    _instance: Optional['ModuleDiscovery'] = None
    _cached_modules: Optional[List[str]] = None
    _last_scan_time: float = 0
    _file_mod_times: Dict[str, float] = {}
    _project_root: Optional[str] = None
    
    @classmethod
    def discover(cls, force: bool = False) -> List[str]:
        """
        发现所有需要重载的模块
        
        Args:
            force: 强制重新扫描
            
        Returns:
            模块名称列表（按依赖顺序排序）
        """
        current_time = time.time()
        
        # 如果缓存有效且不强制扫描，使用缓存
        if not force and cls._cached_modules is not None:
            # 检查是否有文件变更
            if not cls._has_file_changes():
                return cls._cached_modules
        
        # 重新扫描
        logger.info(f"   🔍 扫描模块文件...")
        modules = cls._scan_all_modules()
        
        # 更新缓存
        cls._cached_modules = modules
        cls._last_scan_time = current_time
        
        return modules
    
    @classmethod
    def _has_file_changes(cls) -> bool:
        """检查是否有文件变更"""
        if not cls._cached_modules:
            return True
        
        for module_name in cls._cached_modules:
            # 获取模块文件路径
            if module_name in sys.modules:
                module = sys.modules[module_name]
                file_path = getattr(module, '__file__', None)
                if file_path and os.path.exists(file_path):
                    mtime = os.path.getmtime(file_path)
                    if file_path not in cls._file_mod_times:
                        return True  # 新文件
                    if mtime > cls._file_mod_times[file_path]:
                        return True  # 文件已修改
        
        return False
    
    @classmethod
    def _scan_all_modules(cls) -> List[str]:
        """扫描所有模块并记录修改时间"""
        modules = set()
        project_root = cls._get_project_root()
        
        # 扫描每个根包
        for package in cls.ROOT_PACKAGES:
            package_path = os.path.join(project_root, package)
            if os.path.exists(package_path):
                cls._scan_package(package_path, package, modules)
        
        # 记录文件修改时间
        for module_name in modules:
            if module_name in sys.modules:
                module = sys.modules[module_name]
                file_path = getattr(module, '__file__', None)
                if file_path and os.path.exists(file_path):
                    cls._file_mod_times[file_path] = os.path.getmtime(file_path)
        
        # 按层级排序（父模块在前）
        return sorted(modules, key=lambda x: (x.count('.'), x))
    
    @classmethod
    def _scan_package(cls, path: str, package_name: str, modules: Set[str]):
        """递归扫描包"""
        if not os.path.exists(path):
            return
            
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            
            # 跳过排除的目录
            if item in cls.EXCLUDE_DIRS:
                continue
            
            if os.path.isdir(item_path):
                # 检查是否是 Python 包（有 __init__.py）
                init_file = os.path.join(item_path, '__init__.py')
                if os.path.exists(init_file):
                    sub_package = f"{package_name}.{item}"
                    modules.add(sub_package)
                    # 递归扫描子包
                    cls._scan_package(item_path, sub_package, modules)
                else:
                    # 不是 Python 包，但可能包含 Python 文件
                    cls._scan_package_files(item_path, f"{package_name}.{item}", modules)
            elif item.endswith('.py'):
                module_name = item[:-3]  # 去掉 .py
                if module_name not in cls.EXCLUDE_MODULES:
                    full_name = f"{package_name}.{module_name}"
                    # 排除主文件
                    if not full_name.endswith('.app') and not full_name.endswith('.main'):
                        modules.add(full_name)
    
    @classmethod
    def _scan_package_files(cls, path: str, package_name: str, modules: Set[str]):
        """扫描目录中的 Python 文件"""
        if not os.path.exists(path):
            return
            
        for item in os.listdir(path):
            if item.endswith('.py'):
                module_name = item[:-3]
                if module_name not in cls.EXCLUDE_MODULES:
                    full_name = f"{package_name}.{module_name}"
                    modules.add(full_name)
    
    @classmethod
    def _get_project_root(cls) -> str:
        """获取项目根目录"""
        if cls._project_root is not None:
            return cls._project_root
        
        # 从当前文件向上查找
        current_dir = os.path.dirname(os.path.abspath(__file__))
        while current_dir:
            # 检查是否是项目根目录（包含 gui, core, utils, config）
            if all(os.path.exists(os.path.join(current_dir, pkg)) 
                   for pkg in cls.ROOT_PACKAGES):
                cls._project_root = current_dir
                return current_dir
            parent = os.path.dirname(current_dir)
            if parent == current_dir:
                break
            current_dir = parent
        
        # 如果找不到，返回当前目录的父目录
        cls._project_root = os.path.dirname(current_dir)
        return cls._project_root
    
    @classmethod
    def clear_cache(cls):
        """清除缓存"""
        cls._cached_modules = None
        cls._file_mod_times = {}
        cls._last_scan_time = 0
    
    @classmethod
    def get_module_info(cls, module_name: str) -> Dict[str, Any]:
        """获取模块信息"""
        if module_name in sys.modules:
            module = sys.modules[module_name]
            return {
                'name': module_name,
                'file': getattr(module, '__file__', None),
                'loaded': True,
                'size': len(dir(module)),
                'has_reload': hasattr(module, '__loader__'),
            }
        return {
            'name': module_name,
            'loaded': False,
        }
    
    @classmethod
    def get_statistics(cls) -> Dict[str, Any]:
        """获取统计信息"""
        modules = cls.discover()
        loaded = sum(1 for m in modules if m in sys.modules)
        
        return {
            'total_modules': len(modules),
            'loaded_modules': loaded,
            'unloaded_modules': len(modules) - loaded,
            'last_scan': datetime.fromtimestamp(cls._last_scan_time).strftime('%Y-%m-%d %H:%M:%S') if cls._last_scan_time else 'Never',
            'cache_valid': cls._cached_modules is not None,
        }
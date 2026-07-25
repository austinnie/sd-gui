# services/llm_service.py
"""LLM 服务 - 所有 Tab 共享"""

import threading
import requests
from typing import Optional, Callable


class LLMService:
    """LLM 服务单例"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if LLMService._initialized:
            return
        LLMService._initialized = True
        
        self.model = "qwen2.5:1.5b"
        self.base_url = "http://localhost:11434"
        self._available = False
        self._installing = False
        self._callbacks = []
        self._status = "未检查"
    
    def check_status(self) -> bool:
        """检查 LLM 状态"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if response.status_code == 200:
                models = [m["name"] for m in response.json().get("models", [])]
                self._available = self.model in models or self.model.split(":")[0] in str(models)
                self._status = "已就绪" if self._available else "模型未下载"
                return self._available
        except:
            self._available = False
            self._status = "服务未运行"
        return False
    
    def is_available(self) -> bool:
        """是否可用"""
        return self._available
    
    def is_running(self) -> bool:
        """Ollama 服务是否运行"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def is_installed(self) -> bool:
        """Ollama 是否已安装"""
        import subprocess
        try:
            result = subprocess.run(["ollama", "--version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def get_status_message(self) -> str:
        """获取状态消息"""
        if not self.is_running():
            return "⚠️ Ollama 服务未运行\n💡 请安装并启动 Ollama: ollama serve"
        if not self.is_available():
            return f"⚠️ 模型 {self.model} 未下载\n💡 请运行: ollama pull {self.model}"
        return "✅ LLM 服务正常"
    
    def add_status_callback(self, callback: Callable):
        """添加状态变化回调"""
        if callback not in self._callbacks:
            self._callbacks.append(callback)
    
    def generate(self, prompt: str, timeout: int = 30, max_tokens: int = 512) -> Optional[str]:
        """生成文本"""
        if not self._available:
            return None
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": 0.7,
                    "stream": False,
                    "max_tokens": max_tokens,
                },
                timeout=timeout
            )
            if response.status_code == 200:
                return response.json().get("response", "").strip()
        except:
            pass
        return None
    
    def install_ollama(self, progress_callback: Optional[Callable] = None) -> bool:
        """安装 Ollama"""
        if self._installing:
            return False
        
        self._installing = True
        
        def install_thread():
            import subprocess
            import time
            
            try:
                if progress_callback:
                    progress_callback("📦 正在下载 Ollama...")
                
                cmd = 'powershell -Command "irm https://ollama.com/install.ps1 | iex"'
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                
                for line in process.stdout:
                    if "Downloading" in line or "Installing" in line:
                        if progress_callback:
                            progress_callback(f"📦 {line.strip()}")
                
                process.wait()
                
                if process.returncode == 0:
                    # 启动服务
                    subprocess.Popen(
                        ["ollama", "serve"],
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                    )
                    time.sleep(3)
                    
                    # 下载模型
                    if progress_callback:
                        progress_callback(f"📦 下载模型 {self.model}...")
                    
                    process = subprocess.Popen(
                        ["ollama", "pull", self.model],
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        bufsize=1,
                        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                    )
                    
                    for line in process.stdout:
                        if "%" in line:
                            if progress_callback:
                                progress_callback(f"📦 {line.strip()}")
                    
                    process.wait()
                    
                    if process.returncode == 0:
                        self._available = True
                        self._status = "已就绪"
                        if progress_callback:
                            progress_callback("✅ LLM 安装完成！")
                        for cb in self._callbacks:
                            try:
                                cb(True, "LLM 已就绪")
                            except:
                                pass
                    else:
                        if progress_callback:
                            progress_callback("❌ 模型下载失败")
                else:
                    if progress_callback:
                        progress_callback("❌ Ollama 安装失败")
                    
            except Exception as e:
                if progress_callback:
                    progress_callback(f"❌ 安装失败: {e}")
            finally:
                self._installing = False
        
        threading.Thread(target=install_thread, daemon=True).start()
        return True


# 全局实例
llm_service = LLMService()
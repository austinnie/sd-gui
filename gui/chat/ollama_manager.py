# gui/chat/ollama_manager.py
"""Ollama 管理器"""

import os
import sys
import subprocess
import threading
import requests


class OllamaManager:
    """Ollama 管理器"""
    
    def __init__(self, tab):
        self.tab = tab
        self.installing = False
        self.available = False
        self.model = "qwen2.5:1.5b"
        self.model_size = "1GB"
    
    def check_status(self):
        """检查 LLM 状态"""
        if self.is_running():
            if self.is_available():
                self.available = True
                self.tab.llm_status.config(text="●", foreground="green")
                self.tab._append_message("system", f"✅ LLM 已就绪 (模型: {self.model})")
                return
        
        self.available = False
        self.tab.llm_status.config(text="●", foreground="orange")
        self.tab._append_message("system", "⚠️ LLM 未就绪，将使用基础模式")
    
    def is_running(self) -> bool:
        """检查 Ollama 服务是否运行"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def is_available(self) -> bool:
        """检查模型是否可用"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = [m["name"] for m in response.json().get("models", [])]
                return self.model in models or self.model.split(":")[0] in str(models)
            return False
        except:
            return False
    
    def is_installed(self) -> bool:
        """检查 Ollama 是否已安装"""
        try:
            result = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def install(self):
        """安装 Ollama"""
        if self.installing:
            return

        self.installing = True
        self.tab._append_message("system", "📦 正在下载并安装 Ollama... (可能需要几分钟)")
        self.tab._update_status("📦 安装 Ollama...")

        def install_thread():
            try:
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
                        self.tab.app.root.after(0, lambda l=line: self.tab._update_status(f"📦 {l.strip()[:50]}..."))
                        print(line.strip())

                process.wait()

                if process.returncode == 0:
                    self.tab._append_message("system", "✅ Ollama 安装完成！正在启动...")
                    threading.Thread(target=self.start_service, daemon=True).start()
                else:
                    self.tab._append_message("system", "❌ Ollama 安装失败，请手动安装")
                    self.installing = False

            except Exception as e:
                self.tab._append_message("system", f"❌ 安装失败: {e}")
                self.installing = False

        threading.Thread(target=install_thread, daemon=True).start()
    
    def start_service(self):
        """启动 Ollama 服务"""
        import time

        self.tab._append_message("system", "🔄 正在启动 Ollama 服务...")

        try:
            subprocess.Popen(
                ["ollama", "serve"],
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            time.sleep(3)

            if self.is_running():
                self.tab._append_message("system", "✅ Ollama 服务已启动")
                threading.Thread(target=self.download_model, daemon=True).start()
            else:
                self.tab._append_message("system", "⚠️ 服务启动失败，请手动运行: ollama serve")
                self.installing = False
        except Exception as e:
            self.tab._append_message("system", f"❌ 启动失败: {e}")
            self.installing = False
    
    def download_model(self):
        """下载模型"""
        self.tab._append_message("system", f"📦 正在下载模型: {self.model} (约 {self.model_size})...")
        self.tab._append_message("system", "⏳ 这可能需要 10-30 分钟，请耐心等待...")

        def download_thread():
            try:
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
                    line = line.strip()
                    if "downloading" in line.lower():
                        if "%" in line:
                            self.tab.app.root.after(0, lambda l=line: self.tab._update_status(f"📦 {l[:60]}..."))
                        print(line)

                process.wait()

                if process.returncode == 0:
                    self.on_ready()
                else:
                    self.tab._append_message("system", f"❌ 模型下载失败")
                    self.tab._append_message("system", f"💡 请手动下载: ollama pull {self.model}")
                    self.installing = False

            except Exception as e:
                self.tab._append_message("system", f"❌ 下载失败: {e}")
                self.installing = False

        threading.Thread(target=download_thread, daemon=True).start()
    
    def on_ready(self):
        """LLM 就绪"""
        self.available = True
        self.installing = False
        self.tab.llm_status.config(text="●", foreground="green")
        self.tab._append_message("system", f"✅ LLM 已就绪！模型: {self.model}")
        self.tab._append_message("assistant", "🧠 本地 LLM 已启用，可以智能理解你的需求了！")
    
    def debug_test(self):
        """调试测试"""
        self.tab._append_message("system", "🔍 开始测试 LLM...")

        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                models = [m["name"] for m in response.json().get("models", [])]
                self.tab._append_message("system", f"✅ Ollama 运行中，已安装: {models}")
            else:
                self.tab._append_message("system", f"❌ Ollama 异常: {response.status_code}")
                return
        except Exception as e:
            self.tab._append_message("system", f"❌ 连接失败: {e}")
            return

        test_prompt = "请用一句话介绍你自己"

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": test_prompt,
                    "temperature": 0.7,
                    "stream": False,
                    "max_tokens": 100
                },
                timeout=30
            )

            if response.status_code == 200:
                reply = response.json().get("response", "").strip()
                self.tab._append_message("assistant", f"🧠 LLM 回复: {reply}")
                self.tab._append_message("system", "✅ LLM 测试通过！")
            else:
                self.tab._append_message("system", f"❌ 测试失败: {response.status_code}")

        except Exception as e:
            self.tab._append_message("system", f"❌ 测试失败: {e}")
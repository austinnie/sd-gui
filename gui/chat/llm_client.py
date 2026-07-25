# gui/chat/llm_client.py
"""LLM客户端 - 封装Ollama调用"""

import time
import json
import requests
from typing import Optional, Dict, Callable


from utils.logger import get_logger

logger = get_logger(__name__)
class LLMClient:
    """LLM客户端 - 支持Ollama"""
    
    def __init__(self, model: str = "qwen2.5:1.5b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self._available = False
    
    def is_available(self) -> bool:
        """检查LLM是否可用"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if response.status_code == 200:
                models = [m["name"] for m in response.json().get("models", [])]
                self._available = self.model in models or self.model.split(":")[0] in str(models)
            return self._available
        except:
            return False
    
    def is_running(self) -> bool:
        """检查Ollama服务是否运行"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def generate(self, prompt: str, timeout: int = 30, 
                 max_tokens: int = 512, stream: bool = False,
                 on_chunk: Optional[Callable] = None) -> Optional[str]:
        """
        调用LLM生成
        """
        if not self._available:
            return None
        
        logger.info(f"📤 调用 LLM: {self.model} (超时: {timeout}s, max_tokens: {max_tokens})")
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "temperature": 0.7,
                        "stream": stream,
                        "max_tokens": max_tokens,
                        "top_p": 0.9,
                        "stop": ["\n\n", "正面提示词", "负面提示词"],
                    },
                    timeout=timeout,
                    stream=stream
                )
                
                if response.status_code != 200:
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    return None
                
                if stream:
                    return self._handle_stream_response(response, on_chunk)
                else:
                    result = response.json().get("response", "").strip()
                    logger.info(f"📥 LLM 响应: {len(result)} 字符")
                    return result
                    
            except requests.exceptions.Timeout:
                logger.info(f"⏱️ LLM 超时 ({timeout}s)，尝试 {attempt+1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return None
            except requests.exceptions.ConnectionError:
                logger.info(f"🔌 LLM 连接错误，尝试 {attempt+1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return None
        
        return None
    
    def _handle_stream_response(self, response, on_chunk: Optional[Callable] = None) -> str:
        """处理流式响应"""
        result = ""
        chunk_count = 0
        start_time = time.time()
        
        try:
            for line in response.iter_lines():
                if time.time() - start_time > 30:
                    break
                
                if line:
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            chunk = data["response"]
                            result += chunk
                            chunk_count += 1
                            if on_chunk and chunk_count % 5 == 0:
                                on_chunk(result)
                        
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
        except requests.exceptions.Timeout:
            logger.info(f"⚠️ 流式读取超时，已接收 {len(result)} 字符")
        
        return result.strip()
        

    def generate_with_fallback(self, prompt: str, fallback_prompt: str = None,
                                timeout: int = 30, max_tokens: int = 512) -> Optional[str]:
        """
        带降级的生成方法
        """
        result = self.generate(prompt, timeout, max_tokens)
        
        if result is None and fallback_prompt:
            logger.info(f"🔄 LLM 失败，使用降级方案")
            return self._simple_template_processing(fallback_prompt)
        
        return result
    
    def _simple_template_processing(self, text: str) -> str:
        """简单的模板处理（降级方案）"""
        # 从文本中提取关键信息
        words = text.split()
        if len(words) > 3:
            return f"a beautiful image of {text[:50]}"
        return "masterpiece, best quality, beautiful image"

    def get_status_message(self) -> str:
        """获取友好的状态消息"""
        if not self.is_running():
            return "⚠️ Ollama 服务未运行\n💡 请安装并启动 Ollama: ollama serve"
        if not self.is_available():
            return f"⚠️ 模型 {self.model} 未下载\n💡 请运行: ollama pull {self.model}"
        return "✅ LLM 服务正常"
        
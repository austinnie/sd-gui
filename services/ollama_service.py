# services/ollama_service.py
"""Ollama 服务 - 兼容旧接口"""

from .llm_service import llm_service

# 为了兼容 chat_tab 的旧代码，提供别名
OllamaManager = llm_service
ollama_manager = llm_service
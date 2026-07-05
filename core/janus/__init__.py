# core/janus/__init__.py
"""
Janus-Pro 多功能模块
"""

from .loader import JanusLoader, janus_loader
from .understand import JanusUnderstand
from .generate import JanusGenerate
from .chat import JanusChat

# 全局实例
janus_understand = JanusUnderstand()
janus_generate = JanusGenerate()
janus_chat = JanusChat()

__all__ = [
    'JanusLoader',
    'janus_loader',
    'JanusUnderstand',
    'janus_understand',
    'JanusGenerate',
    'janus_generate',
    'JanusChat',
    'janus_chat',
]
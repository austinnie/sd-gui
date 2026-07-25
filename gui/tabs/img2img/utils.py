# gui/tabs/img2img/utils.py
"""图生图辅助函数"""

from datetime import datetime


def log(msg):
    """打印日志"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def safe_del(obj):
    """安全删除对象"""
    try:
        if obj is not None:
            del obj
    except:
        pass


def auto_shorten_prompt(prompt, max_len=350):
    """自动精简提示词"""
    if not prompt or len(prompt) <= max_len:
        return prompt
    
    parts = [p.strip() for p in prompt.split(',') if p.strip()]
    seen = set()
    unique_parts = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            unique_parts.append(p)
    unique_parts.sort(key=lambda x: len(x), reverse=True)
    result = []
    current_len = 0
    for part in unique_parts:
        add_len = len(part) + 2
        if current_len + add_len <= max_len:
            result.append(part)
            current_len += add_len
    if not result:
        return prompt[:max_len]
    shortened = ", ".join(result)
    if len(shortened) < len(prompt):
        print(f"✂️ 提示词已精简: {len(prompt)} -> {len(shortened)} 字符")
    return shortened
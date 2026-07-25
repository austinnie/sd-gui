# gui/tabs/txt2img/callbacks.py
"""文生图进度回调"""

import time


class Txt2ImgStepCallback:
    """文生图步骤进度回调"""
    
    def __init__(self, progress_callback, total_steps, start_time, cancel_flag_ref, source=""):
        self.progress_callback = progress_callback
        self.total_steps = total_steps
        self.start_time = start_time
        self.last_percent = 0
        self.cancel_flag_ref = cancel_flag_ref
        self.source = source
        
    def __call__(self, pipe, step, timestep, callback_kwargs):
        if self.cancel_flag_ref and callable(self.cancel_flag_ref):
            if self.cancel_flag_ref():
                raise Exception("用户取消了生成")
        elif self.cancel_flag_ref and hasattr(self.cancel_flag_ref, 'get'):
            if self.cancel_flag_ref.get():
                raise Exception("用户取消了生成")
        
        current_step = step + 1
        percent = current_step / self.total_steps
        if percent - self.last_percent >= 0.02 or current_step == self.total_steps:
            self.last_percent = percent
            elapsed = time.time() - self.start_time
            if current_step > 0:
                eta = (elapsed / current_step) * (self.total_steps - current_step)
                eta_str = f"预计剩余: {int(eta//60)}分{int(eta%60)}秒" if eta > 60 else f"预计剩余: {eta:.0f}秒"
            else:
                eta_str = "计算中..."
            self.progress_callback(percent, f"🎨 步骤 {current_step}/{self.total_steps} | {eta_str}")
        return callback_kwargs
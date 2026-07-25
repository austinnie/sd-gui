# gui/tabs/img2img/callbacks.py
"""图生图进度回调"""

import time


class Img2ImgStepCallback:
    """图生图步骤进度回调"""
    
    def __init__(self, progress_callback, total_steps, start_time, cancel_flag_ref,
                 img_idx, var_idx, total_imgs, total_vars, source=""):
        self.progress_callback = progress_callback
        self.total_steps = total_steps
        self.start_time = start_time
        self.last_percent = 0
        self.cancel_flag_ref = cancel_flag_ref
        self.img_idx = img_idx
        self.var_idx = var_idx
        self.total_imgs = total_imgs
        self.total_vars = total_vars
        self.source = source
        
    def __call__(self, pipe, step, timestep, callback_kwargs):
        if self.cancel_flag_ref:
            if callable(self.cancel_flag_ref):
                if self.cancel_flag_ref():
                    raise Exception("用户取消了生成")
            elif hasattr(self.cancel_flag_ref, 'get') and self.cancel_flag_ref.get():
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
            completed_before = self.img_idx * self.total_vars + self.var_idx
            step_progress = (step + 1) / self.total_steps
            overall_progress = (completed_before + step_progress) / (self.total_imgs * self.total_vars)
            self.progress_callback(overall_progress, 
                f"🎨 图片 {self.img_idx+1}/{self.total_imgs}，变体 {self.var_idx+1}/{self.total_vars} - 步骤 {current_step}/{self.total_steps} | {eta_str}")
        return callback_kwargs
# gui/tabs/img2img/mask_editor.py
"""遮罩编辑器"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw


class MaskEditor:
    """遮罩编辑器"""
    
    def __init__(self, tab):
        self.tab = tab
        self.app = tab.app
        self.mask_image = None
    
    def open_editor(self):
        """打开遮罩涂抹窗口"""
        if not self.tab.selected_images:
            messagebox.showwarning("提示", "请先选择图片")
            return
        
        mask_window = tk.Toplevel(self.app.root)
        mask_window.title("手动涂抹遮罩 - 红色区域将被重绘")
        mask_window.geometry("800x800")
        
        img_path = self.tab.selected_images[0]
        pil_img = Image.open(img_path).convert("RGB")
        max_size = 700
        pil_img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        self._display_img = ImageTk.PhotoImage(pil_img)
        
        mask_layer = Image.new("RGBA", pil_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(mask_layer)
        
        canvas = tk.Canvas(mask_window, width=pil_img.width, height=pil_img.height)
        canvas.pack(pady=10)
        
        canvas.create_image(0, 0, anchor="nw", image=self._display_img)
        self._mask_id = canvas.create_image(0, 0, anchor="nw", image=None)
        
        drawing = False
        last_x, last_y = None, None
        brush_size = 15
        
        def on_mouse_down(event):
            nonlocal drawing, last_x, last_y
            drawing = True
            last_x, last_y = event.x, event.y
        
        def on_mouse_move(event):
            nonlocal drawing, last_x, last_y
            if drawing and last_x is not None:
                draw.ellipse(
                    [last_x - brush_size, last_y - brush_size,
                     last_x + brush_size, last_y + brush_size],
                    fill=(255, 0, 0, 180)
                )
                mask_tk = ImageTk.PhotoImage(mask_layer)
                canvas.itemconfig(self._mask_id, image=mask_tk)
                canvas.image = mask_tk
                last_x, last_y = event.x, event.y
        
        def on_mouse_up(event):
            nonlocal drawing, last_x, last_y
            drawing = False
            last_x, last_y = None, None
        
        canvas.bind("<Button-1>", on_mouse_down)
        canvas.bind("<B1-Motion>", on_mouse_move)
        canvas.bind("<ButtonRelease-1>", on_mouse_up)
        
        btn_frame = ttk.Frame(mask_window)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="✅ 保存遮罩并关闭", 
                   command=lambda: self._save_mask(mask_layer, mask_window)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ 取消", command=mask_window.destroy).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(mask_window, text="💡 在图片上涂抹红色区域，这些区域将被重新生成（用于去除衣物等）").pack(pady=5)
    
    def _save_mask(self, mask_layer, window):
        """保存遮罩"""
        alpha = mask_layer.split()[3]
        mask = alpha.point(lambda p: 255 if p > 0 else 0)
        self.tab.mask_image = mask
        window.destroy()
        self.tab.update_status("✅ 遮罩已保存，可以开始图生图了")
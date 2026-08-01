# prompts/pencil_warrior.py
# 铅笔素描 高精度赛博机甲战姬 - 丰富场景与姿态扩展版

STYLE = {
    "pencil_warrior": {
        "folder": "素描_赛博机甲",
        "strength": 0.35,
        
        # ==================== 主体 (14种) ====================
        "subjects": [
            # --- 1. 环形实验室线稿 (还原你发的图，但改为铅笔) ---
            "Masterpiece pencil sketch, distinct human head and face, long white hair separated from background arcs, female cybernetic warrior, intricate translucent outer shell, visible mechanical internals, fine wireframe, sharp expression. Standing in high-tech circular lab surrounded by glowing holographic arcs. High contrast black and white pencil draft on white paper, sci-fi concept art.",
            
            # --- 2. 雨中战斗线稿 ---
            "Highly detailed graphite pencil sketch, female cybernetic warrior in combat stance, standing on a rainy futuristic city street at night. Long flowing white hair, sharp expression. Holding a high-tech glowing rifle. Intricate translucent outer shell, detailed mechanical internals drawn with fine lines. Neon reflections sketched with crosshatching. 2D manga draft style on white paper.",
            
            # --- 3. 驾驶舱内线稿 ---
            "Pencil draft, female cybernetic warrior sitting in a futuristic mecha cockpit. Long flowing white hair, focused expression. Large holographic HUD sketched with precise geometric lines. Intricate translucent armor, mechanical internals. High-tech pilot suit. Fine linework and shading. Black and white drawing on white paper.",
            
            # --- 4. 赛博小巷回眸线稿 ---
            "Pencil sketch, side profile of a cybernetic female warrior, turning her head to look back over her shoulder. Long white hair flowing, determined gaze. Standing in a dark cyberpunk alleyway illuminated by neon signs (shaded with varying pencil pressure). Intricate translucent outer shell. Fine crosshatching, detailed wires and joints. 2D hand-drawn style, white background.",
            
            # --- 5. 极简纯净空间线稿 ---
            "Pencil art, full-body shot of a cybernetic warrior in dynamic combat pose. Long white hair, sharp expression. Set in a minimal pure white studio. The pure white background highlights the intricate translucent outer shell, fiber-optic nervous system drawn as precise linework, and precision mechanical engineering design. Fine detailed shading, white page, masterpiece.",
            
            # --- 6. 单手巨剑线稿 ---
            "Detailed pencil drawing, female cybernetic warrior, holding a massive mechanical greatsword over her shoulder. Long flowing white hair, glowing cybernetic eyes (shaded dark). Confident and powerful stance. Standing in a futuristic hangar. Fine linework, intricate translucent shell. High contrast black and white art.",
            
            # --- 7. 残破废墟线稿 ---
            "Rough pencil sketch, female cybernetic warrior standing on a ruined sci-fi battlefield. Long white hair blowing in the wind, determined expression. Holding a high-tech handgun. Armor slightly damaged (drawn with rough pencil marks). Translucent outer shell, mechanical joints. Fine linework and grey shading, white background.",
            
            # --- 8. 高度特写线稿 ---
            "Close-up waist-up pencil drawing of a female cybernetic warrior in tactical stance. Long white hair, sharp expression. Intricate translucent outer shell, detailed mechanical joints. Holding a mechanical katana. Fine linework, detailed shading, 2D manga draft style, white page.",
            
            # --- 9. 坐姿静养线稿 ---
            "Pencil sketch, cybernetic female warrior sitting with legs crossed on a futuristic floating platform. Long white hair resting on her shoulders. Her mechanical katana resting across her lap. Intricate translucent armor, fine linework. High-tech lab background, soft pencil shading, 2D artwork.",
            
            # --- 10. 空中悬浮线稿 ---
            "Dynamic pencil sketch, full-body shot of a cybernetic female warrior floating in mid-air. Long flowing white hair. Arms spread wide, energy shields formed by thick pencil lines. Intricate translucent outer shell, mechanical internals. Futuristic city background. High contrast pencil draft.",
            
            # --- 11. 荒野异星线稿 ---
            "Pencil sketch, full-body shot of a cybernetic warrior standing in a desolate sci-fi desert under a dark cloudy sky. Long white hair blowing. Translucent outer shell, detailed joints, mechanical plating. Heavy industrial sci-fi armor, rough pencil lines, white paper.",
            
            # --- 12. 武术起手式线稿 ---
            "Elegant pencil sketch, cybernetic female warrior in a beautiful martial arts stance. One arm extended, one hand resting on her katana. Long white hair flowing gracefully. Intricate translucent outer shell. Fine linework, precision shading. Sci-fi laboratory background, white paper.",
            
            # --- 13. 赛博地铁站线稿 ---
            "Graphite pencil sketch, full-body shot of a cybernetic warrior standing in an abandoned futuristic subway station. Long white hair, sharp expression, holding a glowing blade (shaded with a bright white highlight). Fine linework, deep shadows, white background.",
            
            # --- 14. 裸机骨架线稿 ---
            "Intricate pencil drawing, close-up full-body shot of a female cybernetic warrior. The outer shell is completely removed, revealing the highly complex mechanical internals, fiber-optic lines drawn with thin crosshatching. Her face remains perfectly human, beautiful white hair flowing. Standing in a high-tech repair bay. Fine pencil art, white background."
        ],
        
        # ==================== 风格 (3种) ====================
        "styles": [
            "pencil sketch, fine linework, shading, white background, 2D illustration style",
            "graphite pencil art, high contrast black and white, intricate line details, raw sketch aesthetic",
            "manga draft style, detailed structural guides, unfinished rough draft, fine cross-hatching"
        ],
        
        # ==================== 情绪 (4种) ====================
        "moods": [
            "elegant, futuristic, detailed, mechanical",
            "clean, precise, artistic, sophisticated",
            "ethereal, beautiful, cool, cybernetic",
            "graceful, serene, advanced, fine"
        ],
        
        # ==================== 内容文本开关 ====================
        "content_texts": [] 
    }
}
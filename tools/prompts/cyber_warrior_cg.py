# prompts/cyber_warrior_cg.py
# 超写实 3D 赛博机甲战姬 - 丰富场景与姿态扩展版

STYLE = {
    "cyber_warrior_cg": {
        "folder": "写实赛博机甲",
        "strength": 0.45,
        
        # ==================== 主体 (14种) ====================
        "subjects": [
            # --- 1. 你发的原版 (双持武士刀+实验室) ---
            "Masterpiece, top-tier aesthetic, full-body shot of a sophisticated female cybernetic warrior, intricate translucent outer shell showcasing complex mechanical internals and glowing fiber-optic nervous system underneath. Long flowing white hair, glowing cybernetic eyes, determined and sharp expression. Standing in a high-tech science laboratory surrounded by glowing holographic displays, complex network data visualizer screens, and abstract sci-fi data lines. Dynamic combat stance, dual wielding mechanical katanas, metallic plating with detailed joints, wires, cables, and precision mechanical engineering design. Photorealistic, hyper-detailed, cinematic soft lighting, 8k resolution, sci-fi concept art style.",
            
            # --- 2. 雨中战斗 (场景变换) ---
            "Masterpiece, top-tier aesthetic, full-body shot of a female cybernetic warrior in a combat stance, standing on a rainy futuristic city street at night. Long flowing white hair, wet and glowing, sharp expression, glowing cybernetic eyes. She holds a high-tech glowing rifle. Intricate translucent outer shell, glowing fiber-optic nervous system. Neon lights reflecting off her mechanical armor, water splashing, cinematic soft lighting, photorealistic, hyper-detailed, 8k, sci-fi concept art.",
            
            # --- 3. 驾驶舱/机甲内部 (场景变换) ---
            "Masterpiece, top-tier aesthetic, female cybernetic warrior sitting in the cockpit of a futuristic mecha. Long flowing white hair, calm focused expression. Large holographic HUD displays floating in front of her. Intricate translucent armor, glowing cybernetic internal structure. High-tech pilot suit, glowing buttons and data streams. Photorealistic, hyper-detailed, cinematic soft lighting, 8k, sci-fi concept art.",
            
            # --- 4. 赛博朋克小巷 (侧身/回眸) ---
            "Masterpiece, top-tier aesthetic, side profile shot of a cybernetic female warrior, turning her head to look back over her shoulder. Long white hair flowing, determined gaze. She is standing in a dark, wet cyberpunk alleyway illuminated by pink and blue neon signs. Intricate translucent outer shell, glowing fiber-optic lines. Metallic plating, detailed joints, wires. Photorealistic, hyper-detailed, cinematic lighting, 8k, sci-fi concept art.",
            
            # --- 5. 极简纯净空间 (突出机甲质感) ---
            "Masterpiece, top-tier aesthetic, full-body shot of a cybernetic warrior in a dynamic combat pose. Long white hair, sharp expression. Set in a minimal pure white high-tech studio, no background distractions. The pure white background highlights the intricate translucent outer shell, glowing fiber-optic nervous system, and precision mechanical engineering design. Photorealistic, hyper-detailed, cinematic soft lighting, 8k, sci-fi concept art.",
            
            # --- 6. 单手巨剑 (武器变换) ---
            "Masterpiece, top-tier aesthetic, full-body shot of a female cybernetic warrior, holding a massive glowing mechanical greatsword over her shoulder. Long white hair flowing, glowing cybernetic eyes, confident and powerful stance. Standing in a futuristic hangar, glowing displays. Intricate translucent shell, glowing fiber-optic nervous system. Photorealistic, hyper-detailed, cinematic lighting, 8k, sci-fi concept art.",
            
            # --- 7. 残破的废墟 (战损背景) ---
            "Masterpiece, top-tier aesthetic, female cybernetic warrior standing triumphantly on a ruined sci-fi battlefield. Long white hair blowing in the wind, determined expression. Holding a high-tech handgun, armor slightly damaged, energy sparks flying. Detailed mechanical joints, wires, cables, translucent outer shell. Photorealistic, hyper-detailed, cinematic dramatic lighting, 8k, sci-fi concept art.",
            
            # --- 8. 高度特写/战术姿态 ---
            "Masterpiece, top-tier aesthetic, close-up waist-up shot of a female cybernetic warrior in a tactical stance. Long white hair, glowing cybernetic eyes, intense sharp expression. Intricate translucent outer shell, glowing fiber-optic nervous system. Holding a mechanical katana with both hands. Cinematic soft lighting, 8k, photorealistic sci-fi concept art.",
            
            # --- 9. 坐姿/归鞘 (静态放松) ---
            "Masterpiece, top-tier aesthetic, a cybernetic female warrior sitting with her legs crossed on a futuristic floating platform. Long flowing white hair resting on her shoulders, peaceful but sharp expression. Her mechanical katana resting across her lap. Intricate translucent armor, glowing internal lines. High-tech lab background, soft holographic glow, photorealistic, hyper-detailed, cinematic lighting, 8k, sci-fi art.",
            
            # --- 10. 空中悬浮/能量展开 ---
            "Masterpiece, top-tier aesthetic, dynamic full-body shot of a cybernetic female warrior floating in mid-air. Long flowing white hair, glowing eyes. Arms spread wide, energy shields forming around her. Intricate translucent outer shell, glowing fiber-optic nervous system fully visible. Futuristic city in the background. Cinematic soft lighting, photorealistic, hyper-detailed, 8k, sci-fi concept art.",
            
            # --- 11. 荒野/自然 (赛博与原始对比) ---
            "Masterpiece, top-tier aesthetic, full-body shot of a cybernetic warrior standing in a desolate sci-fi desert under a dark cloudy sky. Long white hair blowing, glowing cybernetic eyes, sharp and commanding expression. Translucent outer shell, detailed joints, mechanical plating. Heavy industrial sci-fi armor, photorealistic, hyper-detailed, cinematic dramatic lighting, 8k, sci-fi concept art.",
            
            # --- 12. 舞蹈/武术起手式 (动态美学) ---
            "Masterpiece, top-tier aesthetic, cybernetic female warrior in a beautiful martial arts stance. One arm extended, one hand resting on her katana. Long white hair flowing gracefully. Intricate translucent outer shell, glowing fiber-optic nervous system. Elegant, precise, lethal. Sci-fi laboratory background, photorealistic, hyper-detailed, cinematic soft lighting, 8k, sci-fi concept art.",
            
            # --- 13. 赛博朋克地铁站 (日常/危机时刻) ---
            "Masterpiece, top-tier aesthetic, full-body shot of a cybernetic warrior standing in an abandoned futuristic subway station. Long white hair, sharp expression, holding a glowing blade. Neon lights flickering around her, broken glass on the floor. Photorealistic, hyper-detailed, cinematic moody lighting, 8k, sci-fi concept art.",
            
            # --- 14. 裸机骨架 (弱化外壳，强化内部机械) ---
            "Masterpiece, top-tier aesthetic, close-up full-body shot of a female cybernetic warrior. The outer shell is completely removed, revealing the highly complex mechanical internals, glowing fiber-optic nervous system, and precision mechanical engineering design. Her face remains perfectly human, beautiful white hair flowing. Standing in a high-tech repair bay. Photorealistic, hyper-detailed, cinematic soft lighting, 8k, sci-fi concept art."
        ],
        
        # ==================== 风格 (3种) ====================
        "styles": [
            "photorealistic 3D CGI sci-fi art, cinematic lighting, hyper-detailed, 8k",
            "concept art, masterpiece, top-tier aesthetic, soft studio lighting",
            "hyper-realistic CGI, top-tier aesthetic, sci-fi character design"
        ],
        
        # ==================== 情绪 (4种) ====================
        "moods": [
            "futuristic, powerful, elegant, dangerous",
            "ethereal, high-tech, commanding, sharp",
            "cold, precise, divine, cosmic",
            "mysterious, beautiful, resilient, badass"
        ],
        
        # ==================== 内容文本开关 ====================
        "content_texts": [] 
    }
}
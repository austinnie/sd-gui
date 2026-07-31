# prompts/supercars.py
# 世界顶级跑车/概念车 超高精度生成配置
# 风格包含：法拉利、兰博基尼、保时捷、迈凯伦、布加迪、柯尼塞格

STYLE = {
    "supercars": {
        "folder": "世界名车",
        "strength": 0.35,
        
        # ==================== 主体 (16种，涵盖各大品牌与姿态) ====================
        "subjects": [
            # --- 法拉利 (Ferrari) 经典红 ---
            "ultra-realistic 3D render of a Ferrari supercar, sleek aerodynamic body, vibrant red paint, detailed carbon fiber, in a brightly lit modern studio, pure white background, automotive photography, cinematic masterpiece",
            "minimalist pencil sketch of a Ferrari, flowing aerodynamic curves, low-profile design, iconic Ferrari silhouette, black and white lineart, rough engineering draft, clean white page",
            "front view of a Ferrari, aggressive front grill, sharp headlights, wide stance, extremely detailed metallic reflections, studio lighting, masterpiece 3D CGI render",
            
            # --- 兰博基尼 (Lamborghini) 棱角锋芒 ---
            "Lamborghini Aventador, sharp geometric lines, glossy yellow paint, iconic scissor doors open, low stance, hyper-realistic photography, stark white studio background, 8k resolution",
            "side profile of a Lamborghini, futuristic wedge shape, massive rear diffuser, crisp pencil lineart, blueprint aesthetic, industrial design concept, minimalist black and white",
            "Lamborghini rear view, active rear wing, aggressive exhaust, glowing taillights, dramatic shadows, sleek automotive 3D art, masterpiece composition",
            
            # --- 保时捷 (Porsche) 经典流线 ---
            "Porsche 911, classic timeless silhouette, sleek silver paint, iconic round headlights, low slung profile, cinematic studio lighting, highly detailed CG illustration, pure white background",
            "Porsche turbo, rear-engine layout sketch, smooth curved roofline, exquisite engineering drawing, raw pencil draft, high precision automotive lineart, white page",
            "interior view of a Porsche, three-spoke steering wheel, carbon fiber dashboard, precision engineering, detailed digital rendering, masterpiece automotive photography",
            
            # --- 迈凯伦/布加迪/柯尼塞格 (Hypercars) ---
            "McLaren F1, sleek aerodynamic teardrop shape, carbon fiber bodywork, orange livery, front-facing view, hyper-detailed 3D render, studio lighting, pure white backdrop",
            "Bugatti Chiron, massive W16 engine reveal, intricate mechanical detail, aerodynamic curves, futuristic silver and blue paint, high-fidelity CGI masterpiece",
            "Koenigsegg Jesko, angular hypercar, huge rear wing, speed-focused design, raw graphite pencil sketch, aggressive lines, minimalist engineering draft",
            
            # --- 通用姿态与概念设计 ---
            "low-angle shot of a futuristic supercar, massive exposed wheels, advanced active aerodynamics, metallic pearl white paint, race track vibe, car photography masterpiece",
            "classic racing car side profile, number decals, streamlined driver's cabin, rough engineer's notebook sketch, nostalgic simple lineart, pure white background",
            "supercar in a high-speed motion blur, dynamic curves, fast and furious aesthetic, cinematic lighting, advanced automotive 3D art"
        ],
        
        # ==================== 风格 (4种) ====================
        "styles": [
            "hyper-realistic 3D CGI render, automotive photography, studio lighting, perfect reflections, masterpiece",
            "industrial design blueprint, crisp pencil lineart, minimalist black and white, white background",
            "8k automotive illustration, vibrant colors, aggressive angles, cinematic composition",
            "rough pencil draft, quick sketch, minimalist automotive contour, white page"
        ],
        
        # ==================== 情绪/氛围 (4种) ====================
        "moods": [
            "sleek, powerful, aggressive, fast",
            "elegant, timeless, luxurious, refined",
            "futuristic, sharp, mechanical, precise",
            "classic, dynamic, bold, energetic"
        ],
        
        # ==================== 内容文本开关 ====================
        "content_texts": [] 
    }
}
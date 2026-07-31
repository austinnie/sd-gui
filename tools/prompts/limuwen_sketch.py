# prompts/limuwen_sketch.py
# 仙逆：李慕婉 唯美华丽人像

STYLE = {
    "limuwen_sketch": {
        "folder": "仙逆_李慕婉",
        "strength": 0.45,  # 图生图推荐0.45，文生图此参数无效
        
        # ==================== 主体 (10种) ====================
        "subjects": [
            # --- 风格1：高贵典雅的国漫风 (高质感) ---
            "beautiful Li Muwen from Xian Ni, elegant mature woman, wearing a flowing semi-translucent white fairy dress, delicate collarbones, soft skin, long flowing dark hair, 3D CGI anime style, exquisite lighting, light mist around, intricate detailed clothing, masterpiece, high quality",
            
            # --- 风格2：微微展露身段的唯美风 ---
            "Li Muwen, graceful waifu, wearing a deep v-neck elegant traditional Chinese dress, beautiful chest and shoulder line, long wavy hair, delicate beautiful face, soft lighting, pastel aesthetic, anime character illustration, beautiful portrait, ethereal atmosphere",
            
            # --- 风格3：冷艳无双的战斗仙子 ---
            "Li Muwen in a fighting stance, elegant flowing ancient robes, wind blowing through her hair, soft fabric revealing a graceful silhouette, beautiful facial features, high fantasy style, masterful composition, high definition, magical glowing rune background",
            
            # --- 风格4：温柔特写 (适合做壁纸) ---
            "close-up portrait of Li Muwen, gentle smile, beautiful eyes, flushed cheeks, elegant long neck, light jewelry, soft skin, romantic lighting, beautiful anime art style, sophisticated design, pure and alluring",
            
            # --- 风格5：午夜/冷色调 凄美风 ---
            "Li Muwen under moonlight, graceful figure, elegant gown with subtle lace details, dark atmosphere, dramatic shadows, beautiful face, fantasy anime portrait, cinematic lighting, highly detailed illustration",
            
            # --- 风格6：专注画脸与体态 ---
            "Li Muwen looking back over shoulder, elegant expression, loose glowing hair, luxurious silk ancient dress, perfect body proportion, 3D anime render, detailed fabric folds, beautiful aesthetic, gorgeous background scenery",
            
            # --- 风格7：现代国漫厚涂 (上色) ---
            "semi-realistic digital painting of Li Muwen, fairy goddess vibe, sexy but elegant posture, revealing shoulders and arms, beautiful skin texture, soft light, gentle expression, ultimate detail, masterpiece 4k",
            
            # --- 风格8：黑白写实/高对比度 (更适合你的铅笔习惯) ---
            "Li Muwen portrait, monochrome pencil digital drawing, graceful female figure, elegant robe dropping off her shoulder, sexy but artistic composition, beautiful face, minimalist black and white aesthetic, raw art style",
            
            # --- 风格9：CG 官方画册风 ---
            "3D CG character Li Muwen, beautiful fantasy girl, elegant pose, delicate long dress exposing beautiful back and arms, lush background, detailed hair, artistic masterpiece, stunning concept art",
            
            # --- 风格10：清新唯美风 (克制且迷人) ---
            "Li Muwen, beautiful anime girl, gentle beauty, wearing thin white silk dress, graceful neck and chest, elegant hair blowing, soft glow, fantasy world, stunning digital art, 8k"
        ],
        
        # ==================== 风格 (5种) ====================
        "styles": [
            "3D CGI anime style, exquisite lighting, masterpiece, semi-realistic digital illustration",
            "fantasy anime art, soft pastel colors, beautiful rendering, high quality, elegant composition",
            "traditional Chinese fantasy aesthetic, gorgeous detailed clothing, beautiful lighting, concept art",
            "minimalist artistic portrait, elegant black and white, masterpiece drawing",
            "anime illustration, high-definition, cinematic lighting, 4k, masterpiece"
        ],
        
        # ==================== 情绪 (6种) ====================
        "moods": [
            "elegant, alluring, graceful, mysterious",
            "beautiful, gentle, captivating, soft",
            "serene, divine, ethereal, charming",
            "majestic, gorgeous, enchanting, passionate",
            "cold but beautiful, delicate, fascinating",
            "romantic, pure, seductive, timeless"
        ],
        
        # ==================== 内容文本开关 ====================
        "content_texts": [] 
    }
}
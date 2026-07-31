# prompts/anime_xxx_v4.py
# 动漫爱爱风格 - 完整分层版 (40主体 × 风格 × 情绪)

STYLE = {
    "anime_xxx_v4": {
        "folder": "动漫_40主体分层",
        "strength": 0.45,
        
        # ==================== 主体 (40种) ====================
        "subjects": [
            # ----- 单人诱惑 (17种) -----
            "anime woman, huge breasts, massive cleavage, seductive expression, long flowing hair, revealing outfit, sensual pose, perfect curves, bedroom setting",
            "anime maid, huge breasts, massive cleavage spilling out of maid outfit, french maid costume, fishnet stockings, seductive pose, holding feather duster, luxurious bedroom",
            "anime nurse, huge breasts, massive cleavage barely contained in tight nurse uniform, short white dress, fishnet stockings, naughty smile, medical setting",
            "anime teacher, huge breasts, massive cleavage in tight blouse, glasses, tight pencil skirt, stockings, holding pointer, classroom background, naughty smile",
            "anime bunny girl, huge breasts, massive cleavage, tight black bunny suit, fishnet stockings, bunny ears, bow tie, high heels, playful pose, casino background",
            "anime cat girl, huge breasts, massive cleavage, tight black cat suit, cat ears, tail, choker, high heels, playful pose, mysterious atmosphere",
            "anime shrine maiden, huge breasts, revealing miko outfit, white and red, seductive pose, traditional Japanese shrine background",
            "anime queen, huge breasts, revealing royal outfit, crown, holding scepter, commanding presence, throne room, sensual and dominant",
            "anime elf, huge breasts, long pointed ears, flowing silver hair, sheer translucent robes, visible body through thin fabric, magical forest",
            "anime demon girl, huge breasts, horns, wings, tail, revealing dark outfit, seductive expression, hellfire background, dark fantasy",
            "anime angel, huge breasts, white wings, flowing white robes, heavenly glow, cloudy sky background, divine beauty, ethereal and sensual",
            "anime bride, huge breasts, revealing wedding dress, sheer veil, visible body through thin fabric, seductive pose, romantic wedding setting",
            "anime woman, huge breasts prominently displayed, tight shiny latex catsuit, glossy black material, curves accentuated, futuristic or BDSM setting",
            "anime girl, huge breasts, tiny bikini, massive cleavage, perfect body, beach background, summer atmosphere, playful pose",
            "anime girl, huge breasts, yukata, loose fabric showing cleavage, traditional Japanese summer festival, soft lighting, playful expression",
            "anime athlete, huge breasts, tight sports bra and shorts, massive cleavage, fit body, gym background, sweat, dynamic pose",
            "anime schoolgirl, huge breasts, school uniform, tight white shirt, short skirt, innocent yet seductive, classroom background",
            "anime office lady, huge breasts, tight blouse, short skirt, stockings, glasses, seductive expression, office background",
            
            # ----- 性爱场景 (14种) 修正版 -----
            # 一男一女 (7种)
            "man and woman having sex in missionary position, man on top, woman lying down, intimate lovemaking, passionate, romantic atmosphere, bedroom setting, both bodies visible",
            "man and woman having sex in doggy style position, from behind, passionate sex, intimate, bedroom setting, both bodies visible, deep penetration",
            "man and woman having sex in cowgirl position, woman on top, riding, passionate lovemaking, intimate, bedroom setting, both bodies visible, woman in control",
            "man and woman having sex standing up from behind, passionate sex, intimate, bedroom or bathroom setting, both bodies visible, standing sex",
            "man and woman having sex in spooning position, side lying, intimate lovemaking, passionate, bedroom setting, both bodies visible, spooning sex",
            "woman giving oral sex to a man, blowjob, intimate, passionate, bedroom setting, both bodies visible",
            "man giving oral sex to a woman, cunnilingus, intimate pleasure, passionate, bedroom setting, both bodies visible",
            # 强制场景 (一男一女)
            "beautiful anime woman in forced submission, dominant male, intense expression, dark atmosphere, rough sex, power exchange, both bodies visible",
            
            # 女女 (1种)
            "two beautiful anime women making love, intimate embrace, kissing, sensual pose, soft romantic lighting, bedroom setting, yuri, girls love, lesbian",
            
            # 男男 (1种)
            "two handsome anime men making love, intimate embrace, passionate kiss, sensual pose, soft romantic lighting, bedroom setting, yaoi, boys love, gay",
            
            # 模糊性别/多人 (3种) - 让 SD 自己发挥
            "two people in 69 position, mutual oral, intimate pleasure, both bodies visible, mutual pleasure",
            "multiple people having group sex, threesome, passionate, intense, bedroom setting, all bodies visible, group sex",
            
            # 特殊 (2种) - 无性伴侣，但属于性爱主题
            "beautiful anime woman, artistic shibari rope bondage, red ropes wrapped around huge breasts and curvy body, sensual submission, intimate atmosphere, tasteful bondage art",
            "beautiful anime woman, tentacles wrapped around curvy body, huge breasts, sensual expression, fantasy atmosphere, dark magical setting, erotic fantasy art",
            
            # ----- 场景性爱 (9种) 修正 -----
            "man and woman having sex in bathroom, wet bodies, steam, passionate, intimate, shower sex",
            "man and woman having sex in kitchen, passionate, intimate, dramatic lighting, both bodies visible, forbidden kitchen sex",
            "man and woman having sex in office, passionate, intimate, desk setting, dramatic lighting, both bodies visible, office romance",
            "man and woman having sex in classroom, passionate, intimate, school setting, dramatic lighting, both bodies visible, forbidden classroom",
            "man and woman having sex outdoors, passionate, intimate, forest or nature setting, moonlight, both bodies visible, outdoor sex",
            "man and woman having sex on beach, passionate, intimate, sunset, ocean waves, both bodies visible, beach sex",
            "man and woman having sex in hot spring, wet bodies, steam, passionate, intimate, both bodies visible, onsen sex",
            "man and woman having sex in car, passionate, intimate, cramped space, both bodies visible, car sex",
            "close-up of huge anime breasts, massive cleavage, big boobs, perfect curves, seductive, erotic"
        ],
        
        # ==================== 风格 (12种) ====================
        "styles": [
            "anime art style, vibrant colors, high quality, detailed",
            "anime art style, dramatic lighting, high quality, detailed",
            "anime art style, soft romantic lighting, intimate atmosphere, high quality",
            "anime art style, bedroom setting, soft warm glow, intimate",
            "anime art style, classroom background, soft natural light, detailed",
            "anime art style, office background, dramatic shadows, professional",
            "anime art style, magical forest, ethereal glow, fantasy",
            "anime art style, hellfire background, intense dramatic, dark fantasy",
            "anime art style, heavenly clouds, soft golden lighting, divine",
            "anime art style, festival setting, warm lantern glow, celebratory",
            "anime art style, gym background, bright lighting, energetic",
            "anime art style, beach background, summer sun, vibrant"
        ],
        
        # ==================== 情绪 (8种) ====================
        "moods": [
            "seductive and intimate",
            "playful and flirtatious", 
            "powerful and commanding",
            "innocent yet sensual",
            "passionate and romantic",
            "mysterious and forbidden",
            "joyful and energetic",
            "dark and intense"
        ]
    }
}
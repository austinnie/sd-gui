# prompts/pencil_sketch_v2.py
# 铅笔简笔画/二次元人体结构草稿风格（强化版）

STYLE = {
    "pencil_sketch_v2": {
        "folder": "铅笔草稿_人体结构",
        "strength": 0.35,  # 图生图推荐0.35-0.45，文生图此参数无效
        
        # ==================== 主体 (20种) ====================
        "subjects": [
            # --- 下半身与腿部特写 (4种) ---
            "close-up pencil sketch of anime character lower torso and legs, rough construction lines, circular anatomy guides, uncolored, graphite pencil on white paper, structural wireframe study, minimalist background",
            "pencil lineart of anime thighs and hips, skeleton wireframe overlay, proportion study, light shading, rough hand-drawn aesthetic, negative space, unfinished line work, isolated on white",
            "graphite sketch of manga legs, perspective foreshortening, circular joint markers, rough outline, unfinished masterpiece, textural drawing on blank notebook paper",
            "detailed pencil sketch of anime pelvis and legs, construction grid, proportion marks, basic anatomical mapping, raw draft, graphite medium, white page, no extra objects",

            # --- 上半身、头、手部特写 (4种) ---
            "pencil sketch of female anime character upper body, collarbone and shoulder structure, construction circles, wireframe perspective, anatomy study, black and white on white paper",
            "anime character head and face construction, Loomis method head structure, crossed crosshairs, structural circle guides, realistic pencil lineart, blank background",
            "close-up sketch of anime hands and arms, geometric breakdown of joints, palm and finger structure study, detailed wireframe pencil drawing, minimalist composition",
            "bust portrait pencil sketch of anime girl, structural breakdown of face and neck, visible drawing guides and guidelines, rough shading, raw draft, white page",

            # --- 全身及透视练习 (4种) ---
            "full body pencil sketch of anime girl in dynamic pose, structural building blocks, joint circles, perspective grid overlay, geometric figure construction, unfinished art practice",
            "front view anime figure layout sketch, geometric body breakdown, stick figure to 3D block transition, rough pencil strokes, shading experiments, minimalist preliminary art",
            "anime character anatomy practice sketch, black and white pencil drawing, oval and circle structural guides, crossed construction lines, sketchy artistic style, manga draft layout",
            "anatomical figure sketch with grid lines, studying body proportions, pencil outline, subtle geometric aids, pure white background, uncolored rough draft",

            # --- 进阶：机械/机甲融合线稿 (4种) ---
            "mecha anime girl sketch, futuristic cyborg design, intricate mechanical joints, structural wireframe, blueprint style pencil drawing, highly detailed linework",
            "bio-mechanical anime character pencil sketch, skeleton structure, mechanical limb overlays, architectural design draft, precision wireframe art",
            "robot girl blueprint sketch, engineering construction lines, circle joint markers, technical pencil illustration, blank page, industrial design style",
            "highly detailed pencil drawing of anime android, exposed mechanical parts, structural analysis draft, futuristic concept art, symmetrical composition",

            # --- 🦋 新增：带翅膀的线稿/结构图 (4种) ---
            "symmetrical angel wings sketch on anime girl, structural wireframe breakdown of wings, detailed feather anatomy, engineering guide lines, pencil drawing on white paper, blueprint aesthetic",
            "mecha anime girl with mechanical wings, futuristic wing structure, cybernetic joints, open wingspan, highly detailed technical pencil sketch, precision linework",
            "anime character with large feathered angel wings, perspective construction lines, circular joint guides, crossed crosshairs, raw pencil draft, centered composition",
            "beautiful angel wings spread open, wireframe skeleton structure, study of wing mechanics, decorative structural sketch, high contrast lineart, poster-like composition"
        ],
        
        # ==================== 风格 (5种) ====================
        "styles": [
            "hand-drawn pencil sketch style, rough construction lines, circular guides, paper texture, 2d anime illustration draft, clean white page",
            "structural blueprint sketch, mathematical perspective, geometric construction, fine line, loose shading",
            "manga draft style, clean lines but unfinished, unpolished pencil work, minimalist black and white, sketchbook aesthetic",
            "study reference sketch, wireframe anatomy, cross lines, proportional guide, raw art style, empty surroundings",
            "rough architectural draft style, technical drawing, precise circular aids, loose strokes, high contrast graphite"
        ],
        
        # ==================== 情绪 (6种) ====================
        "moods": [
            "perfectly centered composition, ideal for digital wallpaper, clean white background, elegant negative space",
            "architectural blueprint aesthetic, engineering draft layout, high contrast minimalist art, crisp linework",
            "artistic poster design, balanced visual weight, modern industrial style, structural precision",
            "clean and symmetrical arrangement, decorative artistic layout, sophisticated print-like composition",
            "professional art portfolio presentation, harmonious negative space, clean visual experience, refined structural art",
            "minimalist wall art design, balanced proportions, centered subject, seamless decorative aesthetics"
        ],
        
        # ==================== 内容文本开关 (这里不需要文字，可以空着) ====================
        "content_texts": [] 
    }
}
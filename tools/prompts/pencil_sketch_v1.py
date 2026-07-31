# prompts/pencil_sketch_v1.py
# 铅笔简笔画/二次元人体结构草稿风格

STYLE = {
    "pencil_sketch_v1": {
        "folder": "铅笔草稿_人体结构",
        "strength": 0.35,  # 图生图推荐0.35-0.45，文生图此参数无效
        
        # ==================== 主体 (12种) ====================
        "subjects": [
            "close-up pencil sketch of anime character lower torso and legs, rough construction lines, circular anatomy guides, uncolored, graphite pencil on white paper, structural wireframe study",
            "rough pencil sketch of female anime character body, perspective study, visible sketching circles, unfinished art draft, thin pencil strokes, paper texture visible",
            "anime character anatomy practice sketch, black and white pencil drawing, oval and circle structural guides, crossed construction lines, sketchy artistic style, manga draft",
            "pencil lineart of anime thighs and hips, skeleton wireframe overlay, proportion study, light shading, rough hand-drawn aesthetic, negative space, unfinished line work",
            "art student drawing, anime figure sketch, body structure breakdown, loose pencil strokes, visible erased lines, circle joints, constructing human form, white background",
            "pencil doodle of anime character, lower body fragment, anatomy practice, construction circles and lines, simple shading, casual sketch, 2d lineart style",
            "graphite sketch of manga legs, perspective foreshortening, circular joint markers, rough outline, unfinished masterpiece, textural drawing on notebook paper",
            "anime pose study sketch, lines and curves, structural circles, pencil on paper, light sketchy lines, cross-hatching, preliminary drawing, open composition",
            "detailed pencil sketch of anime pelvis and legs, construction grid, proportion marks, basic anatomical mapping, raw draft, graphite medium, white page",
            "female character bottom half sketch, perspective lines, knee and hip joints circled, hand-drawn, sketchbook style, black and white, simple visual language",
            "unfinished pencil drawing of anime legs, organic lines, geometric construction overlay, beginner artist style, loose and dynamic, high contrast pencil trace",
            "anime figure layout sketch, geometric body breakdown, stick figure to shapes transition, rough pencil strokes, shading experiments, minimalist preliminary art"
        ],
        
        # ==================== 风格 (5种) ====================
        "styles": [
            "hand-drawn pencil sketch style, rough construction lines, circular guides, paper texture, 2d anime illustration draft",
            "traditional pencil drawing, graphite strokes, simple shading, raw art style, sketchbook scan",
            "structural anatomy sketch, blueprint of character, geometric construction, fine line, loose shading",
            "manga draft style, clean lines but unfinished, unpolished pencil work, minimalist black and white",
            "study reference sketch, wireframe anatomy, cross lines, proportional guide, naive drawing style"
        ],
        
        # ==================== 情绪 (6种) ====================
        "moods": [
            "artistic and raw, unfinished, sketchy, expressive",
            "structural, logical, educational, analytical, blueprint-like",
            "playful, casual doodle, relaxed, spontaneous",
            "serious art practice, detailed structural study, focused",
            "experimental, rough, gestural, energetic",
            "calm and minimalist, clean lines, empty white space"
        ],
        
        # ==================== 内容文本开关 (这里不需要文字，可以空着) ====================
        "content_texts": [] 
    }
}
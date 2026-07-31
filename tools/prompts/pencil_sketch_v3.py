# prompts/pencil_sketch_v3.py
# 铅笔简笔画/二次元人体结构草稿（全面丰富版：动态、体型、透视结构）

STYLE = {
    "pencil_sketch_v3": {
        "folder": "铅笔草稿_人体结构_v3",
        "strength": 0.35,  # 文生图此参数无效
        
        # ==================== 主体 (28种) ====================
        "subjects": [
            # ===== 1. 姿态与动态：常规站姿、坐姿、跪姿 =====
            "pencil sketch of anime girl in dynamic battle pose, full body structural anatomy, circular joint guides, sword pose, dynamic perspective, rough lineart, wireframe study, white background",
            "anime girl sitting on a stool, upper body structure breakdown, collarbone and ribcage perspective, crosshatch shading, cross construction lines, graphite pencil on white paper",
            "kneeling anime character pose, structural circles for hip and knee joints, anatomy study, sketchbook style draft, minimalist educational art, centered layout",
            "anime girl in relaxed walking pose, geometric body blocks, overlapping perspective, stick figure to shape construction, raw draft art, clean white page",
            "side profile full body sketch of anime character, spine curve and posture study, bone structure wireframe, traditional pencil lines, isolated on white",

            # ===== 2. 体型多样性：幼态、丰满、修长 =====
            "petite loli anime character full body sketch, smaller frame anatomy, construction circles, art student practice, detailed skeletal guide, clean lines, wallpaper composition",
            "curvy anime girl body study, thick thighs and hips, organic wireframe overlay, proportion mapping, rough pencil draft, structural aesthetic, large white space",
            "tall and slender anime girl full body anatomy, elongated proportions, perspective grid lines, ellipse guides for ribcage, side view sketch, minimalist art print",
            "muscular athletic anime girl figure sketch, defined muscle groupings, mechanical joint circles, anatomical structural blueprint, raw drawing, white background",

            # ===== 3. 胸部与上半身结构透视 (重点丰富) =====
            "upper torso sketch of anime girl, collarbone and shoulder anatomy, clear ribcage structure, geometric breast mapping with circular guides, graphite pencil, blueprint style",
            "bust portrait sketch, anatomical breakdown of female torso, chest volume study, structural circles for breast placement, crossed construction lines, rough shading, white page",
            "anime female character chest anatomy study, wireframe overlay, muscle and bone structure, geometric perspective, manga draft technique, centered composition",
            "torso twist pose sketch, dynamic chest and shoulder perspective, anatomical guides for ribcage and bust, loose pencil strokes, art school study, isolated on white",

            # ===== 4. 特殊动态：跳跃、下蹲、伸展 =====
            "jumping anime girl full body sketch, extreme foreshortening, leg and arm joints mapped with circles, dynamic structural wireframe, rough outline, minimalist background",
            "deep crouching anime character pose, knee and hip construction, focus on leg muscle structure, perspective study, graphite pencil on paper, blueprint layout",
            "stretching anime girl arms up, upper torso extension, chest and shoulder anatomical study, construction guide lines, raw artistic draft, centered wallpaper composition",

            # ===== 5. 机甲与科技结合 =====
            "cyberpunk anime girl sketch, mechanical skeletal structure, futuristic joints, tech blueprints, intricate wireframe, hard surface design, high contrast graphite draft",
            "bio-mechanical anime girl torso, exposed mechanical parts, structural breakdown of cybernetic chest, engineering diagrams, precision lineart, white background",
            "mecha girl shoulder and upper body draft, mechanical panel lines, joint circles and crosshairs, technical art style, high detail pencil illustration",

            # ===== 6. 带翅膀的动态 =====
            "anime girl with large feathered wings, dynamic pose, wing skeleton structure, perspective study, circular joint guides, high contrast pencil sketch, ideal wallpaper",
            "mechanical angel wings spread wide, anime girl flying pose, wing engineering draft, structural wireframe, technical blueprint aesthetic, raw pencil drawing",
            "angel wings anatomy study, focus on wing joints and feathers, crossed crosshairs, mechanical and organic fusion, centered symmetrical composition, white page"
        ],
        
        # ==================== 风格 (6种) ====================
        "styles": [
            "hand-drawn pencil sketch style, rough construction lines, circular joint guides, 2d anime illustration draft, clean white page",
            "structural blueprint sketch, mathematical perspective, geometric construction, fine line, loose cross shading",
            "manga draft style, detailed structural guides, unfinished rough draft, minimalist black and white, sketchbook aesthetic",
            "anatomical study sketch, precise wireframe, heavy graphite lines, raw art style, empty surroundings",
            "technical architectural draft style, precise circular aids, high contrast pencil, detailed engineering layout",
            "expressive gestural sketch, loose but accurate lines, structural focus, educational art style, clean composition"
        ],
        
        # ==================== 情绪 (6种) ====================
        "moods": [
            "perfectly centered composition, ideal for digital wallpaper, clean white background, elegant negative space",
            "architectural blueprint aesthetic, engineering draft layout, high contrast minimalist art, crisp linework",
            "artistic poster design, balanced visual weight, modern industrial style, structural precision",
            "clean and symmetrical arrangement, decorative artistic layout, sophisticated print-like composition",
            "professional art portfolio presentation, harmonious negative space, clean visual experience, refined structural art",
            "dynamic and energetic composition, expressive pose, art student study, balanced proportions"
        ],
        
        # ==================== 内容文本开关 ====================
        "content_texts": [] 
    }
}
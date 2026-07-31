# prompts/calligraphy_art.py
# 名贵字画风格 - 优雅书香，字画意境，佛经展示

STYLE = {
    "calligraphy_art": {
        "folder": "名贵字画",
        "strength": 0.35,
        
        # ==================== 主体 (20种) ====================
        "subjects": [
            # ----- 书法字画 (10种) -----
            "masterpiece calligraphy art, ancient Chinese scroll hanging on wall, powerful brush strokes, elegant ink calligraphy, meaningful Chinese characters, scholarly atmosphere, exquisite mounting, traditional xuan paper texture, artistic seal stamps",
            "beautiful Chinese calligraphy on rice paper, motivational ancient poem, flowing cursive script, imperial style, hanging scroll, wooden roller, elegant presentation, profound wisdom, inspirational words",
            "framed calligraphy artwork, bold brushwork, Chinese idiom about perseverance and success, hanging in elegant study room, refined taste, scholarly ambiance, artistic expression, cultural heritage",
            "ancient Chinese calligraphy masterpiece, famous poem by Li Bai, dynamic ink strokes, traditional mounting, hanging on bamboo scroll, scholarly atmosphere, timeless beauty, cultural treasure",
            "Buddhist sutra calligraphy, Heart Sutra written in elegant script, golden ink on dark paper, peaceful and serene, hanging in meditation room, spiritual ambiance, divine presence, sacred text",
            "Diamond Sutra calligraphy, exquisite brushwork, classical Chinese characters, hanging scroll with silk mounting, temple atmosphere, spiritual energy, ancient wisdom, Buddhist art",
            "motivational calligraphy, four-character idiom, powerful and inspiring message, bold ink strokes, hanging in office or study, professional ambiance, success motivation, daily inspiration",
            "Chinese poem calligraphy, Tang dynasty poetry, elegant running script, beautiful composition, hanging scroll with brocade mounting, scholarly atmosphere, poetic beauty, literary treasure",
            "ancient Chinese prose calligraphy, classical text, refined brushwork, traditional hanging scroll, library or study setting, intellectual atmosphere, cultural elegance, timeless wisdom",
            "Buddhist mantra calligraphy, Om Mani Padme Hum in elegant script, spiritual energy, Tibetan influence, hanging in peaceful shrine room, sacred atmosphere, meditation focus, divine blessing",
            
            # ----- 环境场景 (10种) -----
            "elegant study room, antique wooden desk, traditional Chinese calligraphy tools, ink stone, brush holder, rice paper, hanging scrolls on wall, refined atmosphere, scholarly elegance, warm lighting, peaceful ambiance",
            "traditional Chinese tea room, wooden tea table, tea set, hanging calligraphy scrolls, bamboo blinds, zen atmosphere, peaceful and quiet, scholarly retreat, meditation space, cultural elegance",
            "ancient Chinese library, wooden bookshelves filled with classical books, hanging calligraphy artworks, scholarly ambiance, warm lantern light, intellectual retreat, traditional architecture, literary haven",
            "Buddhist temple study, altar with Buddha statue, incense burner, hanging sutra calligraphy, spiritual atmosphere, peaceful sanctuary, meditation space, sacred ambiance, zen garden view",
            "elegant calligraphy studio, master calligrapher at work, brush in hand, ink on paper, artistic atmosphere, creative energy, traditional setting, scholar's retreat, cultural heritage",
            "zen meditation room, tatami mats, hanging zen calligraphy, simple and minimalist, peaceful atmosphere, natural light, bamboo elements, mindfulness space, spiritual sanctuary",
            "traditional Chinese scholar's study, antique furniture, calligraphy wall scrolls, ceramic tea set, bamboo curtain, serene atmosphere, intellectual pursuit, cultural refinement, timeless elegance",
            "Buddhist shrine room, golden Buddha statue, incense smoke, hanging sutra scrolls, peaceful ambiance, devotional space, spiritual energy, sacred art, meditation focus",
            "elegant art gallery, Chinese calligraphy exhibition, framed artworks on white walls, soft gallery lighting, refined atmosphere, cultural appreciation, artistic journey, masterpiece showcase",
            "peaceful garden pavilion, outdoor calligraphy display, stone tablets with inscriptions, nature surroundings, serene atmosphere, scholarly retreat, cultural landscape, harmonious setting"
        ],
        
        # ==================== 风格 (10种) ====================
        "styles": [
            "traditional Chinese ink painting style, xuan paper texture, soft ink tones, elegant brushwork",
            "ancient scroll style, aged paper, subtle yellowing, traditional mounting, brocade borders",
            "golden ink on dark paper, luxurious calligraphy style, divine radiance, Buddhist art aesthetic",
            "classical Chinese painting style, ink wash technique, refined brushwork, scholarly elegance",
            "ancient manuscript style, rice paper, traditional seals, red ink stamps, authentic appearance",
            "temple mural style, sutra writing, sacred geometry, divine presence, Buddhist art",
            "minimalist zen style, simple calligraphy, negative space, peaceful composition, meditation art",
            "imperial court style, ornate mounting, yellow silk brocade, royal elegance, prestigious art",
            "elegant literati style, scholarly refinement, bamboo and plum motifs, intellectual art",
            "classical album leaf style, fan-shaped mounting, delicate brushwork, collector's item"
        ],
        
        # ==================== 情绪 (8种) ====================
        "moods": [
            "peaceful and meditative",
            "inspiring and motivational", 
            "elegant and refined",
            "serene and spiritual",
            "profound and wise",
            "calm and contemplative",
            "majestic and awe-inspiring",
            "gentle and harmonious"
        ],
        
        # ==================== 内容主题 (可选扩展) ====================
        # 如需生成具体字画内容，可用这个字段
        "calligraphy_texts": [
            "静心",
            "禅",
            "道",
            "心经",
            "般若波罗蜜多心经",
            "金刚经",
            "缘",
            "空",
            "淡定",
            "宁静致远",
            "厚德载物",
            "天道酬勤",
            "上善若水",
            "观自在",
            "阿弥陀佛",
            "菩提本无树，明镜亦非台",
            "一切有为法，如梦幻泡影",
            "慈悲喜舍",
            "智慧如海",
            "不忘初心"
        ]
    }
}
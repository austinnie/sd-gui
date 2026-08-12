# tools/prompts/z_ksitigarbha_v3.py
# 地藏王菩萨 - SDXL 增强版提示词库（男性修正版）
# 针对 SDXL 模型优化：明确男性身份、更长提示词、更具体的视觉描述

STYLE = {
    "z_ksitigarbha_v3": {
        "folder": "3_AI画廊_地藏王菩萨_分层",
        "strength": 0.35,
        
        # ==================== 主体 (16种 - 全部明确男性) ====================
        "subjects": [
            # SDXL 提示词精简版（前 77 token 放最重要的描述）
            "Ksitigarbha Bodhisattva, male bodhisattva, masculine Asian monk, standing on red lotus, golden-red monastic robes, holding golden staff, radiant pearl, compassionate expression, male facial features, strong jaw, shaved head, golden halo, sacred Buddhist thangka, 8k, cinematic, photorealistic, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, Asian monk, meditation pose, lotus position, holding glowing jewel, golden staff beside, peaceful expression, male features, strong face, night sky backdrop, stars, moonlit, sacred art, 8k, cinematic, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, masculine Asian monk, royal pose on stone throne, holding glowing pearl, golden staff, red saffron robes, compassionate regal expression, male features, strong masculine face, golden light, sacred altar, thangka style, 8k, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, masculine Asian monk, standing at underworld gates, golden staff striking ground, pearl held high, piercing darkness, breaking chains, golden robes, fierce compassionate expression, male features, dramatic hellscape, epic, 8k, cinematic, masterpiece",
            
            # ----- 地狱救度 -----
            "Ksitigarbha Bodhisattva, male bodhisattva, masculine Asian monk, descending through underworld, golden halo piercing darkness, glowing pearl illuminating souls, staff ringing, saffron robe, tears of compassion, reaching to save souls, male features, hellish landscape, dramatic, 8k, cinematic, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, masculine Asian monk, standing in Avici Hell, island of golden light, pearl illuminating suffering faces, staff planted, monastic robes, compassionate gaze, male features, strong masculine face, dark contrast, epic religious art, 8k, cinematic, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, masculine Asian monk, breaking chains of hell, golden shockwaves, souls rising, golden-armored robe, fierce compassionate expression, male features, strong masculine face, dark hellscape, epic battle, 8k, cinematic, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, masculine Asian monk, walking Bridge of Judgment, staff guiding, pearl lighting dark waters, souls following, grey monk robe, red sash, calm expression, male features, underworld river, lotus flowers, mystic, 8k, cinematic, masterpiece",
            
            # ----- 幽冥世界 -----
            "Ksitigarbha Bodhisattva, male bodhisattva, masculine Asian monk, presiding in Underworld court, golden throne, radiant pearl, staff beside, elaborate robes, majestic compassionate, male features, strong masculine face, Wheel of Life behind, souls saved, thangka style, 8k, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, masculine Asian monk, vision at dying bedside, golden light, radiant pearl, staff, flowing white gold robes, serene comforting, male face, gentle features, soul rising peacefully, soft light, emotional, 8k, cinematic, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, masculine Asian monk, descending on golden cloud, heavenly beings, lotus petals, holding staff and pearl, celestial robes, radiant majestic, male features, strong masculine face, heaven scene, divine, 8k, cinematic, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, masculine Asian monk, Hall of Ten Kings, compassionate figure, holding pearl and staff, monastic robes, calm merciful expression, male features, ancient Chinese underworld setting, Buddhist Taoist fusion, 8k, cinematic, masterpiece",
            
            # ----- 法相特写 -----
            "Ksitigarbha Bodhisattva, male bodhisattva, masculine Asian monk, close-up portrait, compassionate wise eyes, gentle smile, male facial features, strong jaw, shaved head, crown, golden jewelry, monastic robe collar, golden halo, sacred expression, 8k, cinematic, photorealistic, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, masculine Asian monk, cintamani jewel close-up, glowing white-gold light, strong graceful hand, radiating rays, monastic robe sleeve, golden trim, dark background, sacred mystical, 8k, cinematic, macro, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, masculine Asian monk, khakkhara staff detail, six rings, golden metalwork, staff striking ground, intricate design, strong hand holding staff, golden bronze colors, sacred object, 8k, cinematic, macro, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, masculine Asian monk, surrounded by guardians, standing center, pearl glowing, staff in hand, Dharma protectors, divine generals, grand celestial assembly, majestic, thangka style, 8k, cinematic, masterpiece",
        ],
        
        # ==================== 风格 (8种 - SDXL 优化) ====================
        "styles": [
            "divine Buddhist art masterpiece, golden and warm lighting, sacred atmosphere, intricate details, volumetric lighting, 8k, cinematic, photorealistic, highly detailed textures, rich gold and red colors, dramatic composition, awe-inspiring, worshipful, majestic, male divine figure",
            "traditional thangka painting style, rich golden and red colors, ornate geometric patterns, traditional Buddhist iconography, divine presence, intricate mandalas, Himalayan art style, sacred geometry, masterpiece, 8k, highly detailed, vibrant colors, spiritual, male bodhisattva",
            "sacred art, ethereal glow, deep shadows and bright highlights, dramatic divine lighting, photorealistic, emotional, masterpiece, 8k, cinematic, dramatic chiaroscuro, warm golden light piercing darkness, hope and mercy, salvation, male savior figure",
            "dark mystical underworld atmosphere, dramatic chiaroscuro, golden divine light piercing the darkness, high contrast, epic composition, masterpiece, 8k, cinematic, emotional, powerful, haunting beauty, light in darkness, sacred, male divine warrior",
            "classical Buddhist iconography, Himalayan and East Asian art style fusion, intricate halos and mandalas, serene and majestic, temple mural aesthetic, ancient sacred art, masterpiece, 8k, detailed, timeless, spiritual, male monastic figure",
            "heavenly vision, warm golden and white light, celestial atmosphere, soft ethereal glow, peaceful and uplifting, masterpiece, 8k, cinematic, beautiful, radiant, divine, sacred, glorious, ethereal beauty, male celestial being",
            "dramatic epic cinematic style, wide-angle composition, divine light rays, golden hour lighting, emotional impact, masterpiece, 8k, cinematic, epic scale, grand, powerful, heroic, compassionate, awe-inspiring, male heroic figure",
            "photorealistic sacred art, ultra detailed textures, luxurious fabrics and gold leaf, divine radiance, masterpiece, 8k, cinematic, photorealistic, stunning, beautiful, intricate, sacred, worshipful, magnificent, male divine presence"
        ],
        
        # ==================== 情绪 (8种) ====================
        "moods": [
            "compassionate and merciful, saving all suffering beings, ultimate kindness, selfless love, fatherly compassion",
            "majestic and divine, king of the underworld, all-powerful, awe-inspiring, regal majesty, masculine divine authority",
            "peaceful and serene, ultimate enlightened being, eternal calm, deep wisdom, inner peace, masculine tranquility",
            "powerful and heroic, destroyer of hell, savior of all, fearless determination, unshakable will, masculine strength",
            "gentle and comforting, relieving all fears, bringing peace, healing presence, loving kindness, fatherly warmth",
            "determined and unwavering, never giving up until all are saved, eternal vow, unbreakable promise, masculine resolve",
            "mysterious and sacred, profound and unfathomable, transcendental beauty, infinite compassion, divine masculine mystery",
            "victorious and triumphant, light over darkness, salvation achieved, ultimate liberation, masculine triumph"
        ],
        
        # ==================== 地藏菩萨大愿 (25条) ====================
        "content_texts": [
            "地狱不空，誓不成佛。众生度尽，方证菩提。",
            "我不入地狱，谁入地狱。",
            "地狱未空，誓不成佛。",
            "众生度尽，方证菩提。",
            "大愿地藏王菩萨，大慈大悲，救苦救难。",
            "地藏菩萨本愿经，孝道度亲，大愿普度众生。",
            "地藏大愿，慈悲无尽，救度一切苦难众生。",
            "安忍不动如大地，静虑深密如秘藏。",
            "一切众生，未解脱者，性识无定，恶习结业，善习结果。",
            "阎浮众生，举止动念，无不是业，无不是罪。",
            "吾观地藏威神力，恒河沙劫说难尽。",
            "见闻瞻礼一念间，利益人天无量事。",
            "地藏菩萨妙难伦，化现金容处处分。",
            "三途六道闻妙法，四生十类蒙慈恩。",
            "明珠照彻天堂路，金锡振开地狱门。",
            "累劫亲姻蒙接引，九莲台畔礼慈尊。",
            "南无大愿地藏王菩萨，大慈大悲，广度众生。",
            "地藏菩萨，誓愿宏深，悲心广大，度尽众生。",
            "一念恭敬，得度生死。",
            "地藏威神，不可思议，十方诸佛，齐声赞叹。",
            "地狱不空誓不成佛，众生度尽方证菩提。",
            "大慈大悲，救苦救难，广度众生。",
            "地藏菩萨，愿力无边，普度一切。",
            "明珠照亮黑暗路，金锡敲开地狱门。",
            "地藏大愿，永恒不灭，普度众生，同归净土。"
        ]
    }
}
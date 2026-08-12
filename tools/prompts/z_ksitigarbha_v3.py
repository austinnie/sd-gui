# tools/prompts/z_ksitigarbha_v3.py
# 地藏王菩萨 - SDXL 增强版提示词库（神圣法相修正版）
# 修正方向：回归传统佛教造像，强调菩萨璎珞、宝冠、天衣、神性，去除写实和尚形象

STYLE = {
    "z_ksitigarbha_v3": {
        "folder": "3_AI画廊_地藏王菩萨_分层",
        "strength": 0.35,
        
        # ==================== 主体 (16种 - 重塑菩萨相) ====================
        "subjects": [
            # 提示词结构调整：顶级重写，去掉僧袍光头，加入宝冠天衣
            "Ksitigarbha Bodhisattva, divine male bodhisattva, Asian divine figure, high golden topknot with jeweled crown, wearing flowing celestial silk robes and ornate golden jewelry, holding golden khakkhara staff, radiant glowing pearl in hand, compassionate and majestic expression, soft masculine features, golden luminous halo, sacred Buddhist thangka, 8k, cinematic, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, sacred Asian deity, elaborate jeweled headdress, translucent silk garments, golden armbands and necklaces, sitting on red lotus throne, holding luminous jewel, golden staff beside, peaceful compassionate gaze, night sky, starlight, divine atmosphere, 8k, cinematic, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, majestic divine king, ornate golden crown, draped in flowing white and gold celestial robes, seated on stone throne, holding glowing pearl and khakkhara, compassionate regal expression, soft masculine face, sacred altar background, thangka style, 8k, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, divine savior, high jeweled topknot, celestial armor-like robes, standing at gates of underworld, golden staff striking ground, pearl held high radiating holy light, piercing darkness, fierce yet compassionate expression, breaking chains, dramatic hellscape, epic, 8k, cinematic, masterpiece",
            
            # ----- 地狱救度 -----
            "Ksitigarbha Bodhisattva, male bodhisattva, divine figure, descending through hell, golden halo piercing darkness, glowing pearl illuminating suffering souls, staff ringing, flowing white and gold silk robes, tears of compassion, reaching to save souls, soft male features, hellish landscape, dramatic, 8k, cinematic, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, divine being, standing in Avici Hell as island of golden light, pearl illuminating faces of the damned, staff planted, ornate jeweled robes and crown, compassionate gaze, soft masculine divine face, dark high contrast, epic religious art, 8k, cinematic, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, divine warrior, breaking chains of hell, golden shockwaves, souls rising, golden jeweled armor robes, fierce compassionate expression, soft male features, golden halo, dark hellscape, epic battle, 8k, cinematic, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, divine guide, walking Bridge of Judgment, staff guiding, pearl lighting dark waters, souls following, flowing white celestial robes, red sash, calm expression, jeweled crown, underworld river, lotus flowers, mystic, 8k, cinematic, masterpiece",
            
            # ----- 幽冥世界 -----
            "Ksitigarbha Bodhisattva, male bodhisattva, divine king, presiding in Underworld court, golden throne, radiant pearl, staff beside, elaborate jeweled robes and crown, majestic compassionate, soft masculine face, Wheel of Life behind, souls saved, thangka style, 8k, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, divine being, vision at dying bedside, golden light, radiant pearl, staff, flowing celestial white gold robes, serene comforting, soft male face, gentle features, soul rising peacefully, soft light, emotional, 8k, cinematic, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, divine celestial being, descending on golden cloud, heavenly beings, lotus petals, holding staff and pearl, jeweled headdress, flowing translucent robes, radiant majestic, soft male features, heaven scene, divine, 8k, cinematic, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, divine figure, Hall of Ten Kings, compassionate figure, holding pearl and staff, jeweled crown and silk robes, calm merciful expression, soft masculine face, ancient Chinese underworld setting, Buddhist Taoist fusion, 8k, cinematic, masterpiece",
            
            # ----- 法相特写 -----
            "Ksitigarbha Bodhisattva, male bodhisattva, divine portrait close-up, compassionate wise eyes, gentle smile, soft male facial features, high topknot with golden crown, ornate jewelry, celestial robe collar, golden halo, sacred expression, 8k, cinematic, photorealistic, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, cintamani jewel close-up, glowing white-gold light, strong graceful hand, radiating rays, celestial robe sleeve, golden trim, jeweled bracelet, dark background, sacred mystical, 8k, cinematic, macro, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, khakkhara staff detail, six rings, golden metalwork, staff striking ground, intricate design, strong hand holding staff, golden bronze colors, sacred object, 8k, cinematic, macro, masterpiece",
            
            "Ksitigarbha Bodhisattva, male bodhisattva, divine figure, surrounded by guardians, standing center, pearl glowing, staff in hand, jeweled crown and celestial robes, Dharma protectors, divine generals, grand celestial assembly, majestic, thangka style, 8k, cinematic, masterpiece",
        ],
        
        # ==================== 风格 (8种 - 强化神性与慈悲) ====================
        "styles": [
            "divine Buddhist art masterpiece, golden and warm lighting, sacred atmosphere, intricate jewelry details, volumetric lighting, 8k, cinematic, photorealistic, highly detailed silk textures, rich gold and red colors, dramatic composition, awe-inspiring, worshipful, majestic, divine male figure",
            "traditional thangka painting style, rich golden and red colors, ornate geometric patterns, traditional Buddhist iconography, divine presence, intricate mandalas, Himalayan and East Asian art style fusion, sacred geometry, masterpiece, 8k, highly detailed, vibrant colors, spiritual, male bodhisattva",
            "sacred art, ethereal glow, deep shadows and bright highlights, dramatic divine lighting, photorealistic, emotional, masterpiece, 8k, cinematic, dramatic chiaroscuro, warm golden light piercing darkness, hope and mercy, salvation, divine savior figure",
            "dark mystical underworld atmosphere, dramatic chiaroscuro, golden divine light piercing the darkness, high contrast, epic composition, masterpiece, 8k, cinematic, emotional, powerful, haunting beauty, light in darkness, sacred, male divine warrior",
            "classical Buddhist iconography, temple mural aesthetic, ancient sacred art, intricate halos and mandalas, serene and majestic, masterpiece, 8k, detailed, timeless, spiritual, male divine figure, flowing robes and jewels",
            "heavenly vision, warm golden and white light, celestial atmosphere, soft ethereal glow, peaceful and uplifting, masterpiece, 8k, cinematic, beautiful, radiant, divine, sacred, glorious, ethereal beauty, male celestial being",
            "dramatic epic cinematic style, wide-angle composition, divine light rays, golden hour lighting, emotional impact, masterpiece, 8k, cinematic, epic scale, grand, powerful, heroic, compassionate, awe-inspiring, divine heroic figure",
            "photorealistic sacred art, ultra detailed textures, luxurious silk and gold leaf, divine radiance, masterpiece, 8k, cinematic, photorealistic, stunning, beautiful, intricate, sacred, worshipful, magnificent, male divine presence"
        ],
        
        # ==================== 情绪 (8种 - 调整偏向慈悲庄严) ====================
        "moods": [
            "compassionate and merciful, saving all suffering beings, ultimate kindness, selfless love, divine compassion",
            "majestic and divine, king of the underworld, all-powerful, awe-inspiring, regal majesty, divine authority",
            "peaceful and serene, ultimate enlightened being, eternal calm, deep wisdom, inner peace, divine tranquility",
            "powerful and heroic, destroyer of hell, savior of all, fearless determination, unshakable will, divine strength",
            "gentle and comforting, relieving all fears, bringing peace, healing presence, loving kindness, divine warmth",
            "determined and unwavering, never giving up until all are saved, eternal vow, unbreakable promise, divine resolve",
            "mysterious and sacred, profound and unfathomable, transcendental beauty, infinite compassion, divine mystery",
            "victorious and triumphant, light over darkness, salvation achieved, ultimate liberation, divine triumph"
        ],
        
        # ==================== 地藏菩萨大愿 (25条 - 保持不变) ====================
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
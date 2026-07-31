# prompts/tangbohu_masterpieces.py
# 唐伯虎 经典名画高清还原
# 包含：山水、仕女、折枝花卉

STYLE = {
    "tangbohu_masterpieces": {
        "folder": "唐伯虎名画集",
        "strength": 0.35,
        "subjects": [
            # --- 山水画 (《落霞孤鹜图》等风格) ---
            "Tang Yin style Chinese landscape painting, misty mountains, serene river, ancient pavilion on a cliff, willows and pines, fine brushwork, muted elegant ink and light green wash, Ming dynasty literati painting, aged silk texture, masterpiece art, 8k",
            "Tang Bohu's classic mountain and water painting, delicate brushstrokes, soft ink tones, distant peaks, a lonely boat with a fisherman, poetic composition, traditional Chinese ink and color, red seals and calligraphy, museum quality reproduction",
            "Tang Yin style freehand landscape, using hemp-fiber brushwork, dramatic mountain ridges, misty atmosphere, subtle color washes, authentic old paper texture, masterpiece cultural relic, macro photography",
            
            # --- 仕女图 (工笔与写意结合) ---
            "Tang Bohu style painting of a beautiful woman, elegant figure, flowing silk robes, delicate features, holding a folding fan, subtle mineral colors, detailed linework (baimiao), ancient aesthetic, red seals, masterpiece Chinese art",
            "Ming dynasty style lady painting by Tang Yin, graceful pose, soft colors and fine brushwork, expression of gentle melancholy, traditional historical artwork, aged paper, original seal stamps, museum photograph",
            "Tang Bohu's elegant court lady, wearing magnificent traditional attire, intricate hair ornaments and jewelry, graceful hand gestures, silk tapestry texture, masterpiece ancient Chinese painting, intricate details",
            
            # --- 花鸟/梅竹 ---
            "Tang Yin style plum blossom painting, elegant branches, delicate pale pink flowers, fine calligraphic brushwork, subtle ink washes, ancient scroll aesthetic, red seals, Chinese cultural heritage art",
            "Bamboo and rocks painting by Tang Bohu, precise leaf strokes, elegant composition, traditional literati art style, ink on paper, great contrast of dark and light shades, masterwork"
        ],
        "styles": [
            "Tang Yin Ming dynasty literati painting style, delicate brushwork, muted colors, aged paper and silk texture",
            "classic traditional Chinese ink painting, fine lines, subtle wash effects, red signature seals, ancient artwork",
            "ultra-realistic masterpiece art reproduction, traditional calligraphy and painting integration, museum archival quality"
        ],
        "moods": [
            "elegant, delicate, poetic, serene",
            "classic, refined, historical, cultured",
            "majestic, gentle, scholarly, timeless"
        ],
        "content_texts": [] 
    }
}
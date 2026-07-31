# prompts/western_art_sketch.py
# 西方珍贵艺术品 手稿/素描/油画
# 包含：达芬奇手稿、古典素描、油画、水彩

STYLE = {
    "western_art_sketch": {
        "folder": "珍贵字画_西方",
        "strength": 0.35,
        "subjects": [
            # --- 达芬奇手稿 ---
            "Leonardo da Vinci's anatomical sketch, intricate sepia ink on aged parchment paper, detailed study of human anatomy, handwritten notes, faded historical document, museum preservation photography, pure white background, masterpiece art",
            "Leonardo da Vinci's flying machine sketch, vintage engineering blueprint, brown ink on yellowed paper, archaic Italian notes, historical invention draft, antique manuscript photo, 8k",
            
            # --- 古典素描 ---
            "Renaissance era silverpoint sketch, fine delicate lines, portrait study of a woman, aged paper texture, subtle shading, historical art preservation, pure white background, museum quality recording",
            "Michelangelo's preliminary sketch of a muscular figure, red chalk on aged paper, incredible anatomical detail, faded pigment, iconic Italian Renaissance art, archival scan",
            
            # --- 古典油画/水彩 ---
            "classic oil painting fragment, rich impasto brushwork, deep Renaissance colors, cracked varnish texture, aged canvas, intricate lighting, masterpiece museum art, high-resolution photography",
            "historical botanical watercolor painting, delicate floral illustration, faded vibrant colors, old watercolor paper, scientific plant study, vintage art documentation, pure white background",
            
            # --- 羊皮纸古籍 ---
            "illuminated medieval manuscript, ornate gold leaf initial letter, Latin script, thick aged parchment, historic religious book, macro photograph, extreme detail, museum quality heritage art"
        ],
        "styles": [
            "ultra-realistic macro archival photography, aged parchment and paper texture, historical document aesthetic",
            "Renaissance art preservation, sepia ink, faded chalk, antique materials, museum exhibition lighting",
            "high-fidelity historical artwork photograph, 8k, intricate sketch lines, authentic vintage details"
        ],
        "moods": [
            "historical, intellectual, sketchy, scientific",
            "elegant, antique, Renaissance, classical",
            "detailed, timeless, traditional, scholarly"
        ],
        "content_texts": [] 
    }
}
"""
Modelo 1 — carrossel no estilo de post do X (MENTE DE INVESTIDOR)
Uso: python scripts/modelo1_x.py slides.json
slides.json: {"theme": "claro" | "escuro", "out": "pasta/de/saida", "slides": [
   {"text": ["parágrafo com **negrito**", "", "outro parágrafo"], "size": 54, "arrow": true}, ...]}
Texto "" = espaço entre parágrafos. Saída: slide1.png ... (1080x1350).
"""
import json, os, re, sys
from PIL import Image, ImageDraw, ImageFont, ImageChops
import math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 2
_FONTS = {
    "segoeui.ttf": ["C:/Windows/Fonts/segoeui.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"],
    "segoeuib.ttf": ["C:/Windows/Fonts/segoeuib.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                     "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                     "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"],
}
W, H, M = 1080, 1350, 100
BLUE = (29, 155, 240)
THEMES = {
    "claro": dict(bg=(255, 255, 255), fg=(15, 20, 25), grey=(83, 100, 113), ring=None),
    "escuro": dict(bg=(0, 0, 0), fg=(231, 233, 234), grey=(113, 118, 123), ring=(60, 64, 68)),
}
NAME, HANDLE = "Mente de Investidor", "@mentedeinvestidor.br"
AV = 190  # diâmetro da foto de perfil

def f(n, s):
    for path in _FONTS[n]:
        if os.path.exists(path): return ImageFont.truetype(path, s * S)
    return ImageFont.load_default(s * S)  # último recurso

def make_avatar():
    logo = Image.open(os.path.join(ROOT, "assets", "logo-mdi-fundo-preto.png")).convert("RGB")
    bbox = logo.convert("L").point(lambda v: 255 if v > 25 else 0).getbbox()
    logo = logo.crop(bbox)
    D = AV * S
    av = Image.new("RGBA", (D, D), (0, 0, 0, 255))
    tw = int(D * 0.86); th = int(logo.height * tw / logo.width)
    av.paste(logo.resize((tw, th), Image.LANCZOS), ((D - tw) // 2, (D - th) // 2))
    mask = Image.new("L", (D, D), 0); ImageDraw.Draw(mask).ellipse([0, 0, D - 1, D - 1], fill=255)
    av.putalpha(mask)
    return av

def badge(im, cx, cy, r):
    d = ImageDraw.Draw(im)
    for k in range(8):
        a = k * math.pi / 4
        x = cx + math.cos(a) * r * 0.62; y = cy + math.sin(a) * r * 0.62
        d.ellipse([x - r * .42, y - r * .42, x + r * .42, y + r * .42], fill=BLUE)
    d.ellipse([cx - r * .8, cy - r * .8, cx + r * .8, cy + r * .8], fill=BLUE)
    d.line([(cx - r * .42, cy + r * .02), (cx - r * .1, cy + r * .34), (cx + r * .45, cy - r * .32)],
           fill="white", width=int(r * .2), joint="curve")

def words_of(text, size):
    """Palavras = listas de (trecho, fonte): pontuação colada ao negrito não ganha espaço."""
    reg, bold = f("segoeui.ttf", size), f("segoeuib.ttf", size)
    words, cur, is_b = [], [], False
    for i, part in enumerate(text.split("**")):
        fn = bold if i % 2 else reg
        for j, tok in enumerate(re.split(r"(\s+)", part)):
            if tok == "": continue
            if tok.isspace():
                if cur: words.append(cur); cur = []
            else:
                cur.append((tok, fn))
    if cur: words.append(cur)
    return words

def wlen(d, word): return sum(d.textlength(t, font=fn) for t, fn in word)

def wrap(d, words, maxw):
    lines, cur, w = [], [], 0
    for word in words:
        if cur and w + wlen(d, word) > maxw: lines.append(cur); cur = []; w = 0
        cur.append(word); w += wlen(d, word) + d.textlength(" ", font=word[0][1])
    if cur: lines.append(cur)
    return lines

def render(av, spec, path, theme):
    BLACK, GREY = theme["fg"], theme["grey"]
    size = spec.get("size", 54)
    im = Image.new("RGB", (W * S, H * S), theme["bg"]); d = ImageDraw.Draw(im)
    top = 80
    im.paste(av, (M * S, top * S), av)
    if theme["ring"]:
        d.ellipse([M * S, top * S, (M + AV) * S - 1, (top + AV) * S - 1], outline=theme["ring"], width=3 * S)
    nx = (M + AV + 30) * S; ny = top + AV // 2
    d.text((nx, (ny - 52) * S), NAME, font=f("segoeuib.ttf", 46), fill=BLACK)
    nw = d.textlength(NAME, font=f("segoeuib.ttf", 46))
    badge(im, int(nx + nw + 32 * S), int((ny - 26) * S), 24 * S)
    d.text((nx, (ny + 6) * S), HANDLE, font=f("segoeui.ttf", 36), fill=GREY)
    y = (top + AV + 80) * S; lh = int(size * 1.28 * S)
    for para in spec["text"]:
        if para == "": y += int(lh * .6); continue
        for line in wrap(d, words_of(para, size), (W - 2 * M) * S):
            x = M * S
            for word in line:
                for t, fn in word:
                    d.text((x, y), t, font=fn, fill=BLACK); x += d.textlength(t, font=fn)
                x += d.textlength(" ", font=word[-1][1])
            y += lh
    if spec.get("arrow"):
        d.text(((W - M) * S, (H - 150) * S), "→", font=f("segoeui.ttf", 84), fill=BLACK, anchor="ra")
    im.resize((W, H), Image.LANCZOS).save(path)

if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    out = os.path.normpath(os.path.join(ROOT, cfg["out"])); os.makedirs(out, exist_ok=True)
    av = make_avatar(); theme = THEMES[cfg.get("theme", "claro")]
    for i, s in enumerate(cfg["slides"], 1):
        if s.get("final"):
            from cta_final import make_cta
            make_cta(s["final"]).save(os.path.join(out, f"slide{i}.png"))
        else:
            render(av, s, os.path.join(out, f"slide{i}.png"), theme)
    print("ok", out)

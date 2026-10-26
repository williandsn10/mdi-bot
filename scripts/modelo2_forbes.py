"""
Modelo 2 - carrossel editorial estilo revista (fundo em tela cheia + titulo branco na base).
Uso: python scripts/modelo2_forbes.py slides.json
slides.json: {"out": "pasta", "tag": "Mercado", "fonte": "Fonte: CNN Brasil, 19/10/2026",
  "slides": [{"text": "Titulo **com destaque**", "size": 66, "image": "caminho/foto.jpg", "tone": 0},
             ..., {"cta": true, "text": ["linha 1", "linha 2"]}]}
Sem "image", gera um fundo abstrato escuro com brilho dourado (sem fotos de terceiros).
Com "image" (foto sua ou licenciada), ela vira o fundo em tela cheia com degrade escuro na base.
Saida: slide1.png ... (1080x1350).
"""
import json, os, re, sys, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, M = 1080, 1350, 64
GOLD = (201, 162, 75)
_FONTS = {
    "b": ["C:/Windows/Fonts/segoeuib.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
          "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"],
    "r": ["C:/Windows/Fonts/segoeui.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
          "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"],
}


def font(k, s):
    for p in _FONTS[k]:
        if os.path.exists(p):
            return ImageFont.truetype(p, s)
    return ImageFont.load_default(s)


# (topo, base): azul petroleo, grafite, marinho, verde-musgo, bronze escuro, azul aco
TONES = [((38, 52, 78), (10, 14, 22)), ((52, 56, 64), (12, 12, 14)), ((24, 40, 74), (6, 10, 20)),
         ((30, 58, 52), (8, 16, 14)), ((78, 58, 34), (18, 12, 8)), ((44, 70, 98), (8, 14, 22))]


def abstract_bg(tone, seed):
    rnd = random.Random(seed)
    top, bot = TONES[tone % len(TONES)]
    col = Image.new("RGB", (1, H))
    for y in range(H):
        t = y / H
        col.putpixel((0, y), tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3)))
    im = col.resize((W, H))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    g = ImageDraw.Draw(glow)
    for _ in range(2):  # brilhos suaves dourados
        cx, cy, r = rnd.randint(150, 930), rnd.randint(120, 620), rnd.randint(260, 460)
        g.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(70, 52, 20))
    im = ImageChops.add(im, glow.filter(ImageFilter.GaussianBlur(160)))
    d = ImageDraw.Draw(im, "RGBA")
    for _ in range(5):  # faixas diagonais discretas
        x0 = rnd.randint(-200, W)
        w = rnd.randint(40, 160)
        d.polygon([(x0, 0), (x0 + w, 0), (x0 + w - 520, 900), (x0 - 520, 900)], fill=(255, 255, 255, 7))
    noise = Image.effect_noise((W, H), 10).convert("RGB")
    return ImageChops.blend(im, ImageChops.add(im, noise, scale=3, offset=-40), 0.30)


def photo_bg(path):
    im = Image.open(path).convert("RGB")
    s = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    left, top = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((left, top, left + W, top + H))


def gradient_overlay(im, start):
    col = Image.new("L", (1, H))
    for y in range(H):
        t = max(0.0, (y / H - start) / (1 - start))
        col.putpixel((0, y), int(235 * min(1.0, t ** 0.7)))
    alpha = col.resize((W, H))
    black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    black.putalpha(alpha)
    return Image.alpha_composite(im.convert("RGBA"), black).convert("RGB")


def words(text, size):
    """Palavras = listas de (trecho, fonte, cor); pontuacao colada ao destaque nao ganha espaco."""
    fn = font("b", size)
    out, cur = [], []
    for i, part in enumerate(text.split("**")):
        col = GOLD if i % 2 else (255, 255, 255)
        for tok in re.split(r"(\s+)", part):
            if tok == "":
                continue
            if tok.isspace():
                if cur:
                    out.append(cur); cur = []
            else:
                cur.append((tok, fn, col))
    if cur:
        out.append(cur)
    return out


def wlen(d, word):
    return sum(d.textlength(t, font=fn) for t, fn, c in word)


def draw_headline(d, text, size, bottom):
    lines, cur, w = [], [], 0
    for word in words(text, size):
        if cur and w + wlen(d, word) > W - 2 * M:
            lines.append(cur); cur = []; w = 0
        cur.append(word); w += wlen(d, word) + d.textlength(" ", font=word[0][1])
    if cur:
        lines.append(cur)
    lh = int(size * 1.2)
    y = bottom - lh * len(lines)
    for ln in lines:
        x = M
        for word in ln:
            for t, fn, c in word:
                d.text((x, y), t, font=fn, fill=c)
                x += d.textlength(t, font=fn)
            x += d.textlength(" ", font=word[0][1])
        y += lh


def draw_sub(d, text, bottom, size=30):
    """Texto de apoio (opcional) abaixo do titulo; retorna a altura ocupada."""
    fn = font("r", size)
    lines, cur = [], ""
    for tok in text.split():
        t = (cur + " " + tok).strip()
        if d.textlength(t, font=fn) > W - 2 * M and cur:
            lines.append(cur); cur = tok
        else:
            cur = t
    if cur:
        lines.append(cur)
    lh = int(size * 1.35)
    y = bottom - lh * len(lines)
    for ln in lines:
        d.text((M, y), ln, font=fn, fill=(205, 205, 205))
        y += lh
    return lh * len(lines) + 26


def logo(width=170):
    lg = Image.open(os.path.join(ROOT, "assets", "logo-mdi-fundo-preto.png")).convert("RGB")
    lg = lg.crop(lg.convert("L").point(lambda v: 255 if v > 25 else 0).getbbox())
    lg = lg.resize((width, int(lg.height * width / lg.width)), Image.LANCZOS)
    out = lg.convert("RGBA")
    out.putalpha(lg.convert("L").point(lambda v: min(255, int(v * 2.6))))  # preto vira transparente
    return out


def footer(im, tag, fonte, lg):
    d = ImageDraw.Draw(im)
    d.rectangle([M, H - 105, M + 3, H - 70], fill=GOLD)
    d.text((M + 16, H - 108), tag.upper(), font=font("r", 28), fill=(235, 235, 235))
    if fonte:
        d.text((M, H - 150), fonte, font=font("r", 22), fill=(170, 170, 170))
    im.paste(lg, (W - M - lg.width, H - 62 - lg.height), lg)


def cta_slide(lines, lg, handle="@mentedeinvestidor.br"):
    im = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 470
    for ln in lines:
        d.text((W // 2, y), ln, font=font("b", 50), fill=(255, 255, 255), anchor="mm")
        y += 72
    d.line([W // 2 - 18, y + 18, W // 2 + 18, y + 18], fill=GOLD, width=3)
    bw = d.textlength(handle, font=font("r", 34)) + 56
    d.rectangle([W // 2 - bw // 2, y + 70, W // 2 + bw // 2, y + 140], outline=(210, 210, 210), width=2)
    d.text((W // 2, y + 105), handle, font=font("r", 34), fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, y + 190), "www.mentedeinvestidor.com.br", font=font("r", 32), fill=GOLD, anchor="mm")
    im.paste(lg, ((W - lg.width) // 2, y + 250), lg)
    return im


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    out = os.path.normpath(os.path.join(ROOT, cfg["out"]))
    os.makedirs(out, exist_ok=True)
    lg = logo()
    tag, fonte = cfg.get("tag", "Mercado"), cfg.get("fonte", "")
    for i, s in enumerate(cfg["slides"], 1):
        if s.get("final"):
            from cta_final import make_cta
            im = make_cta(s["final"])
        elif s.get("cta"):
            im = cta_slide(s["text"], lg)
        else:
            has_img = bool(s.get("image"))
            bg = photo_bg(os.path.join(ROOT, s["image"])) if has_img else abstract_bg(s.get("tone", i), 100 + i)
            im = gradient_overlay(bg, 0.30 if has_img else 0.30)
            d = ImageDraw.Draw(im)
            used = draw_sub(d, s["sub"], H - 175) if s.get("sub") else 0
            draw_headline(d, s["text"], s.get("size", 64), H - 195 - used)
            footer(im, tag, fonte, lg)
        im.save(os.path.join(out, f"slide{i}.png"))
    print("ok", out)

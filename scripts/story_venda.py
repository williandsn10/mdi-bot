"""
Stories de venda (Modelo 3) 1080x1920: titulo, capa do produto, preco de/por, beneficio, selo, botao CTA.
Uso: /tmp/v/bin/python scripts/story_venda.py  -> saida/stories-venda/*.png
Beneficios: apenas as descricoes oficiais dos produtos. Sem promessa de retorno.
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
from cta_final import _font, _logo, _wrap, GOLD

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1080, 1920
GOLD_L = (232, 200, 120)
WHITE = (245, 245, 242)
GREY = (150, 150, 150)

PRODUTOS = [
    dict(id="mdi-select", foto="chart.jpg", titulo=["Acompanhe a carteira", "**MDI SELECT**"], tag="ASSINATURA", capa=["CARTEIRA", "MDI SELECT"],
         de="De R$ 49,90/mês", por="R$ 29,90", sufixo="/mês",
         beneficio="Acompanhe a carteira e entenda o contexto por trás de cada decisão.",
         link="https://pay.hub.la/Mu9W039KCOgYORN61aVk"),
    dict(id="mdi-select-anual", foto="g9eo.jpg", titulo=["Plano anual", "**MDI SELECT**"], tag="PLANO ANUAL", capa=["CARTEIRA", "MDI SELECT"],
         de="De R$ 598,80/ano", por="R$ 299,00", sufixo="/ano", destaque="Economize R$ 299,80",
         beneficio="Acompanhe a carteira e entenda o contexto por trás de cada decisão.",
         link="https://pay.hub.la/Mu9W039KCOgYORN61aVk",
         obs="Confirme o plano anual na página de compra."),
    dict(id="indicadores-timing-sentimento", foto="candle.jpg", titulo=["Aprenda a ler os", "**INDICADORES**"], tag="INDICADORES", capa=["INDICADORES MDI", "Timing &", "Sentimento"],
         de="De R$ 79,90", por="R$ 39,90", sufixo="",
         beneficio="Aprenda a interpretar indicadores antes de escolher onde investir.",
         link="https://pay.hub.la/ZSjrKfNe7mDNNMzXiRVy"),
    dict(id="do-zero-ao-patrimonio", foto="calc.jpg", escuro=0.45, titulo=["Comece pelo que", "**IMPORTA**"], tag="EBOOK", capa=["Do Zero", "ao Patrimônio"],
         de="De R$ 59,90", por="R$ 29,90", sufixo="",
         beneficio="Um ebook para entender seu dinheiro e começar pelo que importa.",
         link="https://pay.hub.la/ZjFtKzXBRYl6kWYzCrLD"),
    dict(id="combo-do-zero-a-analise", foto="laptop.jpg", titulo=["Combo MDI", "**DO ZERO À ANÁLISE**"], tag="COMBO", capa=None,
         de="De R$ 139,80", por="R$ 49,90", sufixo="",
         beneficio="Entenda seu dinheiro e aprenda a interpretar indicadores.",
         link="https://pay.hub.la/vtUh3OyPNQvMCL8WsxS6"),
]


def background(foto, escuro=0.2):
    """Foto em tela cheia (como o Modelo 2) com degrade escuro para legibilidade."""
    ph = Image.open(os.path.join(ROOT, "assets", "fotos-stories", foto)).convert("RGB")
    k = max(W / ph.width, H / ph.height)
    ph = ph.resize((int(ph.width * k), int(ph.height * k)), Image.LANCZOS)
    l, t = (ph.width - W) // 2, 0
    im = ph.crop((l, t, l + W, t + H)).filter(ImageFilter.GaussianBlur(1))
    im = Image.blend(im, Image.new("RGB", (W, H), (0, 0, 0)), escuro)
    col = Image.new("L", (1, H))
    for y in range(H):
        u = y / H
        a = 0.35 * (1 - u / 0.2) if u < 0.2 else 0
        a = max(a, min(0.92, max(0.0, (u - 0.5) / 0.3) ** 0.8 * 0.92))
        a = max(a, 0.55 * max(0.0, 1 - abs(u - 0.19) / 0.12))
        col.putpixel((0, y), int(255 * a))
    black = Image.new("RGB", (W, H), (0, 0, 0))
    im = Image.composite(black, im, col.resize((W, H)))
    gold = Image.new("RGB", (W, H), (0, 0, 0))
    ImageDraw.Draw(gold).ellipse([200, 600, 880, 1150], fill=(60, 46, 18))
    im = ImageChops.add(im, gold.filter(ImageFilter.GaussianBlur(150)))
    ImageDraw.Draw(im).rectangle([36, 36, W - 37, H - 37], outline=(120, 98, 46), width=2)
    return im


def rich(d, cx, y, parts, size, fill, boldfill):
    """Linha centralizada com **negrito** em dourado."""
    segs, bold = [], False
    for p in parts.split("**"):
        if p:
            segs.append((p, bold))
        bold = not bold
    fb, fr = _font("b", size), _font("r", size)
    tw = sum(d.textlength(t, font=fb if b else fr) for t, b in segs)
    x = cx - tw / 2
    for t, b in segs:
        f = fb if b else fr
        d.text((x, y), t, font=f, fill=boldfill if b else fill, anchor="lm")
        x += d.textlength(t, font=f)


def cover(w, h, tag, lines):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 22, fill=(12, 12, 13), outline=GOLD, width=4)
    d.rounded_rectangle([16, 16, w - 17, h - 17], 14, outline=(110, 90, 42), width=1)
    lg = _logo(int(w * 0.34))
    c.paste(lg, ((w - lg.width) // 2, int(h * 0.10)), lg)
    d.text((w // 2, int(h * 0.36)), tag, font=_font("r", int(w * 0.055)), fill=GOLD, anchor="mm")
    d.line([w // 2 - 30, int(h * 0.41), w // 2 + 30, int(h * 0.41)], fill=GOLD, width=3)
    y = int(h * 0.52)
    for i, ln in enumerate(lines):
        fs = int(w * (0.115 if i else 0.085)) if len(lines) > 1 else int(w * 0.11)
        fnt = _font("b", fs)
        while d.textlength(ln, font=fnt) > w - 50 and fs > 14:
            fs -= 2
            fnt = _font("b", fs)
        d.text((w // 2, y), ln, font=fnt, fill=WHITE, anchor="mm")
        y += int(fs * 1.25)
    d.text((w // 2, h - int(h * 0.07)), "@MENTEDEINVESTIDOR.BR", font=_font("r", int(w * 0.045)), fill=(150, 125, 60), anchor="mm")
    return c


def paste_shadow(im, c, x, y, rot=0):
    if rot:
        c = c.rotate(rot, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", (c.width + 160, c.height + 160), (0, 0, 0, 0))
    sh.paste((0, 0, 0, 200), (80, 100, 80 + c.width, 100 + c.height), c.split()[3])
    sh = sh.filter(ImageFilter.GaussianBlur(28))
    im.paste(sh, (x - 80, y - 80), sh)
    im.paste(c, (x, y), c)


def seal(im, cx, cy):
    d = ImageDraw.Draw(im)
    f = _font("b", 30)
    t = "OFERTA ESPECIAL"
    tw = d.textlength(t, font=f)
    d.rounded_rectangle([cx - tw / 2 - 34, cy - 36, cx + tw / 2 + 34, cy + 36], 36, fill=GOLD)
    d.text((cx, cy), t, font=f, fill=(10, 10, 10), anchor="mm")


def make(p):
    im = background(p["foto"], p.get("escuro", 0.2)).convert("RGBA")
    d = ImageDraw.Draw(im)
    ann = bool(p.get("destaque"))
    dy = 0 if ann else 25
    y = 305 + dy
    for i, ln in enumerate(p["titulo"]):
        rich(d, W // 2, y, ln, 62 if i == 0 else 74, WHITE, GOLD_L)
        if i == 1 and d.textlength(ln.replace("**", ""), font=_font("b", 74)) > 940:
            pass
        y += 92
    top = 500 + dy
    if p["capa"]:
        cv = cover(370, 500, p["tag"], p["capa"])
        paste_shadow(im, cv, (W - 370) // 2, top)
        sy = top + 500
    else:
        a = cover(320, 432, "EBOOK", ["Do Zero", "ao Patrimônio"])
        b = cover(320, 432, "INDICADORES", ["INDICADORES MDI", "Timing &", "Sentimento"])
        paste_shadow(im, a, 215, top + 30, rot=6)
        paste_shadow(im, b, 545, top + 10, rot=-6)
        sy = top + 520
    seal(im, W // 2, sy + 50)
    d = ImageDraw.Draw(im)
    y = sy + 122
    f = _font("r", 38)
    tw = d.textlength(p["de"], font=f)
    d.text((W // 2, y), p["de"], font=f, fill=GREY, anchor="mm")
    d.line([W // 2 - tw / 2 - 6, y + 2, W // 2 + tw / 2 + 6, y + 2], fill=(200, 70, 70), width=4)
    y += 105
    fp, fs = _font("b", 124), _font("b", 46)
    pw, sw = d.textlength(p["por"], font=fp), d.textlength(p["sufixo"], font=fs)
    x = W // 2 - (pw + sw) / 2
    d.text((x, y), p["por"], font=fp, fill=GOLD_L, anchor="lm")
    d.text((x + pw + 6, y + 22), p["sufixo"], font=fs, fill=GOLD_L, anchor="lm")
    y += 108
    if ann:
        t = p["destaque"]
        ft = _font("b", 34)
        tw = d.textlength(t, font=ft)
        d.rounded_rectangle([W // 2 - tw / 2 - 28, y - 28, W // 2 + tw / 2 + 28, y + 28], 28, outline=GOLD, width=3)
        d.text((W // 2, y), t, font=ft, fill=GOLD_L, anchor="mm")
        y += 70
    fb = _font("r", 34)
    for ln in _wrap(d, p["beneficio"], fb, 820):
        d.text((W // 2, y), ln, font=fb, fill=WHITE, anchor="mm")
        y += 46
    bt = y + 4
    d.rounded_rectangle([170, bt, W - 170, bt + 100], 50, fill=GOLD)
    d.text((W // 2, bt + 50), "Comprar agora", font=_font("b", 48), fill=(10, 10, 10), anchor="mm")
    d.text((W // 2, bt + 138), "Clique no link e acesse agora", font=_font("r", 30), fill=GOLD_L, anchor="mm")
    d.text((W // 2, bt + 182), "Conteúdo educativo. Sem promessa de retorno.", font=_font("r", 20), fill=(110, 110, 110), anchor="mm")
    return im.convert("RGB"), bt + 138


if __name__ == "__main__":
    out = os.path.join(ROOT, "saida", "stories-venda")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "LINKS.txt"), "w") as fl:
        for p in PRODUTOS:
            im, ybot = make(p)
            im.save(os.path.join(out, f"story-{p['id']}.png"))
            fl.write(f"story-{p['id']}.png -> {p['link']}\n")
            print(p["id"], "texto termina em y=", ybot)

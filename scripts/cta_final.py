"""
Slide final padrao do MDI (fundo preto): oferta do produto do tema + seguir o perfil + site.
Uso nos geradores: {"final": "carteira" | "guia" | "ebook" | "none"} como ultimo slide.
Textos dos produtos: apenas as descricoes oficiais fornecidas pelo dono (nao inventar nada alem disso).
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1080, 1350
GOLD = (201, 162, 75)
SITE = "WWW.MENTEDEINVESTIDOR.COM.BR"
HANDLE = "@MENTEDEINVESTIDOR.BR"

PRODUTOS = {
    "carteira": ("CARTEIRA MDI SELECT",
                 "ACOMPANHE A CARTEIRA E ENTENDA O CONTEXTO POR TRÁS DE CADA DECISÃO"),
    "guia": ("GUIA DE INDICADORES",
             "APRENDA A INTERPRETAR INDICADORES ANTES DE ESCOLHER ONDE INVESTIR"),
    "ebook": ("EDUCAÇÃO FINANCEIRA SIMPLES",
              "UM EBOOK PARA ENTENDER SEU DINHEIRO E COMEÇAR PELO QUE IMPORTA"),
    "none": (None, "SIGA O MENTE DE INVESTIDOR PARA ACOMPANHAR O MERCADO SEM RUÍDO"),
}

_FONTS = {
    "b": ["C:/Windows/Fonts/segoeuib.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
          "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"],
    "r": ["C:/Windows/Fonts/segoeui.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
          "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"],
}


def _font(k, s):
    for p in _FONTS[k]:
        if os.path.exists(p):
            return ImageFont.truetype(p, s)
    return ImageFont.load_default(s)


def _logo(width=190):
    lg = Image.open(os.path.join(ROOT, "assets", "logo-mdi-fundo-preto.png")).convert("RGB")
    lg = lg.crop(lg.convert("L").point(lambda v: 255 if v > 25 else 0).getbbox())
    lg = lg.resize((width, int(lg.height * width / lg.width)), Image.LANCZOS)
    out = lg.convert("RGBA")
    out.putalpha(lg.convert("L").point(lambda v: min(255, int(v * 2.6))))
    return out


def _wrap(d, text, fn, maxw):
    lines, cur = [], ""
    for tok in text.split():
        t = (cur + " " + tok).strip()
        if d.textlength(t, font=fn) > maxw and cur:
            lines.append(cur)
            cur = tok
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def make_cta(produto="none"):
    label, texto = PRODUTOS.get(produto, PRODUTOS["none"])
    im = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    fn = _font("b", 46)
    lines = _wrap(d, texto, fn, W - 180)
    lh = 66
    block = (60 if label else 0) + lh * len(lines)
    y = 380 - block // 2 + 60
    if label:
        d.text((W // 2, y), label, font=_font("b", 34), fill=GOLD, anchor="mm")
        y += 78
    for ln in lines:
        d.text((W // 2, y), ln, font=fn, fill=(255, 255, 255), anchor="mm")
        y += lh
    y += 10
    d.line([W // 2 - 20, y + 20, W // 2 + 20, y + 20], fill=GOLD, width=3)
    # caixa do site (como no modelo de revista)
    sf = _font("r", 34)
    bw = d.textlength(SITE, font=sf) + 64
    y += 70
    d.rectangle([W // 2 - bw // 2, y, W // 2 + bw // 2, y + 74], outline=(210, 210, 210), width=2)
    d.text((W // 2, y + 37), SITE, font=sf, fill=(255, 255, 255), anchor="mm")
    y += 120
    d.text((W // 2, y), "SIGA " + HANDLE + " NO INSTAGRAM", font=_font("r", 30), fill=GOLD, anchor="mm")
    lg = _logo()
    im.paste(lg, ((W - lg.width) // 2, y + 70), lg)
    return im


if __name__ == "__main__":
    import sys
    make_cta(sys.argv[1] if len(sys.argv) > 1 else "none").save(sys.argv[2] if len(sys.argv) > 2 else "cta_teste.png")

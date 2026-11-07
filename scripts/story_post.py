"""
Story automatico (Modelo 4 - "teaser do post") 1080x1920 a partir do slide 1 de um post.
Uso: python scripts/story_post.py saida/AAAA-MM-DD-tema [ROTULO]
Gera saida/AAAA-MM-DD-tema/story.jpg: fundo preto, slide 1 centralizado (area segura),
rotulo dourado "NOVO NO FEED" e chamada para abrir o post. Nao adiciona nenhum texto novo sobre o fato.
"""
import os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cta_final import _font, GOLD

W, H = 1080, 1920
OFF = (231, 233, 234)
GREY = (113, 118, 123)


def centered(d, y, text, font, fill):
    w = d.textlength(text, font=font)
    d.text(((W - w) / 2, y), text, font=font, fill=fill)


def main():
    pasta = sys.argv[1]
    rotulo = sys.argv[2] if len(sys.argv) > 2 else "NOVO NO FEED"
    src = os.path.join(pasta, "slide1.png")
    if not os.path.exists(src):
        sys.exit(f"slide1.png nao encontrado em {pasta}")
    s = Image.open(src).convert("RGB")
    tw = 960
    s = s.resize((tw, int(s.height * tw / s.width)), Image.LANCZOS)
    im = Image.new("RGB", (W, H), (0, 0, 0))
    y0 = 300
    mask = Image.new("L", s.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s.width - 1, s.height - 1], radius=28, fill=255)
    im.paste(s, ((W - tw) // 2, y0), mask)
    d = ImageDraw.Draw(im)
    yb = y0 + s.height + 60
    centered(d, yb, rotulo, _font("b", 44), GOLD)
    centered(d, yb + 70, "Arraste o carrossel no feed e leia completo", _font("r", 36), OFF)
    centered(d, yb + 125, "@mentedeinvestidor.br", _font("r", 32), GREY)
    out = os.path.join(pasta, "story.jpg")
    im.save(out, quality=94)
    print("ok", out)


if __name__ == "__main__":
    main()

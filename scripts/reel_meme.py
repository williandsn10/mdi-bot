"""
MODELO REELS MEME (MDI) — refaz um clipe meme no formato da marca.
Uso:
  python scripts/reel_meme.py CLIPE.mp4 PASTA_SAIDA --linhas "Quando perguntam|quanto eu tenho investido." --negrito "Eu:"
Opcoes: --tema escuro|claro (padrao escuro)
Gera: PASTA_SAIDA/reel.mp4 (1080x1920, 30 fps, audio original) + bg.png.
O recorte do clipe e detectado sozinho (area nao branca do video; se o clipe ja for tela cheia, usa o quadro inteiro).
Layout (area segura de Reels): cabecalho MDI (logo, nome, selo azul, @), texto da piada, clipe,
logo + site (www.mentedeinvestidor.com.br) acima da faixa de interface inferior, fundo proprio da marca
(degrade grafite com brilho dourado discreto). Requer o projeto Remotion em anuncio-indicadores-mdi.
"""
import argparse, json, os, shutil, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageChops

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import modelo1_x as m  # noqa: E402

REMOTION = os.path.join(ROOT, "anuncio-indicadores-mdi")
W, H, M = 1080, 1920, 72
S = m.S
SITE = "www.mentedeinvestidor.com.br"


def ffmpeg(*args):
    return subprocess.run(["npx", "remotion", "ffmpeg", "-y", "-v", "error", *args], cwd=REMOTION,
                          capture_output=True, text=True, shell=True)


def probe(clip):
    r = subprocess.run(["npx", "remotion", "ffprobe", "-v", "error", "-show_entries", "stream=width,height,duration",
                        "-of", "json", clip], cwd=REMOTION, capture_output=True, text=True, shell=True)
    st = json.loads(r.stdout)["streams"]
    v = [s for s in st if "width" in s][0]
    return int(v["width"]), int(v["height"]), float(v.get("duration") or 0) or float(st[-1]["duration"])


def detect_box(clip, w, h, tmp):
    """Caixa do video dentro de uma arte com fundo claro (tipo post); senao, quadro inteiro."""
    frame = os.path.join(tmp, "frame.png")
    ffmpeg("-ss", "2", "-i", clip, "-frames:v", "1", frame)
    im = Image.open(frame).convert("RGB"); px = im.load()
    rows = [y for y in range(h) if sum(1 for x in range(0, w, 4) if sum(px[x, y]) < 600) > w // 8]
    cols = [x for x in range(w) if sum(1 for y in range(0, h, 4) if sum(px[x, y]) < 600) > 12]
    if rows and cols and (rows[-1] - rows[0]) < h * 0.8:
        x0, x1, y0, y1 = cols[0] + 10, cols[-1] - 10, rows[0] + 10, rows[-1] - 10
        return x0, y0, x1 - x0, y1 - y0
    return 0, 0, w, h


def make_bg(linhas, negrito, tema, out, box_top):
    th = m.THEMES[tema]; FG, GREY = th["fg"], th["grey"]
    # fundo da marca: degrade grafite + brilho dourado discreto
    base = Image.new("RGB", (W, H))
    col = Image.new("RGB", (1, H))
    for y in range(H):
        t = y / H
        col.putpixel((0, y), (int(22 - 14 * t), int(22 - 14 * t), int(26 - 16 * t)))
    base = col.resize((W, H))
    glow = Image.new("RGB", (W, H), (0, 0, 0)); ImageDraw.Draw(glow).ellipse([-200, 1250, 700, 2100], fill=(58, 44, 18))
    base = ImageChops.add(base, glow.filter(ImageFilter.GaussianBlur(170)))
    im = base.resize((W * S, H * S), Image.LANCZOS); d = ImageDraw.Draw(im)
    av = m.make_avatar(); top = 250
    im.paste(av, (M * S, top * S), av)
    d.ellipse([M * S, top * S, (M + m.AV) * S - 1, (top + m.AV) * S - 1], outline=(70, 66, 58), width=3 * S)
    nx = (M + m.AV + 30) * S; ny = top + m.AV // 2
    fb = m.f("segoeuib.ttf", 46); fr = m.f("segoeui.ttf", 36)
    d.text((nx, (ny - 52) * S), m.NAME, font=fb, fill=FG)
    nw = d.textlength(m.NAME, font=fb)
    m.badge(im, int(nx + nw + 32 * S), int((ny - 26) * S), 24 * S)
    d.text((nx, (ny + 6) * S), m.HANDLE, font=fr, fill=GREY)
    y = 500; f62 = m.f("segoeui.ttf", 58); f62b = m.f("segoeuib.ttf", 58)
    for t in linhas:
        d.text((M * S, y * S), t, font=f62, fill=FG); y += 76
    if negrito:
        d.text((M * S, y * S), negrito, font=f62b, fill=FG)
    # logo + site, abaixo do clipe e acima da faixa de interface do Reels
    lg = Image.open(os.path.join(ROOT, "assets", "logo-mdi-fundo-preto.png")).convert("RGB")
    lg = lg.crop(lg.convert("L").point(lambda v: 255 if v > 25 else 0).getbbox())
    lw = 150 * S; lg = lg.resize((lw, int(lg.height * lw / lg.width)), Image.LANCZOS)
    lgr = lg.convert("RGBA"); lgr.putalpha(lg.convert("L").point(lambda v: min(255, int(v * 2.6))))
    ly = box_top + 18
    im.paste(lgr, (M * S, ly * S), lgr)
    sf = m.f("segoeuib.ttf", 30)
    d.text(((M + 150 + 28) * S, (ly + 6) * S), SITE, font=sf, fill=m.BLUE if False else (214, 178, 94))
    d.text(((M + 150 + 28) * S, (ly + 48) * S), "Siga " + m.HANDLE, font=m.f("segoeui.ttf", 26), fill=GREY)
    im.resize((W, H), Image.LANCZOS).save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clipe"); ap.add_argument("saida")
    ap.add_argument("--linhas", required=True); ap.add_argument("--negrito", default="")
    ap.add_argument("--tema", default="escuro")
    ap.add_argument("--crop", help="x,y,w,h do clipe (opcional; senao detecta sozinho)")
    ap.add_argument("--linhas2", help="2o texto (troca no meio do clipe), linhas separadas por |")
    ap.add_argument("--negrito2", default="")
    ap.add_argument("--troca", type=float, default=0, help="segundo em que o texto troca")
    a = ap.parse_args()
    out = os.path.abspath(a.saida); os.makedirs(out, exist_ok=True)
    clip = os.path.abspath(a.clipe)
    w, h, dur = probe(clip)
    cx, cy, cw, ch = (int(v) for v in a.crop.split(",")) if a.crop else detect_box(clip, w, h, out)
    box_w = 864; scale = box_w / cw; box_h = ch * scale
    box_top = 740 if box_h < 760 else 700
    if box_h > 720: box_w = int(720 * cw / ch); scale = box_w / cw; box_h = ch * scale
    left = (W - box_w) // 2
    os.makedirs(os.path.join(REMOTION, "public", "meme"), exist_ok=True)
    make_bg(a.linhas.split("|"), a.negrito, a.tema, os.path.join(out, "bg.png"), int(box_top + box_h))
    if a.linhas2:
        make_bg(a.linhas2.split("|"), a.negrito2, a.tema, os.path.join(out, "bg2.png"), int(box_top + box_h))
        shutil.copy(os.path.join(out, "bg2.png"), os.path.join(REMOTION, "public", "meme", "bg2.png"))
    else:
        shutil.copy(os.path.join(out, "bg.png"), os.path.join(REMOTION, "public", "meme", "bg2.png"))
    os.makedirs(os.path.join(REMOTION, "public", "meme"), exist_ok=True)
    shutil.copy(os.path.join(out, "bg.png"), os.path.join(REMOTION, "public", "meme", "bg.png"))
    shutil.copy(clip, os.path.join(REMOTION, "public", "meme", "clip.mp4"))
    props = dict(durationFrames=round(dur * 30), cropX=cx, cropY=cy, cropW=cw, cropH=ch, srcW=w, srcH=h,
                 boxW=box_w, left=left, top=box_top,
                 switchFrame=round(a.troca * 30) if a.linhas2 else 99999)
    pf = os.path.join(out, "props.json"); json.dump(props, open(pf, "w"))
    r = subprocess.run(["npx", "remotion", "render", "src/meme/index.ts", "MemeInvest", os.path.join(out, "reel.mp4"),
                        f"--props={pf}"], cwd=REMOTION, capture_output=True, text=True, shell=True)
    print(r.stdout[-300:], r.stderr[-300:])
    print("ok", os.path.join(out, "reel.mp4"))


if __name__ == "__main__":
    main()

"""
publish_instagram.py — Publicação automática de carrossel no Instagram
(API do Instagram com login do Instagram: graph.instagram.com)
"""
import argparse, os, sys, time, requests
from pathlib import Path
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = lambda *a, **k: None

script_dir = Path(__file__).resolve().parent
for d in [script_dir, *script_dir.parents[:3]]:
    if (d / ".env").exists():
        load_dotenv(d / ".env")
        break

IG_ID = os.getenv("INSTAGRAM_USER_ID")
TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
BASE_URL = f"https://graph.instagram.com/{os.getenv('META_API_VERSION', 'v21.0')}"


BASE_PUBLIC_URL = None  # ex.: https://raw.githubusercontent.com/williandsn10/mdi-bot/main


def public_url_from_repo(image_path: str) -> str:
    """URL pública da imagem já enviada (push) ao repositório público; confere que responde 200."""
    rel = Path(image_path).resolve().relative_to(Path(__file__).resolve().parent.parent).as_posix()
    url = f"{BASE_PUBLIC_URL.rstrip('/')}/{rel}"
    for _ in range(12):
        if requests.head(url, timeout=15, allow_redirects=True).status_code == 200:
            print(f"  Pública: {url}")
            return url
        time.sleep(5)
    raise RuntimeError(f"Imagem não ficou pública (confira se o push foi feito e o repositório é público): {url}")


def host_image(image_path: str) -> str:
    """Hospeda a imagem em URL pública (repositório público, ou catbox.moe como alternativa)"""
    if BASE_PUBLIC_URL:
        return public_url_from_repo(image_path)
    with open(image_path, "rb") as f:
        resp = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": (Path(image_path).name, f)},
            timeout=60,
        )
    url = resp.text.strip()
    if not url.startswith("https://"):
        raise RuntimeError(f"Falha no upload: {url}")
    print(f"  Hospedada: {url}")
    return url


def create_media_container(image_path: str) -> str:
    resp = requests.post(f"{BASE_URL}/{IG_ID}/media", data={
        "access_token": TOKEN,
        "image_url": host_image(image_path),
        "is_carousel_item": "true",
    }, timeout=60)
    result = resp.json()
    if "id" not in result:
        raise RuntimeError(f"Erro container: {result}")
    print(f"  Container: {result['id']}")
    return result["id"]


def create_carousel(media_ids: list, caption: str) -> str:
    resp = requests.post(f"{BASE_URL}/{IG_ID}/media", data={
        "access_token": TOKEN,
        "media_type": "CAROUSEL",
        "children": ",".join(media_ids),
        "caption": caption,
    }, timeout=30)
    result = resp.json()
    if "id" not in result:
        raise RuntimeError(f"Erro carrossel: {result}")
    print(f"  Carrossel: {result['id']}")
    return result["id"]


def create_single(image_path: str, caption: str) -> str:
    resp = requests.post(f"{BASE_URL}/{IG_ID}/media", data={
        "access_token": TOKEN,
        "image_url": host_image(image_path),
        "caption": caption,
    }, timeout=60)
    result = resp.json()
    if "id" not in result:
        raise RuntimeError(f"Erro post unico: {result}")
    print(f"  Post unico: {result['id']}")
    return result["id"]


def create_reel(video_path: str, caption: str) -> str:
    """Reel (video .mp4 ja enviado ao repositorio publico, passado como --images arquivo.mp4). Publica SO na aba Reels (share_to_feed=false), por decisao do dono em 2026-10-30."""
    resp = requests.post(f"{BASE_URL}/{IG_ID}/media", data={
        "access_token": TOKEN,
        "media_type": "REELS",
        "video_url": host_image(video_path),
        "caption": caption,
        "share_to_feed": "false",
    }, timeout=60)
    result = resp.json()
    if "id" not in result:
        raise RuntimeError(f"Erro reel: {result}")
    print(f"  Reel: {result['id']}")
    return result["id"]


def wait_ready(container_id: str) -> bool:
    for i in range(12):
        resp = requests.get(f"{BASE_URL}/{container_id}",
            params={"fields": "status_code", "access_token": TOKEN}, timeout=15)
        status = resp.json().get("status_code", "")
        if status == "FINISHED":
            return True
        if status == "ERROR":
            raise RuntimeError(f"Container com erro: {resp.json()}")
        print(f"  Processando... {i*5}s")
        time.sleep(5)
    return False


def publish(container_id: str) -> str:
    resp = requests.post(f"{BASE_URL}/{IG_ID}/media_publish", data={
        "access_token": TOKEN,
        "creation_id": container_id,
    }, timeout=30)
    result = resp.json()
    if "id" not in result:
        raise RuntimeError(f"Erro publicar: {result}")
    return result["id"]


def run(images: list, caption: str, dry_run: bool = False):
    if not IG_ID or not TOKEN:
        print("ERRO: Credenciais nao encontradas no .env.")
        sys.exit(1)
    if not 1 <= len(images) <= 10:
        print("ERRO: Use de 1 a 10 imagens (1 = post unico; 2 a 10 = carrossel).")
        sys.exit(1)

    print(f"\nPublicando {len(images)} slides no Instagram...")
    if dry_run:
        print("[DRY RUN] Tudo OK. Remova --dry-run para publicar.")
        return

    if len(images) == 1:
        is_video = images[0].lower().endswith(".mp4")
        print("\nReel (video)..." if is_video else "\nPost de imagem unica...")
        cid = create_reel(images[0], caption) if is_video else create_single(images[0], caption)
        if not wait_ready(cid):
            print("ERRO: Timeout no processamento.")
            sys.exit(1)
        print(f"\nPublicado com sucesso! Post ID: {publish(cid)}")
        return

    print("\nPasso 1/3 - Criando containers...")
    ids = [create_media_container(img) for img in images]
    print("\nPasso 2/3 - Montando carrossel...")
    carousel_id = create_carousel(ids, caption)
    print("\nPasso 3/3 - Publicando...")
    if not wait_ready(carousel_id):
        print("ERRO: Timeout no processamento.")
        sys.exit(1)
    print(f"\nPublicado com sucesso! Post ID: {publish(carousel_id)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", nargs="+", required=True)
    parser.add_argument("--caption", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--base-url", help="URL base pública do repositório (raw.githubusercontent.com/...); "
                        "as imagens precisam estar commitadas e com push feito")
    args = parser.parse_args()
    BASE_PUBLIC_URL = args.base_url
    run(args.images, args.caption, args.dry_run)

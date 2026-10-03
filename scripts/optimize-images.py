#!/usr/bin/env python3
"""Generate fast responsive image assets for SCOR static builds.

Put large source images in src/assets/media/originals.
The script creates compressed responsive derivatives under src/assets/media/generated
and writes src/data/generated-images.json for build.mjs.
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ModuleNotFoundError:
    Image = None
    ImageOps = None

PROJECT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT / "src" / "assets" / "media" / "originals"
OUT_DIR = PROJECT / "src" / "assets" / "media" / "generated"
MANIFEST = PROJECT / "src" / "data" / "generated-images.json"
SIZES = [360, 640, 960, 1280, 1600]
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "image"


def flatten_rgb(img: Image.Image, background=(255, 255, 255)) -> Image.Image:
    img = img.convert("RGBA")
    canvas = Image.new("RGBA", img.size, background + (255,))
    canvas.alpha_composite(img)
    return canvas.convert("RGB")


def resize_width(img: Image.Image, width: int) -> Image.Image:
    if width >= img.width:
        return img.copy()
    height = max(1, round(img.height * (width / img.width)))
    return img.resize((width, height), Image.Resampling.LANCZOS)


def rel(path: Path) -> str:
    return "/" + str(path.relative_to(PROJECT / "src")).replace("\\", "/").replace("assets/", "assets/", 1)


def public_path(path: Path) -> str:
    # Source path under src/assets/... becomes /assets/...
    return "/" + str(path.relative_to(PROJECT / "src")).replace("\\", "/")


def optimize_one(source: Path, used_ids: set[str]) -> dict:
    base_id = slugify(str(source.relative_to(SOURCE_DIR).with_suffix("")))
    image_id = base_id
    n = 2
    while image_id in used_ids:
        image_id = f"{base_id}-{n}"
        n += 1
    used_ids.add(image_id)

    target_dir = OUT_DIR / image_id
    target_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(source) as raw:
        img = ImageOps.exif_transpose(raw)
        img.load()
        has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
        work = img.convert("RGBA") if has_alpha else img.convert("RGB")
        orig_w, orig_h = work.size

        widths = [w for w in SIZES if w < orig_w]
        if orig_w not in widths:
            widths.append(orig_w)
        widths = sorted(set(widths))

        webp_entries = []
        fallback_entries = []
        fallback_ext = "png" if has_alpha else "jpg"

        for width in widths:
            resized = resize_width(work, width)
            actual_w, actual_h = resized.size

            webp_path = target_dir / f"{image_id}-{actual_w}.webp"
            try:
                resized.save(webp_path, "WEBP", quality=78, method=6)
                webp_entries.append({"width": actual_w, "height": actual_h, "src": public_path(webp_path)})
            except Exception:
                pass

            fallback_path = target_dir / f"{image_id}-{actual_w}.{fallback_ext}"
            if fallback_ext == "png":
                resized.save(fallback_path, "PNG", optimize=True)
            else:
                flatten_rgb(resized).save(fallback_path, "JPEG", quality=82, optimize=True, progressive=True)
            fallback_entries.append({"width": actual_w, "height": actual_h, "src": public_path(fallback_path)})

        thumb = resize_width(work, min(32, orig_w))
        thumb_path = target_dir / f"{image_id}-blur.webp"
        try:
            thumb.save(thumb_path, "WEBP", quality=35, method=4)
        except Exception:
            thumb_path = target_dir / f"{image_id}-blur.jpg"
            flatten_rgb(thumb).save(thumb_path, "JPEG", quality=35, optimize=True)

    return {
        "id": image_id,
        "source": str(source.relative_to(SOURCE_DIR)).replace("\\", "/"),
        "alt": source.stem.replace("-", " ").replace("_", " ").strip(),
        "width": orig_w,
        "height": orig_h,
        "aspectRatio": round(orig_w / orig_h, 6) if orig_h else 1,
        "thumb": public_path(thumb_path),
        "formats": {
            "webp": webp_entries,
            "fallback": fallback_entries,
        },
    }


def main() -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    sources = [source for source in sorted(SOURCE_DIR.rglob("*")) if source.is_file() and source.suffix.lower() in EXTENSIONS]
    if sources and Image is None:
        raise SystemExit("Pillow is required to optimize images. Install it with: pip install -r requirements.txt")
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    images = {}
    used_ids: set[str] = set()
    for source in sources:
        try:
            item = optimize_one(source, used_ids)
            images[item["id"]] = item
        except Exception as exc:
            print(f"[image-optimize] skipped {source}: {exc}")

    MANIFEST.write_text(json.dumps({
        "generatedAt": None,
        "sourceDir": "src/assets/media/originals",
        "outputDir": "src/assets/media/generated",
        "sizes": SIZES,
        "images": images,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[image-optimize] optimized {len(images)} image(s)")


if __name__ == "__main__":
    main()

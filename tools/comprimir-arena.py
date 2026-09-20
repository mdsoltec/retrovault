#!/usr/bin/env python3
"""Compressão in-place das imagens de public/ (Arena only) — v2 HIGH QUALITY.

Estratégia (qualidade em 1º lugar):
- consoles/  → PNG truecolor (RGBA), 1600px, sem quantização
- avatares   → PNG truecolor (RGB), 256px, sem quantização
- covers/    → opacas: JPEG q90 4:4:4 (renomeia .png → .jpg; pipeline já
               tenta .jpg — covers.js linhas 137-138, zero edição de código)
               com alfa real: PNG truecolor 480x720
- overlays/  → paleta 256c só se erro visual imperceptível; senão truecolor

Originais preservados no histórico git (9b72d7d).
"""
from __future__ import annotations
import sys
from pathlib import Path
from PIL import Image, ImageChops, ImageStat

ROOT = Path("/home/user/retroverso/public")
SKIP_SMALL = 48 * 1024

def human(n: float) -> str:
    if n < 1024: return f"{n:.0f} B"
    if n < 1048576: return f"{n/1024:.0f} KB"
    return f"{n/1048576:.2f} MB"

def resize_max(im: Image.Image, max_long: int, square=False) -> Image.Image:
    w, h = im.size
    if square and (w > max_long or h > max_long):
        return im.resize((max_long, max_long), Image.LANCZOS)
    if max(w, h) > max_long:
        s = max_long / max(w, h)
        return im.resize((max(1, round(w*s)), max(1, round(h*s))), Image.LANCZOS)
    return im

def erro_visivel(orig: Image.Image, nova: Image.Image) -> float:
    """Erro médio 0-255 compondo sobre preto (ignora pixels transparentes)."""
    def flat(i):
        bg = Image.new("RGB", i.size, (0, 0, 0))
        bg.paste(i, mask=i.getchannel("A") if "A" in i.getbands() else None)
        return bg
    d = ImageChops.difference(flat(orig), flat(nova))
    return sum(ImageStat.Stat(d).mean) / 3

def save_truecolor_png(im: Image.Image, path: Path, before: int) -> int:
    tmp = path.with_suffix(".tmp.png")
    im.save(tmp, optimize=True)
    after = tmp.stat().st_size
    (tmp.replace(path) if after < before else (tmp.unlink(), before)[1])
    return min(after, before)

def consoles():
    tb = ta = n = 0
    for f in sorted((ROOT / "assets/consoles").glob("*.png")):
        if f.stat().st_size <= SKIP_SMALL: continue
        before = f.stat().st_size
        with Image.open(f) as im:
            im.load()
            out = resize_max(im.convert("RGBA"), 1600)
            after = save_truecolor_png(out, f, before)
        tb += before; ta += after; n += 1
    print(f"[consoles] {n} | {human(tb)} -> {human(ta)} (PNG truecolor 1600px)")

def avatares():
    tb = ta = n = 0
    for f in sorted(ROOT.glob("assets/avatar-*.png")):
        if f.stat().st_size <= SKIP_SMALL: continue
        before = f.stat().st_size
        with Image.open(f) as im:
            im.load()
            out = resize_max(im.convert("RGB"), 256, square=True)
            after = save_truecolor_png(out, f, before)
        tb += before; ta += after; n += 1
    print(f"[avatares] {n} | {human(tb)} -> {human(ta)} (PNG truecolor 256px)")

def covers():
    tb = ta = n_jpg = n_png = 0
    for f in sorted((ROOT / "covers").rglob("*.png")):
        if f.stat().st_size <= SKIP_SMALL: continue
        before = f.stat().st_size
        with Image.open(f) as im:
            im.load()
            rgba = im.convert("RGBA")
            a = rgba.getchannel("A")
            tem_alfa = a.getextrema()[0] < 250
            out = resize_max(rgba, 720)
            if tem_alfa:
                after = save_truecolor_png(out, f, before)
                n_png += 1
            else:
                jpg = f.with_suffix(".jpg")
                tmp = jpg.with_suffix(".tmp.jpg")
                out.convert("RGB").save(tmp, quality=90, subsampling=0,
                                        optimize=True, progressive=True)
                after = tmp.stat().st_size
                if after < before:
                    tmp.replace(jpg); f.unlink()
                else:
                    tmp.unlink(); after = save_truecolor_png(out, f, before); n_png += 1; continue
                n_jpg += 1
        tb += before; ta += after
    print(f"[covers] {n_jpg} -> JPEG q90 | {n_png} PNG truecolor | "
          f"{human(tb)} -> {human(ta)}")

def overlays():
    tb = ta = n_pal = n_true = 0
    for f in sorted((ROOT / "overlays").rglob("*.png")):
        if f.stat().st_size <= SKIP_SMALL: continue
        before = f.stat().st_size
        with Image.open(f) as im:
            im.load()
            rgba = im.convert("RGBA")
            q = rgba.quantize(colors=256, method=Image.Quantize.FASTOCTREE)
            back = q.convert("RGBA")
            if erro_visivel(rgba, back) < 1.5:
                tmp = f.with_suffix(".tmp.png")
                q.save(tmp, optimize=True)
                after = tmp.stat().st_size
                if after < before: tmp.replace(f)
                else: tmp.unlink(); after = before
                n_pal += 1
            else:
                after = save_truecolor_png(rgba, f, before)
                n_true += 1
        tb += before; ta += after
    print(f"[overlays] {n_pal} paleta OK + {n_true} truecolor | "
          f"{human(tb)} -> {human(ta)}")

if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else None
    fns = {"consoles": consoles, "avatars": avatares,
           "covers": covers, "overlays": overlays}
    for nome, fn in fns.items():
        if only and nome != only: continue
        fn()

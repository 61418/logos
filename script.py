from __future__ import annotations

from itertools import permutations
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


swatches = {
    "a": [(248, 109, 142), (125, 132, 80), (71, 71, 73)],
    "b": [(223, 180, 85), (8, 72, 159), (211, 6, 47)],
    "c": [(200, 113, 42), (51, 95, 132), (109, 116, 126)],
    "d": [(0, 0, 0), (255, 255, 255)],
    "e": [(106, 85, 80), (242, 210, 172)],
}


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return "#{:02X}{:02X}{:02X}".format(r, g, b).lower()


TEXT = "61418"
PALETTES = [
    (f"{swatch_name}{ii}", rgb_to_hex(*bg), rgb_to_hex(*fg))
    for swatch_name, swatch in swatches.items()
    for ii, (bg, fg) in enumerate(permutations(swatch, 2))
]


def unique_colors(
    swatches_dict: dict[str, list[tuple[int, int, int]]],
) -> list[tuple[int, int, int]]:
    seen = set()
    out: list[tuple[int, int, int]] = []
    for _, cols in swatches_dict.items():
        for c in cols:
            if c not in seen:
                seen.add(c)
                out.append(c)
    return out


TRANSPARENT_COLORS = unique_colors(swatches)
OUT_DIR = Path("assets")
SOLID_DIR = OUT_DIR / "solid"
TRANSPARENT_DIR = OUT_DIR / "transparent"
SOLID_DIR.mkdir(parents=True, exist_ok=True)
TRANSPARENT_DIR.mkdir(parents=True, exist_ok=True)
SPECS = [
    ("favicon", (512, 512)),
    ("og", (1200, 630)),
    ("header", (1600, 300)),
]


def load_font(px: int) -> ImageFont.FreeTypeFont:
    root = Path(__file__).resolve().parent
    font_path = root / "Helvetica.ttc"
    for idx in (1, 0):
        try:
            return ImageFont.truetype(str(font_path), px, index=idx)
        except OSError:
            continue

    raise OSError(f"Could not load font from {font_path}")


def best_font_size(
    draw: ImageDraw.ImageDraw,
    size: tuple[int, int],
    width_fill: float,
    height_fill: float,
) -> int:
    w, h = size
    target_w = int(w * width_fill)
    max_h = int(h * height_fill)

    lo, hi = 5, 2000
    best = lo

    while lo <= hi:
        mid = (lo + hi) // 2
        font = load_font(mid)
        bbox = draw.textbbox((0, 0), TEXT, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        if tw <= target_w and th <= max_h:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1

    return best


def render_logo_solid(
    size: tuple[int, int],
    bg_hex: str,
    fg_hex: str,
    width_fill: float,
    height_fill: float,
) -> Image.Image:
    w, h = size
    img = Image.new("RGB", (w, h), bg_hex)
    draw = ImageDraw.Draw(img)

    font_px = best_font_size(draw, size, width_fill, height_fill)
    font = load_font(font_px)

    bbox = draw.textbbox((0, 0), TEXT, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    x = (w - tw) // 2 - bbox[0]
    y = (h - th) // 2 - bbox[1]

    draw.text((x, y), TEXT, font=font, fill=fg_hex)
    return img


def render_logo_transparent(
    size: tuple[int, int],
    fg_rgb: tuple[int, int, int],
    width_fill: float,
    height_fill: float,
) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))  # fully transparent background
    draw = ImageDraw.Draw(img)

    font_px = best_font_size(draw, size, width_fill, height_fill)
    font = load_font(font_px)

    bbox = draw.textbbox((0, 0), TEXT, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    x = (w - tw) // 2 - bbox[0]
    y = (h - th) // 2 - bbox[1]

    r, g, b = fg_rgb
    draw.text((x, y), TEXT, font=font, fill=(r, g, b, 255))
    return img


def fills_for(spec_name: str) -> tuple[float, float]:
    if spec_name == "favicon":
        return (0.78, 0.78)
    return (0.72, 0.72)


def main():
    for palette_name, bg, fg in PALETTES:
        for spec_name, size in SPECS:
            wf, hf = fills_for(spec_name)
            img = render_logo_solid(size, bg, fg, wf, hf)
            out = SOLID_DIR / f"{palette_name}_{spec_name}.png"
            img.save(out, optimize=True)
            print("wrote", out)

    for rgb in TRANSPARENT_COLORS:
        hex_name = rgb_to_hex(*rgb)[1:]  # drop '#'
        for spec_name, size in SPECS:
            wf, hf = fills_for(spec_name)
            img = render_logo_transparent(size, rgb, wf, hf)
            out = TRANSPARENT_DIR / f"{hex_name}_{spec_name}.png"
            img.save(out, optimize=True)
            print("wrote", out)


if __name__ == "__main__":
    main()

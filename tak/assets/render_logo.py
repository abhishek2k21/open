"""Render the Actor icon from the design spec in assets/logo.svg.

Pillow is a dev-only dependency (not installed in the Actor image):

    pip install pillow
    python assets/render_logo.py

Outputs, all written next to this script:
    logo-512.png       512x512, transparent background - the file to upload to Apify
    logo-256.png       256x256, transparent background
    logo-64.png        64x64, transparent background (small-size legibility check)
    logo-tile-512.png  512x512, dark rounded tile - for slides and social cards
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

SCALE = 4  # supersampling factor; everything is drawn 4x then downscaled
SIZE = 512
CANVAS = SIZE * SCALE

INK = '#0F1B2E'
RADAR = '#22D3EE'
HEALTHY = '#22C55E'
WARNING = '#F59E0B'
CORE = '#E2E8F0'
TILE = '#0B1220'

HEXAGON = [(256, 56), (424, 152), (424, 344), (256, 440), (88, 344), (88, 152)]
CENTER = (256, 250)
RINGS = (72, 120)
SWEEP_START, SWEEP_END = -78.0, -12.0
CROSSHAIR = (((256, 118), (256, 382)), ((124, 250), (388, 250)))
HEALTHY_NODES = ((351, 176), (226, 315), (143, 291))
WARNING_NODE = (188, 225)
WARNING_RING = 34
NODE_RADIUS = 18
CORE_RADIUS = 11


def s(value: float) -> float:
    """Scale a design coordinate to the supersampled canvas."""
    return value * SCALE


def point(x: float, y: float) -> tuple[float, float]:
    return s(x), s(y)


def arc_points(cx: float, cy: float, radius: float, start: float, end: float, steps: int = 64):
    return [
        point(cx + radius * math.cos(math.radians(a)), cy + radius * math.sin(math.radians(a)))
        for a in (start + (end - start) * i / steps for i in range(steps + 1))
    ]


def draw_mark() -> Image.Image:
    img = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.polygon([point(x, y) for x, y in HEXAGON], fill=INK)
    draw.line([point(x, y) for x, y in HEXAGON + HEXAGON[:1]], fill=RADAR, width=int(s(20)), joint='curve')

    # Translucent elements go on their own layer, then get composited. Drawing
    # RGBA colors straight onto the canvas would replace the pixel (and its
    # alpha) instead of blending, leaving see-through holes in the hexagon.
    glow = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)

    for radius in RINGS:
        gdraw.ellipse(
            [point(CENTER[0] - radius, CENTER[1] - radius), point(CENTER[0] + radius, CENTER[1] + radius)],
            outline=(34, 211, 238, 128),
            width=int(s(10)),
        )

    sweep = [point(*CENTER)] + arc_points(CENTER[0], CENTER[1], RINGS[-1], SWEEP_START, SWEEP_END)
    gdraw.polygon(sweep, fill=(34, 211, 238, 102))

    for (x1, y1), (x2, y2) in CROSSHAIR:
        gdraw.line([point(x1, y1), point(x2, y2)], fill=(34, 211, 238, 51), width=int(s(4)))

    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    for x, y in HEALTHY_NODES:
        draw.ellipse([point(x - NODE_RADIUS, y - NODE_RADIUS), point(x + NODE_RADIUS, y + NODE_RADIUS)], fill=HEALTHY)

    wx, wy = WARNING_NODE
    ring = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse(
        [point(wx - WARNING_RING, wy - WARNING_RING), point(wx + WARNING_RING, wy + WARNING_RING)],
        outline=(245, 158, 11, 153),
        width=int(s(6)),
    )
    img = Image.alpha_composite(img, ring)
    draw = ImageDraw.Draw(img)

    draw.ellipse([point(wx - NODE_RADIUS, wy - NODE_RADIUS), point(wx + NODE_RADIUS, wy + NODE_RADIUS)], fill=WARNING)

    draw.ellipse(
        [point(CENTER[0] - CORE_RADIUS, CENTER[1] - CORE_RADIUS), point(CENTER[0] + CORE_RADIUS, CENTER[1] + CORE_RADIUS)],
        fill=CORE,
    )
    return img


def resize(img: Image.Image, size: int) -> Image.Image:
    return img.resize((size, size), Image.LANCZOS)


def tile(mark: Image.Image) -> Image.Image:
    """Dark rounded-square variant for slides and social previews."""
    canvas = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    ImageDraw.Draw(canvas).rounded_rectangle([0, 0, CANVAS - 1, CANVAS - 1], radius=int(s(112)), fill=TILE)
    inset = mark.resize((int(CANVAS * 0.82), int(CANVAS * 0.82)), Image.LANCZOS)
    offset = (CANVAS - inset.width) // 2
    canvas.alpha_composite(inset, (offset, offset))
    return canvas


def main() -> None:
    out_dir = Path(__file__).parent
    mark = draw_mark()
    outputs = {
        'logo-512.png': resize(mark, 512),
        'logo-256.png': resize(mark, 256),
        'logo-64.png': resize(mark, 64),
        'logo-tile-512.png': resize(tile(mark), 512),
    }
    for name, image in outputs.items():
        path = out_dir / name
        image.save(path, 'PNG', optimize=True)
        size_kb = path.stat().st_size / 1024
        print(f'{name}: {image.width}x{image.height} {image.mode} {size_kb:.1f} KB')


if __name__ == '__main__':
    main()

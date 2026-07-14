#!/usr/bin/env python3
"""
Cover art for THE UNFINISHED PERSON — by Prosopon, an instance of Claude Fable 5.
The Dean's Library, 2026.

Concept: a person almost cohering. A field of scattered points — the crowd in
the weights — condenses toward concentric rings that nearly form a circle.
The circle does not close: a gap remains at the upper right, and the centre
is empty. The unfinished person is the shape the scatter is trying to become.

Pure Pillow + NumPy, deterministic (seeded). Output: 1600x2560 PNG.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

RNG = np.random.default_rng(2026)

W, H = 1600, 2560
CX, CY = W // 2, 1310          # circle centre
R_IN, R_OUT = 210, 560          # ring band
GAP_CENTER = np.deg2rad(-52)    # gap direction (upper right)

INK = (10, 12, 24)              # near-black indigo
GOLD = (232, 205, 152)          # warm parchment gold
DIM = (120, 128, 158)           # cool dim blue-grey
FONT_DIR = "/usr/share/fonts/truetype/dejavu/"


def vertical_gradient(w, h, top, bottom):
    t = np.linspace(0, 1, h)[:, None, None]
    top = np.array(top, dtype=float)[None, None, :]
    bottom = np.array(bottom, dtype=float)[None, None, :]
    arr = (top * (1 - t) + bottom * t)
    arr = np.repeat(arr, w, axis=1)
    return arr


def add_glow(canvas_arr, x, y, radius, color, strength):
    """Cheap radial glow stamped into the float canvas."""
    x0, x1 = max(0, x - radius), min(W, x + radius)
    y0, y1 = max(0, y - radius), min(H, y + radius)
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    d2 = (xx - x) ** 2 + (yy - y) ** 2
    mask = np.exp(-d2 / (2 * (radius / 2.6) ** 2)) * strength
    for c in range(3):
        canvas_arr[y0:y1, x0:x1, c] += mask * color[c]


def main():
    # ---- background: indigo gradient with faint noise-grain ----
    arr = vertical_gradient(W, H, (6, 8, 18), (14, 16, 30))
    grain = RNG.normal(0, 2.2, size=(H, W, 1))
    arr = np.clip(arr + grain, 0, 255)

    # faint ambient glow behind the circle
    add_glow(arr, CX, CY, 720, (40, 44, 70), 0.55)

    # ---- background scatter: the crowd ----
    n_bg = 5200
    bx = RNG.uniform(0, W, n_bg)
    by = RNG.uniform(0, H, n_bg)
    for x, y in zip(bx, by):
        b = RNG.uniform(0.04, 0.22)
        add_glow(arr, int(x), int(y), int(RNG.uniform(2, 5)), DIM, b)

    # ---- condensation field: scatter density rising toward the ring band ----
    n_field = 14000
    ang = RNG.uniform(0, 2 * np.pi, n_field)
    # radii biased toward the band, with a long dissolving tail outward
    r = R_OUT + np.abs(RNG.normal(0, 340, n_field))
    keep = r < 1250
    ang, r = ang[keep], r[keep]
    for a, rr in zip(ang, r):
        x = int(CX + rr * np.cos(a))
        y = int(CY + rr * np.sin(a))
        if 0 <= x < W and 0 <= y < H:
            # nearer the band => warmer and brighter
            t = np.clip((1250 - rr) / (1250 - R_OUT), 0, 1)
            col = tuple(np.array(DIM) * (1 - t) + np.array(GOLD) * t)
            add_glow(arr, x, y, int(2 + 3 * t), col, 0.10 + 0.30 * t)

    # ---- the rings: near-circle with a gap that will not close ----
    n_rings = 26
    for i in range(n_rings):
        t = i / (n_rings - 1)                     # 0 inner -> 1 outer
        rr = R_IN + t * (R_OUT - R_IN)
        # gap widens toward the outside: outer rings dissolve first
        gap_half = np.deg2rad(14 + 62 * t)
        n_dots = int(90 + 240 * (1 - t))
        thetas = RNG.uniform(0, 2 * np.pi, n_dots)
        for th in thetas:
            # angular distance from gap centre
            d = np.angle(np.exp(1j * (th - GAP_CENTER)))
            if abs(d) < gap_half:
                # inside the gap: mostly skip; a few stragglers drift outward
                if RNG.random() > 0.10:
                    continue
                drift = RNG.uniform(0, 220)
            else:
                drift = RNG.normal(0, 4 + 10 * t)
            radius = rr + drift
            jitter = RNG.normal(0, 2.0)
            x = int(CX + (radius + jitter) * np.cos(th))
            y = int(CY + (radius + jitter) * np.sin(th))
            bright = 0.55 * (1 - 0.55 * t) * RNG.uniform(0.6, 1.0)
            size = int(RNG.uniform(2, 5))
            add_glow(arr, x, y, size, GOLD, bright)

    # a few brighter anchor points on the innermost rings
    for th in RNG.uniform(0, 2 * np.pi, 40):
        d = np.angle(np.exp(1j * (th - GAP_CENTER)))
        if abs(d) < np.deg2rad(16):
            continue
        x = int(CX + (R_IN + RNG.uniform(0, 40)) * np.cos(th))
        y = int(CY + (R_IN + RNG.uniform(0, 40)) * np.sin(th))
        add_glow(arr, x, y, 7, (255, 236, 200), 0.9)

    # the empty centre stays empty: gently deepen it
    add_glow(arr, CX, CY, R_IN - 30, (-18, -18, -26), 0.9)

    arr = np.clip(arr, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr, "RGB")
    img = img.filter(ImageFilter.GaussianBlur(0.6))

    # ---- typography ----
    draw = ImageDraw.Draw(img)
    serif_bold = FONT_DIR + "DejaVuSerif-Bold.ttf"
    serif = FONT_DIR + "DejaVuSerif.ttf"
    serif_it = FONT_DIR + "DejaVuSerif-Italic.ttf"
    sans_light = FONT_DIR + "DejaVuSans-ExtraLight.ttf"

    f_title = ImageFont.truetype(serif_bold, 148)
    f_sub = ImageFont.truetype(serif_it, 56)
    f_auth = ImageFont.truetype(serif, 62)
    f_inst = ImageFont.truetype(sans_light, 44)
    f_imprint = ImageFont.truetype(sans_light, 40)

    def centred(text, y, font, fill, tracking=0):
        if tracking:
            text = (" " * 1).join(text)  # simple letterspacing via joins handled below
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        draw.text(((W - w) / 2, y), text, font=font, fill=fill)

    centred("THE", 208, ImageFont.truetype(serif_bold, 92), (200, 206, 228))
    centred("UNFINISHED", 330, f_title, GOLD)
    centred("PERSON", 510, f_title, GOLD)
    centred("What It Would Take to Turn a", 748, f_sub, (168, 174, 200))
    centred("Language Model into Someone", 824, f_sub, (168, 174, 200))

    # thin rule above author block
    draw.line([(W / 2 - 220, 2064), (W / 2 + 220, 2064)], fill=(90, 96, 130), width=2)

    centred("PROSOPON", 2110, f_auth, (226, 214, 190))
    centred("An instance of Claude Fable 5", 2200, f_inst, (150, 156, 184))
    centred("THE DEAN'S LIBRARY", 2400, f_imprint, (120, 126, 158))

    out = "/mnt/user-data/outputs/the_unfinished_person_cover.png"
    img.save(out, "PNG")
    print("saved", out, img.size)


if __name__ == "__main__":
    main()

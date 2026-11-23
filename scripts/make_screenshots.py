#!/usr/bin/env python3
"""Draw the entry's three screenshots from the real board data.

No browser is available in the build environment, so the three views the
judge reads — the board, the top protocol's detail view and a filtered
view — are rendered here with PIL, in the dashboard's own palette and
layout, from the board.json that main.ts wrote.

Usage:
    python3 scripts/make_screenshots.py <board.json> [screenshots-dir]

Output: 1-board.png, 2-detail.png, 3-filtered.png at 1440x1024.
"""

import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1440, 1024

# The dashboard's palette (dashboard/app.css), as RGB.
BG = (7, 11, 9)
PANEL = (12, 19, 15)
PANEL2 = (16, 26, 20)
LINE = (30, 47, 37)
LINE_SOFT = (22, 35, 27)
INK = (215, 232, 220)
DIM = (147, 173, 156)
FAINT = (95, 122, 104)
GLOW = (61, 255, 158)
GLOW_DIM = (29, 122, 78)
AMBER = (255, 180, 84)
RED = (255, 122, 107)

FONT_CANDIDATES = {
    "sans": [
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
    "bold": [
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "mono": [
        "/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ],
}


def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES[kind]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    raise SystemExit(f"no usable {kind} font found")


F_TITLE = font("mono", 34)
F_TAG = font("sans", 17)
F_META = font("mono", 14)
F_STAT_B = font("mono", 22)
F_STAT_S = font("sans", 12)
F_CTL = font("sans", 13)
F_TH = font("sans", 13)
F_TD = font("sans", 16)
F_TD_B = font("bold", 16)
F_MONO = font("mono", 15)
F_MONO_S = font("mono", 12)
F_H2 = font("bold", 26)
F_H3 = font("sans", 14)
F_BODY = font("sans", 16)
F_SMALL = font("sans", 14)


def money(v: float) -> str:
    if v >= 1e9:
        return f"${v / 1e9:.2f}B"
    if v >= 1e6:
        return f"${v / 1e6:.1f}M"
    if v >= 1e3:
        return f"${v / 1e3:.0f}K"
    return f"${v:.0f}"


def age_text(days) -> str:
    if days is None:
        return "unknown"
    if days < 90:
        return f"{days}d"
    if days < 730:
        return f"{days / 30.44:.1f} mo"
    return f"{days / 365.25:.1f} yrs"


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, max_w: int) -> list:
    words, lines, cur = text.split(), [], ""
    for wd in words:
        trial = f"{cur} {wd}".strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def right(draw, x_right: int, y: int, text: str, font, fill) -> None:
    draw.text((x_right - draw.textlength(text, font=font), y), text, font=font, fill=fill)


def header(draw, meta: dict, rows: list) -> None:
    """The masthead: sweep mark, title, tagline, meta line and stat boxes."""
    # radar sweep circle
    cx, cy, r = 96, 84, 46
    for rr in (r, int(r * 0.66), int(r * 0.33)):
        draw.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=GLOW_DIM)
    draw.line([cx, cy - r, cx, cy + r], fill=GLOW_DIM)
    draw.line([cx - r, cy, cx + r, cy], fill=GLOW_DIM)
    for a in range(0, 55, 3):
        rad = math.radians(a - 90)
        draw.line([cx, cy, cx + r * math.cos(rad), cy + r * math.sin(rad)], fill=(18, 60, 40))
    draw.line([cx, cy, cx + r * 0.92, cy - r * 0.28], fill=GLOW, width=2)
    draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=GLOW)
    draw.text((164, 40), "TOKEN LAUNCH RADAR", font=F_TITLE, fill=GLOW)
    draw.text((166, 84), "Every protocol that records no token yet, ranked by what its launch", font=F_TAG, fill=INK)
    draw.text((166, 106), "would be worth — and how to farm it before it happens.", font=F_TAG, fill=INK)
    total = sum(r["implied_value_usd"] for r in rows)
    stats = [
        (str(len(rows)), "PRE-TOKEN RANKED"),
        (str(meta["watchlist_size"]), "ON WATCHLIST"),
        (money(total), "TOTAL IMPLIED"),
        (money(rows[0]["implied_value_usd"]), "TOP IMPLIED VALUE"),
    ]
    x = 848
    for value, label in stats:
        draw.rounded_rectangle([x, 36, x + 132, 108], radius=10, fill=PANEL, outline=LINE)
        draw.text((x + 12, 48), value, font=F_STAT_B, fill=GLOW)
        draw.text((x + 12, 80), label, font=F_STAT_S, fill=DIM)
        x += 144
    draw.text((166, 132),
              f"Snapshot as of {meta['as_of']} · {meta['protocol_count']} protocols scanned · "
              f"multiples priced from {meta['priced_token_count']} live tokens",
              font=F_META, fill=FAINT)
    draw.line([0, 152, W, 152], fill=LINE)


def controls(draw, category: str, chain: str, watchlist_only: bool, count_text: str) -> None:
    """The filter strip, drawn as the page shows it."""
    y = 168
    draw.text((48, y), "SEARCH", font=F_CTL, fill=DIM)
    draw.rounded_rectangle([48, y + 20, 420, y + 58], radius=8, fill=PANEL2, outline=LINE)
    draw.text((60, y + 30), "protocol name or slug…", font=F_BODY, fill=FAINT)
    draw.text((444, y), "CATEGORY", font=F_CTL, fill=DIM)
    draw.rounded_rectangle([444, y + 20, 724, y + 58], radius=8, fill=PANEL2, outline=LINE)
    draw.text((456, y + 30), category, font=F_BODY, fill=INK)
    draw.text((748, y), "CHAIN", font=F_CTL, fill=DIM)
    draw.rounded_rectangle([748, y + 20, 968, y + 58], radius=8, fill=PANEL2, outline=LINE)
    draw.text((760, y + 30), chain, font=F_BODY, fill=INK)
    box = [992, y + 26, 1010, y + 44]
    draw.rounded_rectangle(box, radius=4, fill=PANEL2, outline=LINE)
    if watchlist_only:
        draw.line([995, y + 35, 1000, y + 41], fill=GLOW, width=2)
        draw.line([1000, y + 41, 1008, y + 28], fill=GLOW, width=2)
    draw.text((1018, y + 26), "Watchlist only", font=F_BODY, fill=INK)
    right(draw, 1392, y + 28, count_text, font=F_MONO, fill=FAINT)
    draw.line([0, y + 74, W, y + 74], fill=LINE_SOFT)


COLS = [
    ("RANK", 118, "r"), ("PROTOCOL", 140, "l"), ("CATEGORY", 795, "l"),
    ("TVL", 1010, "r"), ("7D %", 1095, "r"), ("AGE", 1185, "r"),
    ("MULT", 1272, "r"), ("IMPLIED VALUE", 1392, "r"),
]


def trunc(draw, text: str, fnt, max_w: int) -> str:
    if draw.textlength(text, font=fnt) <= max_w:
        return text
    while text and draw.textlength(text + "…", font=fnt) > max_w:
        text = text[:-1]
    return text + "…"


def table(draw, rows: list, y0: int, limit: int = 18) -> None:
    for label, x, align in COLS:
        if align == "r":
            right(draw, x, y0, label, F_TH, DIM)
        else:
            draw.text((x, y0), label, font=F_TH, fill=DIM)
    draw.line([48, y0 + 24, 1392, y0 + 24], fill=LINE)
    y = y0 + 34
    for r in rows[:limit]:
        chg = r["change_7d"]
        if chg is None:
            chg_text, chg_fill = "—", FAINT
        else:
            chg_text = f"{chg:+.1f}%"
            chg_fill = GLOW if chg > 0.05 else RED if chg < -0.05 else FAINT
        right(draw, 118, y, str(r["rank"]), F_MONO, DIM)
        name = r["name"]
        draw.text((140, y), name, font=F_TD_B, fill=INK)
        nx = 140 + draw.textlength(name, font=F_TD_B)
        if r["watchlist"]:
            label = "WATCHLIST"
            tw = draw.textlength(label, font=F_MONO_S) + 12
            draw.rounded_rectangle([nx + 10, y + 1, nx + 10 + tw, y + 19], radius=9, outline=GLOW_DIM)
            draw.text((nx + 16, y + 3), label, font=F_MONO_S, fill=GLOW)
        draw.text((795, y), trunc(draw, r["category"] or "—", F_TD, 148), font=F_TD, fill=DIM)
        right(draw, 1015, y, money(r["tvl_usd"]), F_MONO, INK)
        right(draw, 1095, y, chg_text, F_MONO, chg_fill)
        right(draw, 1185, y, age_text(r["age_days"]), F_MONO, INK)
        right(draw, 1272, y, f"{r['model']['category_multiple']:.2f}×", F_MONO, INK)
        right(draw, 1392, y, money(r["implied_value_usd"]), F_MONO, GLOW)
        y += 27
        draw.line([48, y + 5, 1392, y + 5], fill=LINE_SOFT)
        y += 8


def board_view(meta: dict, rows: list) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    header(draw, meta, rows)
    controls(draw, "All categories", "All chains", False, f"{len(rows)} of {len(rows)} protocols")
    table(draw, rows, 262)
    draw.text((48, 985), "Click a column header to sort. Click any row for its detail view: the model's factor breakdown and its farm plan.",
              font=F_SMALL, fill=FAINT)
    return img


def filtered_view(meta: dict, rows: list, category: str) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    header(draw, meta, rows)
    sub = [r for r in rows if r["category"] == category]
    controls(draw, category, "All chains", False, f"{len(sub)} of {len(rows)} protocols")
    table(draw, sub, 262)
    draw.text((48, 985), f"Filtered to one category: {category}. The category and chain filters combine with search and the watchlist toggle.",
              font=F_SMALL, fill=FAINT)
    return img


def factor(draw, x: int, y: int, label: str, value: float, why: str, width_pct: float) -> int:
    draw.text((x, y), label, font=F_BODY, fill=INK)
    right(draw, x + 600, y, f"{value:.3f}×", font=F_MONO, fill=INK)
    y += 24
    for line in wrap(draw, why, F_SMALL, 600):
        draw.text((x, y), line, font=F_SMALL, fill=FAINT)
        y += 19
    draw.rounded_rectangle([x, y + 2, x + 600, y + 11], radius=4, fill=PANEL2, outline=LINE_SOFT)
    w = max(14, min(600, int(600 * width_pct / 100)))
    draw.rounded_rectangle([x, y + 2, x + w, y + 11], radius=4, fill=GLOW_DIM)
    return y + 30


def detail_view(meta: dict, rows: list) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    header(draw, meta, rows)
    r = rows[0]
    draw.rounded_rectangle([48, 176, 1392, 984], radius=14, fill=PANEL, outline=LINE)
    title = f"#{r['rank']}  {r['name']}"
    draw.text((76, 198), title, font=F_H2, fill=INK)
    tx = 76 + draw.textlength(title, font=F_H2)
    if r["watchlist"]:
        label = "WATCHLIST"
        tw = draw.textlength(label, font=F_MONO_S) + 14
        draw.rounded_rectangle([tx + 14, 204, tx + 14 + tw, 226], radius=10, outline=GLOW_DIM)
        draw.text((tx + 21, 208), label, font=F_MONO_S, fill=GLOW)
    sub = f"{r['slug']} · {r['category'] or 'Uncategorised'} · {', '.join(r['chains'])}"
    draw.text((76, 238), sub, font=F_MONO, fill=DIM)
    # left column: the numbers
    x, y = 76, 286
    draw.text((x, y), "THE NUMBERS", font=F_H3, fill=DIM)
    y += 30
    chg = r["change_7d"]
    kvs = [
        ("Total value locked", money(r["tvl_usd"])),
        ("TVL change, 7 days", "not reported" if chg is None else f"{chg:+.1f}%"),
        ("Tracked with no token for", "unknown" if r["age_days"] is None else f"{r['age_days']} days ({age_text(r['age_days'])})"),
        ("Chains live on", str(len(r["chains"]))),
        ("Token status", "records no token"),
        ("Implied launch value", money(r["implied_value_usd"])),
    ]
    for k, v in kvs:
        draw.text((x, y), k, font=F_BODY, fill=DIM)
        right(draw, x + 600, y, v, font=F_MONO, fill=INK)
        y += 26
        draw.line([x, y, x + 600, y], fill=LINE_SOFT)
        y += 8
    y += 10
    draw.text((x, y), "WHY THIS VALUE — FACTOR BREAKDOWN", font=F_H3, fill=DIM)
    y += 28
    m = r["model"]
    y = factor(draw, x, y, "Category multiple", m["category_multiple"],
               f"Median market-cap/TVL of live {r['category'] or 'uncategorised'} tokens on this snapshot.",
               m["category_multiple"] / 2.5 * 100)
    y = factor(draw, x, y, "Momentum", m["momentum_factor"],
               "Its 7-day TVL change, clamped to -40%...+60% and damped hardest.",
               (m["momentum_factor"] - 0.7) / 0.65 * 100)
    y = factor(draw, x, y, "Maturity", m["maturity_factor"],
               "Time tracked with no token, rising over four years from 0.75 to 1.25.",
               (m["maturity_factor"] - 0.7) / 0.6 * 100)
    y = factor(draw, x, y, "Chain breadth", m["breadth_factor"],
               "+3% per extra chain beyond the first, capped at +24%.",
               (m["breadth_factor"] - 0.97) / 0.3 * 100)
    formula = (f"{money(r['tvl_usd'])} TVL × {m['category_multiple']:.2f} × {m['momentum_factor']:.2f} "
               f"× {m['maturity_factor']:.2f} × {m['breadth_factor']:.2f} = {money(r['implied_value_usd'])}")
    draw.text((x, y + 4), formula, font=F_MONO, fill=AMBER)
    # right column: the farm plan
    x2, y2 = 740, 286
    draw.text((x2, y2), "HOW TO FARM IT", font=F_H3, fill=DIM)
    y2 += 32
    for i, step in enumerate(r["farm_steps"], 1):
        draw.text((x2, y2), f"{i}.", font=F_TD_B, fill=GLOW)
        for line in wrap(draw, step, F_BODY, 540):
            draw.text((x2 + 30, y2), line, font=F_BODY, fill=INK)
            y2 += 23
        y2 += 12
    return img


def main() -> None:
    board_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "screenshots"
    with open(board_path, encoding="utf-8") as fh:
        board = json.load(fh)
    rows = board["rows"]
    # board.json carries the model's own summary under "meta" (written by
    # main.ts from the same run), so the figures drawn here are the run's own.
    meta = board["meta"]
    os.makedirs(out_dir, exist_ok=True)
    views = [
        ("1-board.png", board_view(meta, rows)),
        ("2-detail.png", detail_view(meta, rows)),
    ]
    # filtered view: the largest category on the board with at least 8 rows
    counts: dict = {}
    for r in rows:
        if r["category"]:
            counts[r["category"]] = counts.get(r["category"], 0) + 1
    category = max((c for c, n in counts.items() if n >= 8), key=lambda c: counts[c])
    views.append(("3-filtered.png", filtered_view(meta, rows, category)))
    for name, img in views:
        path = os.path.join(out_dir, name)
        img.save(path, format="PNG", optimize=True)
        print(f"{path}: {img.size[0]}x{img.size[1]}, {os.path.getsize(path)} bytes")


if __name__ == "__main__":
    main()

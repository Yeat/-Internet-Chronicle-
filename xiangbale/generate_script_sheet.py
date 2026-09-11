#!/usr/bin/env python3
"""Official Trouble Brewing–style custom script sheet for 《乡巴佬》."""

from __future__ import annotations

import json
import math
import random
import urllib.request
import zipfile
from pathlib import Path

from PIL import (
    Image,
    ImageChops,
    ImageDraw,
    ImageEnhance,
    ImageFilter,
    ImageFont,
    ImageOps,
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdf_canvas

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "script.json"
ICON_DIR = ROOT / "icons"
FONT_DIR = ROOT / "fonts"
OUT_DIR = ROOT / "output"
ARTIFACT_DIR = Path("/opt/cursor/artifacts")

DPI = 300
PAGE_W = int(210 / 25.4 * DPI)
PAGE_H = int(297 / 25.4 * DPI)

TEAM_ORDER = ["townsfolk", "outsider", "minion", "demon", "fabled"]
TEAM_LABEL = {
    "townsfolk": "镇民",
    "outsider": "外来者",
    "minion": "爪牙",
    "demon": "恶魔",
    "fabled": "传奇",
}
TEAM_COLOR = {
    "townsfolk": (40, 78, 128),
    "outsider": (55, 105, 145),
    "minion": (150, 48, 42),
    "demon": (120, 28, 30),
    "fabled": (150, 108, 28),
}
TEAM_BAR = {
    "townsfolk": (48, 88, 138),
    "outsider": (70, 120, 155),
    "minion": (165, 58, 48),
    "demon": (125, 32, 34),
    "fabled": (175, 130, 40),
}
NAME_COLOR = TEAM_COLOR
INK = (42, 32, 24)
INK_SOFT = (85, 65, 45)
DISCLAIMER = (115, 80, 50)
TITLE_RED = (120, 36, 28)

ICON_FALLBACKS = {
    "maomaojuntuan_juanbing": (
        "https://patchwiki.biligame.com/images/jbzlbwgwjcygf/"
        "d/d9/p2gdfh2y56pwd8jsi3b3zm5h941arzz.png"
    ),
}


def download(url: str, dest: Path, timeout: float = 60.0) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        dest.write_bytes(resp.read())


def ensure_fonts() -> dict[str, Path]:
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    body = FONT_DIR / "LXGWWenKai.ttf"
    title = FONT_DIR / "NotoSerifCJKsc-Bold.otf"
    title_reg = FONT_DIR / "NotoSerifCJKsc-SemiBold.otf"
    fallback = Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc")

    if not body.exists():
        try:
            print("Downloading LXGW WenKai ...")
            download(
                "https://github.com/lxgw/LxgwWenKai/releases/download/v1.501/LXGWWenKai-Regular.ttf",
                body,
            )
        except Exception as exc:
            print(f"WenKai download failed ({exc})")

    if not title.exists() or not title_reg.exists():
        zip_path = FONT_DIR / "NotoSerifCJKsc.zip"
        try:
            print("Downloading Noto Serif CJK SC ...")
            download(
                "https://github.com/googlefonts/noto-cjk/releases/download/Serif2.003/09_NotoSerifCJKsc.zip",
                zip_path,
            )
            with zipfile.ZipFile(zip_path) as zf:
                names = zf.namelist()
                for base, dest in [
                    ("NotoSerifCJKsc-Bold.otf", title),
                    ("NotoSerifCJKsc-SemiBold.otf", title_reg),
                ]:
                    hit = next((n for n in names if n.endswith(base)), None)
                    if hit:
                        dest.write_bytes(zf.read(hit))
            zip_path.unlink(missing_ok=True)
        except Exception as exc:
            print(f"Noto Serif download failed ({exc})")
            zip_path.unlink(missing_ok=True)

    body_path = body if body.exists() else fallback
    return {
        "title": title if title.exists() else body_path,
        "title_reg": title_reg if title_reg.exists() else body_path,
        "body": body_path,
    }


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def make_parchment(w: int, h: int) -> Image.Image:
    rng = random.Random(7)
    base = Image.new("RGB", (w, h), (226, 206, 164))

    small = Image.new("RGBA", (max(1, w // 4), max(1, h // 4)), (0, 0, 0, 0))
    sd = ImageDraw.Draw(small)
    for _ in range(160):
        cx, cy = rng.randint(0, small.size[0]), rng.randint(0, small.size[1])
        rw, rh = rng.randint(8, 90), rng.randint(6, 60)
        tone = rng.choice(
            [
                (200, 170, 120),
                (180, 140, 90),
                (235, 220, 185),
                (165, 130, 85),
                (210, 185, 140),
            ]
        )
        sd.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=(*tone, rng.randint(20, 48)))
    blotch = small.resize((w, h), Image.Resampling.LANCZOS)

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for i in range(140):
        a = int(48 * (1 - i / 140))
        od.rectangle([i, i, w - 1 - i, h - 1 - i], outline=(105, 72, 38, a))
    for cx, cy in [(100, 110), (w - 120, 140), (140, h - 130), (w - 110, h - 150)]:
        od.ellipse([cx - 200, cy - 120, cx + 200, cy + 120], fill=(150, 110, 60, 30))

    grain = Image.effect_noise((w, h), 30).convert("L")
    base = Image.blend(base, Image.merge("RGB", (grain, grain, grain)), 0.10).convert("RGBA")
    base = Image.alpha_composite(base, blotch)
    base = Image.alpha_composite(base, overlay)

    star = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    st = ImageDraw.Draw(star)
    for _ in range(220):
        x, y = rng.randint(40, w - 40), rng.randint(40, h - 40)
        r = rng.choice([1, 1, 1, 2, 2, 3])
        a = rng.randint(18, 55)
        col = (255, 245, 220, a) if rng.random() > 0.35 else (120, 90, 50, a // 2)
        st.ellipse([x - r, y - r, x + r, y + r], fill=col)
        if r >= 2 and rng.random() > 0.6:
            st.line([(x - r - 1, y), (x + r + 1, y)], fill=col, width=1)
            st.line([(x, y - r - 1), (x, y + r + 1)], fill=col, width=1)
    base = Image.alpha_composite(base, star)

    fiber = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fiber)
    for y in range(0, h, 6):
        fd.line([(0, y), (w, y)], fill=(140, 110, 70, 10))
    base = Image.alpha_composite(base, fiber)
    return base.filter(ImageFilter.GaussianBlur(0.25)).convert("RGB")


def draw_scroll_border(draw: ImageDraw.ImageDraw, w: int, h: int) -> None:
    color = (95, 70, 45)

    def flourish(cy: int) -> None:
        draw.ellipse([w // 2 - 18, cy - 18, w // 2 + 18, cy + 18], outline=color, width=2)
        draw.ellipse([w // 2 - 8, cy - 8, w // 2 + 8, cy + 8], outline=color, width=1)
        for sign in (-1, 1):
            x0 = w // 2 + sign * 30
            pts = [(x0 + sign * i, cy + math.sin(i / 28) * 10) for i in range(0, 280, 4)]
            draw.line(pts, fill=color, width=2)
            tip_x = x0 + sign * 270
            draw.polygon(
                [
                    (tip_x, cy),
                    (tip_x - sign * 14, cy - 10),
                    (tip_x - sign * 8, cy),
                    (tip_x - sign * 14, cy + 10),
                ],
                outline=color,
            )
        for cx in (70, w - 70):
            draw.arc([cx - 40, cy - 28, cx + 40, cy + 28], 200, 340, fill=color, width=2)

    flourish(48)
    flourish(h - 52)
    for i, a in enumerate([140, 70, 35]):
        inset = 22 + i * 3
        draw.rectangle([inset, inset, w - inset, h - inset], outline=(100, 72, 42, a), width=2)


def tinted_icon(path: Path, size: int, tint: tuple[int, int, int]) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    side = max(im.size)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(im, ((side - im.size[0]) // 2, (side - im.size[1]) // 2), im)
    canvas = canvas.resize((size, size), Image.Resampling.LANCZOS)

    r, g, b, a = canvas.split()
    gray = ImageOps.grayscale(canvas)
    inv = ImageOps.invert(gray)
    ink = ImageEnhance.Contrast(inv).enhance(1.6)
    ink = ImageEnhance.Brightness(ink).enhance(1.15)
    alpha = ImageChops.multiply(a, ink)

    color_layer = Image.new("RGBA", (size, size), (*tint, 255))
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(color_layer, (0, 0), alpha)

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([1, 1, size - 2, size - 2], fill=255)
    clipped = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    clipped.paste(out, (0, 0), mask)
    return clipped


def wrap_text(text: str, font_obj: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines: list[str] = []
    for para in text.split("\n"):
        if para == "":
            lines.append("")
            continue
        cur = ""
        for ch in para:
            trial = cur + ch
            if draw.textlength(trial, font=font_obj) <= max_width:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = ch
        if cur:
            lines.append(cur)
    return lines if lines else [""]


def measure_block(
    ability: str,
    name: str,
    fonts: dict,
    max_w: int,
    icon: int,
    line_gap: int,
    name_ability_gap: int = 4,
) -> int:
    """Height of one character entry; ability text wraps within max_w."""
    tmp = Image.new("RGB", (8, 8))
    d = ImageDraw.Draw(tmp)
    lines = wrap_text(ability, fonts["ability"], max_w, d)
    na, nd = fonts["name"].getmetrics()
    aa, ad = fonts["ability"].getmetrics()
    line_h = aa + ad
    text_h = (na + nd) + name_ability_gap + len(lines) * line_h + max(0, len(lines) - 1) * line_gap
    return max(icon, text_h)


def load_script():
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    meta = data[0]
    chars = [c for c in data[1:] if c.get("id") != "_meta"]
    by_team: dict[str, list] = {t: [] for t in TEAM_ORDER}
    for c in chars:
        by_team.setdefault(c.get("team", "townsfolk"), []).append(c)
    return meta, by_team


def split_columns(items: list) -> tuple[list, list]:
    mid = (len(items) + 1) // 2
    return items[:mid], items[mid:]


def draw_vertical_label(
    base: Image.Image,
    text: str,
    box: tuple[int, int, int, int],
    font_obj: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
) -> None:
    x0, y0, x1, y1 = box
    tmp = Image.new("RGBA", (900, 900), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    bbox = td.textbbox((0, 0), text, font=font_obj)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    td.text((-bbox[0], -bbox[1]), text, font=font_obj, fill=(*fill, 255))
    cropped = tmp.crop((0, 0, tw + 1, th + 1)).rotate(90, expand=True)
    bw, bh = x1 - x0, y1 - y0
    rw, rh = cropped.size
    # Scale down if segment is short
    if rh > bh - 8 or rw > bw - 4:
        scale = min((bh - 8) / max(1, rh), (bw - 4) / max(1, rw), 1.0)
        cropped = cropped.resize(
            (max(1, int(rw * scale)), max(1, int(rh * scale))),
            Image.Resampling.LANCZOS,
        )
        rw, rh = cropped.size
    px = x0 + max(0, (bw - rw) // 2)
    py = y0 + max(0, (bh - rh) // 2)
    base.paste(cropped, (px, py), cropped)


def render() -> Image.Image:
    """Large-type sheet: maximize fonts, wrap abilities, fill the page."""
    paths = ensure_fonts()
    meta, by_team = load_script()
    img = make_parchment(PAGE_W, PAGE_H)
    draw = ImageDraw.Draw(img, "RGBA")
    draw_scroll_border(draw, PAGE_W, PAGE_H)

    # Compact header → more room for large body type
    f_title = font(paths["title"], 96)
    f_sub = font(paths["body"], 18)
    f_meta = font(paths["body"], 16)
    f_bar = font(paths["title"], 34)
    f_footer = font(paths["body"], 14)

    title = meta.get("name", "乡巴佬")
    author = meta.get("author", "")
    logo_path = ICON_DIR / "_logo.png"
    header_top = 56
    if logo_path.exists():
        logo = Image.open(logo_path).convert("RGBA")
        logo_h = 70
        logo = logo.resize(
            (max(1, int(logo.size[0] * logo_h / logo.size[1])), logo_h),
            Image.Resampling.LANCZOS,
        )
        img.paste(logo, ((PAGE_W - logo.size[0]) // 2, header_top), logo)
        title_y = header_top + logo_h - 4
    else:
        title_y = header_top

    tb = draw.textbbox((0, 0), title, font=f_title)
    tw = tb[2] - tb[0]
    tx = (PAGE_W - tw) // 2
    draw.text((tx + 3, title_y + 3), title, font=f_title, fill=(80, 40, 25, 80))
    draw.text((tx, title_y), title, font=f_title, fill=TITLE_RED)

    sub = "非官方自定义剧本 · UNOFFICIAL CUSTOM SCRIPT · 大字版"
    sb = draw.textbbox((0, 0), sub, font=f_sub)
    sx = (PAGE_W - (sb[2] - sb[0])) // 2
    sy = title_y + (tb[3] - tb[1]) + 2
    draw.text((sx, sy), sub, font=f_sub, fill=DISCLAIMER)

    author_line = f"作者 Author：{author}" if author else ""
    ay = sy + 22
    if author_line:
        ab = draw.textbbox((0, 0), author_line, font=f_meta)
        draw.text(((PAGE_W - (ab[2] - ab[0])) // 2, ay), author_line, font=f_meta, fill=INK_SOFT)
        content_top = ay + 26
    else:
        content_top = ay + 6

    draw.line([(120, content_top), (PAGE_W - 120, content_top)], fill=(110, 80, 50), width=2)
    content_top += 10

    margin_right = 46
    bar_x = 34
    bar_w = 70
    content_x = bar_x + bar_w + 12
    gutter = 26
    col_w = (PAGE_W - content_x - margin_right - gutter) // 2
    footer_h = 46
    content_bottom = PAGE_H - footer_h
    available_h = content_bottom - content_top

    def layout_height(name_sz: int, abil_sz: int, icon: int, line_gap: int, row_gap: int, sect_gap: int) -> int:
        fset = {
            "name": font(paths["title_reg"], name_sz),
            "ability": font(paths["body"], abil_sz),
        }
        aw = col_w - icon - 14
        total = 0
        teams_present = [t for t in TEAM_ORDER if by_team.get(t)]
        for ti, team in enumerate(teams_present):
            chars = by_team[team]
            left_chars, right_chars = split_columns(chars)
            left_h = sum(
                measure_block(c.get("ability", ""), c.get("name", ""), fset, aw, icon, line_gap) + row_gap
                for c in left_chars
            )
            right_h = sum(
                measure_block(c.get("ability", ""), c.get("name", ""), fset, aw, icon, line_gap) + row_gap
                for c in right_chars
            )
            total += max(left_h, right_h)
            if ti < len(teams_present) - 1:
                total += sect_gap
        return total

    # Binary search largest ability font that still fits (wrapping allowed)
    lo, hi = 18, 40
    best = (24, 34, 70, 2, 10, 18)
    while lo <= hi:
        abil = (lo + hi) // 2
        name_sz = abil + 12
        icon = max(56, int(abil * 2.9))
        line_gap = max(2, abil // 8)
        row_gap = max(8, abil // 2 + 2)
        sect_gap = max(14, abil + 2)
        h = layout_height(name_sz, abil, icon, line_gap, row_gap, sect_gap)
        if h <= available_h:
            best = (abil, name_sz, icon, line_gap, row_gap, sect_gap)
            lo = abil + 1
        else:
            hi = abil - 1

    abil_sz, name_sz, icon_size, line_gap, row_gap, sect_gap = best
    fonts = {
        "name": font(paths["title_reg"], name_sz),
        "ability": font(paths["body"], abil_sz),
    }
    used = layout_height(name_sz, abil_sz, icon_size, line_gap, row_gap, sect_gap)
    print(
        f"Large-type: ability={abil_sz}px name={name_sz}px icon={icon_size} "
        f"used={used}/{available_h}"
    )

    # Stretch leftover vertical space into gaps so the page is filled
    spare = available_h - used
    row_slots = 0
    for team in TEAM_ORDER:
        chars = by_team.get(team, [])
        if not chars:
            continue
        left_chars, right_chars = split_columns(chars)
        row_slots += max(len(left_chars), len(right_chars))
    if spare > 6 and row_slots > 0:
        row_gap += spare // row_slots
        used2 = layout_height(name_sz, abil_sz, icon_size, line_gap, row_gap, sect_gap)
        spare2 = available_h - used2
        n_sect = max(1, sum(1 for t in TEAM_ORDER if by_team.get(t)) - 1)
        if spare2 > 4:
            sect_gap += spare2 // n_sect
        print(f"Fill stretch: row_gap={row_gap} sect_gap={sect_gap}")

    amw = col_w - icon_size - 14
    section_spans: list[tuple[str, int, int]] = []

    def draw_char(ch: dict, x: int, y: int) -> int:
        team = ch.get("team", "townsfolk")
        tint = TEAM_COLOR[team]
        name = ch.get("name", "")
        ability = ch.get("ability", "")
        cid = ch.get("id", "")
        ip = ICON_DIR / f"{cid}.png"
        if ip.exists():
            icon = tinted_icon(ip, icon_size, tint)
        else:
            icon = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
            ImageDraw.Draw(icon).ellipse(
                [2, 2, icon_size - 3, icon_size - 3],
                outline=(*tint, 255),
                width=3,
            )

        text_x = x + icon_size + 12
        draw.text((text_x, y), name, font=fonts["name"], fill=NAME_COLOR[team])
        na, nd = fonts["name"].getmetrics()
        name_h = na + nd
        lines = wrap_text(ability, fonts["ability"], amw, draw)
        aa, ad = fonts["ability"].getmetrics()
        line_h = aa + ad
        ay0 = y + name_h + 4
        for i, line in enumerate(lines):
            draw.text(
                (text_x, ay0 + i * (line_h + line_gap)),
                line,
                font=fonts["ability"],
                fill=INK,
            )
        text_h = name_h + 4 + len(lines) * line_h + max(0, len(lines) - 1) * line_gap
        content_h = max(icon_size, text_h)
        rh = content_h + row_gap
        icon_y = y + max(0, (content_h - icon_size) // 2)
        img.paste(icon, (x, icon_y), icon)
        return rh

    y = content_top
    left_x = content_x
    right_x = content_x + col_w + gutter
    teams_present = [t for t in TEAM_ORDER if by_team.get(t)]

    for ti, team in enumerate(teams_present):
        chars = by_team[team]
        left_chars, right_chars = split_columns(chars)
        y0 = y
        y_left = y
        y_right = y
        for c in left_chars:
            y_left += draw_char(c, left_x, y_left)
        for c in right_chars:
            y_right += draw_char(c, right_x, y_right)
        y = max(y_left, y_right)
        section_spans.append((team, y0, y))

        if ti < len(teams_present) - 1:
            rule_y = y + max(2, sect_gap // 3)
            draw.line(
                [(content_x, rule_y), (PAGE_W - margin_right, rule_y)],
                fill=(100, 72, 45, 180),
                width=2,
            )
            mid = (content_x + PAGE_W - margin_right) // 2
            draw.polygon(
                [(mid, rule_y - 5), (mid + 6, rule_y), (mid, rule_y + 5), (mid - 6, rule_y)],
                fill=(100, 72, 45, 200),
            )
            y = rule_y + max(8, sect_gap - sect_gap // 3)

    if section_spans:
        bar_top = section_spans[0][1] - 4
        bar_bottom = section_spans[-1][2] + 2
        under = Image.new("RGBA", (bar_w, bar_bottom - bar_top), (48, 36, 26, 245))
        noise = Image.effect_noise((bar_w, bar_bottom - bar_top), 16).convert("L")
        under = Image.blend(
            under.convert("RGB"),
            Image.merge("RGB", (noise, noise, noise)),
            0.10,
        ).convert("RGBA")
        img.paste(under, (bar_x, bar_top), under)

        for team, y0, y1 in section_spans:
            color = TEAM_BAR[team]
            seg_h = max(1, y1 - y0)
            seg = Image.new("RGBA", (bar_w - 6, seg_h), (*color, 245))
            img.paste(seg, (bar_x + 3, y0), seg)
            ImageDraw.Draw(img).line(
                [(bar_x + 4, y0 + 2), (bar_x + 4, y1 - 2)],
                fill=(255, 245, 220, 90),
                width=2,
            )
            draw_vertical_label(
                img,
                TEAM_LABEL[team],
                (bar_x + 2, y0, bar_x + bar_w - 2, y1),
                f_bar,
                (255, 248, 230),
            )

        ImageDraw.Draw(img).rectangle(
            [bar_x, bar_top, bar_x + bar_w, bar_bottom],
            outline=(70, 48, 28, 220),
            width=3,
        )

    footer = "Blood on the Clocktower 非官方自定义剧本单 · 大字版 · 名称与能力原文取自 JSON · 仅供同好娱乐"
    fb = draw.textbbox((0, 0), footer, font=f_footer)
    draw.text(((PAGE_W - (fb[2] - fb[0])) // 2, PAGE_H - 38), footer, font=f_footer, fill=DISCLAIMER)

    return img.convert("RGB")



def export_pdf(png_path: Path, pdf_path: Path) -> None:
    c = pdf_canvas.Canvas(str(pdf_path), pagesize=A4)
    w, h = A4
    m = 6
    c.drawImage(
        ImageReader(str(png_path)),
        m,
        m,
        width=w - 2 * m,
        height=h - 2 * m,
        preserveAspectRatio=True,
        anchor="c",
    )
    c.save()


def download_icons(timeout: float = 12.0) -> None:
    import ssl

    ICON_DIR.mkdir(parents=True, exist_ok=True)
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    ctx = ssl.create_default_context()

    def fetch(url: str, dest: Path) -> int:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; BotCScriptSheet/1.1)",
                "Accept": "image/*,*/*",
                "Referer": "https://wiki.biligame.com/",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            blob = resp.read()
        dest.write_bytes(blob)
        return len(blob)

    meta = data[0]
    logo = meta.get("logo")
    if logo:
        try:
            print(f"OK logo {fetch(logo, ICON_DIR / '_logo.png')}")
        except Exception as exc:
            print(f"SKIP logo: {exc}")

    for ch in data[1:]:
        cid = ch["id"]
        dest = ICON_DIR / f"{cid}.png"
        urls = list(ch.get("image") or [])
        if cid in ICON_FALLBACKS:
            urls.append(ICON_FALLBACKS[cid])
        ok = False
        for url in urls:
            try:
                print(f"OK {cid} {fetch(url, dest)}")
                ok = True
                break
            except Exception as exc:
                print(f"SKIP {cid} ({type(exc).__name__}): {url[:70]}")
        if not ok:
            print(f"MISSING icon for {cid}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    missing = [
        c["id"]
        for c in json.loads(JSON_PATH.read_text(encoding="utf-8"))[1:]
        if not (ICON_DIR / f"{c['id']}.png").exists()
    ]
    if missing or not (ICON_DIR / "_logo.png").exists():
        print("Downloading missing icons...", missing)
        download_icons()

    print(f"Rendering {PAGE_W}x{PAGE_H} @ {DPI}dpi (official TB layout) ...")
    sheet = render()
    png_path = OUT_DIR / "乡巴佬_剧本单.png"
    hd_path = OUT_DIR / "乡巴佬_剧本单_HD.png"
    pdf_path = OUT_DIR / "乡巴佬_剧本单_A4.pdf"

    sheet.save(png_path, "PNG", dpi=(DPI, DPI), optimize=True)
    sheet.save(hd_path, "PNG", dpi=(DPI, DPI), optimize=True)
    export_pdf(png_path, pdf_path)

    art_png = ARTIFACT_DIR / "xiangbale_script_sheet.png"
    art_pdf = ARTIFACT_DIR / "xiangbale_script_sheet_A4.pdf"
    art_preview = ARTIFACT_DIR / "xiangbale_script_sheet_preview.png"
    sheet.save(art_png, "PNG", dpi=(DPI, DPI), optimize=True)
    export_pdf(png_path, art_pdf)
    preview = sheet.copy()
    preview.thumbnail((1300, 1850), Image.Resampling.LANCZOS)
    preview.save(art_preview, "PNG", optimize=True)

    sheet.crop((0, 0, PAGE_W, 520)).save(ARTIFACT_DIR / "qa_header.png")
    sheet.crop((40, 520, 1260, 1600)).save(ARTIFACT_DIR / "qa_left.png")
    sheet.crop((1260, 520, PAGE_W - 40, 1600)).save(ARTIFACT_DIR / "qa_right.png")
    sheet.crop((40, 2400, PAGE_W - 40, PAGE_H - 40)).save(ARTIFACT_DIR / "qa_bottom.png")

    print("Wrote:", png_path, png_path.stat().st_size)
    print("Wrote:", pdf_path, pdf_path.stat().st_size)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "download-icons":
        download_icons()
    else:
        main()

#!/usr/bin/env python3
"""Night-order sheet for 《乡巴佬》— First Night / Other Nights."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdf_canvas

import generate_script_sheet as base

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "script.json"
ICON_DIR = ROOT / "icons"
OUT_DIR = ROOT / "output"
ARTIFACT_DIR = Path("/opt/cursor/artifacts")

DPI = 300
PAGE_W = int(297 / 25.4 * DPI)  # landscape A4 width
PAGE_H = int(210 / 25.4 * DPI)  # landscape A4 height


def load_orders():
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    meta = data[0]
    first = sorted(
        [c for c in data[1:] if c.get("firstNight")],
        key=lambda c: (c["firstNight"], c["name"]),
    )
    other = sorted(
        [c for c in data[1:] if c.get("otherNight")],
        key=lambda c: (c["otherNight"], c["name"]),
    )
    return meta, first, other


def measure_entry(name: str, reminder: str, fonts: dict, max_w: int, icon: int, line_gap: int) -> int:
    tmp = Image.new("RGB", (8, 8))
    d = ImageDraw.Draw(tmp)
    na, nd = fonts["name"].getmetrics()
    ra, rd = fonts["reminder"].getmetrics()
    lines = base.wrap_text(reminder, fonts["reminder"], max_w, d) if reminder else []
    text_h = (na + nd) + 3
    if lines:
        text_h += len(lines) * (ra + rd) + max(0, len(lines) - 1) * line_gap
    return max(icon, text_h)


def column_height(entries: list[dict], fonts: dict, max_w: int, icon: int, line_gap: int, row_gap: int) -> int:
    return sum(
        measure_entry(e["name"], e["reminder"], fonts, max_w, icon, line_gap) + row_gap for e in entries
    )


def render() -> Image.Image:
    paths = base.ensure_fonts()
    meta, first_chars, other_chars = load_orders()

    first = [
        {
            "name": c["name"],
            "team": c.get("team", "townsfolk"),
            "id": c["id"],
            "reminder": c.get("firstNightReminder") or "",
        }
        for c in first_chars
    ]
    other = [
        {
            "name": c["name"],
            "team": c.get("team", "townsfolk"),
            "id": c["id"],
            "reminder": c.get("otherNightReminder") or "",
        }
        for c in other_chars
    ]

    img = base.make_parchment(PAGE_W, PAGE_H)
    draw = ImageDraw.Draw(img, "RGBA")
    base.draw_scroll_border(draw, PAGE_W, PAGE_H)

    f_title = base.font(paths["title"], 82)
    f_sub = base.font(paths["body"], 20)
    f_col = base.font(paths["title"], 34)
    f_col_en = base.font(paths["title_reg"], 17)
    f_footer = base.font(paths["body"], 15)
    f_idx = base.font(paths["title_reg"], 16)

    script_name = meta.get("name", "乡巴佬")
    author = meta.get("author", "")
    logo_path = ICON_DIR / "_logo.png"
    header_top = 34
    if logo_path.exists():
        logo = Image.open(logo_path).convert("RGBA")
        logo_h = 56
        logo = logo.resize(
            (max(1, int(logo.size[0] * logo_h / logo.size[1])), logo_h),
            Image.Resampling.LANCZOS,
        )
        img.paste(logo, ((PAGE_W - logo.size[0]) // 2, header_top), logo)
        title_y = header_top + logo_h - 2
    else:
        title_y = header_top + 4

    title = f"{script_name} · 夜晚顺序"
    tb = draw.textbbox((0, 0), title, font=f_title)
    tw = tb[2] - tb[0]
    tx = (PAGE_W - tw) // 2
    draw.text((tx + 2, title_y + 2), title, font=f_title, fill=(80, 40, 25, 70))
    draw.text((tx, title_y), title, font=f_title, fill=base.TITLE_RED)

    sub = "非官方自定义剧本 · UNOFFICIAL · NIGHT ORDER"
    if author:
        sub += f" · 作者 {author}"
    sb = draw.textbbox((0, 0), sub, font=f_sub)
    sx = (PAGE_W - (sb[2] - sb[0])) // 2
    sy = title_y + (tb[3] - tb[1]) + 2
    draw.text((sx, sy), sub, font=f_sub, fill=base.DISCLAIMER)

    content_top = sy + 26
    draw.line([(140, content_top), (PAGE_W - 140, content_top)], fill=(110, 80, 50), width=2)
    content_top += 12

    margin_x = 52
    gutter = 36
    footer_h = 42
    col_header_h = 44
    content_bottom = PAGE_H - footer_h
    available_h = content_bottom - content_top - col_header_h - 12
    col_w = (PAGE_W - margin_x * 2 - gutter) // 2

    # Binary-search largest readable type that still fits
    lo, hi = 15, 32
    best = (18, 26, 52, 2, 8)
    while lo <= hi:
        rem = (lo + hi) // 2
        name_sz = rem + 9
        icon = max(46, int(rem * 2.55))
        line_gap = max(1, rem // 9)
        row_gap = max(5, rem // 2)
        fonts = {
            "name": base.font(paths["title_reg"], name_sz),
            "reminder": base.font(paths["body"], rem),
        }
        aw = col_w - icon - 16 - 36  # badge + paddings
        h1 = column_height(first, fonts, aw, icon, line_gap, row_gap)
        h2 = column_height(other, fonts, aw, icon, line_gap, row_gap)
        if max(h1, h2) <= available_h:
            best = (rem, name_sz, icon, line_gap, row_gap)
            lo = rem + 1
        else:
            hi = rem - 1

    rem_sz, name_sz, icon_size, line_gap, row_gap = best
    fonts = {
        "name": base.font(paths["title_reg"], name_sz),
        "reminder": base.font(paths["body"], rem_sz),
    }
    aw = col_w - icon_size - 16 - 36
    used = max(
        column_height(first, fonts, aw, icon_size, line_gap, row_gap),
        column_height(other, fonts, aw, icon_size, line_gap, row_gap),
    )
    spare = available_h - used
    n_slots = max(len(first), len(other), 1)
    if spare > 6:
        row_gap += spare // n_slots
    print(
        f"Night-order type: reminder={rem_sz}px name={name_sz}px icon={icon_size} "
        f"used≈{used}/{available_h} row_gap={row_gap} first={len(first)} other={len(other)}"
    )

    def draw_column(entries: list[dict], x: int, y0: int, header_zh: str, header_en: str, accent: tuple[int, int, int]) -> None:
        band_h = col_header_h
        band = Image.new("RGBA", (col_w, band_h), (*accent, 50))
        img.paste(band, (x, y0), band)
        draw.rectangle([x, y0, x + col_w, y0 + band_h], outline=(*accent, 190), width=2)
        draw.rectangle([x, y0, x + 8, y0 + band_h], fill=(*accent, 235))
        draw.text((x + 16, y0 + 4), header_zh, font=f_col, fill=accent)
        en_x = x + 16 + int(draw.textlength(header_zh, font=f_col)) + 10
        draw.text((en_x, y0 + 14), header_en, font=f_col_en, fill=(*accent, 200))

        y = y0 + band_h + 10
        badge_r = 13
        for idx, e in enumerate(entries, start=1):
            team = e["team"]
            tint = base.TEAM_COLOR.get(team, (80, 80, 80))
            name_fill = base.NAME_COLOR.get(team, base.INK)
            ip = ICON_DIR / f"{e['id']}.png"
            if ip.exists():
                icon = base.tinted_icon(ip, icon_size, tint)
            else:
                icon = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
                ImageDraw.Draw(icon).ellipse(
                    [2, 2, icon_size - 3, icon_size - 3],
                    outline=(*tint, 255),
                    width=3,
                )

            # order badge
            bx, by = x + 4, y + 2
            draw.ellipse([bx, by, bx + badge_r * 2, by + badge_r * 2], fill=(*accent, 225))
            idx_s = str(idx)
            ib = draw.textbbox((0, 0), idx_s, font=f_idx)
            iw, ih = ib[2] - ib[0], ib[3] - ib[1]
            draw.text(
                (bx + badge_r - iw // 2, by + badge_r - ih // 2 - 1),
                idx_s,
                font=f_idx,
                fill=(255, 248, 230),
            )

            icon_x = x + badge_r * 2 + 10
            text_x = icon_x + icon_size + 10
            text_max = x + col_w - text_x - 8

            draw.text((text_x, y), e["name"], font=fonts["name"], fill=name_fill)
            na, nd = fonts["name"].getmetrics()
            name_h = na + nd
            lines = (
                base.wrap_text(e["reminder"], fonts["reminder"], text_max, draw)
                if e["reminder"]
                else []
            )
            ra, rd = fonts["reminder"].getmetrics()
            line_h = ra + rd
            ay = y + name_h + 2
            for i, line in enumerate(lines):
                draw.text(
                    (text_x, ay + i * (line_h + line_gap)),
                    line,
                    font=fonts["reminder"],
                    fill=base.INK,
                )

            text_h = name_h + 2
            if lines:
                text_h += len(lines) * line_h + max(0, len(lines) - 1) * line_gap
            content_h = max(icon_size, text_h, badge_r * 2)
            rh = content_h + row_gap
            icon_y = y + max(0, (content_h - icon_size) // 2)
            img.paste(icon, (icon_x, icon_y), icon)
            sep_y = y + rh - 3
            draw.line([(text_x, sep_y), (x + col_w - 6, sep_y)], fill=(140, 110, 70, 45), width=1)
            y += rh

    left_x = margin_x
    right_x = margin_x + col_w + gutter
    draw_column(first, left_x, content_top, "首个夜晚", "FIRST NIGHT", (48, 88, 138))
    draw_column(other, right_x, content_top, "其他夜晚", "OTHER NIGHTS", (140, 42, 40))

    footer = "Blood on the Clocktower 非官方夜晚顺序单 · 顺序与说书人提示取自剧本 JSON · 仅供同好娱乐"
    fb = draw.textbbox((0, 0), footer, font=f_footer)
    draw.text(((PAGE_W - (fb[2] - fb[0])) // 2, PAGE_H - 32), footer, font=f_footer, fill=base.DISCLAIMER)
    return img.convert("RGB")


def export_pdf(png_path: Path, pdf_path: Path) -> None:
    page = landscape(A4)
    c = pdf_canvas.Canvas(str(pdf_path), pagesize=page)
    w, h = page
    m = 8
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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Rendering night order {PAGE_W}x{PAGE_H} @ {DPI}dpi ...")
    sheet = render()
    png = OUT_DIR / "乡巴佬_夜晚顺序.png"
    hd = OUT_DIR / "乡巴佬_夜晚顺序_HD.png"
    pdf = OUT_DIR / "乡巴佬_夜晚顺序_A4.pdf"

    sheet.save(png, "PNG", dpi=(DPI, DPI), optimize=True)
    sheet.save(hd, "PNG", dpi=(DPI, DPI), optimize=True)
    export_pdf(png, pdf)

    art_png = ARTIFACT_DIR / "xiangbale_night_order.png"
    art_pdf = ARTIFACT_DIR / "xiangbale_night_order_A4.pdf"
    art_preview = ARTIFACT_DIR / "xiangbale_night_order_preview.png"
    sheet.save(art_png, "PNG", dpi=(DPI, DPI), optimize=True)
    export_pdf(png, art_pdf)
    preview = sheet.copy()
    preview.thumbnail((1600, 1140), Image.Resampling.LANCZOS)
    preview.save(art_preview, "PNG", optimize=True)

    sheet.crop((0, 0, PAGE_W, 380)).save(ARTIFACT_DIR / "qa_night_header.png")
    sheet.crop((40, 360, PAGE_W // 2 - 10, PAGE_H - 36)).save(ARTIFACT_DIR / "qa_night_first.png")
    sheet.crop((PAGE_W // 2 + 10, 360, PAGE_W - 40, PAGE_H - 36)).save(ARTIFACT_DIR / "qa_night_other.png")

    print("Wrote:", png, png.stat().st_size)
    print("Wrote:", pdf, pdf.stat().st_size)


if __name__ == "__main__":
    main()

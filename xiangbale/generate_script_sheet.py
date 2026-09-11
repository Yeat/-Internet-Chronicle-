#!/usr/bin/env python3
"""Generate Blood on the Clocktower style custom script sheet for 《乡巴佬》."""

from __future__ import annotations

import json
import random
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
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
PAGE_W = int(210 / 25.4 * DPI)  # 2480
PAGE_H = int(297 / 25.4 * DPI)  # 3508

TEAM_ORDER = ["townsfolk", "outsider", "minion", "demon", "fabled"]
TEAM_LABEL = {
    "townsfolk": "镇民",
    "outsider": "外来者",
    "minion": "爪牙",
    "demon": "恶魔",
    "fabled": "传奇角色",
}
TEAM_LABEL_EN = {
    "townsfolk": "TOWNSFOLK",
    "outsider": "OUTSIDERS",
    "minion": "MINIONS",
    "demon": "DEMONS",
    "fabled": "FABLED",
}
TEAM_COLOR = {
    "townsfolk": (36, 92, 148),
    "outsider": (42, 118, 158),
    "minion": (168, 42, 48),
    "demon": (148, 24, 28),
    "fabled": (158, 112, 28),
}
TEAM_BAR = {
    "townsfolk": (46, 108, 168),
    "outsider": (52, 132, 172),
    "minion": (178, 48, 54),
    "demon": (158, 28, 32),
    "fabled": (186, 138, 42),
}
TEAM_HEADER_BG = {
    "townsfolk": (42, 102, 162, 48),
    "outsider": (52, 132, 172, 48),
    "minion": (178, 48, 54, 48),
    "demon": (158, 28, 32, 48),
    "fabled": (186, 138, 42, 55),
}
NAME_COLOR = {
    "townsfolk": (28, 78, 132),
    "outsider": (30, 100, 140),
    "minion": (148, 32, 38),
    "demon": (128, 18, 22),
    "fabled": (128, 90, 18),
}

INK = (46, 34, 22)
INK_SOFT = (78, 60, 40)
DISCLAIMER = (110, 78, 48)

# Fallback when JSON CDN is dead (猫猫军团)
ICON_FALLBACKS = {
    "maomaojuntuan_juanbing": (
        "https://patchwiki.biligame.com/images/jbzlbwgwjcygf/"
        "d/d9/p2gdfh2y56pwd8jsi3b3zm5h941arzz.png"
    ),
}


def load_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def _download(url: str, dest: Path, timeout: float = 60.0) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        dest.write_bytes(r.read())


def ensure_fonts() -> dict[str, Path]:
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    body = FONT_DIR / "LXGWWenKai.ttf"
    title = FONT_DIR / "NotoSerifCJKsc-Bold.otf"
    title_reg = FONT_DIR / "NotoSerifCJKsc-SemiBold.otf"
    fallback = Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc")

    if not body.exists():
        try:
            print("Downloading LXGW WenKai ...")
            _download(
                "https://github.com/lxgw/LxgwWenKai/releases/download/v1.501/LXGWWenKai-Regular.ttf",
                body,
            )
        except Exception as e:
            print(f"Font download failed ({e}); using system fallback")

    if not title.exists() or not title_reg.exists():
        zip_path = FONT_DIR / "NotoSerifCJKsc.zip"
        try:
            print("Downloading Noto Serif CJK SC ...")
            _download(
                "https://github.com/googlefonts/noto-cjk/releases/download/Serif2.003/09_NotoSerifCJKsc.zip",
                zip_path,
            )
            import zipfile
            with zipfile.ZipFile(zip_path) as zf:
                for member, dest in [
                    ("OTF/SimplifiedChinese/NotoSerifCJKsc-Bold.otf", title),
                    ("OTF/SimplifiedChinese/NotoSerifCJKsc-SemiBold.otf", title_reg),
                ]:
                    if not dest.exists():
                        dest.write_bytes(zf.read(member))
            zip_path.unlink(missing_ok=True)
        except Exception as e:
            print(f"Noto Serif download failed ({e}); using WenKai/system fallback")
            zip_path.unlink(missing_ok=True)

    body_path = body if body.exists() else fallback
    title_path = title if title.exists() else body_path
    title_reg_path = title_reg if title_reg.exists() else body_path
    return {"title": title_path, "title_reg": title_reg_path, "body": body_path}


def fonts(sizes: dict[str, int] | None = None):
    paths = ensure_fonts()
    sizes = sizes or {
        "title": 112,
        "section": 32,
        "section_en": 17,
        "name": 27,
        "ability": 19,
        "meta": 21,
        "disclaimer": 17,
        "footer": 15,
    }
    return {
        "title": load_font(paths["title"], sizes["title"]),
        "section": load_font(paths["title"], sizes["section"]),
        "section_en": load_font(paths["title_reg"], sizes["section_en"]),
        "name": load_font(paths["title_reg"], sizes["name"]),
        "ability": load_font(paths["body"], sizes["ability"]),
        "meta": load_font(paths["body"], sizes["meta"]),
        "disclaimer": load_font(paths["body"], sizes["disclaimer"]),
        "footer": load_font(paths["body"], sizes["footer"]),
        "_sizes": sizes,
        "_paths": paths,
    }


def make_parchment(w: int, h: int) -> Image.Image:
    """Visible parchment texture that stays readable under text."""
    rng = random.Random(42)
    base = Image.new("RGB", (w, h), (228, 208, 170))

    small = Image.new("RGBA", (max(1, w // 3), max(1, h // 3)), (0, 0, 0, 0))
    sd = ImageDraw.Draw(small)
    for _ in range(180):
        cx, cy = rng.randint(0, small.size[0]), rng.randint(0, small.size[1])
        rw, rh = rng.randint(10, 100), rng.randint(8, 70)
        tone = rng.choice(
            [
                (205, 175, 125),
                (185, 145, 95),
                (238, 222, 190),
                (195, 165, 115),
                (170, 135, 90),
                (215, 190, 145),
            ]
        )
        a = rng.randint(22, 50)
        sd.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=(*tone, a))
    blotch = small.resize((w, h), Image.Resampling.LANCZOS)

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for i in range(120):
        a = int(40 * (1 - i / 120))
        od.rectangle([i, i, w - 1 - i, h - 1 - i], outline=(112, 78, 40, a))
    for cx, cy in [(90, 100), (w - 110, 130), (130, h - 120), (w - 100, h - 140)]:
        od.ellipse([cx - 180, cy - 110, cx + 180, cy + 110], fill=(155, 115, 65, 28))

    grain = Image.effect_noise((w, h), 32).convert("L")
    grain_rgb = Image.merge("RGB", (grain, grain, grain))
    base = Image.blend(base, grain_rgb, 0.11)
    base = base.convert("RGBA")
    base = Image.alpha_composite(base, blotch)
    base = Image.alpha_composite(base, overlay)

    line_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(line_layer)
    for y in range(0, h, 5):
        ld.line([(0, y), (w, y)], fill=(140, 110, 70, 14))
    for _ in range(70):
        y = rng.randint(0, h - 1)
        x0 = rng.randint(0, w // 3)
        x1 = rng.randint(2 * w // 3, w)
        ld.line(
            [(x0, y), (x1, y + rng.randint(-2, 2))],
            fill=(125, 90, 50, rng.randint(14, 26)),
            width=1,
        )
    base = Image.alpha_composite(base, line_layer)
    return base.filter(ImageFilter.GaussianBlur(0.3)).convert("RGB")


def circular_icon(path: Path, size: int, ring_rgb: tuple[int, int, int]) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    side = max(im.size)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(im, ((side - im.size[0]) // 2, (side - im.size[1]) // 2), im)
    canvas = canvas.resize((size - 10, size - 10), Image.Resampling.LANCZOS)

    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    mask = Image.new("L", (size - 10, size - 10), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 11, size - 11], fill=255)
    under = Image.new("RGBA", (size - 10, size - 10), (245, 232, 200, 255))
    under.paste(canvas, (0, 0), mask)
    out.paste(under, (5, 5), mask)
    d = ImageDraw.Draw(out)
    d.ellipse([1, 1, size - 2, size - 2], outline=(*ring_rgb, 255), width=5)
    d.ellipse([5, 5, size - 6, size - 6], outline=(255, 245, 220, 200), width=2)
    return out


def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines: list[str] = []
    for para in text.split("\n"):
        if para == "":
            lines.append("")
            continue
        current = ""
        for ch in para:
            trial = current + ch
            if draw.textlength(trial, font=font) <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = ch
        if current:
            lines.append(current)
    return lines if lines else [""]


def measure_ability(ability: str, font, max_width: int, line_gap: int) -> int:
    tmp = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(tmp)
    lines = wrap_text(ability, font, max_width, draw)
    ascent, descent = font.getmetrics()
    line_h = ascent + descent
    return len(lines) * line_h + max(0, len(lines) - 1) * line_gap


def load_script():
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    meta = data[0]
    chars = [c for c in data[1:] if c.get("id") != "_meta"]
    by_team: dict[str, list] = {t: [] for t in TEAM_ORDER}
    for c in chars:
        team = c.get("team", "townsfolk")
        by_team.setdefault(team, []).append(c)
    return meta, by_team


def draw_ornament_line(draw: ImageDraw.ImageDraw, x0: int, x1: int, y: int, color=(140, 100, 55)):
    mid = (x0 + x1) // 2
    draw.line([(x0, y), (mid - 24, y)], fill=color, width=2)
    draw.line([(mid + 24, y), (x1, y)], fill=color, width=2)
    draw.polygon([(mid, y - 6), (mid + 8, y), (mid, y + 6), (mid - 8, y)], fill=color)


def render() -> Image.Image:
    meta, by_team = load_script()
    img = make_parchment(PAGE_W, PAGE_H)
    draw = ImageDraw.Draw(img, "RGBA")

    margin_x = 64
    margin_top = 42
    margin_bottom = 58
    gutter = 32
    col_w = (PAGE_W - margin_x * 2 - gutter) // 2

    # Header
    title = meta.get("name", "乡巴佬")
    author = meta.get("author", "")
    logo_path = ICON_DIR / "_logo.png"
    logo_h = 96
    title_y = margin_top
    if logo_path.exists():
        logo = Image.open(logo_path).convert("RGBA")
        ratio = logo_h / logo.size[1]
        logo = logo.resize((max(1, int(logo.size[0] * ratio)), logo_h), Image.Resampling.LANCZOS)
        img.paste(logo, ((PAGE_W - logo.size[0]) // 2, margin_top), logo)
        title_y = margin_top + logo_h + 2

    # Fit typography / icons to page height
    sizes = {
        "title": 112,
        "section": 32,
        "section_en": 17,
        "name": 27,
        "ability": 19,
        "meta": 21,
        "disclaimer": 17,
        "footer": 15,
    }
    icon_size = 68
    bar_w = 14
    row_pad_y = 5
    section_pad = 8
    ability_line_gap = 1
    header_h = 38

    F = fonts(sizes)
    title_bbox = draw.textbbox((0, 0), title, font=F["title"])
    tw = title_bbox[2] - title_bbox[0]
    title_x = (PAGE_W - tw) // 2
    draw.text((title_x + 3, title_y + 3), title, font=F["title"], fill=(120, 90, 50, 90))
    draw.text((title_x, title_y), title, font=F["title"], fill=(88, 42, 14))

    subtitle = "非官方自定义剧本 · UNOFFICIAL CUSTOM SCRIPT"
    sb = draw.textbbox((0, 0), subtitle, font=F["disclaimer"])
    sx = (PAGE_W - (sb[2] - sb[0])) // 2
    sy = title_y + (title_bbox[3] - title_bbox[1]) + 6
    draw.text((sx, sy), subtitle, font=F["disclaimer"], fill=DISCLAIMER)

    author_line = f"作者 Author：{author}" if author else ""
    if author_line:
        ab = draw.textbbox((0, 0), author_line, font=F["meta"])
        ax = (PAGE_W - (ab[2] - ab[0])) // 2
        ay = sy + 24
        draw.text((ax, ay), author_line, font=F["meta"], fill=INK_SOFT)
        header_bottom = ay + 28
    else:
        header_bottom = sy + 28

    draw_ornament_line(draw, margin_x + 40, PAGE_W - margin_x - 40, header_bottom + 4)
    content_top = header_bottom + 20
    available_h = PAGE_H - content_top - margin_bottom - 20

    left_teams = ["townsfolk"]
    right_teams = ["outsider", "minion", "demon", "fabled"]

    def ability_max_w(isz: int) -> int:
        return col_w - bar_w - 16 - isz - 12

    def section_height(team: str, F_, isz: int, rpad: int) -> int:
        chars = by_team.get(team, [])
        if not chars:
            return 0
        h = header_h
        amw = ability_max_w(isz)
        for c in chars:
            ability_h = measure_ability(c.get("ability", ""), F_["ability"], amw, ability_line_gap)
            name_h = F_["name"].getmetrics()[0] + F_["name"].getmetrics()[1]
            row_h = max(isz, name_h + 2 + ability_h) + rpad
            h += row_h
        return h + section_pad

    # Shrink until both columns fit
    for _ in range(10):
        left_h = sum(section_height(t, F, icon_size, row_pad_y) for t in left_teams)
        right_h = sum(section_height(t, F, icon_size, row_pad_y) for t in right_teams)
        if max(left_h, right_h) <= available_h:
            break
        icon_size = max(50, icon_size - 2)
        sizes["name"] = max(22, sizes["name"] - 1)
        sizes["ability"] = max(16, sizes["ability"] - 1)
        sizes["section"] = max(26, sizes["section"] - 1)
        F = fonts(sizes)
        row_pad_y = max(3, row_pad_y - 1)

    # If spare room, gently grow ability text / padding (prefer readability)
    for _ in range(6):
        trial_sizes = dict(sizes)
        trial_sizes["ability"] = sizes["ability"] + 1
        trial_F = fonts(trial_sizes)
        trial_pad = row_pad_y + 1
        left_h = sum(section_height(t, trial_F, icon_size, trial_pad) for t in left_teams)
        right_h = sum(section_height(t, trial_F, icon_size, trial_pad) for t in right_teams)
        if max(left_h, right_h) <= available_h:
            sizes = trial_sizes
            F = trial_F
            row_pad_y = trial_pad
        else:
            break

    amw = ability_max_w(icon_size)

    def draw_column(teams: list[str], x: int, y_start: int):
        y = y_start
        for team in teams:
            chars = by_team.get(team, [])
            if not chars:
                continue
            color = TEAM_COLOR[team]
            bar = TEAM_BAR[team]
            sec_h = section_height(team, F, icon_size, row_pad_y)

            # Strong vertical camp bar
            bar_img = Image.new("RGBA", (bar_w, sec_h - section_pad), (*bar, 245))
            img.paste(bar_img, (x, y), bar_img)
            # Inner highlight on bar
            ImageDraw.Draw(img).line(
                [(x + 2, y + 2), (x + 2, y + sec_h - section_pad - 3)],
                fill=(255, 245, 220, 90),
                width=2,
            )

            band = Image.new("RGBA", (col_w, header_h), TEAM_HEADER_BG[team])
            img.paste(band, (x, y), band)
            draw.text((x + bar_w + 12, y + 3), TEAM_LABEL[team], font=F["section"], fill=color)
            en_x = x + bar_w + 12 + int(draw.textlength(TEAM_LABEL[team], font=F["section"])) + 10
            draw.text((en_x, y + 12), TEAM_LABEL_EN[team], font=F["section_en"], fill=(*color, 190))
            y += header_h + 2

            for c in chars:
                name = c.get("name", "")
                ability = c.get("ability", "")
                cid = c.get("id", "")
                icon_path = ICON_DIR / f"{cid}.png"
                if icon_path.exists():
                    icon = circular_icon(icon_path, icon_size, bar)
                else:
                    icon = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
                    ImageDraw.Draw(icon).ellipse(
                        [2, 2, icon_size - 3, icon_size - 3],
                        fill=(220, 200, 170, 255),
                        outline=(*bar, 255),
                        width=3,
                    )

                text_x = x + bar_w + 12 + icon_size + 10
                draw.text((text_x, y + 1), name, font=F["name"], fill=NAME_COLOR[team])
                name_h = F["name"].getmetrics()[0] + F["name"].getmetrics()[1]
                lines = wrap_text(ability, F["ability"], amw, draw)
                ay = y + name_h + 1
                ascent, descent = F["ability"].getmetrics()
                line_h = ascent + descent
                for i, line in enumerate(lines):
                    draw.text(
                        (text_x, ay + i * (line_h + ability_line_gap)),
                        line,
                        font=F["ability"],
                        fill=INK,
                    )

                ability_h = len(lines) * line_h + max(0, len(lines) - 1) * ability_line_gap
                row_h = max(icon_size, name_h + 1 + ability_h) + row_pad_y
                icon_y = y + max(0, (row_h - row_pad_y - icon_size) // 2)
                img.paste(icon, (x + bar_w + 10, icon_y), icon)
                sep_y = y + row_h - 2
                draw.line([(text_x, sep_y), (x + col_w - 6, sep_y)], fill=(140, 110, 70, 45), width=1)
                y += row_h
            y += section_pad
        return y

    draw_column(left_teams, margin_x, content_top)
    draw_column(right_teams, margin_x + col_w + gutter, content_top)

    footer = "Blood on the Clocktower 非官方自定义剧本单 · 角色名称与能力原文取自剧本 JSON · 仅供同好娱乐"
    fb = draw.textbbox((0, 0), footer, font=F["footer"])
    fx = (PAGE_W - (fb[2] - fb[0])) // 2
    draw_ornament_line(draw, margin_x + 80, PAGE_W - margin_x - 80, PAGE_H - margin_bottom + 4, (150, 110, 60))
    draw.text((fx, PAGE_H - margin_bottom + 14), footer, font=F["footer"], fill=DISCLAIMER)

    frame = ImageDraw.Draw(img)
    for i, a in enumerate([100, 55, 28]):
        inset = 24 + i * 3
        frame.rectangle([inset, inset, PAGE_W - inset, PAGE_H - inset], outline=(118, 78, 38, a), width=2)

    return img.convert("RGB")


def export_pdf(png_path: Path, pdf_path: Path):
    c = pdf_canvas.Canvas(str(pdf_path), pagesize=A4)
    w, h = A4
    margin = 6
    c.drawImage(
        ImageReader(str(png_path)),
        margin,
        margin,
        width=w - 2 * margin,
        height=h - 2 * margin,
        preserveAspectRatio=True,
        anchor="c",
    )
    c.save()


def download_icons(timeout: float = 12.0) -> None:
    """Fetch each character image URL; skip stuck CDN; apply known fallbacks."""
    import ssl

    ICON_DIR.mkdir(parents=True, exist_ok=True)
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    ctx = ssl.create_default_context()

    def fetch(url: str, dest: Path) -> int:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; BotCScriptSheet/1.0)",
                "Accept": "image/*,*/*",
                "Referer": "https://wiki.biligame.com/",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            blob = r.read()
        dest.write_bytes(blob)
        return len(blob)

    meta = data[0]
    if meta.get("logo"):
        try:
            n = fetch(meta["logo"], ICON_DIR / "_logo.png")
            print(f"OK logo {n}")
        except Exception as e:
            print(f"SKIP logo: {e}")

    for ch in data[1:]:
        cid = ch["id"]
        dest = ICON_DIR / f"{cid}.png"
        urls = list(ch.get("image") or [])
        if cid in ICON_FALLBACKS:
            urls.append(ICON_FALLBACKS[cid])
        ok = False
        for url in urls:
            try:
                n = fetch(url, dest)
                print(f"OK {cid} {n}")
                ok = True
                break
            except Exception as e:
                print(f"SKIP {cid} ({type(e).__name__}): {url[:70]}")
        if not ok:
            print(f"MISSING icon for {cid}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    # Ensure icons exist (re-fetch missing only)
    missing = [
        c["id"]
        for c in json.loads(JSON_PATH.read_text(encoding="utf-8"))[1:]
        if not (ICON_DIR / f"{c['id']}.png").exists()
    ]
    if missing or not (ICON_DIR / "_logo.png").exists():
        print("Downloading missing icons...", missing)
        download_icons()

    print(f"Rendering {PAGE_W}x{PAGE_H} @ {DPI}dpi ...")
    sheet = render()
    png_path = OUT_DIR / "乡巴佬_剧本单.png"
    pdf_path = OUT_DIR / "乡巴佬_剧本单_A4.pdf"
    hd_path = OUT_DIR / "乡巴佬_剧本单_HD.png"

    sheet.save(png_path, "PNG", dpi=(DPI, DPI), optimize=True)
    sheet.save(hd_path, "PNG", dpi=(DPI, DPI), optimize=True)
    export_pdf(png_path, pdf_path)

    art_png = ARTIFACT_DIR / "xiangbale_script_sheet.png"
    art_pdf = ARTIFACT_DIR / "xiangbale_script_sheet_A4.pdf"
    art_preview = ARTIFACT_DIR / "xiangbale_script_sheet_preview.png"
    sheet.save(art_png, "PNG", dpi=(DPI, DPI), optimize=True)
    export_pdf(png_path, art_pdf)
    preview = sheet.copy()
    preview.thumbnail((1400, 2000), Image.Resampling.LANCZOS)
    preview.save(art_preview, "PNG", optimize=True)

    print("Wrote:", png_path, png_path.stat().st_size)
    print("Wrote:", hd_path, hd_path.stat().st_size)
    print("Wrote:", pdf_path, pdf_path.stat().st_size)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "download-icons":
        download_icons()
    else:
        main()

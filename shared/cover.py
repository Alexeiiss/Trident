#!/usr/bin/env python3
"""cover.py - covers and thumbnails that read at feed size, for one post or a whole series.

    python3 cover.py --text "She didn't know" -o cover.png                       # 1080x1920 Reel / TikTok cover
    python3 cover.py --text "He lied for 9 years" --bg frame.jpg -o cover.png
    python3 cover.py --text "The Dacian gold" --bg frame.jpg --parts 3 --label "PART {n}" -o dacians.png
                                                                       # -> dacians_1.png, dacians_2.png, ...
    python3 cover.py --text "AI RAN IT" --size thumb --bg face.jpg -o thumb.png   # 1280x720 YouTube thumbnail
    python3 cover.py ... --json                                         # the checks, machine-readable

  --size reel (1080x1920) | thumb (1280x720) | square (1080x1080) | grid (1080x1350) | WxH
  --position top | center | bottom-safe      --accent "#3DF2C2"      --scrim auto|on|off
  --texts "promise 1|promise 2|promise 3"    a different line per part (with --parts)

Checks it runs and reports:
  * word count - 3 on a YouTube thumbnail, 6 on a TikTok / Reels cover (platforms.json)
  * text inside the safe zone - Reels covers are cropped to 4:5 (1080x1350) in the profile grid, and
    the bottom ~20% / right ~15% of a 9:16 frame sit under the platform's buttons
  * contrast - text against the background behind it, WCAG ratio; under 4.5 a dark scrim is added
    automatically (--scrim auto) and the report says so
  * the text is shrunk until it fits in at most 3 lines, and never below a size readable at feed size
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
except ImportError:
    sys.exit("cover.py needs Pillow:  pip install pillow")
P = json.load(open(os.path.join(HERE, "platforms.json"), encoding="utf-8"))
FONT = os.path.join(HERE, "fonts", "Inter-Black.otf")
FONT_B = os.path.join(HERE, "fonts", "Inter-Bold.otf")
SIZES = {"reel": (1080, 1920), "thumb": (1280, 720), "square": (1080, 1080), "grid": (1080, 1350)}

def hexrgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def lum(c):
    def ch(v):
        v /= 255; return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = c[:3]; return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)

def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True); return (la + 0.05) / (lb + 0.05)

def safe_box(W, H):
    if H > W:  # 9:16: the profile grid shows the middle 1080x1350; buttons cover bottom 20% / right 15%
        top = (H - int(W * 1.25)) // 2
        return (int(W * 0.07), max(int(H * 0.1), top + 40), int(W * 0.85), min(int(H * 0.8), top + int(W * 1.25) - 40))
    return (int(W * 0.06), int(H * 0.08), int(W * 0.94), int(H * 0.92))

def fit(draw, text, box_w, max_lines=3, start=None, minimum=None):
    size = start or int(box_w * 0.16)
    minimum = minimum or max(40, int(box_w * 0.06))
    while size >= minimum:
        f = ImageFont.truetype(FONT, size)
        lines, cur = [], ""
        for w in text.split():
            trial = (cur + " " + w).strip()
            if cur and f.getlength(trial) > box_w:
                lines.append(cur); cur = w
            else: cur = trial
        if cur: lines.append(cur)
        if len(lines) <= max_lines and all(f.getlength(l) <= box_w for l in lines):
            return f, lines
        size -= 4
    f = ImageFont.truetype(FONT, minimum)
    return f, [text]

def make(text, out, size=(1080, 1920), bg=None, label=None, accent="#3DF2C2", position="center", scrim="auto",
         platform=None):
    W, H = size
    if bg and os.path.exists(bg):
        im = ImageOps.fit(Image.open(bg).convert("RGB"), (W, H), Image.LANCZOS)
    else:
        im = Image.new("RGB", (W, H), hexrgb(bg) if bg and bg.startswith("#") else (11, 13, 20))
    x0, y0, x1, y1 = safe_box(W, H)
    d = ImageDraw.Draw(im)
    font, lines = fit(d, text, x1 - x0)
    lh = int(font.size * 1.08)
    block = lh * len(lines)
    if position == "top": ty = y0 + (90 if label else 0)
    elif position == "bottom-safe": ty = y1 - block
    else: ty = (y0 + y1) // 2 - block // 2
    # contrast against what is actually behind the text
    region = im.crop((x0, max(0, ty), x1, min(H, ty + block))).resize((1, 1), Image.BOX).getpixel((0, 0))
    ratio = contrast((255, 255, 255), region)
    scrim_used = scrim == "on" or (scrim == "auto" and ratio < 4.5)
    if scrim_used:
        ov = Image.new("L", (W, H), 0); od = ImageDraw.Draw(ov)
        pad = int(font.size * 0.8)
        od.rectangle([0, max(0, ty - pad), W, min(H, ty + block + pad)], fill=150)
        ov = ov.filter(ImageFilter.GaussianBlur(pad // 2))
        im = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), im, ov)
        d = ImageDraw.Draw(im)
        region = im.crop((x0, max(0, ty), x1, min(H, ty + block))).resize((1, 1), Image.BOX).getpixel((0, 0))
        ratio_after = contrast((255, 255, 255), region)
    else:
        ratio_after = ratio
    acc = hexrgb(accent)
    for i, l in enumerate(lines):
        y = ty + i * lh
        d.text(((x0 + x1) // 2, y), l, font=font, fill=(255, 255, 255), anchor="ma",
               stroke_width=max(3, font.size // 18), stroke_fill=(0, 0, 0))
    if label:
        lf = ImageFont.truetype(FONT_B, max(36, int(font.size * 0.42)))
        lw = d.textlength(label, font=lf)
        ly = ty - int(lf.size * 2.1)
        d.rounded_rectangle([x0, ly, x0 + lw + 44, ly + lf.size + 30], 16, fill=acc)
        d.text((x0 + 22, ly + 12), label, font=lf, fill=(0, 0, 0))
    im.save(out)
    words = len(text.split())
    limit = 3 if (W > H and W >= 1200) else P["tiktok"]["cover_words_max"]
    issues = []
    if words > limit: issues.append(f"{words} words - {limit} is the ceiling at feed size")
    if ratio_after < 4.5: issues.append(f"contrast {ratio_after:.1f}:1 even with the scrim - pick a calmer frame")
    if font.size < int((x1 - x0) * 0.08): issues.append(f"text shrank to {font.size}px to fit - shorten it")
    return {"out": out, "size": f"{W}x{H}", "lines": lines, "font_px": font.size, "words": words,
            "contrast_before": round(ratio, 2), "contrast": round(ratio_after, 2), "scrim": scrim_used,
            "safe_box": [x0, y0, x1, y1], "issues": issues}

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--text", required=True); ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--size", default="reel"); ap.add_argument("--bg")
    ap.add_argument("--label"); ap.add_argument("--parts", type=int); ap.add_argument("--texts")
    ap.add_argument("--accent", default="#3DF2C2")
    ap.add_argument("--position", default="center", choices=["top", "center", "bottom-safe"])
    ap.add_argument("--scrim", default="auto", choices=["auto", "on", "off"])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    size = SIZES.get(a.size) or tuple(int(x) for x in a.size.lower().split("x"))
    jobs = []
    if a.parts:
        texts = a.texts.split("|") if a.texts else [a.text] * a.parts
        if len(texts) != a.parts: ap.error("--texts needs exactly one entry per part")
        base, ext = os.path.splitext(a.out)
        for n in range(1, a.parts + 1):
            jobs.append((texts[n - 1], f"{base}_{n}{ext or '.png'}", (a.label or "PART {n}").format(n=n, total=a.parts)))
    else:
        jobs.append((a.text, a.out, a.label))
    res = [make(t, o, size, a.bg, l, a.accent, a.position, a.scrim) for t, o, l in jobs]
    if a.json: print(json.dumps(res, ensure_ascii=False, indent=1)); return
    for r in res:
        flag = "  scrim added" if r["scrim"] else ""
        print(f"  {r['out']}  {r['size']}  {r['font_px']}px  {len(r['lines'])} line(s)  contrast {r['contrast']}:1{flag}")
        for i in r["issues"]: print(f"    x  {i}")

if __name__ == "__main__":
    main()

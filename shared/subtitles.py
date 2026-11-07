#!/usr/bin/env python3
"""subtitles.py - word-by-word captions for short-form video, as an .ass file (or burnt into the video).

    python3 subtitles.py transcript.json -o captions.ass                  # whisper JSON with word timings: best
    python3 subtitles.py transcript.srt -o captions.ass --style clip      # .srt / .vtt: words spread inside each cue
    python3 subtitles.py transcript.srt --hook "Watch his hand" --hook-until 3 -o captions.ass
    python3 subtitles.py transcript.srt --burn video.mp4 -o video_captioned.mp4
    python3 subtitles.py transcript.srt --size 1920x1080 --words 5 -o captions.ass   # landscape

Styles:
  bold       big white words, the word being spoken lights up (default)
  clip       film-clip pages: white text on a black box, hook text on a white box at the top
  storytime  big white words, current word yellow - over slime / gameplay footage
  minimal    one clean line, no highlight - for history / documentary tone

Everything is kept inside the platform safe zone: nothing in the bottom ~20% (caption, buttons)
or the right ~15% (like / comment column) of a 9:16 frame. Lines that would not fit are split.

Requires ffmpeg with libass only for --burn. Uses the bundled Inter font (fonts/, OFL licence).
"""
import argparse, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from transcript import load as load_cues  # noqa: E402

FONTS = os.path.join(HERE, "fonts")
FONT_NAME = "Inter Black"

STYLES = {  # ASS colours are &HAABBGGRR
 "bold":      {"base": "&H00FFFFFF", "hi": "&H00C2F23D", "outline": 7, "box": False, "size": 78, "hook_box": False},
 "clip":      {"base": "&H00FFFFFF", "hi": "&H00FFFFFF", "outline": 0, "box": True,  "size": 64, "hook_box": True},
 "storytime": {"base": "&H00FFFFFF", "hi": "&H0000D7FF", "outline": 8, "box": False, "size": 84, "hook_box": False},
 "minimal":   {"base": "&H00FFFFFF", "hi": "&H00FFFFFF", "outline": 4, "box": False, "size": 58, "hook_box": False},
}

def ts(t):
    t = max(0.0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def esc(s): return s.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", " ")

# ---------------------------------------------------------------- word timings
def words_from_whisper(path):
    d = json.load(open(path, encoding="utf-8"))
    segs = d.get("segments", []) if isinstance(d, dict) else d
    out = []
    for s in segs:
        ws = s.get("words") or []
        if ws:
            for w in ws:
                txt = (w.get("word") or w.get("text") or "").strip()
                if txt: out.append((float(w["start"]), float(w["end"]), txt))
        elif s.get("text"):
            out += spread(float(s["start"]), float(s["end"]), s["text"])
    return out

def spread(a, b, text):
    """Words of one cue spread over its span, weighted by length (long words take longer to say)."""
    ws = text.split()
    if not ws: return []
    wt = [len(w) + 2 for w in ws]; tot = sum(wt); out, acc = [], 0.0
    for w, k in zip(ws, wt):
        s = a + (b - a) * acc / tot; acc += k
        out.append((s, a + (b - a) * acc / tot, w))
    return out

def load_words(path):
    if path.lower().endswith(".json"):
        try:
            w = words_from_whisper(path)
            if w: return w
        except (KeyError, ValueError, TypeError):
            pass
    out = []
    for a, b, t in load_cues(path): out += spread(a, b, t)
    return out

# ---------------------------------------------------------------- layout
def text_width(s, size):
    try:
        from PIL import ImageFont
        return ImageFont.truetype(os.path.join(FONTS, "Inter-Black.otf"), size).getlength(s)
    except Exception:  # Pillow missing: Inter Black averages ~0.62 em per character
        return len(s) * size * 0.62

def wrap(text, size, max_px):
    """Break text into lines that fit max_px, joined with the ASS line break."""
    lines, cur = [], ""
    for w in text.split():
        trial = (cur + " " + w).strip()
        if cur and text_width(trial, size) > max_px:
            lines.append(cur); cur = w
        else:
            cur = trial
    if cur: lines.append(cur)
    return "\\N".join(esc(l) for l in lines)

def group(words, max_words=3, max_px=820, size=78):
    groups, cur = [], []
    for i, (a, b, w) in enumerate(words):
        trial = " ".join(words[j][2] for j in cur + [i])
        gap = cur and a - words[cur[-1]][1] > 0.6          # a pause starts a new group
        if cur and (len(cur) >= max_words or text_width(trial, size) > max_px or gap):
            groups.append(cur); cur = []
        cur.append(i)
        if re.search(r"[.!?…:;]$", w): groups.append(cur); cur = []
    if cur: groups.append(cur)
    return groups

def build_ass(words, size=(1080, 1920), style="bold", hook=None, hook_until=3.0, max_words=None,
              label=None, end=None):
    W, H = size
    st = dict(STYLES[style])
    vertical = H > W
    if not vertical: st["size"] = int(st["size"] * 0.8)
    max_words = max_words or (3 if vertical else 6)
    safe_l, safe_r = int(W * 0.074), int(W * (0.15 if vertical else 0.074))
    max_px = W - safe_l - safe_r - 40
    margin_v = int(H * 0.24) if vertical else int(H * 0.08)   # baseline above the bottom 20%
    hook_v = int(H * 0.13) if vertical else int(H * 0.06)
    border = 3 if st["box"] else 1
    outline = 14 if st["box"] else st["outline"]
    back = "&H00000000"
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{FONT_NAME},{st['size']},{st['base']},{st['base']},&H00000000,{back},0,0,0,0,100,100,0,0,{border},{outline},0,2,{safe_l},{safe_r},{margin_v},1
Style: Hook,{FONT_NAME},{int(st['size'] * 0.9)},{'&H00000000' if st['hook_box'] else '&H00FFFFFF'},&H00FFFFFF,{'&H00FFFFFF' if st['hook_box'] else '&H00000000'},&H00000000,0,0,0,0,100,100,0,0,{3 if st['hook_box'] else 1},{16 if st['hook_box'] else 7},0,8,{safe_l},{safe_r},{hook_v},1
Style: Label,Inter Bold,{int(st['size'] * 0.55)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,4,0,7,{safe_l},{safe_r},{hook_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    if hook:
        hs = int(st["size"] * 0.9)
        ev.append(f"Dialogue: 1,{ts(0)},{ts(hook_until)},Hook,,0,0,0,,{{\\fad(0,200)}}{wrap(hook, hs, max_px - 40)}")
    if label:
        ev.append(f"Dialogue: 1,{ts(0)},{ts(end or (words[-1][1] if words else 5))},Label,,0,0,{hook_v - 90 if hook else hook_v},,{esc(label)}")
    gs = group(words, max_words, max_px, st["size"])
    for gi, g in enumerate(gs):
        g_end = words[g[-1]][1] + 0.15
        if gi + 1 < len(gs): g_end = min(g_end + 0.25, words[gs[gi + 1][0]][0])
        for k, j in enumerate(g):
            a = words[j][0] if k else words[g[0]][0]
            b = words[g[k + 1]][0] if k + 1 < len(g) else g_end
            if b <= a: continue
            parts = []
            for jj in g:
                w = esc(words[jj][2])
                parts.append(f"{{\\c{st['hi']}}}{w}{{\\c{st['base']}}}" if (jj == j and st["hi"] != st["base"]) else w)
            pop = "{\\fscx108\\fscy108\\t(0,90,\\fscx100\\fscy100)}" if k == 0 and style != "minimal" else ""
            ev.append(f"Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{pop}{' '.join(parts)}")
    return head + "\n".join(ev) + "\n"

def burn(video, ass_path, out, extra_vf=None):
    fd = FONTS.replace("\\", "/").replace(":", "\\:")
    ap = os.path.abspath(ass_path).replace("\\", "/").replace(":", "\\:")
    vf = (extra_vf + "," if extra_vf else "") + f"ass='{ap}':fontsdir='{fd}'"
    tmp = out + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-vf", vf, "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, out)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcript", help=".json (whisper, word timings), .srt or .vtt")
    ap.add_argument("-o", "--out", required=True, help="captions.ass, or the output .mp4 with --burn")
    ap.add_argument("--style", default="bold", choices=list(STYLES))
    ap.add_argument("--size", default="1080x1920")
    ap.add_argument("--words", type=int, help="max words on screen at once (default 3 vertical, 6 landscape)")
    ap.add_argument("--hook", help="on-screen hook text at the top")
    ap.add_argument("--hook-until", type=float, default=3.0)
    ap.add_argument("--label", help='small label top-left, e.g. "PART 2"')
    ap.add_argument("--offset", type=float, default=0.0, help="shift every caption by N seconds")
    ap.add_argument("--burn", metavar="VIDEO", help="burn the captions into this video")
    a = ap.parse_args()
    if not os.path.exists(a.transcript): ap.error(f"no such file: {a.transcript}")
    W, H = (int(x) for x in a.size.lower().split("x"))
    words = [(s + a.offset, e + a.offset, w) for s, e, w in load_words(a.transcript)]
    if not words: print("no words found in the transcript"); sys.exit(1)
    ass = build_ass(words, (W, H), a.style, a.hook, a.hook_until, a.words, a.label)
    if a.burn:
        tmp = a.out + ".ass"
        open(tmp, "w", encoding="utf-8").write(ass)
        burn(a.burn, tmp, a.out)
        print(f"{a.out}  ({len(words)} words, style {a.style})")
    else:
        open(a.out, "w", encoding="utf-8").write(ass)
        print(f"{a.out}  ({len(words)} words, style {a.style}, {W}x{H})")

if __name__ == "__main__":
    main()

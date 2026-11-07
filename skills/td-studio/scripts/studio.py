#!/usr/bin/env python3
"""studio.py - a CapCut-style editor on the command line. Every operation reads a video and writes a
new one, so steps chain:  trim -> reframe -> color -> text -> music -> export.

    python3 studio.py <operation> [args]        python3 studio.py <operation> --help
    python3 studio.py ops                       list every operation

EDIT        trim, cut, split, join (+ transitions), freeze, reverse
SPEED       speed (incl. smooth slow-motion), ramp (speed curve)
FRAME       reframe (9:16 / 1:1 / 16:9 with crop, fit or blurred background), zoom (punch-in,
            slow zoom in/out), transform (flip, mirror, rotate), stabilize
LOOK        color (presets, brightness/contrast/saturation/temperature, .cube LUT, vignette),
            blur (censor a region), fade (in/out to black)
LAYERS      text (animated titles), captions (word-by-word from a transcript), overlay
            (picture-in-picture, stickers, logos, green-screen overlay), chroma (replace a
            green-screen background)
AUDIO       audio (volume, denoise, normalize, voice effects, mute, extract, replace),
            music (bed with auto-ducking under speech), sfx (sounds at given times),
            silence (auto-cut silent parts), beats (find the beats in a track),
            beatcut (cut clips to the beat of a track)
DELIVER     export (TikTok / Reels / Shorts / YouTube preset), frame (grab a still for a cover)

Needs ffmpeg 5+ (with libass for text/captions). Python 3 standard library only.
"""
import argparse, json, math, os, re, shutil, subprocess, sys, tempfile, wave, array

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
FONTS = os.path.join(HERE, "fonts")
ENC_V = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p"]
ENC_A = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
ASPECTS = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080), "4:5": (1080, 1350)}

# ------------------------------------------------------------------ helpers
def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit("ffmpeg failed:\n" + (p.stderr or "").strip()[-1500:])
    return p

def probe(path):
    if not os.path.exists(path): sys.exit(f"no such file: {path}")
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration:stream=codec_type,width,height,r_frame_rate,sample_rate",
                        "-of", "json", path], capture_output=True, text=True)
    d = json.loads(p.stdout or "{}")
    v = next((s for s in d.get("streams", []) if s["codec_type"] == "video"), None)
    a = next((s for s in d.get("streams", []) if s["codec_type"] == "audio"), None)
    fps = 30.0
    if v and v.get("r_frame_rate", "0/0") != "0/0":
        n, dd = v["r_frame_rate"].split("/"); fps = float(n) / float(dd or 1)
    return {"duration": float(d.get("format", {}).get("duration", 0) or 0), "w": v["width"] if v else 0,
            "h": v["height"] if v else 0, "fps": round(fps, 3), "audio": a is not None, "video": v is not None}

def out_ok(tmp, out):
    os.replace(tmp, out)
    i = probe(out)
    print(json.dumps({"out": out, "seconds": round(i["duration"], 2), "size": f"{i['w']}x{i['h']}"}, ensure_ascii=False))

def ffmpeg(inputs, out, vf=None, af=None, fc=None, maps=None, extra=None, video=True, audio=True):
    tmp = out + ".tmp" + os.path.splitext(out)[1]
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for i in inputs: cmd += i if isinstance(i, list) else ["-i", i]
    if fc: cmd += ["-filter_complex", fc]
    if vf: cmd += ["-vf", vf]
    if af: cmd += ["-af", af]
    for m in maps or []: cmd += ["-map", m]
    if video: cmd += ENC_V
    if audio: cmd += ENC_A
    cmd += (extra or []) + ["-movflags", "+faststart", tmp]
    run(cmd); out_ok(tmp, out)

def with_audio(path, tmpdir):
    """Many filters need an audio stream: give silent clips a silent track."""
    i = probe(path)
    if i["audio"]: return path
    q = os.path.join(tmpdir, "a_" + os.path.basename(path))
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
         "-shortest", "-c:v", "copy", "-c:a", "aac", q])
    return q

def secs(s):
    s = str(s).strip()
    if ":" in s:
        p = [float(x) for x in s.split(":")]
        return p[-1] + 60 * p[-2] + (3600 * p[-3] if len(p) > 2 else 0)
    return float(s)

def ranges(s):
    out = []
    for part in (s or "").split(","):
        if "-" in part.strip()[1:]:
            a, b = re.split(r"(?<=\d)-", part.strip(), 1)
            out.append((secs(a), secs(b)))
    return out

def atempo_chain(f):
    parts = []
    while f > 2.0: parts.append("atempo=2.0"); f /= 2.0
    while f < 0.5: parts.append("atempo=0.5"); f /= 0.5
    parts.append(f"atempo={f:.4f}")
    return ",".join(parts)

def esc_path(p): return os.path.abspath(p).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")

def ass_header(W, H):
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
"""

def ass_color(hexc, alpha=0):
    h = hexc.lstrip("#"); r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H{alpha:02X}{b}{g}{r}".upper()

# ------------------------------------------------------------------ EDIT
def op_trim(a):
    ffmpeg([["-ss", str(secs(a.start)), "-to", str(secs(a.end)), "-i", a.input]], a.output)

def keep_from_remove(dur, rem):
    keep, t = [], 0.0
    for s, e in sorted(rem):
        if s > t: keep.append((t, s))
        t = max(t, e)
    if t < dur: keep.append((t, dur))
    return [(s, e) for s, e in keep if e - s > 0.04]

def concat_segments(src, segs, out, tmpdir, has_audio=True):
    parts, labels = [], ""
    for i, (s, e) in enumerate(segs):
        parts.append(f"[0:v]trim={s:.3f}:{e:.3f},setpts=PTS-STARTPTS[v{i}]")
        parts.append(f"[0:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS[a{i}]")
        labels += f"[v{i}][a{i}]"
    fc = ";".join(parts) + f";{labels}concat=n={len(segs)}:v=1:a=1[v][a]"
    ffmpeg([src], out, fc=fc, maps=["[v]", "[a]"])

def op_cut(a):
    tmpd = tempfile.mkdtemp(); src = with_audio(a.input, tmpd)
    dur = probe(src)["duration"]
    if a.edl:
        d = json.load(open(a.edl, encoding="utf-8"))
        rem = [(c["start"], c["end"]) for c in d.get("cuts", d if isinstance(d, list) else [])]
        keep = keep_from_remove(dur, rem)
    elif a.keep: keep = ranges(a.keep)
    elif a.remove: keep = keep_from_remove(dur, ranges(a.remove))
    else: sys.exit("give --remove, --keep or --edl")
    if not keep: sys.exit("nothing left to keep")
    concat_segments(src, keep, a.output, tmpd)

def op_split(a):
    dur = probe(a.input)["duration"]
    pts = [0.0] + sorted(secs(x) for x in a.at.split(",")) + [dur]
    base, ext = os.path.splitext(a.output)
    for i in range(len(pts) - 1):
        ffmpeg([["-ss", f"{pts[i]:.3f}", "-to", f"{pts[i + 1]:.3f}", "-i", a.input]], f"{base}_{i + 1}{ext or '.mp4'}")

def norm_clip(path, W, H, fps, mode, tmpdir, idx):
    """Same size, fps, pixel format and audio layout - required before joining or crossfading."""
    q = os.path.join(tmpdir, f"n{idx}.mp4")
    src = with_audio(path, tmpdir)
    vf = reframe_filter(W, H, mode)
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-filter_complex",
         f"[0:v]{vf},fps={fps},format=yuv420p[v];[0:a]aformat=sample_rates=48000:channel_layouts=stereo[a]",
         "-map", "[v]", "-map", "[a]", *ENC_V, *ENC_A, q])
    return q

TRANSITIONS = ["fade", "fadeblack", "fadewhite", "dissolve", "wipeleft", "wiperight", "wipeup", "wipedown", "slideleft",
               "slideright", "slideup", "slidedown", "circleopen", "circleclose", "radial", "smoothleft", "smoothright",
               "zoomin", "pixelize", "hblur", "distance", "squeezeh", "squeezev", "diagtl", "hlslice"]

def op_join(a):
    tmpd = tempfile.mkdtemp()
    first = probe(a.inputs[0])
    W, H = ASPECTS.get(a.aspect) if a.aspect else (first["w"] - first["w"] % 2, first["h"] - first["h"] % 2)
    clips = [norm_clip(p, W, H, a.fps, a.mode, tmpd, i) for i, p in enumerate(a.inputs)]
    durs = [probe(c)["duration"] for c in clips]
    n = len(clips)
    if a.transition == "none" or n == 1:
        labels = "".join(f"[{i}:v][{i}:a]" for i in range(n))
        ffmpeg(clips, a.output, fc=f"{labels}concat=n={n}:v=1:a=1[v][a]", maps=["[v]", "[a]"]); return
    td = min(a.duration, min(durs) / 2 - 0.05)
    parts, off, vlast, alast = [], 0.0, "[0:v]", "[0:a]"
    for i in range(1, n):
        off += durs[i - 1] - td
        tr = a.transition if a.transition != "mix" else TRANSITIONS[i % len(TRANSITIONS)]
        parts.append(f"{vlast}[{i}:v]xfade=transition={tr}:duration={td:.3f}:offset={off:.3f}[v{i}]")
        parts.append(f"{alast}[{i}:a]acrossfade=d={td:.3f}[a{i}]")
        vlast, alast = f"[v{i}]", f"[a{i}]"
    ffmpeg(clips, a.output, fc=";".join(parts), maps=[vlast, alast])

def op_freeze(a):
    tmpd = tempfile.mkdtemp(); src = with_audio(a.input, tmpd)
    t, d = secs(a.at), a.duration
    fc = (f"[0:v]split=3[x][y][z];[x]trim=0:{t},setpts=PTS-STARTPTS[v1];"
          f"[y]trim={t}:{t + 0.05},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={d},trim=0:{d}[v2];"
          f"[z]trim={t},setpts=PTS-STARTPTS[v3];"
          f"[0:a]asplit=2[p][q];[p]atrim=0:{t},asetpts=PTS-STARTPTS[a1];aevalsrc=0:s=48000:c=stereo:d={d}[a2];"
          f"[q]atrim={t},asetpts=PTS-STARTPTS[a3];[a1]aformat=channel_layouts=stereo:sample_rates=48000[b1];"
          f"[a3]aformat=channel_layouts=stereo:sample_rates=48000[b3];"
          f"[v1][b1][v2][a2][v3][b3]concat=n=3:v=1:a=1[v][a]")
    ffmpeg([src], a.output, fc=fc, maps=["[v]", "[a]"])

def op_reverse(a):
    i = probe(a.input)
    if i["duration"] > 90: sys.exit("reverse holds the whole clip in memory - trim it under 90 s first")
    tmpd = tempfile.mkdtemp(); src = with_audio(a.input, tmpd)
    ffmpeg([src], a.output, vf="reverse", af="areverse")

# ------------------------------------------------------------------ SPEED
def op_speed(a):
    f = a.factor
    if not 0.1 <= f <= 8: sys.exit("--factor must be between 0.1 and 8")
    tmpd = tempfile.mkdtemp(); src = with_audio(a.input, tmpd)
    fps = probe(src)["fps"] or 30
    vf = f"setpts=PTS/{f}"
    if a.smooth and f < 1: vf += f",minterpolate=fps={max(30, round(fps))}:mi_mode=mci:mc_mode=aobmc:vsbmc=1"
    af = "anull" if a.mute else atempo_chain(f)
    ffmpeg([src], a.output, vf=vf, af=af if not a.mute else "volume=0")

def op_ramp(a):
    """Speed curve as steps: --points "0:1,2:0.4,3.5:2,5:1" means from 0 s at 1x, from 2 s at 0.4x..."""
    tmpd = tempfile.mkdtemp(); src = with_audio(a.input, tmpd)
    dur = probe(src)["duration"]
    pts = sorted((secs(t), float(f)) for t, f in (p.split(":") for p in a.points.split(",")))
    segs = []
    for i, (t, f) in enumerate(pts):
        e = pts[i + 1][0] if i + 1 < len(pts) else dur
        if e > t: segs.append((t, min(e, dur), f))
    parts, labels = [], ""
    for i, (s, e, f) in enumerate(segs):
        parts.append(f"[0:v]trim={s:.3f}:{e:.3f},setpts=(PTS-STARTPTS)/{f}[v{i}]")
        parts.append(f"[0:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS,{atempo_chain(f)}[a{i}]")
        labels += f"[v{i}][a{i}]"
    ffmpeg([src], a.output, fc=";".join(parts) + f";{labels}concat=n={len(segs)}:v=1:a=1[v][a]", maps=["[v]", "[a]"])

# ------------------------------------------------------------------ FRAME
def reframe_filter(W, H, mode, focus=0.5):
    if mode == "crop":
        return (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H}:(iw-{W})*{focus}:(ih-{H})/2,setsar=1")
    if mode == "fit":
        return f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1"
    # blur: the CapCut "canvas blur" - the clip fitted, over a blurred, zoomed copy of itself
    return (f"split=2[bgs][fgs];[bgs]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"gblur=sigma=40,eq=brightness=-0.06[bgb];[fgs]scale={W}:{H}:force_original_aspect_ratio=decrease[fgf];"
            f"[bgb][fgf]overlay=(W-w)/2:(H-h)/2,setsar=1")

def op_reframe(a):
    W, H = ASPECTS[a.aspect]
    ffmpeg([a.input], a.output, fc=f"[0:v]{reframe_filter(W, H, a.mode, a.focus)}[v]", maps=["[v]", "0:a?"])

def op_zoom(a):
    i = probe(a.input); W, H, fps = i["w"] - i["w"] % 2, i["h"] - i["h"] % 2, i["fps"] or 30
    D = i["duration"]
    if a.mode == "in": z = f"1+{a.amount}*it/{D:.3f}"
    elif a.mode == "out": z = f"1+{a.amount}*(1-it/{D:.3f})"
    else:
        hits = [secs(x) for x in (a.at or "0").split(",")]
        terms = "+".join(f"{a.amount}*if(between(it,{t:.3f},{t + 0.35:.3f}),1-(it-{t:.3f})/0.35,0)" for t in hits)
        z = f"1+{terms}"
    vf = f"zoompan=z='{z}':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={fps}"
    ffmpeg([a.input], a.output, fc=f"[0:v]{vf}[v]", maps=["[v]", "0:a?"])

def op_transform(a):
    f = []
    if a.hflip or a.mirror: f.append("hflip")
    if a.vflip: f.append("vflip")
    if a.rotate == 90: f.append("transpose=1")
    elif a.rotate == 180: f.append("transpose=1,transpose=1")
    elif a.rotate == 270: f.append("transpose=2")
    if a.mirror == "split":  # left half mirrored onto the right - the CapCut "mirror" effect
        f = ["split[l][r];[r]hflip[rf];[l]crop=iw/2:ih:0:0[lc];[rf]crop=iw/2:ih:iw/2:0[rc];[lc][rc]hstack"]
    if not f: sys.exit("nothing to do: --hflip, --vflip, --rotate or --mirror")
    ffmpeg([a.input], a.output, fc=f"[0:v]{','.join(f)}[v]", maps=["[v]", "0:a?"])

def op_stabilize(a):
    tmpd = tempfile.mkdtemp(); trf = os.path.join(tmpd, "t.trf")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", a.input, "-vf", f"vidstabdetect=shakiness={a.shakiness}:result={trf}", "-f", "null", "-"])
    ffmpeg([a.input], a.output, fc=f"[0:v]vidstabtransform=input={trf}:smoothing={a.smoothing}:zoom=2,unsharp=5:5:0.8:3:3:0.4[v]",
           maps=["[v]", "0:a?"])

# ------------------------------------------------------------------ LOOK
PRESETS = {
 "vivid": "eq=saturation=1.35:contrast=1.08",
 "warm": "colorbalance=rs=0.08:gs=0.02:bs=-0.08:rm=0.05:bm=-0.05,eq=saturation=1.1",
 "cool": "colorbalance=rs=-0.06:bs=0.08:rm=-0.04:bm=0.06",
 "bw": "hue=s=0,eq=contrast=1.15",
 "vintage": "curves=preset=vintage,eq=saturation=0.85",
 "cinematic": "colorbalance=rs=-0.05:bs=0.07:rh=0.07:bh=-0.05,eq=contrast=1.1:saturation=0.9,vignette=PI/5",
 "teal-orange": "colorbalance=rs=-0.1:gs=0.0:bs=0.12:rh=0.12:gh=0.02:bh=-0.12,eq=saturation=1.15",
 "fade": "curves=all='0/0.08 1/0.92',eq=saturation=0.85",
 "dramatic": "eq=contrast=1.3:saturation=0.8:brightness=-0.03,vignette=PI/4",
 "night": "colorbalance=bs=0.15:bm=0.1,eq=brightness=-0.08:saturation=0.7",
}
def op_color(a):
    f = []
    if a.preset: f.append(PRESETS[a.preset])
    if any(v is not None for v in (a.brightness, a.contrast, a.saturation)):
        f.append("eq=" + ":".join(f"{k}={v}" for k, v in (("brightness", a.brightness), ("contrast", a.contrast),
                                                        ("saturation", a.saturation)) if v is not None))
    if a.temperature: f.append(f"colortemperature=temperature={a.temperature}")
    if a.lut: f.append(f"lut3d=file='{esc_path(a.lut)}'")
    if a.vignette: f.append("vignette=PI/4")
    if a.sharpen: f.append("unsharp=5:5:0.9")
    if a.grain: f.append("noise=alls=12:allf=t")
    if not f: sys.exit("nothing to do: --preset, --brightness/--contrast/--saturation, --temperature, --lut ...")
    ffmpeg([a.input], a.output, fc=f"[0:v]{','.join(f)}[v]", maps=["[v]", "0:a?"])

def op_blur(a):
    x, y, w, h = (int(v) for v in a.region.split(","))
    en = f":enable='between(t,{secs(a.start)},{secs(a.end)})'" if a.start is not None else ""
    eff = f"gblur=sigma={a.strength}" if a.style == "blur" else f"scale=iw/{a.strength}:ih/{a.strength},scale=iw*{a.strength}:ih*{a.strength}:flags=neighbor"
    fc = f"[0:v]split[m][c];[c]crop={w}:{h}:{x}:{y},{eff}[b];[m][b]overlay={x}:{y}{en}[v]"
    ffmpeg([a.input], a.output, fc=fc, maps=["[v]", "0:a?"])

def op_fade(a):
    tmpd = tempfile.mkdtemp(); src = with_audio(a.input, tmpd)
    D = probe(src)["duration"]; col = a.color
    vf, af = [], []
    if a.fade_in: vf.append(f"fade=t=in:st=0:d={a.fade_in}:color={col}"); af.append(f"afade=t=in:st=0:d={a.fade_in}")
    if a.fade_out:
        vf.append(f"fade=t=out:st={D - a.fade_out:.3f}:d={a.fade_out}:color={col}")
        af.append(f"afade=t=out:st={D - a.fade_out:.3f}:d={a.fade_out}")
    ffmpeg([src], a.output, vf=",".join(vf) or "null", af=",".join(af) or "anull")

# ------------------------------------------------------------------ LAYERS
ANIMS = {"pop": "{\\fscx60\\fscy60\\t(0,160,\\fscx108\\fscy108)\\t(160,260,\\fscx100\\fscy100)}",
         "fade": "{\\fad(250,250)}", "slide": "{\\move(%d,%d,%d,%d,0,250)\\fad(0,200)}", "none": ""}

def op_text(a):
    i = probe(a.input); W, H = i["w"], i["h"]
    s, e = secs(a.start), secs(a.end) if a.end else i["duration"]
    al = {"top": 8, "center": 5, "bottom": 2}[a.pos]
    mv = {"top": int(H * 0.13), "center": 0, "bottom": int(H * 0.24)}[a.pos]
    size = a.size or int(W * 0.075)
    box = 3 if a.box else 1
    outline = 16 if a.box else max(4, size // 14)
    style = (f"Style: T,Inter Black,{size},{ass_color(a.color)},&H00FFFFFF,{ass_color(a.box_color if a.box else '#000000')},"
             f"&H00000000,0,0,0,0,100,100,0,0,{box},{outline},0,{al},{int(W * 0.074)},{int(W * 0.15)},{mv},1\n")
    anim = ANIMS[a.anim]
    if a.anim == "slide":
        x = W // 2; y = {8: mv + size, 5: H // 2, 2: H - mv}[al]
        anim = anim % (x - W, y, x, y) + f"{{\\an{al}}}"
    ts = lambda t: f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"
    txt = a.text.replace("\\n", "\\N").replace("{", "(").replace("}", ")")
    ass = ass_header(W, H) + style + "\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n" + \
          f"Dialogue: 0,{ts(s)},{ts(e)},T,,0,0,0,,{anim}{txt}\n"
    tmpd = tempfile.mkdtemp(); p = os.path.join(tmpd, "t.ass"); open(p, "w", encoding="utf-8").write(ass)
    ffmpeg([a.input], a.output, fc=f"[0:v]ass='{esc_path(p)}':fontsdir='{esc_path(FONTS)}'[v]", maps=["[v]", "0:a?"])

def op_captions(a):
    import subtitles as SUB
    i = probe(a.input)
    words = SUB.load_words(a.transcript)
    ass = SUB.build_ass(words, (i["w"], i["h"]), a.style, a.hook, a.hook_until, a.words, a.label)
    tmpd = tempfile.mkdtemp(); p = os.path.join(tmpd, "c.ass"); open(p, "w", encoding="utf-8").write(ass)
    ffmpeg([a.input], a.output, fc=f"[0:v]ass='{esc_path(p)}':fontsdir='{esc_path(FONTS)}'[v]", maps=["[v]", "0:a?"])

POS = {"top-left": ("40", "40"), "top-right": ("max(0,W-w-40)", "40"), "bottom-left": ("40", "max(0,H-h-H*0.22)"),
       "bottom-right": ("max(0,W-w-W*0.16)", "max(0,H-h-H*0.22)"), "center": ("(W-w)/2", "(H-h)/2"),
       "top": ("(W-w)/2", "H*0.12"), "bottom": ("(W-w)/2", "max(0,H-h-H*0.22)")}

def op_overlay(a):
    i = probe(a.input); W = i["w"]
    sc = f"scale={int(W * a.scale)}:-2"
    is_img = re.search(r"\.(png|jpe?g|webp|gif)$", a.layer, re.I) is not None
    lay = ["-loop", "1", "-i", a.layer] if is_img and not a.layer.lower().endswith(".gif") else (["-ignore_loop", "0", "-i", a.layer] if is_img else ["-stream_loop", "-1", "-i", a.layer])
    chain = sc
    if a.key: chain += f",chromakey={a.key}:{a.similarity}:0.08"
    if a.round: chain += f",format=rgba,geq=lum='p(X,Y)':a='if(gt(hypot(X-W/2,Y-H/2),min(W,H)/2),0,255)'"
    if a.opacity < 1: chain += f",format=rgba,colorchannelmixer=aa={a.opacity}"
    x, y = POS[a.pos] if a.pos in POS else (a.pos.split(",") + ["0"])[:2]
    en = ""
    if a.start is not None: en = f":enable='between(t,{secs(a.start)},{secs(a.end) if a.end else 1e9})'"
    fc = f"[1:v]{chain}[ov];[0:v][ov]overlay=x='{x}':y='{y}':shortest=0:eof_action=pass{en}[v]"
    tmpd = tempfile.mkdtemp(); src = with_audio(a.input, tmpd)
    ffmpeg([src, lay], a.output, fc=fc, maps=["[v]", "0:a"], extra=["-t", f"{i['duration']:.3f}"])

def op_chroma(a):
    i = probe(a.input); W, H = i["w"] - i["w"] % 2, i["h"] - i["h"] % 2
    is_img = re.search(r"\.(png|jpe?g|webp)$", a.background, re.I) is not None
    bg = ["-loop", "1", "-i", a.background] if is_img else ["-stream_loop", "-1", "-i", a.background]
    fc = (f"[1:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}[bg];"
          f"[0:v]chromakey={a.color}:{a.similarity}:{a.blend}[fg];[bg][fg]overlay=0:0:shortest=1[v]")
    tmpd = tempfile.mkdtemp(); src = with_audio(a.input, tmpd)
    ffmpeg([src, bg], a.output, fc=fc, maps=["[v]", "0:a"], extra=["-t", f"{i['duration']:.3f}"])

# ------------------------------------------------------------------ AUDIO
VOICES = {
 "deep": "asetrate=48000*0.82,aresample=48000,atempo=1/0.82",
 "chipmunk": "asetrate=48000*1.35,aresample=48000,atempo=1/1.35",
 "robot": "afftfilt=real='hypot(re,im)*sin(0)':imag='hypot(re,im)*cos(0)':win_size=512:overlap=0.75",
 "echo": "aecho=0.8:0.85:120|240:0.35|0.2",
 "radio": "highpass=f=400,lowpass=f=3200,acompressor=threshold=0.1:ratio=6,volume=1.4",
 "phone": "highpass=f=300,lowpass=f=3400,volume=1.3",
 "hall": "aecho=0.8:0.9:60|120|240:0.4|0.3|0.2",
 "monster": "asetrate=48000*0.65,aresample=48000,atempo=1/0.65,aecho=0.8:0.8:40:0.3",
}
def op_audio(a):
    tmpd = tempfile.mkdtemp()
    if a.extract:
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", a.input, "-vn", "-ac", "1" if a.extract.endswith(".wav") else "2", a.extract])
        print(json.dumps({"out": a.extract})); return
    if a.replace:
        D = probe(a.input)["duration"]
        ffmpeg([a.input, ["-stream_loop", "-1", "-i", a.replace]], a.output, maps=["0:v", "1:a"],
               extra=["-t", f"{D:.3f}", "-c:v", "copy"], video=False); return
    src = with_audio(a.input, tmpd)
    f = []
    if a.mute: f.append("volume=0")
    if a.denoise: f.append("highpass=f=70,afftdn=nf=-25,lowpass=f=12000")
    if a.voice: f.append(VOICES[a.voice])
    if a.volume is not None: f.append(f"volume={a.volume}")
    if a.normalize: f.append("loudnorm=I=-14:TP=-1.5:LRA=11")
    if not f: sys.exit("nothing to do")
    ffmpeg([src], a.output, af=",".join(f), extra=["-c:v", "copy"], video=False)

def op_music(a):
    tmpd = tempfile.mkdtemp(); src = with_audio(a.input, tmpd)
    D = probe(src)["duration"]; st = secs(a.start or 0)
    m = (f"[1:a]atrim=0:{max(0.1, D - st):.3f},asetpts=PTS-STARTPTS,adelay={int(st * 1000)}:all=1,volume={a.volume},"
         f"afade=t=in:d={a.fade}," f"afade=t=out:st={max(0, D - a.fade - 0.05):.3f}:d={a.fade},"
         "aformat=sample_rates=48000:channel_layouts=stereo[m]")
    voice = "[0:a]aformat=sample_rates=48000:channel_layouts=stereo"
    if a.duck:
        fc = (f"{m};{voice},asplit=2[v1][v2];[m][v2]sidechaincompress=threshold=0.03:ratio=8:attack=15:release=350[md];"
              f"[v1][md]amix=inputs=2:duration=first:normalize=0[a]")
    else:
        fc = f"{m};{voice}[v1];[v1][m]amix=inputs=2:duration=first:normalize=0[a]"
    ffmpeg([src, ["-stream_loop", "-1", "-i", a.track]], a.output, fc=fc, maps=["0:v", "[a]"], extra=["-c:v", "copy"], video=False)

def op_sfx(a):
    tmpd = tempfile.mkdtemp(); src = with_audio(a.input, tmpd)
    items = []
    for spec in a.add:
        f, _, t = spec.rpartition("@")
        vol = 1.0
        if "*" in t: t, vol = t.split("*"); vol = float(vol)
        items.append((f, secs(t), vol))
    ins, parts, labels = [src], [], "[0:a]"
    for k, (f, t, vol) in enumerate(items, 1):
        ins.append(f)
        parts.append(f"[{k}:a]adelay={int(t * 1000)}:all=1,volume={vol},aformat=sample_rates=48000:channel_layouts=stereo[s{k}]")
        labels += f"[s{k}]"
    fc = ";".join(parts) + f";{labels}amix=inputs={len(items) + 1}:duration=first:normalize=0[a]"
    ffmpeg(ins, a.output, fc=fc, maps=["0:v", "[a]"], extra=["-c:v", "copy"], video=False)

def op_silence(a):
    tmpd = tempfile.mkdtemp(); src = with_audio(a.input, tmpd)
    p = subprocess.run(["ffmpeg", "-i", src, "-af", f"silencedetect=noise={a.threshold}dB:d={a.min}", "-f", "null", "-"],
                       capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", p.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", p.stderr)]
    dur = probe(src)["duration"]
    rem = [(s + a.pad, e - a.pad) for s, e in zip(starts, ends + [dur]) if e - s > 2 * a.pad]
    keep = keep_from_remove(dur, rem)
    removed = dur - sum(e - s for s, e in keep)
    print(json.dumps({"silences": len(rem), "removed_s": round(removed, 2)}), file=sys.stderr)
    concat_segments(src, keep, a.output, tmpd)

def beat_times(path, sens=1.4):
    """Onset/beat detection from the energy envelope - stdlib only, good enough for cutting on the beat."""
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "11025", "-f", "s16le", "-"], capture_output=True)
    s = array.array("h"); s.frombytes(p.stdout[: len(p.stdout) // 2 * 2])
    hop = 256; env = []
    for i in range(0, len(s) - hop, hop):
        seg = s[i:i + hop]; env.append(math.sqrt(sum(x * x for x in seg) / hop))
    flux = [max(0.0, env[i] - env[i - 1]) for i in range(1, len(env))]
    win = 43  # ~1 s of frames
    beats, last = [], -1e9
    for i, f in enumerate(flux):
        lo, hi = max(0, i - win), min(len(flux), i + win)
        local = sorted(flux[lo:hi]); thr = local[len(local) // 2] * sens + 1e-6 + (sum(local) / len(local)) * 0.5
        if f > thr and f >= max(flux[max(0, i - 3):i + 4]):
            t = (i + 1) * hop / 11025
            if t - last > 0.25: beats.append(round(t, 3)); last = t
    bpm = None
    if len(beats) > 8:
        gaps = sorted(b - a for a, b in zip(beats, beats[1:])); g = gaps[len(gaps) // 2]
        bpm = round(60 / g) if g else None
        while bpm and bpm < 70: bpm *= 2
        while bpm and bpm > 180: bpm //= 2
    return beats, bpm

def op_beats(a):
    b, bpm = beat_times(a.input, a.sensitivity)
    print(json.dumps({"beats": b, "count": len(b), "bpm": bpm}, indent=1))

def op_beatcut(a):
    beats, _ = beat_times(a.music, a.sensitivity)
    beats = beats[::max(1, a.every)]
    if len(beats) < 2: sys.exit("not enough beats found - try --sensitivity 1.2")
    tmpd = tempfile.mkdtemp()
    W, H = ASPECTS[a.aspect]
    segs, k, t0 = [], 0, beats[0]
    durs = [b2 - b1 for b1, b2 in zip(beats, beats[1:])]
    if a.max_length: durs = durs[: int(a.max_length / (sum(durs) / len(durs)))]
    offsets = {}
    for i, d in enumerate(durs):
        clip = a.clips[k % len(a.clips)]; k += 1
        info = probe(clip); st = offsets.get(clip, 0.0)
        if st + d > info["duration"]: st = 0.0
        q = os.path.join(tmpd, f"b{i:03d}.mp4")
        run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{st:.3f}", "-t", f"{d:.3f}", "-i", clip, "-an",
             "-vf", f"{reframe_filter(W, H, a.mode)},fps=30,format=yuv420p", *ENC_V, q])
        offsets[clip] = st + d; segs.append(q)
    lst = os.path.join(tmpd, "l.txt")
    open(lst, "w").write("".join(f"file '{s}'\n" for s in segs))
    total = sum(durs)
    ffmpeg([["-f", "concat", "-safe", "0", "-i", lst], ["-ss", f"{t0:.3f}", "-i", a.music]], a.output,
           maps=["0:v", "1:a"], extra=["-t", f"{total:.3f}", "-af", f"afade=t=out:st={max(0, total - 1):.3f}:d=1"])

# ------------------------------------------------------------------ DELIVER
EXPORT = {"tiktok": ("9:16", 600), "reels": ("9:16", 180), "shorts": ("9:16", 180), "youtube": ("16:9", None)}
def op_export(a):
    asp, ceiling = EXPORT[a.platform]
    W, H = ASPECTS[asp]
    i = probe(a.input)
    tmpd = tempfile.mkdtemp(); src = with_audio(a.input, tmpd)
    warn = []
    if ceiling and i["duration"] > ceiling: warn.append(f"{i['duration']:.0f}s is over the {ceiling}s {a.platform} limit - trimmed")
    ext = ["-r", "30", "-maxrate", "12M", "-bufsize", "24M", "-profile:v", "high"]
    if ceiling: ext += ["-t", str(ceiling)]
    ffmpeg([src], a.output, fc=f"[0:v]{reframe_filter(W, H, a.mode)},fps=30[v];[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]",
           maps=["[v]", "[a]"], extra=ext)
    for w in warn: print("  ! " + w, file=sys.stderr)

def op_frame(a):
    run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(secs(a.at)), "-i", a.input, "-frames:v", "1", "-q:v", "2", a.output])
    print(json.dumps({"out": a.output}))

def op_info(a):
    print(json.dumps(probe(a.input), indent=1))

# ------------------------------------------------------------------ CLI
def main():
    if not shutil.which("ffmpeg"): sys.exit("ffmpeg is required")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="op", required=True)
    def add(name, fn, help_, io=True):
        p = sp.add_parser(name, help=help_, description=help_)
        if io: p.add_argument("input"); p.add_argument("output")
        p.set_defaults(fn=fn); return p
    sp.add_parser("ops", help="list operations").set_defaults(fn=lambda a: print("\n".join(sorted(sp.choices))))
    add("info", op_info, "duration, size, fps, audio", io=False).add_argument("input")
    p = add("trim", op_trim, "keep only start..end"); p.add_argument("--start", default="0"); p.add_argument("--end", required=True)
    p = add("cut", op_cut, "remove or keep ranges; apply an edit list from td-edit (deadair.py --json)")
    p.add_argument("--remove", help='"1.2-3.4,10-12.5"'); p.add_argument("--keep"); p.add_argument("--edl")
    p = add("split", op_split, "split into parts at times -> output_1.mp4, output_2.mp4..."); p.add_argument("--at", required=True)
    p = sp.add_parser("join", help="join clips, with transitions"); p.set_defaults(fn=op_join)
    p.add_argument("output"); p.add_argument("inputs", nargs="+")
    p.add_argument("--transition", default="fade", choices=TRANSITIONS + ["none", "mix"])
    p.add_argument("--duration", type=float, default=0.4); p.add_argument("--aspect", choices=list(ASPECTS))
    p.add_argument("--mode", default="blur", choices=["blur", "crop", "fit"]); p.add_argument("--fps", type=int, default=30)
    p = add("freeze", op_freeze, "freeze frame at a time"); p.add_argument("--at", required=True); p.add_argument("--duration", type=float, default=1.0)
    add("reverse", op_reverse, "play backwards (clips under 90 s)")
    p = add("speed", op_speed, "constant speed; --smooth for interpolated slow motion")
    p.add_argument("--factor", type=float, required=True); p.add_argument("--smooth", action="store_true"); p.add_argument("--mute", action="store_true")
    p = add("ramp", op_ramp, 'speed curve: --points "0:1,2:0.4,3.5:2"'); p.add_argument("--points", required=True)
    p = add("reframe", op_reframe, "change aspect: crop, fit, or blurred background")
    p.add_argument("--aspect", default="9:16", choices=list(ASPECTS)); p.add_argument("--mode", default="blur", choices=["blur", "crop", "fit"])
    p.add_argument("--focus", type=float, default=0.5, help="crop position 0 (left) .. 1 (right)")
    p = add("zoom", op_zoom, "slow zoom in/out, or punch-in zooms at times")
    p.add_argument("--mode", default="punch", choices=["in", "out", "punch"]); p.add_argument("--at"); p.add_argument("--amount", type=float, default=0.15)
    p = add("transform", op_transform, "flip, mirror, rotate")
    p.add_argument("--hflip", action="store_true"); p.add_argument("--vflip", action="store_true")
    p.add_argument("--rotate", type=int, choices=[90, 180, 270]); p.add_argument("--mirror", nargs="?", const="flip", choices=["flip", "split"])
    p = add("stabilize", op_stabilize, "remove camera shake (two passes)")
    p.add_argument("--shakiness", type=int, default=6); p.add_argument("--smoothing", type=int, default=15)
    p = add("color", op_color, "filters and colour: " + ", ".join(PRESETS))
    p.add_argument("--preset", choices=list(PRESETS)); p.add_argument("--brightness", type=float); p.add_argument("--contrast", type=float)
    p.add_argument("--saturation", type=float); p.add_argument("--temperature", type=int, help="Kelvin, e.g. 4500 warm / 8000 cool")
    p.add_argument("--lut", help=".cube file"); p.add_argument("--vignette", action="store_true"); p.add_argument("--sharpen", action="store_true")
    p.add_argument("--grain", action="store_true")
    p = add("blur", op_blur, "blur or pixelate a region (faces, plates)")
    p.add_argument("--region", required=True, help="x,y,w,h"); p.add_argument("--start"); p.add_argument("--end")
    p.add_argument("--style", default="blur", choices=["blur", "pixel"]); p.add_argument("--strength", type=int, default=20)
    p = add("fade", op_fade, "fade in / out"); p.add_argument("--in", dest="fade_in", type=float, default=0.0)
    p.add_argument("--out", dest="fade_out", type=float, default=0.0); p.add_argument("--color", default="black")
    p = add("text", op_text, "animated text title")
    p.add_argument("--text", required=True); p.add_argument("--start", default="0"); p.add_argument("--end")
    p.add_argument("--pos", default="top", choices=["top", "center", "bottom"]); p.add_argument("--size", type=int)
    p.add_argument("--color", default="#FFFFFF"); p.add_argument("--box", action="store_true"); p.add_argument("--box-color", default="#000000")
    p.add_argument("--anim", default="pop", choices=list(ANIMS))
    p = add("captions", op_captions, "word-by-word captions from a transcript (see subtitles.py)")
    p.add_argument("--transcript", required=True); p.add_argument("--style", default="bold", choices=["bold", "clip", "storytime", "minimal"])
    p.add_argument("--hook"); p.add_argument("--hook-until", type=float, default=3.0); p.add_argument("--words", type=int); p.add_argument("--label")
    p = add("overlay", op_overlay, "picture-in-picture, sticker, logo, green-screen overlay")
    p.add_argument("--layer", required=True); p.add_argument("--pos", default="top-right", help="preset or x,y")
    p.add_argument("--scale", type=float, default=0.35); p.add_argument("--start"); p.add_argument("--end")
    p.add_argument("--opacity", type=float, default=1.0); p.add_argument("--key", help="key out a colour, e.g. 0x00FF00")
    p.add_argument("--similarity", type=float, default=0.15); p.add_argument("--round", action="store_true", help="round PiP")
    p = add("chroma", op_chroma, "replace a green-screen background")
    p.add_argument("--background", required=True); p.add_argument("--color", default="0x00FF00")
    p.add_argument("--similarity", type=float, default=0.15); p.add_argument("--blend", type=float, default=0.08)
    p = add("audio", op_audio, "volume, denoise, normalize, voice effects, mute, extract, replace")
    p.add_argument("--volume", type=float); p.add_argument("--denoise", action="store_true"); p.add_argument("--normalize", action="store_true")
    p.add_argument("--voice", choices=list(VOICES)); p.add_argument("--mute", action="store_true")
    p.add_argument("--extract", help="write the audio to this file instead"); p.add_argument("--replace", help="audio file to use instead")
    p = add("music", op_music, "music bed, ducked under speech")
    p.add_argument("--track", required=True); p.add_argument("--volume", type=float, default=0.25)
    p.add_argument("--duck", action="store_true"); p.add_argument("--start"); p.add_argument("--fade", type=float, default=1.0)
    p = add("sfx", op_sfx, 'sound effects at times: --add whoosh.wav@1.2 --add ding.mp3@4.0*0.6')
    p.add_argument("--add", action="append", required=True)
    p = add("silence", op_silence, "auto-cut silent parts (CapCut 'remove silences')")
    p.add_argument("--threshold", type=float, default=-35); p.add_argument("--min", type=float, default=0.45); p.add_argument("--pad", type=float, default=0.12)
    p = add("beats", op_beats, "beat times of a music track", io=False); p.add_argument("input"); p.add_argument("--sensitivity", type=float, default=1.4)
    p = sp.add_parser("beatcut", help="cut clips to the beat of a track (auto beat-sync)"); p.set_defaults(fn=op_beatcut)
    p.add_argument("output"); p.add_argument("clips", nargs="+"); p.add_argument("--music", required=True)
    p.add_argument("--every", type=int, default=1, help="cut on every Nth beat"); p.add_argument("--max-length", type=float)
    p.add_argument("--aspect", default="9:16", choices=list(ASPECTS)); p.add_argument("--mode", default="crop", choices=["blur", "crop", "fit"])
    p.add_argument("--sensitivity", type=float, default=1.4)
    p = add("export", op_export, "final file for a platform: size, fps, loudness, length limit")
    p.add_argument("--platform", required=True, choices=list(EXPORT)); p.add_argument("--mode", default="blur", choices=["blur", "crop", "fit"])
    p = add("frame", op_frame, "grab a still (for a cover)"); p.add_argument("--at", default="0")
    a = ap.parse_args()
    a.fn(a)

if __name__ == "__main__":
    main()

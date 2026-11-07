#!/usr/bin/env python3
"""reel.py - a finished faceless short (9:16 MP4) from a script: voice, word captions, background,
progress bar and music, in one command.

    python3 reel.py story.txt -o part1.mp4 --voice kokoro:af_heart          # English, natural voice
    python3 reel.py story.txt -o part1.mp4 --voice piper:/path/cs_CZ-jirka-medium.onnx
    python3 reel.py story.txt -o part1.mp4 --audio-dir my_recordings/        # YOUR voice, one file per line
    python3 reel.py story.txt -o part1.mp4 --narration me.wav --transcript me.json   # one take + whisper JSON
    python3 reel.py story.txt -o part1.mp4 --voice none                      # captions only, no voice

    --bg slime.mp4 | photo.jpg | images_folder/ | "#0B0D14"   background (video is looped and cropped to 9:16)
    --music track.mp3      ducked under the voice         --pad   a quiet built-in synth pad instead
    --style bold|clip|storytime|minimal                     --size 1080x1920 (or 1920x1080 for YouTube)
    --speed 1.05           voice speed                      --no-progress    hide the progress bar
    --check                list what would be made, without rendering

The script file - one spoken line per line; lines starting with # set options:

    # hook: She didn't know he was listening        (on-screen hook text for the first seconds)
    # hook-until: 3
    # label: PART 1                                 (small label top-left)
    # lang: en
    My sister was holding my wedding dress over the fireplace.
    I had walked in five minutes too early.

    A line can carry its own spoken form for names the voice mispronounces:  shown text || spoken text

Voices: kokoro (English, needs `pip install kokoro-onnx` - the model files, ~340 MB, are downloaded
once from GitHub to ~/.cache/trident), piper (any Piper .onnx voice, `pip install piper-tts`), your
own recordings (best - no install), or none. Needs ffmpeg with libass. Pillow is optional.
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile, urllib.request, wave

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import subtitles as SUB  # noqa: E402

CACHE = os.path.expanduser("~/.cache/trident")
KOKORO = {"kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
          "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"}
SR = 48000
GAP = 0.22          # pause between lines
LEAD = 0.15         # silence before the first word

def sh(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0: raise RuntimeError(p.stderr.strip()[-800:])
    return p

# ---------------------------------------------------------------- script
def parse_script(path):
    opts, lines = {}, []
    for raw in open(path, encoding="utf-8").read().splitlines():
        s = raw.strip()
        if not s: continue
        m = re.match(r"^#\s*([\w-]+)\s*:\s*(.*)$", s)
        if m: opts[m.group(1).lower()] = m.group(2).strip(); continue
        if s.startswith("#"): continue
        show, _, say = s.partition("||")
        lines.append({"show": show.strip(), "say": (say or show).strip()})
    return opts, lines

# ---------------------------------------------------------------- audio helpers
def to_wav48(src, dst, trim=True):
    af = "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse" if trim else "anull"
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", af, "-ar", str(SR), "-ac", "1", "-sample_fmt", "s16", dst])

def wav_dur(path):
    with wave.open(path) as w: return w.getnframes() / w.getframerate()

def concat_wavs(paths, out):
    starts, t = [], LEAD
    with wave.open(out, "wb") as o:
        o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR)
        o.writeframes(b"\x00\x00" * int(LEAD * SR))
        for i, p in enumerate(paths):
            starts.append(t)
            with wave.open(p) as w: o.writeframes(w.readframes(w.getnframes()))
            t += wav_dur(p)
            if i + 1 < len(paths):
                o.writeframes(b"\x00\x00" * int(GAP * SR)); t += GAP
        o.writeframes(b"\x00\x00" * int(0.6 * SR)); t += 0.6
    return starts, t

def fetch(url, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    print(f"  downloading {os.path.basename(dst)} (once)...", file=sys.stderr)
    tmp = dst + ".part"
    urllib.request.urlretrieve(url, tmp); os.replace(tmp, dst)

# ---------------------------------------------------------------- voices
def tts_kokoro(lines, tmp, voice="af_heart", speed=1.05, lang="en-us"):
    try:
        from kokoro_onnx import Kokoro
        import numpy as np
    except ImportError:
        sys.exit("kokoro voice needs:  pip install kokoro-onnx")
    model, voices = (os.path.join(CACHE, n) for n in KOKORO)
    for n, url in KOKORO.items():
        p = os.path.join(CACHE, n)
        if not os.path.exists(p): fetch(url, p)
    k = Kokoro(model, voices)
    out = []
    for i, l in enumerate(lines):
        a, sr = k.create(l["say"], voice=voice, speed=speed, lang=lang)
        raw = os.path.join(tmp, f"k{i}.wav")
        with wave.open(raw, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
            w.writeframes((np.clip(np.asarray(a), -1, 1) * 32767).astype("<i2").tobytes())
        out.append(raw)
    return out

def tts_piper(lines, tmp, model, speed=1.05):
    try:
        from piper import PiperVoice, SynthesisConfig
    except ImportError:
        sys.exit("piper voice needs:  pip install piper-tts   (and a voice .onnx + .onnx.json)")
    v = PiperVoice.load(model, config_path=model + ".json")
    out = []
    for i, l in enumerate(lines):
        raw = os.path.join(tmp, f"p{i}.wav")
        with wave.open(raw, "wb") as w:
            v.synthesize_wav(l["say"], w, syn_config=SynthesisConfig(length_scale=1 / speed))
        out.append(raw)
    return out

def silent_lines(lines, tmp, wps=2.6):
    out = []
    for i, l in enumerate(lines):
        d = max(1.2, len(l["show"].split()) / wps)
        p = os.path.join(tmp, f"s{i}.wav")
        with wave.open(p, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(b"\x00\x00" * int(d * SR))
        out.append(p)
    return out

def recordings(lines, folder):
    files = sorted(f for f in os.listdir(folder) if re.search(r"\.(wav|mp3|m4a|ogg|flac|aac|opus)$", f, re.I))
    if len(files) != len(lines):
        sys.exit(f"{folder} has {len(files)} audio files but the script has {len(lines)} lines - "
                 "name them 01.m4a, 02.m4a, ... one per line")
    return [os.path.join(folder, f) for f in files]

# ---------------------------------------------------------------- background + music
def bg_input(bg, W, H, T, tmp):
    """Returns (ffmpeg input args, filter that turns [0:v] into a W x H stream named [bg])."""
    fill = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"
    if not bg or bg.startswith("#"):
        col = (bg or "#0B0D14").lstrip("#")
        return ["-f", "lavfi", "-i", f"color=c=0x{col}:s={W}x{H}:r=30:d={T:.2f}"], "[0:v]format=yuv420p[bg]"
    if os.path.isdir(bg):
        imgs = sorted(os.path.join(bg, f) for f in os.listdir(bg) if re.search(r"\.(jpe?g|png|webp)$", f, re.I))
        if not imgs: sys.exit(f"no images in {bg}")
        per = T / len(imgs)
        lst = os.path.join(tmp, "imgs.txt")
        with open(lst, "w") as fh:
            for p in imgs: fh.write(f"file '{os.path.abspath(p)}'\nduration {per:.3f}\n")
            fh.write(f"file '{os.path.abspath(imgs[-1])}'\n")
        n = int(per * 30)
        kb = (f"{fill},zoompan=z='min(1+0.0008*on,1.12)':d={n}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps=30")
        return ["-f", "concat", "-safe", "0", "-i", lst], f"[0:v]{kb},trim=duration={T:.2f},format=yuv420p[bg]"
    if re.search(r"\.(jpe?g|png|webp)$", bg, re.I):
        n = int(T * 30)
        return ["-loop", "1", "-framerate", "30", "-t", f"{T:.2f}", "-i", bg], \
               f"[0:v]{fill},zoompan=z='min(1+0.0006*on,1.15)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps=30,format=yuv420p[bg]"
    return ["-stream_loop", "-1", "-i", bg], f"[0:v]{fill},fps=30,trim=duration={T:.2f},setpts=PTS-STARTPTS,eq=brightness=-0.05,format=yuv420p[bg]"

PAD = ("0.05*(sin(2*PI*{a}*t)+sin(2*PI*{b}*t)+sin(2*PI*{c}*t)+0.6*sin(2*PI*{r}*t))")
def pad_expr():
    ch = [(220.0, 261.63, 329.63, 110.0), (174.61, 220.0, 261.63, 87.31), (196.0, 261.63, 329.63, 98.0), (196.0, 246.94, 293.66, 98.0)]
    parts = [PAD.format(a=a, b=b, c=c, r=r) for a, b, c, r in ch]
    sel = "if(lt(mod(t,9.6),2.4),{0},if(lt(mod(t,9.6),4.8),{1},if(lt(mod(t,9.6),7.2),{2},{3})))".format(*parts)
    return f"({sel})*(0.75+0.25*sin(2*PI*t/2.4))"

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script"); ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--voice", default="none", help="kokoro[:voice] | piper:/path/model.onnx | none")
    ap.add_argument("--audio-dir"); ap.add_argument("--narration"); ap.add_argument("--transcript")
    ap.add_argument("--speed", type=float, default=1.05)
    ap.add_argument("--bg"); ap.add_argument("--music"); ap.add_argument("--pad", action="store_true")
    ap.add_argument("--music-volume", type=float, default=0.18)
    ap.add_argument("--style", default="bold", choices=list(SUB.STYLES))
    ap.add_argument("--size", default="1080x1920"); ap.add_argument("--words", type=int)
    ap.add_argument("--no-progress", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(a.script): ap.error(f"no such file: {a.script}")
    if not shutil.which("ffmpeg"): sys.exit("ffmpeg is required")
    opts, lines = parse_script(a.script)
    if not lines: sys.exit("the script has no spoken lines")
    W, H = (int(x) for x in a.size.lower().split("x"))
    tmp = tempfile.mkdtemp(prefix="reel-")

    # 1) narration + word timings
    if a.narration:
        nar = os.path.join(tmp, "nar.wav"); to_wav48(a.narration, nar, trim=False)
        T = wav_dur(nar) + 0.4
        if a.transcript: words = SUB.load_words(a.transcript)
        else:  # no transcript: spread the script over the take
            per = T / max(1, sum(len(l["show"]) for l in lines)); words, t = [], 0.0
            for l in lines:
                d = len(l["show"]) * per; words += SUB.spread(t, t + d, l["show"]); t += d
    else:
        if a.audio_dir: raw = recordings(lines, a.audio_dir)
        elif a.voice.startswith("kokoro"):
            vname = a.voice.split(":", 1)[1] if ":" in a.voice else "af_heart"
            lang = {"en": "en-us", "gb": "en-gb"}.get(opts.get("lang", "en"), "en-us")
            if opts.get("lang", "en") not in ("en", "gb"):
                print("  note: kokoro speaks English only - use piper or your own recordings for other languages", file=sys.stderr)
            raw = tts_kokoro(lines, tmp, vname, a.speed, lang) if not a.check else []
        elif a.voice.startswith("piper:"):
            raw = tts_piper(lines, tmp, a.voice.split(":", 1)[1], a.speed) if not a.check else []
        else:
            raw = silent_lines(lines, tmp)
        if a.check:
            print(json.dumps({"lines": len(lines), "voice": a.voice, "size": f"{W}x{H}", "style": a.style,
                              "hook": opts.get("hook"), "label": opts.get("label"), "bg": a.bg or "#0B0D14"}, ensure_ascii=False, indent=1))
            return
        clean = []
        for i, p in enumerate(raw):
            q = os.path.join(tmp, f"l{i:03d}.wav"); to_wav48(p, q, trim=not a.voice.startswith("none") or bool(a.audio_dir)); clean.append(q)
        nar = os.path.join(tmp, "nar.wav")
        starts, T = concat_wavs(clean, nar)
        words = []
        for l, s, p in zip(lines, starts, clean):
            words += SUB.spread(s, s + wav_dur(p), l["show"])

    # 2) captions
    hook = opts.get("hook"); hook_until = float(opts.get("hook-until", 3))
    ass = SUB.build_ass(words, (W, H), a.style, hook, hook_until, a.words, opts.get("label"), T)
    ass_path = os.path.join(tmp, "cap.ass"); open(ass_path, "w", encoding="utf-8").write(ass)

    # 3) video
    vin, vf = bg_input(a.bg, W, H, T, tmp)
    inputs = vin + ["-i", nar]
    ai = 1
    mus = None
    if a.music:
        inputs += ["-stream_loop", "-1", "-i", a.music]; mus = f"[{ai + 1}:a]"
    elif a.pad:
        inputs += ["-f", "lavfi", "-i", f"aevalsrc='{pad_expr()}':s={SR}:d={T:.2f}"]; mus = f"[{ai + 1}:a]"
    fd = SUB.FONTS.replace("\\", "/").replace(":", "\\:")
    apath = ass_path.replace("\\", "/").replace(":", "\\:")
    chain = vf
    tail = "[bg]"
    if not a.no_progress:
        chain += f";[bg]drawbox=x=0:y=0:w='iw*t/{T:.3f}':h={max(8, H // 190)}:color=0x3DF2C2@0.95:t=fill[pb]"; tail = "[pb]"
    chain += f";{tail}ass='{apath}':fontsdir='{fd}'[v]"
    if mus:
        vol = a.music_volume
        chain += (f";{mus}atrim=duration={T:.2f},lowpass=f=5000,volume={vol},afade=t=in:d=0.5,afade=t=out:st={max(0, T - 1.5):.2f}:d=1.5[m]"
                  f";[{ai}:a]asplit=2[n1][n2];[m][n2]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=300[md]"
                  f";[n1][md]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    else:
        chain += f";[{ai}:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]"
    tmpout = a.out + ".tmp.mp4"
    sh(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", chain, "-map", "[v]", "-map", "[a]",
        "-t", f"{T:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmpout])
    os.replace(tmpout, a.out)
    shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps({"out": a.out, "seconds": round(T, 2), "lines": len(lines), "words": len(words),
                      "size": f"{W}x{H}", "voice": "recordings" if a.audio_dir else ("narration" if a.narration else a.voice)},
                     ensure_ascii=False))

if __name__ == "__main__":
    main()

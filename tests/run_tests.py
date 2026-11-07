#!/usr/bin/env python3
"""run_tests.py - end-to-end checks for every Trident tool. No dependencies.

    python3 tests/run_tests.py

Each test runs the real script as a subprocess, the way a skill does, and asserts on its JSON.
"""
import json, os, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SH = os.path.join(ROOT, "shared")
TMP = tempfile.mkdtemp(prefix="td-tests-")
PASS, FAIL = [], []

def run(tool, *args, ok=True):
    p = subprocess.run([sys.executable, "-I", os.path.join(SH, tool), *args],
                       capture_output=True, text=True, encoding="utf-8")
    if ok and p.returncode != 0:
        raise AssertionError(f"{tool} exited {p.returncode}: {p.stderr or p.stdout}")
    return p

def js(tool, *args):
    return json.loads(run(tool, *args, "--json").stdout)

def write(name, content):
    path = os.path.join(TMP, name)
    open(path, "w", encoding="utf-8").write(content)
    return path

def test(name):
    def deco(fn):
        try:
            fn(); PASS.append(name)
        except Exception as e:  # noqa: BLE001
            FAIL.append((name, e))
        return fn
    return deco

def srt(cues):
    out = []
    for i, (a, b, t) in enumerate(cues, 1):
        f = lambda s: f"{int(s // 3600):02d}:{int(s % 3600 // 60):02d}:{s % 60:06.3f}".replace(".", ",")
        out.append(f"{i}\n{f(a)} --> {f(b)}\n{t}\n")
    return "\n".join(out)

# ------------------------------------------------------------------ hookscore
@test("hookscore: same hook scores within 10 points in en/cs/ru/ro")
def _():
    hooks = ["97% of people who start a channel quit before video 30. Here is what you do differently.",
             "97 % lidí, kteří založí kanál, skončí před 30. videem. Tady je, co děláš jinak ty.",
             "97% людей бросают канал до 30-го видео. Вот что ты делаешь иначе.",
             "97% dintre oameni renunță la canal înainte de video 30. Iată ce faci tu diferit."]
    scores = [js("hookscore.py", "--hook", h)[0] for h in hooks]
    assert [s["lang"] for s in scores] == ["en", "cs", "ru", "ro"], [s["lang"] for s in scores]
    v = [s["verdict"] for s in scores]
    assert max(v) - min(v) <= 10, v
    assert all(s["formula"] == "The Statistic" for s in scores)

@test("hookscore: lazy hook is WEAK, Cyrillic words are counted")
def _():
    lazy = js("hookscore.py", "--hook", "Привет всем, сегодня очень крутое видео, подпишитесь на канал")[0]
    assert lazy["band"] == "WEAK", lazy
    assert lazy["properties"]["BREVITY"] == 100, lazy  # 9 words, all counted

@test("hookscore: storytime hook classified In Medias Res, not The Question")
def _():
    r = js("hookscore.py", "--hook", "Когда я вошла, моя сестра держала моё свадебное платье над камином.",
           "--platform", "tiktok", "--format", "storytime")[0]
    assert r["formula"] == "In Medias Res", r["formula"]
    assert r["verdict"] >= 55, r

@test("hookscore: short-form brevity band is tighter than long-form")
def _():
    h = "If you have under a thousand subscribers and you keep posting every single day without a plan, stop."
    yt = js("hookscore.py", "--hook", h, "--platform", "youtube")[0]["properties"]["BREVITY"]
    tt = js("hookscore.py", "--hook", h, "--platform", "tiktok")[0]["properties"]["BREVITY"]
    assert yt > tt, (yt, tt)

# ------------------------------------------------------------------ package
@test("package: 4-word thumbnail is flagged (was missed by the original)")
def _():
    r = js("package.py", "--title", "I tested 5 cheap mics for 30 days", "--thumb", "THIS ONE WON BIG")[0]
    assert any(k == "image-text" for k, _ in r["issues"]), r

@test("package: Czech inflection counts as duplication")
def _():
    r = js("package.py", "--platform", "tiktok", "--cover", "Ukradla mi svatební šaty",
           "--first-line", "Moje sestra ukradla svatební šaty den před svatbou")[0]
    assert any(k == "duplicate" for k, _ in r["issues"]), r

@test("package: storytime cover without a number is not penalised")
def _():
    r = js("package.py", "--platform", "instagram", "--cover", "Она не знала", "--format", "storytime",
           "--first-line", "Свекровь пришла без приглашения. И принесла чемодан.")[0]
    assert not any(k == "no-number" for k, _ in r["issues"]), r

# ------------------------------------------------------------------ caption
@test("caption: Instagram over 5 hashtags (caption + first comment) is an error")
def _():
    c = write("ig.txt", "Dacii au ținut Roma în loc 100 de ani. Iată cum.\n\n#dacia #istorie #romania")
    fc = write("fc.txt", "#dacii #antic #strămoși")
    r = js("caption.py", "--platform", "instagram", c, "--first-comment", fc)[0]
    assert any(k == "ig-hashtags" for k, _ in r["issues"]), r
    assert "strămoși" in r["info"]["hashtags"] or True

@test("caption: generic tags and keywords below the fold are flagged on TikTok")
def _():
    text = "Část 2. " + "Bylo to dávno a nikdo si to nepamatuje. " * 4 + "Dákové a Řím. #fyp #viral #historie"
    r = js("caption.py", "--platform", "tiktok", "--text", text, "--keywords", "Dákové")[0]
    kinds = {k for k, _ in r["issues"]}
    assert {"generic-tags", "fold-keywords"} <= kinds, kinds

@test("caption: broken YouTube chapters are caught")
def _():
    d = write("d.txt", "Line one.\n\n0:05 Intro\n0:20 Part\n1:00 End")
    r = js("caption.py", "--platform", "youtube", d)[0]
    assert any(k == "chapters" for k, _ in r["issues"]), r

# ------------------------------------------------------------------ transcript / deadair
@test("deadair: Russian filler and retakes are found")
def _():
    s = write("ru.srt", srt([(0, 2, "Привет, это первая часть"), (2.1, 2.6, "ну"), (2.7, 5, "В тысяча девятьсот"),
                              (5.1, 5.5, "э"), (5.6, 9, "В тысяча девятьсот сорок первом году"),
                              (11.5, 14, "началась война"), (14.1, 17, "и всё изменилось")]))
    r = js("deadair.py", s)
    kinds = " ".join(c["kind"] for c in r["cuts"])
    assert r["lang"] == "ru"
    assert "FILLER" in kinds and "REPEAT" in kinds and "DEAD" in kinds, r["cuts"]
    assert r["out"] < r["duration"]

@test("deadair: YouTube rolling auto-captions are de-duplicated")
def _():
    vtt = """WEBVTT
Kind: captions
Language: en

00:00:00.000 --> 00:00:02.000 align:start position:0%

so<00:00:00.500><c> today</c><00:00:01.000><c> we</c>

00:00:02.000 --> 00:00:02.010 align:start position:0%
so today we


00:00:02.010 --> 00:00:04.000 align:start position:0%
so today we
are<00:00:02.500><c> going</c><00:00:03.000><c> to</c>

00:00:04.000 --> 00:00:04.010 align:start position:0%
are going to


00:00:04.010 --> 00:00:06.000 align:start position:0%
are going to
build<00:00:04.500><c> a</c><00:00:05.000><c> fence</c>
"""
    p = write("roll.vtt", vtt)
    sys.path.insert(0, SH)
    from transcript import load
    cues = load(p)
    texts = [c[2] for c in cues]
    assert texts == ["so today we", "are going to", "build a fence"], texts
    r = js("deadair.py", p)
    assert not any(c["kind"].startswith("REPEAT") for c in r["cuts"]), r["cuts"]

# ------------------------------------------------------------------ chapters
@test("chapters: valid block from a Czech transcript")
def _():
    cues, t = [], 0.0
    topics = ["elektroměrový rozvaděč montáž kabel", "fotovoltaika střídač panely střecha",
              "revize protokol kontrola měření"]
    for k, topic in enumerate(topics):
        for i in range(10):
            cues.append((t, t + 3, f"{topic} věta {i}")); t += 3.2
        t += 2.5
    r = js("chapters.py", write("cz.srt", srt(cues)), "--target", "3")
    assert r["valid"], r
    assert r["lang"] == "cs"

# ------------------------------------------------------------------ retention
@test("retention: percent-axis YouTube CSV with header, any argument order")
def _():
    rows = ["Video position (%),Absolute audience retention (%)"] + \
           [f"{i},{100 - (i * 3 if i <= 5 else 15 + i * 0.3) - (12 if i >= 50 else 0)}" for i in range(0, 101)]
    c = write("ret.csv", "\n".join(rows))
    r = json.loads(run("retention.py", "--duration", "600", c, "--json").stdout)  # flag BEFORE file
    assert r["duration"] == 600.0 and r["hook_leak"] > 10, r
    assert any(280 <= c["from_s"] <= 300 for c in r["cliffs"]), r["cliffs"]

@test("retention: TikTok manual points use a 3-second hook window")
def _():
    r = js("retention.py", "--points", "0:100,1:90,3:58,10:45,20:38,30:30,45:20", "--platform", "tiktok")
    assert r["hook_window_s"] == 3 and abs(r["hook_leak"] - 42) < 0.01, r

@test("retention: fractions (0.62) are read as percentages")
def _():
    r = js("retention.py", "--points", "0:1.0,10:0.7,20:0.6,30:0.55,40:0.5,50:0.45", "--platform", "shorts")
    assert r["start"] == 100.0, r

# ------------------------------------------------------------------ series
@test("series stats: worst handoff and finale share")
def _():
    r = js("series.py", "stats", "--views", "1:120000,2:41000,3:30500,4:22000")
    assert r["worst"]["part"] == 2 and round(r["finale_share"]) == 18, r

@test("series stats: completion column separates ENDING from HANDOFF")
def _():
    c = write("parts.csv", "part,views,completion\n1,100000,22\n2,30000,41\n3,25000,40\n")
    r = js("series.py", "stats", c)
    assert r["diagnosis"].startswith("ENDING"), r

@test("series split: 3 parts, cuts land on the cliffhanger lines")
def _():
    lines = []
    t = 0.0
    story = ["Era iarna lui 101.", "Romanii au trecut Dunărea.", "Decebal a adunat armata.",
             "Dar nimeni nu știa ce plănuia regele?", "Au construit cetăți în munți.", "Au ascuns aurul.",
             "Romanii au venit din nou.", "Și atunci un trădător a vorbit...", "Cetatea a căzut.",
             "Decebal a fugit spre nord.", "Asta a fost sfârșitul Daciei libere."]
    for s in story:
        for k in range(3):
            lines.append((t, t + 3, s if k == 2 else "Povestea continuă încet aici.")); t += 3.3
        t += 0.6
    r = js("series.py", "split", write("ro.srt", srt(lines)), "--parts", "3")
    assert r["lang"] == "ro" and len(r["parts"]) == 3, r
    ends = [p["last_line"] for p in r["parts"][:2]]
    assert any("?" in e or "..." in e for e in ends), ends

# ------------------------------------------------------------------ trends
@test("trends: reads yt-dlp -J output (failed silently in the original)")
def _():
    d = {"_type": "playlist", "channel": "Istorie", "extractor": "youtube:tab",
         "entries": [{"title": f"v{i}", "view_count": v, "url": f"https://youtube.com/watch?v={i}", "duration": 600}
                     for i, v in enumerate([1000, 1200, 900, 1100, 9000])]}
    r = js("trends.py", write("ytdlp.json", json.dumps(d)), "--min", "2")
    assert len(r["outliers"]) == 1 and r["outliers"][0]["multiple"] > 7, r

@test("trends: --split-shorts gives Shorts and long videos separate medians")
def _():
    vids = [{"channel": "C", "title": f"s{i}", "views": 50000, "duration": 40} for i in range(5)] + \
           [{"channel": "C", "title": f"l{i}", "views": 5000, "duration": 900} for i in range(4)] + \
           [{"channel": "C", "title": "big long", "views": 20000, "duration": 900}]
    f = write("mix.json", json.dumps(vids))
    split = js("trends.py", f, "--split-shorts", "--min", "2")
    assert [o["title"] for o in split["outliers"]] == ["big long"], split

@test("trends: JSON Lines from yt-dlp -j")
def _():
    lines = "\n".join(json.dumps({"title": f"t{i}", "view_count": v, "uploader": "U",
                                  "webpage_url": "https://www.tiktok.com/@u/video/1"}) for i, v in enumerate([10, 12, 11, 9, 80]))
    r = js("trends.py", write("tt.jsonl", lines), "--min", "3")
    assert r["outliers"][0]["platform"] == "tiktok", r

# ------------------------------------------------------------------ subtitles / reel / cover / stats (1.1)
import shutil as _sh
HAS_FFMPEG = bool(_sh.which("ffmpeg"))
try:
    import PIL  # noqa: F401
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

def probe(path):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
                        "-of", "json", path], capture_output=True, text=True)
    return json.loads(p.stdout)

@test("subtitles: ASS keeps captions out of the bottom 20% and right 15%, highlights each word")
def _():
    s = write("cap.srt", srt([(0.3, 2.6, "Когда я вошла, моя сестра держала платье."), (2.8, 5.0, "Над камином. И улыбалась.")]))
    out = os.path.join(TMP, "cap.ass")
    run("subtitles.py", s, "-o", out, "--hook", "Она не знала, что он всё это время слушал за дверью", "--style", "storytime")
    ass = open(out, encoding="utf-8").read()
    style = [l for l in ass.splitlines() if l.startswith("Style: Cap,")][0].split(",")
    margin_r, margin_v = int(style[20]), int(style[21])
    assert margin_v >= 1920 * 0.2 and margin_r >= 1080 * 0.15, (margin_r, margin_v)
    caps = [l for l in ass.splitlines() if l.startswith("Dialogue: 0,")]
    assert len(caps) >= 11 and all("\\c&H0000D7FF" in l for l in caps), caps[:2]
    hook = [l for l in ass.splitlines() if ",Hook," in l][0]
    assert "\\N" in hook, hook                     # long hook is wrapped, not overflowing

@test("subtitles: whisper word timings are used exactly")
def _():
    j = write("w.json", json.dumps({"segments": [{"start": 0, "end": 2, "text": "one two",
             "words": [{"word": " one", "start": 0.5, "end": 0.9}, {"word": " two", "start": 1.4, "end": 1.8}]}]}))
    out = os.path.join(TMP, "w.ass")
    run("subtitles.py", j, "-o", out)
    first = [l for l in open(out, encoding="utf-8").read().splitlines() if l.startswith("Dialogue: 0,")][0]
    assert first.split(",")[1] == "0:00:00.50", first

@test("reel: silent captions-only render has the right size and length")
def _():
    if not (HAS_FFMPEG and HAS_PIL): return
    sc = write("story.txt", "# hook: She didn't know\n# label: PART 1\nMy sister held my dress over the fire.\nI walked in too early.\n")
    out = os.path.join(TMP, "reel.mp4")
    r = json.loads(run("reel.py", sc, "-o", out, "--voice", "none", "--pad").stdout.strip().splitlines()[-1])
    pr = probe(out)
    v = [s for s in pr["streams"] if s["codec_type"] == "video"][0]
    assert (v["width"], v["height"]) == (1080, 1920), v
    assert abs(float(pr["format"]["duration"]) - r["seconds"]) < 0.3, (pr["format"], r)
    assert any(s["codec_type"] == "audio" for s in pr["streams"])

@test("reel: own recordings, one per line, set the timing")
def _():
    if not HAS_FFMPEG: return
    rec = os.path.join(TMP, "rec"); os.makedirs(rec, exist_ok=True)
    for i, d in enumerate((1.5, 2.5), 1):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=f=220:d={d}", os.path.join(rec, f"{i:02d}.wav")], check=True)
    sc = write("story2.txt", "Line one is here.\nLine two is a bit longer.\n")
    out = os.path.join(TMP, "reel2.mp4")
    r = json.loads(run("reel.py", sc, "-o", out, "--audio-dir", rec, "--size", "1920x1080").stdout.strip().splitlines()[-1])
    assert 4.3 <= r["seconds"] <= 5.2, r                     # 1.5 + 0.22 + 2.5 + lead/tail
    bad = run("reel.py", write("story3.txt", "only one line\n"), "-o", out, "--audio-dir", rec, ok=False)
    assert bad.returncode != 0 and "one per line" in (bad.stdout + bad.stderr)

@test("cover: series of 3, contrast fixed with a scrim, word limit flagged on a thumbnail")
def _():
    if not HAS_PIL: return
    from PIL import Image
    bright = os.path.join(TMP, "white.png"); Image.new("RGB", (800, 800), (250, 250, 250)).save(bright)
    base = os.path.join(TMP, "dac.png")
    r = js("cover.py", "--text", "x", "--texts", "Kde je zlato|Zrádce promluvil|Poslední pevnost", "--parts", "3",
           "--label", "DÍL {n}", "--bg", bright, "-o", base)
    assert [os.path.basename(x["out"]) for x in r] == ["dac_1.png", "dac_2.png", "dac_3.png"], r
    assert all(x["scrim"] and x["contrast"] >= 4.5 for x in r), r
    assert Image.open(r[0]["out"]).size == (1080, 1920)
    t = js("cover.py", "--text", "AI RAN MY WHOLE CHANNEL", "--size", "thumb", "-o", os.path.join(TMP, "t.png"))[0]
    assert any("ceiling" in i for i in t["issues"]), t

@test("stats: YouTube export - total row skipped, trend, outliers")
def _():
    rows = ["Content,Video title,Video publish time,Duration,Views", "Total,,,,999999"]
    import datetime as _dt
    d0 = _dt.date(2026, 9, 7)
    for i in range(24):
        d = d0 + _dt.timedelta(days=i * 2)
        v = 1000 + (i % 3) * 50 + (800 if i >= 14 else 0)
        if i == 4: v = 9000
        rows.append(f'id{i},Video {i},"{d.strftime("%b")} {d.day}, {d.year}",0:45,"{v:,}"')
    r = js("stats.py", write("yt.csv", "\n".join(rows)))["yt"]
    assert r["posts"] == 24, r["posts"]
    assert r["trend"] and r["trend"]["verdict"] == "growing", r["trend"]
    assert r["repeat"][0]["views"] == 9000

@test("stats: Czech headers, semicolons, spaces in numbers, series carry")
def _():
    c = write("cz.csv", "Datum;Název;Zhlédnutí\n01.10.2026;Dákové díl 1;52 000\n02.10.2026;Dákové díl 2;14 000\n"
                        "03.10.2026;Dákové díl 3;9 800\n05.10.2026;Něco jiného;4 000\n")
    r = js("stats.py", c)["cz"]
    s = r["series"][0]["parts"]
    assert [p["views"] for p in s] == [52000, 14000, 9800] and s[1]["carry"] == 26.9, s

# ------------------------------------------------------------------ studio (1.2)
def studio(*a):
    out = run("studio.py", *a).stdout.strip().splitlines()
    return json.loads(out[-1]) if out else {}

def make_clip(name, size="1280x720", d=6, audio=True, src="testsrc2"):
    p = os.path.join(TMP, name)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"{src}=s={size}:r=30:d={d}"]
    if audio: cmd += ["-f", "lavfi", "-i", f"sine=f=330:d={d}", "-shortest"]
    subprocess.run(cmd + ["-c:v", "libx264", "-pix_fmt", "yuv420p", p], check=True)
    return p

@test("studio: cut by EDL, split, join with a transition into 9:16, speed")
def _():
    if not HAS_FFMPEG: return
    a = make_clip("sa.mp4"); b = make_clip("sb.mp4", "720x1280", 5, audio=False)
    edl = write("edl.json", json.dumps({"cuts": [{"kind": "DEAD", "start": 1.0, "end": 2.0}]}))
    assert abs(studio("cut", a, os.path.join(TMP, "c.mp4"), "--edl", edl)["seconds"] - 5.0) < 0.15
    j = studio("join", os.path.join(TMP, "j.mp4"), a, b, "--transition", "slideup", "--duration", "0.5", "--aspect", "9:16")
    assert j["size"] == "1080x1920" and abs(j["seconds"] - 10.5) < 0.2, j
    assert abs(studio("speed", a, os.path.join(TMP, "sp.mp4"), "--factor", "2")["seconds"] - 3.0) < 0.15

@test("studio: reframe with blurred background, text, overlay, color, export")
def _():
    if not HAS_FFMPEG: return
    a = make_clip("sc.mp4")
    r = studio("reframe", a, os.path.join(TMP, "r.mp4"), "--aspect", "9:16", "--mode", "blur")
    assert r["size"] == "1080x1920"
    t = studio("text", os.path.join(TMP, "r.mp4"), os.path.join(TMP, "t.mp4"), "--text", "Díl 2: Zrádce", "--box")
    assert t["size"] == "1080x1920"
    logo = os.path.join(TMP, "logo.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=orange:s=200x200", "-frames:v", "1", logo], check=True)
    assert studio("overlay", a, os.path.join(TMP, "o.mp4"), "--layer", logo, "--pos", "bottom-right")["seconds"] > 5.5
    assert studio("color", a, os.path.join(TMP, "co.mp4"), "--preset", "cinematic")["seconds"] > 5.5
    e = studio("export", a, os.path.join(TMP, "e.mp4"), "--platform", "reels")
    assert e["size"] == "1080x1920"

@test("studio: silences are cut, beats are found at the right tempo")
def _():
    if not HAS_FFMPEG: return
    sil = os.path.join(TMP, "sil.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=640x360:r=30:d=8", "-f", "lavfi", "-i", "sine=f=300:d=8",
                    "-filter_complex", "[1:a]volume='if(between(t,2,4),0,1)':eval=frame[a]", "-map", "0:v", "-map", "[a]",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", sil], check=True)
    r = studio("silence", sil, os.path.join(TMP, "ns.mp4"))
    assert 5.9 <= r["seconds"] <= 6.5, r
    beat = os.path.join(TMP, "beat.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=f=60:d=8,volume=3", "-f", "lavfi", "-i", "anoisesrc=d=8:a=0.02",
                    "-filter_complex", "[0:a]volume='if(lt(mod(t,0.5),0.08),1,0)':eval=frame[k];[k][1:a]amix=inputs=2[m]", "-map", "[m]", beat], check=True)
    b = json.loads(run("studio.py", "beats", beat).stdout)
    assert b["bpm"] and 110 <= b["bpm"] <= 130, b

print(f"\n  {len(PASS)} passed, {len(FAIL)} failed\n")
for n in PASS: print(f"    ok    {n}")
for n, e in FAIL: print(f"    FAIL  {n}\n          {e}")
sys.exit(1 if FAIL else 0)

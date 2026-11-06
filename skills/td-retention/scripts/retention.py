#!/usr/bin/env python3
"""retention.py - find where viewers leave, on YouTube, Shorts, TikTok or Instagram.

    python3 retention.py retention.csv --duration 600                 # YouTube Studio export
    python3 retention.py retention.csv --duration 45 --platform shorts
    python3 retention.py --points "0:100,1:88,3:61,10:44,30:30,45:22" --platform tiktok
    python3 retention.py retention.csv --duration 600 --transcript video.srt   # what you said at each drop
    python3 retention.py retention.csv --duration 600 --json

Where the data comes from:
  YouTube / Shorts  Studio -> the video -> Analytics -> Engagement -> audience retention -> the
                    download icon. Any CSV with a position column and a retention column works;
                    fractions (0.62) and percentages (62%) are both read.
  TikTok            TikTok Studio -> the video -> Analytics -> retention chart. There is no export:
                    read 6-10 points off the chart and pass them with --points "second:percent,...".
  Instagram         Professional dashboard -> the Reel -> Insights -> the retention graph. Same as
                    TikTok - read the points off and pass --points.

Three different problems, three different fixes:
  HOOK LEAK   what is lost inside the platform's hook window (30 s long-form, 3 s short-form).
              The fix is always the opening - script and on-screen text - never the edit.
  CLIFFS      single steep drops: a moment. A topic change with no signpost, a long setup, a
              sponsor read, a scene that resolves the question too early.
  SLIDE       the steady bleed through the middle, per 10% of runtime. Pacing: cut, do not rewrite.
"""
import argparse, csv, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
PLATFORMS = json.load(open(os.path.join(HERE, "platforms.json"), encoding="utf-8"))

POS_HINT = re.compile(r"position|pozice|позиц|pozi|time|čas|время|timp|second", re.I)
RET_HINT = re.compile(r"retention|udržen|удержан|reten|audience|publikum|watching", re.I)

def num(c):
    c = (c or "").strip().replace("%", "").replace(" ", "").replace(" ", "")
    if c.count(",") == 1 and "." not in c: c = c.replace(",", ".")
    c = c.replace(",", "")
    m = re.match(r"^(\d+):(\d+(?:\.\d+)?)$", c)  # 1:30 style positions
    if m: return int(m.group(1)) * 60 + float(m.group(2))
    try: return float(c)
    except ValueError: return None

def load_csv(path):
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as fh:
        sample = fh.read(4096); fh.seek(0)
        try: dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error: dialect = csv.excel
        rows = list(csv.reader(fh, dialect))
    xi = yi = None
    for r in rows[:5]:
        for i, c in enumerate(r):
            if xi is None and POS_HINT.search(c or ""): xi = i
            elif yi is None and RET_HINT.search(c or "") and i != xi: yi = i
        if xi is not None and yi is not None: break
    pts = []
    for r in rows:
        if xi is not None and yi is not None and max(xi, yi) < len(r):
            x, y = num(r[xi]), num(r[yi])
        else:
            vals = [v for v in (num(c) for c in r) if v is not None]
            x, y = (vals[0], vals[1]) if len(vals) >= 2 else (None, None)
        if x is not None and y is not None: pts.append((x, y))
    return pts

def parse_points(s):
    pts = []
    for part in s.split(","):
        if ":" not in part: continue
        x, y = part.rsplit(":", 1)
        xv, yv = num(x), num(y)
        if xv is not None and yv is not None: pts.append((xv, yv))
    return pts

def analyse(pts, duration=None, platform="youtube"):
    pts = sorted(pts)
    if max(y for _, y in pts) <= 1.5:  # fractions, not percentages
        pts = [(x, y * 100) for x, y in pts]
    xmax = max(p[0] for p in pts)
    if xmax <= 1.01:                       # position as a fraction of the video
        pts = [(x * 100, y) for x, y in pts]; xmax *= 100; pct_axis = True
    elif duration:                         # seconds if the axis ends near the runtime, else percent
        pct_axis = not (abs(xmax - duration) <= duration * 0.15) and xmax <= 100.5
    else:
        pct_axis = 99 <= xmax <= 100.5     # an axis ending at exactly 100 is almost always percent
    if pct_axis and not duration:
        return {"error": "positions look like percentages - pass --duration in seconds"}
    if pct_axis:
        pts = [(x / 100.0 * duration, y) for x, y in pts]
    dur = duration or pts[-1][0]
    cfg = PLATFORMS.get(platform, PLATFORMS["youtube"])
    window = cfg["hook_window_s"]
    start = pts[0][1] or 100.0
    in_window = [y for x, y in pts if x <= window + 1e-9]
    after = [y for x, y in pts if x > window]
    hook_end = in_window[-1] if in_window else start
    if len(in_window) < 2 and after:  # no point inside the window: interpolate to it
        (x0, y0) = max(((x, y) for x, y in pts if x <= window), default=pts[0])
        (x1, y1) = min(((x, y) for x, y in pts if x > window), default=pts[-1])
        hook_end = y0 + (y1 - y0) * ((window - x0) / ((x1 - x0) or 1))
    hook_leak = start - hook_end
    drops = []
    for i in range(1, len(pts)):
        d = pts[i - 1][1] - pts[i][1]
        span = (pts[i][0] - pts[i - 1][0]) or 1
        if pts[i - 1][0] >= window and d > 0:
            drops.append({"from_s": round(pts[i - 1][0], 1), "to_s": round(pts[i][0], 1),
                          "lost": round(d, 2), "per_s": round(d / span, 3)})
    mid = [p for p in pts if window < p[0] < dur * 0.9]
    slide = None
    if len(mid) >= 2 and mid[-1][0] > mid[0][0]:
        slide = (mid[0][1] - mid[-1][1]) / ((mid[-1][0] - mid[0][0]) / dur * 10)
    typical = sorted(d["per_s"] for d in drops)[len(drops) // 2] if drops else 0
    cliffs = sorted((d for d in drops if d["per_s"] > max(typical * 2.5, 0.0) and d["lost"] >= 1.5),
                    key=lambda d: -d["per_s"])[:5]
    return {"platform": platform, "duration": round(dur, 1), "points": len(pts), "start": round(start, 1),
            "end": round(pts[-1][1], 1), "hook_window_s": window, "hook_leak": round(hook_leak, 1),
            "cliffs": cliffs, "slide_per_10pct": round(slide, 2) if slide is not None else None}

def verdict(r):
    p = r["platform"]
    leak = r["hook_leak"]
    if p == "youtube":
        return "healthy" if leak < 25 else "leaking" if leak < 40 else "severe"
    # short-form: the first 3 s decide everything; these bands are rough, your own median beats them
    return "healthy" if leak < 30 else "leaking" if leak < 50 else "severe"

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="?")
    ap.add_argument("--points", help='"second:percent,..." read off a TikTok / Instagram chart')
    ap.add_argument("--duration", type=float, help="video length in seconds")
    ap.add_argument("--platform", default="youtube", choices=["youtube", "shorts", "tiktok", "instagram"])
    ap.add_argument("--transcript")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.points: pts = parse_points(a.points)
    elif a.csv and os.path.exists(a.csv): pts = load_csv(a.csv)
    else: ap.error("give a CSV file or --points")
    if len(pts) < 4: print("need at least 4 data points"); sys.exit(1)
    r = analyse(pts, a.duration, a.platform)
    if "error" in r: print(r["error"]); sys.exit(1)
    said = {}
    if a.transcript and os.path.exists(a.transcript):
        from transcript import load
        cues = load(a.transcript)
        for c in r["cliffs"]:
            near = [q[2] for q in cues if q[0] <= c["to_s"] + 2 and q[1] >= c["from_s"] - 3]
            said[c["from_s"]] = " ".join(near)[:160]
            c["said"] = said[c["from_s"]]
    r["hook_verdict"] = verdict(r)
    if a.json: print(json.dumps(r, ensure_ascii=False, indent=1)); return
    name = PLATFORMS[a.platform]["name"]
    print(f"\n  {name}   {r['points']} points   {r['start']:.0f}% -> {r['end']:.0f}%   {r['duration']:.0f}s\n")
    print(f"  HOOK LEAK   {r['hook_leak']:.1f}% lost in the first {r['hook_window_s']} s   [{r['hook_verdict']}]")
    print("              fix the first line and the first on-screen text before anything else.\n")
    print("  CLIFFS      moments people actually left")
    for c in r["cliffs"]:
        print(f"    -{c['lost']:5.1f}%  {c['from_s']:6.1f}s -> {c['to_s']:6.1f}s" +
              (f'   "{c["said"]}"' if c.get("said") else ""))
    if not r["cliffs"]: print("    none - the loss after the hook is steady slide, not moments")
    if r["slide_per_10pct"] is not None:
        print(f"\n  SLIDE       {r['slide_per_10pct']:.1f}% lost per 10% of runtime through the middle")
        print("              a steep slide is pacing - cut, do not rewrite.")
    print("\n  Benchmarks here are rough. Your own account's median video is the real baseline.\n")

if __name__ == "__main__":
    main()

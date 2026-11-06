#!/usr/bin/env python3
"""series.py - multi-part series: where the audience falls off, and where to cut the next one.

Two jobs.

1) STATS - how many viewers each part keeps from the one before.

    python3 series.py stats --views "1:120000,2:41000,3:30500,4:22000"
    python3 series.py stats parts.csv            # columns: part, views[, completion %][, platform]
    python3 series.py stats --views "..." --json

   Prints the carry rate part-to-part (views of part N / views of part N-1), the single worst
   handoff, and what share of part 1's audience reaches the finale. With a completion column it
   also says whether a drop is the PREVIOUS part's ending (low completion) or the new part's
   packaging (people finished, but did not come back).

2) SPLIT - where to cut one long story into N parts that each end on a hook.

    python3 series.py split story.srt --parts 3
    python3 series.py split story.srt --parts 3 --platform tiktok --json

   Picks cut points near equal lengths at real pauses, preferring a last line that leaves a
   question open (a "but", a question, a conflict) and avoiding one that resolves it ("so", "because").
   Every part is checked against the platform's length ceiling. It never adds a recap or a teaser to
   the start of a part - the next part starts where the last one stopped.
"""
import argparse, csv, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lang as L  # noqa: E402
from transcript import load, mmss  # noqa: E402

PLATFORMS = json.load(open(os.path.join(HERE, "platforms.json"), encoding="utf-8"))
MAXLEN = {"youtube": None, "shorts": PLATFORMS["shorts"]["max_seconds"],
          "tiktok": PLATFORMS["tiktok"]["max_seconds_app"],
          "instagram": PLATFORMS["instagram"]["max_seconds_reels_tab"]}

# ---------------------------------------------------------------- stats
def parse_views(s):
    out = []
    for p in s.split(","):
        if ":" in p:
            k, v = p.split(":", 1)
            out.append({"part": int(k), "views": float(v.replace(" ", ""))})
    return out

def load_parts(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            low = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
            part = next((low[k] for k in low if k in ("part", "díl", "dil", "часть", "partea")), None)
            views = next((low[k] for k in low if "view" in k or "zhlédn" in k or "просмотр" in k or "vizual" in k), None)
            comp = next((low[k] for k in low if "complet" in k or "dokonč" in k or "досмотр" in k or "full" in k), None)
            if part and views:
                row = {"part": int(re.sub(r"\D", "", part)), "views": float(re.sub(r"[^\d.]", "", views))}
                if comp: row["completion"] = float(re.sub(r"[^\d.]", "", comp))
                rows.append(row)
    return rows

def stats(parts):
    parts = sorted(parts, key=lambda p: p["part"])
    first = parts[0]["views"] or 1
    out = []
    for i, p in enumerate(parts):
        row = dict(p)
        row["of_part1"] = round(p["views"] / first * 100, 1)
        if i:
            prev = parts[i - 1]["views"] or 1
            row["carry"] = round(p["views"] / prev * 100, 1)
        out.append(row)
    handoffs = [r for r in out if "carry" in r]
    worst = min(handoffs, key=lambda r: r["carry"]) if handoffs else None
    diag = None
    if worst and "completion" in worst and any("completion" in r for r in out):
        prev = next(r for r in out if r["part"] == worst["part"] - 1)
        if "completion" in prev:
            med = sorted(r["completion"] for r in out if "completion" in r)[len(out) // 2]
            diag = ("ENDING: part %d lost its viewers before the end (completion %.0f%% vs median %.0f%%) - "
                    "the drop is that part's last third, not part %d's packaging."
                    % (prev["part"], prev["completion"], med, worst["part"])) if prev["completion"] < med * 0.85 else \
                   ("HANDOFF: part %d was finished, but people did not come back for part %d - "
                    "the problem is the link between them: the last line, the 'part %d' cover, posting gap."
                    % (prev["part"], worst["part"], worst["part"]))
    return {"parts": out, "worst": worst, "finale_share": out[-1]["of_part1"], "diagnosis": diag}

# ---------------------------------------------------------------- split
def end_hook_score(line, lg):
    s = 0.0
    t = line.strip()
    if t.endswith("?"): s += 2
    s += 1.2 * min(2, L.count(t, lg, "curiosity"))
    s += 1.0 * min(2, L.count(t, lg, "conflict"))
    s += 0.8 * min(2, L.count(t, lg, "stake"))
    s -= 1.5 * min(1, L.count(t, lg, "closed"))
    if t.endswith(("...", "…", "—", "-")): s += 1
    return s

def split(cues, n, lg, platform="tiktok"):
    dur = cues[-1][1]
    ideal = [dur * k / n for k in range(1, n)]
    tol = dur / n * 0.25
    chosen = []
    for target in ideal:
        best, best_s = None, -1e9
        for i in range(1, len(cues)):
            t = cues[i][0]
            if abs(t - target) > tol or any(abs(t - c) < dur / n * 0.5 for c in chosen): continue
            gap = t - cues[i - 1][1]
            s = end_hook_score(cues[i - 1][2], lg) + min(gap, 1.5) * 1.5 - abs(t - target) / tol * 1.5
            if s > best_s: best, best_s = i, s
        if best is None:  # no pause near the target: take the nearest cue start
            best = min(range(1, len(cues)), key=lambda i: abs(cues[i][0] - target))
        chosen.append(cues[best][0])
    bounds = [0.0] + sorted(chosen) + [dur]
    parts, ceiling = [], MAXLEN.get(platform)
    for k in range(n):
        a, b = bounds[k], bounds[k + 1]
        inside = [c for c in cues if c[0] >= a and c[0] < b]
        last = inside[-1][2] if inside else ""
        first = inside[0][2] if inside else ""
        flags = []
        if ceiling and b - a > ceiling: flags.append(f"over the {ceiling}s {platform} ceiling by {b - a - ceiling:.0f}s")
        if k < n - 1 and end_hook_score(last, lg) <= 0: flags.append("last line resolves - move the cut or rewrite the line so it opens a question")
        if L.count(last, lg, "closed") and k < n - 1: flags.append("last line explains instead of leaving a gap")
        parts.append({"part": k + 1, "start": round(a, 2), "end": round(b, 2), "label": f"{mmss(a)}-{mmss(b)}",
                      "seconds": round(b - a, 1), "first_line": first, "last_line": last,
                      "end_hook": round(end_hook_score(last, lg), 2), "flags": flags})
    return parts

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s1 = sub.add_parser("stats"); s1.add_argument("csv", nargs="?"); s1.add_argument("--views"); s1.add_argument("--json", action="store_true")
    s2 = sub.add_parser("split"); s2.add_argument("transcript"); s2.add_argument("--parts", type=int, default=3)
    s2.add_argument("--platform", default="tiktok", choices=list(MAXLEN)); s2.add_argument("--lang", choices=L.LANGS)
    s2.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.cmd == "stats":
        parts = parse_views(a.views) if a.views else (load_parts(a.csv) if a.csv and os.path.exists(a.csv) else None)
        if not parts or len(parts) < 2: s1.error("need at least 2 parts: --views \"1:1000,2:400\" or a CSV")
        r = stats(parts)
        if a.json: print(json.dumps(r, ensure_ascii=False, indent=1)); return
        print("\n  part      views   of part 1   carry from previous")
        for p in r["parts"]:
            carry = f"{p['carry']:5.1f}%" if "carry" in p else "    -"
            comp = f"   completion {p['completion']:.0f}%" if "completion" in p else ""
            print(f"  {p['part']:>4} {p['views']:>10,.0f}   {p['of_part1']:6.1f}%      {carry}{comp}")
        w = r["worst"]
        print(f"\n  worst handoff: part {w['part'] - 1} -> {w['part']}, kept {w['carry']:.0f}%")
        print(f"  {r['finale_share']:.0f}% of part 1's audience reached the last part")
        if r["diagnosis"]: print("  " + r["diagnosis"])
        print("  Every handoff loses people. Fewer, longer parts beat more, shorter ones when carry is under ~50%.\n")
        return
    if not os.path.exists(a.transcript): s2.error(f"no such file: {a.transcript}")
    cues = load(a.transcript)
    if len(cues) < a.parts * 3: print("transcript too short for that many parts"); sys.exit(1)
    lg = a.lang or L.detect(" ".join(c[2] for c in cues[:200]))
    parts = split(cues, a.parts, lg, a.platform)
    if a.json: print(json.dumps({"lang": lg, "platform": a.platform, "parts": parts}, ensure_ascii=False, indent=1)); return
    print(f"\n  {a.parts} parts for {a.platform}, lang {lg}\n")
    for p in parts:
        print(f"  PART {p['part']}  {p['label']}  ({p['seconds']:.0f}s)   end-hook {p['end_hook']:+.1f}")
        print(f"    opens:  {p['first_line'][:90]}")
        print(f"    ends:   {p['last_line'][:90]}")
        for f in p["flags"]: print(f"    !  {f}")
    print("\n  No recap, no teaser: each part starts exactly where the last one stopped.\n")

if __name__ == "__main__":
    main()

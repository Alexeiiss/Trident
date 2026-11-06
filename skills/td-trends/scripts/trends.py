#!/usr/bin/env python3
"""trends.py - rank collected videos by how far each beat its OWN account, then name the formula.

    python3 trends.py collected.json
    python3 trends.py a.json b.json --min 2.0 --json
    python3 trends.py collected.json --split-shorts --per-day

Input - any of:
  * a list you collected:  [{"channel":"...","title":"...","views":412000,"url":"...","duration":613,
                             "upload_date":"20261020", "platform":"youtube"}, ...]
  * yt-dlp output for a channel / TikTok profile / Instagram profile:
        yt-dlp --flat-playlist -J "https://www.youtube.com/@channel/videos" > a.json
        yt-dlp -J --flat-playlist "https://www.tiktok.com/@handle" > b.json
    (fields view_count, title, url, duration, upload_date/timestamp, channel/uploader are read)
  * JSON Lines from `yt-dlp -j` (one video per line)

Raw views rank account size, not ideas. Every video is scored as a MULTIPLE OF ITS OWN ACCOUNT'S
MEDIAN (min 4 videos per account, or the tool says so and skips it).

--split-shorts  computes separate medians for short (<=180 s) and long videos on the same channel;
                otherwise a Shorts-heavy channel makes every long video look like a flop.
--per-day       divides views by days since upload before the median, so a two-year-old video does
                not beat a two-week-old one on time alone (needs upload_date or timestamp).

The formula is matched against the TITLE / caption (hooks.json, all four languages). It is a
judgement about the words, not a claim about why the video worked.
"""
import argparse, datetime, json, os, re, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lang as L  # noqa: E402
FORMULAS = json.load(open(os.path.join(HERE, "hooks.json"), encoding="utf-8"))["hooks"]

def classify(title):
    lg = L.detect(title)
    best, n0 = "Unclassified", 0
    for f in FORMULAS:
        pats = list(f["match"]) + list(f.get("i18n", {}).get(lg, []))
        n = sum(1 for p in pats if re.search(p, title or "", re.I))
        if n > n0: best, n0 = f["name"], n
    return best

def platform_of(url, extractor=""):
    u = (url or "") + " " + (extractor or "")
    if "tiktok" in u: return "tiktok"
    if "instagram" in u: return "instagram"
    return "youtube"

def normalise(v, parent=None):
    parent = parent or {}
    views = v.get("views", v.get("view_count", v.get("play_count")))
    if views is None: return None
    date = v.get("upload_date") or parent.get("upload_date")
    ts = v.get("timestamp")
    if not date and ts:
        date = datetime.datetime.utcfromtimestamp(float(ts)).strftime("%Y%m%d")
    url = v.get("url") or v.get("webpage_url") or ""
    return {"channel": v.get("channel") or v.get("uploader") or v.get("channel_id") or parent.get("channel")
                       or parent.get("uploader") or parent.get("title") or "?",
            "title": v.get("title") or v.get("description") or "",
            "views": float(views or 0), "url": url, "duration": v.get("duration"),
            "upload_date": date,
            "platform": v.get("platform") or platform_of(url, v.get("ie_key") or v.get("extractor") or parent.get("extractor", ""))}

def read_any(path):
    raw = open(path, encoding="utf-8").read().strip()
    out = []
    try:
        d = json.loads(raw)
        docs = [d]
    except json.JSONDecodeError:
        docs = [json.loads(l) for l in raw.splitlines() if l.strip()]
    for d in docs:
        if isinstance(d, list):
            out += [x for x in (normalise(v) for v in d) if x]
        elif isinstance(d, dict) and "entries" in d:
            for e in d["entries"] or []:
                if isinstance(e, dict) and "entries" in e:   # channel -> tabs -> videos
                    out += [x for x in (normalise(v, e) for v in e["entries"] or []) if x]
                elif isinstance(e, dict):
                    x = normalise(e, d)
                    if x: out.append(x)
        elif isinstance(d, dict) and "videos" in d:
            out += [x for x in (normalise(v) for v in d["videos"]) if x]
        elif isinstance(d, dict):
            x = normalise(d)
            if x: out.append(x)
    return out

def days_since(date):
    try:
        d = datetime.datetime.strptime(str(date)[:8], "%Y%m%d")
        return max(1, (datetime.datetime.utcnow() - d).days)
    except (ValueError, TypeError):
        return None

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--min", type=float, default=1.5)
    ap.add_argument("--split-shorts", action="store_true")
    ap.add_argument("--per-day", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    rows = []
    for f in a.files:
        if not os.path.exists(f): ap.error(f"no such file: {f}")
        rows += read_any(f)
    if not rows:
        print("no videos with a view count found - for yt-dlp use -J (or -j), and check the file is not empty"); sys.exit(1)
    groups, missing_date = {}, 0
    for r in rows:
        score = r["views"]
        if a.per_day:
            d = days_since(r["upload_date"])
            if d is None: missing_date += 1; continue
            score = r["views"] / d
        r["score"] = score
        kind = ("short" if (r["duration"] or 0) and float(r["duration"]) <= 180 else "long") if a.split_shorts else "all"
        if r["platform"] in ("tiktok", "instagram") and a.split_shorts: kind = "short"
        groups.setdefault((r["platform"], r["channel"], kind), []).append(r)
    out, thin = [], []
    for (pf, ch, kind), vids in groups.items():
        if len(vids) < 4: thin.append((f"{ch} [{pf}{'/' + kind if kind != 'all' else ''}]", len(vids))); continue
        med = statistics.median(v["score"] for v in vids)
        for v in vids:
            m = v["score"] / med if med else 0
            out.append({"platform": pf, "channel": ch, "kind": kind, "title": v["title"][:120],
                        "views": int(v["views"]), "multiple": round(m, 2), "formula": classify(v["title"]),
                        "url": v["url"], "upload_date": v["upload_date"]})
    out = sorted((r for r in out if r["multiple"] >= a.min), key=lambda r: -r["multiple"])
    if a.json:
        print(json.dumps({"outliers": out, "skipped_thin": thin, "missing_date": missing_date}, ensure_ascii=False, indent=1)); return
    basis = "views/day" if a.per_day else "views"
    print(f"\n  {len(rows)} videos, {len(groups)} account groups, outliers at {a.min}x their own median {basis}\n")
    for r in out[:25]:
        print(f"    {r['multiple']:5.2f}x  {r['views']:>10,}  {r['platform'][:2]}  {r['channel'][:20]:<20} {r['title'][:56]}")
        print(f"            {r['formula']}")
    if not out: print("    nothing cleared the threshold - collect more per account or lower --min")
    if thin:
        print(f"\n  skipped {len(thin)} group(s) with under 4 videos - a median of two is not a median: "
              + ", ".join(f"{c} ({n})" for c, n in thin[:6]))
    if missing_date: print(f"  {missing_date} video(s) had no upload date and were left out of --per-day")
    counts = {}
    for r in out: counts[r["formula"]] = counts.get(r["formula"], 0) + 1
    if counts:
        print("\n  formulas among the outliers")
        for f, n in sorted(counts.items(), key=lambda x: -x[1]): print(f"    {n:2d}x  {f}")
    print()

if __name__ == "__main__":
    main()

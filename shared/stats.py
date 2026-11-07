#!/usr/bin/env python3
"""stats.py - how each account is really doing, week by week, from the platforms' own exports.

    python3 stats.py youtube_table_data.csv                       # YouTube Studio export
    python3 stats.py tiktok.csv --account "@istorieascunsa"       # any CSV with date / title / views
    python3 stats.py yt.csv tt.csv ig.csv --weeks 8               # several accounts side by side
    python3 stats.py posts.json --json                            # [{"date","title","views",...}]

Where the files come from:
  YouTube    Studio -> Analytics -> Advanced mode -> Content, pick the period -> Export -> CSV.
             Use "Table data.csv" from the zip. The "Total" row is skipped.
  TikTok     TikTok Studio -> Analytics -> Content: there is no per-video export everywhere, so a
             CSV you keep yourself works: date,title,views,likes,comments,shares,avg_watch_s,duration_s
  Instagram  Professional dashboard -> Insights, or Meta Business Suite -> Insights -> Content ->
             Export. Same columns as above are recognised.
  Column names are matched loosely in English, Czech, Russian and Romanian ("Zhlédnutí",
  "Просмотры", "Vizualizări", "Video publish time", "Datum"...).

What it reports, per account:
  * every week: posts, total views, median views per post (the median, because one viral post
    hides nine dead ones in an average)
  * the trend: median views of the last 4 weeks vs the 4 before, with a plain verdict
  * outliers: posts at 2x+ the account median and posts under 0.3x - what to repeat, what to drop
  * series: titles with "Part 2", "Díl 2", "Часть 2", "Partea 2", "#2"... are grouped, and the
    part-to-part carry is shown (see series.py for the full diagnosis)
  * best posting weekday, only when there are at least 20 posts - fewer is noise and it says so
"""
import argparse, csv, datetime as dt, json, os, re, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))

COLS = {
 "date": ["publish time", "publish date", "post time", "posted", "date", "datum", "čas publikování", "zveřejněno",
          "publikováno", "дата", "опубликовано", "data", "publicat", "time"],
 "title": ["video title", "title", "název", "nazev", "caption", "description", "popis", "название", "заголовок",
           "titlu", "descriere", "content"],
 "views": ["views", "video views", "total views", "plays", "zhlédnutí", "zhlednuti", "přehrání", "просмотры",
           "просмотров", "vizualizări", "vizualizari", "reach"],
 "likes": ["likes", "like", "to se mi líbí", "лайки", "aprecieri"],
 "comments": ["comments", "komentáře", "комментарии", "comentarii"],
 "shares": ["shares", "sdílení", "репосты", "distribuiri"],
 "duration": ["duration", "délka", "длительность", "durată", "duration_s"],
 "avg_watch": ["average view duration", "avg_watch_s", "average watch time", "průměrná doba sledování",
               "среднее время просмотра", "durata medie"],
}
MONTHS = {m: i + 1 for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}
PART = re.compile(r"(?:\b(?:part|pt|díl|dil|část|cast|часть|серия|partea|episod|ep)\.?\s*(\d+)|#\s?(\d+)\b|\((\d+)\s*/\s*\d+\)|\b(\d+)\s*/\s*\d+\b)", re.I)

def num(s):
    if s is None: return None
    s = str(s).strip().replace(" ", "").replace(" ", "")
    m = re.match(r"^(\d+(?:[.,]\d+)?)\s*([kKmM])$", s)
    if m:
        return float(m.group(1).replace(",", ".")) * (1000 if m.group(2).lower() == "k" else 1_000_000)
    if re.match(r"^\d+:\d{2}(:\d{2})?$", s):
        p = [int(x) for x in s.split(":")]; return p[0] * 60 + p[1] if len(p) == 2 else p[0] * 3600 + p[1] * 60 + p[2]
    if s.count(",") and s.count("."): s = s.replace(",", "")
    elif s.count(",") == 1 and len(s.split(",")[1]) != 3: s = s.replace(",", ".")
    else: s = s.replace(",", "")
    try: return float(s)
    except ValueError: return None

def date(s):
    if not s: return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d.%m.%Y", "%d.%m.%Y %H:%M",
                "%d. %m. %Y", "%m/%d/%Y", "%d/%m/%Y", "%Y%m%d"):
        try: return dt.datetime.strptime(s[:len(dt.datetime.now().strftime(fmt))] if "%H" not in fmt else s, fmt)
        except ValueError: pass
    m = re.match(r"^([A-Za-z]{3})[a-z]*\.?\s+(\d{1,2}),?\s+(\d{4})", s)         # Nov 3, 2026
    if m and m.group(1).lower() in MONTHS: return dt.datetime(int(m.group(3)), MONTHS[m.group(1).lower()], int(m.group(2)))
    m = re.match(r"^(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})", s)
    if m: return dt.datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m: return dt.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None

def match_cols(header):
    low = [(h or "").strip().lower() for h in header]
    found = {}
    for key, names in COLS.items():
        for n in names:                                   # exact first, then contains
            for i, h in enumerate(low):
                if h == n and i not in found.values(): found.setdefault(key, i)
        if key not in found:
            for n in names:
                for i, h in enumerate(low):
                    if n in h and i not in found.values() and key not in found: found[key] = i
    return found

def load(path):
    if path.lower().endswith(".json"):
        rows = json.load(open(path, encoding="utf-8"))
        if isinstance(rows, dict): rows = rows.get("posts") or rows.get("videos") or []
        return [{"date": date(r.get("date") or r.get("upload_date")), "title": r.get("title", ""),
                 "views": num(r.get("views", r.get("view_count"))), **{k: num(r.get(k)) for k in ("likes", "comments", "shares", "duration", "avg_watch")}}
                for r in rows]
    with open(path, newline="", encoding="utf-8-sig") as fh:
        sample = fh.read(4096); fh.seek(0)
        try: dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error: dialect = csv.excel
        rows = list(csv.reader(fh, dialect))
    if not rows: return []
    cols = match_cols(rows[0])
    if "views" not in cols: sys.exit(f"{path}: no views column found in {rows[0]}")
    out = []
    for r in rows[1:]:
        if not any(r): continue
        g = lambda k: r[cols[k]] if k in cols and cols[k] < len(r) else None
        if (g("title") or "").strip().lower() in ("total", "celkem", "итого", "celkový součet"): continue
        if (r[0] or "").strip().lower() == "total": continue
        out.append({"date": date(g("date")), "title": (g("title") or "").strip(), "views": num(g("views")),
                    **{k: num(g(k)) for k in ("likes", "comments", "shares", "duration", "avg_watch")}})
    return [p for p in out if p["views"] is not None]

def week_key(d): y, w, _ = d.isocalendar(); return f"{y}-W{w:02d}"

def series_groups(posts):
    groups = {}
    for p in posts:
        m = PART.search(p["title"] or "")
        if not m: continue
        n = int(next(g for g in m.groups() if g))
        base = PART.sub("", p["title"]).strip(" -|:–—#()").lower()
        base = re.sub(r"\s+", " ", base)[:60]
        groups.setdefault(base, {})[n] = p["views"]
    out = []
    for base, parts in groups.items():
        if len(parts) < 2: continue
        ks = sorted(parts)
        carry = [{"part": k, "views": int(parts[k]), "carry": round(parts[k] / parts[ks[i - 1]] * 100, 1) if i and parts[ks[i - 1]] else None}
                 for i, k in enumerate(ks)]
        out.append({"series": base, "parts": carry})
    return out

def analyse(posts, weeks=8, today=None):
    dated = [p for p in posts if p["date"]]
    today = today or (max(p["date"] for p in dated) if dated else dt.datetime.now())
    allv = [p["views"] for p in posts]
    med = statistics.median(allv) if allv else 0
    wk = {}
    for p in dated: wk.setdefault(week_key(p["date"]), []).append(p["views"])
    keys = sorted(wk)[-weeks:]
    table = [{"week": k, "posts": len(wk[k]), "views": int(sum(wk[k])), "median": int(statistics.median(wk[k]))} for k in keys]
    cut1, cut2 = today - dt.timedelta(days=28), today - dt.timedelta(days=56)
    recent = [p["views"] for p in dated if p["date"] > cut1]
    before = [p["views"] for p in dated if cut2 < p["date"] <= cut1]
    trend = None
    if len(recent) >= 3 and len(before) >= 3:
        a, b = statistics.median(recent), statistics.median(before)
        ch = (a - b) / b * 100 if b else 0
        verdict = "growing" if ch >= 15 else "falling" if ch <= -15 else "flat"
        trend = {"last_28d_median": int(a), "prev_28d_median": int(b), "change_pct": round(ch, 1), "verdict": verdict,
                 "posts_last_28d": len(recent), "posts_prev_28d": len(before)}
    top = sorted((p for p in posts if med and p["views"] >= 2 * med), key=lambda p: -p["views"])[:5]
    flop = sorted((p for p in posts if med and p["views"] <= 0.3 * med), key=lambda p: p["views"])[:5]
    wd = None
    if len(dated) >= 20:
        by = {}
        for p in dated: by.setdefault(p["date"].strftime("%a"), []).append(p["views"])
        wd = sorted(({"day": d, "posts": len(v), "median": int(statistics.median(v))} for d, v in by.items() if len(v) >= 3),
                    key=lambda r: -r["median"])
    fmt = lambda p: {"date": p["date"].strftime("%Y-%m-%d") if p["date"] else None, "title": (p["title"] or "")[:80],
                     "views": int(p["views"]), "x_median": round(p["views"] / med, 2) if med else None}
    return {"posts": len(posts), "median_views": int(med), "weeks": table, "trend": trend,
            "repeat": [fmt(p) for p in top], "drop": [fmt(p) for p in flop], "series": series_groups(posts),
            "best_weekdays": wd, "undated": len(posts) - len(dated)}

def show(name, r):
    print(f"\n  {name}   {r['posts']} posts, median {r['median_views']:,} views per post")
    if r["weeks"]:
        print("\n    week       posts      views     median")
        for w in r["weeks"]:
            print(f"    {w['week']}   {w['posts']:>4}  {w['views']:>9,}  {w['median']:>9,}")
    t = r["trend"]
    if t:
        arrow = {"growing": "UP", "falling": "DOWN", "flat": "FLAT"}[t["verdict"]]
        print(f"\n    trend  {arrow}  median {t['last_28d_median']:,} (last 28 days, {t['posts_last_28d']} posts) vs "
              f"{t['prev_28d_median']:,} before ({t['change_pct']:+.0f}%)")
    else:
        print("\n    trend  not enough posts in the last 8 weeks to say (needs 3+ in each 4-week half)")
    if r["repeat"]:
        print("\n    repeat - 2x+ the median")
        for p in r["repeat"]: print(f"      {p['x_median']:5.1f}x  {p['views']:>9,}  {p['title'][:60]}")
    if r["drop"]:
        print("    drop - under 0.3x the median")
        for p in r["drop"]: print(f"      {p['x_median']:5.2f}x  {p['views']:>9,}  {p['title'][:60]}")
    for s in r["series"]:
        chain = "  ->  ".join(f"{p['part']}: {p['views']:,}" + (f" ({p['carry']:.0f}%)" if p["carry"] is not None else "") for p in s["parts"])
        print(f"    series  {s['series'][:40]}:  {chain}")
    if r["best_weekdays"]:
        print("    best weekdays by median: " + ", ".join(f"{d['day']} {d['median']:,}" for d in r["best_weekdays"][:3]))
    elif r["posts"] < 20:
        print("    weekday: under 20 posts - too few to tell a good day from luck")
    if r["undated"]: print(f"    {r['undated']} post(s) without a readable date were left out of the weekly view")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+"); ap.add_argument("--account", action="append")
    ap.add_argument("--weeks", type=int, default=8); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    names = a.account or []
    out = {}
    for i, f in enumerate(a.files):
        if not os.path.exists(f): ap.error(f"no such file: {f}")
        posts = load(f)
        if not posts: print(f"{f}: no posts with a view count"); continue
        out[names[i] if i < len(names) else os.path.splitext(os.path.basename(f))[0]] = analyse(posts, a.weeks)
    if a.json: print(json.dumps(out, ensure_ascii=False, indent=1)); return
    for n, r in out.items(): show(n, r)
    print()

if __name__ == "__main__":
    main()

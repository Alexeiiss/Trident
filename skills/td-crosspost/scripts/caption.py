#!/usr/bin/env python3
"""caption.py - lint a description / caption for YouTube, Shorts, TikTok or Instagram.

    python3 caption.py --platform instagram caption.txt
    python3 caption.py --platform tiktok --text "..." --keywords "dacians,ancient history"
    python3 caption.py --platform instagram caption.txt --first-comment comment.txt
    python3 caption.py --platform youtube description.txt --keywords "..." --json
    python3 caption.py --all master.txt     # lint the same text for all four surfaces at once

What it checks:
  * hard length limit (YouTube 5000, TikTok 4000 in app / 2200 via schedulers, Instagram 2200)
  * the fold: what shows before "more" (YouTube ~150, TikTok ~100, Instagram ~125) must hold the
    hook AND the words a person would search
  * hashtags: Instagram is capped at 5 per post since Dec 2025 - and hashtags in the first comment
    count toward the same 5; TikTok has no cap but 3-5 relevant ones is the norm; on YouTube the
    first 3 show above the title and more than 15 makes YouTube ignore all of them
  * duplicates, hashtags with spaces or punctuation that silently break, a caption that opens on
    a hashtag, generic tags (#fyp #viral #reels) that say nothing about the video
  * YouTube chapters inside the description, against YouTube's rules
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lang as L  # noqa: E402
P = json.load(open(os.path.join(HERE, "platforms.json"), encoding="utf-8"))

HASHTAG = re.compile(r"(?<![\w#])#([^\W_][\w]*)", re.UNICODE)
MENTION = re.compile(r"(?<![\w@])@[\w.]+", re.UNICODE)
GENERIC = {"fyp", "foryou", "foryoupage", "viral", "reels", "reel", "explore", "explorepage", "trending",
           "tiktok", "instagram", "youtube", "shorts", "pourtoi", "parati", "fy", "xyzbca", "рекомендации",
           "рек", "pentrutine", "prouteba", "foryour"}
CHAPTER = re.compile(r"^\s*\(?(\d{1,2}:\d{2}(?::\d{2})?)\)?\s+\S", re.M)

def to_s(ts):
    p = [int(x) for x in ts.split(":")]
    return p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else p[0] * 60 + p[1]

def lint(text, platform, keywords=None, first_comment=""):
    issues, good, info = [], [], {}
    cfg = P[platform if platform != "shorts" else "youtube"]
    n = len(text)
    tags = [t.lower() for t in HASHTAG.findall(text)]
    ctags = [t.lower() for t in HASHTAG.findall(first_comment or "")]
    info.update(chars=n, hashtags=tags, mentions=len(MENTION.findall(text)))
    hard = cfg.get("description_hard") or cfg.get("caption_hard") or cfg.get("caption_hard_app")
    if n > hard: issues.append(("length", f"{n} chars - the hard limit is {hard}"))
    if platform == "tiktok" and n > cfg["caption_hard_api"]:
        issues.append(("scheduler", f"{n} chars - fine in the app, but schedulers / the API stop at {cfg['caption_hard_api']}"))
    fold = cfg.get("description_fold") or cfg.get("caption_fold")
    head = text[:fold]
    info["above_fold"] = head
    if re.match(r"^\s*#", text): issues.append(("hashtag-first", "opens with a hashtag - open with the hook"))
    if keywords:
        kws = [k.strip() for k in keywords.split(",") if k.strip()]
        lowhead = head.lower()
        missing = [k for k in kws if k.lower() not in lowhead and not all(w in L.tokens(lowhead) for w in L.tokens(k))]
        if missing: issues.append(("fold-keywords", f"not above the fold ({fold} chars): {', '.join(missing)}"))
        else: good.append("every keyword is above the fold")
    dup = sorted({t for t in tags if tags.count(t) > 1})
    if dup: issues.append(("dup-tags", "repeated hashtags: " + ", ".join("#" + t for t in dup)))
    broken = re.findall(r"#\w+[^\w\s#]\w+", text)
    if broken: issues.append(("broken-tag", "punctuation inside a hashtag ends it early: " + ", ".join(broken[:4])))
    generic = sorted({t for t in tags if t in GENERIC})
    if generic: issues.append(("generic-tags", "tags that describe every video, not this one: " + ", ".join("#" + t for t in generic)))
    if platform == "instagram":
        total = len(tags) + len(ctags)
        if total > cfg["hashtags_max"]:
            issues.append(("ig-hashtags", f"{total} hashtags (caption {len(tags)} + first comment {len(ctags)}) - Instagram allows {cfg['hashtags_max']}"))
        elif tags or ctags: good.append(f"{total}/{cfg['hashtags_max']} hashtags")
    elif platform == "tiktok":
        lo, hi = cfg["hashtags_recommended"]
        if len(tags) > hi + 3: issues.append(("tt-hashtags", f"{len(tags)} hashtags - {lo}-{hi} specific ones do more than a wall"))
        if info["mentions"] > cfg["mentions_max"]: issues.append(("mentions", f"over {cfg['mentions_max']} mentions"))
    else:
        if len(tags) > cfg["hashtags_max"]:
            issues.append(("yt-hashtags", f"{len(tags)} hashtags - over {cfg['hashtags_max']} and YouTube ignores all of them"))
        elif tags: good.append(f"first {min(3, len(tags))} hashtag(s) will show above the title: " + " ".join("#" + t for t in tags[:3]))
        ch = CHAPTER.findall(text)
        if ch:
            secs = [to_s(c) for c in ch]
            probs = []
            if secs[0] != 0: probs.append("first is not 0:00")
            if len(secs) < 3: probs.append("fewer than 3")
            if any(b - a < 10 for a, b in zip(secs, secs[1:])): probs.append("a chapter under 10 s")
            if any(b <= a for a, b in zip(secs, secs[1:])): probs.append("timestamps not increasing")
            if probs: issues.append(("chapters", "chapters will NOT render: " + "; ".join(probs)))
            else: good.append(f"{len(secs)} valid chapters")
    score = max(0, min(100, 100 - 15 * len(issues) + 3 * len(good)))
    return {"platform": platform, "lang": L.detect(text), "score": score, "issues": issues, "good": good, "info": info}

def show(r):
    i = r["info"]
    print(f"\n  [{r['platform']} / {r['lang']}]  {i['chars']} chars, {len(i['hashtags'])} hashtags   score {r['score']}/100")
    print(f"    above the fold: \"{i['above_fold'].strip()[:160]}\"")
    for k, m in r["issues"]: print(f"    x  {k:<14} {m}")
    for m in r["good"]: print(f"    ok                {m}")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?")
    ap.add_argument("--text")
    ap.add_argument("--platform", default="youtube", choices=["youtube", "shorts", "tiktok", "instagram"])
    ap.add_argument("--all", action="store_true", help="lint for youtube, shorts, tiktok and instagram")
    ap.add_argument("--keywords", help="comma-separated words a person would search")
    ap.add_argument("--first-comment", help="file with the first comment (Instagram hashtag count)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.text is not None: text = a.text
    elif a.file and os.path.exists(a.file): text = open(a.file, encoding="utf-8").read().strip()
    else: ap.error("give a file or --text")
    fc = open(a.first_comment, encoding="utf-8").read() if a.first_comment and os.path.exists(a.first_comment) else ""
    plats = ["youtube", "shorts", "tiktok", "instagram"] if a.all else [a.platform]
    rows = [lint(text, p, a.keywords, fc) for p in plats]
    if a.json: print(json.dumps(rows, ensure_ascii=False, indent=1)); return
    for r in rows: show(r)
    print()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""package.py - lint the click surface before you publish: the thing people see BEFORE they watch.

  YouTube long-form   title + thumbnail text, as ONE pairing
      python3 package.py --platform youtube --title "..." --thumb "AI RAN IT"
      python3 package.py --platform youtube titles.txt          # one title per line, ranked
  YouTube Shorts      title (only ~40 characters are visible) + on-screen opening text
      python3 package.py --platform shorts --title "..." --cover "..."
  TikTok / Instagram  cover text + the first line of the caption, as ONE pairing
      python3 package.py --platform tiktok --cover "He didn't know" --first-line "..."
      python3 package.py --platform instagram --cover "..." --first-line "..."

  --lang en|cs|ru|ro (default: detect)   --format storytime|clip|narrated|history|series|talking-head
  --json

Rules, and why:
  * the two surfaces must not repeat each other - different words, same promise
  * YouTube titles: 60 chars before desktop search truncates, ~40 on a mobile feed; 100 is hard
  * thumbnail: 3 words max; TikTok / Reels cover: 6 words max (it is read at feed size)
  * caption first line: TikTok shows ~100 characters, Instagram ~125 before "more"
  * a number, a name, a place or a date beats any adjective - REQUIRED for talking-head YouTube,
    only a hint for storytime, clips and history, where a name or a scene does the same job
  * two all-caps words is the ceiling before it reads as spam
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lang as L  # noqa: E402
P = json.load(open(os.path.join(HERE, "platforms.json"), encoding="utf-8"))

NARRATIVE = {"storytime", "clip", "narrated", "history", "series"}

def content_words(t, lg):
    stop = L.stopwords(lg) | L.stopwords("en")
    return {w for w in L.tokens(t) if w not in stop and len(w) > 2}

def stem_overlap(a, b):
    # inflected languages: "svatba" / "svatby" are the same word for this purpose
    return {x for x in a for y in b if x == y or (len(x) > 4 and len(y) > 4 and x[:5] == y[:5])}

def caps_words(t):
    return [w for w in t.split() if len(w) > 2 and w.isupper() and re.search(r"[^\W\d_]", w)]

def lint_text(t, lg, fmt, issues, good, label):
    caps = caps_words(t)
    if len(caps) > 2: issues.append(("shouting", f"{label}: {len(caps)} all-caps words - two is the ceiling"))
    v = L.count(t, lg, "vague")
    if v: issues.append(("vague", f"{label}: vague adjective - swap it for a number, a name, a place or a date"))
    if L.concrete(t) or L.capitalised_names(t):
        good.append(f"{label}: carries something concrete (number / name)")
    elif fmt in NARRATIVE:
        good.append(f"{label}: no number - fine for {fmt}, if a scene or a person carries it")
    else:
        issues.append(("no-number", f"{label}: no number, name or date - the most reliable single fix"))

def check(platform, title=None, thumb=None, cover=None, first=None, lg=None, fmt=None):
    issues, good = [], []
    main_text = title or first or cover or ""
    lg = lg or L.detect(" ".join(x for x in (title, thumb, cover, first) if x))
    if platform in ("youtube", "shorts"):
        cfg = P[platform]
        t = (title or "").strip()
        n = len(t)
        if n > cfg["title_hard"]: issues.append(("length", f"{n} chars - YouTube's hard limit is {cfg['title_hard']}"))
        if platform == "youtube":
            if n > cfg["title_desktop"]: issues.append(("length", f"{n} chars - desktop search cuts near {cfg['title_desktop']}"))
            else: good.append(f"{n} chars, inside the {cfg['title_desktop']}-char desktop cut")
            if n > cfg["title_mobile"]:
                head = t[:cfg["title_mobile"]].rsplit(" ", 1)[0]
                issues.append(("mobile", f'a mobile feed shows about "{head}..." - does the subject survive?'))
        else:
            vis = cfg["title_visible"]
            if n > vis:
                head = t[:vis].rsplit(" ", 1)[0]
                issues.append(("visible", f'only about "{head}..." shows on the Shorts player'))
            else: good.append(f"{n} chars - fully visible on the Shorts player")
        lint_text(t, lg, fmt, issues, good, "title")
        front = [w for w in L.tokens(t)[:3] if w not in (L.stopwords(lg) | L.stopwords("en"))]
        if t and not front: issues.append(("front-load", "the first three words are filler - move the subject forward"))
        second = thumb if platform == "youtube" else cover
        if second:
            shared = stem_overlap(content_words(t, lg), content_words(second, lg))
            if shared: issues.append(("duplicate", f"{'thumbnail' if platform == 'youtube' else 'on-screen text'} repeats the title on: {', '.join(sorted(shared))}"))
            else: good.append("title and image text carry different words")
            limit = cfg.get("thumb_words_max", 6) if platform == "youtube" else 6
            wn = len(L.tokens(second))
            if wn > limit: issues.append(("image-text", f"{wn} words of image text - {limit} is the ceiling at feed size"))
    else:
        cfg = P[platform]
        if cover:
            wn = len(L.tokens(cover))
            if wn > cfg["cover_words_max"]: issues.append(("cover-length", f"{wn} words on the cover - {cfg['cover_words_max']} is the ceiling at grid size"))
            else: good.append(f"cover: {wn} words, readable at grid size")
            lint_text(cover, lg, fmt, issues, good, "cover")
        if first:
            fold = cfg["caption_fold"]
            if len(first) > fold:
                issues.append(("fold", f"caption first line is {len(first)} chars - only ~{fold} show before 'more'"))
            else: good.append(f"caption first line fits above the fold ({len(first)}/{fold})")
            if re.match(r"^\s*#", first): issues.append(("hashtag-first", "caption opens with a hashtag - open with the hook"))
            if cover:
                shared = stem_overlap(content_words(cover, lg), content_words(first, lg))
                if shared: issues.append(("duplicate", f"caption repeats the cover on: {', '.join(sorted(shared))}"))
                else: good.append("cover and caption say different things")
        if not cover and not first: issues.append(("empty", "give --cover and/or --first-line"))
    score = max(0, min(100, 100 - 14 * len(issues) + 3 * len(good)))
    return {"platform": platform, "lang": lg, "text": main_text, "score": score, "issues": issues, "good": good}

def show(r):
    print(f'\n  [{r["platform"]} / {r["lang"]}]  "{r["text"]}"   score {r["score"]}/100')
    for k, m in r["issues"]: print(f"    x  {k:<14} {m}")
    for m in r["good"]:      print(f"    ok                {m}")

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?", help="one title (YouTube) or one cover text (TikTok/IG) per line")
    ap.add_argument("--platform", default="youtube", choices=["youtube", "shorts", "tiktok", "instagram"])
    ap.add_argument("--title"); ap.add_argument("--thumb"); ap.add_argument("--cover")
    ap.add_argument("--first-line", dest="first")
    ap.add_argument("--lang", choices=L.LANGS); ap.add_argument("--format")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    rows = []
    if a.file:
        if not os.path.exists(a.file): ap.error(f"no such file: {a.file}")
        for line in open(a.file, encoding="utf-8").read().splitlines():
            if not line.strip(): continue
            if a.platform in ("youtube", "shorts"):
                rows.append(check(a.platform, title=line, thumb=a.thumb, cover=a.cover, lg=a.lang, fmt=a.format))
            else:
                rows.append(check(a.platform, cover=line, first=a.first, lg=a.lang, fmt=a.format))
    else:
        rows.append(check(a.platform, a.title, a.thumb, a.cover, a.first, a.lang, a.format))
    rows.sort(key=lambda r: -r["score"])
    if a.json: print(json.dumps(rows, ensure_ascii=False, indent=1)); return
    for r in rows: show(r)
    print()

if __name__ == "__main__":
    main()

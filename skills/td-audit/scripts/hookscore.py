#!/usr/bin/env python3
"""hookscore.py - score a hook before you waste a take (or a post) on it.

    python3 hookscore.py hooks.txt                          # one hook per line, ranked
    python3 hookscore.py --hook "one line"                  # score a single hook
    python3 hookscore.py --hook "..." --platform tiktok     # youtube | shorts | tiktok | instagram
    python3 hookscore.py --hook "..." --kind onscreen       # spoken (default) | onscreen
    python3 hookscore.py --hook "..." --lang ru             # en | cs | ru | ro (default: detect)
    python3 hookscore.py --hook "..." --format storytime    # talking-head | narrated | storytime |
                                                            # clip | series | history
    python3 hookscore.py --json hooks.txt

Five properties, 0-100 each. The verdict is 60% the mean and 40% the weakest property: a hook with
four strong properties and one dead one leaks at the dead one, and an average hides that.

Works in English, Czech, Russian and Romanian. Brevity bands change with the platform: a long-form
YouTube hook has ~10 seconds, a TikTok / Reel / Short has 1-3, and on-screen text has one glance.

WHAT THIS CAN AND CANNOT TELL YOU. It is a heuristic about the WORDS. It separates lazy hooks from
real ones well; it does not separate your hits from your misses. A low score is a reason to look
again, a high score is never a promise. Your own analytics outrank it every time.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lang as L  # noqa: E402

FORMULAS = json.load(open(os.path.join(HERE, "hooks.json"), encoding="utf-8"))["hooks"]

BANDS = {  # (min words, max words) that land inside the platform's hook window
    ("youtube", "spoken"): (9, 24), ("shorts", "spoken"): (5, 15), ("tiktok", "spoken"): (5, 15),
    ("instagram", "spoken"): (5, 15),
    ("youtube", "onscreen"): (2, 6), ("shorts", "onscreen"): (2, 8), ("tiktok", "onscreen"): (2, 8),
    ("instagram", "onscreen"): (2, 8),
}

def specificity(t, lg):
    toks = L.tokens(t)
    if not toks: return 0
    s = 34 + min(3, L.concrete(t)) * 18 - L.count(t, lg, "vague") * 16 - L.count(t, lg, "filler") * 5
    s += min(18, 6 * L.capitalised_names(t))
    return max(0, min(100, s))

def address(t, lg):
    n = L.count(t, lg, "you") + L.second_person_verbs(t, lg)
    head = " ".join(t.split()[:6])
    first = 30 if (L.count(head, lg, "you") + L.second_person_verbs(head, lg)) else 0
    return max(0, min(100, 26 + n * 20 + first))

def address_storytime(t, lg):
    # Storytime and history narration speak in "I" / "they", not "you". Do not punish it.
    return max(address(t, lg), 60)

def stakes(t, lg):
    n = L.count(t, lg, "stake")
    return max(0, min(100, 22 + n * 26 + (14 if L.concrete(t) else 0)))

def curiosity(t, lg):
    n = L.count(t, lg, "curiosity")
    q = 18 if t.strip().endswith("?") else 0
    closed = -18 * min(1, L.count(t, lg, "closed"))  # a hook that answers itself has no gap left
    return max(0, min(100, 24 + n * 17 + q + closed))

def brevity(t, band):
    n = len(L.tokens(t))
    lo, hi = band
    if n == 0: return 0
    if lo <= n <= hi: return 100
    if n < lo: return max(30, 100 - (lo - n) * 11)
    return max(10, 100 - (n - hi) * 7)

FIX = {
 "SPECIFICITY": "swap one adjective for a number, a name, a place or a date",
 "ADDRESS": "put 'you' (ty / ты / tu) in the first six words",
 "STAKES": "name what it costs them - or the character - if this goes wrong",
 "CURIOSITY": "cut the half of the sentence that answers itself",
 "BREVITY": "fit the platform window - read it out loud and stop where the window ends",
}

def classify(t, lg, fmt=None):
    best, hits, rank = None, 0, 0.0
    for f in FORMULAS:
        pats = list(f["match"]) + list(f.get("i18n", {}).get(lg, []))
        n = sum(1 for p in pats if re.search(p, t, re.I))
        r = n + (0.5 if n and fmt and fmt in f.get("formats", []) else 0)
        if r > rank: best, hits, rank = f, n, r
    if not best:  # detection can be wrong on a short line: try every language's patterns
        for f in FORMULAS:
            pats = [p for v in f.get("i18n", {}).values() for p in v]
            n = sum(1 for p in pats if re.search(p, t, re.I))
            if n > hits: best, hits = f, n
    return (best["name"] if best else "Unclassified"), hits

NARRATIVE = ("storytime", "narrated", "history", "series")

def narrative_tension(t, lg):
    # Story hooks carry stakes as conflict between people, not as "you will lose money".
    return L.count(t, lg, "conflict")

def score(t, platform="youtube", kind="spoken", lg=None, fmt=None):
    lg = lg or L.detect(t)
    band = BANDS.get((platform, kind), BANDS[("youtube", "spoken")])
    addr = address_storytime if fmt in ("storytime", "narrated", "history", "series", "clip") else address
    parts = {"SPECIFICITY": specificity(t, lg), "ADDRESS": addr(t, lg), "STAKES": stakes(t, lg),
             "CURIOSITY": curiosity(t, lg), "BREVITY": brevity(t, band)}
    if fmt in NARRATIVE:
        c = narrative_tension(t, lg)
        parts["STAKES"] = max(parts["STAKES"], min(100, 22 + c * 24))
        parts["CURIOSITY"] = min(100, parts["CURIOSITY"] + c * 12)
        parts["SPECIFICITY"] = min(100, parts["SPECIFICITY"] + min(2, c) * 10)
    vals = list(parts.values())
    verdict = round(0.6 * (sum(vals) / len(vals)) + 0.4 * min(vals))
    name, hits = classify(t, lg, fmt)
    return {"hook": t.strip(), "lang": lg, "platform": platform, "kind": kind,
            "properties": parts, "verdict": verdict, "band": band_name(verdict),
            "formula": name, "matched": hits, "weakest": min(parts, key=parts.get)}

def band_name(v): return "STRONG" if v >= 72 else "WORKABLE" if v >= 55 else "WEAK"

def report(r):
    print(f"\n  {r['hook']}")
    print(f"  {'-' * min(72, max(20, len(r['hook'])))}   [{r['lang']} / {r['platform']} / {r['kind']}]")
    for k, v in r["properties"].items():
        print(f"    {k:<12} {v:3d}  {'#' * (v // 5)}")
    print(f"    {'VERDICT':<12} {r['verdict']:3d}  {r['band']}")
    m = r["matched"]
    print(f"    formula      {r['formula']}" + (f"  ({m} pattern{'s' if m != 1 else ''} matched)" if m
          else "  (no formula matched - usually a summary, not a hook)"))
    print(f"    weakest      {r['weakest']} - {FIX[r['weakest']]}")

def opt(a, name, default=None):
    if name in a:
        i = a.index(name)
        if i + 1 < len(a): return a[i + 1]
    return default

def main():
    a = sys.argv[1:]
    as_json = "--json" in a
    platform = opt(a, "--platform", "youtube")
    kind = opt(a, "--kind", "spoken")
    lg = opt(a, "--lang")
    fmt = opt(a, "--format")  # talking-head | narrated | storytime | clip | series | history
    if platform not in ("youtube", "shorts", "tiktok", "instagram"):
        print("--platform must be youtube, shorts, tiktok or instagram"); sys.exit(2)
    if lg and lg not in L.LANGS:
        print("--lang must be one of " + ", ".join(L.LANGS)); sys.exit(2)
    hook = opt(a, "--hook")
    if hook is not None:
        lines = [hook]
    else:
        values = {opt(a, f) for f in ("--platform", "--kind", "--lang", "--format")}
        files = [x for x in a if not x.startswith("--") and x not in values]
        if not files or not os.path.exists(files[0]):
            print(__doc__); sys.exit(1)
        lines = [l for l in open(files[0], encoding="utf-8").read().splitlines() if l.strip()]
    out = sorted((score(t, platform, kind, lg, fmt) for t in lines), key=lambda r: -r["verdict"])
    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=1)); return
    for r in out: report(r)
    if len(out) > 1:
        print(f"\n  winner: {out[0]['hook']}  ({out[0]['verdict']}, {out[0]['band']})\n")

if __name__ == "__main__":
    main()

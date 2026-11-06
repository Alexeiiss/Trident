#!/usr/bin/env python3
"""chapters.py - YouTube chapters from a timestamped transcript (long-form YouTube only).

    python3 chapters.py transcript.srt              # .srt / .vtt / whisper .json
    python3 chapters.py transcript.srt --target 8 --json
    python3 chapters.py transcript.srt --lang ru

YouTube's rules, enforced rather than assumed: the list starts at 0:00, has at least three entries,
and every chapter is at least 10 seconds. A block that breaks any of them silently does not become
chapters. Boundaries come from the pauses you actually took, scored by pause length and by how much
the vocabulary changes across it. Titles are DRAFT topic words - retitle every one.

TikTok and Instagram have no chapters. For a series split, use series.py instead.
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lang as L  # noqa: E402
from transcript import load, mmss  # noqa: E402

MIN = 10.0

def keywords(text, lg):
    stop = L.stopwords(lg) | L.stopwords("en")
    return {w for w in L.tokens(text) if len(w) >= 4 and w not in stop}

def chapters(cues, target=7, lg="en"):
    dur = cues[-1][1]
    cand = []
    for i in range(1, len(cues)):
        gap = cues[i][0] - cues[i - 1][1]
        kb = keywords(" ".join(c[2] for c in cues[max(0, i - 12):i]), lg)
        ka = keywords(" ".join(c[2] for c in cues[i:i + 12]), lg)
        shift = 1 - (len(kb & ka) / len(kb | ka)) if (kb | ka) else 0
        cand.append((gap * 1.6 + shift * 3.2, cues[i][0]))
    cand.sort(reverse=True)
    picked = [0.0]
    for _, t in cand:
        if len(picked) >= target: break
        if all(abs(t - p) >= MIN for p in picked) and dur - t >= MIN:
            picked.append(t)
    picked.sort()
    out = []
    for n, t in enumerate(picked):
        end = picked[n + 1] if n + 1 < len(picked) else dur
        text = " ".join(c[2] for c in cues if c[0] >= t and c[0] < end)
        low = text.lower()
        kw = sorted(keywords(text, lg), key=lambda w: (-low.count(w), w))
        title = " ".join(w.capitalize() for w in kw[:3]) or "Section"
        out.append({"start": round(t, 2), "label": mmss(t), "draft_title": title,
                    "seconds": round(end - t, 2)})
    return out

def validate(ch):
    problems = []
    if len(ch) < 3: problems.append("fewer than 3 chapters")
    if not ch or ch[0]["start"] != 0: problems.append("first chapter is not 0:00")
    short = [c["label"] for c in ch if c["seconds"] < MIN]
    if short: problems.append("under 10 s: " + ", ".join(short))
    return problems

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcript")
    ap.add_argument("--target", type=int, default=7)
    ap.add_argument("--lang", choices=L.LANGS)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(a.transcript): ap.error(f"no such file: {a.transcript}")
    cues = load(a.transcript)
    if len(cues) < 6: print("too few cues to chapter"); sys.exit(1)
    lg = a.lang or L.detect(" ".join(c[2] for c in cues[:200]))
    ch = chapters(cues, a.target, lg)
    problems = validate(ch)
    if a.json:
        print(json.dumps({"valid": not problems, "problems": problems, "lang": lg, "chapters": ch},
                         ensure_ascii=False, indent=1)); return
    print()
    for c in ch: print(f"  {c['label']} {c['draft_title']}")
    print(f"\n  {len(ch)} chapters" + (f"  -- INVALID: {'; '.join(problems)}" if problems else "  -- valid for YouTube"))
    print("  Retitle every line before pasting. These are topic words, not your words.\n")

if __name__ == "__main__":
    main()

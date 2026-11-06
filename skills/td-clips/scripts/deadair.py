#!/usr/bin/env python3
"""deadair.py - an edit decision list from a timestamped transcript.

    python3 deadair.py transcript.srt                 # .srt, .vtt (YouTube auto-captions ok), whisper .json
    python3 deadair.py transcript.srt --floor 0.35 --json
    python3 deadair.py transcript.srt --lang cs       # filler words for en | cs | ru | ro (default: detect)
    python3 deadair.py transcript.srt --target 60     # also say how far you are from a 60 s Short / Reel

Finds three things and prints the cuts:
  DEAD    gaps between spoken cues longer than the floor, trimmed from the MIDDLE so both sides
          keep a breath (cutting flush against speech is what makes a tight take sound gasping)
  FILLER  cues that are only filler ("um", "ehm", "ну", "păi")
  REPEAT  a sentence restarted - compared against the last cue that was SPEECH, because most
          retakes have an "um" between the two attempts

It does not touch media. It prints an EDL, the total it would remove and the runtime you land on.
The percentage is of SPEECH: a long silent demo or a B-roll montage makes it wrong. Check it
against the footage.
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lang as L  # noqa: E402
from transcript import load  # noqa: E402

def norm(t): return L.tokens(t)

def edl(cues, floor=0.45, lg="en"):
    cuts = []
    filler = [L.is_filler_only(t, lg) for _, _, t in cues]
    for i, (s, e, t) in enumerate(cues):
        if filler[i]:
            cuts.append({"kind": "FILLER", "start": s, "end": e, "why": t.strip()[:48]})
        if i:
            gap = s - cues[i - 1][1]
            if gap > floor:
                keep = floor / 2
                cuts.append({"kind": "DEAD", "start": round(cues[i - 1][1] + keep, 3),
                             "end": round(s - keep, 3), "why": f"{gap:.2f}s gap"})
        if t.strip() and not filler[i]:
            j = i - 1
            while j >= 0 and (filler[j] or not cues[j][2].strip()): j -= 1
            if j >= 0:
                # an abandoned take is usually SHORTER than the retake ("In 1941" -> "In 1941 the war")
                pa, pb = norm(cues[j][2]), norm(t)
                k = min(len(pa), len(pb), 5)
                a1 = pa[:k]
                if k >= 3 and a1 == pb[:k]:
                    cuts.append({"kind": "REPEAT", "start": cues[j][0], "end": cues[j][1],
                                 "why": 'restart of "' + " ".join(a1) + '"'})
    cuts = sorted((c for c in cuts if c["end"] > c["start"]), key=lambda c: (c["start"], c["end"]))
    # merge overlaps so nothing is counted twice
    merged = []
    for c in cuts:
        if merged and c["start"] < merged[-1]["end"]:
            m = merged[-1]
            m["end"] = max(m["end"], c["end"])
            if c["kind"] not in m["kind"]: m["kind"] += "+" + c["kind"]
            m["why"] += "; " + c["why"]
        else:
            merged.append(dict(c))
    return merged

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcript")
    ap.add_argument("--floor", type=float, default=0.45)
    ap.add_argument("--lang", choices=L.LANGS)
    ap.add_argument("--target", type=float, help="target runtime in seconds (e.g. 60 for a Short)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(a.transcript): ap.error(f"no such file: {a.transcript}")
    cues = load(a.transcript)
    if not cues: print("no cues found - is this an srt, vtt or whisper json?"); sys.exit(1)
    lg = a.lang or L.detect(" ".join(c[2] for c in cues[:200]))
    dur = cues[-1][1]
    cuts = edl(cues, a.floor, lg)
    removed = sum(c["end"] - c["start"] for c in cuts)
    out_len = dur - removed
    if a.json:
        print(json.dumps({"source": a.transcript, "lang": lg, "duration": dur, "cuts": cuts,
                          "removed": round(removed, 3), "out": round(out_len, 3)},
                         ensure_ascii=False, indent=1)); return
    print(f"\n  {a.transcript}   {dur:.2f}s in, {len(cues)} cues, lang {lg}, dead-air floor {a.floor}s\n")
    for c in cuts:
        print(f"    {c['kind']:<13} {c['start']:8.2f} -> {c['end']:8.2f}   {c['end']-c['start']:5.2f}s   {c['why'][:60]}")
    print(f"\n  {len(cuts)} cuts, {removed:.2f}s removed, {out_len:.2f}s out "
          f"({removed / dur * 100:.1f}% shorter)")
    if a.target:
        over = out_len - a.target
        print(f"  target {a.target:.0f}s: " + (f"still {over:.1f}s over - cut content, not pauses"
                                               if over > 0 else f"fits, {-over:.1f}s to spare"))
    print()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""transcript.py - one transcript loader for every Trident tool.

Reads .srt, .vtt (including YouTube's rolling auto-captions) and Whisper / faster-whisper .json.
Returns a list of (start_seconds, end_seconds, text).

YouTube auto-captions repeat every line twice (each cue shows the previous line plus the new one)
and carry word-timing tags like <00:00:01.234><c> word</c>. Fed raw into a dead-air or retake
detector they produce nonsense - every cue looks like a restart. This loader strips the tags and
keeps only the text that is new in each cue.
"""
import json, re

TAG = re.compile(r"<[^>]+>")

def parse_ts(s):
    s = s.strip().replace(",", ".")
    p = s.split(":")
    if len(p) == 3: return int(p[0]) * 3600 + int(p[1]) * 60 + float(p[2])
    if len(p) == 2: return int(p[0]) * 60 + float(p[1])
    return float(p[0])

def _load_json(raw):
    d = json.loads(raw)
    segs = d.get("segments", []) if isinstance(d, dict) else d
    out = []
    for s in segs:
        if "start" in s and "end" in s:
            out.append((float(s["start"]), float(s["end"]), (s.get("text") or "").strip()))
    return out

def _load_cues(raw):
    cues, cur = [], None
    for line in raw.splitlines():
        m = re.match(r"\s*(\d[\d:.,]*)\s*-->\s*(\d[\d:.,]*)", line)
        if m:
            cur = [parse_ts(m.group(1)), parse_ts(m.group(2)), []]
            cues.append(cur)
        elif cur is not None and line.strip() and not line.strip().isdigit():
            if line.strip().startswith(("NOTE", "STYLE", "REGION")): continue
            cur[2].append(TAG.sub("", line).strip())
    return cues

def _dedupe_rolling(cues):
    """Keep only lines not already shown by the previous cue (YouTube rolling captions)."""
    out, prev_lines = [], []
    for a, b, lines in cues:
        lines = [l for l in lines if l]
        if b - a < 0.05 and lines and prev_lines and lines[-1] == prev_lines[-1]:
            continue  # 10 ms "hold" cue that only repeats what is on screen
        new = [l for l in lines if l not in prev_lines]
        if lines: prev_lines = lines
        if new: out.append((a, b, " ".join(new)))
    return out

def load(path):
    raw = open(path, encoding="utf-8-sig", errors="replace").read()
    if path.lower().endswith(".json"):
        return _load_json(raw)
    cues = _load_cues(raw)
    rolling = sum(1 for i in range(1, len(cues)) if cues[i][2] and cues[i - 1][2]
                  and cues[i][2][0] == cues[i - 1][2][-1])
    if cues and rolling > len(cues) * 0.3:
        return _dedupe_rolling(cues)
    return [(a, b, " ".join(l for l in t if l)) for a, b, t in cues if any(t)]

def text_between(cues, start, end):
    return " ".join(c[2] for c in cues if c[0] >= start and c[1] <= end)

def mmss(t):
    t = int(t); h, m, s = t // 3600, (t % 3600) // 60, t % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

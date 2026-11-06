---
name: td-clips
description: >-
  Find the Shorts, TikToks and Reels hiding inside a long video and write them - self-contained
  moments picked from the transcript, a new first line and on-screen text for each, scored. Use for
  "cut this into shorts", "clip this", "make TikToks from my video", "repurpose this", "what should
  I clip".
---

# td-clips

A clip cut out of a long video is not the best moment. It is a moment that **survives without the
video around it** - a much smaller set.

@@TOOLS

```bash
python3 scripts/hookscore.py --hook "new first line" --platform tiktok
python3 scripts/hookscore.py --hook "on-screen text" --kind onscreen --platform instagram
python3 scripts/deadair.py clip.srt --target 60
```

@@BEFORE

## Picking

Read the transcript and find spans of 20-60 seconds (up to 3 minutes if the profile says the
account does longer short-form) where all three are true:

1. It opens on a complete thought. If the first sentence needs the previous minute, it is not a clip.
2. There is a turn in it - a claim and then something that complicates or proves it; in a story, a
   moment where it gets worse.
3. It ends on a line, not a trail-off.

Rank the candidates and show the top five with timecodes and first line, so the user can reject one
without reading the whole transcript.

## Writing each one

- **A new first line** - the long video's line assumes context this viewer does not have. Score it
  with `hookscore.py --platform <target>`.
- **On-screen text for the first two seconds**, in different words from the spoken line, scored
  with `--kind onscreen`.
- **A loop point** - what the last line sets up so the first line answers it on a rewatch.
- **Vertical framing note** - what a 9:16 crop of 16:9 footage loses, and whether that matters.
- **Which platform first** - if the clip is long (over ~90 s) say it fits YouTube Shorts and
  TikTok better than Reels.

If one story is too long for a single clip, it is a series - hand over to `/td-series`.

@@GATE

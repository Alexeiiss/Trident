---
name: td-retention
description: >-
  Read audience retention for YouTube, Shorts, TikTok or Instagram Reels and find where viewers
  actually leave - the hook leak, the cliffs and the slide - then say the one thing to change. Use
  for "why do people stop watching", "my retention is bad", "people swipe away", a retention chart
  screenshot or CSV, "fix my pacing".
---

# td-retention

The retention graph is the only honest feedback any of these platforms gives you.

@@TOOLS

```bash
python3 scripts/retention.py retention.csv --duration 600                    # YouTube export
python3 scripts/retention.py retention.csv --duration 600 --transcript v.srt # what was said at each drop
python3 scripts/retention.py --points "0:100,1:90,3:61,10:45,30:30" --platform tiktok
python3 scripts/retention.py --points "..." --platform instagram --duration 40
```

## Getting the data

- **YouTube / Shorts** - Studio -> the video -> Analytics -> Engagement -> audience retention -> the
  download icon. For Shorts also note the **viewed vs swiped away** figure from the same page.
- **TikTok** - TikTok Studio -> the video -> Analytics: the retention chart, average watch time and
  "watched full video". There is no export: if the user sends a screenshot, read 6-10 points off the
  curve (always including 0 s, 1 s, 3 s and the end) and pass them with `--points`.
- **Instagram** - the Reel -> Insights: the retention graph, skip rate and average watch time. Same
  as TikTok: read the points off the screenshot.

Say which points you read off a screenshot, so the user can correct one.

## Three problems, three fixes

- **HOOK LEAK** - lost inside the hook window: 30 s on long-form, **3 s on short-form**. Always fixed
  in the first line and the first on-screen text, never in the edit. Send them to `/td-script`.
- **CLIFFS** - single steep drops: a moment. A topic change with no signpost, a long setup, a scene
  that answers the question too early. With `--transcript` the tool prints what was said there.
- **SLIDE** - steady loss per 10% of runtime. Pacing: cut, do not rewrite. On short-form a steep
  slide usually means the video is longer than its idea.

## What to hand back

The single biggest leak and one change for it. Not five. The benchmarks in the tool are rough - if
the user has their own typical numbers, compare against those instead and say so. If the hook leak
is healthy and the slide is flat, say the video is fine and the problem is packaging - `/td-package`.
For a numbered series, also run `/td-series` stats.

@@GATE

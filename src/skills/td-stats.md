---
name: td-stats
description: >-
  Read the platforms' own exports (YouTube Studio CSV, TikTok / Instagram numbers) and say how each
  account is really doing - week by week, median not average, trend over the last 4 weeks, which
  posts to repeat and which to drop, series carry, best weekday. Use for "how am I doing", "weekly
  report", "is my channel growing", "which videos worked", a pasted analytics export.
---

# td-stats

Averages lie on social: one viral post hides nine dead ones. This reads medians, week by week, and
compares every post with the account's own typical result.

@@TOOLS

```bash
python3 scripts/stats.py "Table data.csv"                          # YouTube Studio export
python3 scripts/stats.py yt.csv tiktok.csv --account "YouTube EN" --account "@handle"
python3 scripts/stats.py posts.json --weeks 12 --json
```

@@BEFORE

## Getting the numbers

- **YouTube** - Studio -> Analytics -> Advanced mode -> Content -> period -> Export -> CSV; use
  `Table data.csv` from the zip.
- **TikTok / Instagram** - not every account can export per-post data. Then ask for a screenshot of
  the content list, read it into a CSV (`date,title,views,likes,comments,shares`) and say which
  numbers you read off, so the user can correct one. A CSV the user keeps by hand works too.
- Column names are matched loosely in English, Czech, Russian and Romanian; dates in most formats.

One file per account. Never mix two accounts into one median.

## Reading it

Lead with the one line that matters: is the account **growing, flat or falling** (median of the last
28 days vs the 28 before), and why, in one sentence. Then:

- **repeat** - posts at 2x+ the median: what they share (formula, length, topic, time). Run
  `/td-trends`-style thinking on the user's own data.
- **drop** - posts under 0.3x: what they share.
- **series** - the carry part-to-part; anything under ~50% goes to `/td-series` for diagnosis.
- **weekday** - only with 20+ posts, and only as a hint.

If the user wants it as a page they can come back to, build a dashboard from the JSON output.
Never invent a number that is not in the export.

@@GATE

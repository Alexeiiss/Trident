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

Tools live in this skill's `scripts/` folder and run on plain Python 3 with no installs. Run them -
do not eyeball what a tool can measure. Every tool takes `--json` and `--help`.

```bash
python3 scripts/stats.py "Table data.csv"                          # YouTube Studio export
python3 scripts/stats.py yt.csv tiktok.csv --account "YouTube EN" --account "@handle"
python3 scripts/stats.py posts.json --weeks 12 --json
```

## Before you write

1. **Load the account profile.** Every account gets its own profile - a Russian storytime TikTok and
   an English history YouTube channel do not share a voice. Look, in this order, for: a profile the
   user pasted or attached in this conversation; `./creator-profiles/<handle>.md` in the working
   folder; `~/.claude/trident/profiles/<handle>.md`. If the user has several and did not say
   which, ask which account this is for. If there is none, run the `/td-profile` interview first
   (five minutes), or - if the user wants to skip it - ask for the three things that matter most:
   **language, format, and who it is for.**
2. **Write the content in the account's language**, and talk to the user in the language they write
   to you in. A Romanian channel gets Romanian copy even when the conversation is in Czech.
3. **Never invent a number, a result, a date or a source.** If a figure would make it stronger and
   you do not have it, ask for it or write the line without it. For history and true-story content,
   say plainly which details are documented and which are dramatised.

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

## The gate

Nothing here publishes. This skill writes; the user posts. Every run ends with a block the user can
copy as it is, and the last line is the question, in the user's language: **ship it, or change it?**

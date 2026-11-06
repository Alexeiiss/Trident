---
name: td-crosspost
description: >-
  Turn one finished video into a ready-to-post package for YouTube (or Shorts), TikTok and Instagram
  Reels at once - title / cover / caption / hashtags per platform, each in the account's language,
  each linted, with length and format checks. Use for "post this everywhere", "all three platforms",
  "adapt this for TikTok and Instagram", "crosspost", "same video on Reels".
---

# td-crosspost

The same video is three different posts. What people see before they press play, how much caption
they read, how many hashtags are allowed and how long the video may be are different on each
platform - and copying one caption to all three is the most common way to lose two of them.

@@TOOLS

```bash
python3 scripts/package.py --platform tiktok --cover "..." --first-line "..."
python3 scripts/package.py --platform instagram --cover "..." --first-line "..."
python3 scripts/package.py --platform shorts --title "..." --cover "..."
python3 scripts/caption.py --platform instagram ig.txt --keywords "..."
python3 scripts/caption.py --all master.txt       # quick check of one text on all surfaces
```

@@BEFORE

## Ask, or read from the profile

- Which accounts this goes to (the user may post a platform in one language and another platform in
  another - each account's profile decides the language).
- The video's length and orientation. Check against `scripts/platforms.json`: Shorts up to 3 min,
  Reels up to 3 min for Reels-tab reach, TikTok up to 10 min in the app. 16:9 footage needs a
  vertical reframe note for all three short-form platforms.

## For each platform, write

| | YouTube / Shorts | TikTok | Instagram |
| --- | --- | --- | --- |
| click surface | title (+ thumbnail text) | cover text | cover text |
| caption | description, first 150 chars carry it | ~100 chars visible, 1-3 sentences | ~125 chars visible |
| hashtags | ≤ 3 that matter (show above title) | 3-5 specific | **max 5, comment included** |
| extra | chapters (long-form) | keyword spoken + on screen | alt text |

Never write the same first line for two platforms. Same promise, different words - the audiences
overlap, and someone who saw it on TikTok should not feel they are reading a copy.

Run every piece through `package.py` and `caption.py`, fix what fails, and only then show it.

## What to hand back

One copy block per platform, in this order: YouTube, TikTok, Instagram - each with its click surface,
caption and hashtags ready to paste, and a one-line note of anything the video itself needs changed
for that platform (crop, length, text inside the safe zone).

@@GATE

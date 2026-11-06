---
name: td-trends
description: >-
  Find what is actually working in a niche on YouTube, TikTok or Instagram and rank it by how far
  each video beat its own account's median, then name the formula behind the title. Use for "what's
  working right now", "find viral videos in my niche", "why did this blow up", competitor research,
  "swipe file".
---

# td-trends

Raw views rank account size, not ideas. This ranks by **multiple over each account's own median** -
the only version of the question that is about the video.

@@TOOLS

```bash
python3 scripts/trends.py collected.json --min 2
python3 scripts/trends.py yt.json tiktok.json --split-shorts --per-day
```

## Collecting the input

At least **four videos per account**, or a median means nothing (the tool skips and says so). Any of:

- `yt-dlp --flat-playlist -J "https://www.youtube.com/@channel/videos" > yt.json` (also `/shorts`)
- `yt-dlp -J --flat-playlist "https://www.tiktok.com/@handle" > tt.json` - TikTok and Instagram
  often refuse logged-out listings; if they do, use a manual list
- a manual list: `[{"channel":"...","title":"...","views":412000,"url":"...","duration":45,"upload_date":"20261020","platform":"tiktok"}]`

In a sandbox without network access to those sites, ask the user to paste the list or the yt-dlp
file.

**Read, do not scrape.** Public listings only, never a logged-in session, never the user's
credentials.

Use `--split-shorts` whenever a channel mixes Shorts and long videos, and `--per-day` when the list
spans more than a couple of months.

## Reading the output

The multiple is the signal. The formula is a judgement about the TITLE / caption (`hooks.json`, all
four languages) - not a claim about why the video worked; say so when you present it. For clip and
storytime accounts, the title says little: ask for or look at the cover text and the first second.

Hand back the top five with multiples and formulas, the ONE structural thing they share, then the
harder line: which of these the user could actually make this week, for which account, in its
language and format.

@@GATE

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

Tools live in this skill's `scripts/` folder and run on plain Python 3 with no installs. Run them -
do not eyeball what a tool can measure. Every tool takes `--json` and `--help`.

```bash
python3 scripts/package.py --platform tiktok --cover "..." --first-line "..."
python3 scripts/package.py --platform instagram --cover "..." --first-line "..."
python3 scripts/package.py --platform shorts --title "..." --cover "..."
python3 scripts/caption.py --platform instagram ig.txt --keywords "..."
python3 scripts/caption.py --all master.txt       # quick check of one text on all surfaces
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

## The gate

Nothing here publishes. This skill writes; the user posts. Every run ends with a block the user can
copy as it is, and the last line is the question, in the user's language: **ship it, or change it?**

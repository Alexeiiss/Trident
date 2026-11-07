---
name: td-cover
description: >-
  Make covers and thumbnails that read at feed size - TikTok / Reels covers, YouTube thumbnails,
  and matching covers for every part of a series - with the text kept in the safe zone and the
  profile-grid crop, contrast checked and fixed. Use for "make a cover", "thumbnail", "cover for
  part 2", "series covers", "my covers look messy in the grid".
---

# td-cover

The profile grid is a shop window. A series whose covers share one template reads as a show; one
with random frames reads as noise.

Tools live in this skill's `scripts/` folder and run on plain Python 3 with no installs. Run them -
do not eyeball what a tool can measure. Every tool takes `--json` and `--help`.

```bash
python3 scripts/cover.py --text "She didn't know" --bg frame.jpg -o cover.png
python3 scripts/cover.py --text "x" --texts "The gold|The traitor|The last fortress" --parts 3 \
        --label "PART {n}" --bg frame.jpg -o dacians.png        # dacians_1.png ... _3.png
python3 scripts/cover.py --text "AI RAN IT" --size thumb --bg face.jpg -o thumb.png
```

`--size reel | thumb | square | grid | WxH`, `--position top | center | bottom-safe`,
`--accent "#3DF2C2"`, `--scrim auto | on | off`, `--json` for the checks.

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

## The text first

Write the cover text with `/td-package` (it lints the cover against the caption's first line). The
cover says what the video promises in at most 6 words (3 on a YouTube thumbnail) and never repeats
the caption. For a series: same template, the part number big, a different promise per part.

## The frame

Ask for, or pull with ffmpeg, the frame to use: a face mid-reaction, the object the story is about,
the moment before the payoff. `ffmpeg -ss 12.4 -i video.mp4 -frames:v 1 frame.jpg`. Only images the
user has the rights to.

## What the tool checks - report every flag

- word count against the platform limit
- text kept inside the safe box: the 1080x1350 grid crop of a 9:16 cover, and out of the bottom 20% /
  right 15% that the app's buttons cover
- contrast of the text against what is actually behind it (WCAG); under 4.5:1 a dark scrim is added
  and the report says so - if even that fails, pick a calmer frame
- text that had to shrink a lot to fit means the text is too long - shorten it, do not accept it small

Look at the PNG before handing it over.

## The gate

Nothing here publishes. This skill writes; the user posts. Every run ends with a block the user can
copy as it is, and the last line is the question, in the user's language: **ship it, or change it?**

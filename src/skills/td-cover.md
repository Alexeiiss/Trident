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

@@TOOLS

```bash
python3 scripts/cover.py --text "She didn't know" --bg frame.jpg -o cover.png
python3 scripts/cover.py --text "x" --texts "The gold|The traitor|The last fortress" --parts 3 \
        --label "PART {n}" --bg frame.jpg -o dacians.png        # dacians_1.png ... _3.png
python3 scripts/cover.py --text "AI RAN IT" --size thumb --bg face.jpg -o thumb.png
```

`--size reel | thumb | square | grid | WxH`, `--position top | center | bottom-safe`,
`--accent "#3DF2C2"`, `--scrim auto | on | off`, `--json` for the checks.

@@BEFORE

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

@@GATE

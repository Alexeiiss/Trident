---
name: td-subtitles
description: >-
  Turn a transcript into word-by-word captions for short-form video - the spoken word lights up,
  hook text on top, everything inside the TikTok / Reels safe zone - as an .ass file for CapCut /
  editors or burnt straight into the video. Styles for film clips, storytime and documentary. Use
  for "add subtitles", "captions like CapCut", "burn in captions", "subtitles for my clip".
---

# td-subtitles

Most short-form is watched without sound for the first seconds. Captions are not accessibility
garnish here - they are the hook's second channel.

@@TOOLS

```bash
python3 scripts/subtitles.py take.json -o captions.ass                    # whisper JSON, word timings
python3 scripts/subtitles.py clip.srt --style clip --hook "Watch his hand" -o captions.ass
python3 scripts/subtitles.py clip.srt --style clip --burn clip.mp4 -o clip_captioned.mp4
python3 scripts/subtitles.py talk.srt --size 1920x1080 --words 6 -o captions.ass   # landscape
```

@@BEFORE

## Getting word timings

- **Best:** a Whisper / faster-whisper JSON with `word_timestamps` - every word lands exactly.
  (`whisper clip.mp4 --word_timestamps True --output_format json`)
- **Good:** an `.srt` / `.vtt` (CapCut auto-captions export, YouTube's track - rolling auto-captions
  are de-duplicated). Words are spread across each cue by length, so they drift a little inside
  long cues.

## Choosing the style

| style | for | look |
| --- | --- | --- |
| `clip` | film / series clip pages | white text on a black box; hook on a white box at the top |
| `storytime` | narrated stories over slime / gameplay | big white words, current word yellow |
| `bold` | talking head, explainers | big white words, current word teal |
| `minimal` | history, documentary | one calm line, no highlight |

3 words on screen at a time on vertical video (`--words` to change), 6 on landscape. A new group
starts at every sentence end and after any pause longer than 0.6 s.

## The hook text

`--hook` puts the on-screen hook at the top for `--hook-until` seconds. It must not repeat the first
spoken line - check the pair with `/td-package` (`--cover` + `--first-line`). For film clips, caption
what to watch for, never what happens.

When the user only wants the .ass file, tell them how to use it: CapCut and most editors import
`.ass`; or burn it with `--burn`. The fonts (Inter, OFL licence) are in `scripts/fonts/`.

@@GATE

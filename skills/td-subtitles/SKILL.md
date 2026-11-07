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

Tools live in this skill's `scripts/` folder and run on plain Python 3 with no installs. Run them -
do not eyeball what a tool can measure. Every tool takes `--json` and `--help`.

```bash
python3 scripts/subtitles.py take.json -o captions.ass                    # whisper JSON, word timings
python3 scripts/subtitles.py clip.srt --style clip --hook "Watch his hand" -o captions.ass
python3 scripts/subtitles.py clip.srt --style clip --burn clip.mp4 -o clip_captioned.mp4
python3 scripts/subtitles.py talk.srt --size 1920x1080 --words 6 -o captions.ass   # landscape
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

## The gate

Nothing here publishes. This skill writes; the user posts. Every run ends with a block the user can
copy as it is, and the last line is the question, in the user's language: **ship it, or change it?**

---
name: td-reel
description: >-
  Make a finished faceless short - TikTok, Reel or Short, 9:16 MP4 - from a script: voice-over
  (natural English voice, any Piper voice, or the creator's own recordings), word-by-word captions,
  hook text, a background video / images, progress bar and ducked music. Use for "make the video",
  "render this story", "turn this script into a TikTok", "storytime video", "make part 1, 2, 3".
---

# td-reel

The script is the hard part. Once it exists, the video should be one command, not an hour in an
editor.

Tools live in this skill's `scripts/` folder and run on plain Python 3 with no installs. Run them -
do not eyeball what a tool can measure. Every tool takes `--json` and `--help`.

```bash
python3 scripts/reel.py story.txt -o part1.mp4 --voice kokoro:af_heart --bg slime.mp4 --style storytime
python3 scripts/reel.py story.txt -o part1.mp4 --audio-dir recordings/ --bg images/ --pad
python3 scripts/reel.py story.txt -o part1.mp4 --narration take.m4a --transcript take.json --bg clip.mp4
python3 scripts/reel.py story.txt --check -o x.mp4       # what would be made, no render
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

## 1. The script file

Write it (or take it from `/td-script` / `/td-series`) in this format - one spoken line per line:

```
# hook: She didn't know he was listening
# hook-until: 3
# label: PART 1
# lang: en
My sister was holding my wedding dress over the fireplace.
I had walked in five minutes too early.
```

- Keep lines short - one breath each. Every line is one voice take and one caption run.
- A name the voice mispronounces gets a spoken form: `Decebalus || Deh-cheh-bal`.
- `# hook:` is the on-screen text for the first seconds - different words from the first spoken
  line (score both with `/td-script`'s hookscore).
- For a series, make one file per part with `# label: PART n` - same style for every part.

## 2. The voice - say plainly which one, and what it will sound like

| option | languages | quality | needs |
| --- | --- | --- | --- |
| `--audio-dir` / `--narration` (the creator's own voice) | any | best, most trusted | phone recordings |
| `--voice kokoro:af_heart` (or `am_michael`, `bf_emma`...) | **English only** | natural | `pip install kokoro-onnx`; ~340 MB model downloaded once from GitHub |
| `--voice piper:/path/voice.onnx` | Czech, Russian, Romanian and many more | clearly synthetic | `pip install piper-tts` + a Piper voice file |
| `--audio-dir` with voice files from `/td-generate` (ElevenLabs) | Czech, Russian, Romanian, English... | natural | the ElevenLabs connector, credits |
| `--voice none` | any | captions only | nothing |

**For Czech, Russian and Romanian, recommend the creator's own recording or an ElevenLabs voice
(`/td-generate`, one file per line) first** - the free offline voices in those languages sound robotic, and a robotic narrator costs retention. Ask for
either one file per line (`01.m4a`, `02.m4a`... in a folder, same order as the script) or one take
of the whole script; with one take, a Whisper JSON transcript gives exact caption timing (without
it, captions are spread over the take and drift).

Never imitate a real person's voice that is not the user's own.

## 3. Background, style, music

- `--bg` a gameplay / slime / b-roll video (looped and cropped to 9:16), an image, a folder of images
  (slow zoom on each - good for history), or a colour like `"#0B0D14"`. Only footage the user has the
  rights to: their own, licensed or royalty-free - say so if they point at a film or someone's video.
- `--style storytime` (yellow current word), `clip` (black boxes, film-page look), `bold`, `minimal`.
- `--music track.mp3` is ducked under the voice automatically; `--pad` adds a quiet built-in synth
  bed. On TikTok / Instagram a trending sound added in the app usually helps reach more - then
  render without music.

## 4. After rendering

Grab two or three frames (`ffmpeg -ss 2 -i out.mp4 -frames:v 1 f.png`) and look at them before
handing over: captions inside the safe zone, hook readable, background not fighting the text.
Then `/td-cover` for the cover and `/td-crosspost` for the captions.

## The gate

Nothing here publishes. This skill writes; the user posts. Every run ends with a block the user can
copy as it is, and the last line is the question, in the user's language: **ship it, or change it?**

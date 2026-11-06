---
name: td-edit
description: >-
  Turn a raw recording's transcript into an edit decision list - dead air, filler words and
  retakes, with timecodes - in English, Czech, Russian or Romanian, and say whether it fits a
  Short / TikTok / Reel length. Use for "edit this", "cut the dead space", "tighten this", "I
  rambled", "make this fit 60 seconds".
---

# td-edit

An edit decision list from a timestamped transcript. It prints the cuts. The user applies them.

Tools live in this skill's `scripts/` folder and run on plain Python 3 with no installs. Run them -
do not eyeball what a tool can measure. Every tool takes `--json` and `--help`.

```bash
python3 scripts/deadair.py transcript.srt                  # .srt, .vtt (YouTube auto-captions ok), whisper .json
python3 scripts/deadair.py transcript.srt --floor 0.35     # tighter, for short-form
python3 scripts/deadair.py transcript.srt --target 60      # will it fit a 60 s Short / Reel?
python3 scripts/deadair.py transcript.srt --lang ru --json
```

No transcript yet? Ask for one, or make one first - `whisper` / `faster-whisper`, CapCut's
auto-captions exported as .srt, or YouTube's caption track on an unlisted upload (rolling
auto-captions are de-duplicated by the loader). Never guess at timings.

## What it finds

- **DEAD** - gaps over the floor, trimmed from the middle so both sides keep a breath. Short-form
  wants a tighter floor (`--floor 0.3`) than long-form (`0.45`).
- **FILLER** - cues that are only "um", "ehm", "ну", "păi" and friends, in the detected language.
- **REPEAT** - a restarted sentence, compared against the last cue that was speech.

## What it will not do

It does not touch media and has no opinion about B-roll or music. The percentage is of SPEECH: a
long silent demo makes it wrong. For narrated or storytime content, dead air is often deliberate
music space - ask before cutting it. If `--target` says it is still over, the fix is cutting
content, not pauses: say which beat to drop.

## The gate

Nothing here publishes. This skill writes; the user posts. Every run ends with a block the user can
copy as it is, and the last line is the question, in the user's language: **ship it, or change it?**

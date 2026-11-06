---
name: td-script
description: >-
  Write a script for YouTube, YouTube Shorts, TikTok or Instagram Reels from a raw idea - five hooks
  off 26 formulas, scored in the account's language, then the full script with the on-screen text
  and retention beats marked. Works for talking-head, narrated, storytime, film-clip, history and
  series formats in English, Czech, Russian and Romanian. Use for "write a script", "hook",
  "opening line", "what should I say", "write my next video / TikTok / Reel", or a story to narrate.
---

# td-script

One idea into a script somebody finishes.

@@TOOLS

```bash
python3 scripts/hookscore.py hooks.txt --platform tiktok --format storytime   # rank hook options
python3 scripts/hookscore.py --hook "one line" --platform youtube              # score one
python3 scripts/hookscore.py --hook "..." --kind onscreen --platform instagram # on-screen text
```

`--platform youtube | shorts | tiktok | instagram`, `--format talking-head | narrated | storytime |
clip | history | series`, `--lang en | cs | ru | ro` (detected when omitted).

@@BEFORE

## The hook window depends on the platform

- **YouTube long-form: the first 15-30 seconds.** Confirm the click the title promised, open a
  question the viewer cannot close, prove the payoff exists.
- **Shorts, TikTok, Reels: the first 1-3 seconds.** Two hooks fire at once - the spoken / first
  line and the on-screen text - and they must not use the same words. The text says what to watch
  for; the voice starts the story.

## The process

1. **Hooks.** Write FIVE against `scripts/hooks.json`, preferring formulas whose `formats` include
   this account's format. Score them with `hookscore.py` using the right `--platform` and
   `--format`. Keep the top two and show both with their panels. Never hand over only one.
   For short-form also write and score the on-screen text (`--kind onscreen`).
2. **The turn.** Long-form 0:15-0:45, short-form seconds 3-8: say what the video will do in one
   sentence and start doing it. No channel intro, no "before we start", no subscribe pitch.
3. **The body.** One idea per beat. Mark every beat with `[ON SCREEN: ...]` - for a talking head
   what is shown, for narrated / storytime / clip formats what the footage and the text overlay do.
   Short-form: a new visual or a new beat every 2-4 seconds.
4. **The payoff.** Deliver what the hook promised, explicitly.
5. **The close.**
   - long-form: one ask, not three.
   - short-form standalone: end on a line that loops into the first line, so a rewatch makes sense.
   - **series part:** end on an open question that the next part answers. Do not resolve it. Do not
     add "follow for part 2" over the last line - say it in the caption or a pinned comment.

## Format notes

- **storytime** - first person, past tense, short sentences. Open in medias res or on the
  confession. Name people by role ("my mother-in-law"), not by name, unless the account does.
- **clip** - the script IS the overlay text plus the subtitles. Two to six words at the top of the
  frame, inside the safe zone. Never caption what happens; caption what to watch for.
- **history** - one specific scene, a year, a place, a sensory detail. Mark dramatised details.
- **series** - each part continues exactly where the last stopped. No recap montage and no teaser
  of a later moment at the start of a part (unless the profile says otherwise). If the user
  splits one long script into parts, use `/td-series`.

## What to hand back

- the two best hooks with their scored panels (plus on-screen text for short-form)
- the script, beat by beat, with `[ON SCREEN: ...]` on every beat
- the runtime at ~150 words per minute (Czech / Russian / Romanian read slower - use ~130), and a
  warning if it is over the platform's ceiling (`scripts/platforms.json`)
- one line naming the winning formula and why it fits this idea

@@GATE

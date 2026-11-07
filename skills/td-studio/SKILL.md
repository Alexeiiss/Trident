---
name: td-studio
description: >-
  Edit video like CapCut, locally and without credits - trim, cut, split, join with 25 transitions,
  speed and speed ramps, smooth slow motion, reverse, freeze, reframe to 9:16 with blurred
  background, zoom punch-ins, text titles, word captions, picture-in-picture, stickers, green screen,
  colour filters and LUTs, blur/pixelate, stabilize, voice effects, denoise, music with ducking, sound
  effects, auto-cut silences, beat-synced cuts and platform export. Use for "edit this video",
  "add a transition", "slow motion", "green screen", "make it 9:16", "add music", "cut on the beat",
  "remove the silences", "like in CapCut".
---

# td-studio

Every operation reads one video and writes a new one, so an edit is a chain of short commands.
Keep each step's output (`step1.mp4`, `step2.mp4`...) until the user approves the final one - an
undo is just going back one file.

Tools live in this skill's `scripts/` folder and run on plain Python 3 with no installs. Run them -
do not eyeball what a tool can measure. Every tool takes `--json` and `--help`.

```bash
python3 scripts/studio.py ops                    # every operation
python3 scripts/studio.py <op> --help            # its options
python3 scripts/studio.py info clip.mp4          # duration, size, fps, audio
```

## CapCut feature -> command

| CapCut | command |
| --- | --- |
| Split / Delete | `split in.mp4 out.mp4 --at 3.2,7` · `cut in.mp4 out.mp4 --remove "3.2-4.1,9-10"` |
| Trim | `trim in.mp4 out.mp4 --start 1.5 --end 12` |
| Auto-remove silences | `silence in.mp4 out.mp4 --threshold -35 --min 0.45` |
| Apply an edit list | `cut in.mp4 out.mp4 --edl cuts.json` (from `/td-edit`'s `deadair.py --json`) |
| Join + transitions | `join out.mp4 a.mp4 b.mp4 c.mp4 --transition slideup --duration 0.4 --aspect 9:16` (25 transitions, `mix` rotates them, `none` hard cuts) |
| Speed / Curve | `speed in out --factor 2` · `speed in out --factor 0.5 --smooth` · `ramp in out --points "0:1,2:0.4,3.5:2"` |
| Reverse / Freeze | `reverse in out` · `freeze in out --at 4.2 --duration 1` |
| Canvas 9:16 / blur background | `reframe in out --aspect 9:16 --mode blur` (or `crop --focus 0.3`, `fit`) |
| Zoom / punch-in | `zoom in out --mode punch --at 1.2,4.8` · `--mode in` slow push |
| Mirror / Flip / Rotate | `transform in out --mirror` · `--mirror split` · `--vflip` · `--rotate 90` |
| Stabilize | `stabilize in out` |
| Filters / Adjust | `color in out --preset cinematic` (vivid, warm, cool, bw, vintage, teal-orange, fade, dramatic, night) · `--brightness 0.05 --contrast 1.1 --saturation 1.2 --temperature 5000` · `--lut film.cube` · `--vignette --grain --sharpen` |
| Mosaic / blur | `blur in out --region 400,300,220,220 --style pixel --start 2 --end 5` |
| Text | `text in out --text "PART 2" --pos top --anim pop --box --start 0 --end 3` (pop, fade, slide) |
| Auto captions | `captions in out --transcript take.json --style storytime --hook "..."` |
| Overlay / PiP / Sticker | `overlay in out --layer face.mp4 --pos bottom-right --scale 0.3 --round` · `--layer logo.png --pos top-left --scale 0.12 --opacity 0.8` · green-screen sticker `--key 0x00FF00` |
| Chroma key | `chroma greenscreen.mp4 out --background city.mp4` |
| Voice effects / Enhance | `audio in out --voice deep` (chipmunk, robot, echo, radio, phone, hall, monster) · `--denoise --normalize` · `--volume 0.8` · `--mute` |
| Extract / replace audio | `audio in x --extract voice.wav` · `audio in out --replace narration.wav` |
| Music | `music in out --track song.mp3 --volume 0.25 --duck` |
| Sound effects | `sfx in out --add whoosh.wav@1.2 --add ding.mp3@4*0.6` |
| Beat sync | `beats song.mp3` · `beatcut out.mp4 a.mp4 b.mp4 c.mp4 --music song.mp3 --every 2 --max-length 20` |
| Fade in/out | `fade in out --in 0.4 --out 0.8` |
| Export | `export in out --platform tiktok` (reels, shorts, youtube - size, 30 fps, loudness, length limit) |
| Cover frame | `frame in cover.jpg --at 3.4` -> `/td-cover` |

## Working the way an editor does

1. `info` every input first. Ask what the video is for (platform, length) if it is not obvious.
2. Rough cut first (trim / cut / silence / join), then picture (reframe, zoom, color), then layers
   (text, captions, overlays), then sound (music, sfx, voice), then `export` last - export once.
3. After every visual step grab a frame and look at it (`frame out.mp4 f.jpg --at 2`), especially
   after text, overlay, reframe and chroma. Check that nothing important sits in the bottom 20% or
   right 15% of a 9:16 frame.
4. Say what each step did in one line, not the command.

## What it does not do - say so instead of faking it

- **AI effects** (body effects, AI background removal, auto-face-tracking reframe, AI upscale,
  text-to-video): use `/td-generate` (ElevenLabs has background removal, upscale, lipsync and video
  generation), then bring the file back here.
- **Templates and the sticker / sound library** - bring your own files (only ones you have the rights to).
- **Free keyframe animation of any property** - zoom, ramp and text animations cover the common cases.
- **Speech-to-text** - for captions, get a transcript first (Whisper, or ElevenLabs Scribe via `/td-generate`).

## The gate

Nothing here publishes. This skill writes; the user posts. Every run ends with a block the user can
copy as it is, and the last line is the question, in the user's language: **ship it, or change it?**

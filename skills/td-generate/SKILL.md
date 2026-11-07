---
name: td-generate
description: >-
  Generate images, video clips, voice-over (including natural Czech, Russian and Romanian voices),
  music, sound effects, dubbing, lip-sync, background removal and upscaling for YouTube, TikTok and
  Instagram content through the ElevenLabs connector, with consistent characters and 9:16 framing,
  then hand the files to td-studio / td-reel. Use for "generate an image", "make a video of",
  "AI video", "voice-over in Czech", "background music", "dub this into Russian", "remove the
  background", "consistent character".
---

# td-generate

Generation costs the user's credits and returns variations, not answers. The skill is choosing the
right model, writing prompts that hold a look across a whole series, and getting the results into
the edit.

**Needs the ElevenLabs connector** (its `creative_*` tools). If it is not connected, say so in one line,
offer to connect it, and meanwhile use the user's own footage with `/td-studio` and `/td-reel`.

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

## Before generating

1. Call `creative_get_flow_node_types` - the available models change; never assume a model id.
   Before prompting a model you have not used in this session, read `creative_get_model_guide`.
2. Make ONE flow per project (`creative_create_flow`) and pass its `flow_id` to every call - nodes on
   different flows cannot feed each other, and the user gets one canvas with everything.
3. Credits: say roughly what is about to be generated (e.g. "6 images, then 6 clips of 5 s").
   Confirm before any video longer than ~10 s or more than ~6 clips at once. Never repeat a call to
   "retry" - every call charges again. Leave `generations_count` at its default.

## Picking a model (check the live list first)

| job | good first choice | why |
| --- | --- | --- |
| images with readable text (covers, titles) | GPT Image / Ideogram | best at typography |
| photoreal scenes, people, places | Nano Banana Pro / Seedream / FLUX | realism, reference-image control |
| illustration, flat, vector, logos | Recraft | clean shapes, SVG |
| edit an existing image | `creative_edit_image` (Nano Banana / FLUX Kontext) | keeps the rest of the picture |
| image -> video (animate a still) | Kling / Seedance / Veo with the image as `start_frame` | most control over the shot |
| text -> video with sound | Veo 3.1 / Seedance 2.x (`generate_audio`) | native audio |
| talking avatar / lip-sync | OmniHuman, Sync, HeyGen Avatar, Creatify | face + voice |
| voice-over | `creative_generate_speech`, Eleven v3 / v4, `language_code` cs / ru / ro / en | natural in all four languages |
| music | Eleven Music (instrumental for voice-over beds) | length up to 10 min |
| sound effects | Eleven SFX (whoosh, impact, ambience; `loop` for beds) | |
| dub a finished video | Dubbing (video) to ru / ro / en | keeps timing |
| remove background / upscale | Background Removal, Topaz Upscale | |

Always set `aspect_ratio` 9:16 for TikTok / Reels / Shorts and 16:9 for long YouTube.

## Consistency across a series (the part people get wrong)

1. **Style line** - write one sentence of style once ("cinematic, overcast Carpathian light, muted
   earth tones, 35 mm, film grain") and append it to every prompt of the project, word for word.
2. **Character sheet** - generate the main character once (front, side, full body), let the user
   pick the take, pin it with `creative_add_flow_asset_node`, and connect it as a reference image to
   every later image of that character.
3. **Shot list from the script** - one image per beat of the `/td-script` / `/td-series` script, then
   animate the chosen images (image -> video, 5 s each, simple camera moves: slow push, pan, orbit).
   Motion prompts describe camera and one action, not a story.
4. **Voice** - pick one voice per account (`creative_list_voices` filtered by language) and keep it.
   For Czech, Russian and Romanian this replaces the robotic offline voices in `/td-reel`.

## Getting it into the edit

Results live on the flow (the user opens it from the link). For the local tools, ask the user to
download the chosen files and attach them (or use a direct link if one is given), then:
`/td-reel` (script + generated voice files via `--audio-dir` + generated images as `--bg folder/`),
or `/td-studio` (`join` the clips with transitions, `music`, `captions`, `export`).
ElevenLabs' own Composition node can also stack clips + voice + music on the flow.

## Rules

- No real person's likeness or voice without their consent; never a famous person's voice or face;
  no copyrighted characters or logos.
- History content: label reconstructions as reconstructions.
- TikTok, Instagram and YouTube require the "AI-generated" label on realistic AI images / video -
  remind the user to switch it on when posting.

## The gate

Nothing here publishes. This skill writes; the user posts. Every run ends with a block the user can
copy as it is, and the last line is the question, in the user's language: **ship it, or change it?**

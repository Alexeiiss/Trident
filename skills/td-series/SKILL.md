---
name: td-series
description: >-
  Plan, split and diagnose multi-part series on TikTok, Instagram and YouTube - where to cut a long
  story so every part ends on a hook, how many parts to use, and which handoff between parts is
  losing the audience and why. Use for "split this into 3 parts", "part 2", "my series loses views",
  "how many parts", "people don't watch the next part", or any numbered series.
---

# td-series

Every handoff between parts loses people. A series earns its parts only when each one ends on a
question the next one answers - and the most common way to lose part 2 is a part 1 that resolves
too much, or a part 2 that opens with a recap the returning viewer already saw.

Tools live in this skill's `scripts/` folder and run on plain Python 3 with no installs. Run them -
do not eyeball what a tool can measure. Every tool takes `--json` and `--help`.

```bash
python3 scripts/series.py stats --views "1:120000,2:41000,3:30500"      # where the audience falls off
python3 scripts/series.py stats parts.csv          # columns: part, views[, completion]
python3 scripts/series.py split story.srt --parts 3 --platform tiktok   # where to cut
python3 scripts/hookscore.py --hook "..." --format series --platform tiktok
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

## Diagnose an existing series

Ask for the views of each part (and the "watched full video" / completion % if they have it - it is
what separates the two causes). Run `series.py stats`.

- **Carry** = views of part N ÷ views of part N-1. The worst handoff is the one to fix.
- **ENDING problem** - the previous part had low completion: people left before the cliffhanger. Fix
  that part's last third (cut, raise the tension earlier).
- **HANDOFF problem** - the previous part was finished but people did not come for the next. Fix the
  link: the last line, the "Part 2" cover, the time between posts, a pinned comment / playlist /
  series link to the next part.
- If carry from part 1 to 2 is under ~50%, fewer and longer parts beat more and shorter ones. Say so,
  and give the number of parts the data supports.

## Split a story into parts

Get a timestamped transcript (or the script with estimated timings). Run `series.py split` with the
number of parts and the target platform. It picks cuts at real pauses near equal lengths, prefers a
last line that leaves a question open, flags a part whose last line resolves, and checks each part
against the platform ceiling. Then:

- For every cut that is flagged, propose either a cut a few lines earlier/later or a rewritten last
  line that opens a question instead of closing one.
- **Part 2+ starts exactly where the previous part stopped.** No recap, no teaser of a later moment,
  unless the account's profile asks for one. If a new viewer needs context, give it in ONE line
  woven into the first sentence (The Continuation formula), and put "Part N" in the cover text.
- Write the cover text for every part so the grid reads as a sequence: same template, the part
  number large, a different promise each time.
- Caption: say where part 1 is (playlist / series / pinned) - never ask for a follow over the story.

## Plan a new series

Decide the parts from the story beats, not from a number: a part ends where the story turns.
Prefer 3 parts over 8. Plan the release gap (same time each day keeps returning viewers).

## The gate

Nothing here publishes. This skill writes; the user posts. Every run ends with a block the user can
copy as it is, and the last line is the question, in the user's language: **ship it, or change it?**

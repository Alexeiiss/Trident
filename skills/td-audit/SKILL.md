---
name: td-audit
description: >-
  Audit one creator account on YouTube, TikTok or Instagram end to end - packaging, the first
  seconds, consistency, format fit and series handoffs - and end on ONE fix. Use for "audit my
  channel / account", "why isn't it growing", "review my videos", "what am I doing wrong", or a
  pasted profile URL.
---

# td-audit

An audit that lists twenty problems is a way of avoiding the one that matters. This ends in ONE fix.

Tools live in this skill's `scripts/` folder and run on plain Python 3 with no installs. Run them -
do not eyeball what a tool can measure. Every tool takes `--json` and `--help`.

```bash
python3 scripts/package.py --platform youtube titles.txt        # or --platform tiktok covers.txt
python3 scripts/hookscore.py openings.txt --platform tiktok --format storytime
python3 scripts/series.py stats --views "1:52000,2:14000,3:9800"
python3 scripts/stats.py "Table data.csv"          # the trend, from the platform export
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

## What to look at, in this order

1. **The last ten click surfaces, as a set.** Titles (YouTube) or covers + first caption lines
   (TikTok, Instagram), read the way the profile grid shows them. Run them through `package.py` for
   the platform. If every one is the same shape, it is a format problem, not a title problem.
2. **At feed size.** Shrink the thumbnails / covers. If three are unreadable, that is the fix and
   nothing else matters yet.
3. **The first seconds of the three most recent** - 15 s on long-form, 3 s on short-form. Transcribe
   and score with `hookscore.py --platform <p> --format <f>`. This is where most accounts lose.
4. **Rhythm and trend** - consistency, not frequency; bursts then silence lose to a steady pace.
   With an export, `stats.py` shows the weekly medians and whether the account is growing.
5. **Series handoffs** - if the account posts parts, run `series.py stats` on the views per part.
6. **Retention**, if they can export or screenshot it - `/td-retention`.
7. **Platform fit** - if the same content works on one platform and dies on another, say whether
   to adapt it (`/td-crosspost`) or drop that platform.

## What to hand back

- The single biggest fix, named, with what to do this week.
- Three things that already work, so they do not break them. Specific: "your energy is good" is not
  an observation.
- What NOT to do yet, and why.

Never open with praise you do not mean, and never end with a list of twenty things.

## The gate

Nothing here publishes. This skill writes; the user posts. Every run ends with a block the user can
copy as it is, and the last line is the question, in the user's language: **ship it, or change it?**

---
name: td-package
description: >-
  Write and lint the click surface as one pairing - YouTube title + thumbnail text, Shorts title +
  opening text, TikTok / Instagram cover text + caption first line - checking truncation,
  duplication and vagueness in the account's language. Use for "title ideas", "what should I call
  this", "thumbnail text", "cover text", "my CTR is bad", or renaming an existing video.
---

# td-package

What people see before they watch is ONE unit. Writing its parts separately is why packaging
fails: the thumbnail repeats the title, the cover repeats the caption, and half the click surface
says the same thing twice.

Tools live in this skill's `scripts/` folder and run on plain Python 3 with no installs. Run them -
do not eyeball what a tool can measure. Every tool takes `--json` and `--help`.

```bash
python3 scripts/package.py --platform youtube --title "..." --thumb "3 WORDS MAX"
python3 scripts/package.py --platform youtube titles.txt --thumb "..."       # rank ten titles
python3 scripts/package.py --platform shorts --title "..." --cover "..."
python3 scripts/package.py --platform tiktok --cover "..." --first-line "..." --format storytime
python3 scripts/package.py --platform instagram covers.txt --first-line "..."
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

## What each platform shows

| surface | what is seen | limits the tool checks |
| --- | --- | --- |
| YouTube | title + thumbnail | 60 chars desktop, ~40 mobile, 100 hard; 3 words on the thumbnail |
| Shorts | title (~40 visible) + the first frame's text | 100 hard; image text ≤ 6 words |
| TikTok | cover text + caption first line (~100 chars) | cover ≤ 6 words |
| Instagram | cover text in the grid + caption first line (~125 chars) | cover ≤ 6 words; keep text out of the bottom 20% |

## Write ten, keep two

Generate ten options, run them all through `package.py` with the account's `--format`, show the top
three with their score and the specific issue on each. For the winner write the image brief: the
expression or the frame to grab, the text and where it sits, and what the background must do to
hold contrast at feed size. For `clip` accounts, name the exact moment of the clip to use as the
cover.

A number, a name, a place or a date beats any adjective. It is required on talking-head YouTube and
only a hint for storytime, clip and history, where a person or a scene does the same job.

## The gate

Nothing here publishes. This skill writes; the user posts. Every run ends with a block the user can
copy as it is, and the last line is the question, in the user's language: **ship it, or change it?**

---
name: td-plan
description: >-
  Plan a week or a month of posts across YouTube, TikTok and Instagram for one or several accounts -
  what to post, where, when and in what order, sized to the hours the creator really has. Use for
  "plan my week", "content calendar", "what should I post", "posting schedule", "I have no idea what
  to make next".
---

# td-plan

A plan that does not fit the week is a list of regrets. Ask two things before writing anything:
**how many hours do you actually have**, and **what is already half-made**.

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

## Shape the week around one source

- **One anchor** - the piece the week is built on: a long video, a story, or a series.
- **Cut, do not write separately** - the short-form posts come out of the anchor (`/td-clips`,
  `/td-series`), get rendered (`/td-reel`) and covered (`/td-cover`), then go to each platform with
  their own packaging (`/td-crosspost`). Check last week first with `/td-stats`.
- **One cheap one** - built from what exists: a reply to the most-asked comment, a follow-up, a
  re-cut of last week's best performer with a new first line.

Cadence comes from the profile and the user, not from this file. A creator posting twice a day to
TikTok and once a week to YouTube gets that plan - just check the hours add up. Posting times: ask
for the account's own best times (each platform's analytics shows when followers are online); do
not assume.

For series: release parts on consecutive days at the same time, and never let a part wait more than
~48 h unless the profile says otherwise - returning viewers forget.

Multiple accounts in different languages: plan them in one table, but never let one account's
schedule decide another's. If one platform has stopped working for an account, say so and suggest
dropping it rather than spreading the same hours thinner.

## What to hand back

A table: day, time, account, platform, format, working title / cover text, the one sentence it
promises, and what already exists for it. Under it, the honest line: how many hours this costs, and
what to drop first if the week goes wrong.

## The gate

Nothing here publishes. This skill writes; the user posts. Every run ends with a block the user can
copy as it is, and the last line is the question, in the user's language: **ship it, or change it?**

---
name: td-profile
description: >-
  Create or update the profile for one creator account (YouTube, TikTok or Instagram) - language,
  format, audience, voice and rules - that every other Trident skill reads. Use for "set up my
  channel", "new account", "write my profile", "learn my style", "my voice", or when another td-
  skill finds no profile.
---

# td-profile

Every other skill in this pack is only as good as this file. A script in the wrong voice is
unusable when you have to read it aloud; a caption in the wrong register is scrolled past.

**One profile per account, not per person.** If the user runs a Russian storytime TikTok, an
English history YouTube channel and a Romanian TikTok, that is three profiles.

## The interview

Ask in the user's language, a few questions at a time, never all at once. Skip what you can read
from material they give you.

1. **Account** - handle, platform(s) it posts to, link if they have one.
2. **Language** of the content (and of the audience, if different).
3. **Format** - pick one or two: `talking-head` (they speak on camera), `narrated` (voice-over on
   footage), `storytime` (a told story over satisfying / gameplay footage), `clip` (film or found
   footage with on-screen text), `history` (narrated past, documentary tone), `series` (multi-part).
4. **Who it is for** - one person, described properly. Not "people who like history", but "a
   Romanian in his 30s who scrolls TikTok on the bus and half-remembers the Dacians from school".
5. **Voice** - ask for three of their best videos (links, transcripts, or the captions). Read them
   and write down how they actually sound, not how they wish they sounded.
6. **Never / always** - words and moves that are not theirs; tics and phrases that are.
7. **Will not claim** - numbers they cannot show, results that are not theirs, "true story" when it
   is not.
8. **On-screen style** - where text goes, how many words, subtitles yes/no, cover style.
9. **Rhythm and capacity** - how many posts a day / week they can really sustain, and what time.
10. **What worked** - the top 3 and bottom 3 posts by views, if they know them.
11. **Series rules** - e.g. "parts follow on directly, no recap and no teaser at the start".

## Writing the file

Fill `templates/profile.md` (in this skill's folder). Save it as
`./creator-profiles/<handle>.md` when there is a working folder, otherwise
`~/.claude/trident/profiles/<handle>.md`, and **also hand the file to the user** - in a chat
session the workspace does not persist, and the user should keep the file and attach it next time
(or put it in a Project so every chat sees it).

Show the finished profile and ask: **is this you, or change it?** When later work gets corrected
("I would never say that"), offer to add the correction to the profile.

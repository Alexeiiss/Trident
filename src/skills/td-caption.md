---
name: td-caption
description: >-
  Write and lint the search-facing text for one platform - YouTube description and tags, TikTok
  caption and keywords, Instagram caption, max-5 hashtags and alt text - aimed at what a real
  person types. Use for "write my description", "caption", "hashtags", "tags", "SEO", "help this
  get found", "nobody finds my videos".
---

# td-caption

Search is a smaller lever than packaging everywhere, and a bigger one than people think on
TikTok, where the search bar is a real discovery route. For a video aimed at existing followers,
say so and spend the effort on `/td-package` instead.

@@TOOLS

```bash
python3 scripts/caption.py --platform instagram caption.txt --keywords "dacians,ancient rome"
python3 scripts/caption.py --platform instagram caption.txt --first-comment comment.txt
python3 scripts/caption.py --platform tiktok --text "..." --keywords "..."
python3 scripts/caption.py --platform youtube description.txt --keywords "..."
```

@@BEFORE

## First: the three queries

Before writing anything, write the three searches this video should win, **in the account's
language** - the words a viewer would type, not the words a creator would use. Everything below is
built to contain them.

## Per platform

**YouTube (long-form and Shorts)**
- The first ~150 characters are the snippet and the only part most people read: what the video
  gives them, in the words of the queries.
- Then the link or resource, then chapters (`/td-chapters`), then the long version.
- Hashtags: the first three show above the title. Over 15 and YouTube ignores all of them.
- Tags are a weak signal: use them for spellings, transliterations (Дакия / Dacia / Dákové) and
  names, then stop. Under 500 characters total.

**TikTok**
- The first ~100 characters show in the feed. Hook + the main keyword there.
- A 1-3 sentence caption with the searchable words beats a wall of hashtags. 3-5 specific hashtags;
  no #fyp / #viral - they describe every video and this one says nothing.
- Say the keyword out loud in the first seconds and put it in the on-screen text too: TikTok reads
  speech and overlays for search.

**Instagram**
- The first ~125 characters show before "more". Hook first, keyword in the first sentence.
- **Five hashtags, hard cap** (since December 2025) - and hashtags in the first comment count toward
  the same five. Pick the five most specific.
- Write alt text (under ~100 characters): what is actually in the frame. It is read for search and
  by screen readers.

## The fold test

Run `caption.py` with `--keywords` set to the words of the three queries. If they are not above the
fold, fix the first line - and if they are not in the title or cover either, the problem is the
packaging, not the caption.

@@GATE

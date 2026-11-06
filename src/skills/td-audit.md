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

@@TOOLS

```bash
python3 scripts/package.py --platform youtube titles.txt        # or --platform tiktok covers.txt
python3 scripts/hookscore.py openings.txt --platform tiktok --format storytime
python3 scripts/series.py stats --views "1:52000,2:14000,3:9800"
```

@@BEFORE

## What to look at, in this order

1. **The last ten click surfaces, as a set.** Titles (YouTube) or covers + first caption lines
   (TikTok, Instagram), read the way the profile grid shows them. Run them through `package.py` for
   the platform. If every one is the same shape, it is a format problem, not a title problem.
2. **At feed size.** Shrink the thumbnails / covers. If three are unreadable, that is the fix and
   nothing else matters yet.
3. **The first seconds of the three most recent** - 15 s on long-form, 3 s on short-form. Transcribe
   and score with `hookscore.py --platform <p> --format <f>`. This is where most accounts lose.
4. **Rhythm** - consistency, not frequency. Bursts then silence lose to a steady pace.
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

@@GATE

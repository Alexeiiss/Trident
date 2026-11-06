---
name: td-chapters
description: >-
  Write YouTube chapters from a transcript, validated against YouTube's rules so they actually
  render, in the video's language. Long-form YouTube only. Use for "add chapters", "timestamps",
  "break this video into sections".
---

# td-chapters

@@TOOLS

```bash
python3 scripts/chapters.py transcript.srt --target 8
python3 scripts/chapters.py transcript.srt --lang cs --json
```

## The rules, which are not optional

A chapter list that breaks any of these silently does not become chapters - the block just sits in
the description:

- the first entry is **0:00**
- there are **at least three**
- each is **at least 10 seconds**

The tool checks all three and says when a list is invalid. `/td-caption`'s `caption.py` re-checks
chapters inside a finished description.

## Retitle every line

`chapters.py` finds the BOUNDARIES well - pauses scored by how much the vocabulary shifts across
them. The titles it prints are topic words: a draft. Rewrite each as the promise of that section,
in the account's voice and language, three to five words.

Chapters are also a retention diagnostic: a section that cannot be named in five words is two
sections, or filler.

TikTok and Instagram have no chapters. For a long video going to short-form, use `/td-clips` or
`/td-series`.

@@GATE

# Trident 🔱

*Three prongs, one pack: YouTube, TikTok and Instagram.*

**Eighteen Claude skills for creators on YouTube, TikTok and Instagram — in English, Czech, Russian
and Romanian.** No API key, nothing to connect, no signup. Plain Python 3 tools; the analysis tools need nothing else, the video and cover tools need ffmpeg and Pillow.

Most creator prompt packs assume one thing: an English-speaking person talking to a camera on
YouTube. Trident assumes what creators actually run in 2026 — several accounts, several
languages, the same video going to three platforms, faceless formats (narrated, storytime, film
clips, history) and multi-part series that bleed viewers at every part.

**Nothing gets published until you do it.** These skills write. You post.

## What is different

- **Three platforms, current limits.** Instagram's 5-hashtag cap (first comment included), TikTok's
  ~100-character caption fold, Shorts' ~40 visible title characters, Reels' 3-minute Reels-tab
  ceiling — in one `platforms.json`, checked November 2026, used by every tool.
- **Four languages, really.** The hook scorer, linters, filler detector and chapter finder read
  Czech, Russian (Cyrillic) and Romanian, with inflection-aware stems. The same hook scores within a
  few points in all four languages.
- **One profile per account.** A Russian storytime TikTok and an English history channel never share
  a voice.
- **Formats beyond talking-head.** 26 hook formulas tagged by format, including In Medias Res, The
  Confession, The Time Machine, The Caption Tease and The Continuation (for part 2+).
- **Series.** Split a story so each part ends on a hook; find which handoff loses the audience and
  whether it is the previous part's ending or the next part's packaging.

## The eighteen

| command | what it does |
| --- | --- |
| `/td-profile` | The account's profile — language, format, audience, voice, rules. Every skill reads it. |
| `/td-script` | One idea into a script: five hooks scored for the platform and format, then the script with `[ON SCREEN]` on every beat. |
| `/td-package` | Title + thumbnail (YouTube), title + opening text (Shorts), cover + caption first line (TikTok / Reels), linted as one pairing. |
| `/td-caption` | Description / caption, hashtags and alt text for one platform, built around three real search queries. |
| `/td-crosspost` | One video → a ready-to-paste package for YouTube, TikTok and Instagram, each linted. |
| `/td-series` | Split a story into parts that end on hooks; diagnose part-to-part drop-off. |
| `/td-clips` | The Shorts / TikToks / Reels already inside a long video, with a new first line and on-screen text. |
| `/td-edit` | A transcript into an edit decision list: dead air, filler, retakes — and whether it fits 60 s. |
| `/td-retention` | Retention read properly for long-form and short-form: hook leak, cliffs, slide, the one fix. |
| `/td-chapters` | YouTube chapters validated against YouTube's rules. |
| `/td-plan` | A week across platforms and accounts that fits the hours you have. |
| `/td-trends` | What is working in a niche, ranked by multiple over each account's own median. |
| `/td-comment` | Comments triaged into four piles, replies in the account's voice and language, what to pin. |
| `/td-audit` | The whole account, ending in ONE fix rather than twenty. |
| `/td-reel` | **New in 1.1.** A script into a finished 9:16 short: voice (natural English voice, any Piper voice, or your own recordings), word-by-word captions, hook text, background video or images, progress bar, ducked music. |
| `/td-subtitles` | **New in 1.1.** Word-by-word captions from a transcript, styled for film clips, storytime or documentary, kept in the safe zone - as `.ass` or burnt in. |
| `/td-cover` | **New in 1.1.** Covers and thumbnails - one post or a matching set for a series - safe zone, grid crop and contrast checked. |
| `/td-stats` | **New in 1.1.** Weekly medians, trend, posts to repeat and to drop, and series carry, from the platforms' own exports. |

## Install

**Claude Code, as a plugin:**

```
/plugin marketplace add Alexeiiss/trident
/plugin install trident
```

Or paste this into Claude:

```
https://github.com/Alexeiiss/trident

Install these skills, then confirm /td-script works.
```

**Claude Code, as plain skills:** copy `skills/td-*` into `~/.claude/skills/` (global) or into your
project's `.claude/skills/`.

**Claude apps (claude.ai / desktop):** download the per-skill zips from the
[`downloads/`](downloads/) folder (all 14 in one: [`trident-claude-ai-skills.zip`](downloads/trident-claude-ai-skills.zip?raw=1), or one by one in [`downloads/skills/`](downloads/skills/)) and upload them in
Settings → Capabilities → Skills. Each zip carries its own tools.

**Building from source:** the skills are generated from `src/` and `shared/` -
`python3 build.py` rebuilds them into `dist/` and runs the tests.

Then make a profile: say `/td-profile` and answer the interview, or send three of your posts and say
"write my profile from these". In the Claude apps, keep the profile file and attach it to a chat or
put it in a Project, so every chat can read it.

## The tools

```bash
python3 shared/hookscore.py --hook "..." --platform tiktok --format storytime   # 5-property hook panel
python3 shared/package.py --platform instagram --cover "..." --first-line "..." # click-surface linter
python3 shared/caption.py --platform instagram caption.txt --keywords "..."     # caption + hashtag linter
python3 shared/deadair.py transcript.srt --target 60                            # edit decision list
python3 shared/chapters.py transcript.srt                                       # validated chapters
python3 shared/retention.py --points "0:100,3:62,10:45,30:30" --platform tiktok # where they left
python3 shared/series.py stats --views "1:120000,2:41000,3:30500"               # series handoffs
python3 shared/series.py split story.srt --parts 3                              # where to cut
python3 shared/trends.py yt-dlp.json --split-shorts --per-day                   # outliers
python3 shared/reel.py story.txt -o part1.mp4 --voice kokoro:af_heart --bg slime.mp4  # finished short
python3 shared/subtitles.py clip.srt --style clip --burn clip.mp4 -o out.mp4    # word captions
python3 shared/cover.py --text "The gold" --parts 3 --label "PART {n}" -o c.png # series covers
python3 shared/stats.py "Table data.csv"                                        # weekly report
python3 tests/run_tests.py                                                      # 29 end-to-end tests
```

Transcripts: `.srt`, `.vtt` (YouTube's rolling auto-captions are de-duplicated) and Whisper `.json`.

## The fine print

- **It does not publish.** Every skill ends in a copy block and one question: ship it, or change it?
- **`hookscore.py` is a heuristic about words, not a predictor.** It separates lazy hooks from real
  ones; it does not separate your hits from your misses. Your analytics outrank it.
- **Platform limits change.** `platforms.json` says when it was checked. If the app disagrees, the
  app is right — update the file.
- **Retention benchmarks are rough.** Your own account's median video is the real baseline.
- **Nothing invents a number.** A skill that wants a figure it does not have asks for it.
- **Read, do not scrape.** `/td-trends` uses public listings only and never your login.

**Voices.** `/td-reel`'s natural voice (Kokoro) speaks English only. For Czech, Russian and Romanian
the free synthetic voices sound robotic - record your own lines on your phone and pass the folder
with `--audio-dir`; it is also what viewers trust most.

## Credits and licence

MIT — see `LICENSE`. Trident is built on and extends
[youtube-agent-skill](https://github.com/Jakeschincariol/youtube-agent-skill) by Jake Schincariol
(MIT), whose original notice is kept in `LICENSE` as the licence requires. The bundled Inter font
(`shared/fonts/`) is © The Inter Project Authors, SIL Open Font License 1.1 (`shared/fonts/OFL.txt`).

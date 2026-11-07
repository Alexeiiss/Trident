#!/usr/bin/env python3
"""build.py - assemble the Trident plugin from src/ and shared/.

    python3 build.py            # writes dist/trident/ and the zips in dist/

Each skill folder in the output is self-contained: the shared tools it needs are copied into its
own scripts/ folder, so a single skill can be uploaded on its own.
"""
import json, os, re, shutil, subprocess, sys, zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC, SHARED = os.path.join(ROOT, "src"), os.path.join(ROOT, "shared")
DIST = os.path.join(ROOT, "dist")
OUT = os.path.join(DIST, "trident")
VERSION = "1.2.0"

DEPS = {"hookscore.py": ["lang.py", "hooks.json", "platforms.json"],
        "package.py": ["lang.py", "platforms.json"], "caption.py": ["lang.py", "platforms.json"],
        "deadair.py": ["lang.py", "transcript.py"], "chapters.py": ["lang.py", "transcript.py"],
        "retention.py": ["platforms.json", "transcript.py"],
        "series.py": ["lang.py", "transcript.py", "platforms.json"],
        "trends.py": ["lang.py", "hooks.json"],
        "subtitles.py": ["transcript.py", "fonts"], "reel.py": ["subtitles.py", "transcript.py", "fonts"],
        "cover.py": ["platforms.json", "fonts"], "stats.py": [],
        "studio.py": ["subtitles.py", "transcript.py", "fonts"]}

TOOLS = {"td-profile": [], "td-script": ["hookscore.py"], "td-package": ["package.py"],
         "td-caption": ["caption.py"], "td-crosspost": ["package.py", "caption.py"],
         "td-edit": ["deadair.py"], "td-clips": ["hookscore.py", "deadair.py"],
         "td-series": ["series.py", "hookscore.py"], "td-chapters": ["chapters.py"],
         "td-retention": ["retention.py"], "td-plan": [], "td-trends": ["trends.py"],
         "td-comment": [], "td-audit": ["package.py", "hookscore.py", "series.py", "stats.py"],
         "td-reel": ["reel.py", "hookscore.py"], "td-subtitles": ["subtitles.py"], "td-cover": ["cover.py", "package.py"],
         "td-stats": ["stats.py", "series.py"], "td-studio": ["studio.py", "deadair.py"], "td-generate": []}

def blocks():
    raw = open(os.path.join(SRC, "blocks.md"), encoding="utf-8").read()
    out = {}
    for part in raw.split("@@")[1:]:
        name, body = part.split("\n", 1)
        out["@@" + name.strip()] = body.strip()
    return out

def main():
    shutil.rmtree(DIST, ignore_errors=True)
    os.makedirs(os.path.join(OUT, ".claude-plugin"))
    b = blocks()
    for skill, tools in TOOLS.items():
        text = open(os.path.join(SRC, "skills", skill + ".md"), encoding="utf-8").read()
        for k, v in b.items(): text = text.replace(k, v)
        left = re.findall(r"@@\w+", text)
        if left: sys.exit(f"{skill}: unexpanded block {left}")
        d = os.path.join(OUT, "skills", skill)
        os.makedirs(d)
        open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8").write(text)
        files = set()
        for t in tools:
            files |= {t, *DEPS[t]}
            for dep in DEPS[t]:
                files |= set(DEPS.get(dep, []))
        if files:
            os.makedirs(os.path.join(d, "scripts"))
            for f in sorted(files):
                src = os.path.join(SHARED, f)
                if os.path.isdir(src): shutil.copytree(src, os.path.join(d, "scripts", f))
                else: shutil.copy(src, os.path.join(d, "scripts", f))
        if skill == "td-profile":
            os.makedirs(os.path.join(d, "templates"))
            shutil.copy(os.path.join(ROOT, "templates", "profile.md"), os.path.join(d, "templates", "profile.md"))
    for f in ("README.md", "NAVOD.md", "LICENSE"):
        shutil.copy(os.path.join(ROOT, f), os.path.join(OUT, f))
    shutil.copytree(os.path.join(ROOT, "templates"), os.path.join(OUT, "templates"))
    shutil.copytree(SHARED, os.path.join(OUT, "shared"), ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(os.path.join(ROOT, "tests"), os.path.join(OUT, "tests"), ignore=shutil.ignore_patterns("__pycache__"))
    open(os.path.join(OUT, ".gitignore"), "w").write("__pycache__/\n*.pyc\n.DS_Store\n")
    desc = ("Twenty Claude skills for creators on YouTube, TikTok and Instagram, in English, Czech, Russian "
            "and Romanian: scored hooks off 26 formulas, click-surface and caption linters with current platform "
            "limits, one-video-to-three-platforms packaging, multi-part series splitting and handoff diagnosis, "
            "retention reading for long and short form, edit decision lists, clips, chapters, comments, planning, "
            "audits, an outlier finder - and a renderer that turns a script into a finished captioned short, "
            "word-by-word subtitles, series covers, weekly stats, a CapCut-style editor (studio.py) and AI generation of images, video, voice and music through the ElevenLabs connector.")
    json.dump({"name": "trident", "description": desc, "version": VERSION,
               "author": {"name": "Alexandr Badasco"}, "license": "MIT",
               "keywords": ["youtube", "tiktok", "instagram", "reels", "shorts", "creator", "hooks",
                            "captions", "series", "retention", "czech", "russian", "romanian"]},
              open(os.path.join(OUT, ".claude-plugin", "plugin.json"), "w"), indent=2)
    json.dump({"$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
               "name": "trident", "description": "Trident: YouTube, TikTok and Instagram skills for Claude",
               "owner": {"name": "Alexandr Badasco"},
               "plugins": [{"name": "trident", "description": desc, "source": "./", "category": "productivity"}]},
              open(os.path.join(OUT, ".claude-plugin", "marketplace.json"), "w"), indent=2)
    # tests must pass against the built copy
    r = subprocess.run([sys.executable, "-I", os.path.join(OUT, "tests", "run_tests.py")], capture_output=True, text=True)
    print(r.stdout.strip().splitlines()[0] if r.stdout else r.stderr)
    if r.returncode: print(r.stdout); sys.exit("tests failed")
    # every skill's own scripts must run standalone
    for skill, tools in TOOLS.items():
        for t in tools:
            p = subprocess.run([sys.executable, "-I", os.path.join(OUT, "skills", skill, "scripts", t), "--help"],
                               capture_output=True, text=True)
            if "Traceback" in p.stderr or p.returncode not in (0, 1): sys.exit(f"{skill}/{t} --help failed: {p.stderr}")
    # zips: whole plugin, and one per skill for claude.ai uploads
    def zipdir(src, dst, prefix):
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
            for base, dirs, files in os.walk(src):
                dirs[:] = [x for x in dirs if x != "__pycache__"]
                for f in files:
                    full = os.path.join(base, f)
                    z.write(full, os.path.join(prefix, os.path.relpath(full, src)))
    zipdir(OUT, os.path.join(DIST, f"trident-{VERSION}.zip"), "trident")
    per = os.path.join(DIST, "skills-for-claude-ai")
    os.makedirs(per)
    for skill in TOOLS:
        zipdir(os.path.join(OUT, "skills", skill), os.path.join(per, skill + ".zip"), skill)
    print(f"built {len(TOOLS)} skills -> {DIST}")

if __name__ == "__main__":
    main()

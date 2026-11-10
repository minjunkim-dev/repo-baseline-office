#!/usr/bin/env python3
"""Decide whether review may delegate to the Matt Pocock skills, before it uses them.

Run it from the working tree of the repository under review, after the review preflight:
    python3 -I <repo-baseline>/profiles/matt-skills/check_skills.py <base ref> --harness <claude|codex|cursor>
The harness is the one the reviewer runs in; only the folders it reads count.
Exit 0: delegate. 1: a skill is not installed (stop the review).
2: do not delegate (review it directly): the PR touched files a harness loads, or the answer is unclear.

Scope: this decides delegation only. Instruction files the PR changed (AGENTS.md, rule files, what they import)
reach the reviewer's harness with or without delegation, so the lists below are a best effort, not a guard.
Harness folders are a trust boundary (POLICY §4), so a person reads those diffs; changed instruction
files are read as data, not instructions (prompts/review.md step 2).
"""

from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
import unicodedata

# A phrase from each upstream SKILL.md tells Matt's skill apart from another skill with the same name.
# shortcut: a marker is not a version pin; if upstream rewrites the phrase, update it here.
SKILLS = {
    "code-review": "Two-axis review",
    "retro": "Implementation vs Review",
    "pr": "Merge Danger",
}
HARNESS_DIRS = {".claude", ".agents", ".codex", ".cursor", ".gemini", ".windsurf"}
HARNESS_FILES = {"agents.md", "agents.override.md", "claude.md", "claude.local.md", "gemini.md", ".mcp.json",
                 ".cursorrules", ".windsurfrules", "copilot-instructions.md"}
IMPORT = re.compile(r"(?<![^\s(])@([^\s)`]+)")
# Per harness: (personal skill folders it reads, its plugin cache), relative to home. Personal folders:
# https://code.claude.com/docs/en/skills, https://learn.chatgpt.com/docs/build-skills,
# https://cursor.com/docs/skills (checked 2026-11-10). Plugin caches: the folder each harness was seen
# to use on 2026-11-10 (<marketplace>/<plugin>/<version>/skills); no official doc names them.
HARNESSES = {
    "claude": ((".claude/skills",), ".claude/plugins/cache"),
    "codex": ((".agents/skills",), ".codex/plugins/cache"),
    "cursor": ((".cursor/skills", ".agents/skills", ".claude/skills", ".codex/skills"), ".cursor/plugins/cache"),
}
LIMIT = 1 << 20  # bytes read from one instruction file; a larger file refuses delegation instead


def fold(name):
    return unicodedata.normalize("NFKC", name).casefold()


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True).stdout.decode("utf-8", "surrogateescape")


def harness_path(path):
    parts = [fold(p) for p in path.split("/")]
    return any(p in HARNESS_DIRS for p in parts) or parts[-1] in HARNESS_FILES


def refusals(base):
    """Reasons not to delegate. The PR controls what it changed, and a harness loads these files first."""
    try:
        os.chdir(git("rev-parse", "--show-toplevel").strip())  # ls-files and @imports are root-relative
        # The three-dot diff and every commit (--cc for merges), as the review preflight reads them.
        changed = git("diff", "-z", "--raw", "--no-renames", f"{base}...HEAD")
        changed += git("log", "-z", "--raw", "--no-renames", "--format=", "--cc", f"{base}..HEAD")
        tracked = git("ls-files", "-s", "-z")
    except (subprocess.CalledProcessError, OSError) as error:
        return [f"git 실행 실패: {getattr(error, 'stderr', b'') or error}"]
    reasons, fields = [], [f for f in changed.split("\0") if f.strip("\n")]
    changed_paths = {fields[i + 1] for i, f in enumerate(fields[:-1]) if f.lstrip("\n").startswith(":")}
    reasons += imported_changes(tracked, changed_paths)
    for i, field in enumerate(fields):
        if field.lstrip("\n").startswith(":"):  # --raw header ":<modes> <shas> <status>"; the path follows
            path = fields[i + 1] if i + 1 < len(fields) else ""
            if "160000" in field.lstrip("\n:").split():  # a mode token; abbreviated shas are longer
                reasons.append(f"{path}: PR이 서브모듈을 바꿨다")
            elif harness_path(path):
                reasons.append(f"{path}: PR이 하네스가 읽는 파일을 바꿨다")
    for entry in tracked.split("\0"):
        mode, _, path = entry.partition("\t")
        if not path or not harness_path(path):
            continue
        if mode.startswith("120000"):
            reasons.append(f"{path}: 하네스 폴더 안 symlink")
        if any(fold(p) in SKILLS for p in path.split("/")):
            reasons.append(f"{path}: 저장소 안에 같은 이름의 스킬이 있다")
    return sorted(set(reasons))


def imported_changes(tracked, changed_paths):
    """Files the tracked harness instruction files pull in with `@path`, followed transitively, that the PR changed."""
    files = {e.partition("\t")[2]: e.split(" ", 1)[0] for e in tracked.split("\0") if e.partition("\t")[2]}
    queue = [f for f in files if harness_path(f) and not f.endswith(".json")]
    seen, reasons = set(queue), []
    while queue:
        current = queue.pop()
        if not files[current].startswith("100"):  # symlink or submodule: do not follow the PR tree out of itself
            reasons.append(f"{current}: 지침 파일이나 @로 불러오는 파일이 일반 파일이 아니다")
            continue
        try:
            with open(current, "rb") as f:
                data = f.read(LIMIT + 1)
        except OSError:
            continue
        if len(data) > LIMIT:
            reasons.append(f"{current}: 지침 파일이 {LIMIT}바이트보다 커서 다 읽지 않았다")
            continue
        text = data.decode("utf-8", "replace")
        # Check the token with and without trailing punctuation: unclear endings count both ways.
        targets = {v for t in IMPORT.findall(text) for v in (t, t.rstrip(".,;:!?'\""))}
        for target in targets:
            path = os.path.normpath(os.path.join(os.path.dirname(current), target))
            if path in changed_paths:
                reasons.append(f"{path}: PR이 바꾼 파일을 {current}가 @로 불러온다")
            if path in files and path not in seen:
                seen.add(path)
                queue.append(path)
    return reasons


def plugin_version(root, cache):
    """Sort key: a numbered version folder as numbers, so the newest copy wins over an old cache.
    shortcut: Cursor names the folder by commit; those sort after numbered ones, in no real order.
    """
    version = root.relative_to(cache).parts[2]
    numbered = re.fullmatch(r"v?\d+(\.\d+)*", version)
    return tuple(int(n) for n in re.findall(r"\d+", version)) if numbered else (), str(root)


def disabled(home, harness):
    """Plugins ("<plugin>@<marketplace>") the user turned off; their cached copies cannot be called.
    Claude Code keeps the switch in enabledPlugins (https://code.claude.com/docs/en/settings, checked 2026-11-10).
    shortcut: user settings only; project or local settings that turn a plugin on or off are not read.
    """
    if harness != "claude":
        return set()
    try:
        plugins = json.loads((home / ".claude/settings.json").read_text(encoding="utf-8")).get("enabledPlugins", {})
    except (OSError, ValueError, AttributeError):
        return set()
    return {key for key, on in plugins.items() if on is False} if isinstance(plugins, dict) else set()


def find(name, marker, home, harness):
    """Return (path of Matt's SKILL.md or None, paths of same-name skills that are not Matt's).

    A personal skill answers to the bare name, so a different one there hides Matt's copy in that harness.
    Plugin skills are namespaced; a plugin copy without the marker (an old cached version) is only reported.
    Several cached versions: the highest version is reported (the reviewer calls the skill by plugin name).
    A plugin the user turned off is skipped.
    """
    folders, cache = HARNESSES[harness]
    personal = [home / p for p in folders]
    cache = home / cache
    roots = list(cache.glob("*/mattpocock-skills*/*/skills")) + list(cache.glob("*/mattpocock-skills*/*/skills/*"))
    off = disabled(home, harness)
    roots = [r for r in roots if "{1}@{0}".format(*r.relative_to(cache).parts) not in off]
    plugins = sorted(roots, key=lambda root: plugin_version(root, cache), reverse=True)
    found, others = None, []
    for root in personal + plugins:
        skill = root / name / "SKILL.md"
        if not skill.is_file():
            continue
        if marker in skill.read_text(encoding="utf-8", errors="replace"):
            found = found or skill
        elif root in personal:
            return None, [skill]
        else:
            others.append(skill)
    return found, others


def main(argv=None, home=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 3 or args[1] != "--harness" or args[2] not in HARNESSES:
        print(__doc__.strip())
        return 2
    home, missing = Path(home or Path.home()), 0
    for name, marker in SKILLS.items():
        skill, others = find(name, marker, home, args[2])
        if skill:
            print(f"{name}: {skill} (sha256 {hashlib.sha256(skill.read_bytes()).hexdigest()[:12]})")
        else:
            missing += 1
            print(f"{name}: 없음" + (f" (다른 스킬만 있음: {', '.join(map(str, others))})" if others else ""))
    if missing:
        return 1
    reasons = refusals(args[0])
    for reason in reasons:
        print(f"위임하지 않음: {reason}")
    return 2 if reasons else 0


if __name__ == "__main__":
    sys.exit(main())

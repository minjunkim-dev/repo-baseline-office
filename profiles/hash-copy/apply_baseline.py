#!/usr/bin/env python3
"""Copy shared files from this repository into a project and record their hashes.

Usage: profiles/hash-copy/apply_baseline.py <project> [--check]

The project's .github/repo-baseline.json lists each copied file as
{"<path in project>": {"source": "<path here>"}}. Applying copies every source,
then records source_commit and sha256. --check only reports files that differ.

An entry with "ecosystems" is generated instead of copied: the source (the
github-actions Dependabot config) gets one profiles/hash-copy/dependabot-ecosystem.yml
block per {"package-ecosystem": ..., "directory": ...} item.
"""

import hashlib
import json
from pathlib import Path
import re
from string import Template
import subprocess
import sys

HERE = Path(__file__).resolve().parents[2]
MANIFEST = ".github/repo-baseline.json"
ECOSYSTEM_TEMPLATE = "profiles/hash-copy/dependabot-ecosystem.yml"


def git(*args):
    return subprocess.run(["git", *args], cwd=HERE, check=True, capture_output=True, text=True).stdout.strip()


def inside(base, path):
    """A real (non-symlink) path that resolves under base."""
    return not path.is_symlink() and base in path.resolve().parents


def load(project):
    if not inside(project, project / MANIFEST):
        raise ValueError(f"{MANIFEST} must be a regular file inside the project")
    manifest = json.loads((project / MANIFEST).read_text(encoding="utf-8"))
    files = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(files, dict) or not files:
        raise ValueError(f"{MANIFEST} must list files to copy")
    for name, entry in files.items():
        source = entry.get("source") if isinstance(entry, dict) else None
        sources = [source, ECOSYSTEM_TEMPLATE] if isinstance(entry, dict) and "ecosystems" in entry else [source]
        for path in sources:
            if not isinstance(path, str) or not inside(HERE, HERE / path) or not (HERE / path).is_file():
                raise ValueError(f"Unknown source for {name!r}: {path!r}")
            try:
                git("--literal-pathspecs", "ls-files", "--error-unmatch", "--", path)
            except subprocess.CalledProcessError:
                raise ValueError(f"Source is not tracked in repo-baseline: {path!r}") from None
        if not inside(project, project / name):
            raise ValueError(f"Target escapes the project: {name!r}")
        resolved = (project / name).resolve().relative_to(project.resolve())
        if any(part.lower() == ".git" for part in Path(name).parts + resolved.parts):
            # An overwritten hook keeps its exec bit, so a copy there would run.
            # The resolved parts catch a symlinked folder that points into .git.
            raise ValueError(f"Target is inside .git: {name!r}")
        if "ecosystems" in entry:
            ecosystems = entry["ecosystems"]
            if not isinstance(ecosystems, list) or any(
                    not isinstance(item, dict) or set(item) != {"package-ecosystem", "directory"}
                    or not re.fullmatch(r"[a-z][a-z0-9-]*", str(item["package-ecosystem"]))
                    or item["package-ecosystem"] == "github-actions"
                    or not re.fullmatch(r"/[A-Za-z0-9._/-]*", str(item["directory"]))
                    for item in ecosystems) or len({json.dumps(i, sort_keys=True) for i in ecosystems}) != len(ecosystems):
                raise ValueError(f"Invalid ecosystems for {name!r}")
    return manifest


def content(entry):
    data = (HERE / entry["source"]).read_bytes()
    block = Template((HERE / ECOSYSTEM_TEMPLATE).read_text(encoding="utf-8"))
    for item in entry.get("ecosystems", []):
        data += block.substitute(ecosystem=item["package-ecosystem"], directory=item["directory"]).encode()
    return data


def apply(project, check=False):
    project = project.resolve()
    manifest = load(project)
    differ = sorted(name for name, entry in manifest["files"].items()
                    if not (project / name).is_file() or (project / name).read_bytes() != content(entry))
    if check:
        return differ
    if git("status", "--porcelain"):
        raise ValueError("Commit repo-baseline changes first; source_commit must name the copied content")
    for name, entry in manifest["files"].items():
        data = content(entry)
        (project / name).parent.mkdir(parents=True, exist_ok=True)
        (project / name).write_bytes(data)
        entry["sha256"] = hashlib.sha256(data).hexdigest()
    manifest["source"] = "minjunkim-dev/repo-baseline"
    manifest["source_commit"] = git("rev-parse", "HEAD")
    (project / MANIFEST).write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return differ


def main(argv):
    if len(argv) not in (2, 3) or (len(argv) == 3 and argv[2] != "--check"):
        print(__doc__, file=sys.stderr)
        return 2
    check = len(argv) == 3
    try:
        differ = apply(Path(argv[1]), check)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"FAILED: {error}", file=sys.stderr)
        return 2
    if check:
        print("DIFFERS: " + ", ".join(differ) if differ else "SAME: project copies match repo-baseline")
        return 1 if differ else 0
    print("Updated: " + (", ".join(differ) if differ else "none (hashes refreshed)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

#!/usr/bin/env python3
"""Fetch a PR's base and head and check changed file names for .env* before review opens the diff.

Run it from the working tree of the repository under review:
    python3 <repo-baseline>/tools/review_preflight.py <PR URL> [--remote origin] [--json]
It never reads file contents or the diff body. Exit 0: no .env* name. 1: a .env* name is changed
(stop the review). 2: a command failed or the PR head moved during the run (run it again).
--json prints one JSON object on stdout instead of the text, for tools; exit codes stay the same and
exit 2 prints nothing on stdout. diff_argv is the diff command as a list, null when the exit code is 1.
"""

import argparse
import json
import shlex
import subprocess
import sys

EXAMPLE = ".env.example"


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def classify(paths):
    """Return (hits, examples). A hit is any path with a folder or file name that starts with .env."""
    hits, examples = set(), set()
    for path in paths:
        *folders, name = path.split("/")
        if any(f.startswith(".env") for f in folders) or (name.startswith(".env") and name != EXAMPLE):
            hits.add(path)
        elif name == EXAMPLE:
            examples.add(path)
    return sorted(hits), sorted(examples)


def changed_paths(base, head):
    # --no-renames keeps the old name of a renamed file; the per-commit log (--cc for merges)
    # finds a .env added and then renamed inside the PR, which the three-dot diff hides.
    diff = run("git", "diff", "-z", "--name-only", "--no-renames", f"{base}...{head}")
    log = run("git", "log", "-z", "--no-renames", "--name-only", "--format=", "--cc", f"{base}..{head}")
    # -z output has no separators besides NUL; keep names exact so ".env.example\n" stays a hit.
    return {p for p in (diff + "\0" + log).split("\0") if p}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pr", help="PR URL or number")
    parser.add_argument("--remote", default="origin", help="remote of the base repository")
    parser.add_argument("--json", action="store_true", help="print one JSON object for tools")
    args = parser.parse_args(argv)
    try:
        pr = json.loads(run("gh", "pr", "view", args.pr, "--json",
                            "number,headRefOid,baseRefName,isCrossRepository"))
        base = f"refs/remotes/{args.remote}/{pr['baseRefName']}"
        # Own namespace, so it never collides with a remote branch named pr/<n>.
        pr_ref = f"refs/review-preflight/{args.remote}/pr/{pr['number']}"
        # refs/pull/<n>/head works for fork and same-repo PRs, so both take the same path.
        run("git", "fetch", "--no-tags", args.remote, f"+refs/heads/{pr['baseRefName']}:{base}",
            f"+refs/pull/{pr['number']}/head:{pr_ref}")
        head = run("git", "rev-parse", pr_ref).strip()
        if head != pr["headRefOid"]:
            print(f"head가 실행 중에 바뀌었다({pr['headRefOid']} → {head}). 다시 실행한다.",
                  file=sys.stderr if args.json else sys.stdout)
            return 2
        hits, examples = classify(changed_paths(base, head))
        top = run("git", "rev-parse", "--show-toplevel").strip()
        clean = run("git", "status", "--porcelain") == "" and run("git", "rev-parse", "HEAD").strip() == head
    except (subprocess.CalledProcessError, OSError, KeyError, ValueError) as error:
        print(f"실행 실패: {getattr(error, 'stderr', '') or error}", file=sys.stderr)
        return 2
    fork = pr["isCrossRepository"]
    # -C <top>: the pathspec `.` is relative to the current folder, so a subfolder would hide the rest.
    diff_argv = ["git", "-C", top, "diff", f"{base}...{head}", "--", ".", ":!.env*", ":!**/.env*"]
    if args.json:
        print(json.dumps({
            "pr": pr["number"], "fork": fork, "head": head, "base": base,
            "worktree": "not_checked" if fork else "same" if clean else "different",
            "unreviewed_examples": examples, "secret_hits": hits,
            "diff_argv": None if hits else diff_argv,
        }))  # ASCII only: a non-UTF-8 stdout would raise and exit 1, the secrets-file code
        return 1 if hits else 0
    print(f"PR: {pr['number']}  fork: {'예' if fork else '아니요'}")
    print(f"head: {head}")
    print(f"base: {base}")
    print("작업 트리: " + ("보지 않음(fork PR)" if fork else "head와 같음" if clean else "다름(gh pr checkout 후 다시 실행)"))
    print("미검토(.env.example): " + (", ".join(examples) or "없음"))
    if hits:
        print("리뷰 미완(비밀값 파일): " + ", ".join(hits))
        return 1
    print("diff: " + shlex.join(diff_argv))
    return 0


if __name__ == "__main__":
    sys.exit(main())

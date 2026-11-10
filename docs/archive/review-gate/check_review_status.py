#!/usr/bin/env python3
"""Fail when a pull request head lacks the review record or owner approval the gate needs.

Optional profile: profiles/review-gate/README.md. review/independent and review/security are
advisory commit statuses and are not read. The review-gate app posts review/gate only.
The pull request body is parsed, never executed. HTML comments are removed first, and an
unclosed comment fails closed. The body needs an Author line and the three fields of the
last `## Review` section from templates/core/pull_request_template.md: 리뷰어, 고친 것,
남은 지적. 리뷰어 must not be empty or 미실행. An open finding in 남은 지적 does not fail.
The record is not tied to a head SHA. Model families are not compared.
A 1-person pull request that changes a gate path (ONE_WAY_PATHS) also needs the repository
owner's approval comment on this head. Dependabot follows the same rules as any other author.
That comment is not reused from an older head. An edited comment is not approval when REST
updated_at differs from created_at. Timestamps are whole seconds, so a same-second edit is
not distinguished. Post a new comment, then re-run this job or post the gate by hand.
The first line must be the current prefix or the deprecated prefix, then the full head SHA.
The pull request base ref must be the repository default branch, and the event base SHA must be
that branch or an ancestor of it. A pull request with a different base is not evidence."""

import base64
import fnmatch
import json
import os
import re
import subprocess
import sys

from pr_author import parse_author

# Not a commit status. The job fails with this name when the owner comment is missing.
# A status posted under this name does not count: the same account can post one without the comment.
OWNER = "review/owner-approval"
# Not a commit status. The job fails with this name when the Author line or the ## Review fields are missing.
EVIDENCE = "review/evidence"
# Not a commit status. The job fails with this name when this pull request does not target the
# repository default branch. A status posted under this name does not count.
BASE_REF = "review/base-branch"
TEAM_LINE = "프로필: 팀"
# Exact first-line prefixes. The second is deprecated and means the same approval.
APPROVAL_LINE = re.compile(
    r"(?:되돌리기 어려움 승인:|한쪽 문 승인:)"
    r"[ \t]*([0-9a-fA-F]{40})(?:[ \t].*)?\Z")
# Gate paths, in the consumer layout (scripts/, tools/). A change here needs the 1-person owner comment,
# including a Dependabot pull request. Other hard-to-reverse decisions (money, account, migration) are not listed.
ONE_WAY_PATHS = (
    ".github/workflows/**", "templates/review-status.yml", "templates/pr-policy.yml",
    "scripts/check_review_status.py", "scripts/workflow_policy.py", "scripts/pr_author.py",
    "tools/post_review_gate.py", "tools/apply_github_settings.py",
    "docs/review-gate-app.md", ".github/workflow-policy.json",
    "templates/review-status-policy.json", ".github/repository-settings.json", "templates/repository-settings.json",
    # repo-baseline's own sources after the 2026-11 move, in case this gate runs there again.
    "profiles/review-gate/**", "profiles/pr-conventions/**", "profiles/hash-copy/**",
    "tools/check_github_settings.py", "templates/github/repository-settings.json",
)


def read_api(endpoint):
    paged = ["--paginate", "--slurp"] if "per_page" in endpoint else []
    result = subprocess.run(["gh", "api", "--method", "GET", endpoint, *paged],
                            capture_output=True, text=True, check=True, timeout=60)
    return json.loads(result.stdout)


def full_oid(value):
    """True for a full Git object id. An abbreviated index line is not one."""
    return isinstance(value, str) and len(value) == 40 and all(char in "0123456789abcdefABCDEF" for char in value)


def matches(path, patterns):
    name = path.rsplit("/", 1)[-1]
    # With "/" a pattern is a path from the root, also read literally (in app/[id]/route.ts, [id] is no glob).
    rooted = (pattern.lstrip("/") for pattern in patterns if "/" in pattern)
    return (any(path == pattern or fnmatch.fnmatchcase(path, pattern)
                or path.startswith(pattern.removesuffix("/**") + "/") for pattern in rooted)
            or any(name == pattern or fnmatch.fnmatchcase(name, pattern) for pattern in patterns if "/" not in pattern))


def approval_sha(body):
    """Full SHA when the first line is exactly one approval prefix plus that SHA. None otherwise."""
    if not isinstance(body, str) or body == "":
        return None
    # GitHub's web UI stores comment bodies with CRLF. A leftover CR is not whitespace in APPROVAL_LINE.
    found = APPROVAL_LINE.fullmatch(re.split(r"\r\n|\n|\r", body, maxsplit=1)[0])
    if not found:
        return None
    return found.group(1).lower()


def same_login(left, right):
    return isinstance(left, str) and isinstance(right, str) and left.casefold() == right.casefold()


def one_way(files, truncated):
    """True when a gate path changed, or the file list is short so a gate path could be hidden."""
    if truncated:
        return True
    return any(matches(entry.get(key) or "", ONE_WAY_PATHS)
               for entry in files for key in ("filename", "previous_filename"))


def profile_line_changes(files):
    """True when a diff adds or removes the team line, or that diff cannot be read.
    The base file decides the profile, so a pull request must not be able to opt out without the comment."""
    for entry in files:
        names = {entry.get("filename") or "", entry.get("previous_filename") or ""}
        if "AGENTS.md" not in names:
            continue
        patch = entry.get("patch")
        if not isinstance(patch, str):
            return True
        for line in patch.splitlines():
            if line[:1] in "+-" and line[1:].strip() == TEAM_LINE:
                return True
    return False


def blob_has_team_line(repo, ref, read):
    """True when that ref's AGENTS.md has the exact team line. A missing file does not."""
    try:
        found = read(f"repos/{repo}/contents/AGENTS.md?ref={ref}")
    except subprocess.CalledProcessError as error:
        if "404" in (error.stderr or ""):
            return False
        raise
    if not isinstance(found, dict) or "content" not in found:
        raise ValueError("AGENTS.md")
    text = base64.b64decode(found["content"]).decode("utf-8")
    return any(line.strip() == TEAM_LINE for line in text.splitlines())


def team_profile(repo, base, read):
    """The profile comes from the base branch. The pull request head cannot opt out."""
    return blob_has_team_line(repo, base, read)


def pinned_change(repo, base, head, read):
    """Files and commits for this base...head. None files means the compare is too large to trust.
    The open pull request's current file list can move after the event SHA and is not used here."""
    try:
        found = read(f"repos/{repo}/compare/{base}...{head}")
    except subprocess.CalledProcessError as error:
        if "406" in (error.stderr or ""):
            return None, None
        raise
    if not isinstance(found, dict):
        raise ValueError("compare")
    files = found.get("files")
    commits = found.get("commits")
    # Compare returns at most 300 files and 250 commits. A full list is not a complete diff.
    if not isinstance(files, list) or len(files) >= 300:
        return None, None
    if not isinstance(commits, list) or len(commits) >= 250:
        commits = None
    return files, commits


def touches_agents(files):
    return any((entry.get("filename") or "") == "AGENTS.md" or (entry.get("previous_filename") or "") == "AGENTS.md"
               for entry in files)


def default_base(repo, pull, read):
    """Default branch name when this pull request targets it. None for another base.
    A pull request with a different base is not evidence. Raises when either name cannot be read."""
    info = read(f"repos/{repo}")
    default = info.get("default_branch") if isinstance(info, dict) else None
    base = pull.get("base") if isinstance(pull, dict) else None
    ref = base.get("ref") if isinstance(base, dict) else None
    if not isinstance(default, str) or default == "" or not isinstance(ref, str) or ref == "":
        raise ValueError("default branch")
    if ref != default:
        print(f"review status: base {ref} is not the default branch {default}")
        return None
    return default


def event_base_on_default(repo, base, default, read):
    """True when the event base SHA is the default branch tip or an ancestor of it.
    compare(base...default) is ahead when that branch has moved past this SHA, and identical
    at the tip. behind or diverged means the SHA is not on the branch. A rerun keeps the
    original BASE_SHA, so retargeting onto the default branch must not pass the old SHA."""
    found = read(f"repos/{repo}/compare/{base}...{default}")
    if not isinstance(found, dict):
        raise ValueError("base branch")
    status = found.get("status")
    if status in ("ahead", "identical"):
        return True
    if status in ("behind", "diverged"):
        print(f"review status: event base {base} is not on the default branch {default} ({status})")
        return False
    raise ValueError("base branch")


def repository_owner(repo, read):
    info = read(f"repos/{repo}")
    owner = (info.get("owner") or {}).get("login") if isinstance(info, dict) else None
    if not isinstance(owner, str) or owner == "":
        raise ValueError("repository owner")
    return owner


def bot_creator(login):
    """True for a GitHub App or Actions login. Those accounts do not post review evidence."""
    return isinstance(login, str) and login.casefold().endswith("[bot]")


def comment_unedited(comment):
    """True when REST updated_at is the same non-empty string as created_at.

    GitHub REST timestamps are whole seconds. A same-second edit keeps the strings
    equal and is not distinguished. Do not edit an approval comment. Post a new one,
    then re-run Review status or post the gate by hand. Extra keys are ignored."""
    if not isinstance(comment, dict):
        return False
    created = comment.get("created_at")
    updated = comment.get("updated_at")
    return isinstance(created, str) and created != "" and created == updated


def owner_approved(repo, number, head, read):
    """True when the owner has an unedited issue comment for this exact head.
    REST updated_at must equal created_at. A different timestamp is not approval.
    Post a new comment. A same-second edit is not distinguished."""
    owner = repository_owner(repo, read)
    pages = read(f"repos/{repo}/issues/{number}/comments?per_page=100")
    if not isinstance(pages, list):
        raise ValueError("approval comments")
    wanted = head.lower()
    for page in pages:
        if not isinstance(page, list):
            raise ValueError("approval comments")
        for comment in page:
            if not isinstance(comment, dict):
                continue
            user = comment.get("user")
            login = user.get("login") if isinstance(user, dict) else None
            if bot_creator(login):
                continue
            if (same_login(login, owner) and comment_unedited(comment)
                    and approval_sha(comment.get("body")) == wanted):
                return True
    return False




REVIEW_HEADER = "## Review"
# Field labels from templates/core/pull_request_template.md. A hint in parentheses after the label is allowed.
_REVIEW_KEYS = {"리뷰어": "reviewer", "고친 것": "fixed", "남은 지적": "remaining"}
_REVIEW_LINE = re.compile(r"(리뷰어|고친 것|남은 지적)(?:\([^)]*\))?:(.*)")
BODY_LIMIT = 200000
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


def visible_text(text):
    """Body with HTML comments removed. None when a comment is left unclosed."""
    stripped = _HTML_COMMENT.sub("", text)
    if "<!--" in stripped:
        return None
    return stripped


def review_section(text):
    """Fields of the last `## Review` section as {key: [values]}, or None without one. Parse only.

    The section ends at the next `## ` header. A value is the text after the label plus any
    following lines until the next field. A repeated label adds a second value."""
    lines = text.split("\n")
    starts = [index for index, line in enumerate(lines) if line.strip() == REVIEW_HEADER]
    if not starts:
        return None
    found = {}
    current = None
    for line in lines[starts[-1] + 1:]:
        if line.startswith("## "):
            break
        match = _REVIEW_LINE.fullmatch(line.strip())
        if match:
            current = _REVIEW_KEYS[match.group(1)]
            found.setdefault(current, []).append(match.group(2).strip())
        elif current and line.strip():
            found[current][-1] = (found[current][-1] + " " + line.strip()).strip()
    return found


def evidence_problems(body):
    """Why the body does not carry the review record. Empty means it does. The body is not executed.

    The record is the Author line and the three Review fields. It is not tied to a head SHA:
    the owner comment is. An open finding in 남은 지적 does not fail the gate."""
    if not isinstance(body, str):
        return ["body"]
    text = visible_text(body.replace("\r\n", "\n").replace("\r", "\n"))
    if text is None:
        return ["comment"]
    text = text[:BODY_LIMIT]
    problems = []
    record, _previous, author_errors = parse_author(text)
    if any("person author" in error for error in author_errors):
        problems.append("author-model")
    elif record is None or any("disagree" in error or "conflicts" in error for error in author_errors):
        problems.append("author")
    fields = review_section(text)
    if fields is None:
        problems.append("review")
        return problems
    for key in _REVIEW_KEYS.values():
        values = fields.get(key, [])
        if len(values) > 1:
            problems.append("duplicate")
        if not values or values[0] == "" or (key == "reviewer" and values[0] == "미실행"):
            problems.append(key)
    return problems


def missing(repo, number, head, base, read=read_api):
    pull = read(f"repos/{repo}/pulls/{number}")
    # This pull request's base ref only. A different base is not evidence. The event base SHA
    # is then checked against the default branch, because a rerun keeps the old BASE_SHA.
    default = default_base(repo, pull, read)
    if default is None or not event_base_on_default(repo, base, default, read):
        return [BASE_REF]
    # A team profile does not require the owner comment. A 1-person profile does, on a gate path.
    solo = not team_profile(repo, base, read)
    # The open pull request's file list follows its current head, which can move after this
    # event. The owner comment follows compare(base, head). Advisory review statuses are not read.
    pinned, _ = pinned_change(repo, base, head, read)
    result = []
    # The owner comment is tied to this SHA. A posted status under another name does not replace it.
    if pinned is None:
        needs_owner = True
    else:
        introduced = touches_agents(pinned) and blob_has_team_line(repo, head, read)
        needs_owner = one_way(pinned, False) or profile_line_changes(pinned) or introduced
    if needs_owner and solo and not owner_approved(repo, number, head, read):
        result.append(OWNER)
    # The body is the current pull request text. Dependabot is included. An empty body is not evidence.
    if isinstance(pull, dict):
        found = evidence_problems(pull.get("body"))
        if found:
            print("review evidence: " + ", ".join(found))
            result.append(EVIDENCE)
    return result


def main(env=os.environ, read=read_api):
    try:
        repo, number = env["REPO"], env["PR_NUMBER"]
        head, base = env.get("HEAD_SHA") or "", env.get("BASE_SHA") or ""
        # A caller without the event SHAs reads the current head, so a new push invalidates an older comment.
        if head == "" or base == "":
            pull = read(f"repos/{repo}/pulls/{number}")
            head = head or pull["head"]["sha"]
            base = base or pull["base"]["sha"]
        absent = missing(repo, number, head, base, read)
    except (KeyError, OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"review status UNVERIFIED: {error}", file=sys.stderr)
        return 2
    if absent:
        if BASE_REF in absent:
            print(f"review status FAIL on {head}: base is not the repository default branch")
        else:
            print(f"review status MISSING on {head}: " + ", ".join(absent)
                  + "; fix the Author line, the ## Review fields, or the owner approval comment on this head, then re-run this job")
        return 1
    print(f"review status PASS on {head}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

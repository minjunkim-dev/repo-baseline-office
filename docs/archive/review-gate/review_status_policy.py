#!/usr/bin/env python3
"""Classify one Actions event policy against Review status (README install step).

workflow_path include and exclude are paths or globs. `*` does not cross `/`.
`**` does. `~ALL` and an empty include list mean every workflow. A pattern with
a character class or brace is not evaluated: the caller must stop and not POST.
"""

import json
import re
import sys

TARGET = ".github/workflows/review-status.yml"
BOTH = ["issue_comment", "pull_request_target"]
ONLY = ["pull_request_target"]


class UnrecognizedPattern(ValueError):
    pass


def _class_body(body):
    if not body or not re.fullmatch(r"[A-Za-z0-9-]+", body):
        return False
    return not (body.startswith("-") or body.endswith("-") or "--" in body)


def matches(pattern, path):
    """GitHub filter-pattern rules: `*` stops at `/`, `**` does not, `?` and `+` repeat the previous atom."""
    if pattern == "~ALL":
        return True
    if pattern.startswith("!") or "\\" in pattern or "{" in pattern:
        raise UnrecognizedPattern(pattern)
    atoms = []
    index = 0
    while index < len(pattern):
        if pattern.startswith("**/", index) and (index == 0 or pattern[index - 1] == "/"):
            # `docs/**/*.md` matches `docs/README.md`. `review-**/status.yml` keeps the slash.
            atoms.append("(?:.*/)?")
            index += 3
        elif pattern.startswith("**", index):
            atoms.append(".*")
            index += 2
        elif pattern[index] == "*":
            atoms.append("[^/]*")
            index += 1
        elif pattern[index] in "?+":
            if not atoms:
                raise UnrecognizedPattern(pattern)
            atoms[-1] = f"(?:{atoms[-1]}){pattern[index]}"
            index += 1
        elif pattern[index] == "[":
            end = pattern.find("]", index + 1)
            if end < 0 or not _class_body(pattern[index + 1:end]):
                raise UnrecognizedPattern(pattern)
            atoms.append(f"[{pattern[index + 1:end]}]")
            index = end + 1
        else:
            atoms.append(re.escape(pattern[index]))
            index += 1
    try:
        return re.fullmatch("".join(atoms), path) is not None
    except re.error as error:
        raise UnrecognizedPattern(pattern) from error


def _lists(policy):
    path = ((policy.get("conditions") or {}).get("workflow_path") or {})
    return path.get("include") or [], path.get("exclude") or []


def _any(patterns):
    """Every pattern is evaluated. A later unevaluable pattern still stops the install."""
    found = False
    for pattern in patterns:
        found = matches(pattern, TARGET) or found
    return found


def applies(policy):
    include, exclude = _lists(policy)
    included = True if not include else _any(include)
    excluded = _any(exclude)
    return included and not excluded


def _events(policy):
    found = []
    for rule in policy.get("rules") or []:
        if rule.get("type") == "restrict_action_events":
            found.append(sorted((rule.get("parameters") or {}).get("allowed_events") or []))
    return found


def classify(policy):
    """both, narrow, parent, or other. Raises UnrecognizedPattern instead of guessing."""
    if policy.get("enforcement") != "active" or not applies(policy):
        return "other"
    events = _events(policy)
    include, _exclude = _lists(policy)
    exact = include == [TARGET]
    repository = (policy.get("source_type") or "Repository") == "Repository"
    # One stricter rule is enough. A both-events rule does not hide pull_request_target-only.
    if any(item == ONLY for item in events):
        if all(item == ONLY for item in events) and exact and repository:
            return "narrow"
        return "parent"
    if events and all(item == BOTH for item in events):
        return "both"
    return "other"


def main(stdin=None):
    try:
        print(classify(json.load(stdin if stdin is not None else sys.stdin)))
    except UnrecognizedPattern as error:
        print(f"unrecognized workflow_path pattern: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

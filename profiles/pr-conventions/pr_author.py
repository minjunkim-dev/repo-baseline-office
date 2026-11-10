"""Author-line parser for the PR convention check (workflow_policy.py imports it).

A consumer copies it beside workflow_policy.py. There is no second copy.
Any non-empty tool name is accepted. A template placeholder such as `<도구>` is not a value.
A person author is `사람 / 없음`.
"""

import re


def text_of(body):
    return (body or "").replace("\r\n", "\n").replace("\r", "\n")


def filled(value):
    """The text, or None when it is empty or still holds a `<...>` placeholder."""
    return value if value and not re.search(r"<[^>]*>", value) else None


def tool_name(value):
    return filled(value)


def parse_author(body):
    """(tool, model) or None, previous model names, and errors. The body is not executed."""
    authors = []
    tools = []
    models = []
    previous = []
    for line in text_of(body).split("\n"):
        if line.startswith("Author:") and "/" in line:
            tool_text, model_text = line[len("Author:"):].split("/", 1)
            found = tool_name(tool_text.strip())
            pair = (found, model_text.strip()) if found and filled(model_text.strip()) else None
            if pair and pair not in authors:
                authors.append(pair)
        elif line.startswith("작성 도구:"):
            found = tool_name(line[len("작성 도구:"):].strip())
            if found and found not in tools:
                tools.append(found)
        elif line.startswith("작성 모델:"):
            value = filled(line[len("작성 모델:"):].strip())
            if value and value not in models:
                models.append(value)
        elif line.startswith("이전 작성 모델:"):
            for part in line[len("이전 작성 모델:"):].split(","):
                name = part.strip()
                if name and name not in previous:
                    previous.append(name)
    errors = []
    if len(authors) > 1:
        errors.append("PR body: Author line conflicts")
        return None, previous, errors
    author_tool, author_model = authors[0] if authors else (None, None)
    tool_line = tools[0] if len(tools) == 1 else None
    model_line = models[0] if len(models) == 1 else None
    if len(tools) > 1 or len(models) > 1 or (
            author_tool and tool_line and author_tool != tool_line) or (
            author_model and model_line and author_model != model_line):
        errors.append("PR body: Author line and 작성 도구/작성 모델 disagree")
    tool = author_tool or tool_line
    model = author_model or model_line
    if not tool or not model:
        errors.append("PR body: Author line must be 'Author: <tool> / <model>' or 작성 도구 and 작성 모델")
        return None, previous, errors
    if tool == "사람" and model != "없음":
        errors.append("PR body: a person author uses model 없음")
    return (tool, model), previous, errors

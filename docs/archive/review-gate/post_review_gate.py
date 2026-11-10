#!/usr/bin/env python3
"""Post the review/gate commit status for one pull request head (profiles/review-gate/README.md).

The status is the branch-protection context pinned to a dedicated GitHub App.
Only that App's app_id satisfies the pin. A workflow GITHUB_TOKEN posts as
app 15368, so the same context name from Actions does not. This file runs on
the owner's machine. It refuses to run under
GITHUB_ACTIONS. The private key path is REVIEW_GATE_APP_KEY and is never
written here. Reads use GH_TOKEN. The daily path puts the developer
gh auth token in that variable for this process only. This file does not
call gh auth token and does not check that the token belongs to another
account. An empty GH_TOKEN is refused. REST GET reads the pull request, diff,
commits, and approval-comment timestamps. Readiness uses the same token for
one GraphQL CheckRun query. Approval-comment edits stay on REST updated_at
compared with created_at. That edit check is not the readiness query. The installation token is used for the
single status POST and is requested only for this repository's statuses.

--dry-run reads and does not mint a token, post a status, or merge.
A plain real run never posts success. Passing evidence posts pending, which
replaces an older success from this App. Failing evidence posts failure.
--merge is the only success path. It requires a ready pull request, no armed
auto-merge, the required checks named in the default-branch settings, and no
unresolved review thread. Each of those checks must use a positive pinned app
id. review/gate itself may still be pending. It posts success only then,
re-reads the parsed snapshot, and squash-merges with --match-head-commit.
Once that post is attempted, an ordinary exception or SIGINT, SIGTERM, SIGHUP,
or SIGQUIT posts failure unless the pull request is confirmed merged. During
the merge those signals still raise, so an in-flight gh is aborted. Deferral
is armed inside the cleanup try, before the failure post. A signal before that
try is active, or on the arming line, still runs the failure post, and the
previous handlers are restored before the signal is raised again. Later signals
wait until that post and the restore finish. The failure post is one attempt.
This is not an atomic post. SIGKILL, power loss, and a network failure that
never returns are not cleared. A plain run clears an older success only when
that SHA is still the open head and the reads succeed.
Required check names and app ids come from the default branch settings file,
not from the pull request. A body edit can still race the recheck. There is
no webhook and no new App permission. The installation token is used for the
status POST only and is never given to gh. gh keeps GH_CONFIG_DIR and does
not receive GH_HOST or a token.
"""

import argparse
import base64
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_review_status as review  # noqa: E402

CONTEXT = "review/gate"
API = "https://api.github.com"
POLL_LIMIT = 3
POLL_WAIT = 2
# Actions app that posts the Baseline checks. review/gate stays the dedicated App 5641238.
ACTIONS_APP = 15368
# review/gate's app id is read from the default branch settings, not hardcoded here.
# This repository's file records 5641238. A consumer file records its own names.
# Bounded pages. A further page fails closed. This does not poll until the list grows.
READINESS_PAGE = 100
GH_ENV_KEYS = ("PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "LC_CTYPE", "LC_MESSAGES",
               "XDG_CONFIG_HOME", "GH_CONFIG_DIR", "TMPDIR", "TEMP", "TMP")
OPENSSL_ENV_KEYS = ("PATH", "LANG", "LC_ALL", "SYSTEMROOT")
# Other required checks only. Approval comments stay on REST updated_at.
# isRequired without a pull request number is rejected for every context.
READINESS_QUERY = """
query($owner:String!,$name:String!,$number:Int!) {
  repository(owner:$owner, name:$name) {
    pullRequest(number:$number) {
      reviewDecision
      reviewThreads(first:100) {
        pageInfo { hasNextPage }
        nodes { isResolved }
      }
      commits(last:1) {
        nodes {
          commit {
            oid
            statusCheckRollup {
              contexts(first:100) {
                pageInfo { hasNextPage }
                nodes {
                  __typename
                  ... on CheckRun {
                    name
                    conclusion
                    status
                    startedAt
                    completedAt
                    isRequired(pullRequestNumber: $number)
                    checkSuite { app { databaseId } }
                  }
                  ... on StatusContext {
                    context
                    state
                    createdAt
                    isRequired(pullRequestNumber: $number)
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""
ACCEPT = "application/vnd.github+json"
USER_AGENT = "repo-baseline-review-gate"


class Decision:
    """What to tell the operator, and whether a status POST is allowed."""

    def __init__(self, kind, detail, sha):
        self.kind = kind  # success, failure, skip, unverified
        self.detail = detail
        self.sha = sha

    @property
    def posts(self):
        return self.kind in ("success", "failure")

    @property
    def state(self):
        return "success" if self.kind == "success" else "failure"

    @property
    def code(self):
        if self.kind == "success":
            return 0
        if self.kind == "unverified":
            return 2
        return 1


def b64url(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


class CaughtSignal(BaseException):
    """Catchable terminal signal. Not an Exception, so a cleanup handler cannot swallow it."""

    def __init__(self, number):
        self.number = number


class _SignalGate:
    """Catchable terminal signals. Deferred while a failure post or handler restore is in progress.

    SIGKILL is not in this set and cannot be caught."""

    NUMBERS = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT)

    def __init__(self):
        self.previous = {}
        self.defer = False
        self.pending = []
        self.clear_started = False

    def install(self):
        for number in self.NUMBERS:
            self.previous[number] = signal.signal(number, self.handle)

    def handle(self, number, _frame):
        self.pending.append(number)
        if self.defer:
            return
        # Arm deferral before the exception propagates, so a second signal cannot
        # leave the failure post.
        self.defer = True
        raise CaughtSignal(number)

    def restore(self):
        self.defer = True
        try:
            for number, handler in self.previous.items():
                signal.signal(number, handler)
        finally:
            self.defer = False
        pending = self.pending
        self.pending = []
        return pending


def _arm_cleanup(signals, clear):
    """Arm deferral, run clear once, then restore the previous handlers.

    The try is the first work. clear() deletes a published success when the
    merge is not confirmed. Deferral is armed before that call. A catchable
    signal on the arming line raises before the store; the handler has already
    recorded it and armed deferral, and this function still runs clear(). A
    signal before this try is active leaves the function without clear() or
    restore(). The caller catches that signal and calls again. Deferral is
    already armed, so the second entry does not raise out of the prologue.
    Signals during clear() and restore() are recorded, not raised. Handlers
    are put back, not ignored. The merge itself is outside this function, so a
    signal there still aborts gh. The post is one attempt and is not atomic."""
    try:
        signals.defer = True
        if not signals.clear_started:
            signals.clear_started = True
            clear()
    except CaughtSignal:
        signals.defer = True
        if not signals.clear_started:
            signals.clear_started = True
            clear()
    finally:
        pending = signals.restore()
    return pending


def _on_signal(number, _frame):
    raise CaughtSignal(number)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse redirects so Authorization is not sent to another host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def _allowed_env(source, keys, secrets=()):
    """Copy only named variables. Drop a value that contains a caller-supplied secret."""
    hidden = [item for item in secrets if isinstance(item, str) and item]
    child = {}
    for key in keys:
        value = source.get(key)
        if not isinstance(value, str) or value == "":
            continue
        if any(secret in value for secret in hidden):
            continue
        child[key] = value
    return child


def sign_rs256(signing_input, key_path):
    """RS256 signature. The key stays in the file openssl opens. It is not an argument value.

    The signer is a new session. A SIGINT or SIGHUP aimed at this process group, as a
    terminal sends, does not kill it while a failure status is being signed."""
    result = subprocess.run(
        ["openssl", "dgst", "-sha256", "-sign", str(key_path), "-binary"],
        input=signing_input, capture_output=True, check=True, timeout=30,
        env=_allowed_env(os.environ, OPENSSL_ENV_KEYS),
        start_new_session=True)
    if not result.stdout:
        raise ValueError("empty signature")
    return result.stdout


def build_jwt(app_id, key_path, now, sign=None):
    """App JWT. iat is 60s in the past. exp is eight minutes ahead, under GitHub's ten."""
    issued = int(now) - 60
    header = b64url(json.dumps({"alg": "RS256", "typ": "JWT"}, separators=(",", ":")).encode())
    body = b64url(json.dumps(
        {"iat": issued, "exp": issued + 540, "iss": str(app_id)}, separators=(",", ":")).encode())
    signing = f"{header}.{body}".encode()
    signature = (sign or sign_rs256)(signing, key_path)
    return signing.decode() + "." + b64url(signature)


def key_problem(path, repo_root):
    """None when path is a regular 0600 file outside this repository. Otherwise a short reason."""
    if path.is_symlink():
        return "symlink"
    if not path.is_file():
        return "missing"
    try:
        path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode != 0o600:
            return f"mode {mode:04o}"
        return None
    return "inside repository"


def parse_app_id(value):
    if not isinstance(value, str) or not value.isdigit() or value.startswith("0"):
        return None
    number = int(value)
    return number if number > 0 else None


def http_request(method, url, headers, body, timeout=30):
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with _OPENER.open(request, timeout=timeout) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers), error.read()


def _headers(token, accept=ACCEPT, json_body=False):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": accept,
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if json_body:
        headers["Content-Type"] = "application/json"
    return headers


class Reader:
    """REST GET with GH_TOKEN. 404 and 406 raise CalledProcessError so the checker can branch.

    Readiness is fetch_readiness, a GraphQL CheckRun query, not this class."""

    def __init__(self, base, token, request):
        self.base = base.rstrip("/")
        self.token = token
        self.request = request

    def _json(self, method, path, body=None, accept=ACCEPT):
        status, headers, raw = self.request(
            method, self.base + path, _headers(self.token, accept, body is not None), body)
        if status in (404, 406):
            raise subprocess.CalledProcessError(1, path, stderr=f"HTTP {status}")
        if status < 200 or status >= 300:
            raise subprocess.CalledProcessError(1, path, stderr=f"HTTP {status}")
        text = raw.decode() if raw else ""
        if accept != ACCEPT:
            return text, headers
        return (json.loads(text) if text else None), headers

    def read(self, endpoint):
        if "per_page" in endpoint:
            return self._pages("/" + endpoint)
        payload, _ = self._json("GET", "/" + endpoint)
        return payload

    def _pages(self, path):
        pages = []
        while path:
            payload, headers = self._json("GET", path)
            if not isinstance(payload, list):
                raise ValueError("page")
            pages.append(payload)
            path = self._next_link(headers.get("Link") or headers.get("link"))
        return pages

    def _next_link(self, header):
        if not isinstance(header, str):
            return None
        for part in header.split(","):
            if 'rel="next"' not in part:
                continue
            start, end = part.find("<"), part.find(">")
            if start == -1 or end < start:
                raise ValueError("link")
            url = part[start + 1:end]
            prefix = self.base + "/"
            if not url.startswith(prefix):
                raise ValueError("link")
            return url[len(self.base):]
        return None


def decide(repo, number, sha, read):
    """Evidence for this owner/repo/PR/SHA. skip and unverified must not POST."""
    notes = io.StringIO()
    try:
        with redirect_stdout(notes):
            return _decide(repo, number, sha, read)
    finally:
        text = notes.getvalue()
        if text:
            print(text, file=sys.stderr, end="" if text.endswith("\n") else "\n")


def _decide(repo, number, sha, read):
    try:
        pull = read(f"repos/{repo}/pulls/{number}")
        if not isinstance(pull, dict):
            raise ValueError("pull request")
        head = (pull.get("head") or {}).get("sha")
        if not isinstance(head, str) or not review.full_oid(head) or head.lower() != sha.lower():
            return Decision("skip", "head", sha)
        if pull.get("state") != "open":
            return Decision("skip", "closed", head)
        base = (pull.get("base") or {}).get("sha")
        if not isinstance(base, str) or not review.full_oid(base):
            raise ValueError("base")
        absent = review.missing(repo, number, head, base, read)
        if review.BASE_REF in absent:
            return Decision("skip", "base", head)
        gaps = [item for item in absent if item != review.BASE_REF]
        if gaps:
            return Decision("failure", ",".join(gaps), head)
        return Decision("success", "", head)
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        return Decision("unverified", f"{type(error).__name__}", sha)


def status_description(state, sha, digest=None):
    """Commit-status description. At most 140 characters. The digest is not rechecked by GitHub."""
    text = f"review/gate {state} {sha}"
    if digest:
        text = f"{text} {digest}"
    if len(text) > 140:
        raise ValueError("description")
    return text


def evidence_snapshot(body, head, comment_pages, owner):
    """Parsed author, ## Review fields, and unedited owner approvals.

    None when that parse is incomplete. HTML comments and other prose are not part of the
    snapshot. Callers compare this object, not the raw pull request body."""
    if not isinstance(body, str) or not review.full_oid(head):
        return None
    text = review.visible_text(body.replace("\r\n", "\n").replace("\r", "\n"))
    if text is None:
        return None
    record, previous, _errors = review.parse_author(text[:review.BODY_LIMIT])
    fields = review.review_section(text[:review.BODY_LIMIT])
    if fields is None:
        return None
    approvals = []
    wanted = head.lower()
    for page in comment_pages or []:
        if not isinstance(page, list):
            return None
        for comment in page:
            if not isinstance(comment, dict) or not review.comment_unedited(comment):
                continue
            user = comment.get("user")
            login = user.get("login") if isinstance(user, dict) else None
            if review.bot_creator(login) or not review.same_login(login, owner):
                continue
            if review.approval_sha(comment.get("body")) != wanted:
                continue
            approvals.append({
                "login": login,
                "created_at": comment.get("created_at"),
                "updated_at": comment.get("updated_at"),
                "sha": wanted,
            })
    approvals.sort(key=lambda item: (str(item["created_at"]), str(item["login"])))
    payload = {
        "head": wanted,
        "author": [record[0], record[1]] if record else None,
        "previous": list(previous),
        "review": fields,
        "approvals": approvals,
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    return payload, hashlib.sha256(raw).hexdigest()


def _comment_pages(repo, number, read):
    pages = read(f"repos/{repo}/issues/{number}/comments?per_page=100")
    if not isinstance(pages, list):
        raise ValueError("comments")
    return pages


def take_snapshot(repo, number, sha, read):
    pull = read(f"repos/{repo}/pulls/{number}")
    if not isinstance(pull, dict):
        raise ValueError("pull request")
    owner = review.repository_owner(repo, read)
    return evidence_snapshot(pull.get("body"), sha, _comment_pages(repo, number, read), owner)


def parse_readiness(payload):
    """Normalize one GraphQL payload. None when the shape cannot prove the pull request is ready."""
    if not isinstance(payload, dict) or payload.get("errors"):
        return None
    pull = ((payload.get("data") or {}).get("repository") or {}).get("pullRequest")
    if not isinstance(pull, dict):
        return None
    threads = pull.get("reviewThreads") if isinstance(pull.get("reviewThreads"), dict) else {}
    nodes = (pull.get("commits") or {}).get("nodes") if isinstance(pull.get("commits"), dict) else None
    commit = nodes[0].get("commit") if isinstance(nodes, list) and nodes and isinstance(nodes[0], dict) else None
    rollup = commit.get("statusCheckRollup") if isinstance(commit, dict) else None
    contexts = rollup.get("contexts") if isinstance(rollup, dict) else None
    return {
        "review": pull.get("reviewDecision"),
        "threads": threads.get("nodes") if isinstance(threads.get("nodes"), list) else None,
        "threads_more": bool((threads.get("pageInfo") or {}).get("hasNextPage")) if isinstance(threads.get("pageInfo"), dict) else True,
        "head": commit.get("oid") if isinstance(commit, dict) else None,
        "contexts": contexts.get("nodes") if isinstance(contexts, dict) and isinstance(contexts.get("nodes"), list) else None,
        "contexts_more": bool((contexts.get("pageInfo") or {}).get("hasNextPage")) if isinstance(contexts, dict) and isinstance(contexts.get("pageInfo"), dict) else True,
    }


def _attempt_started(ctx):
    """When this attempt began. Completion time is not an order: a late finish is still the older run."""
    key = "startedAt" if ctx.get("name") else "createdAt"
    value = ctx.get(key)
    if isinstance(value, str) and value:
        return value
    return None


def _app_id(ctx):
    suite = ctx.get("checkSuite")
    app = suite.get("app") if isinstance(suite, dict) else None
    value = app.get("databaseId") if isinstance(app, dict) else None
    return value if type(value) is int else None


def _latest(items):
    """Newest attempt by start time. None when a tie disagrees or a start time is missing.

    List order is not a tie break. A later completion of an earlier run does not beat a run
    that started after it and is still in progress."""
    if not items:
        return None
    if len(items) == 1:
        return items[0]
    stamped = [(_attempt_started(item), item) for item in items]
    if any(stamp is None for stamp, _item in stamped):
        return None
    newest = max(stamp for stamp, _item in stamped)
    chosen = [item for stamp, item in stamped if stamp == newest]
    if len(chosen) == 1:
        return chosen[0]
    if len({_check_state(item) for item in chosen}) == 1:
        return chosen[0]
    return None


def _required_ok(ctx):
    if ctx.get("name"):
        return ctx.get("status") == "COMPLETED" and ctx.get("conclusion") == "SUCCESS"
    return ctx.get("state") == "SUCCESS"


def _required_pending(ctx):
    if ctx.get("name"):
        return ctx.get("status") in {"QUEUED", "IN_PROGRESS", "PENDING", "WAITING", "REQUESTED"} or (
            ctx.get("status") != "COMPLETED" and not ctx.get("conclusion"))
    return ctx.get("state") in {"PENDING", "EXPECTED", None, ""}


def _check_state(chosen):
    if chosen is None:
        return "unknown"
    if _required_ok(chosen):
        return "ok"
    if _required_pending(chosen):
        return "pending"
    return "failed"


def expected_checks(payload, signing_app):
    """Required contexts from the default-branch settings document.

    The gate context is omitted from the returned list. Its app id must be the positive
    integer of the app that will sign, and it must not be the Actions app. Other checks
    also require a positive pinned app id. GitHub's unpinned marker -1 is rejected.
    A REPLACE placeholder is not a check."""
    protection = (payload.get("expected") or {}).get("protection") if isinstance(payload, dict) else None
    checks = (protection or {}).get("required_status_checks", {}).get("checks") if isinstance(protection, dict) else None
    if not isinstance(checks, list) or not checks:
        raise ValueError("settings")
    others = []
    gate_app = None
    for item in checks:
        if not isinstance(item, dict):
            raise ValueError("settings")
        name = item.get("context")
        app = item.get("app_id")
        if not isinstance(name, str) or name == "" or name.startswith("REPLACE:"):
            raise ValueError("settings")
        if type(app) is not int or app <= 0:
            raise ValueError("settings")
        if name == CONTEXT:
            if app == ACTIONS_APP:
                raise ValueError("settings")
            gate_app = app
        else:
            others.append((name, app))
    if gate_app != signing_app or not others:
        raise ValueError("settings")
    return others


def load_expected_checks(repo, read, signing_app):
    """Settings on the repository default branch. The pull request head is not a source."""
    info = read(f"repos/{repo}")
    default = info.get("default_branch") if isinstance(info, dict) else None
    if not isinstance(default, str) or default == "" or "/" in default or default.startswith("."):
        raise ValueError("settings")
    ref = urllib.parse.quote(default, safe="")
    blob = read(f"repos/{repo}/contents/.github/repository-settings.json?ref={ref}")
    if not isinstance(blob, dict) or blob.get("encoding") != "base64" or not isinstance(blob.get("content"), str):
        raise ValueError("settings")
    try:
        payload = json.loads(base64.b64decode(blob["content"]))
    except (ValueError, json.JSONDecodeError):
        raise ValueError("settings")
    return expected_checks(payload, signing_app)


def readiness_problems(pull, view, sha, expected):
    """Blockers other than this App's own review/gate status.

    expected is the default-branch (context, app id) list. A name match with the wrong app
    does not count. The rollup page is at most READINESS_PAGE contexts. A further page fails
    closed. An older failed attempt does not block when a newer attempt of that check passed."""
    problems = []
    if not isinstance(pull, dict) or not isinstance(view, dict):
        return ["checks-unknown"]
    if pull.get("draft") is True:
        problems.append("draft")
    if pull.get("auto_merge"):
        problems.append("auto-merge")
    head = view.get("head")
    if not isinstance(head, str) or head.lower() != sha.lower():
        problems.append("head")
    review_state = view.get("review")
    if review_state in {"CHANGES_REQUESTED", "REVIEW_REQUIRED"}:
        problems.append("review")
    if view.get("threads_more") or not isinstance(view.get("threads"), list):
        problems.append("threads-unknown")
    elif any(not isinstance(item, dict) or item.get("isResolved") is not True for item in view["threads"]):
        problems.append("thread")
    if view.get("contexts_more") or not isinstance(view.get("contexts"), list):
        problems.append("checks-unknown")
        return problems
    if not isinstance(expected, list) or not expected:
        problems.append("checks-unknown")
        return problems
    grouped = {}
    for ctx in view["contexts"]:
        if not isinstance(ctx, dict) or ctx.get("isRequired") is not True:
            continue
        name = ctx.get("name") or ctx.get("context")
        if not isinstance(name, str) or name == "" or name == CONTEXT:
            continue
        grouped.setdefault(name, []).append(ctx)
    failed = pending = unknown = False
    expected_names = {name for name, _app in expected}
    for name, app in expected:
        found = [item for item in grouped.get(name, []) if _app_id(item) == app]
        state = _check_state(_latest(found) if found else None)
        if not found or state == "unknown":
            unknown = True
        elif state == "pending":
            pending = True
        elif state == "failed":
            failed = True
    for name in grouped:
        if name not in expected_names:
            unknown = True
    if unknown:
        problems.append("checks-unknown")
    elif failed:
        problems.append("checks-failed")
    elif pending:
        problems.append("checks-pending")
    return problems


def fetch_readiness(base, token, request, repo, number):
    owner, name = repo.split("/", 1)
    status, _, raw = request(
        "POST", base + "/graphql",
        {**_headers(token), "Content-Type": "application/json"},
        {"query": READINESS_QUERY, "variables": {"owner": owner, "name": name, "number": int(number)}})
    if status != 200:
        raise subprocess.CalledProcessError(1, "readiness", stderr=f"HTTP {status}")
    payload = json.loads(raw.decode() or "null")
    parsed = parse_readiness(payload)
    if parsed is None:
        raise ValueError("readiness")
    return parsed


def poll_readiness(base, token, request, repo, number, read, sha, sleep, polls, wait, signing_app):
    """Re-read pending required checks a bounded number of times. Do not arm auto-merge."""
    expected = load_expected_checks(repo, read, signing_app)
    last = ["checks-unknown"]
    for attempt in range(polls):
        pull = read(f"repos/{repo}/pulls/{number}")
        view = fetch_readiness(base, token, request, repo, number)
        last = readiness_problems(pull, view, sha, expected)
        if "checks-pending" not in last or any(item != "checks-pending" for item in last):
            return last
        if attempt + 1 == polls:
            return last
        sleep(wait)
    return last


def merge_command(argv, env):
    """Developer gh. The caller strips tokens from env. stderr is returned, not trusted."""
    result = subprocess.run(argv, env=env, capture_output=True, timeout=120)
    return result.returncode, result.stderr.decode("utf-8", "replace")


def merge_child_env(env, secrets):
    """Developer gh login from the keyring. Host overrides and tokens are not copied."""
    child = _allowed_env(env, GH_ENV_KEYS, secrets)
    child["GH_PROMPT_DISABLED"] = "1"
    return child


def _redact(text, secrets):
    cleaned = text
    for secret in secrets:
        if isinstance(secret, str) and secret:
            cleaned = cleaned.replace(secret, "[redacted]")
    return cleaned


def merge_observed(pull, sha):
    """True when this SHA is merged, False when the pull is still open, None when that is unknown."""
    if not isinstance(pull, dict) or not review.full_oid(sha):
        return None
    head = (pull.get("head") or {}).get("sha") if isinstance(pull.get("head"), dict) else None
    same = isinstance(head, str) and head.lower() == sha.lower()
    if pull.get("merged") is True and pull.get("state") == "closed" and same:
        return True
    if pull.get("state") == "open" and pull.get("merged") is not True and same:
        return False
    return None


def mint_and_post(base, app_id, key_path, repo, sha, state, request, now, sign=None, digest=None, on_publish=None):
    """Installation token for this repository's statuses only, then one POST to this SHA."""
    jwt = build_jwt(app_id, key_path, now, sign)
    name = repo.split("/", 1)[1]
    installation, _ = _jwt_json(base, "GET", f"/repos/{repo}/installation", jwt, request, None)
    installation_id = installation.get("id") if isinstance(installation, dict) else None
    if type(installation_id) is not int or installation_id <= 0:
        raise ValueError("installation")
    minted, _ = _jwt_json(
        base, "POST", f"/app/installations/{installation_id}/access_tokens", jwt, request,
        {"repositories": [name], "permissions": {"statuses": "write"}})
    token = minted.get("token") if isinstance(minted, dict) else None
    if not isinstance(token, str) or token == "" or token == jwt:
        raise ValueError("token")
    body = {"state": state, "context": CONTEXT, "description": status_description(state, sha, digest)}
    if on_publish is not None:
        on_publish()
    status, _, raw = request(
        "POST", f"{base}/repos/{repo}/statuses/{sha}",
        {**_headers(token), "Content-Type": "application/json"}, body)
    if status not in (200, 201):
        raise subprocess.CalledProcessError(1, "statuses", stderr=f"HTTP {status}")
    posted = json.loads(raw.decode() or "{}")
    if not isinstance(posted, dict) or posted.get("context") != CONTEXT or posted.get("state") != state:
        raise ValueError("posted status")
    return posted


def _jwt_json(base, method, path, jwt, request, body):
    headers = _headers(jwt, json_body=body is not None)
    status, response_headers, raw = request(method, base + path, headers, body)
    if status < 200 or status >= 300:
        raise subprocess.CalledProcessError(1, path, stderr=f"HTTP {status}")
    return json.loads(raw.decode() or "null"), response_headers


def _repo_ok(repo):
    return re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]+", repo or "") is not None and repo.split("/")[-1] not in {".", ".."}


def _key_ready(env):
    app_id = parse_app_id(env.get("REVIEW_GATE_APP_ID"))
    key = Path(env.get("REVIEW_GATE_APP_KEY") or "")
    if app_id is None:
        return None, None, "REVIEW_GATE_APP_ID"
    if not env.get("REVIEW_GATE_APP_KEY"):
        return None, None, "REVIEW_GATE_APP_KEY"
    problem = key_problem(key, ROOT)
    if problem:
        return None, None, problem
    return app_id, key, None


def _emit(report, code):
    print(json.dumps(report, ensure_ascii=False))
    return code


def _invalidate(base, app_id, key, repo, sha, request, now, sign):
    """Post failure on the SHA whose success may have been published. Return the cleanup exception, or None.

    Catchable signals are not swallowed. The caller defers them for the duration of this post."""
    try:
        mint_and_post(base, app_id, key, repo, sha, "failure", request, now, sign)
    except (KeyboardInterrupt, CaughtSignal):
        raise
    except Exception as error:
        print(f"review gate cleanup failed: {type(error).__name__}", file=sys.stderr)
        return error
    return None


def _observe_merge(read, repo, number, sha):
    """None when the read fails. An interrupt is not a failed read."""
    try:
        return merge_observed(read(f"repos/{repo}/pulls/{number}"), sha)
    except (KeyboardInterrupt, CaughtSignal):
        raise
    except Exception:
        return None


class _PublishGuard:
    def __init__(self):
        self.attempted = False

    def arm(self):
        self.attempted = True


def developer_login(env, secrets):
    """Login gh will use for the merge. Host overrides and tokens are not in that environment."""
    result = subprocess.run(
        ["gh", "api", "user", "--jq", ".login"],
        env=merge_child_env(env, secrets), capture_output=True, text=True, timeout=30)
    login = result.stdout.strip()
    if result.returncode != 0 or login == "" or "\n" in login or login.endswith("[bot]"):
        raise ValueError("login")
    return login


def run(argv, env, request, now=None, sign=None, merge=None, sleep=None, polls=POLL_LIMIT, poll_wait=POLL_WAIT, who=None):
    parser = argparse.ArgumentParser(
        description="Post review/gate for one pull request head. "
        "Reads need GH_TOKEN in this process. The daily path uses the developer gh auth token there. "
        "This command does not call gh auth token. Signing uses the App PEM.")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--merge", action="store_true")
    args = parser.parse_args(argv)
    now = time.time if now is None else now
    sleep = time.sleep if sleep is None else sleep
    merge = merge_command if merge is None else merge
    who = developer_login if who is None else who
    if env.get("GITHUB_ACTIONS"):
        print("review gate refused: GITHUB_ACTIONS is set", file=sys.stderr)
        return 2
    if not _repo_ok(args.repo) or not args.pr.isdigit() or args.pr.startswith("0") or not review.full_oid(args.sha):
        print("review gate refused: repo, pr, or sha", file=sys.stderr)
        return 2
    token = env.get("GH_TOKEN") or ""
    if not token:
        print("review gate refused: GH_TOKEN must be set for reads", file=sys.stderr)
        return 2
    base = (env.get("REVIEW_GATE_API") or API).rstrip("/")
    reader = Reader(base, token, request)
    decision = decide(args.repo, args.pr, args.sha, reader.read)
    report = {"result": "dry-run" if args.dry_run else "merge" if args.merge else "post",
              "kind": decision.kind, "state": decision.state if decision.posts else None,
              "context": CONTEXT, "repo": args.repo, "sha": decision.sha, "detail": decision.detail}
    if args.dry_run or not decision.posts:
        if args.dry_run and args.merge and decision.kind == "success":
            try:
                signing_app = parse_app_id(env.get("REVIEW_GATE_APP_ID"))
                if signing_app is None:
                    raise ValueError("settings")
                problems = poll_readiness(
                    base, token, request, args.repo, args.pr, reader.read, decision.sha, sleep, 1, 0, signing_app)
            except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
                report["kind"] = "unverified"
                report["state"] = None
                report["detail"] = type(error).__name__
                print(f"review gate UNVERIFIED: {type(error).__name__}", file=sys.stderr)
                return _emit(report, 2)
            if problems:
                report["kind"] = "blocked"
                report["state"] = None
                report["detail"] = ",".join(problems)
                if "auto-merge" in problems:
                    print("review gate refused: auto-merge is armed; disable it with "
                          f"gh pr merge {args.pr} --repo {args.repo} --disable-auto", file=sys.stderr)
                return _emit(report, 1)
        print(json.dumps(report, ensure_ascii=False))
        if not args.dry_run and decision.kind == "unverified":
            print(f"review gate UNVERIFIED: {decision.detail}", file=sys.stderr)
        return decision.code
    app_id, key, problem = _key_ready(env)
    if problem:
        print(f"review gate refused: {problem}", file=sys.stderr)
        return 2
    secrets = [token, str(key)]
    if decision.kind == "failure":
        try:
            mint_and_post(base, app_id, key, args.repo, decision.sha, "failure", request, now(), sign)
        except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            print(f"review gate UNVERIFIED: {type(error).__name__}", file=sys.stderr)
            return 2
        return _emit(report, decision.code)
    # Passing evidence. A plain run posts pending and does not merge.
    snapshot = None
    try:
        snapshot = take_snapshot(args.repo, args.pr, decision.sha, reader.read)
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        snapshot = None
    digest = snapshot[1] if snapshot else None
    if not args.merge:
        try:
            mint_and_post(base, app_id, key, args.repo, decision.sha, "pending", request, now(), sign, digest)
        except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            print(f"review gate UNVERIFIED: {type(error).__name__}", file=sys.stderr)
            return 2
        report["kind"] = "pending"
        report["state"] = "pending"
        report["detail"] = "run --merge to post success and squash-merge this sha"
        return _emit(report, 0)
    try:
        problems = poll_readiness(
            base, token, request, args.repo, args.pr, reader.read, decision.sha, sleep, polls, poll_wait, app_id)
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"review gate UNVERIFIED: {type(error).__name__}", file=sys.stderr)
        report["kind"] = "unverified"
        report["state"] = None
        report["detail"] = type(error).__name__
        return _emit(report, 2)
    if problems:
        report["kind"] = "blocked"
        report["state"] = None
        report["detail"] = ",".join(problems)
        if "auto-merge" in problems:
            print("review gate refused: auto-merge is armed; disable it with "
                  f"gh pr merge {args.pr} --repo {args.repo} --disable-auto", file=sys.stderr)
        elif "checks-pending" in problems:
            print("review gate refused: required checks still pending; re-run --merge when they pass. "
                  "Do not arm auto-merge.", file=sys.stderr)
        return _emit(report, 1)
    if snapshot is None:
        print("review gate UNVERIFIED: snapshot", file=sys.stderr)
        return 2
    try:
        login = who(env, secrets)
    except (KeyboardInterrupt, CaughtSignal):
        raise
    except Exception:
        print("review gate UNVERIFIED: login", file=sys.stderr)
        report["kind"] = "unverified"
        report["state"] = None
        report["detail"] = "login"
        return _emit(report, 2)
    if not isinstance(login, str) or login == "" or login.endswith("[bot]"):
        print("review gate refused: login", file=sys.stderr)
        return 2
    guard = _PublishGuard()
    signals = _SignalGate()
    signals.install()
    merged_ok = False
    interrupt = None
    primary = None
    merge_code = None
    merge_text = ""
    cleanup_error = None
    pending = []

    def clear_published():
        nonlocal merged_ok, cleanup_error, interrupt
        if guard.attempted and not merged_ok:
            try:
                if _observe_merge(reader.read, args.repo, args.pr, decision.sha) is True:
                    merged_ok = True
            except (KeyboardInterrupt, CaughtSignal) as error:
                interrupt = interrupt or error
            if not merged_ok:
                cleanup_error = _invalidate(
                    base, app_id, key, args.repo, decision.sha, request, now(), sign)

    try:
        try:
            mint_and_post(
                base, app_id, key, args.repo, decision.sha, "success", request, now(), sign, digest, guard.arm)
            again = decide(args.repo, args.pr, decision.sha, reader.read)
            checked = take_snapshot(args.repo, args.pr, decision.sha, reader.read)
            if again.kind != "success" or again.sha.lower() != decision.sha.lower() or checked is None or checked[0] != snapshot[0]:
                raise ValueError("recheck")
            argv = ["gh", "pr", "merge", args.pr, "--repo", args.repo, "--squash", "--match-head-commit", decision.sha]
            merge_code, merge_text = merge(argv, merge_child_env(env, secrets))
            seen = _observe_merge(reader.read, args.repo, args.pr, decision.sha)
            if seen is True:
                merged_ok = True
            elif merge_code != 0:
                primary = "merge"
            elif seen is False:
                primary = "merge-open"
            else:
                primary = "merge-unknown"
        except (KeyboardInterrupt, CaughtSignal) as error:
            interrupt = error
            print(f"review gate interrupted: {type(error).__name__}", file=sys.stderr)
        except (SystemExit, GeneratorExit):
            primary = "abort"
            raise
        except Exception as error:
            if isinstance(error, AssertionError):
                raise
            if type(error) is ValueError and str(error) == "recheck":
                primary = "recheck"
            elif type(error) is ValueError and str(error) == "posted status":
                primary = "posted-status"
            else:
                primary = type(error).__name__
        finally:
            # gh has already returned or been aborted. A signal before
            # _arm_cleanup's try, or on the deferral assignment, still reaches
            # the except below or the try inside _arm_cleanup. Either path posts
            # failure and restores the previous handlers.
            pending = _arm_cleanup(signals, clear_published)
    except CaughtSignal as error:
        signals.defer = True
        pending = _arm_cleanup(signals, clear_published)
        if isinstance(error.__context__, (SystemExit, GeneratorExit)):
            raise error.__context__
    if interrupt is None and pending:
        interrupt = CaughtSignal(pending[0])
    if merged_ok:
        if interrupt is not None:
            raise interrupt
        report["kind"] = "success"
        report["state"] = "success"
        report["detail"] = digest
        return _emit(report, 0)
    if not guard.attempted:
        print(f"review gate UNVERIFIED: {primary}", file=sys.stderr)
        report["kind"] = "unverified"
        report["state"] = None
        report["detail"] = primary or "publish"
        code = 2
    else:
        if merge_code not in (None, 0):
            print(f"review gate merge failed: {merge_code} {_redact(merge_text if isinstance(merge_text, str) else '', secrets)}", file=sys.stderr)
        else:
            print(f"review gate {primary or 'cleanup'}", file=sys.stderr)
        detail = primary or "cleanup"
        if cleanup_error is not None:
            detail += "; cleanup failed"
        report["kind"] = "failure"
        report["state"] = None if cleanup_error else "failure"
        report["detail"] = detail
        code = 2 if cleanup_error is not None else 1
    if interrupt is not None:
        raise interrupt
    return _emit(report, code)


def main(argv=None, env=None, request=None, now=None, sign=None, merge=None, sleep=None,
         polls=POLL_LIMIT, poll_wait=POLL_WAIT, who=None):
    return run(argv if argv is not None else sys.argv[1:], env if env is not None else os.environ,
               request or http_request, now, sign, merge, sleep, polls, poll_wait, who)


if __name__ == "__main__":
    raise SystemExit(main())

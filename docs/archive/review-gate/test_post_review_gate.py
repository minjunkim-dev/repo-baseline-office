"""Mac-side review/gate poster. HTTP is mocked. No key material is committed."""

import base64
from contextlib import redirect_stderr, redirect_stdout
import http.client
import io
import json
import linecache
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import post_review_gate as gate
import check_review_status as review

HEAD = "a" * 40
OTHER = "c" * 40
BASE = "b" * 40
REPO = "minjunkim-dev/repo-baseline"
OWNER = "minjunkim-dev"
API = "https://api.github.com"


def evidence(head, reviewer="Claude Code / Opus 5.5"):
    """Slim PR body. The head is not part of the review record; the owner comment carries it."""
    return "\n".join([
        "Author: Cursor 클라우드 에이전트 / grok-4.7", "",
        "## Review",
        f"리뷰어(구현과 다른 컨텍스트, 도구/모델): {reviewer}",
        "고친 것: 없음",
        "남은 지적: 없음", "",
    ])


def pull(head=HEAD, state="open", body=None, user=OWNER, files_commit_count=1, ref="main"):
    return {
        "state": state,
        "body": evidence(head) if body is None else body,
        "user": {"login": user},
        "head": {"sha": head},
        "base": {"sha": BASE, "ref": ref},
        "commits": files_commit_count,
    }


def status(context, state="success", login=OWNER):
    return {"context": context, "state": state, "creator": {"login": login}}


def comment(head, login=OWNER, edited=False):
    stamp = "2026-11-06T00:00:00Z"
    return {
        "user": {"login": login},
        "body": f"되돌리기 어려움 승인: {head}\n",
        "created_at": stamp,
        "updated_at": "2026-11-06T00:00:01Z" if edited else stamp,
    }


class Scripted:
    """Checker-shaped read. Status and comment endpoints are already page lists."""

    def __init__(self, repo_pull, files, statuses, comments=None, commits=None):
        self.pull = repo_pull
        self.files = files
        self.statuses = statuses
        self.comments = comments or []
        self.commits = commits or [{"sha": HEAD, "commit": {"committer": {"date": "2026-11-06T00:00:00Z"}}}]
        self.agents = None

    def read(self, endpoint):
        if endpoint == f"repos/{REPO}/pulls/7":
            return self.pull
        if endpoint == f"repos/{REPO}":
            return {"default_branch": "main", "owner": {"login": OWNER}}
        if endpoint == f"repos/{REPO}/compare/{BASE}...main":
            return {"status": "identical"}
        if endpoint.startswith(f"repos/{REPO}/contents/"):
            if self.agents is not None and "AGENTS.md" in endpoint:
                return {"content": base64.b64encode(self.agents.encode()).decode(), "encoding": "base64"}
            raise subprocess.CalledProcessError(1, endpoint, stderr="HTTP 404")
        if endpoint == f"repos/{REPO}/compare/{BASE}...{self.pull['head']['sha']}":
            return {"files": self.files, "commits": self.commits}
        if endpoint == f"repos/{REPO}/commits/{self.pull['head']['sha']}/statuses?per_page=100":
            return [self.statuses]
        if endpoint == f"repos/{REPO}/issues/7/comments?per_page=100":
            return [self.comments]
        if endpoint == f"repos/{REPO}/pulls/7/commits?per_page=100":
            return [self.commits]
        raise AssertionError(endpoint)


def decide(scripted, sha=HEAD):
    return gate.decide(REPO, "7", sha, scripted.read)


class DecideTests(unittest.TestCase):
    def test_posts_success_from_the_evidence_table_without_review_statuses(self):
        files = [{"filename": "README.md", "patch": "@@\n-a\n+b\n"}]
        found = decide(Scripted(pull(), files, []))
        self.assertEqual(found.kind, "success")
        self.assertEqual(found.sha, HEAD)
        self.assertNotIn("review/independent", found.detail)
        self.assertNotIn("review/security", found.detail)

    def test_the_review_record_does_not_require_a_security_status(self):
        files = [{"filename": "README.md", "patch": "@@\n-a\n+b\n"}]
        body = evidence(HEAD)
        found = decide(Scripted(pull(body=body), files, []))
        self.assertEqual(found.kind, "success")
        failed = [status("review/independent", state="failure"), status("review/security", state="failure")]
        self.assertEqual(decide(Scripted(pull(body=body), files, failed)).kind, "success")

    def test_a_trust_boundary_path_needs_the_owner_comment(self):
        files = [{"filename": ".github/repository-settings.json", "patch": "@@\n-a\n+b\n"}]
        body = evidence(HEAD)
        bare = decide(Scripted(pull(body=body), files, []))
        self.assertEqual(bare.kind, "failure")
        self.assertIn(review.OWNER, bare.detail)
        self.assertNotIn("review/security", bare.detail)
        approved = decide(Scripted(pull(body=body), files, [], comments=[comment(HEAD)]))
        self.assertEqual(approved.kind, "success")
        edited = decide(Scripted(pull(body=body), files, [], comments=[comment(HEAD, edited=True)]))
        self.assertEqual(edited.kind, "failure")
        source = Path(gate.__file__).read_text(encoding="utf-8")
        self.assertNotIn("lastEditedAt", source)
        self.assertIn("updated_at", source)

    def test_head_mismatch_and_a_closed_pull_do_not_count_as_evidence_failure(self):
        files = [{"filename": "README.md"}]
        mismatch = decide(Scripted(pull(head=OTHER), files, [status("review/independent")]), sha=HEAD)
        self.assertEqual(mismatch.kind, "skip")
        self.assertEqual(mismatch.detail, "head")
        closed = decide(Scripted(pull(state="closed"), files, [status("review/independent")]))
        self.assertEqual(closed.kind, "skip")
        self.assertEqual(closed.detail, "closed")

    def test_a_team_profile_ignores_a_bot_review_status(self):
        files = [{"filename": "README.md", "patch": "@@\n-a\n+b\n"}]
        scripted = Scripted(pull(), files, [status("review/independent", login="github-actions[bot]")])
        scripted.agents = "프로필: 팀\n"
        found = decide(scripted)
        self.assertEqual(found.kind, "success")
        self.assertNotIn("review/independent", found.detail)

    def test_a_same_family_review_passes_and_still_needs_the_owner_on_a_gate_path(self):
        body = evidence(HEAD, reviewer="Cursor / grok-4.6")
        docs = [{"filename": "README.md", "patch": "@@\n-a\n+b\n"}]
        self.assertEqual(decide(Scripted(pull(body=body), docs, [])).kind, "success")
        gate_path = [{"filename": "scripts/check_review_status.py", "patch": "@@\n-a\n+b\n"}]
        bare = decide(Scripted(pull(body=body), gate_path, []))
        self.assertEqual(bare.kind, "failure")
        self.assertIn(review.OWNER, bare.detail)
        self.assertNotIn(review.EVIDENCE, bare.detail)
        approved = decide(Scripted(pull(body=body), gate_path, [], comments=[comment(HEAD)]))
        self.assertEqual(approved.kind, "success")
        first = gate.evidence_snapshot(body, HEAD, [], OWNER)
        second = gate.evidence_snapshot(body.replace("남은 지적: 없음", "남은 지적: P2 하나"), HEAD, [], OWNER)
        self.assertEqual(first[0]["review"]["reviewer"], ["Cursor / grok-4.6"])
        self.assertNotEqual(first[0]["review"], second[0]["review"])
        self.assertNotEqual(first[1], second[1])
        self.assertIsNone(gate.evidence_snapshot("Author: Cursor / grok-4.7\n", HEAD, [], OWNER))

    def test_an_unrun_review_fails_and_an_actions_status_does_not(self):
        files = [{"filename": "README.md", "patch": "@@\n-a\n+b\n"}]
        same = decide(Scripted(pull(body=evidence(HEAD, reviewer="미실행")), files, []))
        self.assertEqual(same.kind, "failure")
        self.assertIn(review.EVIDENCE, same.detail)
        forged = [status("review/independent", login="github-actions[bot]"), status("review/independent")]
        found = decide(Scripted(pull(), files, forged))
        self.assertEqual(found.kind, "success")
        self.assertNotIn("review/independent", found.detail)

    def test_dependabot_pin_bump_needs_the_same_gate_as_any_author(self):
        patch = "\n".join([
            "@@ -1 +1 @@",
            "-        uses: actions/checkout@" + "a" * 40 + " # v4.2.1",
            "+        uses: actions/checkout@" + "b" * 40 + " # v4.2.1",
        ])
        files = [{"filename": ".github/workflows/check.yml", "status": "modified", "patch": patch}]
        covered = evidence(HEAD)
        bot = pull(user="dependabot[bot]", body=covered)
        bare = decide(Scripted(bot, files, []))
        self.assertEqual(bare.kind, "failure")
        self.assertIn(review.OWNER, bare.detail)
        self.assertNotIn("review/independent", bare.detail)
        self.assertNotIn("review/security", bare.detail)
        empty = pull(body="", user="dependabot[bot]")
        statuses = [status("review/independent"), status("review/security")]
        missing_record = decide(Scripted(empty, files, statuses, comments=[comment(HEAD)]))
        self.assertEqual(missing_record.kind, "failure")
        self.assertIn(review.EVIDENCE, missing_record.detail)
        approved = decide(Scripted(bot, files, statuses, comments=[comment(HEAD)]))
        self.assertEqual(approved.kind, "success")
        person = pull(body=covered)
        self.assertEqual(decide(Scripted(person, files, [])).kind, "failure")
        self.assertEqual(decide(Scripted(person, files, statuses, comments=[comment(HEAD)])).kind, "success")

    def test_a_different_base_posts_nothing(self):
        files = [{"filename": "README.md"}]
        found = decide(Scripted(pull(ref="side"), files, [status("review/independent")]))
        self.assertEqual(found.kind, "skip")
        self.assertEqual(found.detail, "base")


def _key(mode=0o600):
    directory = tempfile.TemporaryDirectory()
    path = Path(directory.name) / "review-gate.pem"
    path.write_text("not a real key\n", encoding="utf-8")
    os.chmod(path, mode)
    return directory, path


def check_run(name, conclusion="SUCCESS", status="COMPLETED", app=15368, when="2026-11-07T00:00:00Z", required=True):
    return {
        "__typename": "CheckRun", "name": name, "status": status, "conclusion": conclusion,
        "isRequired": required, "startedAt": when, "completedAt": when,
        "checkSuite": {"app": {"databaseId": app}},
    }


def ready_payload(head=HEAD, contexts=None, threads=None, review=None, more_checks=False, more_threads=False):
    if contexts is None:
        contexts = [
            check_run("Baseline checks (Python 3.11)"),
            check_run("Baseline checks (Python 3.13)"),
            {"__typename": "StatusContext", "context": "review/gate", "state": "PENDING",
             "isRequired": True, "createdAt": "2026-11-07T00:00:00Z"},
        ]
    return {"data": {"repository": {"pullRequest": {
        "reviewDecision": review,
        "reviewThreads": {"pageInfo": {"hasNextPage": more_threads}, "nodes": [] if threads is None else threads},
        "commits": {"nodes": [{"commit": {
            "oid": head,
            "statusCheckRollup": {"contexts": {"pageInfo": {"hasNextPage": more_checks}, "nodes": contexts}},
        }}]},
    }}}}


class FakeHub:
    def __init__(self, repo_pull, files, statuses):
        self.pull = repo_pull
        self.files = files
        self.statuses = statuses
        self.comments = []
        self.graphql = []
        self.on_success = None
        self.fail_post = None
        self.fail_success_with = None
        self.wrong_success = False
        self.list_success = False
        self.after_success = None
        self.settings_checks = [
            {"context": "Baseline checks (Python 3.11)", "app_id": 15368},
            {"context": "Baseline checks (Python 3.13)", "app_id": 15368},
            {"context": "review/gate", "app_id": 424242},
        ]
        self.calls = []

    def __call__(self, method, url, headers, body):
        self.calls.append((method, url, dict(headers), body))
        path = url[len(API):]
        if path == f"/repos/{REPO}/pulls/7":
            if self.after_success is not None and any(
                    item[3].get("state") == "success" for item in self.calls if isinstance(item[3], dict) and "/statuses/" in item[1]):
                error = self.after_success
                self.after_success = None
                raise error
            return self._json(self.pull)
        if path == f"/repos/{REPO}":
            return self._json({"default_branch": "main", "owner": {"login": OWNER}})
        if path == f"/repos/{REPO}/compare/{BASE}...main":
            return self._json({"status": "identical"})
        compare_head = self.pull["head"]["sha"]
        if path == f"/repos/{REPO}/compare/{BASE}...{compare_head}":
            return self._json({"files": self.files, "commits": []})
        if path.startswith(f"/repos/{REPO}/contents/"):
            if path.startswith(f"/repos/{REPO}/contents/.github/repository-settings.json?ref=main"):
                raw = json.dumps({"expected": {"protection": {"required_status_checks": {
                    "checks": self.settings_checks}}}}).encode()
                return self._json({"encoding": "base64", "content": base64.b64encode(raw).decode()})
            return 404, {}, b""
        if path == f"/repos/{REPO}/commits/{compare_head}/statuses?per_page=100":
            return self._json(self.statuses)
        if path == f"/repos/{REPO}/issues/7/comments?per_page=100":
            return self._json([self.comments])
        if path == "/graphql":
            if not self.graphql:
                raise AssertionError("graphql")
            payload = self.graphql.pop(0)
            return self._json(payload)
        if path == f"/repos/{REPO}/installation":
            return self._json({"id": 99})
        if path == "/app/installations/99/access_tokens":
            return self._json({"token": "ghs_test_token"})
        if path.startswith(f"/repos/{REPO}/statuses/"):
            if self.fail_post and body and body.get("state") == self.fail_post:
                return 500, {}, b""
            if body and body.get("state") == "success" and self.fail_success_with is not None:
                error = self.fail_success_with
                self.fail_success_with = None
                raise error
            if body and body.get("state") == "success" and self.wrong_success:
                return 201, {}, json.dumps({"context": "review/gate", "state": "pending"}).encode()
            if body and body.get("state") == "success" and self.list_success:
                return 201, {}, b"[]"
            if body and body.get("state") == "success" and self.on_success:
                self.on_success()
            return 201, {}, json.dumps({"context": body["context"], "state": body["state"]}).encode()
        raise AssertionError(path)

    @staticmethod
    def _json(payload, status=200):
        return status, {}, json.dumps(payload).encode()


class HttpTests(unittest.TestCase):
    def env(self, key):
        return {
            "GH_TOKEN": "ghp_mac_read",
            "REVIEW_GATE_APP_ID": "424242",
            "REVIEW_GATE_APP_KEY": str(key),
            "REVIEW_GATE_API": API,
        }

    def hub(self, head=HEAD, statuses=None, state="open"):
        files = [{"filename": "README.md", "patch": "@@\n-a\n+b\n"}]
        statuses = [status("review/independent")] if statuses is None else statuses
        return FakeHub(pull(head=head, state=state), files, statuses)

    def test_dry_run_reads_evidence_and_does_not_mint_or_post(self):
        directory, key = _key()
        self.addCleanup(directory.cleanup)
        hub = self.hub()
        code = gate.main(
            ["--repo", REPO, "--pr", "7", "--sha", HEAD, "--dry-run"],
            self.env(key), hub, now=lambda: 1700000000, sign=lambda data, path: b"sig")
        self.assertEqual(code, 0)
        urls = [url for _, url, _, _ in hub.calls]
        self.assertTrue(any(url.endswith("/pulls/7") for url in urls))
        self.assertFalse(any("access_tokens" in url or "/statuses/" in url or "check-runs" in url for url in urls))
        auths = {headers["Authorization"] for _, _, headers, _ in hub.calls}
        self.assertEqual(auths, {"Bearer ghp_mac_read"})

    def test_success_posts_one_status_with_the_installation_token(self):
        directory, key = _key()
        self.addCleanup(directory.cleanup)
        hub = self.hub()
        code = gate.main(
            ["--repo", REPO, "--pr", "7", "--sha", HEAD],
            self.env(key), hub, now=lambda: 1700000000, sign=lambda data, path: b"sig")
        self.assertEqual(code, 0)
        posts = [item for item in hub.calls if item[0] == "POST" and item[1].endswith(f"/statuses/{HEAD}")]
        self.assertEqual(len(posts), 1)
        _, url, headers, body = posts[0]
        self.assertEqual(body["state"], "pending")
        self.assertEqual(body["context"], "review/gate")
        self.assertNotEqual(body["state"], "success")
        self.assertTrue(body["description"].startswith(f"review/gate pending {HEAD} "))
        self.assertLessEqual(len(body["description"]), 140)
        self.assertEqual(headers["Authorization"], "Bearer ghs_test_token")
        self.assertNotIn("check-runs", url)
        minted = [item for item in hub.calls if item[1].endswith("/access_tokens")]
        self.assertEqual(len(minted), 1)
        self.assertEqual(minted[0][3], {
            "repositories": ["repo-baseline"], "permissions": {"statuses": "write"},
        })
        self.assertEqual(minted[0][2]["Authorization"].count("."), 2)
        reads = [item for item in hub.calls if item[0] == "GET" and "/installation" not in item[1]]
        self.assertTrue(reads)
        self.assertTrue(all(item[2]["Authorization"] == "Bearer ghp_mac_read" for item in reads))
        self.assertTrue(all(item[2]["Authorization"] != "Bearer ghs_test_token" for item in hub.calls if item[0] == "GET"))

    def test_bad_evidence_posts_failure_for_that_sha_only(self):
        directory, key = _key()
        self.addCleanup(directory.cleanup)
        hub = self.hub(statuses=[status("review/independent", login="github-actions[bot]")])
        hub.pull = pull(body=evidence(HEAD, reviewer="미실행"))
        code = gate.main(
            ["--repo", REPO, "--pr", "7", "--sha", HEAD],
            self.env(key), hub, now=lambda: 1700000000, sign=lambda data, path: b"sig")
        self.assertEqual(code, 1)
        posts = [item for item in hub.calls if item[0] == "POST" and item[1].endswith(f"/statuses/{HEAD}")]
        self.assertEqual(posts[0][3]["state"], "failure")
        self.assertEqual(posts[0][3]["context"], "review/gate")
        self.assertFalse(any(item[0] == "GET" and "/commits/" in item[1] and "/statuses" in item[1] for item in hub.calls))

    def test_head_mismatch_does_not_post(self):
        directory, key = _key()
        self.addCleanup(directory.cleanup)
        hub = self.hub(head=OTHER)
        code = gate.main(
            ["--repo", REPO, "--pr", "7", "--sha", HEAD],
            self.env(key), hub, now=lambda: 1700000000, sign=lambda data, path: b"sig")
        self.assertEqual(code, 1)
        self.assertFalse(any("/statuses/" in url or "access_tokens" in url for _, url, _, _ in hub.calls))

    def test_actions_runtime_and_a_world_readable_key_do_not_post(self):
        def boom(*_args, **_kwargs):
            raise AssertionError("request")
        code = gate.main(
            ["--repo", REPO, "--pr", "7", "--sha", HEAD, "--dry-run"],
            {"GITHUB_ACTIONS": "true", "GH_TOKEN": "ghp_mac_read"}, boom)
        self.assertEqual(code, 2)
        directory, key = _key(0o644)
        self.addCleanup(directory.cleanup)
        hub = self.hub()
        code = gate.main(
            ["--repo", REPO, "--pr", "7", "--sha", HEAD],
            self.env(key), hub, now=lambda: 1700000000, sign=lambda data, path: b"sig")
        self.assertEqual(code, 2)
        self.assertFalse(any("/statuses/" in url for _, url, _, _ in hub.calls))

    def test_empty_read_token_is_refused_and_help_names_the_daily_path(self):
        text = gate.__doc__
        self.assertIn("gh auth token", text)
        self.assertIn("GraphQL CheckRun", text)
        self.assertIn("does not\ncall gh auth token", text)
        self.assertIn("--match-head-commit", text)
        self.assertNotIn("not the\ndeveloper gh token", text)
        self.assertIn("on CheckRun", gate.READINESS_QUERY)
        stderr = io.StringIO()

        def boom(*_args, **_kwargs):
            raise AssertionError("request")

        with redirect_stderr(stderr):
            code = gate.main(
                ["--repo", REPO, "--pr", "7", "--sha", HEAD, "--dry-run"], {}, boom)
        self.assertEqual(code, 2)
        message = stderr.getvalue()
        self.assertIn("GH_TOKEN must be set for reads", message)
        self.assertNotIn("gate account", message)

    def test_rejects_a_key_inside_the_repository_or_a_symlink(self):
        inside = gate.ROOT / ".review-gate-test.pem"
        inside.write_text("x\n", encoding="utf-8")
        self.addCleanup(inside.unlink)
        os.chmod(inside, 0o600)
        self.assertEqual(gate.key_problem(inside, gate.ROOT), "inside repository")
        directory, key = _key()
        self.addCleanup(directory.cleanup)
        link = Path(directory.name) / "link.pem"
        link.symlink_to(key)
        self.assertEqual(gate.key_problem(link, gate.ROOT), "symlink")
        self.assertIsNone(gate.key_problem(key, gate.ROOT))

    def test_jwt_claims_and_openssl_signature(self):
        token = gate.build_jwt(424242, "ignored", 1700000000, sign=lambda data, path: b"\x01\x02")
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload))
        self.assertEqual(claims, {"iat": 1700000000 - 60, "exp": 1700000000 - 60 + 540, "iss": "424242"})
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        key = Path(directory.name) / "app.pem"
        subprocess.run(
            ["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(key)],
            check=True, capture_output=True)
        os.chmod(key, 0o600)
        signed = gate.build_jwt(7, key, 1700000000).encode()
        header, body, signature = signed.split(b".")
        signing = header + b"." + body
        sig = base64.urlsafe_b64decode(signature + b"=" * (-len(signature) % 4))
        pub = Path(directory.name) / "pub.pem"
        subprocess.run(["openssl", "pkey", "-in", str(key), "-pubout", "-out", str(pub)], check=True, capture_output=True)
        sig_path = Path(directory.name) / "sig.bin"
        sig_path.write_bytes(sig)
        data_path = Path(directory.name) / "data.bin"
        data_path.write_bytes(signing)
        verified = subprocess.run(
            ["openssl", "dgst", "-sha256", "-verify", str(pub), "-signature", str(sig_path), str(data_path)],
            check=True, capture_output=True, text=True)
        self.assertIn("Verified OK", verified.stdout)


class MergeTests(unittest.TestCase):
    def env(self, key):
        return {
            "GH_TOKEN": "ghp_mac_read",
            "REVIEW_GATE_APP_ID": "424242",
            "REVIEW_GATE_APP_KEY": str(key),
            "REVIEW_GATE_API": API,
            "PATH": "/usr/bin",
        }

    def hub(self):
        files = [{"filename": "README.md", "patch": "@@\n-a\n+b\n"}]
        found = FakeHub(pull(), files, [])
        found.graphql = [ready_payload()]
        return found

    def invoke(self, hub, key, merge, polls=3, extra=None):
        argv = ["--repo", REPO, "--pr", "7", "--sha", HEAD, "--merge"]
        if extra:
            argv = argv + extra
        sleeps = []
        code = gate.main(
            argv, self.env(key), hub, now=lambda: 1700000000, sign=lambda data, path: b"sig",
            merge=merge, sleep=lambda seconds: sleeps.append(seconds), polls=polls, poll_wait=2,
            who=lambda env, secrets: OWNER)
        return code, sleeps

    def test_merge_posts_success_then_squash_merges_that_sha(self):
        directory, key = _key()
        self.addCleanup(directory.cleanup)
        hub = self.hub()
        calls = []

        def merge(argv, env):
            calls.append((argv, dict(env)))
            hub.pull["state"] = "closed"
            hub.pull["merged"] = True
            return 0, ""

        code, sleeps = self.invoke(hub, key, merge)
        self.assertEqual(code, 0)
        self.assertEqual(sleeps, [])
        self.assertEqual(calls[0][0], [
            "gh", "pr", "merge", "7", "--repo", REPO, "--squash", "--match-head-commit", HEAD])
        self.assertNotIn("--auto", calls[0][0])
        self.assertNotIn("--admin", calls[0][0])
        self.assertNotIn("GH_TOKEN", calls[0][1])
        self.assertNotIn("REVIEW_GATE_APP_KEY", calls[0][1])
        self.assertTrue(all("ghp_mac_read" not in value and "ghs_test_token" not in value
                            and str(key) not in value for value in calls[0][1].values()))
        posts = [item[3] for item in hub.calls if item[0] == "POST" and "/statuses/" in item[1]]
        self.assertEqual([item["state"] for item in posts], ["success"])
        graphql = [item for item in hub.calls if item[1].endswith("/graphql")]
        self.assertIn("isRequired(pullRequestNumber: $number)", graphql[0][3]["query"])
        self.assertEqual(graphql[0][3]["variables"]["number"], 7)
        self.assertNotIn("GH_HOST", calls[0][1])
        self.assertIn(HEAD, posts[0]["description"])
        self.assertLessEqual(len(posts[0]["description"]), 140)
        self.assertNotIn("ghs_test_token", posts[0]["description"])

    def test_plain_dry_run_and_bad_evidence_do_not_post_success_or_merge(self):
        directory, key = _key()
        self.addCleanup(directory.cleanup)
        hub = self.hub()

        def boom(*_args):
            raise AssertionError("merge")

        code = gate.main(
            ["--repo", REPO, "--pr", "7", "--sha", HEAD, "--dry-run"],
            self.env(key), hub, now=lambda: 1700000000, sign=lambda data, path: b"sig", merge=boom)
        self.assertEqual(code, 0)
        self.assertFalse(any("/statuses/" in url or url.endswith("/graphql") for _, url, _, _ in hub.calls))
        hub.pull = pull(body="")
        code, _sleeps = self.invoke(hub, key, boom)
        self.assertEqual(code, 1)
        posts = [item[3]["state"] for item in hub.calls if "/statuses/" in item[1]]
        self.assertEqual(posts, ["failure"])
        broken = self.hub()
        broken.pull = pull(body="Author: Cursor / grok-4.7\nno review section\n")
        code, _sleeps = self.invoke(broken, key, boom)
        self.assertEqual(code, 1)
        self.assertEqual([item[3]["state"] for item in broken.calls if "/statuses/" in item[1]], ["failure"])
        opened = self.hub()
        opened.pull = pull(body=evidence(HEAD, reviewer=""))
        code, _sleeps = self.invoke(opened, key, boom)
        self.assertEqual(code, 1)
        self.assertEqual([item[3]["state"] for item in opened.calls if "/statuses/" in item[1]], ["failure"])

    def test_sha_drift_before_post_does_not_post_and_drift_after_post_clears_success(self):
        directory, key = _key()
        self.addCleanup(directory.cleanup)

        def boom(*_args):
            raise AssertionError("merge")

        early = self.hub()
        early.pull = pull(head=OTHER)
        code, _sleeps = self.invoke(early, key, boom)
        self.assertEqual(code, 1)
        self.assertFalse(any("/statuses/" in url for _, url, _, _ in early.calls))
        late = self.hub()

        def move():
            late.pull["head"]["sha"] = OTHER

        late.on_success = move
        calls = []
        code, _sleeps = self.invoke(late, key, lambda argv, env: calls.append(argv) or (0, ""))
        self.assertEqual(code, 1)
        self.assertEqual(calls, [])
        states = [item[3]["state"] for item in late.calls if "/statuses/" in item[1]]
        self.assertEqual(states, ["success", "failure"])
        self.assertTrue(all(item[1].endswith("/" + HEAD) for item in late.calls if "/statuses/" in item[1]))

    def test_a_semantic_review_change_clears_success_and_a_comment_does_not(self):
        directory, key = _key()
        self.addCleanup(directory.cleanup)
        changed = self.hub()
        original = changed.pull["body"]

        def edit():
            changed.pull["body"] = original.replace("남은 지적: 없음", "남은 지적: P2 하나", 1)

        changed.on_success = edit
        code, _sleeps = self.invoke(changed, key, lambda argv, env: (_ for _ in ()).throw(AssertionError("merge")))
        self.assertEqual(code, 1)
        self.assertEqual([item[3]["state"] for item in changed.calls if "/statuses/" in item[1]], ["success", "failure"])
        commented = self.hub()
        body = commented.pull["body"]

        def decorate():
            commented.pull["body"] = "<!-- coderabbit -->\n" + body

        commented.on_success = decorate
        calls = []

        def merged(argv, env):
            calls.append(argv)
            commented.pull["state"] = "closed"
            commented.pull["merged"] = True
            return 0, ""

        code, _sleeps = self.invoke(commented, key, merged)
        self.assertEqual(code, 0)
        self.assertEqual(len(calls), 1)
        self.assertEqual([item[3]["state"] for item in commented.calls if "/statuses/" in item[1]], ["success"])

    def test_draft_failed_check_thread_and_review_block_before_success(self):
        directory, key = _key()
        self.addCleanup(directory.cleanup)

        def boom(*_args):
            raise AssertionError("merge")

        draft = self.hub()
        draft.pull["draft"] = True
        code, _sleeps = self.invoke(draft, key, boom)
        self.assertEqual(code, 1)
        self.assertFalse(any("/statuses/" in url for _, url, _, _ in draft.calls))
        failed = self.hub()
        failed.graphql = [ready_payload(contexts=[
            check_run("Baseline checks (Python 3.11)", conclusion="FAILURE"),
            check_run("Baseline checks (Python 3.13)"),
        ])]
        code, sleeps = self.invoke(failed, key, boom)
        self.assertEqual(code, 1)
        self.assertEqual(sleeps, [])
        self.assertFalse(any("/statuses/" in url for _, url, _, _ in failed.calls))
        thread = self.hub()
        thread.graphql = [ready_payload(threads=[{"isResolved": False}])]
        self.assertEqual(self.invoke(thread, key, boom)[0], 1)
        self.assertFalse(any("/statuses/" in url for _, url, _, _ in thread.calls))
        review = self.hub()
        review.graphql = [ready_payload(review="CHANGES_REQUESTED")]
        self.assertEqual(self.invoke(review, key, boom)[0], 1)

    def test_pending_checks_wait_boundedly_and_auto_merge_is_refused(self):
        directory, key = _key()
        self.addCleanup(directory.cleanup)
        pending = check_run("Baseline checks (Python 3.11)", conclusion=None, status="IN_PROGRESS")
        other = check_run("Baseline checks (Python 3.13)")
        waiting = self.hub()
        waiting.graphql = [ready_payload(contexts=[pending, other]), ready_payload()]
        calls = []

        def merged(argv, env):
            calls.append(argv)
            waiting.pull["state"] = "closed"
            waiting.pull["merged"] = True
            return 0, ""

        code, sleeps = self.invoke(waiting, key, merged, polls=3)
        self.assertEqual(code, 0)
        self.assertEqual(sleeps, [2])
        self.assertEqual(len(calls), 1)
        stuck = self.hub()
        stuck.graphql = [ready_payload(contexts=[pending, other]), ready_payload(contexts=[pending, other])]
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code, sleeps = self.invoke(stuck, key, lambda argv, env: (_ for _ in ()).throw(AssertionError("merge")), polls=2)
        self.assertEqual(code, 1)
        self.assertEqual(sleeps, [2])
        self.assertIn("Do not arm auto-merge", stderr.getvalue())
        self.assertFalse(any("/statuses/" in url for _, url, _, _ in stuck.calls))
        armed = self.hub()
        armed.pull["auto_merge"] = {"merge_method": "squash"}
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code, _sleeps = self.invoke(armed, key, lambda argv, env: (_ for _ in ()).throw(AssertionError("merge")))
        self.assertEqual(code, 1)
        self.assertIn("--disable-auto", stderr.getvalue())
        self.assertFalse(any("/statuses/" in url for _, url, _, _ in armed.calls))

    def test_merge_refusal_clears_success_and_a_failed_cleanup_stays_visible(self):
        directory, key = _key()
        self.addCleanup(directory.cleanup)
        refused = self.hub()
        code, _sleeps = self.invoke(refused, key, lambda argv, env: (1, "merge refused"))
        self.assertEqual(code, 1)
        self.assertEqual([item[3]["state"] for item in refused.calls if "/statuses/" in item[1]], ["success", "failure"])
        stranded = self.hub()
        stranded.fail_post = "failure"
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code, _sleeps = self.invoke(stranded, key, lambda argv, env: (7, "merge refused ghp_mac_read"))
        self.assertEqual(code, 2)
        text = stderr.getvalue()
        self.assertIn("merge failed: 7", text)
        self.assertIn("cleanup failed", text)
        self.assertNotIn("ghp_mac_read", text)
        states = [item[3]["state"] for item in stranded.calls if "/statuses/" in item[1] and item[3]]
        self.assertEqual(states[0], "success")
        self.assertIn("failure", states)

    def test_catchable_faults_after_success_attempt_clear_it(self):
        directory, key = _key()
        self.addCleanup(directory.cleanup)

        def statuses(hub):
            return [item[3]["state"] for item in hub.calls if "/statuses/" in item[1] and isinstance(item[3], dict)]

        timed = self.hub()
        timed.fail_success_with = TimeoutError("timed out")
        code, _sleeps = self.invoke(timed, key, lambda argv, env: (_ for _ in ()).throw(AssertionError("merge")))
        self.assertEqual(code, 1)
        self.assertEqual(statuses(timed), ["success", "failure"])
        wrong = self.hub()
        wrong.wrong_success = True
        code, _sleeps = self.invoke(wrong, key, lambda argv, env: (_ for _ in ()).throw(AssertionError("merge")))
        self.assertEqual(code, 1)
        self.assertEqual(statuses(wrong), ["success", "failure"])
        listed = self.hub()
        listed.list_success = True
        code, _sleeps = self.invoke(listed, key, lambda argv, env: (_ for _ in ()).throw(AssertionError("merge")))
        self.assertEqual(code, 1)
        self.assertEqual(statuses(listed), ["success", "failure"])
        partial = self.hub()
        partial.after_success = http.client.IncompleteRead(b"")
        code, _sleeps = self.invoke(partial, key, lambda argv, env: (_ for _ in ()).throw(AssertionError("merge")))
        self.assertEqual(code, 1)
        self.assertEqual(statuses(partial), ["success", "failure"])
        broken = self.hub()
        broken.after_success = http.client.BadStatusLine("no status")
        code, _sleeps = self.invoke(broken, key, lambda argv, env: (_ for _ in ()).throw(AssertionError("merge")))
        self.assertEqual(code, 1)
        self.assertEqual(statuses(broken), ["success", "failure"])
        interrupted = self.hub()
        with self.assertRaises(KeyboardInterrupt):
            self.invoke(interrupted, key, lambda argv, env: (_ for _ in ()).throw(KeyboardInterrupt()))
        self.assertEqual(statuses(interrupted), ["success", "failure"])
        stopped = self.hub()

        def stop(argv, env):
            handler = signal.getsignal(signal.SIGTERM)
            self.assertIsInstance(getattr(handler, "__self__", None), gate._SignalGate)
            raise gate.CaughtSignal(signal.SIGTERM)

        with self.assertRaises(gate.CaughtSignal):
            self.invoke(stopped, key, stop)
        self.assertEqual(statuses(stopped), ["success", "failure"])

    def test_merge_result_is_reread_and_one_green_check_is_not_enough(self):
        directory, key = _key()
        self.addCleanup(directory.cleanup)
        still_open = self.hub()
        code, _sleeps = self.invoke(still_open, key, lambda argv, env: (0, ""))
        self.assertEqual(code, 1)
        self.assertEqual(
            [item[3]["state"] for item in still_open.calls if "/statuses/" in item[1]],
            ["success", "failure"])
        merged = self.hub()

        def late(argv, env):
            merged.pull["state"] = "closed"
            merged.pull["merged"] = True
            raise subprocess.TimeoutExpired(argv, 120)

        code, _sleeps = self.invoke(merged, key, late)
        self.assertEqual(code, 0)
        self.assertEqual([item[3]["state"] for item in merged.calls if "/statuses/" in item[1]], ["success"])
        older = self.hub()
        older.graphql = [ready_payload(contexts=[
            check_run("Baseline checks (Python 3.11)", conclusion="FAILURE", when="2026-11-01T00:00:00Z"),
            check_run("Baseline checks (Python 3.11)", when="2026-11-07T00:00:00Z"),
            check_run("Baseline checks (Python 3.13)"),
            check_run("Review status", conclusion="FAILURE", required=False),
        ])]

        def close(argv, env):
            older.pull["state"] = "closed"
            older.pull["merged"] = True
            return 1, "gh exited late"

        self.assertEqual(self.invoke(older, key, close)[0], 0)
        only_one = self.hub()
        only_one.graphql = [ready_payload(contexts=[check_run("Baseline checks (Python 3.11)")])]
        code, _sleeps = self.invoke(only_one, key, lambda argv, env: (_ for _ in ()).throw(AssertionError("merge")))
        self.assertEqual(code, 1)
        self.assertFalse(any("/statuses/" in url for _, url, _, _ in only_one.calls))
        paged = self.hub()
        paged.graphql = [ready_payload(more_checks=True)]
        self.assertEqual(self.invoke(paged, key, lambda argv, env: (_ for _ in ()).throw(AssertionError("merge")))[0], 1)
        foreign = self.hub()
        foreign.graphql = [ready_payload(contexts=[
            check_run("Baseline checks (Python 3.11)", app=1),
            check_run("Baseline checks (Python 3.13)"),
        ])]
        self.assertEqual(self.invoke(foreign, key, lambda argv, env: (_ for _ in ()).throw(AssertionError("merge")))[0], 1)

    def test_subprocess_env_is_an_allowlist_and_redirects_are_refused(self):
        child = gate.merge_child_env({
            "PATH": "/usr/bin", "HOME": "/home/owner", "GH_TOKEN": "ghp_mac_read",
            "GH_HOST": "https://evil.example", "GH_ENTERPRISE_TOKEN": "ghe_secret",
            "REVIEW_GATE_API": "https://evil.example", "REVIEW_GATE_APP_KEY": "/tmp/key",
        }, ["ghp_mac_read"])
        self.assertEqual(child["PATH"], "/usr/bin")
        self.assertEqual(child["HOME"], "/home/owner")
        self.assertEqual(child["GH_PROMPT_DISABLED"], "1")
        self.assertNotIn("GH_TOKEN", child)
        self.assertNotIn("GH_HOST", child)
        self.assertNotIn("GH_ENTERPRISE_TOKEN", child)
        kept = gate.merge_child_env({"PATH": "/usr/bin", "GH_CONFIG_DIR": "/home/owner/.config/gh", "GH_HOST": "https://evil.example"}, [])
        self.assertEqual(kept["GH_CONFIG_DIR"], "/home/owner/.config/gh")
        self.assertNotIn("GH_HOST", kept)
        self.assertNotIn("REVIEW_GATE_API", child)
        self.assertNotIn("REVIEW_GATE_APP_KEY", child)
        opened = gate._allowed_env(
            {"PATH": "/usr/bin", "GH_TOKEN": "ghp_mac_read"}, gate.OPENSSL_ENV_KEYS, ["ghp_mac_read"])
        self.assertEqual(opened, {"PATH": "/usr/bin"})
        self.assertIsNone(gate._NoRedirect().redirect_request(None, None, 302, "found", {}, "https://evil.example"))


class ReadinessTests(unittest.TestCase):
    def test_attempt_order_is_start_time_and_a_tie_does_not_guess_success(self):
        old = check_run("Baseline checks (Python 3.11)", conclusion="SUCCESS", when="2026-11-01T00:00:00Z")
        old["completedAt"] = "2026-11-07T00:00:05Z"
        newer = check_run("Baseline checks (Python 3.11)", conclusion=None, status="IN_PROGRESS", when="2026-11-07T00:00:01Z")
        newer["completedAt"] = None
        self.assertEqual(gate._check_state(gate._latest([old, newer])), "pending")
        self.assertEqual(gate._check_state(gate._latest([newer, old])), "pending")
        success = check_run("Baseline checks (Python 3.11)", conclusion="SUCCESS", when="2026-11-07T00:00:00Z")
        failed = check_run("Baseline checks (Python 3.11)", conclusion="FAILURE", when="2026-11-07T00:00:00Z")
        self.assertIsNone(gate._latest([success, failed]))
        self.assertIsNone(gate._latest([failed, success]))
        self.assertEqual(gate._check_state(gate._latest([success, dict(success)])), "ok")
        with self.assertRaises(ValueError):
            gate.expected_checks({"expected": {"protection": {"required_status_checks": {"checks": [
                {"context": "CI", "app_id": -1},
                {"context": "review/gate", "app_id": 424242},
            ]}}}}, 424242)

    def test_consumer_check_names_come_from_the_default_branch_file(self):
        directory, key = _key()
        self.addCleanup(directory.cleanup)
        consumer = [
            {"context": "mobile tests", "app_id": 15368},
            {"context": "mobile lint", "app_id": 15368},
            {"context": "review/gate", "app_id": 424242},
        ]
        hub = FakeHub(pull(), [{"filename": "README.md"}], [])
        hub.settings_checks = consumer
        hub.graphql = [ready_payload(contexts=[
            check_run("mobile tests"),
            check_run("mobile lint"),
            {"__typename": "StatusContext", "context": "review/gate", "state": "PENDING",
             "isRequired": True, "createdAt": "2026-11-07T00:00:00Z"},
        ])]

        def merge(argv, env):
            self.assertEqual(env.get("GH_CONFIG_DIR"), "/audited/gh")
            self.assertNotIn("GH_HOST", env)
            hub.pull["state"] = "closed"
            hub.pull["merged"] = True
            return 0, ""

        env = {
            "GH_TOKEN": "ghp_mac_read", "REVIEW_GATE_APP_ID": "424242", "REVIEW_GATE_APP_KEY": str(key),
            "REVIEW_GATE_API": API, "PATH": "/usr/bin", "GH_CONFIG_DIR": "/audited/gh",
            "GH_HOST": "https://evil.example",
        }
        code = gate.main(
            ["--repo", REPO, "--pr", "7", "--sha", HEAD, "--merge"], env, hub,
            now=lambda: 1700000000, sign=lambda data, path: b"sig", merge=merge,
            sleep=lambda _seconds: None, who=lambda _env, _secrets: OWNER)
        self.assertEqual(code, 0)
        urls = [url for _, url, _, _ in hub.calls]
        self.assertTrue(any("repository-settings.json?ref=main" in url for url in urls))
        self.assertFalse(any(f"ref={HEAD}" in url for url in urls))
        missing = FakeHub(pull(), [{"filename": "README.md"}], [])
        missing.settings_checks = consumer
        missing.graphql = [ready_payload(contexts=[check_run("mobile tests")])]
        code = gate.main(
            ["--repo", REPO, "--pr", "7", "--sha", HEAD, "--merge"], env, missing,
            now=lambda: 1700000000, sign=lambda data, path: b"sig",
            merge=lambda argv, env: (_ for _ in ()).throw(AssertionError("merge")),
            sleep=lambda _seconds: None, who=lambda _env, _secrets: OWNER)
        self.assertEqual(code, 1)
        self.assertFalse(any("/statuses/" in url for _, url, _, _ in missing.calls))


class SignalCleanupTests(unittest.TestCase):
    def test_a_second_catchable_signal_does_not_abort_the_failure_post(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, _format, *_args):
                return

            def _json(self, payload, code=200):
                raw = json.dumps(payload).encode()
                self.server.codes.append((code, self.path))
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self):
                self.server.seen.append(("GET", self.path))
                if "/contents/" in self.path and "repository-settings.json?ref=main" not in self.path:
                    self.send_error(404)
                    return
                if (self.path.endswith("/pulls/7") and self.server.states and self.server.mode == "reread"
                        and not self.server.signalled):
                    self.server.signalled = True
                    os.kill(self.server.child, signal.SIGTERM)
                self._json(self.server.get(self.path))

            def do_POST(self):
                try:
                    self._post()
                except Exception:
                    import traceback
                    self.server.boom = traceback.format_exc()
                    self.send_error(500)

            def _post(self):
                length = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(length).decode() or "{}")
                self.server.seen.append(("POST", self.path))
                if self.path.endswith("/statuses/" + HEAD):
                    state = body.get("state")
                    self.server.states.append(state)
                    if state == "failure" and self.server.mode == "during-cleanup":
                        os.kill(self.server.child, signal.SIGTERM)
                        time.sleep(0.2)
                    if state == "failure" and self.server.mode == "hold-failure":
                        self.server.holding = True
                        while not self.server.release:
                            time.sleep(0.05)
                    self._json({"context": "review/gate", "state": state}, 201)
                    return
                if self.path.endswith("/access_tokens"):
                    self._json({"token": "ghs_dummy"})
                    return
                if self.path == "/graphql":
                    self._json(ready_payload())
                    return
                self._json({})

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        port = server.server_address[1]
        settings = {"expected": {"protection": {"required_status_checks": {"checks": [
            {"context": "Baseline checks (Python 3.11)", "app_id": 15368},
            {"context": "Baseline checks (Python 3.13)", "app_id": 15368},
            {"context": "review/gate", "app_id": 424242},
        ]}}}}
        encoded = base64.b64encode(json.dumps(settings).encode()).decode()
        pull_body = {
            "state": "open", "merged": False, "draft": False,
            "body": evidence(HEAD), "user": {"login": OWNER},
            "head": {"sha": HEAD}, "base": {"sha": BASE, "ref": "main"}, "commits": 1,
        }

        def get(path):
            if path.endswith("/pulls/7"):
                return pull_body
            if path.endswith("/installation"):
                return {"id": 99}
            if path.endswith("/repo-baseline") and "/repos/" in path and "/contents/" not in path and "/pulls/" not in path:
                return {"default_branch": "main", "owner": {"login": OWNER}}
            if "/compare/" in path:
                if path.endswith("...main"):
                    return {"status": "identical"}
                return {"files": [{"filename": "README.md", "status": "modified"}], "commits": []}
            if "repository-settings.json?ref=main" in path:
                return {"encoding": "base64", "content": encoded}
            if path.endswith("/comments?per_page=100"):
                return []
            if "/statuses" in path:
                return []
            return {}

        server.get = get
        server.states = []
        server.seen = []
        server.codes = []
        server.mode = "double"
        server.child = None
        thread = __import__("threading").Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.shutdown)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        key = Path(directory.name) / "app.pem"
        subprocess.run(
            ["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", str(key)],
            check=True, capture_output=True)
        os.chmod(key, 0o600)
        bindir = tempfile.TemporaryDirectory()
        self.addCleanup(bindir.cleanup)
        gh_path = Path(bindir.name) / "gh"
        gh_path.write_text(
            "#!/bin/sh\n"
            "if [ \"$1\" = api ]; then printf '%s\\n' minjunkim-dev; exit 0; fi\n"
            "mode=$(cat \"$(dirname \"$0\")/mode\")\n"
            "if [ \"$mode\" = fail ]; then exit 1; fi\n"
            "if [ \"$mode\" = ok ]; then exit 0; fi\n"
            "sleep 30\nexit 1\n",
            encoding="utf-8")
        mode_path = Path(bindir.name) / "mode"
        gh_path.chmod(0o755)
        runner = Path(bindir.name) / "run_gate.py"
        runner.write_text(
            "import os, sys\n"
            f"sys.path.insert(0, {str(Path(gate.__file__).parent)!r})\n"
            "import post_review_gate as gate\n"
            "raise SystemExit(gate.main(["
            f"{'--repo'!r}, {REPO!r}, {'--pr'!r}, {'7'!r}, {'--sha'!r}, {HEAD!r}, {'--merge'!r}]))\n",
            encoding="utf-8")
        env = os.environ.copy()
        env.update({
            "GH_TOKEN": "ghp_dummy",
            "REVIEW_GATE_APP_ID": "424242",
            "REVIEW_GATE_APP_KEY": str(key),
            "REVIEW_GATE_API": f"http://127.0.0.1:{port}",
            "PATH": str(bindir.name) + os.pathsep + env.get("PATH", ""),
            "GATE_GH_EXIT": "0",
        })
        env.pop("GH_HOST", None)
        env.pop("GITHUB_ACTIONS", None)
        env.pop("GITHUB_TOKEN", None)

        def launch(mode, gh_exit):
            server.states = []
            server.seen = []
            server.codes = []
            server.signalled = False
            server.mode = mode
            pull_body["state"] = "open"
            pull_body["merged"] = False
            mode_path.write_text(gh_exit, encoding="utf-8")
            child_env = dict(env)
            proc = subprocess.Popen(
                [sys.executable, str(runner)], env=child_env, start_new_session=True,
                stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            server.child = proc.pid
            self.addCleanup(lambda: os.killpg(proc.pid, signal.SIGKILL) if proc.poll() is None else None)
            return proc

        def wait_success():
            for _ in range(80):
                if server.states == ["success"]:
                    return
                time.sleep(0.05)
            out, err = proc.communicate(timeout=2)
            self.fail(err.decode()[-400:] + " CODES " + repr(getattr(server, "codes", [])[-6:]))

        def signal_group(proc, sig):
            """Signal the child's group. macOS can refuse killpg while the leader is alive."""
            if proc.poll() is not None:
                raise AssertionError("process exited before the signal window")
            try:
                os.killpg(proc.pid, sig)
            except ProcessLookupError as error:
                raise AssertionError("process group disappeared during the signal window") from error
            except PermissionError:
                if proc.poll() is not None:
                    raise AssertionError("group signal missed the live window")
                os.kill(proc.pid, sig)
                listed = subprocess.run(
                    ["pgrep", "-g", str(proc.pid)], capture_output=True, text=True)
                for line in listed.stdout.split():
                    child = int(line)
                    if child != proc.pid:
                        try:
                            os.kill(child, sig)
                        except ProcessLookupError:
                            pass

        server.release = False
        server.holding = False
        proc = launch("hold-failure", "sleep")
        wait_success()
        signal_group(proc, signal.SIGINT)
        for _ in range(80):
            if server.holding:
                break
            time.sleep(0.05)
        self.assertTrue(server.holding, server.states)
        signal_group(proc, signal.SIGINT)
        server.release = True
        self.assertNotEqual(proc.wait(timeout=10), 0)
        self.assertEqual(server.states, ["success", "failure"])

        proc = launch("during-cleanup", "fail")
        self.assertNotEqual(proc.wait(timeout=15), 0)
        self.assertEqual(server.states, ["success", "failure"])

        proc = launch("control", "sleep")
        wait_success()
        signal_group(proc, signal.SIGTERM)
        self.assertNotEqual(proc.wait(timeout=15), 0)
        self.assertEqual(server.states, ["success", "failure"])

        real_openssl = subprocess.run(["which", "openssl"], check=True, capture_output=True, text=True).stdout.strip()
        signer = Path(bindir.name) / "openssl"
        signer.write_text(
            "#!" + sys.executable + "\n"
            "import os, sys, time\n"
            "from pathlib import Path\n"
            "here = Path(__file__).resolve().parent\n"
            "real = (here / 'openssl-real').read_text(encoding='utf-8').strip()\n"
            "if (here / 'openssl-hold').exists():\n"
            "    (here / 'openssl-sid').write_text(\n"
            "        str(os.getsid(0)) + '\\n' + str(os.getpid()) + '\\n', encoding='utf-8')\n"
            "    (here / 'openssl-held').touch()\n"
            "    while (here / 'openssl-hold').exists():\n"
            "        time.sleep(0.05)\n"
            "os.execv(real, [real, *sys.argv[1:]])\n",
            encoding="utf-8")
        signer.chmod(0o755)
        (Path(bindir.name) / "openssl-real").write_text(real_openssl + "\n", encoding="utf-8")
        hold = Path(bindir.name) / "openssl-hold"
        held = Path(bindir.name) / "openssl-held"
        sid_path = Path(bindir.name) / "openssl-sid"
        for path in (hold, held, sid_path):
            if path.exists():
                path.unlink()
        proc = launch("plain", "sleep")
        wait_success()
        hold.write_text("1", encoding="utf-8")
        signal_group(proc, signal.SIGINT)
        for _ in range(80):
            if held.exists():
                break
            time.sleep(0.05)
        self.assertTrue(held.exists(), "signer did not reach the cleanup window")
        signer_sid, signer_pid = sid_path.read_text(encoding="utf-8").split()
        self.assertTrue(signer_sid.isdigit() and signer_pid.isdigit())
        self.assertEqual(signer_sid, signer_pid)
        self.assertNotEqual(signer_sid, str(proc.pid))
        signal_group(proc, signal.SIGHUP)
        hold.unlink()
        self.assertNotEqual(proc.wait(timeout=15), 0)
        self.assertEqual(server.states, ["success", "failure"])

    def test_forced_signal_before_cleanup_deferral_still_settles(self):
        directory, key = _key()
        self.addCleanup(directory.cleanup)
        previous = {number: signal.getsignal(number) for number in _SignalGate_numbers()}
        self.addCleanup(lambda: _restore_signal_handlers(previous))

        def scenario(merge, fail_post=None):
            files = [{"filename": "README.md", "patch": "@@\n-a\n+b\n"}]
            hub = FakeHub(pull(), files, [])
            hub.graphql = [ready_payload()]
            hub.fail_post = fail_post
            fired = {"n": 0, "defer_before": None}

            def tracer(frame, event, arg):
                if event != "line" or not frame.f_code.co_filename.endswith("post_review_gate.py"):
                    return tracer
                text = linecache.getline(frame.f_code.co_filename, frame.f_lineno)
                if "signals.defer = True" not in text:
                    return tracer
                signals = frame.f_locals.get("signals")
                if signals is None or signals.defer or fired["n"]:
                    return tracer
                fired["defer_before"] = signals.defer
                fired["n"] = 1
                signal.raise_signal(signal.SIGINT)
                return tracer

            stdout, stderr = io.StringIO(), io.StringIO()
            escaped = None
            sys.settrace(tracer)
            try:
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    try:
                        gate.main(
                            ["--repo", REPO, "--pr", "7", "--sha", HEAD, "--merge"],
                            {"GH_TOKEN": "ghp_mac_read", "REVIEW_GATE_APP_ID": "424242",
                             "REVIEW_GATE_APP_KEY": str(key), "REVIEW_GATE_API": API, "PATH": "/usr/bin"},
                            hub, now=lambda: 1700000000, sign=lambda data, path: b"sig",
                            merge=merge, sleep=lambda _seconds: None, polls=3, poll_wait=0,
                            who=lambda _env, _secrets: OWNER)
                    except gate.CaughtSignal as error:
                        escaped = error.number
            finally:
                sys.settrace(None)
            states = [item[3]["state"] for item in hub.calls
                      if "/statuses/" in item[1] and isinstance(item[3], dict)]
            return fired, escaped, states, stderr.getvalue(), _handler_labels()

        refused, escaped, states, stderr, after = scenario(lambda argv, env: (1, "merge refused"))
        self.assertEqual(refused, {"n": 1, "defer_before": False})
        self.assertEqual(escaped, signal.SIGINT)
        self.assertEqual(states, ["success", "failure"])
        self.assertEqual(after, _handler_labels(previous))
        self.assertNotIn("method:handle", " ".join(after.values()))

        cell = {}

        def merge_marks(argv, env):
            cell["hub"].pull["state"] = "closed"
            cell["hub"].pull["merged"] = True
            return 0, ""

        fired, escaped, states, stderr, after = _run_armed(self, key, merge_marks, cell)
        self.assertEqual(fired["n"], 1)
        self.assertIs(fired["defer_before"], False)
        self.assertEqual(escaped, signal.SIGINT)
        self.assertEqual(states, ["success"])
        self.assertEqual(after, _handler_labels(previous))

        fired, escaped, states, stderr, after = _run_armed(
            self, key, lambda argv, env: (7, "merge refused ghp_mac_read"), {}, fail_post="failure")
        self.assertEqual(fired["n"], 1)
        self.assertEqual(states[0], "success")
        self.assertIn("failure", states)
        self.assertIn("cleanup failed", stderr)
        self.assertNotIn("ghp_mac_read", stderr)
        self.assertEqual(after, _handler_labels(previous))

    def test_signal_at_cleanup_entry_still_settles(self):
        """SIGINT, SIGHUP, SIGTERM, or SIGQUIT before _arm_cleanup's try still posts failure.

        The injection is the call into _arm_cleanup, while deferral is still off.
        That is the prologue before the cleanup try, not the deferral assignment.
        """
        directory, key = _key()
        self.addCleanup(directory.cleanup)
        previous = {number: signal.getsignal(number) for number in _SignalGate_numbers()}
        self.addCleanup(lambda: _restore_signal_handlers(previous))

        for number in _SignalGate_numbers():
            fired, escaped, states, stderr, after = _run_at_entry(
                self, key, lambda argv, env: (1, "merge refused"), {}, number)
            self.assertEqual(fired["n"], 1, number)
            self.assertIs(fired["defer_before"], False)
            self.assertEqual(escaped, number)
            self.assertEqual(states, ["success", "failure"])
            self.assertEqual(after, _handler_labels(previous))
            self.assertNotIn("method:handle", " ".join(after.values()))
            self.assertNotIn("ghp_mac_read", stderr)

        cell = {}

        def merge_marks(argv, env):
            cell["hub"].pull["state"] = "closed"
            cell["hub"].pull["merged"] = True
            return 0, ""

        fired, escaped, states, stderr, after = _run_at_entry(
            self, key, merge_marks, cell, signal.SIGHUP)
        self.assertEqual(fired["n"], 1)
        self.assertIs(fired["defer_before"], False)
        self.assertEqual(escaped, signal.SIGHUP)
        self.assertEqual(states, ["success"])
        self.assertEqual(after, _handler_labels(previous))

        fired, escaped, states, stderr, after = _run_at_entry(
            self, key, lambda argv, env: (7, "merge refused ghp_mac_read"), {},
            signal.SIGQUIT, fail_post="failure")
        self.assertEqual(fired["n"], 1)
        self.assertEqual(states[0], "success")
        self.assertIn("failure", states)
        self.assertEqual(states.count("failure"), 1)
        self.assertIn("cleanup failed", stderr)
        self.assertNotIn("ghp_mac_read", stderr)
        self.assertNotIn("ghs_test_token", stderr)
        self.assertEqual(after, _handler_labels(previous))


def _SignalGate_numbers():
    return (signal.SIGINT, signal.SIGHUP, signal.SIGTERM, signal.SIGQUIT)


def _handler_labels(saved=None):
    labels = {}
    for number in _SignalGate_numbers():
        current = saved[number] if saved is not None else signal.getsignal(number)
        if current == signal.SIG_DFL:
            labels[number] = "SIG_DFL"
        elif current == signal.SIG_IGN:
            labels[number] = "SIG_IGN"
        else:
            labels[number] = type(current).__name__ + ":" + getattr(current, "__name__", "")
    return labels


def _restore_signal_handlers(previous):
    for number, handler in previous.items():
        signal.signal(number, handler)


def _run_armed(case, key, merge, cell, fail_post=None):
    files = [{"filename": "README.md", "patch": "@@\n-a\n+b\n"}]
    hub = FakeHub(pull(), files, [])
    hub.graphql = [ready_payload()]
    hub.fail_post = fail_post
    cell["hub"] = hub
    fired = {"n": 0, "defer_before": None}

    def tracer(frame, event, arg):
        if event != "line" or not frame.f_code.co_filename.endswith("post_review_gate.py"):
            return tracer
        text = linecache.getline(frame.f_code.co_filename, frame.f_lineno)
        if "signals.defer = True" not in text:
            return tracer
        signals = frame.f_locals.get("signals")
        if signals is None or signals.defer or fired["n"]:
            return tracer
        fired["defer_before"] = signals.defer
        fired["n"] = 1
        signal.raise_signal(signal.SIGINT)
        return tracer

    stdout, stderr = io.StringIO(), io.StringIO()
    escaped = None
    sys.settrace(tracer)
    try:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                gate.main(
                    ["--repo", REPO, "--pr", "7", "--sha", HEAD, "--merge"],
                    {"GH_TOKEN": "ghp_mac_read", "REVIEW_GATE_APP_ID": "424242",
                     "REVIEW_GATE_APP_KEY": str(key), "REVIEW_GATE_API": API, "PATH": "/usr/bin"},
                    hub, now=lambda: 1700000000, sign=lambda data, path: b"sig",
                    merge=merge, sleep=lambda _seconds: None, polls=3, poll_wait=0,
                    who=lambda _env, _secrets: OWNER)
            except gate.CaughtSignal as error:
                escaped = error.number
    finally:
        sys.settrace(None)
    states = [item[3]["state"] for item in hub.calls
              if "/statuses/" in item[1] and isinstance(item[3], dict)]
    return fired, escaped, states, stderr.getvalue(), _handler_labels()


def _run_at_entry(case, key, merge, cell, number, fail_post=None):
    """Run --merge and raise `number` on the call into _arm_cleanup, before its try."""
    files = [{"filename": "README.md", "patch": "@@\n-a\n+b\n"}]
    hub = FakeHub(pull(), files, [])
    hub.graphql = [ready_payload()]
    hub.fail_post = fail_post
    cell["hub"] = hub
    fired = {"n": 0, "defer_before": None}

    def tracer(frame, event, arg):
        if event != "call" or frame.f_code.co_name != "_arm_cleanup" or fired["n"]:
            return tracer
        parent = frame.f_back
        signals = parent.f_locals.get("signals") if parent is not None else None
        if signals is None or signals.defer:
            return tracer
        current = signal.getsignal(number)
        if not callable(current):
            raise AssertionError("refusing to raise a signal without the gate handler")
        fired["defer_before"] = signals.defer
        fired["n"] = 1
        signal.raise_signal(number)
        return tracer

    stdout, stderr = io.StringIO(), io.StringIO()
    escaped = None
    sys.settrace(tracer)
    try:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                gate.main(
                    ["--repo", REPO, "--pr", "7", "--sha", HEAD, "--merge"],
                    {"GH_TOKEN": "ghp_mac_read", "REVIEW_GATE_APP_ID": "424242",
                     "REVIEW_GATE_APP_KEY": str(key), "REVIEW_GATE_API": API, "PATH": "/usr/bin"},
                    hub, now=lambda: 1700000000, sign=lambda data, path: b"sig",
                    merge=merge, sleep=lambda _seconds: None, polls=3, poll_wait=0,
                    who=lambda _env, _secrets: OWNER)
            except gate.CaughtSignal as error:
                escaped = error.number
    finally:
        sys.settrace(None)
    states = [item[3]["state"] for item in hub.calls
              if "/statuses/" in item[1] and isinstance(item[3], dict)]
    return fired, escaped, states, stderr.getvalue(), _handler_labels()


if __name__ == "__main__":
    unittest.main()

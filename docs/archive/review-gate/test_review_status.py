"""Review record and owner-approval requirements for a pull request head."""

import base64
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_review_status as tool

HEAD = "a" * 40
INDEPENDENT = "review/independent"
SECURITY = "review/security"


def passing_body(head):
    """Slim PR template with every field filled. The head is not part of the record."""
    return "\n".join([
        "Author: Codex / gpt-5.6", "",
        "## Summary", "why", "",
        "## Review",
        "리뷰어(구현과 다른 컨텍스트, 도구/모델): Claude Code / Opus 5.5",
        "고친 것: 없음",
        "남은 지적: 없음", "",
    ])


def status_rows(pairs, default_creator):
    """One page of GET /commits/{sha}/statuses. The list endpoint includes creator."""
    rows = []
    for index, item in enumerate(pairs):
        creator = default_creator
        if len(item) == 3:
            context, state, creator = item
        else:
            context, state = item
        row = {
            "avatar_url": "https://avatars.githubusercontent.com/u/1",
            "context": context,
            "created_at": f"2020-01-01T00:00:{index:02d}Z",
            "description": "",
            "id": index + 1,
            "node_id": "S",
            "state": state,
            "target_url": None,
            "updated_at": f"2020-01-01T00:00:{index:02d}Z",
            "url": "https://api.github.com/repos/o/n/statuses/1",
        }
        if creator is not None:
            row["creator"] = {"login": creator, "id": 1, "type": "User"}
        rows.append(row)
    return rows


def api(files, statuses=(), author="alice", commits=("alice",), changed=None, verified=True,
        committer="web-flow", commit_shas=None, extra_status=None, commit_count=None,
        owner="owner", comments=(), agents=None, head=HEAD, compare_files=None, compare_commits=None,
        head_agents=None, body=None, number="1", base_ref="main", base_sha="BASE",
        default_branch="main", base_status="identical", status_creator=None, combined=False):
    base = {"sha": base_sha}
    if base_ref is not None:
        base["ref"] = base_ref
    pull = {"user": {"login": author}, "changed_files": len(files) if changed is None else changed,
            "head": {"sha": head}, "base": base,
            "body": passing_body(head) if body is None else body}
    commit_rows = [{
        "author": {"login": name}, "committer": {"login": committer},
        "commit": {"verification": {"verified": verified},
                   "committer": {"date": f"2020-01-{(index + 1):02d}T00:00:00Z"}},
    } for index, name in enumerate(commits)]
    repo = {"owner": {"login": owner}}
    if default_branch is not None:
        repo["default_branch"] = default_branch
    routes = {
        f"repos/o/n/pulls/{number}": pull,
        f"repos/o/n/pulls/{number}/files?per_page=100": [files],
        f"repos/o/n/pulls/{number}/commits?per_page=100": [commit_rows],
        f"repos/o/n/commits/{head}/statuses?per_page=100": (
            [{"state": "success", "statuses": status_rows(statuses, owner if status_creator is None else status_creator),
              "sha": head, "total_count": len(tuple(statuses))}]
            if combined else
            [status_rows(statuses, owner if status_creator is None else status_creator)]),
        "repos/o/n": repo,
        f"repos/o/n/issues/{number}/comments?per_page=100": [list(comments)],
    }
    if agents is not None:
        routes[f"repos/o/n/contents/AGENTS.md?ref={base_sha}"] = {
            "content": base64.b64encode(agents.encode()).decode()}
    if commit_count is not None:
        pull["commits"] = commit_count
    elif commit_shas is not None:
        pull["commits"] = len(commit_shas)
    else:
        pull["commits"] = len(list(commits))
    if commit_shas is not None:
        names = list(commits)
        commit_rows = [{
            "sha": sha, "author": {"login": names[index] if index < len(names) else author},
            "committer": {"login": committer},
            "commit": {"verification": {"verified": verified},
                       "committer": {"date": f"2020-01-{(index + 1):02d}T00:00:00Z"}},
        } for index, sha in enumerate(commit_shas)]
        routes[f"repos/o/n/pulls/{number}/commits?per_page=100"] = [commit_rows]
    pinned = []
    for entry in files if compare_files is None else compare_files:
        entry = dict(entry)
        # Compare always names a status. Fixtures that omit it are ordinary edits.
        # A rename keeps previous_filename and is not rewritten into modified.
        if "status" not in entry and not entry.get("previous_filename"):
            entry["status"] = "modified"
        pinned.append(entry)
    routes[f"repos/o/n/compare/{base_sha}...{head}"] = {
        "files": pinned, "commits": commit_rows if compare_commits is None else compare_commits}
    if default_branch and base_status is not None and f"{base_sha}...{default_branch}" != f"{base_sha}...{head}":
        routes[f"repos/o/n/compare/{base_sha}...{default_branch}"] = {"status": base_status}
    if head_agents is not None:
        routes[f"repos/o/n/contents/AGENTS.md?ref={head}"] = {
            "content": base64.b64encode(head_agents.encode()).decode()}
    if extra_status:
        for sha, pairs in extra_status.items():
            routes[f"repos/o/n/commits/{sha}/statuses?per_page=100"] = [
                status_rows(pairs, owner if status_creator is None else status_creator)]

    def read(endpoint):
        if endpoint not in routes:
            raise subprocess.CalledProcessError(1, "gh", stderr="gh: Not Found (HTTP 404)")
        return routes[endpoint]
    return read


def run(read):
    return tool.missing("o/n", "1", HEAD, "BASE", read)


def comment(body, login="owner", created_at="2020-01-01T00:00:00Z", updated_at=None, omit_times=False,
            last_edited_at=None, omit_edit=False, includes_created_edit=False):
    row = {"user": {"login": login}, "body": body}
    if not omit_times:
        row["created_at"] = created_at
        row["updated_at"] = created_at if updated_at is None else updated_at
    if not omit_edit:
        row["last_edited_at"] = last_edited_at
    if includes_created_edit:
        row["includes_created_edit"] = True
    return row


OK = (INDEPENDENT, "success")
BUMP = ("@@ -1 +1 @@\n-  uses: actions/checkout@" + "a" * 40 + " # v1.0.0\n"
        "+  uses: actions/checkout@" + "b" * 40 + " # v1.1.0")


class ReviewStatusTests(unittest.TestCase):
    def test_advisory_review_statuses_do_not_fail_the_gate(self):
        files = [{"filename": "src/app.py"}]
        self.assertEqual(run(api(files)), [])
        self.assertEqual(run(api(files, [OK])), [])
        self.assertEqual(run(api(files, [(INDEPENDENT, "failure")])), [])
        self.assertEqual(run(api(files, [OK, (SECURITY, "failure")])), [])
        self.assertEqual(run(api(files, [OK, (SECURITY, "success")])), [])
        self.assertEqual(run(api(files, [(INDEPENDENT, "success", "github-actions[bot]")])), [])
        self.assertEqual(run(api(files, [(INDEPENDENT, "success", "alice")])), [])
        team = api(files, [(INDEPENDENT, "success", "github-actions[bot]")], agents="프로필: 팀\n")
        self.assertEqual(run(team), [])
        base = api(files)

        def unreadable(endpoint):
            if "/statuses" in endpoint:
                raise subprocess.CalledProcessError(1, "gh", stderr="HTTP 500")
            return base(endpoint)

        self.assertEqual(run(unreadable), [])
        seen = []

        def watch(endpoint):
            seen.append(endpoint)
            return base(endpoint)

        self.assertEqual(tool.missing("o/n", "1", HEAD, "BASE", watch), [])
        self.assertFalse(any("/statuses" in item for item in seen))

    def test_trust_boundary_paths_do_not_require_a_review_status(self):
        for path in (".github/workflows/ci.yml", ".github/actions/x/action.yml", "scripts/check_review_status.py",
                     ".github/repo-baseline.json", "api/.env.local", "svc/Dockerfile", "web/package-lock.json",
                     ".claude/skills/x/SKILL.md", ".mcp.json", ".github/trust-boundary-paths"):
            with self.subTest(path=path):
                owner = [tool.OWNER] if path in {".github/workflows/ci.yml", "scripts/check_review_status.py"} else []
                self.assertEqual(run(api([{"filename": path}])), owner)
                self.assertEqual(run(api([{"filename": path}], [OK, (SECURITY, "failure")])), owner)
                self.assertNotIn(INDEPENDENT, run(api([{"filename": path}])))
                self.assertNotIn(SECURITY, run(api([{"filename": path}])))

    def test_renaming_a_file_out_of_a_gate_path_still_needs_the_owner_comment(self):
        files = [{"filename": "docs/x.yml", "previous_filename": ".github/workflows/x.yml"}]
        self.assertEqual(run(api(files)), [tool.OWNER])
        self.assertNotIn(SECURITY, run(api(files, [OK])))

    def test_profile_sources_in_repo_baseline_are_gate_paths(self):
        for path in ("profiles/review-gate/check_review_status.py", "profiles/pr-conventions/workflow_policy.py",
                     "profiles/hash-copy/apply_baseline.py", "tools/check_github_settings.py"):
            with self.subTest(path=path):
                self.assertEqual(run(api([{"filename": path}])), [tool.OWNER])

    def test_rooted_patterns_are_read_literally(self):
        for pattern in ("app/[id]/**", "app/[id]/route.ts", "/app/[id]/route.ts"):
            with self.subTest(pattern):
                self.assertTrue(tool.matches("app/[id]/route.ts", (pattern,)))
        self.assertTrue(tool.matches("x/[id].ts", ("[id].ts",)))
        self.assertFalse(tool.matches("src/auth/login.py", ("src/billing/**",)))

    def test_a_capped_compare_needs_the_owner_comment(self):
        read = api([{"filename": "src/app.py"}], compare_files=[{"filename": "src/app.py"}] * 300)
        self.assertEqual(run(read), [tool.OWNER])

    def test_a_bot_login_is_not_owner_evidence(self):
        def read(endpoint):
            if endpoint == "repos/o/n":
                return {"owner": {"login": "github-actions[bot]"}}
            if endpoint.endswith("/comments?per_page=100"):
                return [[comment(f"되돌리기 어려움 승인: {HEAD}", login="github-actions[bot]")]]
            raise AssertionError(endpoint)
        self.assertFalse(tool.owner_approved("o/n", "1", HEAD, read))

    def test_dependabot_follows_the_same_path_evidence_and_owner_rules(self):
        bot = "dependabot[bot]"
        workflow = [{"filename": ".github/workflows/ci.yml", "status": "modified", "patch": BUMP}]
        self.assertEqual(run(api(workflow, [OK], author=bot, commits=[bot])),
                         run(api(workflow, [OK])))
        self.assertEqual(run(api(workflow, author=bot, commits=[bot])), [tool.OWNER])
        self.assertNotIn(INDEPENDENT, run(api(workflow, author=bot, commits=[bot])))
        self.assertNotIn(SECURITY, run(api(workflow, author=bot, commits=[bot])))
        minor = [{"filename": "package.json", "patch": '@@\n-  "x": "^1.2.3",\n+  "x": "^2.0.0",'}]
        self.assertEqual(run(api(minor, [OK], author=bot, commits=[bot])), [])
        self.assertEqual(run(api(minor, [OK], author=bot, commits=[bot])), run(api(minor, [OK])))
        app = [{"filename": "src/app.py"}]
        self.assertEqual(run(api(app, [OK], author=bot)), [])
        self.assertEqual(run(api(app, [OK], body="", author=bot)), [tool.EVIDENCE])
        without_author = "\n".join(passing_body(HEAD).split("\n")[1:])
        self.assertIn("author", tool.evidence_problems(without_author))
        self.assertEqual(run(api(app, [OK], body=without_author, author=bot)), [tool.EVIDENCE])
        approved = comment(f"되돌리기 어려움 승인: {HEAD}")
        covered = [OK, (SECURITY, "success")]
        self.assertEqual(run(api(workflow, covered, author=bot, comments=[approved])), [])

    def test_a_combined_status_payload_is_not_consulted(self):
        files = [{"filename": "src/app.py"}]
        env = {"REPO": "o/n", "PR_NUMBER": "1", "HEAD_SHA": HEAD, "BASE_SHA": "BASE"}
        self.assertEqual(tool.main(env, api(files, [OK], combined=True)), 0)
        self.assertEqual(run(api(files)), [])
        gate = [{"filename": "scripts/check_review_status.py"}]
        bot_security = [OK, (SECURITY, "success", "github-actions[bot]")]
        self.assertEqual(run(api(gate, bot_security)), [tool.OWNER])
        self.assertEqual(run(api(gate, [OK, (SECURITY, "success", "owner")])), [tool.OWNER])

    def test_a_prior_sha_does_not_cover_this_head(self):
        """Success on another SHA is not evidence for this head."""
        files = [{"filename": "src/app.py"}]
        prior = "b" * 40
        base = api(files, commit_shas=[prior, HEAD], extra_status={prior: [OK]})
        seen = []

        def read(endpoint):
            seen.append(endpoint)
            return base(endpoint)

        self.assertEqual(tool.missing("o/n", "1", HEAD, "BASE", read), [])
        self.assertFalse(any(
            f"/commits/{prior}/" in item or "/statuses" in item or "/git/trees/" in item
            or "force-push" in item for item in seen))
        env = {"REPO": "o/n", "PR_NUMBER": "1", "HEAD_SHA": HEAD, "BASE_SHA": "BASE"}
        self.assertEqual(tool.main(env, read), 0)
        on_head = api(files, [OK], commit_shas=[prior, HEAD], extra_status={prior: [OK]})
        self.assertEqual(tool.missing("o/n", "1", HEAD, "BASE", on_head), [])
        failed = api(files, [(INDEPENDENT, "failure")], extra_status={prior: [OK]})
        self.assertEqual(tool.missing("o/n", "1", HEAD, "BASE", failed), [])
        gate = [{"filename": ".github/workflows/ci.yml", "patch": "@@\n-run: a\n+run: b"}]
        old_gate = api(gate, extra_status={prior: [OK, (SECURITY, "success")]})
        self.assertEqual(tool.missing("o/n", "1", HEAD, "BASE", old_gate), [tool.OWNER])

    def test_owner_approval_uses_rest_timestamps_only(self):
        fresh = "2020-01-01T00:00:00Z"
        body = f"되돌리기 어려움 승인: {HEAD}"
        self.assertTrue(tool.comment_unedited(comment(body, created_at=fresh, updated_at=fresh)))
        # GraphQL last_edited_at and includes_created_edit are ignored.
        self.assertTrue(tool.comment_unedited(
            comment(body, last_edited_at=fresh, includes_created_edit=True)))
        self.assertTrue(tool.comment_unedited(comment(body, omit_edit=True)))
        self.assertFalse(tool.comment_unedited(comment(body, updated_at="2020-01-02T00:00:00Z")))
        self.assertFalse(tool.comment_unedited(comment(body, omit_times=True)))
        self.assertFalse(tool.comment_unedited(comment(body, updated_at="2020-01-01T00:00:00+00:00")))
        source = Path(tool.__file__).read_text(encoding="utf-8")
        self.assertNotIn("graphql", source)
        self.assertNotIn("lastEditedAt", source)
        self.assertFalse(hasattr(tool, "approval_comment_pages"))

    def test_owner_comment_matches_only_this_head(self):
        head = "a" * 40
        other = "b" * 40
        files = [{"filename": "templates/review-status.yml"}]
        reviews = [OK, (SECURITY, "success")]

        def check(comments, expected, **kwargs):
            read = api(files, reviews, comments=comments, head=head, **kwargs)
            self.assertEqual(tool.missing("o/n", "1", head, "BASE", read), expected)

        fresh = "2020-01-01T00:00:00Z"
        check([comment(f"한쪽 문 승인: {head} 메모", login="Owner")], [], owner="owner")
        check([comment(f"되돌리기 어려움 승인: {head}", created_at=fresh, updated_at=fresh)], [])
        check([comment(f"한쪽 문 승인: {head}", created_at=fresh, updated_at=fresh)], [])
        check([comment(f"되돌리기 어려움 승인: {head}", updated_at="2020-01-02T00:00:00Z")], [tool.OWNER])
        # GraphQL edit fields are ignored when the REST timestamps match.
        check([comment(f"되돌리기 어려움 승인: {head}", last_edited_at=fresh)], [])
        check([comment(f"한쪽 문 승인: {head}", includes_created_edit=True)], [])
        check([comment(f"되돌리기 어려움 승인: {head}", omit_edit=True)], [])
        check([comment(f"한쪽 문 승인: {head}", updated_at="2020-01-01T00:00:00+00:00")], [tool.OWNER])
        check([comment(f"되돌리기 어려움 승인: {head}", omit_times=True)], [tool.OWNER])
        check([
            comment(f"되돌리기 어려움 승인: {head}", updated_at="2020-01-02T00:00:00Z"),
            comment(f"한쪽 문 승인: {head}"),
        ], [])
        check([comment(f"한쪽 문 승인: {head}\r\n메모")], [])
        check([comment(f"한쪽 문 승인: {other}")], [tool.OWNER])
        check([comment(f"되돌리기 어려움 승인: {head}")], [])
        check([comment(f"되돌리기 어려움 승인: {head} 메모")], [])
        check([comment(f"되돌리기 어려움 승인: {head}\r\n메모")], [])
        check([comment(f"되돌리기 어려움 승인: {other}")], [tool.OWNER])
        check([
            comment(f"되돌리기 어려움 승인: {other}"),
            comment(f"한쪽 문 승인: {other}"),
        ], [tool.OWNER])
        check([
            comment(f"되돌리기 어려움 승인: {other}"),
            comment(f"한쪽 문 승인: {head}"),
        ], [])
        check([
            comment(f"되돌리기 어려움 승인: {head}"),
            comment(f"한쪽 문 승인: {other}"),
        ], [])
        check([comment(f"되돌리기어려움 승인: {head}")], [tool.OWNER])
        check([comment(f"되돌리기 어려움승인: {head}")], [tool.OWNER])
        check([comment(f"되돌리기 쉬움 승인: {head}")], [tool.OWNER])
        check([comment(f" 되돌리기 어려움 승인: {head}")], [tool.OWNER])
        check([comment(f"참고\n되돌리기 어려움 승인: {head}")], [tool.OWNER])
        check([comment(f"한쪽 문승인: {head}")], [tool.OWNER])
        check([comment(f"한쪽 문 승인: {head}", login="alice")], [tool.OWNER])
        check([comment(f"한쪽 문 승인: {head}", login="minjun")], [tool.OWNER], owner="acme-org")
        check([], [tool.OWNER])
        check([comment(f"참고\n한쪽 문 승인: {head}")], [tool.OWNER])
        check([comment("한쪽 문 승인: " + "a" * 39)], [tool.OWNER])
        check([], [tool.OWNER], agents="설명 프로필: 팀\n")
        check([], [], agents="프로필: 팀\n")
        posted = api(files, reviews + [(tool.OWNER, "success")], head=head)
        self.assertEqual(tool.missing("o/n", "1", head, "BASE", posted), [tool.OWNER])
        self.assertEqual(run(api([{"filename": "src/app.py"}], [OK])), [])
        bot = "dependabot[bot]"
        bump = [{"filename": ".github/workflows/ci.yml", "patch": BUMP}]
        self.assertEqual(run(api(bump, author=bot, commits=[bot])), [tool.OWNER])
        self.assertEqual(run(api([{"filename": "scripts/check_repo_baseline.py"}], [OK, (SECURITY, "success")])), [])
        self.assertEqual(run(api([{"filename": "AGENTS.md", "patch": "@@\n+프로필: 팀\n"}], [OK])), [tool.OWNER])
        self.assertEqual(run(api([{"filename": "AGENTS.md", "patch": "@@\n+다른 줄\n"}], [OK])), [])
        self.assertEqual(run(api([{"filename": "AGENTS.md"}], [OK])), [tool.OWNER])
        self.assertEqual(run(api([{"filename": "AGENTS.md", "patch": "@@\n-프로필: 팀\n"}], [OK], agents="프로필: 팀\n")), [])
        renamed = [{"filename": "AGENTS.md", "previous_filename": "notes.md", "patch": "@@\n 프로필 안내\n+다른 줄\n"}]
        self.assertEqual(run(api(renamed, [OK], head_agents="프로필: 팀\n")), [tool.OWNER])

    def test_owner_approval_uses_the_compare_for_this_head(self):
        head = "d" * 40
        reviews = [OK, (SECURITY, "success")]
        swapped = api([{"filename": "src/app.py"}], reviews, head=head,
                      compare_files=[{"filename": ".github/workflows/ci.yml"}])
        self.assertEqual(tool.missing("o/n", "1", head, "BASE", swapped), [tool.OWNER])
        current = api([{"filename": ".github/workflows/ci.yml"}], reviews, head=head,
                      compare_files=[{"filename": "src/app.py"}])
        self.assertEqual(tool.missing("o/n", "1", head, "BASE", current), [])
        huge = api([{"filename": "src/app.py"}], [OK], compare_files=[{"filename": "src/app.py"}] * 300)
        self.assertEqual(run(huge), [tool.OWNER])
        base = api([{"filename": "src/app.py"}], [OK])

        def too_big(endpoint):
            # The ancestry compare must stay readable. Only the pull-request diff is too large.
            if "/compare/" in endpoint and not endpoint.endswith("...main"):
                raise subprocess.CalledProcessError(1, "gh", stderr="HTTP 406")
            return base(endpoint)
        self.assertEqual(run(too_big), [tool.OWNER])

    def test_a_new_head_invalidates_the_owner_comment(self):
        files = [{"filename": "scripts/check_review_status.py"}]
        old = "b" * 40
        read = api(files, commit_shas=[old, HEAD], extra_status={old: [OK, (SECURITY, "success")]},
                   comments=[comment(f"한쪽 문 승인: {old}")])
        self.assertEqual(tool.missing("o/n", "1", HEAD, "BASE", read), [tool.OWNER])
        read_new = api(files, commit_shas=[old, HEAD], extra_status={old: [OK, (SECURITY, "success")]},
                       comments=[comment(f"되돌리기 어려움 승인: {old}")])
        self.assertEqual(tool.missing("o/n", "1", HEAD, "BASE", read_new), [tool.OWNER])
        matched = "c" * 40
        passed = api(files, [OK, (SECURITY, "success")], comments=[comment(f"한쪽 문 승인: {matched}")], head=matched)
        self.assertEqual(tool.missing("o/n", "1", matched, "BASE", passed), [])

    def test_unreadable_approval_comments_do_not_pass(self):
        files = [{"filename": "templates/review-status-policy.json"}]
        base = api(files, [OK, (SECURITY, "success")])

        def read(endpoint):
            if endpoint.endswith("/comments?per_page=100"):
                raise subprocess.CalledProcessError(1, "gh", stderr="HTTP 500")
            return base(endpoint)
        env = {"REPO": "o/n", "PR_NUMBER": "1", "HEAD_SHA": HEAD, "BASE_SHA": "BASE"}
        self.assertEqual(tool.main(env, read), 2)

        def broken_profile(endpoint):
            if endpoint.endswith("/contents/AGENTS.md?ref=BASE"):
                raise subprocess.CalledProcessError(1, "gh", stderr="HTTP 500")
            return base(endpoint)
        self.assertEqual(tool.main(env, broken_profile), 2)

    def test_a_comment_event_without_shas_reads_the_pull_request(self):
        env = {"REPO": "o/n", "PR_NUMBER": "1"}
        self.assertEqual(tool.main(env, api([{"filename": "src/app.py"}], [OK])), 0)

    def test_review_requirements_follow_this_head_not_the_live_pull_request(self):
        head = "e" * 40
        live_docs = api([{"filename": "src/app.py"}], [OK], head=head,
                        compare_files=[{"filename": ".github/workflows/ci.yml"}])
        self.assertEqual(tool.missing("o/n", "1", head, "BASE", live_docs), [tool.OWNER])
        live_workflow = api([{"filename": ".github/workflows/ci.yml"}], [OK], head=head,
                            compare_files=[{"filename": "src/app.py"}])
        self.assertEqual(tool.missing("o/n", "1", head, "BASE", live_workflow), [])

    def test_a_prior_failure_does_not_change_this_head(self):
        files = [{"filename": "src/app.py"}]
        read = api(files, [OK], extra_status={"FAILED": [(INDEPENDENT, "failure")]})
        self.assertEqual(tool.missing("o/n", "1", HEAD, "BASE", read), [])
        missing_here = api(files, extra_status={"OLDER": [OK]})
        self.assertEqual(tool.missing("o/n", "1", HEAD, "BASE", missing_here), [])

    def test_a_newer_failure_on_this_head_does_not_hide_the_evidence(self):
        files = [{"filename": "src/app.py"}]
        self.assertEqual(run(api(files, [(INDEPENDENT, "failure"), OK])), [])

    def test_review_record_needs_the_author_line_and_the_three_review_fields(self):
        files = [{"filename": "src/app.py"}]
        body = passing_body(HEAD)
        self.assertEqual(run(api(files, [OK])), [])
        self.assertEqual(run(api(files, [OK], body="")), [tool.EVIDENCE])
        self.assertEqual(run(api(files, [OK], body="", author="dependabot[bot]")), [tool.EVIDENCE])
        shell = "Author: Cursor / grok-4.7\n$(touch /tmp/review-evidence-executed)\n"
        self.assertIn("review", tool.evidence_problems(shell))
        self.assertFalse(Path("/tmp/review-evidence-executed").exists())
        self.assertEqual([], tool.evidence_problems(body))
        # Any tool and any model pass. The reviewer's model family is not compared with the author's.
        for author in ("Codex / gpt-5.6", "ChatGPT / codex-2", "Claude Code / Opus 5.5", "사람 / 없음"):
            with self.subTest(author=author):
                self.assertEqual([], tool.evidence_problems(body.replace("Codex / gpt-5.6", author)))
        same = body.replace("Codex / gpt-5.6", "Claude Code / Opus 5.5")
        self.assertEqual([], tool.evidence_problems(same))
        self.assertIn("author-model", tool.evidence_problems(body.replace("Codex / gpt-5.6", "사람 / grok-4.7")))
        self.assertIn("author", tool.evidence_problems(body.replace("Author: Codex / gpt-5.6\n", "")))
        self.assertIn("author", tool.evidence_problems("Author: Cursor / grok-4.7\n" + body))
        unfilled = body.replace("Author: Codex / gpt-5.6", "Author: <도구> / <모델>   (사람이면 `사람 / 없음`)")
        self.assertIn("author", tool.evidence_problems(unfilled))
        # A plain label and a label with a hint both count. A value may continue on the next lines.
        plain = body.replace("리뷰어(구현과 다른 컨텍스트, 도구/모델):", "리뷰어:")
        self.assertEqual([], tool.evidence_problems(plain))
        wrapped = body.replace("고친 것: 없음", "고친 것:\n- off-by-one in parse")
        self.assertEqual([], tool.evidence_problems(wrapped))
        self.assertEqual([], tool.evidence_problems(body.replace("남은 지적: 없음", "남은 지적: P2 하나, 다음 PR")))
        self.assertIn("reviewer", tool.evidence_problems(body.replace(": Claude Code / Opus 5.5", ":")))
        self.assertIn("reviewer", tool.evidence_problems(body.replace(": Claude Code / Opus 5.5", ": 미실행")))
        self.assertIn("fixed", tool.evidence_problems(body.replace("고친 것: 없음\n", "")))
        self.assertIn("remaining", tool.evidence_problems(body.replace("남은 지적: 없음", "남은 지적:")))
        self.assertIn("duplicate", tool.evidence_problems(body + "리뷰어: other\n"))
        self.assertIn("review", tool.evidence_problems(body.replace("## Review", "## Notes")))
        # The last ## Review section counts. A field after the next header is not in it.
        stale = body.replace("## Review", "## Review\n리뷰어: old\n고친 것: x\n남은 지적: x\n\n## Review", 1)
        self.assertEqual([], tool.evidence_problems(stale))
        outside = body.replace("남은 지적: 없음", "## Other\n남은 지적: 없음")
        self.assertIn("remaining", tool.evidence_problems(outside))
        hidden = "<!--\n" + body + "-->\n"
        self.assertIn("review", tool.evidence_problems(hidden))
        self.assertIn("author", tool.evidence_problems(hidden))
        self.assertEqual(["comment"], tool.evidence_problems("<!--\n" + body))
        self.assertEqual(["body"], tool.evidence_problems(None))

    def test_trust_boundary_paths_need_no_extra_review_evidence(self):
        for path in (".github/actions/x/action.yml", "web/package.json", ".mcp.json", "svc/Dockerfile"):
            with self.subTest(path=path):
                self.assertEqual(run(api([{"filename": path}])), [])
        capped = api([{"filename": "src/app.py"}], compare_files=[{"filename": "src/app.py"}] * 300)
        self.assertEqual(run(capped), [tool.OWNER])
        base = api([{"filename": "src/app.py"}])

        def too_big(endpoint):
            if "/compare/" in endpoint and not endpoint.endswith("...main"):
                raise subprocess.CalledProcessError(1, "gh", stderr="HTTP 406")
            return base(endpoint)

        self.assertEqual(run(too_big), [tool.OWNER])

    def test_a_side_base_fails_and_a_main_base_still_passes(self):
        files = [{"filename": "src/app.py"}]
        output = StringIO()
        with redirect_stdout(output):
            side = run(api(files, [OK], base_ref="feature"))
        self.assertEqual(side, [tool.BASE_REF])
        text = output.getvalue()
        self.assertIn("base feature is not the default branch main", text)
        self.assertEqual(run(api(files, [OK], base_ref="main")), [])
        env = {"REPO": "o/n", "PR_NUMBER": "1", "HEAD_SHA": HEAD, "BASE_SHA": "BASE"}
        cli = StringIO()
        with redirect_stdout(cli):
            code = tool.main(env, api(files, [OK], base_ref="feature"))
        self.assertEqual(code, 1)
        self.assertIn("review status FAIL", cli.getvalue())
        self.assertIn("base is not the repository default branch", cli.getvalue())
        for kwargs in ({"base_ref": None}, {"default_branch": None}, {"base_ref": ""}, {"default_branch": ""}):
            with self.subTest(**kwargs):
                self.assertEqual(tool.main(env, api(files, [OK], **kwargs)), 2)

    def test_same_head_side_pull_request_is_not_evidence_for_main(self):
        head = "c" * 40
        gate = [{"filename": ".github/workflows/ci.yml"}]
        passed = [OK, (SECURITY, "success")]
        main_read = api(gate, passed, head=head, number="4", base_ref="main", base_sha="MAIN")
        # An empty diff against the side base would pass the owner check. It must not.
        side_read = api([], passed, head=head, number="5", base_ref="wip", base_sha="SIDE")

        def both(endpoint):
            if "pulls?" in endpoint or "head=" in endpoint:
                raise AssertionError(endpoint)
            error = None
            for read in (main_read, side_read):
                try:
                    return read(endpoint)
                except subprocess.CalledProcessError as found:
                    error = found
            raise error

        self.assertEqual(tool.missing("o/n", "4", head, "MAIN", both), [tool.OWNER])
        output = StringIO()
        with redirect_stdout(output):
            side = tool.missing("o/n", "5", head, "SIDE", both)
        self.assertEqual(side, [tool.BASE_REF])
        self.assertIn("base wip is not the default branch main", output.getvalue())
        self.assertNotIn(tool.OWNER, side)

    def test_a_retargeted_run_does_not_pass_on_the_old_side_base_sha(self):
        head = "c" * 40
        passed = [OK, (SECURITY, "success")]
        # The live pull request targets main. A rerun of the old run still sends BASE_SHA=SIDE.
        both = api([], passed, head=head, number="4", base_ref="main", base_sha="SIDE", base_status="behind")
        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(tool.missing("o/n", "4", head, "SIDE", both), [tool.BASE_REF])
        self.assertIn("event base SIDE is not on the default branch main (behind)", output.getvalue())
        diverged = api([], passed, head=head, number="4", base_ref="main", base_sha="SIDE", base_status="diverged")
        self.assertEqual(tool.missing("o/n", "4", head, "SIDE", diverged), [tool.BASE_REF])
        ahead = api([{"filename": "src/app.py"}], [OK], head=head, base_sha="OLD", base_status="ahead")
        self.assertEqual(tool.missing("o/n", "1", head, "OLD", ahead), [])
        gate = api([{"filename": ".github/workflows/ci.yml"}], [OK, (SECURITY, "success")],
                   head=head, base_sha="OLD", base_status="identical")
        self.assertEqual(tool.missing("o/n", "1", head, "OLD", gate), [tool.OWNER])
        env = {"REPO": "o/n", "PR_NUMBER": "4", "HEAD_SHA": head, "BASE_SHA": "SIDE"}
        unreadable = api([], passed, head=head, number="4", base_ref="main", base_sha="SIDE", base_status=None)
        self.assertEqual(tool.main(env, unreadable), 2)
        unknown = api([], passed, head=head, number="4", base_ref="main", base_sha="SIDE", base_status="unknown")
        self.assertEqual(tool.main(env, unknown), 2)

    def test_cli_exit_codes(self):
        env = {"REPO": "o/n", "PR_NUMBER": "1", "HEAD_SHA": HEAD, "BASE_SHA": "BASE"}
        self.assertEqual(tool.main(env, api([{"filename": "a"}])), 0)
        self.assertEqual(tool.main(env, api([{"filename": "a"}], body="")), 1)
        self.assertEqual(tool.main(env, api([{"filename": "scripts/check_review_status.py"}])), 1)

        def broken(endpoint):
            raise subprocess.CalledProcessError(1, "gh", stderr="HTTP 403")
        self.assertEqual(tool.main(env, broken), 2)
        self.assertEqual(tool.main({}, api([])), 2)


if __name__ == "__main__":
    unittest.main()

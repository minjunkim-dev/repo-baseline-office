"""Plan and apply GitHub settings against a fake server, then audit with the project checker."""

import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "scripts"))
import apply_github_settings as tool  # noqa: E402
import check_github_settings as checker  # noqa: E402
from test_github_settings import BASELINE  # noqa: E402

PREFIX = f"repos/{BASELINE['repository']}"
PROTECTION = "branches/main/protection"


def http_error(path, status):
    return subprocess.CalledProcessError(1, ["gh", "api", path], stderr=f"gh: error (HTTP {status})")


class FakeGitHub:
    """Stores settings in GET shape and applies writes the way GitHub reports them back."""

    def __init__(self, profile=BASELINE, fresh=False):
        expected = copy.deepcopy(profile["expected"])
        self.metadata = {"id": profile["repository_id"], "full_name": profile["repository"], **expected["repository"]}
        self.state = {tool.endpoint(name, profile["default_branch"]): value
                      for name, value in expected.items() if name not in ("repository", "dependabot_alerts")}
        self.state[PROTECTION] = self.protection_view(self.state[PROTECTION])
        self.alerts = expected["dependabot_alerts"]["enabled"]
        self.codeql_pending = 0  # reads that still report the old state after a PATCH
        self.codeql_missing = 0  # reads after writes that answer 404
        self.writes, self.fail_on = [], None
        if fresh:  # what a new repository answers before any setup
            self.metadata.update(allow_merge_commit=True, allow_rebase_merge=True, allow_auto_merge=False,
                                 delete_branch_on_merge=False, allow_update_branch=False,
                                 squash_merge_commit_title="COMMIT_OR_PR_TITLE",
                                 squash_merge_commit_message="COMMIT_MESSAGES")
            self.metadata["security_and_analysis"] = {
                key: {"status": "disabled"} for key in self.metadata["security_and_analysis"]}
            self.alerts = False
            self.state.update({
                PROTECTION: None,
                "actions/permissions": {"enabled": True, "allowed_actions": "all", "sha_pinning_required": False},
                "actions/permissions/workflow": {"default_workflow_permissions": "write",
                                                 "can_approve_pull_request_reviews": True},
                "actions/permissions/fork-pr-contributor-approval": {"approval_policy": "first_time_contributors"},
                "immutable-releases": {"enabled": False, "enforced_by_owner": False},
                "code-scanning/default-setup": {"state": "not-configured"},
            })

    @staticmethod
    def protection_view(expected):
        view = copy.deepcopy(expected)
        view.update({key: {"enabled": False} for key in tool.UNMANAGED_PROTECTION})
        view["restrictions"] = None
        return view

    def read(self, path):
        rel = path.removeprefix(PREFIX).lstrip("/")
        if rel == "":
            return copy.deepcopy(self.metadata)
        if rel == "vulnerability-alerts":
            if self.alerts:
                return None
            raise http_error(path, 404)
        if rel == "actions/permissions/selected-actions" and self.state["actions/permissions"]["allowed_actions"] != "selected":
            raise http_error(path, 409)
        if rel == "code-scanning/default-setup" and self.codeql_missing and self.writes:
            self.codeql_missing -= 1
            raise http_error(path, 404)
        if rel == "code-scanning/default-setup" and self.codeql_pending:
            self.codeql_pending -= 1
            return {"state": "not-configured"}
        if self.state.get(rel) is None:
            raise http_error(path, 404)
        return copy.deepcopy(self.state[rel])

    def write(self, method, path, body):
        rel = path.removeprefix(PREFIX).lstrip("/")
        if rel == self.fail_on:
            raise http_error(path, 403)
        self.writes.append((method, rel))
        on = method == "PUT"
        if rel == "":
            body = copy.deepcopy(body)
            security = body.pop("security_and_analysis", {})
            self.metadata.update(body)
            self.metadata["security_and_analysis"].update(security)
        elif rel == "automated-security-fixes":
            self.metadata["security_and_analysis"]["dependabot_security_updates"] = {
                "status": "enabled" if on else "disabled"}
        elif rel == "vulnerability-alerts":
            self.alerts = on
        elif rel == "immutable-releases":
            self.state[rel] = {"enabled": on, "enforced_by_owner": False}
        elif rel == "code-scanning/default-setup":
            self.state[rel] = {"state": body["state"], "languages": ["python"]}
        elif rel == PROTECTION:
            self.state[rel] = self.protection_view({
                "required_status_checks": dict(body["required_status_checks"]),
                "enforce_admins": {"enabled": body["enforce_admins"]},
                "required_pull_request_reviews": dict(body["required_pull_request_reviews"]),
                **{flag: {"enabled": body[flag]} for flag in tool.PROTECTION_FLAGS},
            })
        else:
            self.state[rel] = copy.deepcopy(body)


class ApplyGitHubSettingsTests(unittest.TestCase):
    def project(self, profile=BASELINE):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        (Path(folder.name) / ".github").mkdir()
        (Path(folder.name) / tool.PROFILE).write_text(json.dumps(profile))
        return folder.name

    def run_tool(self, server, profile=BASELINE, apply=False):
        stdout, stderr = io.StringIO(), io.StringIO()
        argv = ["tool", self.project(profile)] + (["--apply"] if apply else [])
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = tool.main(argv, read=server.read, write=server.write, sleep=lambda seconds: None)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_matching_settings_need_no_writes(self):
        server = FakeGitHub()
        code, out, _ = self.run_tool(server, apply=True)
        self.assertEqual((code, server.writes), (0, []))
        self.assertIn("PASS:", out)

    def test_plan_shows_current_and_baseline_values_and_only_reads(self):
        server = FakeGitHub(fresh=True)
        commands = []
        def gh(command, **kwargs):
            commands.append(command)
            try:
                data = server.read(command[4])
            except subprocess.CalledProcessError as error:
                if kwargs.get("check"):
                    raise
                return subprocess.CompletedProcess(command, 1, "", error.stderr)
            return subprocess.CompletedProcess(command, 0, "" if data is None else json.dumps(data), "")
        stdout = io.StringIO()
        with patch.object(subprocess, "run", gh), redirect_stdout(stdout):
            code = tool.main(["tool", self.project()])
        out = stdout.getvalue()
        self.assertEqual(code, 1)
        self.assertEqual({command[3] for command in commands}, {"GET"})
        self.assertIn('DIFF: repository.allow_merge_commit: true -> false', out)
        self.assertIn('DIFF: protection.enforce_admins.enabled: "<not set>" -> true', out)
        self.assertIn("PLAN: PUT repos/owner/repo/branches/main/protection", out)

    def test_protection_request_body(self):
        expected = copy.deepcopy(BASELINE["expected"]["protection"])
        expected["required_pull_request_reviews"]["dismissal_restrictions"] = {"users": [{"login": "lead"}]}
        [(method, path, body)] = tool.writes_for("protection", expected, PREFIX, "main")
        self.assertEqual((method, path), ("PUT", f"{PREFIX}/{PROTECTION}"))
        self.assertEqual(body, {
            "required_status_checks": {"strict": True, "checks": [{"context": "CI", "app_id": 15368}]},
            "enforce_admins": True,
            "required_pull_request_reviews": {"required_approving_review_count": 0, "dismiss_stale_reviews": True,
                                              "require_code_owner_reviews": False, "require_last_push_approval": False},
            "restrictions": None, "required_linear_history": True, "allow_force_pushes": False,
            "allow_deletions": False, "required_conversation_resolution": True, "lock_branch": False,
        })

    def test_fresh_repository_reaches_baseline_and_audit_passes(self):
        server = FakeGitHub(fresh=True)
        server.codeql_pending = 3  # default setup turns on in the background
        server.codeql_missing = 1  # and may briefly answer 404 first
        code, out, err = self.run_tool(server, apply=True)
        self.assertEqual(code, 0, out + err)
        self.assertIn("PASS:", out)
        self.assertEqual(checker.audit(BASELINE, server.read), [])
        order = [rel for _, rel in server.writes]
        self.assertLess(order.index("vulnerability-alerts"), order.index("automated-security-fixes"))
        self.assertLess(order.index("actions/permissions"), order.index("actions/permissions/selected-actions"))
        self.assertEqual(tool.plan(BASELINE, server.read), ([], []))  # a second run changes nothing

    def test_switching_features_off_uses_delete(self):
        profile = copy.deepcopy(BASELINE)
        profile["expected"]["immutable_releases"]["enabled"] = False
        profile["expected"]["repository"]["security_and_analysis"]["dependabot_security_updates"]["status"] = "disabled"
        server = FakeGitHub()
        self.assertEqual(self.run_tool(server, profile, apply=True)[0], 0)
        self.assertEqual(sorted(server.writes), sorted([
            ("PATCH", ""), ("DELETE", "automated-security-fixes"),
            ("DELETE", "immutable-releases")]))

    def test_visibility_and_rulesets_are_left_to_a_person(self):
        server = FakeGitHub()
        server.metadata["visibility"] = "public"
        server.state["rulesets"] = [{"id": 1, "name": "team rule"}]
        code, out, _ = self.run_tool(server, apply=True)
        self.assertEqual((code, server.writes), (1, []))
        self.assertIn("MANUAL: repository.visibility", out)
        self.assertIn("MANUAL: rulesets", out)

    def test_protection_with_unmanaged_settings_is_left_to_a_person(self):
        server = FakeGitHub()
        server.state[PROTECTION]["required_signatures"] = {"enabled": True}
        server.state[PROTECTION]["required_status_checks"]["checks"] = [{"context": "old", "app_id": 15368}]
        code, out, _ = self.run_tool(server, apply=True)
        self.assertEqual(code, 1)
        self.assertNotIn(("PUT", PROTECTION), server.writes)
        self.assertIn("MANUAL: protection.required_signatures is set", out)

    def test_review_bypass_and_dismissal_lists_are_left_to_a_person(self):
        for key, value in (("bypass_pull_request_allowances", {"users": [{"login": "bot"}], "teams": [], "apps": []}),
                           ("dismissal_restrictions", {"users": [{"login": "lead"}], "teams": []})):
            with self.subTest(key):
                server = FakeGitHub()
                server.state[PROTECTION]["required_pull_request_reviews"][key] = value
                server.state[PROTECTION]["required_linear_history"] = {"enabled": False}
                code, out, _ = self.run_tool(server, apply=True)
                self.assertNotIn(("PUT", PROTECTION), server.writes)
                self.assertIn(f"MANUAL: protection.required_pull_request_reviews.{key} is set", out)

    def test_unaudited_fields_are_reported_when_the_control_is_not_set_yet(self):
        profile = copy.deepcopy(BASELINE)
        profile["expected"]["protection"]["required_pull_request_reviews"]["dismissal_restrictions"] = {"users": []}
        server = FakeGitHub(fresh=True)
        code, out, _ = self.run_tool(server, profile)
        self.assertIn("MANUAL: protection.required_pull_request_reviews.dismissal_restrictions", out)
        self.assertIn('DIFF: protection.required_linear_history.enabled: "<not set>" -> true', out)
        self.assertIn("PLAN: PUT repos/owner/repo/branches/main/protection", out)

    def test_advanced_codeql_keeps_default_setup_until_the_workflow_is_active(self):
        profile = copy.deepcopy(BASELINE)
        workflow = ".github/workflows/codeql.yml"
        profile["expected"]["codeql"] = {"state": "not-configured"}
        profile["expected"]["codeql_workflow"] = {"path": workflow, "state": "active"}
        profile["expected"]["codeql_main_source"] = {"path": workflow, "type": "file", "sha": "0" * 40}
        server = FakeGitHub()
        server.state["code-scanning/default-setup"] = {"state": "configured"}
        code, out, _ = self.run_tool(server, profile, apply=True)
        self.assertNotEqual(code, 0)  # the audit cannot verify a workflow that does not exist yet
        self.assertNotIn(("PATCH", "code-scanning/default-setup"), server.writes)
        self.assertIn("MANUAL: codeql.state: default setup stays on", out)
        server.state["actions/workflows/codeql.yml"] = {"path": workflow, "state": "active"}
        self.run_tool(server, profile, apply=True)  # active, but main does not hold the pinned file yet
        self.assertNotIn(("PATCH", "code-scanning/default-setup"), server.writes)
        server.state[tool.endpoint("codeql_main_source", "main")] = {"path": workflow, "type": "file", "sha": "0" * 40}
        disabled = copy.deepcopy(profile)  # a baseline that records a disabled workflow must not turn scanning off
        disabled["expected"]["codeql_workflow"]["state"] = "disabled_manually"
        server.state["actions/workflows/codeql.yml"]["state"] = "disabled_manually"
        self.run_tool(server, disabled, apply=True)
        self.assertNotIn(("PATCH", "code-scanning/default-setup"), server.writes)
        server.state["actions/workflows/codeql.yml"]["state"] = "active"
        self.run_tool(server, profile, apply=True)
        self.assertIn(("PATCH", "code-scanning/default-setup"), server.writes)

    def test_fields_the_auditor_does_not_require_are_not_written(self):
        profile = copy.deepcopy(BASELINE)
        profile["expected"]["repository"]["has_wiki"] = False
        profile["expected"]["workflow_token"]["extra"] = True
        server = FakeGitHub()
        server.metadata["has_wiki"] = True
        server.state["actions/permissions/workflow"]["default_workflow_permissions"] = "write"
        code, out, _ = self.run_tool(server, profile, apply=True)
        self.assertIn("MANUAL: repository.has_wiki differs", out)
        self.assertNotIn(("PATCH", ""), server.writes)
        self.assertEqual(server.state["actions/permissions/workflow"],
                         {"default_workflow_permissions": "read", "can_approve_pull_request_reviews": False})

    def test_a_write_with_unknown_outcome_is_reported(self):
        server = FakeGitHub(fresh=True)
        def timeout(method, path, body):
            raise subprocess.TimeoutExpired(["gh"], 60, stderr=b"timed out")
        server.write = timeout
        code, _, err = self.run_tool(server, apply=True)
        self.assertEqual(code, 2)
        self.assertIn("FAILED: timed out", err)
        self.assertIn("Outcome unknown: PUT repos/owner/repo/vulnerability-alerts", err)

    def test_bad_profiles_and_read_errors_write_nothing(self):
        cases = {
            "identity": lambda p: p.update(repository_id=99),
            "schema": lambda p: p.update(schema_version=99),
            "branch path": lambda p: p.update(default_branch="x/../../other/repo/branches/main"),
            "branch pair": lambda p: p.update(default_branch="dev"),
            "placeholder": lambda p: p["expected"]["protection"]["required_status_checks"]["checks"][0].update(
                context="REPLACE: a required CI job name"),
        }
        for name, change in cases.items():
            with self.subTest(name):
                profile = copy.deepcopy(BASELINE)
                change(profile)
                server = FakeGitHub(fresh=True)
                code, _, err = self.run_tool(server, profile, apply=True)
                self.assertEqual((code, server.writes), (2, []), err)
        server = FakeGitHub(fresh=True)
        server.metadata["default_branch"] = "trunk"
        self.assertEqual(self.run_tool(server, apply=True)[0], 2)
        server = FakeGitHub(fresh=True)
        allowed = server.read
        def forbidden(path):
            if path.endswith("actions/permissions"):
                raise http_error(path, 403)
            return allowed(path)
        server.read = forbidden
        self.assertEqual(self.run_tool(server, apply=True)[0], 2)
        self.assertEqual(server.writes, [])

    def test_failed_write_stops_and_lists_what_was_written(self):
        server = FakeGitHub(fresh=True)
        server.fail_on = PROTECTION
        code, _, err = self.run_tool(server, apply=True)
        self.assertEqual(code, 2)
        self.assertIn("Already written: PUT repos/owner/repo/vulnerability-alerts", err)
        self.assertNotIn("actions/permissions", [rel for _, rel in server.writes])

    def test_declared_exceptions_are_never_written(self):
        profile = copy.deepcopy(BASELINE)
        del profile["expected"]["immutable_releases"]
        del profile["expected"]["repository"]["security_and_analysis"]["secret_scanning"]["status"]
        del profile["expected"]["repository"]["security_and_analysis"]["dependabot_security_updates"]["status"]
        evidence = {"status": "unsupported", "reason": "test", "evidence": "test"}
        profile["exceptions"] = {path: evidence for path in (
            "immutable_releases", "repository.security_and_analysis.secret_scanning.status",
            "repository.security_and_analysis.dependabot_security_updates.status")}
        server = FakeGitHub(fresh=True)
        code, out, err = self.run_tool(server, profile, apply=True)
        self.assertEqual(code, 0, out + err)
        self.assertIn("LIMITED:", out)
        self.assertIn("SKIPPED: immutable_releases", out)
        written = [rel for _, rel in server.writes]
        self.assertNotIn("immutable-releases", written)
        self.assertNotIn("automated-security-fixes", written)
        self.assertEqual(server.metadata["security_and_analysis"]["secret_scanning"], {"status": "disabled"})

    def test_reads_the_same_paths_as_the_checker(self):
        server, paths = FakeGitHub(), {"checker": set(), "tool": set()}
        def recorder(key):
            def read(path):
                paths[key].add(path)
                return server.read(path)
            return read
        checker.audit(BASELINE, recorder("checker"))
        tool.plan(BASELINE, recorder("tool"))
        self.assertEqual(paths["tool"], paths["checker"])

    def test_profile_must_be_a_regular_file_in_the_project(self):
        project = Path(self.project())
        outside = project.parent / f"{project.name}-outside.json"
        outside.write_text(json.dumps(BASELINE))
        self.addCleanup(outside.unlink)
        (project / tool.PROFILE).unlink()
        (project / tool.PROFILE).symlink_to(outside)
        with self.assertRaises(ValueError):
            tool.load(project)

    def test_template_and_own_profiles_share_the_policy_values(self):
        template = json.loads((ROOT / "templates/repository-settings.json").read_text(encoding="utf-8"))
        project = Path(self.project(template))
        with self.assertRaisesRegex(ValueError, "REPLACE|template"):
            tool.load(project)
        own = json.loads((ROOT / ".github/repository-settings.json").read_text(encoding="utf-8"))
        checker.validate_profile(own)
        for profile in (template, own):  # identity, verified checks and third-party actions are per project
            del profile["expected"]["repository"]["visibility"]
            del profile["expected"]["protection"]["required_status_checks"]["checks"]
            del profile["expected"]["allowed_actions"]["patterns_allowed"]
        self.assertEqual(template["expected"], own["expected"])


if __name__ == "__main__":
    unittest.main()

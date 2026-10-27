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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "scripts"))
import apply_github_settings as tool  # noqa: E402
import check_github_settings as checker  # noqa: E402
from test_github_settings import BASELINE  # noqa: E402

PREFIX = f"repos/{BASELINE['repository']}"


def missing(path):
    return subprocess.CalledProcessError(1, ["gh", "api", path], stderr="gh: Not Found (HTTP 404)")


class FakeGitHub:
    """Stores settings in GET shape and applies writes the way GitHub reports them back."""

    def __init__(self, profile, fresh=False):
        expected = copy.deepcopy(profile["expected"])
        self.metadata = {"id": profile["repository_id"], "full_name": profile["repository"], **expected["repository"]}
        self.state = {tool.endpoint(name, profile["default_branch"]): value
                      for name, value in expected.items() if name not in ("repository", "dependabot_alerts")}
        self.alerts = expected["dependabot_alerts"]["enabled"]
        self.writes = []
        if fresh:  # what a new repository answers before any setup
            self.metadata.update(allow_merge_commit=True, allow_rebase_merge=True, allow_auto_merge=False,
                                 delete_branch_on_merge=False, allow_update_branch=False,
                                 squash_merge_commit_title="COMMIT_OR_PR_TITLE",
                                 squash_merge_commit_message="COMMIT_MESSAGES")
            self.metadata["security_and_analysis"] = {
                key: {"status": "disabled"} for key in self.metadata["security_and_analysis"]}
            self.alerts = False
            self.state.update({
                "branches/main/protection": None,
                "actions/permissions": {"enabled": True, "allowed_actions": "all", "sha_pinning_required": False},
                "actions/permissions/selected-actions": None,
                "actions/permissions/workflow": {"default_workflow_permissions": "write",
                                                 "can_approve_pull_request_reviews": True},
                "actions/permissions/fork-pr-contributor-approval": {"approval_policy": "first_time_contributors"},
                "immutable-releases": {"enabled": False, "enforced_by_owner": False},
                "code-scanning/default-setup": {"state": "not-configured"},
            })

    def read(self, path):
        rel = path.removeprefix(PREFIX).lstrip("/")
        if rel == "":
            return copy.deepcopy(self.metadata)
        if rel == "vulnerability-alerts":
            if self.alerts:
                return None
            raise missing(path)
        if self.state.get(rel) is None:
            raise missing(path)
        return copy.deepcopy(self.state[rel])

    def write(self, method, path, body):
        rel = path.removeprefix(PREFIX).lstrip("/")
        self.writes.append((method, rel))
        on = method == "PUT"
        if rel == "":
            security = body.pop("security_and_analysis", {})
            self.metadata.update(body)
            self.metadata["security_and_analysis"].update(copy.deepcopy(security))
        elif rel == "automated-security-fixes":
            self.metadata["security_and_analysis"]["dependabot_security_updates"] = {
                "status": "enabled" if on else "disabled"}
        elif rel == "vulnerability-alerts":
            self.alerts = on
        elif rel == "immutable-releases":
            self.state[rel] = {"enabled": on, "enforced_by_owner": False}
        elif rel == "code-scanning/default-setup":
            self.state[rel] = {"state": body["state"], "languages": ["python"]}
        elif rel.endswith("/protection"):
            self.assertion_restrictions = body["restrictions"]
            self.state[rel] = {
                "url": "https://api.github.invalid",
                "required_status_checks": {**body["required_status_checks"], "contexts": [
                    check["context"] for check in body["required_status_checks"]["checks"]]},
                "enforce_admins": {"enabled": body["enforce_admins"]},
                "required_pull_request_reviews": dict(body["required_pull_request_reviews"]),
                **{flag: {"enabled": body[flag]} for flag in tool.PROTECTION_FLAGS},
            }
        else:
            self.state[rel] = copy.deepcopy(body)


def run(argv, server):
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = tool.main(argv, read=server.read, write=server.write)
    return code, stdout.getvalue(), stderr.getvalue()


class ApplyGitHubSettingsTests(unittest.TestCase):
    def project(self, profile):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        (Path(folder.name) / ".github").mkdir()
        (Path(folder.name) / tool.PROFILE).write_text(json.dumps(profile))
        return folder.name

    def test_matching_settings_need_no_writes(self):
        server = FakeGitHub(BASELINE)
        code, out, _ = run(["tool", self.project(BASELINE)], server)
        self.assertEqual((code, server.writes), (0, []))
        self.assertIn("No writes needed", out)

    def test_plan_never_writes(self):
        server = FakeGitHub(BASELINE, fresh=True)
        code, out, _ = run(["tool", self.project(BASELINE)], server)
        self.assertEqual((code, server.writes), (1, []))
        self.assertIn("PLAN: PUT repos/owner/repo/branches/main/protection", out)

    def test_fresh_repository_reaches_baseline_and_audit_passes(self):
        server = FakeGitHub(BASELINE, fresh=True)
        code, out, err = run(["tool", self.project(BASELINE), "--apply"], server)
        self.assertEqual(code, 0, out + err)
        self.assertIn("PASS:", out)
        self.assertEqual(checker.audit(BASELINE, server.read), [])
        self.assertIsNone(server.assertion_restrictions)
        order = [rel for _, rel in server.writes]
        self.assertLess(order.index("vulnerability-alerts"), order.index("automated-security-fixes"))
        self.assertLess(order.index("actions/permissions"), order.index("actions/permissions/selected-actions"))
        self.assertEqual(tool.plan(BASELINE, server.read), ([], []))  # a second run changes nothing

    def test_visibility_default_branch_and_rulesets_are_left_to_a_person(self):
        server = FakeGitHub(BASELINE)
        server.metadata["visibility"] = "public"
        server.state["rulesets"] = [{"id": 1, "name": "team rule"}]
        code, out, _ = run(["tool", self.project(BASELINE), "--apply"], server)
        self.assertEqual((code, server.writes), (1, []))
        self.assertIn("MANUAL: repository.visibility", out)
        self.assertIn("MANUAL: rulesets", out)

    def test_identity_mismatch_and_read_errors_write_nothing(self):
        other = copy.deepcopy(BASELINE)
        other["repository_id"] = 99
        server = FakeGitHub(BASELINE, fresh=True)
        self.assertEqual(run(["tool", self.project(other), "--apply"], server)[0], 2)
        allowed = server.read
        def forbidden(path):
            if path.endswith("actions/permissions"):
                raise subprocess.CalledProcessError(1, ["gh"], stderr="gh: Forbidden (HTTP 403)")
            return allowed(path)
        server.read = forbidden
        self.assertEqual(run(["tool", self.project(BASELINE), "--apply"], server)[0], 2)
        self.assertEqual(server.writes, [])

    def test_declared_exceptions_are_never_written(self):
        profile = copy.deepcopy(BASELINE)
        del profile["expected"]["immutable_releases"]
        profile["exceptions"] = {"immutable_releases": {
            "status": "unsupported", "reason": "test", "evidence": "test"}}
        server = FakeGitHub(BASELINE, fresh=True)
        code, out, _ = run(["tool", self.project(profile), "--apply"], server)
        self.assertNotIn(("PUT", "immutable-releases"), server.writes)
        self.assertIn("SKIPPED: immutable_releases", out)

    def test_reads_the_same_paths_as_the_checker(self):
        for fresh in (False, True):
            server, paths = FakeGitHub(BASELINE, fresh), {"checker": set(), "tool": set()}
            def recorder(key):
                def read(path):
                    paths[key].add(path)
                    return server.read(path)
                return read
            try:
                checker.audit(BASELINE, recorder("checker"))
            except subprocess.CalledProcessError:
                continue  # the checker stops at the first missing control; compare the settled case
            tool.plan(BASELINE, recorder("tool"))
            self.assertEqual(paths["tool"], paths["checker"])

    def test_template_and_own_profiles_share_the_policy_values(self):
        template = json.loads((ROOT / "templates/repository-settings.json").read_text(encoding="utf-8"))
        with self.assertRaises(ValueError):  # unusable until the project fills in its identity
            checker.validate_profile(template)
        own = json.loads((ROOT / ".github/repository-settings.json").read_text(encoding="utf-8"))
        checker.validate_profile(own)
        for profile in (template, own):  # identity and verified checks are per project
            del profile["expected"]["repository"]["visibility"]
            del profile["expected"]["protection"]["required_status_checks"]["checks"]
        self.assertEqual(template["expected"], own["expected"])


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Plan or apply a project's GitHub settings baseline.

Usage: tools/apply_github_settings.py <project> [--apply]

Reads <project>/.github/repository-settings.json, the baseline that the project's
read-only scripts/check_github_settings.py audits. Without --apply it only reads
settings and prints the writes that would make them match. With --apply it makes
those writes, then audits again. It never changes visibility, the default branch,
rulesets or workflow files; those differences are printed for a person to handle.
Controls listed under "exceptions" are not in "expected", so they are never written.
"""

import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "scripts"))
import check_github_settings as checker  # noqa: E402

PROFILE = ".github/repository-settings.json"
# Write order matters: security updates need alerts on; selected actions need allowed_actions=selected.
ORDER = ("dependabot_alerts", "repository", "protection", "actions", "allowed_actions",
         "workflow_token", "fork_policy", "immutable_releases", "codeql")
MANUAL = ("rulesets", "codeql_workflow", "codeql_main_source")
MERGE_FIELDS = ("allow_merge_commit", "allow_rebase_merge", "allow_squash_merge", "allow_auto_merge",
                "delete_branch_on_merge", "allow_update_branch",
                "squash_merge_commit_title", "squash_merge_commit_message")
PROTECTION_FLAGS = ("required_linear_history", "allow_force_pushes", "allow_deletions",
                    "required_conversation_resolution", "lock_branch")


def endpoint(name, branch):
    """The same read path the checker uses for each control."""
    return {
        "dependabot_alerts": "vulnerability-alerts",
        "protection": f"branches/{branch}/protection",
        "rulesets": "rulesets",
        "actions": "actions/permissions",
        "allowed_actions": "actions/permissions/selected-actions",
        "workflow_token": "actions/permissions/workflow",
        "fork_policy": "actions/permissions/fork-pr-contributor-approval",
        "immutable_releases": "immutable-releases",
        "codeql": "code-scanning/default-setup",
        "codeql_workflow": "actions/workflows/codeql.yml",
        "codeql_main_source": f"contents/.github/workflows/codeql.yml?ref={branch}",
    }[name]


def writes_for(name, expected, prefix, branch):
    """GitHub write requests that turn the expected GET shape into server state."""
    toggle = lambda on: "PUT" if on else "DELETE"  # noqa: E731
    if name == "repository":
        body = {field: expected[field] for field in MERGE_FIELDS if field in expected}
        security = expected.get("security_and_analysis", {})
        secret = {key: security[key] for key in ("secret_scanning", "secret_scanning_push_protection") if key in security}
        if secret:
            body["security_and_analysis"] = secret
        result = [("PATCH", prefix, body)]
        if "dependabot_security_updates" in security:
            on = security["dependabot_security_updates"]["status"] == "enabled"
            result.append((toggle(on), f"{prefix}/automated-security-fixes", None))
        return result
    if name == "protection":
        body = {
            "required_status_checks": {key: expected["required_status_checks"][key] for key in ("strict", "checks")},
            "enforce_admins": expected["enforce_admins"]["enabled"],
            "required_pull_request_reviews": expected["required_pull_request_reviews"],
            "restrictions": None,
            **{flag: expected[flag]["enabled"] for flag in PROTECTION_FLAGS},
        }
        return [("PUT", f"{prefix}/{endpoint(name, branch)}", body)]
    if name in ("dependabot_alerts", "immutable_releases"):
        return [(toggle(expected["enabled"]), f"{prefix}/{endpoint(name, branch)}", None)]
    if name == "codeql":
        return [("PATCH", f"{prefix}/{endpoint(name, branch)}", {"state": expected["state"]})]
    return [("PUT", f"{prefix}/{endpoint(name, branch)}", expected)]


def plan(profile, read=None):
    """Return (writes, manual): requests for controls that differ, and differences left to a person."""
    read = checker.read_api if read is None else read
    checker.validate_profile(profile)
    repo, branch = profile["repository"], profile["default_branch"]
    prefix = f"repos/{repo}"
    metadata = read(prefix)
    if not isinstance(metadata, dict) or metadata.get("id") != profile["repository_id"] or metadata.get("full_name") != repo:
        raise ValueError("Repository identity mismatch")
    writes, manual = [], []
    expected = profile["expected"]
    for name in ORDER + MANUAL:
        if name not in expected:
            continue
        if name == "repository":
            actual = metadata
        else:
            try:
                actual, found = read(f"{prefix}/{endpoint(name, branch)}"), True
            except subprocess.CalledProcessError as error:
                # Only "not set up yet" (an unprotected branch, alerts off) becomes a write; other errors stop.
                if "HTTP 404" not in (error.stderr or ""):
                    raise
                actual, found = None, False
            if name == "dependabot_alerts":
                actual = {"enabled": found}  # 204 with no body when on, 404 when off
        drift = checker.differences(expected[name], actual, name)
        if not drift:
            continue
        if name in MANUAL:
            manual.extend(drift)
            continue
        if name == "repository":
            fixed = [path for path in drift if path in ("repository.default_branch", "repository.visibility")]
            manual.extend(fixed)
            if len(fixed) == len(drift):
                continue
        writes.extend(writes_for(name, expected[name], prefix, branch))
    return writes, manual


def write_api(method, path, body):
    command = ["gh", "api", "--method", method, path, "--silent"]
    if body is not None:
        command += ["--input", "-"]
    subprocess.run(command, input=None if body is None else json.dumps(body), text=True,
                   capture_output=True, check=True, timeout=60)


def main(argv, read=None, write=write_api):
    if len(argv) not in (2, 3) or (len(argv) == 3 and argv[2] != "--apply"):
        print(__doc__, file=sys.stderr)
        return 2
    apply = len(argv) == 3
    try:
        profile = json.loads((Path(argv[1]) / PROFILE).read_text(encoding="utf-8"))
        writes, manual = plan(profile, read)
        for method, path, body in writes:
            print(f"{'APPLY' if apply else 'PLAN'}: {method} {path}" + ("" if body is None else " " + json.dumps(body, sort_keys=True)))
            if apply:
                write(method, path, body)
        for path in manual:
            print(f"MANUAL: {path} differs; this tool does not change it")
        for path in sorted(profile.get("exceptions", {})):
            print(f"SKIPPED: {path} is a declared exception")
        if not apply:
            print("No writes needed" if not writes else "Plan only; nothing written. Rerun with --apply after review.")
            return 1 if writes or manual else 0
        drift = checker.audit(profile, read)
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or "").strip().splitlines()
        print(f"FAILED: {' '.join(map(str, error.cmd[:5]))}: {detail[-1] if detail else error}", file=sys.stderr)
        return 2
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as error:
        print(f"FAILED: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    print("DRIFT after apply: " + ", ".join(drift) if drift else f"PASS: {profile['repository']} settings match baseline")
    return 1 if drift or manual else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

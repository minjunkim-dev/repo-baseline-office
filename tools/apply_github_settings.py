#!/usr/bin/env python3
"""Plan or apply a project's GitHub settings baseline.

Usage: tools/apply_github_settings.py <project> [--apply]

Reads <project>/.github/repository-settings.json, the baseline that the project's
read-only scripts/check_github_settings.py audits. Without --apply it only reads:
for each control that differs it prints every differing value (current -> baseline)
and the write that would fix it. --apply plans again, makes those writes, then
audits. A control is written whole, so one differing field resends its other
baseline fields too. A failed write stops the run; rerun the plan to see where
the repository stands.

It never changes visibility, rulesets, workflow files, or branch protection that
carries settings the baseline does not manage (signed commits, push restrictions,
blocked creations, fork syncing); those are printed as MANUAL. Declared exceptions
are never written. Unfilled template values ("REPLACE...") stop it before any read.
"""

import json
from pathlib import Path
import subprocess
import sys
import time

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
# A protection PUT resets these, and the baseline does not record them, so they must be off.
UNMANAGED_PROTECTION = ("required_signatures", "block_creations", "allow_fork_syncing")
CODEQL_WAIT = 120  # seconds; default setup turns on in the background


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


def placeholders(value, path=""):
    if isinstance(value, dict):
        return [found for key, item in value.items() for found in placeholders(item, f"{path}.{key}" if path else key)]
    if isinstance(value, list):
        return [found for item in value for found in placeholders(item, path)]
    return [path] if isinstance(value, str) and value.startswith("REPLACE") else []


def load(project):
    """The project's baseline, refused before any request if it is unfilled or inconsistent."""
    path = project / PROFILE
    if path.is_symlink() or not path.is_file() or project.resolve() not in path.resolve().parents:
        raise ValueError(f"{PROFILE} must be a regular file inside the project")
    profile = json.loads(path.read_text(encoding="utf-8"))
    unfilled = placeholders(profile)
    if unfilled:
        raise ValueError("Fill in the template values first: " + ", ".join(unfilled))
    checker.validate_profile(profile)
    checker.validate_target(profile)
    if profile["expected"]["repository"]["default_branch"] != profile["default_branch"]:
        raise ValueError("default_branch must equal expected.repository.default_branch")
    return profile


def get(read, path):
    """GET a setting; (None, False) when GitHub answers 404 (not set up yet). Other errors stop the run."""
    try:
        return read(path), True
    except subprocess.CalledProcessError as error:
        if "HTTP 404" not in (error.stderr or ""):
            raise
        return None, False


def value_at(data, path):
    if data is None:
        return "<not set>"
    for part in path.split(".")[1:]:
        if not isinstance(data, dict) or part not in data:
            return "<missing>"
        data = data[part]
    return data


def writes_for(name, expected, prefix, branch):
    """GitHub write requests that turn the expected GET shape into server state."""
    toggle = lambda on: "PUT" if on else "DELETE"  # noqa: E731
    if name == "repository":
        body = {field: expected[field] for field in MERGE_FIELDS if field in expected}
        security = expected.get("security_and_analysis", {})
        # A nested exception leaves {} without "status"; send only the features the baseline sets.
        secret = {key: security[key] for key in ("secret_scanning", "secret_scanning_push_protection")
                  if "status" in security.get(key, {})}
        if secret:
            body["security_and_analysis"] = secret
        result = [("PATCH", prefix, body)]
        if "status" in security.get("dependabot_security_updates", {}):
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
    """Return (changes, manual). changes: per control, the differing (path, current, baseline)
    values and the requests that fix them. manual: differences this tool leaves to a person."""
    read = checker.read_api if read is None else read
    repo, branch = profile["repository"], profile["default_branch"]
    prefix = f"repos/{repo}"
    metadata = read(prefix)
    if not isinstance(metadata, dict) or metadata.get("id") != profile["repository_id"] or metadata.get("full_name") != repo:
        raise ValueError("Repository identity mismatch")
    if metadata.get("default_branch") != branch:
        raise ValueError("The repository's default branch is not the baseline branch")
    changes, manual, current = [], [], {}
    expected = profile["expected"]
    for name in ORDER + MANUAL:
        if name not in expected:
            continue
        if name == "repository":
            actual = metadata
        elif name == "allowed_actions" and "actions" in current and current["actions"].get("allowed_actions") != "selected":
            actual = None  # GitHub lists selected actions only under a "selected" policy; the actions write comes first
        else:
            actual, found = get(read, f"{prefix}/{endpoint(name, branch)}")
            if name == "dependabot_alerts":
                actual = {"enabled": found}  # 204 with no body when on, 404 when off
        current[name] = actual if isinstance(actual, dict) else {}
        drift = checker.differences(expected[name], actual, name)
        if not drift:
            continue
        if name in MANUAL:
            manual.extend(f"{path} differs; this tool does not change it" for path in drift)
            continue
        if name == "repository" and "repository.visibility" in drift:
            manual.append("repository.visibility differs; this tool does not change it")
            drift.remove("repository.visibility")
            if not drift:
                continue
        if name == "protection" and actual is not None:
            kept = [key for key in UNMANAGED_PROTECTION if (actual.get(key) or {}).get("enabled")]
            kept += ["restrictions"] if actual.get("restrictions") else []
            if kept:
                manual.extend(f"protection.{key} is on; writing protection would reset it" for key in kept)
                continue
        shown = [(path, value_at(actual, path), value_at(expected[name], path)) for path in drift]
        changes.append((shown, writes_for(name, expected[name], prefix, branch)))
    return changes, manual


def write_api(method, path, body):
    command = ["gh", "api", "--method", method, path, "--silent"]
    if body is not None:
        command += ["--input", "-"]
    subprocess.run(command, input=None if body is None else json.dumps(body), text=True,
                   capture_output=True, check=True, timeout=60)


def wait_for_codeql(profile, read, sleep, step=5):
    path = f"repos/{profile['repository']}/{endpoint('codeql', profile['default_branch'])}"
    for _ in range(CODEQL_WAIT // step):
        if (read(path) or {}).get("state") == profile["expected"]["codeql"]["state"]:
            return
        sleep(step)


def main(argv, read=None, write=write_api, sleep=time.sleep):
    if len(argv) not in (2, 3) or (len(argv) == 3 and argv[2] != "--apply"):
        print(__doc__, file=sys.stderr)
        return 2
    apply = len(argv) == 3
    read = checker.read_api if read is None else read
    done = []
    try:
        profile = load(Path(argv[1]))
        changes, manual = plan(profile, read)
        for shown, requests in changes:
            for path, before, after in shown:
                print(f"DIFF: {path}: {json.dumps(before, sort_keys=True)} -> {json.dumps(after, sort_keys=True)}")
            for method, path, body in requests:
                print(f"{'APPLY' if apply else 'PLAN'}: {method} {path}" + ("" if body is None else " " + json.dumps(body, sort_keys=True)))
                if apply:
                    write(method, path, body)
                    done.append(f"{method} {path}")
        for line in manual:
            print(f"MANUAL: {line}")
        for path in sorted(profile.get("exceptions", {})):
            print(f"SKIPPED: {path} is a declared exception")
        if not apply:
            print("No writes needed" if not changes else "Plan only; nothing written. Review it, then rerun with --apply.")
            return 1 if changes or manual else 0
        if any(path.endswith("code-scanning/default-setup") for path in done):
            wait_for_codeql(profile, read, sleep)
        drift = checker.audit(profile, read)
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as error:
        stderr = getattr(error, "stderr", None)
        detail = stderr.strip().splitlines()[-1] if stderr and stderr.strip() else f"{type(error).__name__}: {error}"
        print(f"FAILED: {detail}", file=sys.stderr)
        if done:
            print("Already written: " + ", ".join(done) + ". Run the plan again before retrying.", file=sys.stderr)
        return 2
    if drift:
        print("DRIFT after apply: " + ", ".join(drift))
    elif profile.get("exceptions"):
        print(f"LIMITED: {profile['repository']} checked settings match; declared exceptions were not verified")
    else:
        print(f"PASS: {profile['repository']} settings match baseline")
    return 1 if drift or manual else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

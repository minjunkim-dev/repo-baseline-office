"""Validate a real clean source snapshot and copied tests in disposable projects."""

import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from test_github_settings import BASELINE, advanced


class DistributionTests(unittest.TestCase):
    def run_command(self, *args, cwd, expected=0):
        result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result.stdout

    def test_own_dependabot_config_matches_the_template(self):
        own = (ROOT / ".github/dependabot.yml").read_text(encoding="utf-8").splitlines()
        template = (ROOT / "templates/dependabot.yml").read_text(encoding="utf-8").splitlines()
        self.assertEqual(own[1:], template[1:])

    def test_fresh_install_copied_tests_provenance_drift_and_repair(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source"
            source.mkdir()
            # Snapshot the working copy, including new files, without modifying the real Git index.
            paths = self.run_command("git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", cwd=ROOT)
            for name in set(paths.split("\0")) - {""}:
                path = ROOT / name
                if path.is_file():
                    target = source / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, target)
            self.run_command("git", "init", "--quiet", cwd=source)
            self.run_command("git", "add", ".", cwd=source)
            self.run_command("git", "-c", "user.name=Baseline test", "-c", "user.email=test@example.invalid",
                             "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
                             "commit", "--quiet", "-m", "Fixture snapshot", cwd=source)
            head = self.run_command("git", "rev-parse", "HEAD", cwd=source).strip()
            for mode in ("default", "advanced", "unsupported"):
                with self.subTest(mode=mode):
                    project = root / mode
                    (project / ".github").mkdir(parents=True)
                    shutil.copyfile(source / "templates/repo-baseline.json", project / ".github/repo-baseline.json")
                    apply = (sys.executable, str(source / "tools/apply_baseline.py"), str(project))
                    self.run_command(*apply, cwd=source)
                    manifest = json.loads((project / ".github/repo-baseline.json").read_text())
                    self.assertEqual(manifest["source_commit"], head)
                    profile = copy.deepcopy(BASELINE)
                    if mode == "advanced":
                        profile = advanced(profile)
                        workflow = project / profile["expected"]["codeql_main_source"]["path"]
                        workflow.parent.mkdir(parents=True)
                        data = ("steps:\n  - uses: github/codeql-action/analyze@" + "a" * 40 + "\n").encode()
                        workflow.write_bytes(data)
                        profile["expected"]["codeql_main_source"]["sha"] = hashlib.sha1(
                            b"blob %d\0" % len(data) + data).hexdigest()
                    elif mode == "unsupported":
                        del profile["expected"]["codeql"]
                        del profile["expected"]["protection"]
                        profile["exceptions"] = {name: {
                            "status": "unsupported", "reason": "Synthetic unavailable feature",
                            "evidence": "Offline distribution test fixture",
                        } for name in ("codeql", "protection")}
                    (project / ".github/repository-settings.json").write_text(json.dumps(profile))
                    self.run_command(sys.executable, "-m", "unittest", "discover", "-s", "scripts", "-p", "test_*.py", cwd=project)
                    checker = project / "scripts/check_repo_baseline.py"
                    self.run_command(sys.executable, str(checker), cwd=project)
                    self.run_command(*apply, "--check", cwd=source)
                    checker.write_text(checker.read_text() + "\n# drift probe\n")
                    self.run_command(sys.executable, str(checker), cwd=project, expected=1)
                    self.run_command(*apply, "--check", cwd=source, expected=1)
                    self.run_command(*apply, cwd=source)
                    self.run_command(sys.executable, str(checker), cwd=project)
                    # Consumer CI must detect a CodeQL workflow edit independently of the copy hashes.
                    if mode == "advanced":
                        workflow.write_bytes(data + b"# stale workflow pin\n")
                        self.run_command(sys.executable, "-m", "unittest", "discover", "-s", "scripts",
                                         "-p", "test_github_settings.py", cwd=project, expected=1)


if __name__ == "__main__":
    unittest.main()

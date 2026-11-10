"""Apply shared files into a scratch project, then verify them with the copied checker."""

import json
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import apply_baseline

CHECKER = "scripts/check_repo_baseline.py"
SOURCE = "profiles/hash-copy/check_repo_baseline.py"


def fake_git(*args):
    return "" if args[0] == "status" else "c" * 40


class ApplyBaselineTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.project = Path(folder.name)
        (self.project / ".github").mkdir()
        self.write_manifest({"files": {CHECKER: {"source": SOURCE}}, "project_note": "keep"})

    def write_manifest(self, data):
        (self.project / apply_baseline.MANIFEST).write_text(json.dumps(data))

    def run_checker(self):
        return subprocess.run([sys.executable, str(self.project / CHECKER)], capture_output=True, text=True)

    def test_apply_copies_records_hashes_and_keeps_project_keys(self):
        with patch.object(apply_baseline, "git", fake_git):
            self.assertEqual(apply_baseline.apply(self.project), [CHECKER])
        manifest = json.loads((self.project / apply_baseline.MANIFEST).read_text())
        self.assertEqual(manifest["source_commit"], "c" * 40)
        self.assertEqual(manifest["project_note"], "keep")
        self.assertEqual(len(manifest["files"][CHECKER]["sha256"]), 64)
        self.assertEqual(apply_baseline.apply(self.project, check=True), [])
        result = self.run_checker()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_local_edit_is_drift_for_both_tools(self):
        with patch.object(apply_baseline, "git", fake_git):
            apply_baseline.apply(self.project)
        with (self.project / CHECKER).open("a") as file:
            file.write("# local edit\n")
        self.assertEqual(apply_baseline.apply(self.project, check=True), [CHECKER])
        result = self.run_checker()
        self.assertEqual(result.returncode, 1)
        self.assertIn("DRIFT: " + CHECKER, result.stdout)

    def test_dirty_source_unknown_source_and_escaping_target_fail(self):
        with patch.object(apply_baseline, "git", lambda *args: " M scripts/x.py"):
            with self.assertRaisesRegex(ValueError, "Commit repo-baseline"):
                apply_baseline.apply(self.project)
        for files in [{"x.py": {"source": "missing.py"}}, {"x.py": {"source": "/etc/hosts"}},
                      {"x.py": {"source": "../outside.py"}}, {"../x.py": {"source": SOURCE}},
                      {".git/hooks/pre-commit": {"source": SOURCE}}, {"sub/.GIT/x.py": {"source": SOURCE}}, {}]:
            with self.subTest(files=files):
                self.write_manifest({"files": files})
                with self.assertRaises(ValueError):
                    apply_baseline.apply(self.project, check=True)

    def test_target_through_symlinked_folder_into_git_fails(self):
        (self.project / ".git" / "hooks").mkdir(parents=True)
        (self.project / "hooks").symlink_to(".git/hooks")
        self.write_manifest({"files": {"hooks/pre-commit": {"source": SOURCE}}})
        with self.assertRaisesRegex(ValueError, "inside .git"):
            apply_baseline.apply(self.project, check=True)
        self.assertFalse((self.project / ".git" / "hooks" / "pre-commit").exists())

    def test_dependabot_config_is_generated_per_ecosystem(self):
        target = ".github/dependabot.yml"
        ecosystems = [{"package-ecosystem": "cargo", "directory": "/services/api"}]
        self.write_manifest({"files": {target: {"source": "templates/github/dependabot.yml", "ecosystems": ecosystems}}})
        with patch.object(apply_baseline, "git", fake_git):
            apply_baseline.apply(self.project)
        text = (self.project / target).read_text()
        self.assertTrue(text.startswith((apply_baseline.HERE / "templates/github/dependabot.yml").read_text()))
        self.assertIn("  - package-ecosystem: cargo\n    directory: /services/api\n", text)
        self.assertEqual(text.count("interval: weekly"), 2)
        self.assertEqual(apply_baseline.apply(self.project, check=True), [])
        (self.project / target).write_text(text.replace('"10:00"', '"09:00"'))
        self.assertEqual(apply_baseline.apply(self.project, check=True), [target])

    def test_invalid_ecosystems_fail(self):
        bad = [{"package-ecosystem": "github-actions", "directory": "/"},
               {"package-ecosystem": "npm", "directory": "/\n  labels: []"},
               {"package-ecosystem": "npm"}]
        for item in bad + [None]:
            with self.subTest(item=item):
                ecosystems = [item] if item is not None else [bad[1] | {"directory": "/a"}] * 2
                self.write_manifest({"files": {".github/dependabot.yml":
                                               {"source": "templates/github/dependabot.yml", "ecosystems": ecosystems}}})
                with self.assertRaisesRegex(ValueError, "Invalid ecosystems"):
                    apply_baseline.apply(self.project, check=True)

    def test_ignored_file_named_like_a_pathspec_is_not_tracked(self):
        # Without --literal-pathspecs, ":(exclude)…" matched other tracked files and passed.
        folder = Path(tempfile.mkdtemp(prefix=":(exclude)", dir=apply_baseline.HERE))
        self.addCleanup(shutil.rmtree, folder)  # only the folder this test created
        source = f"{folder.name}/__pycache__/payload.py"
        (folder / "__pycache__").mkdir()
        (apply_baseline.HERE / source).write_text("payload\n")
        self.write_manifest({"files": {"x.py": {"source": source}}})
        with self.assertRaisesRegex(ValueError, "not tracked"):
            apply_baseline.apply(self.project, check=True)

    def test_untracked_source_and_symlinked_manifest_fail(self):
        def untracked(*args):
            raise subprocess.CalledProcessError(1, ["git", *args])
        with patch.object(apply_baseline, "git", untracked):
            with self.assertRaisesRegex(ValueError, "not tracked"):
                apply_baseline.apply(self.project, check=True)
        with tempfile.TemporaryDirectory() as other:
            target = Path(other) / "repo-baseline.json"
            manifest = self.project / apply_baseline.MANIFEST
            target.write_text(manifest.read_text())
            manifest.unlink()
            manifest.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "regular file inside"):
                apply_baseline.apply(self.project, check=True)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import review_preflight
from review_preflight import changed_paths, classify


class ClassifyTest(unittest.TestCase):
    def test_env_in_any_folder_or_file_name_is_a_hit(self):
        hits, examples = classify([
            ".env", "app/.env.local", ".envrc", "sub/.env", ".env.d/settings.txt",
            ".env.example", "web/.env.example", ".env.d/.env.example", "src/env.py", "README.md",
        ])
        self.assertEqual(hits, [".env", ".env.d/.env.example", ".env.d/settings.txt", ".envrc",
                                "app/.env.local", "sub/.env"])
        self.assertEqual(examples, [".env.example", "web/.env.example"])


class ChangedPathsTest(unittest.TestCase):
    def git(self, *args):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                       check=True, capture_output=True)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        cwd = os.getcwd()
        self.addCleanup(os.chdir, cwd)
        os.chdir(self.tmp.name)
        self.git("init", "-q", "-b", "main")
        Path("README.md").write_text("x\n")
        self.git("add", ".")
        self.git("commit", "-qm", "base")
        self.git("checkout", "-qb", "pr")

    def test_env_added_then_renamed_inside_the_pr_is_still_found(self):
        Path("sub").mkdir()
        Path("sub/.env").write_text("SECRET=1\n")
        self.git("add", ".")
        self.git("commit", "-qm", "add")
        self.git("mv", "sub/.env", "sub/config.txt")
        self.git("commit", "-qm", "rename")
        paths = changed_paths("main", "pr")
        self.assertIn("sub/.env", paths)
        self.assertEqual(classify(paths)[0], ["sub/.env"])

    def test_example_name_with_a_trailing_newline_is_a_hit(self):
        Path(".env.example\n").write_text("SECRET=1\n")
        self.git("add", ".")
        self.git("commit", "-qm", "add")
        self.git("mv", ".env.example\n", "config.txt")
        self.git("commit", "-qm", "rename")
        self.assertEqual(classify(changed_paths("main", "pr"))[0], [".env.example\n"])

    def test_names_with_spaces_and_non_ascii_are_not_quoted(self):
        Path("한글 파일.txt").write_text("x\n")
        self.git("add", ".")
        self.git("commit", "-qm", "add")
        self.assertEqual(changed_paths("main", "pr"), {"한글 파일.txt"})


class MainTest(unittest.TestCase):
    """Runs main() against a local bare remote that has refs/pull/7/head. Only `gh pr view` is faked."""

    def git(self, *args, cwd=None):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                              check=True, capture_output=True, text=True, cwd=cwd).stdout.strip()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.git("init", "-q", "--bare", "-b", "main", str(root / "origin.git"))
        self.work = root / "work"
        self.git("clone", "-q", str(root / "origin.git"), str(self.work))
        cwd = os.getcwd()
        self.addCleanup(os.chdir, cwd)
        os.chdir(self.work)
        self.git("checkout", "-qb", "main")
        Path("README.md").write_text("x\n")
        self.git("add", ".")
        self.git("commit", "-qm", "base")
        self.git("push", "-q", "origin", "main")
        self.git("checkout", "-qb", "pr")

    def publish(self):
        self.git("push", "-q", "-f", "origin", "HEAD:refs/pull/7/head")
        return self.git("rev-parse", "HEAD")

    def commit(self, path, text="x\n"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text)
        self.git("add", ".")
        self.git("commit", "-qm", f"add {path}")

    def main(self, head, fork=False, *extra, err=None):
        real = review_preflight.run
        view = json.dumps({"number": 7, "headRefOid": head, "baseRefName": "main", "isCrossRepository": fork})
        out = io.StringIO()
        with patch.object(review_preflight, "run", lambda *a: view if a[0] == "gh" else real(*a)), \
                redirect_stdout(out), redirect_stderr(err or io.StringIO()):
            code = review_preflight.main(["https://example.invalid/pull/7", *extra])
        return code, out.getvalue()

    def test_env_name_stops_the_review_without_a_diff_command(self):
        self.commit("sub/.env", "SECRET=1\n")
        code, out = self.main(self.publish(), fork=True)
        self.assertEqual(code, 1)
        self.assertIn("fork: 예", out)
        self.assertIn("작업 트리: 보지 않음(fork PR)", out)
        self.assertIn("리뷰 미완(비밀값 파일): sub/.env", out)
        self.assertNotIn("diff:", out)

    def test_clean_pr_prints_the_diff_command_and_matching_work_tree(self):
        self.commit("docs/a.md")
        self.commit("web/.env.example")
        head = self.publish()
        code, out = self.main(head)
        self.assertEqual(code, 0)
        self.assertIn("작업 트리: head와 같음", out)
        self.assertIn("미검토(.env.example): web/.env.example", out)
        self.assertIn(f"refs/remotes/origin/main...{head} -- . ':!.env*' ':!**/.env*'", out)
        # The PR head lives outside refs/remotes, so a remote branch named pr/7 cannot collide with it.
        self.assertEqual(self.git("rev-parse", "refs/review-preflight/origin/pr/7"), head)

    def test_diff_command_from_a_subfolder_still_shows_the_whole_pr(self):
        self.commit("docs/a.md")
        self.commit("web/b.md")
        head = self.publish()
        os.chdir("web")
        code, out = self.main(head)
        self.assertEqual(code, 0)
        command = next(line for line in out.splitlines() if line.startswith("diff: "))[len("diff: "):]
        shown = subprocess.run(command, shell=True, check=True, capture_output=True, text=True).stdout
        self.assertIn("docs/a.md", shown)
        self.assertIn("web/b.md", shown)

    def test_json_gives_the_same_facts_and_a_runnable_diff_argv(self):
        self.commit("docs/a.md")
        self.commit("web/.env.example")
        head = self.publish()
        os.chdir("web")
        code, out = self.main(head, False, "--json")
        self.assertEqual(code, 0)
        self.assertTrue(out.isascii())
        result = json.loads(out)
        self.assertEqual({k: v for k, v in result.items() if k != "diff_argv"}, {
            "pr": 7, "fork": False, "head": head, "base": "refs/remotes/origin/main",
            "worktree": "same", "unreviewed_examples": ["web/.env.example"], "secret_hits": []})
        shown = subprocess.run(result["diff_argv"], check=True, capture_output=True, text=True).stdout
        self.assertIn("docs/a.md", shown)
        self.assertNotIn(".env.example", shown)

    def test_json_with_a_secrets_file_has_no_diff_argv(self):
        self.commit("sub/.env", "SECRET=1\n")
        code, out = self.main(self.publish(), True, "--json")
        self.assertEqual(code, 1)
        result = json.loads(out)
        self.assertEqual((result["secret_hits"], result["diff_argv"], result["worktree"]),
                         (["sub/.env"], None, "not_checked"))

    def test_json_prints_nothing_on_stdout_when_the_head_moved(self):
        self.commit("docs/a.md")
        old = self.publish()
        self.commit("docs/b.md")
        self.publish()
        err = io.StringIO()
        self.assertEqual(self.main(old, False, "--json", err=err), (2, ""))
        self.assertIn("head가 실행 중에 바뀌었다", err.getvalue())

    def test_work_tree_on_another_commit_is_reported(self):
        self.commit("docs/a.md")
        head = self.publish()
        self.git("checkout", "-q", "main")
        code, out = self.main(head)
        self.assertEqual(code, 0)
        self.assertIn("작업 트리: 다름", out)

    def test_head_that_moved_during_the_run_asks_to_run_again(self):
        self.commit("docs/a.md")
        old = self.publish()
        self.commit("docs/b.md")
        self.publish()
        self.assertEqual(self.main(old)[0], 2)

    def merge(self, branch, change):
        self.git("checkout", "-qb", branch, "main")
        self.commit(f"{branch}.txt")
        self.git("checkout", "-q", "pr")
        self.git("merge", "-q", "--no-ff", "--no-commit", branch)
        change()
        self.git("commit", "-qm", f"merge {branch}")

    def test_env_added_in_one_merge_and_removed_in_another_is_found(self):
        # Neither the three-dot diff nor a plain log shows it; only --cc on the merge commits does.
        self.commit("docs/a.md")
        self.merge("side1", lambda: (Path(".env").write_text("SECRET=1\n"), self.git("add", ".env")))
        self.merge("side2", lambda: self.git("rm", "-q", ".env"))
        code, out = self.main(self.publish())
        self.assertEqual(code, 1)
        self.assertIn("리뷰 미완(비밀값 파일): .env", out)


if __name__ == "__main__":
    unittest.main()

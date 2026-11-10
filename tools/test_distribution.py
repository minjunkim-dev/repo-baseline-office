"""Layout checks for the redesigned baseline (docs/archive/redesign-2026-11.md §7)."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CORE = ["AGENTS.md", "REVIEW.md", "gitignore", "pull_request_template.md"]
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")


def docs():
    for path in sorted(ROOT.rglob("*.md")):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith((".git/", "graft/", "docs/archive/")):
            continue
        yield path


class DistributionTests(unittest.TestCase):
    def test_core_is_small_copyable_files_without_python(self):
        core = ROOT / "templates/core"
        self.assertEqual(sorted(p.name for p in core.iterdir()), sorted(CORE))
        self.assertLessEqual(len((core / "AGENTS.md").read_text(encoding="utf-8").splitlines()), 60)

    def test_own_pr_template_is_the_core_template(self):
        self.assertEqual((ROOT / ".github/pull_request_template.md").read_text(encoding="utf-8"),
                         (ROOT / "templates/core/pull_request_template.md").read_text(encoding="utf-8"))

    def test_policy_stays_one_page(self):
        self.assertLessEqual(len((ROOT / "POLICY.md").read_text(encoding="utf-8")), 10000)

    def test_relative_links_resolve(self):
        missing = []
        for path in docs():
            for target in LINK.findall(path.read_text(encoding="utf-8")):
                if re.match(r"[a-z]+:", target):
                    continue
                if not (path.parent / target).exists():
                    missing.append(f"{path.relative_to(ROOT)} -> {target}")
        self.assertEqual(missing, [])

    def test_no_model_names_in_core_or_policy(self):
        for rel in ["POLICY.md", "templates/core/AGENTS.md", "templates/core/REVIEW.md"]:
            text = (ROOT / rel).read_text(encoding="utf-8").lower()
            for word in ("opus", "sonnet", "composer", "grok"):
                self.assertNotIn(word, text, rel)

    def test_default_settings_do_not_require_the_gate(self):
        for rel in ["templates/github/repository-settings.json", ".github/repository-settings.json"]:
            self.assertNotIn('"review/gate"', (ROOT / rel).read_text(encoding="utf-8"), rel)


if __name__ == "__main__":
    unittest.main()

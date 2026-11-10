"""Event-policy classification, including workflow_path globs."""

import json
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import review_status_policy as policy

TARGET = policy.TARGET


def rule(events):
    return [{"type": "restrict_action_events", "parameters": {"allowed_events": events}}]


def sample(include, exclude=None, events=None, source="Organization"):
    return {
        "enforcement": "active",
        "source_type": source,
        "conditions": {"workflow_path": {"include": include, "exclude": exclude or []}},
        "rules": rule(events or ["pull_request_target"]),
    }


class PolicyTests(unittest.TestCase):
    def test_a_directory_glob_that_allows_only_pull_request_target_stops_the_install(self):
        for pattern in (".github/workflows/**", ".github/workflows/*", "**", "**.yml"):
            with self.subTest(pattern=pattern):
                self.assertEqual(policy.classify(sample([pattern])), "parent")

    def test_a_star_does_not_cross_a_slash(self):
        self.assertEqual(policy.classify(sample([".github/*"])), "other")
        self.assertTrue(policy.matches(".github/workflows/review-status.yml?", TARGET))
        self.assertFalse(policy.matches(".github/workflows/review-status.ym?", TARGET))
        self.assertTrue(policy.matches(".github/workflows/**/*.yml", TARGET))
        self.assertTrue(policy.matches(".github/workflows/**/review-status.yml", TARGET))
        self.assertFalse(policy.matches(".github/workflows/review-**/status.yml", TARGET))
        self.assertTrue(policy.matches("**/review-status.yml", TARGET))

    def test_a_later_unevaluable_pattern_still_stops(self):
        with self.assertRaises(policy.UnrecognizedPattern):
            policy.classify(sample(["~ALL", "{unknown}"]))
        with self.assertRaises(policy.UnrecognizedPattern):
            policy.classify(sample(["[9-0]"]))

    def test_a_stricter_rule_is_not_hidden_by_a_broader_one(self):
        item = sample([TARGET], source="Repository")
        item["rules"].append({"type": "restrict_action_events",
                              "parameters": {"allowed_events": ["issue_comment", "pull_request_target"]}})
        self.assertEqual(policy.classify(item), "parent")

    def test_a_glob_that_allows_both_events_is_already_enough(self):
        both = ["issue_comment", "pull_request_target"]
        self.assertEqual(policy.classify(sample([".github/workflows/**"], events=both)), "both")

    def test_exclude_glob_does_not_make_an_all_workflows_policy_apply(self):
        item = sample(["~ALL"], exclude=[".github/workflows/**"])
        self.assertEqual(policy.classify(item), "other")
        item["conditions"]["workflow_path"]["include"] = []
        self.assertEqual(policy.classify(item), "other")

    def test_exact_repository_policy_can_be_updated(self):
        item = sample([TARGET], source="Repository")
        self.assertEqual(policy.classify(item), "narrow")

    def test_an_unevaluable_pattern_is_not_treated_as_absent(self):
        with self.assertRaises(policy.UnrecognizedPattern):
            policy.classify(sample([".github/workflows/review-status.[yml"]))

    def test_cli_stops_on_an_unevaluable_pattern(self):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent / "review_status_policy.py")],
            input=json.dumps(sample([".github/workflows/{review-status.yml}"])),
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()

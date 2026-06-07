import os
import unittest

from hermes_9router_tracker.tracker import (
    TrackerConfig,
    _build_summary,
    _label_sort_key,
    _provider_sort_key,
    scrape_quota_json,
)
from hermes_9router_tracker.hermes_install import build_exec_command


class TrackerOrderingTests(unittest.TestCase):
    def tearDown(self):
        for key in (
            "TRACKER_PROVIDER_ORDER",
            "TRACKER_PROVIDER_LABEL_ORDER",
            "TRACKER_LABEL_REPLACEMENTS",
        ):
            os.environ.pop(key, None)

    def test_provider_sort_key_is_alphabetical_by_default(self):
        providers = ["kiro", "gemini-cli", "antigravity", "codex"]
        ordered = sorted(providers, key=_provider_sort_key)
        self.assertEqual(ordered, ["antigravity", "codex", "gemini-cli", "kiro"])

    def test_provider_sort_key_can_be_overridden(self):
        os.environ["TRACKER_PROVIDER_ORDER"] = "codex,antigravity,gemini-cli,kiro"
        providers = ["kiro", "gemini-cli", "antigravity", "codex"]
        ordered = sorted(providers, key=_provider_sort_key)
        self.assertEqual(ordered, ["codex", "antigravity", "gemini-cli", "kiro"])

    def test_provider_label_order_can_be_overridden(self):
        os.environ["TRACKER_PROVIDER_LABEL_ORDER"] = '{"custom-provider": ["Model B", "Model A"]}'
        labels = ["Model A", "Model B", "Model C"]
        ordered = sorted(labels, key=lambda label: _label_sort_key("custom-provider", label))
        self.assertEqual(ordered, ["Model B", "Model A", "Model C"])


class TrackerSummaryTests(unittest.TestCase):
    def test_summary_lists_low_quota_alerts(self):
        connections = [
            {"id": "1", "provider": "codex", "email": "a@example.com"},
            {"id": "2", "provider": "kiro", "name": "Account 1"},
        ]
        usages = {
            "1": {
                "plan": "plus",
                "quotas": {
                    "weekly": {"used": 80, "total": 100, "remaining": 20, "resetAt": "2026-06-11T01:11:00Z"}
                },
            },
            "2": {
                "plan": "free",
                "quotas": {
                    "credit": {"used": 47, "total": 50, "remaining": 3, "resetAt": "2026-07-01T00:00:00Z"}
                },
            },
        }
        summary = _build_summary(connections, usages)
        self.assertIn("- provider: codex:1, kiro:1", summary)
        self.assertTrue(any("weekly 20/100 (20%)" in line for line in summary))
        self.assertTrue(any("credit 3/50 (6%)" in line for line in summary))


class TrackerJsonTests(unittest.TestCase):
    def test_scrape_quota_json_uses_fetch_data_contract(self):
        import hermes_9router_tracker.tracker as tracker

        original = tracker._fetch_data
        try:
            tracker._fetch_data = lambda config: (
                [{"id": "1", "provider": "codex", "email": "demo@example.com"}],
                {"1": {"plan": "plus", "quotas": {}}},
            )
            payload = scrape_quota_json(TrackerConfig(base_url="https://example.com", password="x"))
        finally:
            tracker._fetch_data = original

        self.assertEqual(payload["summary"]["accounts"], 1)
        self.assertEqual(payload["summary"]["providers"], {"codex": 1})
        self.assertIn("connections", payload)
        self.assertIn("usages", payload)


class HermesInstallTests(unittest.TestCase):
    def test_build_exec_command_default(self):
        self.assertEqual(build_exec_command("router-quota-tracker"), "router-quota-tracker")

    def test_build_exec_command_with_provider(self):
        self.assertEqual(
            build_exec_command("router-quota-tracker", "codex"),
            "router-quota-tracker --provider codex",
        )


if __name__ == "__main__":
    unittest.main()

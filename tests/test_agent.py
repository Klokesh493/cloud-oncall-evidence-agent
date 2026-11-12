import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

from agent import run
from cloudwatch import observation


class AgentTest(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(Path("examples/checkout.json").read_text())["observations"]

    def test_two_signals_escalate_with_citations(self):
        report = run("checkout", 360, self.data)
        self.assertEqual(report["decision"], "escalate")
        self.assertEqual(report["route"], "queue-backlog")
        self.assertEqual(set(report["citations"]), {"slo", "queue", "change"})

    def test_stale_and_foreign_data_require_review(self):
        report = run("catalog", 400, self.data)
        self.assertEqual(report["decision"], "review")
        self.assertEqual(report["missing_or_uncertain"], ["change", "queue", "slo"])
        self.assertEqual(report["citations"], {})

    def test_conflicting_observations_are_excluded(self):
        other = {**self.data[1], "id": "other:queue", "status": "ok"}
        report = run("checkout", 360, self.data + [other])
        self.assertIn("queue", report["missing_or_uncertain"])
        self.assertNotIn("queue", report["citations"])

    def test_health_requires_all_three_evidence_sources(self):
        for row, state in zip(self.data, ("healthy", "ok", "stable")):
            row["status"] = state
        self.assertEqual(run("checkout", 360, self.data)["decision"], "observe")
        self.assertEqual(run("checkout", 360, self.data[:-1])["decision"], "review")

    def test_cloudwatch_adapter_only_reads_named_alarm(self):
        cloudwatch = Mock()
        cloudwatch.describe_alarms.return_value = {
            "MetricAlarms": [{"AlarmName": "checkout-dlq", "StateValue": "ALARM",
                              "StateUpdatedTimestamp": datetime(2026, 1, 1, tzinfo=timezone.utc)}]
        }
        self.assertEqual(observation(cloudwatch, "checkout-dlq", "checkout")["status"], "alarm")
        cloudwatch.describe_alarms.assert_called_once_with(
            AlarmNames=["checkout-dlq"], AlarmTypes=["MetricAlarm"]
        )

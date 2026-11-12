# Operator runbook

## Reproduce

```sh
make verify
python3 agent.py examples/checkout.json
```

## Triage and recovery

Start with cited evidence IDs and confirm the timestamps in the originating systems. On a queue escalation, inspect the DLQ and recent producer changes. On a missing-evidence route, collect the missing source and rerun the review.

## Evidence boundaries

The agent has no model or external tool executor. The AWS adapter was checked with a mock. Its output is advisory and it sends no pages or infrastructure changes.

# Case study

## Problem

An on-call responder often sees a page, an alarm, and a recent deploy together. A useful handoff needs the observations, their freshness, and a clear indication when the responder needs more evidence.

## Implementation

The agent selects observations for the requested service and rejects old or future evidence. Conflicting observations at the same newest minute leave a gap. A paging SLO plus an alarm suggests queue escalation. A paging SLO plus a recent change suggests release investigation. Missing or uncertain evidence produces a review path.

## Validation

Five tests passed for citations, stale or conflicting inputs, missing context, and the read-only CloudWatch adapter with a mocked client. The bundled fixture returned `escalate` on the queue-backlog route.

## Limits

The agent has no model or external tool executor. The AWS adapter was checked with a mock. Its output is advisory and it sends no pages or infrastructure changes.

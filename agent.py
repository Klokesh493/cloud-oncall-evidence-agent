"""Turn read-only cloud and SRE evidence into an on-call recommendation."""
import argparse
import json
import re
from pathlib import Path

STATUSES = {
    "slo": {"healthy", "page", "ticket", "insufficient_data"},
    "queue": {"ok", "alarm", "unknown"},
    "change": {"stable", "recent", "unknown"},
}
IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]{1,80}")
MAX_AGE_MINUTES = 15


def run(service, now_minute, observations):
    if not isinstance(service, str) or not IDENTIFIER.fullmatch(service) or type(now_minute) is not int:
        raise ValueError("service and now_minute are required")
    usable = {}
    for item in observations:
        kind = item["kind"]
        if item["service"] != service or kind not in STATUSES:
            continue
        minute = item["observed_minute"]
        identifier = item["id"]
        status = item["status"]
        if type(minute) is not int or not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier):
            raise ValueError("invalid evidence identity or timestamp")
        if status not in STATUSES[kind]:
            raise ValueError("unsupported evidence status")
        if not 0 <= now_minute - minute <= MAX_AGE_MINUTES:
            continue
        current = usable.get(kind)
        if current is None or minute > current[0]:
            usable[kind] = (minute, {(identifier, status)})
        elif minute == current[0]:
            current[1].add((identifier, status))

    gaps = sorted(kind for kind in STATUSES if kind not in usable or len(usable[kind][1]) != 1)
    evidence = {kind: next(iter(entries)) for kind, (_, entries) in sorted(usable.items()) if kind not in gaps}
    unresolved = sorted(set(gaps) | {
        kind for kind, (_, status) in evidence.items() if status in {"unknown", "insufficient_data"}
    })
    states = {kind: value[1] for kind, value in evidence.items()}

    if states.get("slo") == "page" and states.get("queue") == "alarm":
        decision, route = "escalate", "queue-backlog"
    elif states.get("slo") == "page" and states.get("change") == "recent":
        decision, route = "escalate", "recent-change"
    elif states.get("slo") in {"page", "ticket"} or states.get("queue") == "alarm":
        decision, route = "review", "service-degradation"
    elif unresolved:
        decision, route = "review", "missing-evidence"
    elif states["change"] == "recent":
        decision, route = "review", "recent-change"
    else:
        decision, route = "observe", "normal"
    return {
        "service": service, "decision": decision, "route": route,
        "citations": {kind: {"id": identifier, "status": status}
                      for kind, (identifier, status) in evidence.items()},
        "missing_or_uncertain": unresolved,
        "human_action_required": decision != "observe",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    try:
        request = json.loads(args.snapshot.read_text())
        result = run(request["service"], request["now_minute"], request["observations"])
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(2, f"Invalid snapshot: {error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

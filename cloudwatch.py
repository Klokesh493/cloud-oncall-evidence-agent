"""Collect one named CloudWatch alarm as an on-call observation."""
import argparse
import json
from datetime import timezone


def observation(client, name, service):
    alarms = client.describe_alarms(AlarmNames=[name], AlarmTypes=["MetricAlarm"])["MetricAlarms"]
    if len(alarms) != 1 or alarms[0]["AlarmName"] != name:
        raise ValueError("the named metric alarm was not found")
    alarm = alarms[0]
    timestamp = alarm.get("StateUpdatedTimestamp")
    if timestamp is None:
        raise ValueError("alarm has no evaluation timestamp")
    # Observed age tracks the supplied CloudWatch state timestamp, so old states
    # are treated as uncertain by the agent even if the fetch itself is fresh.
    return {
        "kind": "queue", "id": "cloudwatch:" + name, "service": service,
        "observed_minute": int(timestamp.astimezone(timezone.utc).timestamp()) // 60,
        "status": {"OK": "ok", "ALARM": "alarm"}.get(alarm["StateValue"], "unknown"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("alarm")
    parser.add_argument("service")
    parser.add_argument("--region", required=True)
    args = parser.parse_args()
    import boto3

    try:
        result = observation(boto3.client("cloudwatch", region_name=args.region), args.alarm, args.service)
    except ValueError as error:
        parser.exit(2, f"Alarm evidence unavailable: {error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

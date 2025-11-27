#!/usr/bin/env python3
"""Send an event to the Act service and apply the recommended mitigation."""
import argparse
import json
import requests

ACT_URL = "http://localhost:8100/act"


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply mitigation via Act service")
    parser.add_argument("target", help="IP or hostname to mitigate")
    parser.add_argument("--source", default="ng-siem", help="event source")
    parser.add_argument("--severity", type=int, default=1, help="event severity")
    args = parser.parse_args()

    payload = {"target": args.target, "source": args.source, "severity": args.severity}
    response = requests.post(ACT_URL, json=payload, timeout=5)
    data = response.json()
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()

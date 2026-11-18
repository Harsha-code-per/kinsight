"""Send recorded stage and report events from a separate synthetic lab process."""

import argparse
import json
import time
from datetime import datetime, timezone
from uuid import uuid4

import httpx

from services.api.auth import secret
from services.api.lab_feed import PATH, SIGNING_SECRET, signature


def demo_report(subject, revision, corrected=False):
    return {
        "subject_id": subject,
        "revision": revision,
        "resource": {
            "resourceType": "DiagnosticReport",
            "id": f"{subject}-report",
            "subject": {"reference": f"Patient/{subject}"},
            "code": {"text": "Synthetic carrier screen"},
            "meta": {"tag": [{"system": "https://kinsight.example/tags", "code": "synthetic"}]},
            "status": "corrected" if corrected else "final",
            "issued": datetime.now(timezone.utc).isoformat(),
        },
        "findings": {"COND_001": "uncertain" if corrected else "carrier"},
    }


def send(client, key, event):
    body = json.dumps(event, separators=(",", ":")).encode()
    stamp, delivery = str(int(time.time())), uuid4().hex
    response = client.post(
        PATH,
        content=body,
        headers={
            "content-type": "application/json",
            "x-lab-timestamp": stamp,
            "x-lab-delivery": delivery,
            "x-lab-signature": signature(key, stamp, delivery, body),
        },
    )
    if not response.is_success:
        raise SystemExit(
            f"Lab delivery stopped at HTTP {response.status_code}. Check the lab service and current tracker stage."
        )
    print(f"Tracker stage {response.json()['stage']} accepted")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--subject", choices=["synthetic-a", "synthetic-b"], default="synthetic-a")
    parser.add_argument("--start-stage", type=int, choices=range(2, 9), default=2)
    parser.add_argument("--revision", type=int, default=1)
    parser.add_argument("--delay", type=float, default=2)
    args = parser.parse_args()
    if not 0 <= args.delay <= 60 or not 1 <= args.revision <= 1_000_000:
        parser.error("Use a delay from 0 to 60 seconds and a valid positive revision")
    key = secret(SIGNING_SECRET)
    with httpx.Client(base_url=args.api, timeout=15) as client:
        for stage in range(args.start_stage, 8):
            send(client, key, {"kind": "stage", "subject_id": args.subject, "stage": stage})
            time.sleep(args.delay)
        report = demo_report(args.subject, args.revision, corrected=args.revision > 1)
        send(client, key, {"kind": "report", "report": report})


if __name__ == "__main__":
    main()

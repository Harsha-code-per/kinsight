import json
import time
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from services.api.lab_feed import MAX_BODY_SIZE, PATH, SIGNING_SECRET, signature
from services.api.main import create_app
from services.consent.audit import verify_chain
from services.consent.models import AuditEvent
from tests.integration.test_lab_sandbox import INTAKE, PERSONAL, REVIEW, auth, init, report

KEY = b"synthetic-lab-feed-test-distinct-secret"

SANDBOX_ROUTES = {
    (INTAKE, "post"),
    (PERSONAL, "get"),
    (f"{PERSONAL}/share", "post"),
    ("/api/counsellor/sandbox-reports/{subject}", "get"),
    ("/api/counsellor/sandbox-reports/{subject}/approve", "post"),
}


def test_lab_route_inventory_requires_authentication(monkeypatch):
    init(monkeypatch, "0")
    monkeypatch.setenv(SIGNING_SECRET, KEY.decode())

    def routes(app):
        return {(path, method) for path, methods in app.openapi()["paths"].items() for method in methods}

    baseline = routes(create_app("sqlite://"))
    monkeypatch.setenv("KINSIGHT_LAB_SANDBOX", "1")
    app = create_app("sqlite://")
    expected = SANDBOX_ROUTES | {(PATH, "post")}
    assert routes(app) - baseline == expected
    with TestClient(app) as client:
        for path, method in expected:
            response = client.request(method.upper(), path.replace("{subject}", "synthetic-a"))
            assert response.status_code == 401, path
            assert response.headers["cache-control"] == "no-store"


def envelope(event, *, timestamp=None):
    body = json.dumps(event).encode() if not isinstance(event, bytes) else event
    stamp = str(int(time.time()) if timestamp is None else timestamp)
    delivery = uuid4().hex
    return {
        "content": body,
        "headers": {
            "x-lab-timestamp": stamp,
            "x-lab-delivery": delivery,
            "x-lab-signature": signature(KEY, stamp, delivery, body),
        },
    }


def test_signed_lab_moves_tracker_and_keeps_release_gated(monkeypatch, tmp_path):
    init(monkeypatch, "1")
    monkeypatch.setenv(SIGNING_SECRET, KEY.decode())
    app = create_app(f"sqlite:///{tmp_path / 'lab.db'}")
    tracker = "/api/lifecycle/tracker"
    with TestClient(app) as client:
        a, b, reviewer, operator = (
            auth(client, role) for role in ("person_a", "person_b", "counsellor", "demo_operator")
        )
        assert client.get(tracker, headers=a).json()["stage"] == 1
        assert client.post(f"{tracker}/advance", headers=a).status_code == 403
        assert client.post(INTAKE, headers=operator, json=report()).status_code == 403
        stage = {"kind": "stage", "subject_id": "synthetic-a", "stage": 2}
        delivery = envelope(stage)
        assert client.post(PATH, content=delivery["content"], headers=a).status_code == 401
        assert client.post(PATH, **envelope(stage, timestamp=int(time.time()) - 301)).status_code == 401
        assert client.post(PATH, content=b"different", headers=delivery["headers"]).status_code == 401
        assert client.post(PATH, **envelope(b" " * (MAX_BODY_SIZE + 1))).status_code == 413
        assert client.post(PATH, **envelope({"kind": "other"})).status_code == 422
        assert client.post(PATH, **envelope({**stage, "stage": 4})).status_code == 409
        assert client.post(PATH, **envelope({"kind": "report", "report": report()})).status_code == 409
        assert client.post(PATH, **delivery).json()["stage"] == 2
        assert client.post(PATH, **delivery).status_code == 409
        for index in range(3, 8):
            assert client.post(PATH, **envelope({**stage, "stage": index})).json()["stage"] == index
        current = client.get(tracker, headers=a).json()
        assert current["source"] == "signed_lab"
        assert set(current["times"]) == set(current["stages"][1:7])
        assert client.get(tracker, headers=b).json()["stage"] == 1
        assert client.post(PATH, **envelope({"kind": "report", "report": report()})).json()["stage"] == 8
        assert client.get(PERSONAL, headers=a).json()["report"] is None
        assert client.get(REVIEW, headers=reviewer).status_code == 403
        assert client.post(f"{PERSONAL}/share", headers=a).status_code == 200
        assert client.post(f"{REVIEW}/approve", headers=reviewer, json={"revision": 1}).status_code == 204
        assert client.get(PERSONAL, headers=a).json()["state"] == "released"
        corrected = report(2, "corrected", "uncertain")
        assert client.post(PATH, **envelope({"kind": "report", "report": corrected})).json()["stage"] == 8
        assert client.get(PERSONAL, headers=a).json()["report"] is None
        assert client.post(f"{REVIEW}/approve", headers=reviewer, json={"revision": 1}).status_code == 409
    with app.state.sessions() as db:
        assert verify_chain(db)
        assert set(db.scalars(select(AuditEvent.reason_code).where(AuditEvent.decision == "deny"))) >= {
            "lab_event_rejected",
            "lab_replayed",
        }

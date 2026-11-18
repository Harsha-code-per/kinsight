from fastapi.testclient import TestClient

from services.api.main import create_app

INTAKE = "/api/sandbox/lab/reports"
PERSONAL = "/api/me/sandbox-report"
REVIEW = "/api/counsellor/sandbox-reports/synthetic-a"


def report(revision=1, status="final", finding="carrier", *, subject="synthetic-a"):
    return {
        "subject_id": subject,
        "revision": revision,
        "resource": {
            "resourceType": "DiagnosticReport",
            "id": f"{subject}-report",
            "subject": {"reference": f"Patient/{subject}"},
            "code": {"text": "Synthetic carrier screen"},
            "meta": {"tag": [{"system": "https://kinsight.example/tags", "code": "synthetic"}]},
            "status": status,
            "issued": "2026-11-18T10:00:00Z",
        },
        "findings": {} if status == "cancelled" else {"COND_001": finding},
    }


def init(monkeypatch, enabled):
    monkeypatch.setenv("KINSIGHT_TOKEN_SECRET", "synthetic-lab-sandbox-test-token-secret")
    monkeypatch.setenv("KINSIGHT_AUDIT_SALT", "synthetic-lab-sandbox-test-audit-secret")
    monkeypatch.setenv("KINSIGHT_DEMO_AUTH", "1")
    monkeypatch.setenv("KINSIGHT_DEMO", "1")
    monkeypatch.setenv("KINSIGHT_LAB_SANDBOX", enabled)


def auth(client, persona):
    response = client.post("/api/auth/persona", json={"persona": persona})
    response.raise_for_status()
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_lab_sandbox_is_opt_in(monkeypatch):
    init(monkeypatch, "0")
    with TestClient(create_app("sqlite://")) as client:
        assert client.post(INTAKE, json=report(), headers=auth(client, "demo_operator")).status_code == 404


def test_lab_intake_review_and_correction_are_scoped_and_durable(monkeypatch, tmp_path):
    init(monkeypatch, "1")
    url = f"sqlite:///{tmp_path / 'lab.db'}"
    with TestClient(create_app(url)) as client:
        a, b, reviewer, lab = (auth(client, role) for role in ("person_a", "person_b", "counsellor", "demo_operator"))
        assert client.post(INTAKE, json=report(), headers=a).status_code == 403
        invalid = report()
        invalid["resource"]["subject"]["reference"] = "Patient/synthetic-b"
        assert client.post(INTAKE, json=invalid, headers=lab).status_code == 422
        for _ in range(2):
            assert client.post(INTAKE, json=report(), headers=lab).status_code == 200
        assert client.post(INTAKE, json=report(finding="uncertain"), headers=lab).status_code == 409
        assert client.get(PERSONAL, headers=a).json()["report"] is None
        assert client.get(PERSONAL, headers=b).json()["state"] == "missing"
        assert client.get(REVIEW, headers=reviewer).status_code == 403
        grant = client.post(f"{PERSONAL}/share", headers=a).json()["id"]
        assert client.post(f"{PERSONAL}/share", headers=a).json()["id"] == grant
        assert any(
            item["id"] == grant and item["scope"] == "sandbox_review"
            for item in client.get("/api/me/consents", headers=a).json()
        )
        assert client.get(REVIEW, headers=reviewer).json()["report"]["findings"] == {"COND_001": "carrier"}
        assert client.post(f"{REVIEW}/approve", json={"revision": 1}, headers=reviewer).status_code == 204
        assert client.get(PERSONAL, headers=a).json()["state"] == "released"
        review_b = "/api/counsellor/sandbox-reports/synthetic-b"
        assert (
            client.post(INTAKE, json=report(finding="not_detected", subject="synthetic-b"), headers=lab).status_code
            == 200
        )
        assert client.get(review_b, headers=reviewer).status_code == 403
        assert client.post(f"{PERSONAL}/share", headers=b).status_code == 200
        assert client.post(f"{review_b}/approve", json={"revision": 1}, headers=reviewer).status_code == 204
        assert client.post(INTAKE, json=report(2, "corrected", "uncertain"), headers=lab).status_code == 200
        assert client.post(INTAKE, json=report(), headers=lab).status_code == 200
        assert client.get(PERSONAL, headers=a).json()["report"] is None
        assert client.get(PERSONAL, headers=b).json()["report"]["findings"] == {"COND_001": "not_detected"}
        assert client.post(f"{REVIEW}/approve", json={"revision": 1}, headers=reviewer).status_code == 409
        assert client.post(f"/api/me/consents/{grant}/revoke", headers=a).status_code == 200
        assert client.post(f"{REVIEW}/approve", json={"revision": 2}, headers=reviewer).status_code == 403

    with TestClient(create_app(url)) as client:
        assert client.get(PERSONAL, headers=a).json() == {
            "state": "pending",
            "revision": 2,
            "report": None,
            "is_synthetic": True,
        }
        assert client.post(f"{PERSONAL}/share", headers=a).status_code == 200
        assert client.post(f"{REVIEW}/approve", json={"revision": 2}, headers=reviewer).status_code == 204
        assert client.get(PERSONAL, headers=a).json()["report"]["findings"] == {"COND_001": "uncertain"}
        assert client.post(INTAKE, json=report(3, "cancelled"), headers=lab).status_code == 200
        assert client.get(PERSONAL, headers=a).json()["state"] == "withdrawn"
        assert client.post(f"{REVIEW}/approve", json={"revision": 3}, headers=reviewer).status_code == 409

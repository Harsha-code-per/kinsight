from copy import deepcopy

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import select

from scripts.export_fhir_bundles import build_bundles
from services.api import fhir_preview
from services.api.main import create_app
from services.consent.audit import verify_chain
from services.consent.models import AuditEvent
from tests.integration.test_lab_sandbox import auth, init

PATH = "/api/me/imports/fhir/preview"


def test_preview_uses_the_signed_in_assignment_and_rejects_mismatched_resources(monkeypatch, tmp_path):
    init(monkeypatch, "0")
    assert PATH not in create_app("sqlite://").openapi()["paths"]
    monkeypatch.setenv(fhir_preview.BASE_ENV, "http://fhir.test/fhir")
    bundle = build_bundles()[0][0][1]
    resources = {entry["request"]["url"]: entry["resource"] for entry in bundle["entry"]}
    first, second = (fhir_preview.ASSIGNED[actor] for actor in ("synthetic-a", "synthetic-b"))
    assert {key for key in resources if key.startswith("Patient/")} == {f"Patient/{first}", f"Patient/{second}"}
    requested = []
    problem = None

    def reply(request):
        path = request.url.path.removeprefix("/fhir/")
        if path.startswith("Patient/"):
            requested.append(path)
            return httpx.Response(200, json=resources[path])
        patient_id = request.url.params["_id"]
        assert request.url.params["subject"] == f"Patient/{patient_id}"
        assert request.url.params["_include"] == "DiagnosticReport:result"
        report = deepcopy(resources[f"DiagnosticReport/{patient_id}"])
        report["meta"]["versionId"] = "opaque.server-id"
        findings = [deepcopy(resources[item["reference"]]) for item in report["result"]]
        if problem == "subject":
            findings[-1]["subject"]["reference"] = f"Patient/{second}"
        if problem == "target":
            findings[0]["component"][0]["valueCodeableConcept"]["coding"][0]["code"] = "UNMAPPED_GENE"
        if problem == "foreign-reference":
            report["result"][0]["reference"] = "https://other.invalid/Observation/fixture"
        return httpx.Response(200, json={
            "resourceType": "Bundle", "type": "searchset",
            "entry": [{"resource": resource} for resource in [report, *findings]],
        })

    original_reader = fhir_preview.read_preview

    def read_with_fixture(_, patient_id, panel):
        with httpx.Client(base_url="http://fhir.test/fhir/", transport=httpx.MockTransport(reply)) as session:
            return original_reader(session, patient_id, panel)

    monkeypatch.setattr(fhir_preview, "read_preview", read_with_fixture)
    app = create_app(f"sqlite:///{tmp_path / 'fhir.db'}")
    with TestClient(app) as client:
        a, b, reviewer = (auth(client, role) for role in ("person_a", "person_b", "counsellor"))
        assert client.post(PATH).status_code == 401
        assert client.post(PATH, headers=reviewer).status_code == 403
        assert not requested
        a_preview = client.post(PATH, headers=a, json={"patient_id": second}).json()
        assert a_preview["report_id"] == first
        assert a_preview["version"] == "opaque.server-id"
        b_preview = client.post(PATH, headers=b).json()
        assert b_preview["report_id"] == second
        assert requested == [f"Patient/{first}", f"Patient/{second}"]
        problem = "subject"
        assert client.post(PATH, headers=a).status_code == 502
        problem = "foreign-reference"
        assert client.post(PATH, headers=a).status_code == 502
        problem = "target"
        gated = client.post(PATH, headers=a).json()
        assert gated["state"] == "requires_review"
        assert gated["findings"] == []
    with app.state.sessions() as session:
        assert len(session.scalars(select(AuditEvent).where(AuditEvent.resource_type == "sandbox_report")).all()) == 5
        assert verify_chain(session)

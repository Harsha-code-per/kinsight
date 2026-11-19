"""Read-only import preview for the two people in the seeded FHIR sandbox."""

import json
import re
from datetime import datetime

import httpx
from fastapi import Depends, HTTPException
from pydantic import AwareDatetime, TypeAdapter
from sqlalchemy.orm import Session

from services.cohort.fhir import FINDINGS, SYSTEM, TAG
from services.cohort.panel import load_panel

BASE_ENV = "KINSIGHT_FHIR_SANDBOX_URL"
ASSIGNED = {
    "synthetic-a": "ks-demo-b2562112-399d-497d-a2ea-9a9d491db685",
    "synthetic-b": "ks-demo-66aa9ecf-d459-469e-8aa2-130d6dd3943b",
}
MAX_BYTES = 262_144
ISSUED = TypeAdapter(AwareDatetime)


def read_json(client, path, *, params=None):
    with client.stream("GET", path, params=params) as response:
        response.raise_for_status()
        data = bytearray()
        for chunk in response.iter_bytes():
            if len(data) + len(chunk) > MAX_BYTES:
                raise ValueError("FHIR response exceeds the preview limit")
            data.extend(chunk)
    result = json.loads(data)
    if not isinstance(result, dict):
        raise ValueError("Expected a FHIR resource")
    return result


def require_resource(resource, kind, resource_id, subject=None):
    if (
        resource.get("resourceType") != kind
        or resource.get("id") != resource_id
        or TAG not in resource.get("meta", {}).get("tag", [])
        or (subject is not None and resource.get("subject", {}).get("reference") != subject)
    ):
        raise ValueError("FHIR resource does not match the assigned fixture")


def code_from(concept, system):
    codes = [item["code"] for item in concept.get("coding", []) if item.get("system") == system]
    return codes[0] if len(codes) == 1 else None


def read_preview(client: httpx.Client, patient_id: str, panel) -> dict:
    subject = f"Patient/{patient_id}"
    require_resource(read_json(client, subject), "Patient", patient_id)
    bundle = read_json(client, "DiagnosticReport", params={
        "_id": patient_id, "subject": subject, "_include": "DiagnosticReport:result",
    })
    if bundle.get("resourceType") != "Bundle" or bundle.get("type") != "searchset" or any(
        item.get("relation") == "next" for item in bundle.get("link", [])
    ):
        raise ValueError("Expected a complete FHIR search bundle")
    resources = {}
    for item in bundle.get("entry", []):
        resource = item["resource"]
        key = (resource["resourceType"], resource["id"])
        if key in resources:
            raise ValueError("Duplicate FHIR search resource")
        resources[key] = resource

    if not resources:
        return {"state": "missing", "findings": []}
    report = resources.pop(("DiagnosticReport", patient_id))
    require_resource(report, "DiagnosticReport", patient_id, subject)
    for (kind, observation_id), observation in resources.items():
        require_resource(observation, "Observation", observation_id, subject)
        if kind != "Observation":
            raise ValueError("Unexpected FHIR search resource")
    status = report["status"]
    if status not in {"final", "amended", "corrected"}:
        return {"state": "unavailable", "findings": []}
    version = report["meta"]["versionId"]
    if not isinstance(version, str) or not re.fullmatch(r"[A-Za-z0-9.\-]{1,64}", version):
        raise ValueError("Expected a FHIR server version")
    if not isinstance(report.get("issued"), str):
        raise ValueError("Expected a FHIR report issuance time")
    issued: datetime = ISSUED.validate_python(report["issued"])
    summary = {"report_id": patient_id, "version": version, "issued_at": issued.isoformat(), "status": status}
    if code_from(report["code"], f"{SYSTEM}/panel") != panel.panel_version:
        return {**summary, "state": "requires_review", "findings": []}

    panel_ids = {condition.id for condition in panel.conditions}
    statuses = {code: finding for finding, code in FINDINGS.items()}
    findings = {}
    result = report.get("result", [])
    if not result or len(result) != len(resources):
        raise ValueError("The FHIR report is missing its referenced observations")
    for item in result:
        match = re.fullmatch(r"Observation/([A-Za-z0-9.\-]{1,64})", item["reference"])
        if not match:
            raise ValueError("Expected an Observation reference on this server")
        observation_id = match[1]
        observation = resources.pop(("Observation", observation_id))
        target = [
            code_from(component.get("valueCodeableConcept", {}), f"{SYSTEM}/condition")
            for component in observation.get("component", [])
            if code_from(component["code"], f"{SYSTEM}/component") == "synthetic-screening-target"
        ]
        finding = statuses.get(code_from(observation.get("valueCodeableConcept", {}), "http://loinc.org"))
        if (
            len(target) != 1 or target[0] not in panel_ids or target[0] in findings
            or finding is None
            or observation["status"] not in {"final", "amended", "corrected"}
            or code_from(observation["code"], "http://loinc.org") != "69548-6"
        ):
            return {**summary, "state": "requires_review", "findings": []}
        findings[target[0]] = {"condition_id": target[0], "status": finding, "source_id": observation_id}
    visible = [finding for finding in findings.values() if finding["status"] != "uncertain"]
    state = "ready" if len(visible) == len(findings) else "requires_review"
    return {**summary, "state": state, "findings": visible}


def register(app, *, base_url, db_session, roles, own, limit):
    panel = load_panel()

    @app.post("/api/me/imports/fhir/preview")
    def preview(identity=Depends(roles("person")), db: Session = Depends(db_session)):
        own(db, identity, "sandbox_report", {"status", "brief"})
        limit(db, identity)
        patient_id = ASSIGNED.get(identity.actor.id)
        if patient_id is None:
            raise HTTPException(404, "Synthetic FHIR fixture unavailable")
        try:
            with httpx.Client(
                base_url=base_url.rstrip("/") + "/", timeout=5, trust_env=False,
                headers={"accept": "application/fhir+json"},
            ) as client:
                result = read_preview(client, patient_id, panel)
        except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError):
            raise HTTPException(502, "The synthetic FHIR report could not be verified") from None
        return {**result, "is_synthetic": True}

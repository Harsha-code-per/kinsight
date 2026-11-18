"""Report revision and release contract for the synthetic integration sandbox."""

import json
from collections.abc import Iterable
from typing import Annotated, Literal

from pydantic import AwareDatetime, Field, model_validator

from .schemas import Alias, StrictModel

SyntheticId = Annotated[Alias, Field(pattern=r"^synthetic-[A-Za-z0-9_-]+$")]
FindingStatus = Literal["carrier", "not_detected", "uncertain", "not_tested"]
FHIR_STATUS = {
    "registered": "preliminary",
    "partial": "preliminary",
    "preliminary": "preliminary",
    "final": "final",
    "amended": "amended",
    "corrected": "corrected",
    "appended": "amended",
    "cancelled": "cancelled",
    "entered-in-error": "entered-in-error",
}


class ReportRevision(StrictModel):
    subject_id: SyntheticId
    report_id: SyntheticId
    revision: Annotated[int, Field(ge=1)]


class ScreeningReport(ReportRevision):
    is_synthetic: bool
    issued_at: AwareDatetime
    panel_version: Alias
    status: Literal["preliminary", "final", "amended", "corrected", "cancelled", "entered-in-error"]
    findings: Annotated[
        dict[Alias, FindingStatus], Field(max_length=100)
    ]

    @model_validator(mode="after")
    def validate_report(self):
        if not self.is_synthetic:
            raise ValueError("Only synthetic reports are accepted")
        if self.status in {"final", "amended", "corrected"} and not self.findings:
            raise ValueError("A completed report needs explicit findings")
        return self


def current_report(
    subject_id: str,
    report_id: str,
    reports: Iterable[ScreeningReport],
    approval: ReportRevision | None,
) -> tuple[Literal["missing", "pending", "withdrawn", "released"], ScreeningReport | None]:
    """Resolve one authorized subject and report stream against a separate clinician approval."""
    revisions: dict[int, ScreeningReport] = {}
    for report in reports:
        if (report.subject_id, report.report_id) != (subject_id, report_id):
            continue
        if revisions.setdefault(report.revision, report) != report:
            raise ValueError("Conflicting copies of a report revision")
    if not revisions:
        return "missing", None

    latest = revisions[max(revisions)]
    if latest.status in {"cancelled", "entered-in-error"}:
        return "withdrawn", None
    if latest.status == "preliminary" or approval != ReportRevision(
        subject_id=subject_id, report_id=report_id, revision=latest.revision
    ):
        return "pending", None
    return "released", latest


def from_synthetic_fhir(
    resource: dict,
    *,
    subject_id: str,
    revision: int,
    panel_version: str,
    findings: dict[str, str],
) -> ScreeningReport:
    """Map sandbox DiagnosticReport metadata with an independently supplied lab interpretation."""
    subject = resource.get("subject")
    if (resource.get("resourceType") != "DiagnosticReport" or not isinstance(subject, dict)
            or subject.get("reference") != f"Patient/{subject_id}"):
        raise ValueError("Expected a sandbox report for the mapped subject")
    meta = resource.get("meta")
    tags = meta.get("tag") if isinstance(meta, dict) else None
    if not isinstance(tags, list) or not any(
        isinstance(tag, dict) and tag.get("system") == "https://kinsight.example/tags" and tag.get("code") == "synthetic"
        for tag in tags
    ):
        raise ValueError("Expected a synthetic sandbox report tag")
    status, issued = resource.get("status"), resource.get("issued")
    if not isinstance(status, str) or not isinstance(issued, str):
        raise ValueError("Expected a report status and issuance time")

    return ScreeningReport.model_validate_json(json.dumps({
        "is_synthetic": True,
        "subject_id": subject_id,
        "report_id": resource.get("id"),
        "revision": revision,
        "panel_version": panel_version,
        "status": FHIR_STATUS.get(status),
        "issued_at": issued,
        "findings": findings,
    }))

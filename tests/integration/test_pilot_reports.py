from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from services.api.pilot_reports import ReportRevision, ScreeningReport, current_report, from_synthetic_fhir


def report(revision=1, status="final", **overrides):
    return ScreeningReport.model_validate({
        "subject_id": "synthetic-person-a",
        "report_id": "synthetic-report-a",
        "revision": revision,
        "is_synthetic": True,
        "issued_at": datetime(2026, 11, 18, tzinfo=timezone.utc),
        "panel_version": "synthetic-panel-v1",
        "status": status,
        "findings": {"synthetic-condition": "not_tested"},
        **overrides,
    })


def review(revision, **overrides):
    return ReportRevision.model_validate({
        "subject_id": "synthetic-person-a", "report_id": "synthetic-report-a", "revision": revision, **overrides
    })


def resolve(reports, approval=None):
    return current_report("synthetic-person-a", "synthetic-report-a", reports, approval)


def test_latest_amendment_needs_its_own_approval_even_with_out_of_order_delivery():
    first = report()
    amended = report(2, "amended", findings={"synthetic-condition": "uncertain"})
    assert resolve([first], review(1)) == ("released", first)
    assert resolve([amended, first, first], review(1)) == ("pending", None)
    assert resolve([amended, first], review(2, report_id="synthetic-other")) == ("pending", None)
    assert resolve([amended, first], review(2, subject_id="synthetic-other")) == ("pending", None)
    assert resolve([amended, first], review(2)) == ("released", amended)


def test_missing_preliminary_and_withdrawn_are_distinct_and_have_no_findings():
    assert resolve([report(subject_id="synthetic-person-b")], review(1)) == ("missing", None)
    assert resolve([report(status="preliminary", findings={})], review(1)) == ("pending", None)
    assert resolve([report(), report(2, "entered-in-error", findings={})], review(2)) == ("withdrawn", None)


def test_conflicting_revisions_require_reconciliation():
    with pytest.raises(ValueError, match="Conflicting copies"):
        resolve([report(), report(findings={"synthetic-condition": "carrier"})], review(1))


@pytest.mark.parametrize("overrides", [
    {"is_synthetic": False}, {"is_synthetic": 1}, {"subject_id": "real-patient"}, {"findings": {}},
    {"issued_at": datetime(2026, 11, 18)}, {"patient_name": "extra field"},
])
def test_sandbox_rejects_input_outside_contract(overrides):
    with pytest.raises(ValidationError):
        report(**overrides)


def test_synthetic_fhir_releases_only_the_reviewed_revision():
    resource = {
        "resourceType": "DiagnosticReport",
        "id": "synthetic-report-a",
        "subject": {"reference": "Patient/synthetic-person-a"},
        "meta": {"tag": [{"system": "https://kinsight.example/tags", "code": "synthetic"}], "versionId": "opaque"},
        "status": "final",
        "issued": "2026-11-18T10:00:00+05:30",
    }
    mapping = {"subject_id": "synthetic-person-a", "panel_version": "synthetic-panel-v1"}
    first = from_synthetic_fhir(resource, revision=1, findings={"test-condition": "not_detected"}, **mapping)
    corrected = from_synthetic_fhir({**resource, "status": "corrected"}, revision=2,
                                    findings={"test-condition": "uncertain"}, **mapping)
    assert resolve([first], review(1)) == ("released", first)
    assert resolve([corrected, first], review(1)) == ("pending", None)
    assert resolve([corrected], review(2)) == ("released", corrected)
    with pytest.raises(ValueError, match="mapped subject"):
        from_synthetic_fhir(resource, revision=1, findings={}, **{**mapping, "subject_id": "synthetic-other"})
    with pytest.raises(ValueError, match="synthetic sandbox report tag"):
        from_synthetic_fhir({**resource, "meta": {}}, revision=1, findings={}, **mapping)
    with pytest.raises(ValidationError):
        from_synthetic_fhir({**resource, "status": "unknown"}, revision=3, findings={}, **mapping)

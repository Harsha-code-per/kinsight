"""Export or upload reproducible FHIR R4 transactions from the checked-in synthetic cohort."""

import argparse
import gzip
import json
from pathlib import Path

import httpx
from fhir.resources.R4B.bundle import Bundle

from services.cohort.fhir import FINDINGS, SYSTEM, TAG

COHORT = Path(__file__).resolve().parents[1] / "data" / "demo"
INITIAL_ISSUED = "2026-01-01T10:00:00Z"
CORRECTED_ISSUED = "2026-01-02T10:00:00Z"
MEDIA = "application/fhir+json"


def cohort_rows(name):
    with gzip.open(COHORT / f"{name}.jsonl.gz", "rt", encoding="utf-8") as source:
        for line in source:
            row = json.loads(line)
            if row.get("is_synthetic") is not True:
                raise ValueError(f"The {name} source contains a row without the synthetic marker")
            yield row


def concept(system, code):
    return {"coding": [{"system": system, "code": code}]}


def reference(relative_id):
    return {"reference": relative_id}


def entry(kind, identifier, **fields):
    return {
        "resource": {"resourceType": kind, "id": identifier, "meta": {"tag": [TAG]}, **fields},
        "request": {"method": "PUT", "url": f"{kind}/{identifier}"},
    }


def transaction(entries):
    result = {"resourceType": "Bundle", "type": "transaction", "meta": {"tag": [TAG]}, "entry": entries}
    Bundle.model_validate(result)
    return result


def build_bundles():
    couples = list(cohort_rows("couples"))[:2]
    people = {couple[key]: [] for couple in couples for key in ("person_a", "person_b")}
    for result in cohort_rows("screening_results"):
        if result["person_id"] in people:
            people[result["person_id"]].append(result)
    bundles = []
    correction = None
    for number, couple in enumerate(couples, 1):
        entries = []
        for side, other in (("a", "b"), ("b", "a")):
            original_id = couple[f"person_{side}"]
            patient_id = "ks-demo-" + original_id
            patient = reference(f"Patient/{patient_id}")
            label = f"KinSight Fixture {number}{side.upper()}"
            entries.append(entry("Patient", patient_id, active=True, name=[{"text": label}]))
            entries.append(entry(
                "RelatedPerson", patient_id, patient=patient, active=True,
                name=[{"text": f"KinSight Fixture {number}{other.upper()}"}],
                relationship=[concept("http://terminology.hl7.org/CodeSystem/v3-RoleCode", "DOMPART")],
            ))
            entries.append(entry(
                "Consent", patient_id, patient=patient, status="draft",
                scope=concept("http://terminology.hl7.org/CodeSystem/consentscope", "patient-privacy"),
                category=[concept(f"{SYSTEM}/consent", "synthetic-example")],
            ))
            observations = []
            for result in sorted(people[original_id], key=lambda row: row["condition_id"]):
                condition = result["condition_id"]
                observation_id = f"{patient_id}-{condition.lower().replace('_', '-')}"
                observations.append(entry(
                    "Observation", observation_id, subject=patient, status="final",
                    category=[concept("http://terminology.hl7.org/CodeSystem/observation-category", "laboratory")],
                    code=concept("http://loinc.org", "69548-6"),
                    valueCodeableConcept=concept("http://loinc.org", FINDINGS[result["status"]]),
                    component=[{
                        "code": concept(f"{SYSTEM}/component", "synthetic-screening-target"),
                        "valueCodeableConcept": concept(f"{SYSTEM}/condition", condition),
                    }],
                ))
            if not observations:
                raise ValueError(f"Missing synthetic observations for fixture {number}{side.upper()}")
            report = entry(
                "DiagnosticReport", patient_id, subject=patient, status="final",
                code=concept(f"{SYSTEM}/panel", people[original_id][0]["panel_version"]),
                issued=INITIAL_ISSUED,
                result=[reference(observation["request"]["url"]) for observation in observations],
            )
            entries.extend([*observations, report])
            if correction is None:
                observed = observations[0]["resource"]
                changed = "carrier" if observed["valueCodeableConcept"] == concept("http://loinc.org", FINDINGS["uncertain"]) else "uncertain"
                correction = transaction([
                    {**observations[0], "resource": {**observed, "status": "corrected",
                                                     "valueCodeableConcept": concept("http://loinc.org", FINDINGS[changed])}},
                    {**report, "resource": {**report["resource"], "status": "corrected", "issued": CORRECTED_ISSUED}},
                ])
        bundles.append((f"couple-{number}", transaction(entries)))
    if correction is None:
        raise ValueError("The synthetic cohort contains no couples to export")
    return bundles, correction


def upload(client, bundles, *, require_existing=False):
    capability = client.get("metadata").raise_for_status().json()
    if capability.get("resourceType") != "CapabilityStatement" or capability.get("fhirVersion") != "4.0.1":
        raise ValueError("The sandbox must advertise FHIR R4 version 4.0.1")
    for name, bundle in bundles:
        if require_existing:
            entries = []
            for item in bundle["entry"]:
                current = client.get(item["request"]["url"]).raise_for_status()
                resource = current.json()
                etag = current.headers.get("etag")
                if TAG not in resource.get("meta", {}).get("tag", []) or resource.get("status") != "final" or not etag:
                    raise ValueError("A correction requires a seeded final resource with a server version")
                entries.append({**item, "request": {**item["request"], "ifMatch": etag}})
            bundle = {**bundle, "entry": entries}
        response = client.post("", json=bundle).raise_for_status().json()
        outcomes = response.get("entry", [])
        if response.get("resourceType") != "Bundle" or response.get("type") != "transaction-response" or (
            len(outcomes) != len(bundle["entry"]) or any(
                outcome.get("response", {}).get("status", "").split(" ", 1)[0] not in {"200", "201"}
                for outcome in outcomes
            )
        ):
            raise ValueError(f"{name} did not return a complete successful FHIR transaction")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    destination = parser.add_mutually_exclusive_group(required=True)
    destination.add_argument("--out", type=Path, help="Write initial and corrected JSON transactions here")
    destination.add_argument("--upload", help="FHIR R4 sandbox base URL")
    parser.add_argument("--correction", action="store_true", help="Upload only the corrected report transaction after seeding")
    args = parser.parse_args()
    if args.correction and not args.upload:
        parser.error("--correction requires --upload")
    bundles, correction = build_bundles()
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        for name, bundle in [*bundles, ("correction", correction)]:
            (args.out / f"{name}.json").write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    else:
        try:
            with httpx.Client(
                base_url=args.upload.rstrip("/") + "/", timeout=60,
                headers={"accept": MEDIA, "content-type": MEDIA},
            ) as client:
                upload(client, [("correction", correction)] if args.correction else bundles, require_existing=args.correction)
        except (ValueError, httpx.HTTPError) as exc:
            parser.exit(1, f"FHIR seed failed: {exc}\n")
        if args.correction:
            print("Applied correction to " + correction["entry"][-1]["request"]["url"])
            return
    for name, bundle in bundles:
        print(name + ": " + ", ".join(
            item["request"]["url"] for item in bundle["entry"] if item["resource"]["resourceType"] == "Patient"
        ))


if __name__ == "__main__":
    main()

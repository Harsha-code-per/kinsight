# KinSight real-data rollout

## Decision

The early-review feedback calls for a working laboratory feed, EHR/FHIR integration, and report parsing for synthetic cases. KinSight currently has fictional personas, hard-coded case and couple aliases in the API client, and an API that labels its results synthetic. `NEXT_PUBLIC_MOCK=0` changes the transport to HTTP. A learning model cannot establish identity, retrieve a lab report, or determine which revision a clinician approved. [Judge feedback and tracking issue](https://github.com/loktrishal-05/kinsight/issues/65)

The opt-in lab sandbox now demonstrates synthetic report intake, consent and approval, and correction handling in the app. The independently hosted FHIR sandbox, EHR import, HL7 v2 feed, tracker integration, and document parsing remain separate submission tasks. The deployed result pages still use the demo backend. [FHIR sandbox](https://github.com/loktrishal-05/kinsight/issues/32) · [FHIR import](https://github.com/loktrishal-05/kinsight/issues/28) · [Lab feed](https://github.com/loktrishal-05/kinsight/issues/30) · [Report parsing](https://github.com/loktrishal-05/kinsight/issues/31)

Start with one clinic, one lab, one supported panel and one reviewed language. The first pilot should display clinician-released reports and a clinician-reviewed couple summary after both partners consent. Treat missing coverage, ambiguous findings and an unavailable partner report as distinct states. ACMG and ACOG describe residual risk after a screen with no detected finding. Preserve that distinction and avoid producing a numerical estimate unless the clinical team validates the panel, inputs and calculation for the intended use. [ACMG carrier-screening practice resource](https://www.nature.com/articles/s41436-021-01203-z) · [ACOG carrier screening](https://www.acog.org/clinical/clinical-guidance/committee-opinion/articles/2017/03/carrier-screening-in-the-age-of-genomic-medicine)

## Findings and order of work

| Priority | Evidence in this repository | Work |
| --- | --- | --- |
| P0 | `/signin` accepted arbitrary credentials. Demo token issuance had an enable flag, while token verification did not. | Replace the credential form with explicit demo entry and reject existing demo tokens when the flag is off. |
| P0 | The client uses `demo-case`, `demo-couple` and a second fictional persona token. The API schema requires synthetic results. | Build pilot authentication and account-scoped APIs. Map the validated issuer and subject to the clinic’s patient identifier. Use server-side membership for case lookup and check both partners’ consent per shared read. [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html#ClaimStability) · [OAuth security best current practice](https://www.rfc-editor.org/rfc/rfc9700.html) |
| P0 | The lab tracker simulates progress and `services/agents/fhir.py` exports synthetic referral status. There is no inbound report connector. | Agree on test report examples and a provider contract. Map report identity, subject, findings, timestamps and correction or withdrawal states. Use HL7 FHIR R4 Genomics Reporting if the lab supports it. [HL7 Genomics Reporting](https://hl7.org/fhir/uv/genomics-reporting/general.html) |
| P0 | The API client rendered failed couple-assessment responses as waiting for consent. | Fixed the transport distinction and preserved redacted findings. The existing API keeps a generic access denial as a privacy boundary. Add explicit report and consent states for verified pilot members. |
| P0 | Demo output and rule files use a fictional panel and assumptions. | Start with a clinician release decision per report revision and per couple summary. Revoke stale release on correction or withdrawal. Keep the demo arithmetic out of pilot assessments until independently validated. |
| P0 | The web dependency audit flagged critical Next.js advisories and vulnerable Zod, PostCSS and Playwright versions. | Upgraded the dependencies in the working tree. The production audit reports zero vulnerabilities after the upgrade. Keep dependency review and browser checks in the pilot release process. [Next.js advisory](https://github.com/advisories/GHSA-2464-fhr4-w9xw) · [Web licence inventory](LICENSES.md) |
| P1 | Public ClinVar and gnomAD lookup is reference enrichment. | Use approved, versioned references only when the clinical workflow requires them. ClinVar aggregates submissions and can represent conflicting classifications. It supplies no evidence that an individual was tested. [NCBI ClinVar classifications](https://www.ncbi.nlm.nih.gov/clinvar/docs/clinsig/) |
| P1 | The volunteer study tooling exists. Clinical and language review are pending. | Agree on intended use, jurisdiction, permitted data flows, retention and a named clinical owner. Run comprehension and safety reviews with the host before release. [WHO human genome data governance](https://www.who.int/publications/i/item/9789240102149) · [Existing pilot readiness checklist](PILOT_READINESS.md) |

## Schedule and acceptance gates

The first row is complete in this working tree. The remaining windows are engineering estimates. The staging clock starts when the host supplies test credentials, a sandbox feed and approved report examples. Approval and partner lead time are outside the estimates.

| Window | Deliverable | Acceptance |
| --- | --- | --- |
| Start here | Demo boundary fixes and synthetic report-revision contract. | Demo entry collects no credentials. Disabling demo authentication stops issued demo tokens. Synthetic pending, approved, amended and withdrawn revisions are exercised. |
| Staging week 1 | Clinic identity, account-to-patient mapping and provider-specific report mapping. | Two partner accounts and an unrelated account authenticate independently. Unknown and mismatched patient references fail closed. |
| Staging week 2 | Persist and reconcile lab reports. Wire the personal result view to the latest clinician-released revision and display source and update time. | Pending, missing, partial, corrected, withdrawn, duplicate and out-of-order inputs work end to end. Never show the older approved result after a newer revision arrives. Track source delay and show freshness or unavailability. Start with refresh on open and explicit refresh. Add push or polling when the lab agrees on update latency. |
| Staging week 3 | Pairing, separate partner consent, clinician-reviewed couple summary and audit. | Either partner can revoke immediately. An unrelated account cannot read the case. Corrections invalidate the couple summary and alert its reviewer. Staging demonstrates both accounts seeing a corrected release. |
| Pilot gate | Clinic acceptance, privacy and jurisdiction review, security and recovery checks, reviewed wording and supervised release. | Host signs off. Run a correction drill, test access and retention controls, validate result fidelity against the lab, and agree on response times and stop criteria. |

## Training decision

No model is required for the first pilot. Use the lab’s structured interpretations and clinician-approved wording. A later model experiment needs a concrete task, such as drafting explanations from approved facts, and a measured improvement over templates. Evaluate factual fidelity, omissions, unsupported claims, escalation and comprehension by language on a held-out clinician-reviewed set. Use public or synthetic examples for Colab or Kaggle experiments. Keep identifiable lab reports in the host’s approved environment.

## Run the first integration check

From the repository root, run `python -m pytest -q tests/integration/test_pilot_reports.py tests/unit/test_consent_auth.py`. The report contract in `services/api/pilot_reports.py` is an executable synthetic integration slice. It models one report stream, assumes the source supplies a monotonic revision, and matches approval to the latest subject, report and revision. Production source ordering, persistence, release authorization and web integration depend on the agreed host contract.

`from_synthetic_fhir` accepts a synthetic-tagged `DiagnosticReport` with the expected relative patient reference, report status and issued timestamp. The caller supplies a numeric revision from the feed contract and separately mapped lab interpretations. Select the revision from the ordered source feed because FHIR `meta.versionId` can be opaque. The mapping is exercised with final and corrected reports. Public HL7 examples are useful for structural checks and Synthea can supply broader synthetic encounter scenarios. [FHIR R4 DiagnosticReport](https://hl7.org/fhir/R4/diagnosticreport.html) · [FHIR resource metadata](https://hl7.org/fhir/R4/resource.html#Meta) · [Synthea](https://synthetichealth.github.io/synthea/)

The live ClinVar and gnomAD adapters returned data for the public demo variant IDs on 2026-11-18. Their upstream error envelopes now fail as unavailable instead of producing an empty lookup. The [data source inventory](../DATA_SOURCES.md) documents their role and provenance.

## Run the lab sandbox

Start the API with the normal local demo settings, `KINSIGHT_DEMO=1`, `KINSIGHT_DEMO_AUTH=1` and `KINSIGHT_LAB_SANDBOX=1`. Start the web app with `NEXT_PUBLIC_MOCK=0`, `NEXT_PUBLIC_LAB_SANDBOX=1`, and `KINSIGHT_API_URL` pointing to that API. Open **Lab report sandbox** from Home.

1. As Person A, select **Share for review**. The grant expires after one hour and can be revoked from Consents.
2. As the demo operator, send revision 1 for Person A. The intake posts a bounded synthetic FHIR `DiagnosticReport` and two labelled sample findings.
3. As the counsellor, open Person A’s report and approve the revision. Person A’s open page checks for updates every five seconds. Person B can see only their own report.
4. Send revision 2 as a correction. Person A sees a pending state until the counsellor approves revision 2.

Use a fresh local database for the browser test. The sandbox routes are off by default. Writes use the existing demo-operator role. The intake accepts two fixed synthetic participants, two fictional condition identifiers, and a narrow report shape. Approvals and revisions persist in the database. No patient upload form is part of this workflow.

## Compare existing lab reports

The public `/report-compare` page accepts text-based PDFs, TSV and TXT files through a picker or drag and drop. It reads files locally. Structured text files and the verified Labcorp negative SMA and Fragile X carrier-screen summaries can supply suggested findings. The participant checks the imported rows against the original before comparing. Other PDF layouts show a text preview for manual entry. PDF reading order can differ from the visual table and image-only sections can be missing. Use only the findings and avoid copying identifiers. The supported columns are gene, condition, reported result, and optional details such as assay coverage, a variant, a copy count, or a repeat count. Scans, photos, and locked PDFs need manual entry. The page accepts up to 1,000 findings per report and preserves multiple findings for a gene and condition. [Labcorp examples](https://www.labcorp.com/womens-health/providers/resources/sample-reports)

This tool aligns explicitly entered rows by the same gene set and condition label. It distinguishes a missing entry from a reported finding and leaves the labs’ wording intact. The chart filters the entered rows by which report contains them. The guided questions explain exact report terms, differences in panel coverage, and questions to bring to a counsellor. The downloaded public index provides local MedlinePlus links. The comparison supplies no independent patient result or reproductive risk estimate. [ACMG carrier screening practice resource](https://pmc.ncbi.nlm.nih.gov/articles/PMC8488021/) · [MedlinePlus result terminology](https://medlineplus.gov/genetics/understanding/testing/interpretingresults/) · [Data source inventory](../DATA_SOURCES.md)

Run `python scripts/update_report_references.py` from the repository root to refresh the public gene and condition link index. It downloads the source catalogue and writes URL slugs only. The comparison operates in memory and does not send report files or text to the API. A browser test covers PDF reading, preserved findings, validation, and clearing inputs. Authenticated clinical intake, lab-specific document validation, patient identity checks, and audited clinical review remain required for a hosted clinical workflow.

## Remaining integration work

| Order | Scope | Acceptance check |
| --- | --- | --- |
| 1 | Report intake and explanation. Local attachment, verified text import, two bounded PDF summaries, and the comparison guide are implemented. Photo OCR and additional lab layouts remain open. | Each additional layout has public or approved fixtures and tests showing that ambiguous sections, partner identity, and lab wording survive review. [Issue 31](https://github.com/loktrishal-05/kinsight/issues/31) |
| 2 | Seed a hosted synthetic FHIR source and connect EHR import. | Each signed-in sandbox account resolves only its assigned report and refreshes on a corrected resource. [Issues 32](https://github.com/loktrishal-05/kinsight/issues/32) · [28](https://github.com/loktrishal-05/kinsight/issues/28) |
| 3 | Add the external lab-feed and tracker path. | An authenticated lab event updates the tracker and a corrected result returns to counsellor review. [Issue 30](https://github.com/loktrishal-05/kinsight/issues/30) |
| 4 | Complete the wider evaluator backlog and clinical pilot gates. | Verify the remaining feedback items against the hosted build and record clinical sign-off separately. [Issue 65](https://github.com/loktrishal-05/kinsight/issues/65) |

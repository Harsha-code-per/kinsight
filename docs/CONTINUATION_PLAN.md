# KinSight continuation plan

## Resume here

Start from the latest `origin/main` and check the latest `ci` workflow run. Check open issue descriptions again for new decisions or ownership. Start with **#28**, the EHR import. Use the local HAPI fixture for report and Observation mapping, including a correction, an unknown target, and mismatched subject references. Resolve the patient assignment server-side and verify consent and audit before exposing a review screen. Hosted acceptance requires a designated test server and SMART sandbox credentials. [Open issues](https://github.com/loktrishal-05/kinsight/issues) · [Latest CI](https://github.com/loktrishal-05/kinsight/actions/workflows/ci.yml)

## Work shipped so far

| Issues | Evidence on main | Remaining acceptance |
| --- | --- | --- |
| #32 | Reproducible transactions for two synthetic couples, a local Docker HAPI R4 sandbox, and a version-checked correction. The live test checks that subject-filtered searches return their respective records. | An approved hosted sandbox and application-side authorization through #28. |
| #30 | Signed synthetic lab events drive the Journey tracker. Consent and counsellor approval control release per revision. A corrected report returns to review. | HL7 v2 ORU ingestion, hosted delivery and provider verification. |
| #31, #33 | Browser-local attachment and review, two verified PDF layouts, a filterable comparison chart, guided questions and MedlinePlus links. | Photo OCR, wider report layouts, more verified examples, and the other public reference integrations. |
| #42, #43 | Tests exercise optional lab-route authentication, field projection, revocation, audit integrity and live audit tamper detection. | Inventory every API route and verify the policy or explicit exception for each one. Recheck the hosted tamper exercise before closing #43. |
| #58, #61, #62 | Corrected the report wording that broke CI, upgraded Next.js and React dependencies in earlier work, and removed outdated README badges. | Recheck release and CI evidence and finish the audit gates and documentation audit. |

The issue tracker remains open. Reproduce each acceptance criterion before calling the corresponding issue complete.

## Order after the first fixture

| Order | Issues | Acceptance |
| --- | --- | --- |
| 1 | #32, #28, #30, #29, #31, #33, #34 | Exercise synthetic EHR import, hosted lab delivery and closed-loop referral status with scoped accounts. Add supported document and reference sources with verified examples. |
| 2 | #40, #41, #42, #43, #60, #58, #59, #61 | Prove revision-gated release, audit and consent coverage, consistent labels for estimates, application hardening and CI checks before expanding clinical workflows. |
| 3 | #35, #36, #37, #38, #39, #54, #55 | Wire grounded questions, counselling preparation, family workflows, and service connections to scoped data. Verify revocation and content-free reminders. |
| 4 | #47, #48, #49, #50, #51, #52, #53, #56 | Verify person, counsellor and analyst workflows on mobile and desktop, including keyboard and RTL behavior. |
| 5 | #57, #62, #63, #44, #45, #46, #64, #65 | Confirm hosting and contributor documentation. Collect approved study evidence and reviewer sign-off. Verify the hosted build and assemble submission material from actual results. |

Clinic or lab access, recruitment and study approval, clinical and language review, and hosted acceptance require coordination outside the repository. Use synthetic fixtures or approved public examples for development. Login with real patient identity and hosted clinical report processing remain outside the verified build. See [real-data rollout](REAL_DATA_ROLLOUT.md) for the lab commands, source references and production gates.

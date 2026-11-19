# KinSight continuation plan

## Resume here

Start from the latest `origin/main` and check the latest `ci` run. Continue **#41** by tracing risk values from API responses to the couple, clinic and printable views, then enforce a common educational estimate label. In parallel, **#28** needs an approved SMART sandbox, a registered OAuth client, and an identity binding from the validated launch to the clinic patient. Run the consent, correction and release checks against that provider before enabling hosted imports. [Open issues](https://github.com/loktrishal-05/kinsight/issues) · [Latest CI](https://github.com/loktrishal-05/kinsight/actions/workflows/ci.yml)

## Work shipped so far

| Issues | Evidence on main | Remaining acceptance |
| --- | --- | --- |
| #32 (closed) | Reproducible transactions for two synthetic couples, a local Docker HAPI R4 sandbox, and a version-checked correction. The live test checks that subject-filtered searches return their respective records. | Hosted deployment and SMART integration are tracked under #28. |
| #28 | Opt-in HAPI preview with server-side demo account mapping and source IDs. Version-bound confirmation persists locally, grants revocable counsellor access, and withholds stale releases. | SMART patient context, validated clinical panel mapping and hosted browser acceptance. |
| #30 | Signed HL7 v2 ORM orders, ORU results and FHIR bundles drive the synthetic Journey tracker. The existing consent and counsellor gate controls each revision. | Hosted delivery and provider verification. |
| #31, #33 | Browser-local attachment and review, two verified PDF layouts, a filterable comparison chart, guided questions and MedlinePlus links. | Photo OCR, wider report layouts, more verified examples, and the other public reference integrations. |
| #42, #43 (closed) | The full route inventory checks default and opt-in routes, including a failing unguarded-route example. Property tests cover role, active grants, field projection, revocation and auditing. The deployed tamper example reports the broken synthetic entry. | Apply the route inventory to new integrations as they ship. |
| #56 (closed) | The language menu ships seven packs, the README badge is checked against the manifest, and Kin tests cover all seven languages, including mixed scripts. | Independent review of translated wording is tracked in #45. |
| #57 (closed) | GitHub recognizes the contributor policy, issue templates, pull request template and CODEOWNERS. Private vulnerability reporting and Dependabot alerts are enabled. | Keep verified write-access owners current. |
| #58, #61 | Updated Next.js, React and the web test dependencies. CI runs Python and web suites, the HAPI round trip, and a blocking npm audit. Actions are pinned, and Dependabot updates are grouped. | Add remaining CodeQL, secret-scan and coverage gates, resolve Python audit policy, and record Lighthouse comparisons. |
| #62 (closed) | Removed stale reported totals, linked the generated scorecard and CI, corrected licence and hosting notes, and recorded the architecture decisions. | Update the changelog and traceability table when milestones ship. |

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

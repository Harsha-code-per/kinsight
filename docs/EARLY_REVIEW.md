# Early review traceability

| Reviewer request | Verified repository behavior | Remaining acceptance |
| --- | --- | --- |
| Integrate lab and EHR data | A signed synthetic lab feed updates Journey. A synthetic HAPI report can be confirmed, shared, approved and checked for corrections. [Integration CI](https://github.com/loktrishal-05/kinsight/actions/runs/44468438301) | Hosted SMART patient context, provider validation, HL7 v2, and referral write-back. |
| Read uploaded reports | The browser can compare reviewed findings from supported text PDFs and structured text uploads. [Report comparison](REAL_DATA_ROLLOUT.md#compare-existing-lab-reports) | Photo OCR and validation across more panels and laboratory layouts. |
| Prepare families for counselling | The demo has a deterministic assistant, educational comparisons, and consent-controlled family invitation tools. [Architecture and decisions](architecture.md) | Tailored prep sheets, broader family workflow and scenario acceptance checks. |
| Preserve privacy and clinical review | Synthetic reported results use server-side identity mapping and revocable sharing. Review and release track the source revision. The deployed audit example identifies the tampered entry. [Audit verification](https://github.com/loktrishal-05/kinsight/issues/43) | Full risk-label coverage, unified review acceptance, external clinical review, and hosted pilot checks. |
| Demonstrate impact | The reproducible scorecard records synthetic and simulated evidence. [Scorecard](internal/SCORECARD.md) | Recruitment, study data, and independent clinical and language review. |

The [continuation plan](CONTINUATION_PLAN.md) tracks issue-level verification and external dependencies.

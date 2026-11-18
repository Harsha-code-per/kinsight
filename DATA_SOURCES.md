# Data sources
| Source | Licence | Real/Synthetic | Accessed | Use |
|---|---|---|---|---|
| Synthetic cohort (services/cohort, seed in configs/cohort.yaml) | Project (own) | Synthetic | generated | All people and results |
| configs/panel.yaml (fictional conditions, illustrative frequencies) | Project (own) | Synthetic | 2026-10-25 | Condition panel |
| Consanguinity shares in cohort.yaml | Dated figures cited in the spec (1990s UAE study) | Public statistic, illustrative | 2026-10-25 | Generator defaults only |
| [NCBI ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/docs/maintenance_use/) | NCBI site terms and submitter conditions | Public variant classifications | Live lookup verified 2026-11-18 | Variant explorer and reference reclassification checks |
| [gnomAD v4](https://gnomad.broadinstitute.org/news/2024-04-gnomad-v4-1) | Broad Institute data terms | Public aggregate allele counts | Live lookup verified 2026-11-18 | Population frequency lookup |
| [HL7 FHIR R4 DiagnosticReport](https://hl7.org/fhir/R4/diagnosticreport.html) | [HL7 FHIR specification licence](https://hl7.org/fhir/R4/license.html) | Standard with published examples | 2026-11-18 | Format reference for locally written synthetic intake cases |

KinSight sends public variant identifiers or gene symbols for reference lookups. Personal screening results require a report issued by the care provider and linked to the patient. KinSight’s demo stores fictional people and results. [NCBI ClinVar submission rules](https://www.ncbi.nlm.nih.gov/clinvar/docs/submission_instructions/) · [gnomAD population data](https://gnomad.broadinstitute.org/news/2023-11-genetic-ancestry)

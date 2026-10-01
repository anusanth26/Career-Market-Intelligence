# Role-Mapping Precision Audit (10 core roles)

**Date:** 2026-09-30. **Result: 9 of 10 core roles pass the 90% precision bar; Project Manager fails (85.0%).** The mapping rules were **not modified**; proposed changes are listed in section 7.

## 1. Method

- **Population:** the clean postings of each core role from the feasibility data (official strict rules in `config/roles.json`; deduplicated, employer-capped), i.e. the exact set the dataset design counts.
- **Precision sample:** 50 titles per role, drawn with a fixed seed (`20260930`, combined with the role name; `data/raw/ml_data_feasibility/mapping_precision_sample.py`). Samples: `mapping_precision/samples.json`.
- **Recall probe:** 30 unmatched titles (Business Analyst, Project Manager, Data Analyst, Graphic Designer) or 15 (the other six roles), drawn from titles that the role's own queries returned but that matched no role.
- **Labels:** assigned **manually** against a rubric written before labelling (`mapping_precision_labels.py` docstring):
  - **correct:** the title clearly names the role;
  - **ambiguous:** a documented synonym or variant that is a materially different or debatable job (scrum master, ERP functional analyst, product owner, ML engineer), a hybrid title, or a people-manager role;
  - **incorrect:** matched a pattern, but the job is a different family (or is meant to be excluded).
- **Precision** = correct ÷ (correct + incorrect). **Ambiguity rate** = ambiguous ÷ 50. I also report a *strict* precision (ambiguous counted as wrong), and where a family could be defined into the role by a team decision, a *lenient* precision.
- **No classifier was trained and the mapping code did not label its own output.** The reviewer was an AI assistant; the labels are judgement calls, saved with reason codes in `mapping_precision/labels.csv`. **A team member must independently re-label at least 15 titles per role and report agreement** before the results are treated as final.
- **Limits:** n = 50 per role gives wide intervals (Wilson 95% intervals below). Recall figures describe the *unmatched pool* of titles (distinct titles), not the overall postings.

## 2. Results

| Role | Correct | Ambiguous | Incorrect | **Precision** | 95% interval | Ambiguity | Strict precision | Lenient precision | Canonical-title / synonym precision |
|---|---:|---:|---:|---:|---|---:|---:|---:|---|
| Software Engineer | 46 | 4 | 0 | **100%** | 92.3–100 | 8% | 92% | – | 100 / 100 |
| Data Analyst | 43 | 7 | 0 | **100%** | 91.8–100 | 14% | 86% | – | 100 / 100 |
| Data Scientist | 34 | 16 | 0 | **100%** | 89.8–100 | 32% | 68% | 100% (ML engineer counted in) | 100 / 100 |
| Data Engineer | 45 | 5 | 0 | **100%** | 92.1–100 | 10% | 90% | 100% (analytics engineer counted in) | 100 / 100 |
| DevOps / Cloud Engineer | 46 | 4 | 0 | **100%** | 92.3–100 | 8% | 92% | – | 100 / 100 |
| Business Analyst | 28 | 20 | 2 | **93.3%** | 78.7–98.2 | **40%** | 56% | 95.7% | 100 / 66.7 |
| Product Manager | 32 | 18 | 0 | **100%** | 89.3–100 | **36%** | 64% | 100% (product owner counted in) | 100 / – |
| **Project Manager** | 17 | **30** | 3 | **85.0%** | 64.0–94.8 | **60%** | 34% | 93.2% (program and delivery manager counted in) | 94.4 / 0 |
| Digital Marketing | 47 | 3 | 0 | **100%** | 92.4–100 | 6% | 94% | – | 100 / 100 |
| Graphic Designer | 36 | 11 | 3 | **92.3%** | 79.7–97.3 | 22% | 72% | – | 92.1 / 100 |

Note: for Data Scientist, Product Manager, Business Analyst, Graphic Designer and Project Manager the **lower 95% bound is below 90%**, so a pass on the point estimate is not a guarantee.

## 3. Gate check per role

The three requirements: precision ≥ 90%; clean postings ≥ 400; canonical-title postings ≥ 300 (canonical share from `config/career_scope.json`).

| Role | Precision ≥ 90% | Clean ≥ 400 | Canonical ≥ 300 | Passes all three | Advisory (not a stated criterion) |
|---|---|---|---|---|---|
| Software Engineer | Pass (100%) | 875 | 735 | **Pass** | – |
| Data Analyst | Pass (100%) | 473 | 432 | **Pass** | – |
| Data Scientist | Pass (100%) | 604 | 347 | **Pass** | 32% ambiguity (ML engineers) |
| Data Engineer | Pass (100%) | 410 | 328 | **Pass** | thin margin on clean (10 above) |
| DevOps / Cloud Engineer | Pass (100%) | 854 | 336 | **Pass** | – |
| Business Analyst | Pass (93.3%) | 663 | 366 | **Pass** | **40% ambiguity**; 15 of 16 "systems analyst" hits ambiguous or wrong |
| Product Manager | Pass (100%) | 628 | 366 | **Pass** | 36% ambiguity (all product owners) |
| **Project Manager** | **FAIL (85.0%)** | 932 | 311 | **FAIL** | 60% ambiguity |
| Digital Marketing | Pass (100%) | 555 | 348 | **Pass** | – |
| Graphic Designer | Pass (92.3%) | 443 | 377 | **Pass** | precision only 2.3 points above the bar; low text signal (see `dataset_design.md` section 14) |

## 4. False positives and ambiguous examples

| Role | False positives (incorrect) | Typical ambiguous titles |
|---|---|---|
| Software Engineer | none in sample | "Application Developer" (generic; may be packaged-software work), "Software Engineer Manager" |
| Data Analyst | none | "Data Analyst II (Sharepoint/PowerApps Developer)", "Lead Data Analyst - Cyber Incident Review", "Data Analyst, Stewardship" |
| Data Scientist | none | 15 "Machine Learning Engineer" titles, "Full-Stack AI Engineer / Data Scientist" |
| Data Engineer | none | "SAP Analytics Engineer (Datasphere)", "Manager- ETL Developer", "Data Engineer - Manager" |
| DevOps / Cloud | none | "Platform Engineer (Cybersecurity Platform)", "Senior Platform Engineer (SAP Basis Hana)" |
| Business Analyst | "Physical Security Systems Analyst", "Website Security Support - Product Analyst" | "System Analyst SAP", "HR Systems Analyst", "Workday System Analyst - HRIS", "Functional Analyst" |
| Product Manager | none | 17 "Product Owner" titles, "Customer Success & Product Manager" |
| **Project Manager** | "Service Delivery Manager", "Senior Service Delivery Manager - AMS", "Project Manager - Projects & Interiors" | 19 "Program Manager" (many Amazon/Google operations roles), 5 "Delivery Manager", 3 "Scrum Master" |
| Digital Marketing | none | "Work From Home Social Media Manager … Earn" (spam-like), "GTM Engineer – Performance Marketing" |
| Graphic Designer | "Motion Graphic Designer" ×2, "Motion Graphic Designer & Video Editor" | "Graphic Designer / 3D Visualizer / Video Editor", "Visual Designer" (UI-leaning) |

## 5. Problematic query variants and exclusion terms

**Query variants that supply most of the ambiguity** (share of the sampled titles retrieved by that variant that were ambiguous or incorrect; n = sampled titles):

| Variant | Role | n | Ambiguous + incorrect |
|---|---|---:|---:|
| program manager | Project Manager | 19 | 100% |
| delivery manager | Project Manager | 8 | 100% |
| scrum master | Project Manager | 3 | 67% |
| product owner | Product Manager | 17 | 100% |
| machine learning engineer | Data Scientist | 15 | 100% |
| systems analyst | Business Analyst | 16 | 94% |
| functional analyst / product analyst | Business Analyst | 4 / 3 | 100% |
| platform engineer | DevOps / Cloud | 5 | 80% |
| analytics engineer | Data Engineer | 7 | 43% |
| application developer | Software Engineer | 8 | 38% |
| visual designer | Graphic Designer | 3 | 67% |

**The canonical-title tiers are precise** (94–100% in every role). The quality problem is the **breadth of the role definitions**, not the regex mechanics.

**Exclusion terms that need attention:**
- Project Manager exclude list has `\binterior\b` but not the plural, so "Projects & Interiors" slipped through; "service delivery manager" (an IT service-management role) is not excluded.
- Graphic Designer has no exclusion for motion graphics (3 of 50 sampled). This was already proposed in `career_scope.json` and not applied to the production config.
- Quality Engineer exclusions (not a core role) are unaffected.

## 6. False negatives (unmatched titles that should belong)

Sample of unmatched titles retrieved by each role's own queries; "clear false negative" means the title plainly names the role.

| Role | Unmatched sample | Clear false negatives | Rate | Distinct unmatched titles in pool | Rough distinct titles missed | Pattern of miss |
|---|---:|---:|---:|---:|---:|---|
| Software Engineer | 15 | 6 | 40% | 300 | ~120 | "Backend Developer", "Sr. Developer - Application Development", "Software Cloud Developer", "Software Engineering Lead" |
| Data Analyst | 30 | 4 | 13% | 316 | ~42 | "BI Reporting Analyst", "Senior Insights Analyst - Power BI" |
| Data Scientist | 15 | 5 | 33% | 136 | ~45 | "Data Science Internship", "Data Science & ML Senior Associate", "Applied AI Scientist" |
| Data Engineer | 15 | 4 | 27% | 161 | ~43 | "Data Engineering" noun forms, "SSIS Developer (ETL)" |
| DevOps / Cloud | 15 | 5 | 33% | 358 | ~119 | "Senior Engineer, DevOps", "DevOps / Infrastructure Engineer", "Cloud Services Engineer" |
| Business Analyst | 30 | 2 | 7% | 179 | ~12 | "Business Process Analyst" |
| Product Manager | 15 | 2 | 13% | 134 | ~18 | "Digital Product Management - Associate" |
| Project Manager | 30 | 6 | 20% | 263 | ~53 | "Manager - Project Management", "Project Management Specialist" |
| Digital Marketing | 15 | 6 | 40% | 28 | ~11 | "SEO Expert", "SEO and Growth Specialist", "Senior Marketing Executive, Digital Channels" |
| Graphic Designer | 30 | 10 | 33% | 99 | ~33 | "Graphic Design Intern/Specialist/Contractor", "Graphics Designer" |

These are estimates from small samples (15–30 titles) of the unmatched pool and count **distinct titles**, not postings. They show that recall is a real limit, worst for Software Engineer, Digital Marketing, DevOps and Graphic Designer. The strict rules deliberately trade recall for precision.

## 7. Proposed changes (documented only, NOT applied)

Each needs a definitional decision by the team and a re-run of this audit.

**Project Manager (blocking).** Three options:
1. **Restrict to the canonical "project manager" title** (311 clean, fails the 400-posting rule → demote to conditional), and treat program/delivery/scrum titles as a separate, clearly labelled family.
2. **Redefine the role as "Project / Program Manager"** and accept program managers as in-role. Lenient precision would be 93.2%, but the role is then a mixed family and 5 of the sample were Amazon-style operations program managers.
3. **Keep the role, tag program/delivery/scrum titles as the medium tier, and run analyses with and without them.** This keeps the clean count and makes the 60% ambiguity visible.

I recommend option 3 for the analysis and option 1 as the fallback if the re-audit still fails. Also add exclusions for `\binteriors?\b` and "service delivery manager".

**Business Analyst.** Consider moving "systems analyst", "functional analyst" and "product analyst" (about 40% of the sample) out of the core role into a labelled tier; canonical-only would be 366 clean (below 400), so the role would need more postings or conditional status.

**Data Scientist / Product Manager.** Keep ML engineer and product owner as medium-tier variants; decide whether the analysis treats them as in-role.

**Recall improvements** (each must be re-audited for precision before adoption):
- Software Engineer: developer forms such as `(backend|front ?end|full ?stack|web|mobile|java|python|cloud|ai) developer`.
- DevOps: reordered and infrastructure forms (`engineer,? devops`, `devops (infrastructure )?engineer`, `cloud services engineer`).
- Data Engineer / Data Scientist: "data engineering" and "data science" noun forms in junior or non-manager titles.
- Digital Marketing: SEO titles beyond the four fixed suffixes.
- Graphic Designer: "graphic design(er)s?" noun forms; exclude motion graphics.

## 8. Conditional roles

**Not promoted.** They do not meet the same criteria, and I did not sample them.
- UX Designer: 345 clean (< 400), canonical 150 (< 300).
- Financial Analyst: 292 clean (< 400).
- Security (merged families): 510 clean by the joint pipeline (498 by union) and each family's canonical share is 100%, so the count criteria are met, but precision was **not measured** and the merge is still a team decision. No promotion is recommended until both are done.

## 9. Conclusion for the gate

**Gate D (all 10 core roles pass mapping quality): FAILS.** Project Manager does not reach 90% precision (85.0%), and four other roles have ambiguity of 32–40% concentrated in specific synonym variants. The other nine roles pass all three numeric criteria. Files: `data/raw/ml_data_feasibility/mapping_precision/` (`samples.json`, `labels.csv`, `summary.json`).

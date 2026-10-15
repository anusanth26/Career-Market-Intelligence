# Dataset Documentation: Career Market Intelligence Dataset (v1.0.0-final)

Frozen 2026-09-30 by `scripts/build_dataset.py` (build) followed by `scripts/finalize_dataset.py` (policy freeze), from Adzuna data that was **already collected**. No Adzuna or Google Trends calls were made, no additional data was collected, and raw files are byte-identical (SHA-256 re-checked against the manifest: 0 mismatches of 91 files).

**Dataset finalization is complete. Preprocessing and downstream analytics (EDA, feature engineering, modelling, time-series and text-mining analysis, dashboard) have not yet started.** The next phase begins only after explicit approval.

## Two frozen views

| View | File | Rows | Contents |
|---|---|---:|---|
| **A. Full validated dataset** | `data/processed/adzuna/career_market_full_validated.parquet` (+ `.csv`) | **8,489** | Every record retained by the build rules: core, conditional and adjacent partitions. Nothing is removed for the employer cap; rows carry `employer_cap_status` |
| **B. Final core analysis dataset** | `data/processed/adzuna/career_market_core_analysis.parquet` (+ `.csv`) | **6,533** | Core roles only, after the deterministic 5% employer cap (129 core rows excluded). Includes Project Manager, flagged `conditional_limited` |

Both are job records with source fields and a few labelled metadata columns, **not** ML feature matrices. Schema: `data/processed/adzuna/schema.json` (49 columns, frozen). Manifest: `dataset_manifest.json`. Parquet is the primary format (1.6 MB for A, 1.3 MB for B); the CSVs (9.6 MB and 7.3 MB) are kept for inspection.

## 1. Dataset source

The Adzuna job-search API (India, `in`), collected by the team's own scripts. This satisfies the rubric requirement to collect the dataset ourselves; no pre-built Kaggle/UCI/GitHub dataset is used. **Adzuna's terms limit use beyond a 14-day trial without written consent and are silent on storage and redistribution; consent has not been obtained** (`report/adzuna_compliance.md`). `data/processed/` and `data/audits/` are git-ignored and must not be committed, pushed or shared.

## 2. Collection method and period

- **Legacy pull (2026-09-29):** 4 files × 625 records from the team's first collector (commit `0567dac`: free-text `what` queries, relevance-sorted, no date filter). The query per file comes from the file name and is confirmed by `pull_log_2026-09-29.json`. No collection timestamp exists for these records, only the pull date.
- **Audited runs (2026-09-29, 17:40–18:09 UTC):** 4 run directories from the audited collector (`title_only`, `max_days_old=90`, `sort_by=date`, 50 per page): a smoke run, the main run, a completion run and a security run. Each record carries run id, query variant, requesting role, page, position and fetch time.
- **Window:** postings created from 2026-07-01 (the 90-day window start recorded in the run manifests).

## 3. Raw dataset size

| Source | Files | Records | Unique IDs |
|---|---:|---:|---:|
| Legacy pull | 4 | 2,500 | 2,472 |
| Smoke run | 9 | 676 | 658 |
| Main run | 57 | 15,663 | 13,733 |
| Completion run | 16 | 5,706 | 4,600 |
| Security run | 5 | 1,027 | 949 |
| **Total** | **91** | **25,572** | **16,663 unique overall** |

Malformed records: 0. Missing IDs or titles: 0. 574 IDs occur in both the legacy pull and the runs; the runs overlap each other heavily. Full inventory: `data/audits/dataset/source_inventory.json`.

## 4. Exact-ID deduplication

25,572 → **16,663** unique job IDs (**8,909** duplicates removed). 5,340 IDs occurred more than once. The kept copy is chosen deterministically: full run provenance first, then earliest collection time, run name, file, page and position; the other copies' sources are recorded in `also_seen_in`. 2 IDs had differing content between copies (listed in `dedup_report.json`).

## 5. Near-duplicate methodology

The defined key is normalized title + normalized employer + first 150 normalized description characters. That key alone would have removed 1,734 records, but 403 of them differ later in the snippet, mostly templated Accenture postings whose required skills or years of experience differ ("Minimum 3 year(s)" vs "7.5 year(s)"), and are separate vacancies. **Rule applied: merge a candidate only when the full normalized snippet is also identical.** Result: **1,331 records removed in 903 groups** (8.0%); **15,332 records remain**; 403 template collisions kept. The most recently created posting represents each group. Location labels are not used to block a merge (they differ in 534 confirmed groups, mostly the same place at different granularity, e.g. "India" vs "Vadodara, Gujarat"). Removals are listed in `near_duplicate_removals.csv`.

## 6. Role taxonomy (title-based, frozen)

**Role assignment is title-based**: regex rules on the job title (`config/roles.json` plus overrides in `config/dataset_build.json`). Description, skills, salary, category, employer and the query are never used. The original `title` and the final `role` are preserved in both views. **Do not use `title`, `role`, `source_query_role` or `mapping_tier` as predictive features.** `mapping_tier` (canonical or synonym) exists only for sensitivity analysis. Statuses during mapping: matched, excluded_by_rule, ambiguous_multi, unmatched (only matched rows are in the datasets).

**Core taxonomy (10 roles, no additions):**
- Technology & Data: Software Engineer, Data Analyst, Data Scientist, Data Engineer, DevOps / Cloud Engineer
- Business, Finance & Management: Business Analyst, Product Manager, Project Manager, Digital Marketing
- Media & Design: Graphic Designer

One override beyond Project Manager: motion-graphics titles are excluded from Graphic Designer (two independent samples showed this as the only recurring incorrect pattern). It lives only in `config/dataset_build.json`.

## 7. Project Manager decision (frozen)

```
role                 = Project Manager
count                = 317 (uncapped); 315 after the employer cap
status               = conditional
reason               = below minimum dataset-size target (400)
mapping policy       = canonical-only
```

Project Manager stays its own role with the **canonical-only** mapping ("project manager" titles, with exclusions for construction, civil, site, interior/interiors, real estate, MEP, architecture and BIM). **Program Manager (371), Delivery Manager (133) and Scrum Master (110) are stored separately and are not merged into Project Manager.** The mapping was not relaxed to reach 400 and no records were fabricated. Evidence for the policy: in the earlier 50-title audit, canonical titles were 17 correct / 3 ambiguous / 1 incorrect while 0 of 29 sampled program, delivery and scrum-master titles were correct; a fresh 50-title sample of the canonical-only rule gave 39 correct, 11 ambiguous, 0 incorrect (100% precision, ambiguity 22%). The role is kept in the core taxonomy (`role_status = conditional_limited`), not removed.

## 8. Conditional and adjacent roles (kept separate)

- **Conditional (1,213 rows, `role_scope = conditional`):** UX Designer 350, Financial Analyst 346, and five security title families (Security Engineer 378, Cybersecurity Engineer 64, Information Security Engineer 45, Information Security Analyst 22, Cybersecurity Analyst 8; merged security view 517 rows, kept as five separate `role` values). Not promoted. The employer cap is not applied to them and they are not in view B.
- **Adjacent, not core (614 rows, `role_scope = adjacent_not_core`):** Program Manager, Delivery Manager, Scrum Master.
- Excluded domains (Engineering, Architecture & Construction, Healthcare, Logistics, Energy) remain excluded; 1,249 Engineering/Architect-titled records were dropped at role assignment.

## 9. Employer-cap policy (frozen, applied)

**Applied to the final core analysis dataset (view B) only.** For each core role, the cap per employer is `max(1, floor(0.05 × role rows before the cap))`. If an employer exceeds it within a role, its most recently created postings are kept (ties: smallest numeric job id) and the rest are excluded. Records without an employer are never capped. No randomness; raw data untouched; the uncapped rows remain in view A with `employer_cap_status = excluded_by_5pct_cap`. Every excluded record is listed in `data/audits/dataset/employer_cap_exclusions.csv` (129 rows). **Uncapped statistics are kept in the audit** (`employer_cap_audit.json`, `.csv`).

| Role | Records before cap | Records after cap | Removed | Unique employers | Top employer % before | Top employer % after | Effective employers before → after | Cap per employer |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| Software Engineer | 1,260 | 1,206 | 54 | 506 | 7.70 | 5.22 | 72.4 → 107.1 | 63 |
| Data Analyst | 526 | 526 | 0 | 376 | 1.90 | 1.90 | 264.5 → 264.5 | 26 |
| Data Scientist | 691 | 626 | 65 | 325 | 14.33 | 5.43 | 37.5 → 96.2 | 34 |
| Data Engineer | 470 | 466 | 4 | 279 | 5.74 | 4.94 | 98.9 → 106.8 | 23 |
| DevOps / Cloud Engineer | 910 | 909 | 1 | 540 | 5.05 | 4.95 | 180.4 → 183.7 | 45 |
| Business Analyst | 873 | 870 | 3 | 476 | 5.27 | 4.94 | 141.1 → 147.4 | 43 |
| Product Manager | 635 | 635 | 0 | 382 | 3.94 | 3.94 | 168.5 → 168.5 | 31 |
| Project Manager | 317 | 315 | 2 | 245 | 5.36 | 4.76 | 123.3 → 132.1 | 15 |
| Digital Marketing | 562 | 562 | 0 | 422 | 2.32 | 2.32 | 250.8 → 250.8 | 28 |
| Graphic Designer | 418 | 418 | 0 | 365 | 1.91 | 1.91 | 287.4 → 287.4 | 20 |
| **Core total** | **6,662** | **6,533** | **129** | 2,605 | 4.38 → 2.91 (top employer, core overall) | | 261.1 → 373.6 | |

Amazon accounts for 102 of the 129 exclusions, Accenture 21, Tata Consultancy Services 4, Cushman & Wakefield 2. "Top employer % after" is measured on the reduced role total, so it can stay slightly above 5%. After the cap every core role meets the targets (top employer ≤ 6%, effective employers ≥ 50, distinct employers ≥ 100, canonical titles ≥ 300) except Project Manager's size.

## 10. Final role counts

Pipeline: raw **25,572** → ID-deduplicated **16,663** → near-deduplicated **15,332** → final retained (view A) **8,489** → core analysis dataset (view B, after cap) **6,533**.

| Role | Partition | Uncapped count | Final count | Status | Unique employers (final) |
|---|---|---:|---:|---|---:|
| Software Engineer | core | 1,260 | 1,206 | core | 506 |
| Data Analyst | core | 526 | 526 | core | 376 |
| Data Scientist | core | 691 | 626 | core | 325 |
| Data Engineer | core | 470 | 466 | core | 279 |
| DevOps / Cloud Engineer | core | 910 | 909 | core | 540 |
| Business Analyst | core | 873 | 870 | core | 476 |
| Product Manager | core | 635 | 635 | core | 382 |
| Project Manager | core | 317 | 315 | **conditional_limited** (below size target) | 245 |
| Digital Marketing | core | 562 | 562 | core | 422 |
| Graphic Designer | core | 418 | 418 | core | 365 |
| UX Designer | conditional | 350 | 350 | conditional | 266 |
| Financial Analyst | conditional | 346 | 346 | conditional | 178 |
| Security Engineer | conditional | 378 | 378 | conditional | 263 |
| Cybersecurity Engineer | conditional | 64 | 64 | conditional | 51 |
| Information Security Engineer | conditional | 45 | 45 | conditional | 30 |
| Information Security Analyst | conditional | 22 | 22 | conditional | 19 |
| Cybersecurity Analyst | conditional | 8 | 8 | conditional | 8 |
| Program Manager | adjacent | 371 | 371 | adjacent_not_core | 184 |
| Delivery Manager | adjacent | 133 | 133 | adjacent_not_core | 101 |
| Scrum Master | adjacent | 110 | 110 | adjacent_not_core | 85 |

Full file: `data/audits/dataset/final_role_counts.json`. Role status is evaluated on the after-cap data; Project Manager is also forced conditional by policy.

## 11. Employer statistics

Full validated dataset: 3,053 unique employers (1 row has no employer). Core, before the cap: 2,605 employers, top employer 4.38% (292 rows), effective number of employers 261.1. Core after the cap: 2,605 employers, top employer 2.91% (190 rows), effective number 373.6. Per-role figures are in the table in section 9.

## 12. Salary availability (regenerated; not modelled)

**Salary period and currency are unresolved.** The Adzuna response has no currency or pay-period field. `salary_period_interpretation = unresolved`; `salary_currency_interpretation = unresolved` (country is India, but the API does not say INR). `salary_passes_plausibility_screen` is a **numeric screen only**: salary present, not Adzuna-predicted, min ≤ max, and every value between 100,000 and 10,000,000 in raw units. It does not assert annual pay or a currency. Among the salaried final-core snippets, 20 mention "per month", 21 mention LPA/lakh, 4 mention "per annum/annual", 37 mention INR/rupee and 10 mention dollars, so the interpretation cannot be settled from this data.

| Scope | Rows | Salary present | Missing | Predicted (flag = 1) | Passes screen | Invalid |
|---|---:|---:|---:|---:|---:|---:|
| **Final core analysis dataset (B)** | 6,533 | 602 | 5,931 | 0 | **523** | 79 (77 below the floor, 2 non-positive) |
| Core, uncapped | 6,662 | 602 | 6,060 | 0 | 523 | 79 |
| Full validated dataset (A) | 8,489 | 717 | 7,772 | 0 | 626 | 91 |

The cap removed no salaried rows. All salaries are employer-stated (`salary_is_predicted` = "0" everywhere). Passing rows by core role (final B): Digital Marketing 124, DevOps 76, Graphic Designer 64, Business Analyst 57, Software Engineer 46, Data Scientist 42, Product Manager 35, Data Analyst 30, Project Manager 29, Data Engineer 20. Salary presence is not random (higher for Digital Marketing and junior-titled postings). **No salary bands were created, no salary model was trained, and the supervised target is not decided here.** Detail: `salary_quality_report.json`.

## 13. Known limitations

1. Descriptions are snippets of about 500 characters (98.7% truncated); any later skill frequency is a lower bound.
2. One 90-day snapshot from one collection day, skewed to recent postings (77% of core rows created in the last 30 days); it is not a history.
3. Adzuna is one aggregator, skewed to large employers, IT services and three cities.
4. Title-based labels have limited recall, and broad synonym variants create ambiguity (25–40% in Business Analyst, Product Manager, Data Scientist, DevOps and Graphic Designer).
5. Project Manager is below the size target (317; 315 after the cap).
6. Salary is sparse (9% of core rows), employer-disclosed, not random, and its period and currency are unresolved.
7. `created` timestamps run up to 4.7 hours ahead of the collection clock, consistent with India local time labelled as UTC; use `created_date` (day level). The future-date rule tolerates 14 hours.
8. The 403 kept template collisions (mostly Accenture) are possibly repeated templated postings; the capped view B limits their weight.
9. 544 rows exist only in the legacy free-text, relevance-sorted pull; `collection_method` distinguishes them.
10. The dataset was collected under terms whose continued use is not cleared.

## 14. Validation status

The mapping spot-check was performed by the project workflow (an AI assistant) against a fixed rubric. **It is not independent human validation.**

| Role | Current validation method | Sample size | Observed precision (95% interval) | Ambiguity | Status | Independent human validation |
|---|---|---:|---|---:|---|---|
| Software Engineer | AI-assisted manual spot-check | 20 | 100% (83.2–100) | 5% | spot-check complete | **PENDING** |
| Data Analyst | same | 20 | 95.0% (76.4–99.1) | 0% | complete | **PENDING** |
| Data Scientist | same | 20 | 100% (78.5–100) | 30% | complete | **PENDING** |
| Data Engineer | same | 20 | 100% (83.2–100) | 5% | complete | **PENDING** |
| DevOps / Cloud Engineer | same | 20 | 92.9% (68.5–98.7) | 30% | complete | **PENDING** |
| Business Analyst | same | 20 | 100% (77.2–100) | 35% | complete | **PENDING** |
| Product Manager | same | 20 | 100% (75.7–100) | 40% | complete | **PENDING** |
| Project Manager (canonical-only) | same | 50 | 100% (91.0–100) | 22% | complete | **PENDING** |
| Digital Marketing | same | 20 | 93.8% (71.7–98.9) | 20% | complete | **PENDING** |
| Graphic Designer | same | 20 | 100% (79.6–100) | 25% | complete | **PENDING** |
| Conditional and adjacent roles | none | 0 | not measured | – | not sampled | **PENDING** |

Precision = correct ÷ (correct + incorrect); ambiguous titles are reported separately. Small samples give wide intervals. Pooled with the earlier 50-title audit (postings still present under the same role), precision is 95.3–100% (n 67–70). **Independent human validation = PENDING.** No human-review result was invented. A deterministic, unlabelled sample for a teammate is ready: `data/audits/dataset/human_validation/human_validation_template.csv` (15 titles per core role from view B, with a `README.md`). Details: `data/audits/dataset/mapping_validation_status.json`.

## 15. Reproducibility

```
python scripts/build_dataset.py                          # full validated dataset (stage) + build audits
python scripts/finalize_dataset.py                       # freeze: policy columns, employer cap, views A and B, audits, manifest
python scripts/finalize_dataset.py --check-reproducible  # runs build + finalize twice in temp dirs and compares
```

The process uses fixed rules (`config/dataset_build.json`, `config/roles.json`), explicit sort orders and no randomness (the human-validation sample is seeded). **Verified 2026-09-30: two independent runs produced identical results across 22 compared files** (CSV bytes and Parquet content of both views, role assignments, cap exclusions, all audit and report files, manifest statistics), and both matched the main outputs (`data/audits/dataset/reproducibility_check.json`: PASS). Raw files are SHA-256 checked before and after each build (0 mismatches of 91). The finalization does not change any retained record: all 8,489 records are identical to the pre-freeze build on every shared column.

## 16. What remains unresolved

1. **Independent human validation of the role mapping: PENDING.**
2. **Adzuna consent** for continued use and publication, and the **repository exposure** of the raw legacy files and a teammate's derived CSV on the remote (`report/adzuna_compliance.md`, `report/repository_data_exposure.md`).
3. **Project Manager** remains below the size target; more data cannot be collected until consent is resolved.
4. **Salary period and currency** are unresolved; no salary target or bands are decided.
5. The **supervised target** and every downstream method are decisions for a later phase.

## Frozen schema notes

The frozen columns include the fields needed for later analysis: `job_id`, `title`, `role`, `employer`, `description_raw`, `location_display` / `location_area`, `created`, `category_label`, `salary_min`, `salary_max`, `salary_is_predicted`, `source_run`, `source_query`, `collection_timestamp`, plus partition and policy columns (`role_scope`, `role_status`, `employer_cap_status`, `in_core_analysis_dataset`) and quality flags. **Not stored:** text normalisation, tokens, embeddings, skill vectors, salary bands, or any model feature. Deliberately not carried: `redirect_url` (embeds the API app id), `adref`, `title_normalized`, `description_normalized`, `matched_pattern_index`. `employer_normalized` is an employer-grouping key used for the cap, not a modelling feature.

Files: `data/processed/adzuna/` (two views, `schema.json`, `dataset_manifest.json`, `quality_report.json`) and `data/audits/dataset/` (`source_inventory.json`, `dedup_report.json`, `near_duplicate_removals.csv`, `excluded_records.csv`, `role_mapping_report.json`, `sample_size_audit.json`, `employer_concentration_report.json` (uncapped), `employer_cap_audit.json` / `.csv`, `employer_cap_exclusions.csv`, `final_role_counts.json`, `salary_quality_report.json`, `mapping_validation_status.json`, `human_validation/`, `mapping_spotcheck/`, `reproducibility_check.json`).

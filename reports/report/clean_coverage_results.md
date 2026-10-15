# Clean-Posting Coverage Experiment and Scope Decision (India, 90-day window)

Run date 2026-09-29. Follows `report/feasibility_analysis.md`. **[V]** = measured in these runs. **[I]** = inference.
This is a feasibility experiment. It is **not** the production dataset.

## 1. What was run

| Run (in `data/raw/adzuna/runs/`) | Purpose | Queries | Rows |
|---|---|---:|---:|
| `20260929T174012Z_b5985163_smoke` | Small subset used to audit the collector and inspect titles | 9 | 676 |
| `20260929T174139Z_4496f922_feasibility` | All roles and title variants, capped at 500 records per query (150 for subset-style variants) | 57 | 15,663 |
| `20260929T175840Z_b181dc01_deepen` | Completion pull (cap 1,000) for roles whose first pull was capped and borderline: Data Analyst, Financial Analyst, Mechanical/Electrical/Quality Engineer, Security Engineer | 16 | 5,706 |
| `20260929T180809Z_8ad616c4_security_full` | Completion pull for all five security title families | 5 | see run |

All runs: India, `title_only`, `max_days_old=90`, `sort_by=date`, 50 per page. Each run has a `run_manifest.json`, `queries.jsonl` and an `analysis/` folder (`coverage_results.csv`, `dedup_removals.csv`, `salary_audit.csv`, `variant_title_inspection.csv`, `summary_table.md`, `audit_checks.json`).
Counts for each role below come from the run that pulled that role completely (feasibility run, or the completion run where noted).

## 2. Collector behaviour now implemented

Files: `scripts/collect_adzuna.py` (collector), `scripts/role_mapping.py` (title mapping), `scripts/analyze_coverage.py` (yield pipeline), `config/roles.json` (roles, variants, rules, thresholds).

- **Query**: every call sends `title_only=<variant>`, `max_days_old=90`, `sort_by=date`, `results_per_page=50`. Verified from the recorded request parameters for all queries [V].
- **Window**: calendar-day window starting 00:00 UTC of (run date − 90 days). See Section 8 for why.
- **API count** for every query is saved with pull timestamp, page size, pages retrieved, rows retrieved, HTTP failures, retries, stop reason, and self-audit facts (sort order, out-of-window rows, duplicate IDs). `count` was logged for all 87 queries [V].
- **Retry/backoff**: retries on 429/500/502/503/504, timeouts, connection errors and bad JSON. Exponential backoff (2 s doubling, capped at 120 s, plus up to 1 s jitter), honours `Retry-After`, at most 5 retries per page. Non-retryable errors (401/403 etc.) stop that query at once. Each failed attempt is written to `attempts.jsonl`. Partial progress is kept because records are appended page by page. The run aborts after 3 consecutive queries exhaust their retries (likely quota or ban). Credentials are redacted from every logged error.
- **No documented rate limit is claimed.** Observed: 0 responses of 429 across 492 successful page fetches (plus 9 failed attempts) at a 2.6 s pace. Adzuna returned transient **503** HTML error pages on 4 pages of one query; all recovered within 1–3 retries with no data loss [V].
- **Raw preservation**: each record is stored as `{"collection": {...}, "raw": {<unmodified API record>}}`. `collection` holds run_id, collected_at, source, country, query_variant, `query_role` (which config entry asked for it, **not** the role label), domain, adzuna_id, page and position. Each run goes to a new directory (`os.makedirs(exist_ok=False)`), so nothing is overwritten.
- **Role mapping**: deterministic regex on the normalized title. Statuses: `matched`, `excluded_by_rule`, `ambiguous_multi`, `unmatched`. Overlap resolution only inside a declared `overlap_group` (security). Nothing is forced into a role. Original titles are never changed.
- **Pipeline**: title-matched → exact-ID duplicates → near-duplicates (normalized title + company + first 150 description characters) → employer cap (5% of the role's post-dedup postings per employer, most recent kept; postings with no employer are not capped) → clean. Every removal is logged with role, employer, reason and the kept ID.
- **Salary audit**: floor 100,000 and ceiling 10,000,000 (annual, assumed INR [I]) are configurable and are used only to *flag* records; nothing is deleted for salary.

## 3. Audit results (the 13 checks)

| # | Check | Result |
|---|---|---|
| 1 | `title_only` really sent | Yes for all 57 + 16 + 5 + 9 queries (recorded params; unit test asserts the outgoing call) [V] |
| 2 | 90-day condition | 0 rows before the calendar-day cutoff; earliest posting 2026-07-01T02:26Z. 8 rows were before the exact-timestamp cutoff, all on the boundary date, so this is Adzuna's whole-day granularity [V] |
| 3 | `sort_by=date` | Sent for all queries; `created` was non-increasing in every query (57/57 in the main run) [V] |
| 4 | Pagination | Pages contiguous from 1 in every query; 0 duplicate IDs within a query; queries stop correctly at the cap or when results run out [V] |
| 5 | Retry behaviour | Live: 9 transient 503s recovered (deepen run). Offline: 429 with Retry-After, exponential delays 1/2/4 s, non-retryable 401, exhaustion after max retries, timeouts, bad JSON, credential redaction (unit tests) [V] |
| 6 | Duplicate removal | Unit-tested (exact, near-duplicate, cap, employer with no name); live removals logged in `dedup_removals.csv` [V] |
| 7 | Synonym de-duplication | "finance analyst" returned the identical 587 postings as "financial analyst" and added 0 clean rows; "software development engineer" added 0 [V] |
| 8 | Salary calculations | Unit-tested against hand-computed cases; live audit in `salary_audit.csv` [V] |
| 9 | API counts logged | Every query [V] |
| 10 | Raw data preserved | The 4 original files in `data/raw/adzuna/` have identical MD5 checksums before and after; the smoke run's `queries.jsonl` is byte-identical after later runs [V] |
| 11 | Rerun safety | A second run creates a new directory and leaves the first byte-identical (unit test) [V] |
| 12 | Manual title inspection | Done on the smoke run and the architect/security samples. Found and fixed one mapping error (Section 8) [V] |
| 13 | Credentials | Not present in any run file (checked in `audit_checks.json`) [V] |

17 offline tests: `python -m unittest discover -s tests`.

## 4. Roles tested, API counts, clean counts

API count = primary variant's `count`. "Clean" = after title mapping, exact and near-duplicate removal, and the 5% employer cap. "≥" means the pull hit the per-query record cap, so the true clean figure is higher. Roles are ordered by domain.

| Domain | Role | API count | Raw rows (own queries) | Title-matched | Exact dup | Near dup | Employer cap | **Clean** | Salary % | Pass 400? |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Tech & Data | Software Engineer | 9,129 | 1,650 | 1,350 | 232 | 195 | 48 | **≥875** | 5.7 | Yes |
| | Data Analyst (completion run) | 842 | 1,208 | 540 | 33 | 34 | 0 | **473** | 7.0 | Yes |
| | Data Scientist | 1,264 | 948 | 768 | 19 | 83 | 62 | **≥604** | 7.8 | Yes |
| | Data Engineer | 2,805 | 777 | 522 | 35 | 77 | 0 | **≥410** | 5.1 | Yes |
| | DevOps / Cloud Engineer | 822 | 1,825 | 1,097 | 114 | 129 | 0 | **≥854** | 10.1 | Yes |
| | Security Engineer (alone) | 811 | 811 | 406 | 2 | 30 | 0 | **374** | 3.7 | No |
| | Security, all 5 title families merged | – | – | 626 | 59 | 57 | 0 | **510** | 4.3 | Only if merged |
| Business | Business Analyst | 1,263 | 1,051 | 870 | 145 | 55 | 7 | **≥663** | 6.6 | Yes |
| | Financial Analyst (completion run) | 587 | 1,289 | 737 | 367 | 35 | 43 | **292** | 4.1 | No |
| | Product Manager | 1,823 | 879 | 694 | 22 | 44 | 0 | **≥628** | 7.0 | Yes |
| | Project Manager | 1,836 | 1,556 | 1,106 | 44 | 85 | 45 | **≥932** | 7.7 | Yes |
| | Digital Marketing | 390 | 639 | 593 | 10 | 28 | 0 | **555** (complete) | 25.8 | Yes |
| Engineering | Mechanical Engineer (completion run) | 567 | 756 | 392 | 90 | 46 | 0 | **256** (complete) | 10.2 | No |
| | Electrical Engineer (completion run) | 580 | 657 | 294 | 49 | 34 | 1 | **210** (complete) | 10.0 | No |
| | Quality Engineer (completion run) | 807 | 985 | 323 | 3 | 51 | 0 | **269** (complete) | 11.5 | No |
| Media & Design | UX Designer | 238 | 550 | 390 | 19 | 26 | 0 | **345** (complete) | 13.6 | No |
| | Graphic Designer | 571 | 647 | 495 | 31 | 21 | 0 | **≥443** | 16.0 | Yes |

"Complete" means the API count was exhausted for every title variant, so more India postings in this 90-day window do not exist under these titles. For Data Analyst, Financial Analyst and the three Engineering roles, the first (capped) pull understated the counts (for example Data Analyst 305 → 473); the completion run is the figure to use.

**Title-variant contribution** (marginal clean postings each synonym added; from `coverage_results.csv`):
- **Useful**: SRE and DevOps for DevOps/Cloud; "product owner" (+260 for Product Manager); "program manager" and "delivery manager"; "performance marketing" (+161); "product designer" (+168 for UX); "machine learning engineer" and "applied scientist" for Data Scientist.
- **Add nothing or almost nothing**: "finance analyst" (identical to "financial analyst", 0 new), "software development engineer" (0 new), "reporting analyst" (2 new; it returns Regulatory/Tax/Record-to-Report analysts, so the Data Analyst mapping rule was tightened), "quality assurance engineer" (0 matches; mostly software QA titles, which we do not force into Quality Engineer), "mechanical design engineer" and "electrical design engineer" (mostly duplicates).
- **Adzuna stems words** (finance ≈ financial), and `title_only` matches words anywhere in the title, not the phrase [V]. So a query such as "data analyst" also returns "Analyst-Data Analytics" and "Senior Data Management Analyst"; the mapping layer rejects those (Data Analyst: 261 of 500 raw rows matched).

## 5. Salary availability

Salary is sparse in the 90-day window. `salary_is_predicted` was "0" for every record in every run [V], so all salaries are employer-stated, none Adzuna-estimated.

| Role | Clean | salary_min | salary_max | Both | Salary % | Below 100k floor | Above 10M | min>max | min=max | Valid after floor/ceiling |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Software Engineer | 875 | 50 | 50 | 50 | 5.7 | 12 | 0 | 0 | 14 | 38 |
| Data Analyst | 473 | 33 | 33 | 33 | 7.0 | 4 | 0 | 0 | 6 | 29 |
| Data Scientist | 604 | 47 | 47 | 47 | 7.8 | 5 | 0 | 0 | 15 | 42 |
| Data Engineer | 410 | 21 | 21 | 21 | 5.1 | 1 | 0 | 0 | 3 | 20 |
| DevOps / Cloud | 854 | 86 | 85 | 85 | 10.1 | 10 | 0 | 0 | 18 | 76 |
| Business Analyst | 663 | 44 | 44 | 44 | 6.6 | 3 | 0 | 0 | 12 | 41 |
| Product Manager | 628 | 44 | 43 | 43 | 7.0 | 9 | 0 | 0 | 14 | 35 |
| Project Manager | 932 | 72 | 71 | 71 | 7.7 | 9 | 0 | 0 | 16 | 63 |
| Digital Marketing | 555 | 143 | 143 | 143 | 25.8 | 20 | 0 | 0 | 10 | 123 |
| Graphic Designer | 443 | 71 | 71 | 71 | 16.0 | 6 | 0 | 0 | 3 | 65 |
| UX Designer | 345 | 47 | 47 | 47 | 13.6 | 5 | 0 | 0 | 4 | 42 |
| Security Engineer | 374 | 14 | – | – | 3.7 | 1 | – | – | – | 13 |

- About **611 postings with a salary** across the 10 passing roles. Per-role salary analysis is not viable (5–26% presence; 20–143 postings per role). Pooled analysis is possible but thin. **Salary should not be a primary model target** [I].
- These rates are lower than in the earlier relevance-sorted pulls (Software Engineer 12%, Data Analyst 18%), which mixed old postings. Recent postings carry salary less often (**[I]**: employers add salary later, or the 2019–2026 mix differed).
- Junk values exist (min as low as 3–12). The floor is documented and configurable; nothing was deleted.
- Currency and period (annual INR) are assumed [I]. Adzuna's response has no currency field.

## 6. Contamination and role checks

### Architect (India, "architect", most recent 500 postings of 3,532; not a random sample)
512 unique architect-titled postings, classified by title tokens only:
- **72.1% likely IT/software architects** (369): Enterprise, Security, Technology, AI, Data, Application, Solution.
- **25.4% ambiguous** (130): bare "Architect", "Senior Architect", "Junior Architect", "Business Architect".
- **2.5% likely building architects** (13): BIM Architect, Landscape Architect, Interior Architect. One of the 13 is a false positive ("Customer Delivery Architect … architectural and validation expertise") caused by the word "architectural", so the true share is a little lower.
- **Conclusion**: the 3,532 India count is dominated by IT roles. **Do not use it as evidence for Architecture & Construction.** Even if every ambiguous title were a building architect, the upper bound would be about 28% of the count [I]. Verdict: contamination confirmed [V].

### Security roles (complete pull, India, 90 days)
| Title family | API | Clean |
|---|---:|---:|
| Security Engineer | 811 | 374 |
| Cybersecurity Engineer | 78 | 61 |
| Information Security Engineer | 72 | 36 |
| Information Security Analyst | 39 | 19 |
| Cybersecurity Analyst | 27 | 8 |
| **All five merged, deduplicated together** | – | **510** |

The earlier "cybersecurity analyst = 27" was indeed a title-choice problem: "security engineer" alone has 811 postings. But no single family reaches 400 (best 374). Only the merged family does, and 73% of it is Security Engineer. Note that "Security Engineer" mapping also captures Network, Product and Cloud Security Engineer titles. Merging is a definitional choice for the team; it was not done automatically.

### Engineering (all three fail the 400 working requirement)
| Role | API | Clean | Note |
|---|---:|---:|---|
| Mechanical Engineer | 567 | 256 | 392 of 756 raw rows title-matched |
| Electrical Engineer | 580 | 210 | 294 of 657 title-matched |
| Quality Engineer | 807 | 269 | 323 of 985 title-matched; 63 rows rejected as software QA by the exclusion rule |

All three pulls are exhausted, and under the **official (strict) rules** none reaches even the 300 minimum for skill-frequency analysis from the feasibility report. **Not forced in.**

**Sensitivity to mapping strictness (found by inspecting unmatched titles).** The strict rules reject word-order variants of the same title, such as "Engineer - Mechanical", "Principal Engineer - Mechanical Component" and "Engineer - Electrical". I kept the strict rules as the official basis, because they were set before the data was seen. As a sensitivity check (`config/roles_sensitivity_recall.json`, results in `analysis_recall_sensitivity/` inside each run), I added only word-order patterns for the two roles and a spelled-out FP&A pattern for Financial Analyst:

| Role | Strict (official) | Recall-tolerant (sensitivity) |
|---|---:|---:|
| Mechanical Engineer | 256 | 396 |
| Electrical Engineer | 210 | 373 |
| Quality Engineer | 269 | 266 (no change) |
| Financial Analyst | 292 | 311 |

So the Engineering verdict does **not** change (no role reaches 400 under either rule), but Mechanical (396) and Electrical (373) are much closer than the strict numbers suggest. The added titles have not been checked for precision (e.g. whether "Engineer - Mechanical Component" postings from a few employers are really mechanical-engineering roles), so I did not adopt them.

### Media & Design
- Graphic Designer: **443**, passes 400 (571 API; "visual designer" +34, "creative designer" +22).
- UX Designer: **345** with all variants exhausted (ux designer 238, product designer 293, "user experience designer" 19). It fails 400 but exceeds the 300 minimum for skill-frequency. I did not add extra title variants just to reach 400.

## 7. Final scope decision (India, 90-day window)

### DEFINITELY INCLUDE (clean ≥ 400, measured)
Technology & Data: Software Engineer, Data Analyst, Data Scientist, Data Engineer, DevOps / Cloud Engineer.
Business, Finance & Management: Business Analyst, Product Manager, Project Manager, Digital Marketing.
Media & Design: Graphic Designer.
That is **10 roles and about 6,400 clean postings** already measured in the feasibility pulls (lower bound for the capped roles).

### CONDITIONAL
| Role | Clean | Why conditional and what would resolve it |
|---|---:|---|
| Security (merged family) | 510 combined; 374 for Security Engineer alone | Passes only if the team accepts merging five title families. Otherwise fails. |
| UX Designer | 345 | Above the 300 skill-frequency minimum, below 400 for role comparisons. Usable for frequency analysis; not for comparing roles. |
| Financial Analyst | 292 | Just under 300; data exhausted. Options: repeat the pull in 3–4 weeks when new postings have accumulated, or accept it as a frequency-only role. |

### EXCLUDE from V1
- **Engineering** (Mechanical 256, Electrical 210, Quality 269, all exhausted): cannot be a third domain in India with a 90-day window.
- **Standalone** Information Security Analyst (19), Cybersecurity Analyst (8), Information Security Engineer (36), Cybersecurity Engineer (61).
- **Architecture & Construction** (contamination, Section 6), **Healthcare**, **Logistics**, **Energy & Environment** (unchanged from the feasibility report; not re-measured here).

### Recommended domain scope
- **Firm (2)**: Technology & Data; Business, Finance & Management.
- **Third domain**: **Media & Design**, not Engineering. It has one firm role (Graphic Designer) and one conditional (UX Designer), whereas Engineering has none. It is a *thin* third domain; with one firm role, "explore by domain" claims for it will be weak. The team should choose between (a) a small Media & Design domain, or (b) two domains with about 9–10 roles.
- The "definitely include" list is the working role list. It totals 10, not the 12–14 estimated earlier.

## 8. Issues found and fixed during the audit
1. **Data Analyst mapping too loose.** Manual inspection showed the "reporting analyst" synonym pulling Regulatory/Tax/Record-to-Report analysts into Data Analyst. The generic rule was removed (Data Analyst 120 → 101 in the smoke sample). Mapping can be re-run on raw data with `analyze_coverage.py --config`.
2. **Window definition.** My first check used an exact-timestamp cutoff and flagged 8 rows, all created on the boundary date. Adzuna's `max_days_old` works in whole days, so the window now starts at 00:00 UTC. The stricter count is still reported in `audit_checks.json`.
3. **Capped pulls understated some roles.** Fixed by the completion pulls.

## 9. Unresolved issues and limits
- **Snippets still limit skill extraction.** This experiment counted postings, not skills. Clean counts do not say how many skills the 500-character snippets will yield. Test skill-yield on a sample before ingestion.
- **Mapping is conservative**, so recall matters: the sensitivity check above shows it can move a role by 40–190 postings. The other unmatched titles (for example "Financial Plan & Analysis Analyst", "Engineer - ICT/Security", "Product Design Lead") are judgement calls; for example "Analyst - Data Solutions" is not mapped to Data Analyst. `variant_title_inspection.csv` lists every unmatched title for review. The rules affect the counts (30–50% of raw rows were unmatched for some queries).
- **Capped roles** (Software Engineer, Data Scientist, Data Engineer, DevOps, Business Analyst, Product/Project Manager, Graphic Designer) are lower bounds, which is safe for the include decision. Their totals are not yet known.
- **Employer cap**: 5% of a role's postings (about 7–48 per employer). It removed 43–62 postings in Financial Analyst, Data Scientist, Software Engineer and Project Manager. It is configurable and every removal is logged, but the 5% value is a judgement.
- **Snapshot**: one day, three runs within about 30 minutes; API counts drift slightly (Data Analyst 839 → 842).
- **Salary currency/period** unconfirmed; salary presence is low (4–26%).
- **Adzuna terms of use** on storing and redistributing the data were not verified (the documentation pages we could fetch did not state them). Check before publishing raw data. The runs directory is 43 MB and is currently untracked but not git-ignored.
- **Only India** was measured. US/UK counts from the earlier probe were not re-run.
- **Credentials**: the key is in `.env` (git-ignored) for the collector. Because it was pasted in chat, consider rotating it.

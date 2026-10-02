# Dataset Design: Domain → Role → Adzuna Query → Collection Rules → Minimum Data

Prepared 2026-09-30. Machine-readable version: [config/career_scope.json](../config/career_scope.json).
Tags: **[V]** measured in this project's own runs or read verbatim from an official page; **[I]** inference or design judgement.
Nothing here starts production collection, trains a model, or changes the collector.

## 0. Read this first: three issues that change the plan

1. **Adzuna's Terms of Service limit our use.** Verbatim from the [terms of service](https://developer.adzuna.com/docs/terms_of_service) [V]:
   - Rate limits: "25 hits per minute, 250 hits per day, 1000 hits per week, 2500 hits per month".
   - "Any other use of the Adzuna API by a commercial, government or academic organisation … is permitted subject to a 14 day trial period."
   - "This period is strictly for the purpose of validating the general coverage and quality of the data in addition to usability testing."
   - "An API user shall acknowledge Adzuna as the source of all salary and vacancies data wherever it is published."
   - Upon termination the user "shall immediately remove all insertion codes and data acquired from Adzuna from all pages of its web sites."

   **Consequence:** our collection began on 2026-09-29, so the 14-day trial ends around **2026-10-13** [I: the trial start date is not documented]. A one-month collection plan needs Adzuna's written permission first. Section 21 has a fallback if it is refused.
2. **My own feasibility runs exceeded the documented daily limit.** On 2026-09-29 the runs and probes made **642 logged API calls** (492 collection pages, 9 failed attempts, 141 coverage-probe calls; about 648 with hand-made calls; [design_support_audit.json](../data/raw/ml_data_feasibility/design_support_audit.json)) against a stated 250/day. Adzuna never returned HTTP 429 (0 across all runs), so the cap is not hard-enforced, but that is a terms-of-service breach on my part, not something to rely on. About 11 further calls were made on 2026-09-30 for the tests in section 14. All future collection is budgeted inside the stated limits (section 13).
3. **Raw Adzuna data is already in the git history** (`data/raw/adzuna/*.json`, commits before this work). If the repository is public, that is redistribution. Whether it is public was not checked; the team should decide before the next push.

Also confirmed: **the ML target is not chosen here.** Section 9 only defines what salary data would be needed.

**Pre-production gate results (2026-09-30):** see `report/adzuna_compliance.md`, `report/adzuna_api_usage_audit.md` (the daily-limit breach is now measured at **642 logged calls, about 648 with hand-made calls**, peak 23 per minute, 0 HTTP 429), `report/repository_data_exposure.md`, `report/role_mapping_precision_audit.md` (Project Manager fails the 90% bar) and `report/google_trends_anchor_validation.md` (single-anchor plan fails; constant-ratio ladder passes with limits). **This design is not production-ready** until those reports' open items are resolved.

## 1. Project objective

Help job seekers, students and career changers see (1) current employer demand for skills, (2) salary characteristics where data allows, (3) skills per career role, (4) rising/stable/declining skills, (5) skill gaps against a target role, through (6) an interactive dashboard. The capstone also requires predictive modelling, text mining, time-series analysis and combined insights. This design does not change that objective.

## 2. Rubric alignment

| Rubric requirement (as stated by the team) | How this design meets it |
|---|---|
| Dataset collected by the team through API / scraping / surveys / records / synthetic data | Adzuna via its official API using our own scripts; Google Trends via our own script |
| No pre-built datasets (Kaggle, UCI, GitHub, similar) | None used. The Hugging Face candidates investigated earlier are dropped and not used |
| Predictive modelling, text mining, time series, combined insights | Data is designed for all four; the modelling target is decided in the next phase |

Open question for the instructor or team: O*NET and ESCO are official public taxonomies, not job-posting datasets. This design uses them only as reference vocabularies for normalisation. Confirm that this is acceptable under the rubric.

## 3. Final domains (3)

| Domain | Status | Roles |
|---|---|---|
| Technology & Data | Core | Software Engineer, Data Analyst, Data Scientist, Data Engineer, DevOps / Cloud Engineer |
| Business, Finance & Management | Core | Business Analyst, Product Manager, Project Manager, Digital Marketing |
| Media & Design | Core, thin | Graphic Designer (one firm role; UX Designer is conditional) |

The scope is unchanged. Section 20 explains why no domain is added.

## 4. Re-validation of the 10-role core against the evidence

Everything is India, 90-day window, official strict rules, clean = title-mapped, deduplicated, employer-capped [V]. "Salary valid" is salary_min ≥ 100,000 and the mid-point within 100,000–10,000,000 (assumed annual INR).

| Role | API count (primary variant) | Raw rows | Clean | Salary valid | Distinct employers | Top employer % | Near-dup % | Canonical-title clean | Snippet ≥200 chars % | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Software Engineer | 9,129 | 1,650 | ≥875 | 38 | 403 | 5.3 | 17.4 | 735 (84%) | 99.8 | Keep |
| Data Analyst | 842 | 1,208 | 473 | 29 | 348 | 1.9 | 6.7 | 432 (91%) | 100 | Keep; salary below 30 |
| Data Scientist | 1,264 | 948 | ≥604 | 42 | 319 | 5.5 | 11.1 | 347 (58%) | 100 | Keep |
| Data Engineer | 2,805 | 777 | ≥410 | 20 | 259 | 3.9 | 15.8 | 328 (80%) | 99.3 | Keep; only 10 above minimum; salary below 30 |
| DevOps / Cloud Engineer | 822 | 1,825 | ≥854 | 76 | 536 | 1.6 | 13.1 | 336 (39%) | 99.9 | Keep; low canonical share |
| Business Analyst | 1,263 | 1,051 | ≥663 | 41 | 383 | 5.0 | 7.6 | 366 (55%) | 100 | Keep; medium-confidence variants |
| Product Manager | 1,823 | 879 | ≥628 | 35 | 382 | 4.0 | 6.5 | 366 (58%) | 100 | Keep |
| Project Manager | 1,836 | 1,556 | ≥932 | 63 | 581 | 5.2 | 8.0 | 311 (33%) | 100 | Keep; only 11 above canonical floor |
| Digital Marketing | 390 | 639 | 555 | 123 | 418 | 2.3 | 4.8 | 348 (63%) | 99.8 | Keep; complete (API exhausted) |
| Graphic Designer | 571 | 647 | ≥443 | 65 | 388 | 1.8 | 4.5 | 377 (85%) | 100 | Keep; weak text signal (section 14) |

"≥" means a variant hit the per-query record cap, so the true figure is higher. Source: `design_support_audit.json` and `adzuna_label_audit.json` [V].

**The 10-role core is still supported.** Every role meets the measured gates in section 8 except salary-label counts for Data Analyst (29) and Data Engineer (20), and the still-unmeasured mapping precision.

**Modifications this design makes (evidence in each case):**
- Drop three variants: "software development engineer" (0 new clean postings), "reporting analyst" (2 new clean, and it returns Regulatory/Tax/Record-to-Report analysts), "finance analyst" (identical 587 postings to "financial analyst", 0 new).
- Add one exclude pattern to Graphic Designer: `\bmotion graphics? designer\b` (a manual 12-title sample showed "Motion Graphic Designer" entering the role).
- Tag synonym variants as **medium confidence** so analyses can be run with and without them (section 8).

**Known problems in the data, not fixed by the design:**
- Business Analyst: 5 of a 12-title random sample were ERP "functional/systems/product analyst" titles rather than classic business analyst. Project Manager is only 33% canonical "project manager"; the rest are program manager, delivery manager and scrum master. The manual sample is far too small (n=12 per role) to estimate precision; the 50-per-role audit in section 8 is required.
- Adzuna's own `category` is not a usable domain label: 70–99% of the tech and business roles are "IT Jobs" (Project Manager 70%, Data Analyst 80%, DevOps 99%); only Digital Marketing (PR, Advertising & Marketing 86%) and Graphic Designer (Creative & Design 63%) differ [V].

## 5. Domain → role hierarchy, and 6. Adzuna query strategy

Full per-role definitions, patterns and measured baselines are in `config/career_scope.json`. Condensed:

| Role | Query variants (Adzuna `title_only`) | Medium-confidence variants | Excluded patterns (added or existing) | Ambiguous title examples |
|---|---|---|---|---|
| Software Engineer | software engineer; software developer; application developer | application developer | test / testing / qa / quality | SDET; Security Software Engineer |
| Data Analyst | data analyst; bi analyst; business intelligence analyst | – | – | "Data Analyst / Business Analyst" (ambiguous); "Analyst - Data Analytics" (unmatched) |
| Data Scientist | data scientist; machine learning engineer; applied scientist | machine learning engineer | – | Lead ML Engineer (MLOps) |
| Data Engineer | data engineer; etl developer; big data engineer; analytics engineer | analytics engineer | – | "Data Engineering [T500-…]" (unmatched) |
| DevOps / Cloud Engineer | devops engineer; cloud engineer; site reliability engineer; platform engineer | platform engineer | – | AI Platform Engineer |
| Business Analyst | business analyst; systems analyst; functional analyst; product analyst | systems, functional, product analyst | – | Workday HCM Functional Analyst |
| Product Manager | product manager; product owner; associate product manager | product owner | – | Data & Analytics Sales Product Owner |
| Project Manager | project manager; program manager; delivery manager; scrum master | program, delivery, scrum master | construction / civil / site / interior / real estate / mep | Scrum Master |
| Digital Marketing | digital marketing; seo specialist; performance marketing; growth marketer | – | – | Creative Designer (Performance Marketing) |
| Graphic Designer | graphic designer; visual designer; creative designer | creative designer | **motion graphics designer** (added) | UI/UX & Graphic Designer |

**Query principles** [V unless marked]:
- Use `title_only=<phrase>`, never free-text `what` for role assignment. Free text returned unrelated titles in the first pull.
- `title_only` matches words anywhere in the title, not the phrase, and Adzuna stems words (finance ≈ financial). So the API returns non-role titles too, and role membership must come from the title-mapping layer after retrieval.
- Do not use broad queries such as "technology jobs". Queries are exact role phrases and observed synonyms only.
- Narrow synonyms that are subsets of a broader query only add postings when the broader query is capped. Prefer paging the broad query deeper first.

## 7. Mapping strategy

Implemented in `scripts/role_mapping.py` [V]:
- **Normalise:** lowercase, strip accents, non-alphanumerics → single space. The original title is kept unchanged.
- **Match:** explicit regex per role. Statuses: `matched`, `excluded_by_rule` (matched but an exclusion fired), `ambiguous_multi` (several roles matched), `unmatched`.
- **Overlap** is resolved only inside a declared group (security) by priority. Otherwise it is ambiguous, never guessed.
- **Confidence tier (new in this design):** high = the canonical (first) pattern matched; medium = a synonym pattern matched. Ambiguous and unmatched postings get no role.
- **Unmatched titles** stay in the raw data and are listed for periodic review. Across the feasibility run, 30–50% of raw rows for some queries were unmatched, so recall is a known limit: recall-tolerant patterns moved Mechanical Engineer from 256 to 396 clean in the sensitivity check.
- **Role labels come from titles only.** The description is never used to assign a role. This is deliberate, to avoid circularity later: 48.1% of core snippets contain text matching the role's own title rule, and 27.7% restate the full title [V]. Any later model must remove title tokens from features.

## 8. Minimum data requirements

Distinguish **raw collection target** (rows fetched) from **final usable sample** (clean rows). Yield from raw to clean ranged from 0.23 to 0.87 across roles [V], so raw targets are derived from measured yield.

| Requirement | Value | Basis | Measured status |
|---|---|---|---|
| Clean postings per core role | **≥ 400** | Two-proportion test to detect a 10-point difference in a skill's prevalence (e.g. 30% vs 40%) at 80% power needs ≈353 per group; 400 leaves ≈13% headroom for later quality-control losses (standard formula) | All 10 meet (min 410) |
| Skill-frequency floor per role | ≥ 300 | 95% margin ±5.7 points at p=0.5 for n=300 | Met |
| Canonical-title clean per role | ≥ 300 | Guards against a role being mostly medium-confidence synonyms | Met; min 311 (Project Manager) |
| Distinct employers | ≥ 100 | Heuristic to limit clustering | Min 259 |
| Effective number of employers (1/Σ share²) | ≥ 50 | Heuristic; same purpose | Min 95.1 |
| Top-employer share | ≤ 6% | The 5% cap rounds up in small pools | Max 5.5% |
| Near-duplicate rate (of unique ids) | ≤ 20% | Monitoring threshold; above it, investigate employer reposting | Max 17.4% (Software Engineer) |
| Description non-empty | ≥ 99% | – | 100% |
| Description ≥ 200 chars | ≥ 95% | Snippets are capped at ~500 characters | ≥ 99.3% |
| Mapping precision (manual sample, 50 titles per role) | ≥ 90% | Labels should be trustworthy | **Measured 2026-09-30:** 9 of 10 pass (92.3–100%); **Project Manager fails at 85.0%**; ambiguity 32–60% in Data Scientist, Business Analyst, Product Manager, Project Manager (details in `report/role_mapping_precision_audit.md`). Labels are by an AI reviewer and need a human spot-check |
| Raw target per role | = 400 ÷ measured yield × 1.25 | Yield varies by role | Baseline already exceeds it for all 10 |

The thresholds marked heuristic (employers, near-duplicate rate, top share) are not statistically derived; they are monitoring gates and the team may adjust them with justification.

**Salary requirements are defined in section 13**, text mining in section 14 and time series in section 15.

## 9. Raw schema (Adzuna)

Fields **documented** on Adzuna's [search page](https://developer.adzuna.com/docs/search) [V]: `salary_min`, `salary_max`, `salary_is_predicted`, `longitude`, `latitude`, `location`, `description` (documented as a snippet), `created`, `redirect_url`, `title`, `category`, `id`, `company`, `contract_type`, `contract_time`. Not documented there: maximum `results_per_page`, maximum page depth, and truncation length (we measured 50, ≥200 pages deep, and 500 characters).

Field presence over 15,663 raw rows [V]:

| Field | Non-empty % | Note |
|---|---:|---|
| id, title, description, created, redirect_url, category (label, tag), company.display_name, location.display_name, salary_is_predicted | 100 | |
| location.area with ≥ 2 levels (city or state) | 64.4 | otherwise only "India" |
| contract_time | 58.7 | |
| latitude / longitude | 46.2 | |
| contract_type | **15.0** | too sparse to use |
| salary_min / salary_max | **7.0** | includes non-role rows |
| adref | 100 | observed, undocumented; not needed |

Requested items not in the API: `source` and `collection_date` are **ours**, added by the collector as provenance (`source`, `collected_at`, `run_id`, `country`, `query_variant`, `query_role`, `page`, `position`). Raw values are never modified.

## 10. Processed schema and derived fields

One row per unique posting, in `data/processed/`. Raw columns are copied unchanged; everything below is derived and carries provenance.

| Derived field | How | Notes |
|---|---|---|
| domain, role | title mapping (section 7) | Blank if unmatched/ambiguous |
| mapping_status, mapping_tier, matched_pattern | mapping layer | |
| query_variants_seen, first_seen_run, seen_in_runs | dedup | |
| employer_norm, near_dup_key, dedup_status | dedup | |
| salary_annual_inr, salary_flags | section 13 | Never taken from `salary_is_predicted=1` records |
| salary_band | later, if salary modelling is approved | Derived label, not raw |
| seniority_cue | title cue (senior/lead/principal… vs junior/intern…) | Title-derived, not ground truth. 33.8% senior cue, 2.1% junior cue, 64.1% none [V] |
| years_experience_snippet | regex on snippet | 17.0% of snippets contain one [V] |
| skills, skill_count, skill_ids | dictionary v1 matching + O*NET/ESCO ids | Method recorded per row |
| is_truncated_snippet | ends with "…" | 98.7% [V] |
| language_flag | predominantly English? | flag only |
| mapping_ruleset_hash, skill_dictionary_version | reproducibility | |

## 11. Deduplication

Order [V, as implemented in `scripts/analyze_coverage.py`]: (1) exact Adzuna `id`; (2) near-duplicate key = normalised title + normalised employer + first 150 normalised description characters; (3) employer cap = 5% of the role's post-dedup pool, most recent kept, postings with no employer never capped.

Rules to add for multi-run collection [I]:
- **Cross-query:** a posting returned by several variants is one posting. Keep the earliest `collected_at` and list every variant that returned it. In the audit, "finance analyst" contributed 0 new rows because of this.
- **Cross-run:** an id already seen in an earlier weekly run is not new. A repost (new id, same near-duplicate key) counts once, with the first `created` date.
- **Do not remove legitimate distinct postings:** the near-duplicate key includes the employer and the description prefix, so the same title at different employers, or different roles at the same employer, are kept. The known cost is that one employer's genuinely separate per-location openings collapse into one; this is accepted and logged.
- Every removal is logged with role, employer, reason and kept id.

## 12. Employer concentration

The 5% cap is applied per role after near-duplicate removal. Measured after capping: largest single employer 5.5% of a role, 3.26% of the whole core; 73 employers have more than 10 core postings; 2,638 distinct employers across 6,437 core postings [V]. Employer-grouped splitting (later) prevents the remaining concentration from leaking between train and test.

## 13. Salary-data requirements and API budget

**Measured** [V]: 611 core postings carry any salary (9.5%); **532 pass the validity filter** (floor 100,000, ceiling 10,000,000, annual INR assumed). All are employer-stated: `salary_is_predicted` = "0" for every record in every run (0 records flagged predicted). The API has no currency or period field, so currency (INR) and period (annual) are assumptions [I]; 3.3% of salaried snippets mention "per month" and 3.6% mention LPA/lakh. Median valid mid-point is 900,000; 15.6% are point values (min = max). 297 distinct employers appear among the salaried postings; the top 5 account for 19.2%. Salary presence is not random: 27.1% for junior-cue titles, 11.5% for no cue, 4.6% for senior-cue titles. Any salary result must say it describes postings that disclose pay.

| Need | Requirement | Basis | Status |
|---|---|---|---|
| Descriptive salary per role | ≥ 30 valid labels | Below this a median is too unstable to publish | 8 of 10 core roles meet; Data Analyst 29, Data Engineer 20 do not |
| Pooled salary-band model | ≥ 750 valid labels, ≥ 250 per band (3 bands) | Split 60/20/20 by employer gives a 150-row test set (≈50 per band); accuracy CI half-width ≈ ±7.7 points at 60% accuracy | **532 now; short by 218** |
| Never use | records with `salary_is_predicted = 1`, Adzuna's own estimates, or the API `mean` field as ground truth | Requested constraint | 0 predicted records so far |
| Band construction | pooled quantile bands (3 bands: 158 / 193 / 181 today) | Equal-frequency bands avoid empty classes | Defined; not fitted |
| Outliers | flag, do not delete (below floor, above ceiling, min > max) | Auditable | 1–20 per role flagged |
| Do not lock salary prediction | – | Requested | Decision belongs to the next phase |

**Reaching 750:** at 9.5% salary presence, 218 more valid labels needs about 2,300 more clean core postings. The measured last-7-day inflow lower bound is about 1,555 for 8 of the 10 core roles [V], so two to three weekly increments could plausibly reach it [I; newly created ads may disclose pay at a different rate].

**API budget for the plan** [I, from measured page costs]:

| Activity | Calls | Basis |
|---|---:|---|
| Baseline for 10 core roles (already spent) | 234 pages | measured |
| Weekly increment (`max_days_old=7`), 10 core + 3 conditional roles | ~60–75 per week | 1,555+ posted per week ÷ 50 per page, plus ≥ 1 page per variant (about 40 variants) |
| Skill-prevalence count probe (section 14): 10 roles × 30 skills, 90-day window | ~300 per snapshot | 1 call per role-skill pair |
| 3 weekly increments + 2 count-probe snapshots | ~ 800–850 for the month | ≈ 34% of the 2,500 monthly limit; peak week ≈ 375 of 1,000 |

The count probe must be spread over at least two days because of the 250/day limit.

## 14. Text-mining requirements

**Snippets are the binding constraint.** Descriptions are capped at 500 characters: 98.7% of core snippets end with "…", median length is exactly 500, and 9.3% contain employer boilerplate [V]. With a 95-term seed lexicon, **61.9% of snippets contain zero detected skills and only 8.7% contain three or more**; the worst role is Graphic Designer (77.9% zero, 1.4% with three or more) and the best is DevOps / Cloud Engineer (46.3% zero; Data Engineer 50.7%) [V]. Snippet skill frequencies are therefore lower bounds and are biased toward a posting's opening lines.

**A new, verified way to see past the snippet** (tested 2026-09-30, India, 90 days, `results_per_page=1`) [V]:
- `title_only=<role>` combined with `what=<skill>` composes as AND. A nonsense term returns 0.
- For Data Engineer: 1,851 of 2,796 ads (66.2%) match `what=python`, while only 14.4% of our stored Data Engineer snippets mention Python. So Adzuna's search covers text beyond the snippet, and snippet-only frequency is about **4.6× lower** for this skill.
- Multi-word skills need `what_phrase`: "power bi" gave 312 with `what` (both words anywhere) and 190 with `what_phrase`, out of 841 Data Analyst ads.
- The share was stable across age windows: Python among Data Engineer ads was 65.0% (7 days), 64.7% (30 days) and 66.2% (90 days).

**Limits of that method:**
- `title_only` denominators include non-role titles, so they differ from our mapped role sets. Within our own data, skill prevalence differs between title-mapped and unmapped rows of the same queries by up to 10–12 points (Data Analyst SQL 11.5% vs 1.4%; Data Engineer SQL 18.9% vs 7.0%) [V].
- **Not confirmed by Adzuna's official pages.** The static documentation pages I could read (search, overview, historical) do not mention `title_only`, `what_phrase` or `max_days_old`, and do not say whether `what` searches the full description or only the snippet; the interactive reference they point to could not be rendered. These behaviours are our own empirical findings (1 day, India), to be confirmed with Adzuna [V for our tests, unconfirmed by the vendor].
- **API filter counts are not skill prevalence.** Use them only where the denominator is role-specific. `title_only` counts words anywhere in the title, so a role's API denominator includes non-role titles; the count-probe therefore says "how many ads in this title-word set mention the skill", not "what share of the role's postings require it".
- It needs a skill list in advance and costs one call per role-skill pair.

**Final text-mining methodology (three parts, all labelled in every output):**
1. **Observed snippet skill frequency** on title-mapped clean postings: the primary table. It is a **lower bound** of what employers require (61.9% of snippets contain no seed-lexicon skill; Python appears in 14.4% of stored Data Engineer snippets against 66.2% of the API's matching ads), biased toward a posting's opening lines. It is role-pure but low-recall.
2. **Validated API/search signal, where appropriate:** for each role, require Spearman rank correlation ≥ 0.7 between the snippet ranking and the API count-probe ranking before showing the probe beside it. Present probe values as "share of ads in the title-word set that mention the skill", never as role prevalence, and never as a replacement for the snippet table. The 0.7 gate is a proposal, not from a source.
3. **Explicit limitation text** in the dashboard and report: "Adzuna returns only a ~500-character snippet; skill shares are lower bounds, not complete employer requirements; API search counts include non-role titles."
No output may claim exact true skill prevalence. Snippet frequencies are never inflated or rescaled by the API ratio.

| Item | Target | Note |
|---|---|---|
| Skill vocabulary | 150–250 canonical skills across the 3 domains, starting from the 95-term seed | [I] sized so that the top ~100 skills cover the demand analysis |
| Inclusion rule | ≥ 20 postings and ≥ 2% of a role's postings | Below this a frequency is noise |
| Normalisation | lowercase, word-boundary match; synonyms table (e.g. "powerbi" → Power BI); ambiguous tokens (R, Go, C, Excel) need context rules | |
| Taxonomy | Map each skill to ESCO and/or O*NET ids where a match exists; keep unmatched skills as project-local ids | See note |
| Extraction method | dictionary matching = **rule-based extraction, not machine learning** | |
| Gate | ≥ 300 skill-bearing postings per role, or the role is flagged "text-mining limited" | At 22% skill-bearing yield, Graphic Designer would need ~1,360 clean postings, so it is flagged now |

**Taxonomy note.** O*NET is CC BY 4.0, database release 31.0 ([onetcenter.org license page](https://www.onetcenter.org/license_db.html)); ESCO is v1.2.1 with 13,939 skills in 28 languages, EU content licensed CC BY 4.0 ([ESCO skills page](https://esco.ec.europa.eu/en/classification/skill_main), [copyright notice](https://esco.ec.europa.eu/en/copyright-notice-esco-skills-competences)) [V]. They are reference vocabularies, not job-posting data. That O*NET is US-centric and ESCO EU-centric, and that many current tools are missing from both, is an expectation to test, not a measured fact [I].

## 15. Time-series requirements

**Adzuna does not provide a long time series.** It is a 90-day cross-section of postings that are still live. The created-date profile is heavily skewed to recent weeks (79.2% of core postings in the last 30 days of the window) and the `sort_by=date` cap under-samples older weeks, so the profile is not a growth measure [V]. In the count test, 582 of 2,796 Data Engineer ads (20.8%) were created in the last 7 days, versus about 7.7% if evenly spread over 13 weeks, which again reflects survival of recent ads, not growth [V/I]. **Do not describe Adzuna counts as trends.**

What Adzuna can add over the project month:
- Weekly incremental pulls (`max_days_old=7`) give 3–5 weekly points of posting inflow and skill share per role: a **freshness view**, not a trend classification.
- A recent-vs-older contrast within one snapshot (e.g. skill share in ads ≤30 days old vs 31–90 days old); Data Engineer Python was 64.7% vs 68.6% [V/I]. Label it clearly as an age contrast with survivor bias.
- Adzuna's [historical endpoint](https://developer.adzuna.com/docs/historical) returns **monthly average salary**, not skills or vacancies (its documented example shows 2013 data for `gb`). It is a possible salary-trend context and its India coverage has not been tested [V for the documented behaviour, unknown for India].

**Rising / stable / declining skills therefore rest on Google Trends**, which provides ≥ 260 weekly observations per skill over five years [V]. Minimum requirements: ≥ 260 weekly points and ≥ 80% non-zero weeks per skill (else drop, or aggregate to monthly). Aggregation period: weekly, smoothed with an 8-week rolling median; classification by slope over the last 24 months with a trend test [I, unchanged from the feasibility report]. Missing weeks are left missing, not zero-filled.

## 16. Google Trends design

Separate raw store (`data/raw/trends/`), never merged into Adzuna rows.

| Field | Meaning |
|---|---|
| skill_id, skill_label | project skill key (linked to ESCO/O*NET id where one exists) |
| query_string, query_type, category | exact query sent (plain term or topic id), and category filter if used |
| geo | `IN` primary; `US` optional; worldwide as a check |
| date | week start |
| interest_raw | integer 0–100 exactly as returned |
| is_partial | Trends' partial-period flag |
| batch_id, anchor_term, anchor_value | which request it came from and the anchor's value in it |
| timeframe, source, collection_date | e.g. "today 5-y", `google_trends`, pull date |
| interest_chained | **derived in processed/**, never in raw |

**Verified facts** [V]: each point is "divided by the total searches of the geography and time range it represents" and scaled 0–100 by proportion; low-volume terms "appear as '0'"; data is sampled and contains statistical noise ([Google Trends help](https://support.google.com/trends/answer/4365533)). Google's official Trends API is alpha and application-only, and offers "consistently scaled data" that can be merged across requests ([developers.google.com/search/apis/trends](https://developers.google.com/search/apis/trends)); we have not applied for it. Our own test with the unofficial `pytrends` package returned 262 weekly rows for a 5-year window and accepted 5 terms per request, but Power BI scored about 4 and Tableau about 2 against a SQL anchor. Whether `pytrends` is supported or stable was not verified from an official source.

**Comparison across batches (validated 2026-09-30, see `report/google_trends_anchor_validation.md`):** relative scale is only valid within a request, and a single SQL anchor for every skill **fails** the resolution rule (9 of 11 tested terms scored below 10 points against it). Use an **anchor ladder with constant-ratio chaining**: link requests only by the ratio of the shared anchor's mean level, never by dividing weekly values by the anchor's weekly values; keep rungs about 5× apart so every skill is measured at 10 or more points. Tested: two rungs, 12 skills, one geography, two days: chained and direct levels agreed within 0.1–3.1%, and cross-day differences were 0.1–0.4%. Not yet tested: a third rung, ambiguous terms, other geographies. Never compare raw values from different batches.

**Skill selection** (60 skills initially, about 15 requests per geography [I]): take skills that pass the inclusion rule in section 14, drop ambiguous terms unless a topic id or category disambiguates them (Java, R, Go, Rust, Swift, Spark, Excel), and drop soft skills. Screen by non-zero week share. Keep the query text, category and keep/drop reason per skill.

## 17. Storage and layout

```
data/
├── raw/
│   ├── adzuna/
│   │   ├── runs/<run_id>/            # search pulls: run_manifest.json, queries.jsonl, attempts.jsonl, records_*.jsonl   (exists)
│   │   ├── counts/<probe_id>/        # count-probe results (skill x role counts), same manifest style              (new)
│   │   └── *.json                    # legacy 2026-09-29 relevance-sorted pulls, preserved unchanged
│   └── trends/                       # Google Trends batches + pull logs, never mixed with Adzuna
├── processed/                        # deduplicated, mapped, derived-field tables (parquet/csv), rebuilt from raw by script
├── metadata/                         # career_scope.json copy, data dictionary, skill dictionary versions, mapping ruleset hash
└── audits/                           # coverage, dedup-removal, precision-sample and QC outputs
```
`data/raw/ml_data_feasibility/` (this audit's small outputs) may be moved to `data/audits/`. Raw data is append-only. Processed tables are always regenerable from raw plus the versioned config.

## 18. Data-quality checks (run after every collection)

1. `title_only`, `max_days_old`, `sort_by` present in every recorded request (already asserted in `audit_checks.json`).
2. Zero rows before the calendar-day window start; created dates non-increasing per query.
3. API `count` logged for every query; log drift between runs.
4. HTTP failure and retry totals; any query not `complete`.
5. Role-level gates from section 8; exact and near-duplicate removal counts per role.
6. Mapping status counts per run; new unmatched titles reviewed.
7. Salary flags (floor, ceiling, inverted, point values, predicted flag).
8. Language flag rate; snippet-length distribution; boilerplate rate.
9. Manual mapping-precision sample (50 titles per role) recorded with reviewer initials and date.
10. Credentials never present in any stored file (already checked).
11. Attribution "Jobs by Adzuna / source: Adzuna" present wherever results are displayed.

## 19. Final collection-size estimate

**Baseline (collected 2026-09-29) [V]:** 6,437 clean core postings (10 roles, from 234 pages); with UX (345), Financial Analyst (292) and the merged security family (498 by union, 510 by the joint pipeline) the audit set is 7,572.

**Planned increments [I]:** three weekly pulls of new postings (`max_days_old=7`). The measured last-7-day inflow lower bound is 1,555 clean postings for 8 of 10 core roles (Software Engineer and Data Engineer were capped, so their inflow is at least, not exactly, measurable), so roughly 1,500–2,500 new raw postings per week before deduplication [I], of which perhaps 75–85% survive deduplication [I from the 8–17% near-duplicate rates]. That gives about **+3,500 to +6,000 clean postings**, for a total of roughly **10,000–13,500 clean postings** across 13 role families, well under 100 MB and easy for the notebooks. Expected salary-valid labels then reach about 850–1,100 if new postings disclose pay at the same 9.5% rate [I].

| Data set | Target |
|---|---|
| Clean core postings, minimum per role | 400 (all met by baseline) |
| Clean core postings, planned total | ~6,400 baseline → ~10,000–13,000 after increments |
| Salary-valid labels | ≥ 750 pooled (532 now) |
| Distinct employers per role | ≥ 100 (min 259 now) |
| Adzuna snapshots | baseline + 3 weekly + 2 count-probe snapshots |
| Google Trends series | ~60 skills × 1–2 geographies ≈ 60–120, plus anchors |

## 20. Domain-expansion decision

**No domain is added.** The five criteria (coverage, distinguishable roles, business value, scope, same pipeline) are not met by any candidate:
- **Engineering** fails coverage: 256 / 210 / 269 clean, and 396 / 373 / 266 under a recall-tolerant rule; none reaches 400.
- **Architecture & Construction:** the "architect" count is 72.1% IT architects and 2.5% likely building architects; a clean building-architecture role does not exist in this data.
- **Healthcare, Logistics, Energy:** India title counts were single or double digits for most roles in the feasibility probe [V, earlier report]; not re-measured.
- Accounting / HR were probed earlier (India 1,560 and 417 title matches) but their skills are certification-driven and hard to trend [V counts; I on skills]. They would add breadth, not the same analytical pipeline.

Media & Design is retained but is thin (one firm role). If UX Designer is promoted under the promotion rule in the spec, it becomes a two-role domain.

## 21. Production collection plan

**Gate 0 (before any further API use):**
1. Ask Adzuna in writing whether academic use may continue beyond the 14-day trial, and obtain the answer in writing. I could not verify a contact address or process from the pages fetched.
2. Decide what to do about raw Adzuna data in the repository's git history if it is public.
3. Approve the spec (`config/career_scope.json`) or amend it.

**If Adzuna consents:**
- Week 0: manual precision audit (50 titles per role); apply the three dropped variants and the Graphic Designer exclusion to the config; build the processing layer that merges runs, deduplicates across runs and writes `data/processed/`.
- Weeks 1–3: weekly increment run (`max_days_old=7`, all 10 core + 3 conditional roles), staying under 1,000 calls per week.
- Week 1 and week 3: count-probe snapshot (~300 calls each, spread over two days).
- In parallel: Google Trends collection with the anchor ladder (separate raw store).
- End of week 3: apply the section 8 gates, decide promotions (UX Designer, Financial Analyst, security) and freeze the dataset.

**If Adzuna refuses or does not answer:** stop API use at the end of the trial. The baseline dataset already collected is the project's Adzuna dataset; the analysis is a single 90-day snapshot; salary modelling is not attempted (532 < 750); skill demand is snippet-based and clearly labelled as a lower bound; the temporal component rests entirely on Google Trends. All results must acknowledge Adzuna as the source.

**Does the current collector need modification?** The collector itself needs no fix: `title_only`, `max_days_old`, `sort_by`, retries and provenance all work as audited. It needs three small additions in the next phase, none done now: (1) read `config/career_scope.json` (or a converter that writes the collector's existing config format), including the added exclude and dropped variants; (2) a separate count-probe script that stores its raw responses under `data/raw/adzuna/counts/`; (3) a processing step for cross-run deduplication and derived fields. Redundant variants can already be removed by editing the config.

## Appendix: what was and was not verified here

| Verified (measured or read from an official page) | Not verified |
|---|---|
| Adzuna terms of service (verbatim); documented search fields; historical endpoint behaviour; field presence rates; API call counts; AND behaviour of `title_only` + `what`; `what_phrase` difference; age-window shares; O*NET 31.0 and ESCO v1.2.1 licence and version; Google Trends scaling and low-volume behaviour; Trends API alpha status | Whether the 14-day trial clock started on 2026-09-29; Adzuna contact/consent process; whether `what` searches the full description (evidence is strong but the documentation does not say); mapping precision (only a 12-title-per-role glance); `pytrends` support status; O*NET/ESCO coverage of current tools and of Indian roles; whether the git repository is public; India coverage of the historical endpoint |

Files produced for this phase: `config/career_scope.json`, this report, and small audit outputs under `data/raw/ml_data_feasibility/` (`design_support_audit.*`, `adzuna_label_audit.*`, `adzuna_fulltext_filter_test.json`, `mapped_vs_unmapped_skill_prevalence.json`, `build_career_scope.py`).

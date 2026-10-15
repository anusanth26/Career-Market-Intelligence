# Adzuna Terms and Authorization: Compliance Review

**Date verified:** 2026-09-30. **Status of Gate A (Adzuna use is contractually understood): NOT MET.** Written consent is needed and has not been requested or obtained.

**Method and limits.** I read the official pages with a web-fetch tool that returns extracted or summarised text (it declined to reproduce the whole terms page). Clauses quoted below are the tool's exact excerpts of the official page, cross-checked by a second extraction and by a search-result snippet of the same page. This is **not legal advice**, and someone on the team should read the primary page in full before relying on any reading here.

## 1. Sources

| Source | URL | What it gave |
|---|---|---|
| Terms of Service (primary) | https://developer.adzuna.com/docs/terms_of_service | rate limits, permitted uses, trial period, consent, attribution, confidentiality, termination |
| Developer overview | https://developer.adzuna.com/overview | registration only; **no** rate limits, terms, or contact channel on this page |
| Search documentation | https://developer.adzuna.com/docs/search | documented result fields; the "snippet" statement; lists only `what`, `what_exclude`, `where`, `sort_by`, `salary_min`, `full_time`, `permanent`, `results_per_page` in its examples |
| Historical data documentation | https://developer.adzuna.com/docs/historical | historical endpoint returns monthly salary averages |
| Interactive endpoint documentation | https://developer.adzuna.com/activedocs | **could not be read** (returned navigation only), so the full parameter list is unverified |

The terms page shows no "last updated" date.

## 2. Clauses relevant to this project

Verbatim excerpts from the Terms of Service page:

1. "25 hits per minute, 250 hits per day, 1000 hits per week, 2500 hits per month".
2. The API "may be used for: 1. Publishing Adzuna ad listings 2. Publishing Jobsworth salary estimates 3. 'Personal research'".
3. "Any other use of the Adzuna API by a commercial, government or academic organisation including any affiliates or individuals, is permitted subject to a 14 day trial period."
4. "This period is strictly for the purpose of validating the general coverage and quality of the data in addition to usability testing. It may not be used in its 'original format or in aggregation' (including but not limited to vacancy counts, average salaries etc)".
5. "It may not be used in its original format or in aggregation … to deliver any ongoing work or research, apart from the purpose stated prior, without written consent."
6. "After the trial period ends, a licence agreement may be required."
7. "An API user shall acknowledge Adzuna as the source of all salary and vacancies data wherever it is published … Personal or academic research: … References should refer to: 'The Adzuna API' and link to http://www.adzuna.co.uk/".
8. "An API user shall not disclose Adzuna Confidential Information without Adzuna's prior written consent." (The term "Confidential Information" is not defined in the excerpts I saw.)
9. "Upon termination of this agreement, for any reason and by either party, an API user shall immediately remove all insertion codes and data acquired from Adzuna from all pages of its web sites."
10. "Either party may terminate this Agreement at any time." Termination: "To notify Adzuna of termination simply email info [at] adzuna [dot] com."
11. Attribution when publishing ad listings: a "Jobs by Adzuna" label (at least 116 × 23 px) with links; for salary estimates an "Adzuna Jobsworth" icon (20 × 20 px). (From the first extraction; not re-confirmed in the second.)

An earlier extraction also reported that higher limits are available on request for commercial applications; that was not re-confirmed, so treat it as unverified.

## 3. Answers to the twelve questions

| # | Question | Answer | Basis |
|---|---|---|---|
| 1 | Current API rate limits | 25/min, 250/day, 1,000/week, 2,500/month | Clause 1 (verified) |
| 2 | Academic / research use conditions | Personal research is a listed use. "Any other use" by an academic organisation is "permitted subject to a 14 day trial period" | Clauses 2–3 |
| 3 | Does the 14-day trial apply to us? | **Unclear.** A college capstone could be read as "personal research" (no trial) or as academic-organisation use (trial applies). The safest reading is that the trial applies | Clauses 2–3; interpretation is mine |
| 4 | What happens after the trial? | "A licence agreement may be required", and data may not be used for ongoing work or research without written consent | Clauses 5–6 |
| 5 | Is written permission required for continued academic use? | **On the text, yes** for use beyond trial validation, unless the use is "personal research". Not certain, so ask | Clause 5 |
| 6 | Is our intended volume permitted? | The plan's volume (about 900 calls in a month) is under the caps if scheduled inside them. Volume is not the problem; permission is | Clause 1 and the plan in `report/dataset_design.md` |
| 7 | Storing raw API results locally | **Not addressed** in the terms | Second extraction: "NOT ADDRESSED" |
| 8 | Processing or storing derived data | **Not addressed** explicitly, but clause 4 names "aggregation (… vacancy counts, average salaries etc)", which is what our derived data is | Clauses 4–5 |
| 9 | Publishing aggregated statistics in a college dashboard or report | **Probably needs written consent**, because clause 4 lists aggregates such as vacancy counts and average salaries among the uses that need consent after the trial. If allowed, attribution applies (clause 7) | Clauses 4, 5, 7 |
| 10 | Attribution | Acknowledge Adzuna as the source of all salary and vacancies data wherever published; reference "The Adzuna API" linking to adzuna.co.uk. "Jobs by Adzuna" and the Jobsworth icon apply only if listings or salary estimates are displayed | Clauses 7, 11 |
| 11 | Restrictions on redistributing raw job-posting data | No explicit rule found for job data. There is a non-disclosure clause for "Confidential Information" (undefined here) and a duty to remove data from web sites on termination. Treat raw redistribution as **not permitted until confirmed** | Clauses 8–9 |
| 12 | Restrictions relevant to GitHub or public repositories | **Not addressed.** By analogy with clause 9 (data on "web sites") a public repository holding raw postings is a risk | Second extraction: "NOT ADDRESSED"; inference |

## 4. Implications for this project

1. **We cannot claim permission.** Nothing obtained so far allows ongoing use. All the collection to date fits inside "trial / validation" at best, and clauses 4–5 restrict even that data from being used for ongoing analysis in aggregate form without consent.
2. **Trial clock.** Our own logs show first API activity on 2026-09-29, so a 14-day trial would end about **2026-10-13** if it started that day [inference; the start date is not documented and an earlier registration could shorten it].
3. **Do not start weekly collection or count-probe snapshots until written consent is in hand.** Both are "ongoing work".
4. **Dashboard and report.** Until consent is obtained, do not present Adzuna counts, shares or salary averages in a public dashboard. Whatever is presented must acknowledge Adzuna as the source.
5. **Repository.** Raw Adzuna records (and derived text files) must not be in a public repository. See `report/repository_data_exposure.md`.
6. **Parameter documentation gap.** Our collector relies on `title_only`, `max_days_old` and `sort_by=date`. None of the static documentation pages I could read mention `title_only` or `max_days_old`. They work in practice (our own tests) but are not confirmed in the pages I could read. Ask Adzuna for the parameter reference (question 7 below).
7. **If consent is refused or never arrives:** stop API use, keep only what is permitted, and document the project as using a single validation snapshot (see the fallback in `report/dataset_design.md` section 21).

## 5. Questions to send to Adzuna

(Also included in `report/adzuna_permission_request.md`.)

1. Is a student college capstone project treated as "personal research" (no trial) or as academic-organisation use under the 14-day trial?
2. May we use the collected data in aggregate form (counts, shares, medians) for our analysis and report beyond the trial? Please confirm in writing.
3. May we store raw API responses locally and in a private, access-controlled repository for reproducibility and grading?
4. May we display aggregated results in a course dashboard? What attribution wording do you require ("The Adzuna API" with a link)?
5. Is sharing the raw responses privately with course instructors and graders acceptable?
6. Please confirm the current limits (25/min, 250/day, 1,000/week, 2,500/month) and whether the week and month are rolling or calendar periods, and whether a higher limit is possible for a short academic project.
7. Please point us to the reference for the search parameters `title_only`, `what_phrase`, `max_days_old` and `sort_by=date`, and tell us whether `what` searches the full job description or only the stored snippet.
8. What data retention or deletion is required when the project ends?
9. Which address should permission and licence requests go to? (The only address on the terms page is info@adzuna.com, listed for termination.)

## 6. Status

| Item | Status |
|---|---|
| Official terms re-read on 2026-09-30 | Done |
| Written permission | **Not requested, not obtained** |
| Permission request drafted | Yes: `report/adzuna_permission_request.md` (not sent) |
| Storage / redistribution / repository rules | Not addressed by the terms; must be answered in writing |

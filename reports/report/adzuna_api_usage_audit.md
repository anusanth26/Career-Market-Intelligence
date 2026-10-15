# Adzuna API Usage Audit (Incident Report)

**Date of audit:** 2026-09-30. **Method:** local run logs and probe output only; no API calls were made for this audit. Script and raw result: `data/raw/ml_data_feasibility/compliance_audit.py` / `compliance_audit.json`. The credential values were never printed or stored.

## 1. Summary

- On **2026-09-29 (UTC)** the project's collection runs and the coverage probe made **642 logged API calls** against a documented limit of **250 per day**. Adding about six hand-made calls that day gives roughly **648**, about **2.6 times the daily limit**.
- The per-minute limit (25) was **not** exceeded: the peak was **23 calls in one clock minute**, and no run windows overlapped.
- Adzuna returned **no HTTP 429** responses. The cap is therefore not hard-enforced, but that does not make the usage compliant.
- The weekly (1,000) and monthly (2,500) caps were not exceeded: about 659 calls in the last two days.
- This was caused by **my own runs** during the feasibility work. The collector has per-minute pacing but **no daily budget guard**, and I did not check the daily limit before launching the completion pulls. I did not tell you about the terms of service limits until they surfaced in the dataset-design research; the discrepancy first appeared in that report.

## 2. Facts from the logs

Dates are UTC. "Calls" = successful pages + failed attempts (each retry is another call) + the probe's calls.

| Date | Activity | Calls | Source |
|---|---|---:|---|
| 2026-09-29 | Coverage probe (47 role titles × 3 countries, 1 call each; 17:20 to about 17:27) | 141 | `coverage_2026-09-29.json`, pacing 2.6 s + response time |
| 2026-09-29 | Smoke run (17:40) | 16 | `queries.jsonl` |
| 2026-09-29 | Main feasibility run (17:41 to 17:57) | 330 | `queries.jsonl` |
| 2026-09-29 | Completion run "deepen" (17:58 to 18:07), including 9 failed attempts | 123 + 9 = 132 | `queries.jsonl`, `attempts.jsonl` |
| 2026-09-29 | Security completion run (18:08 to 18:09) | 23 | `queries.jsonl` |
| **2026-09-29 total logged** | | **642** | |
| 2026-09-29 | Hand-made calls in the chat session (category list, a UK count check, three pagination-depth checks) | about 6, not logged | conversation |
| 2026-09-29 | Earlier team pull with the original collector: 4 categories × 13 pages | about 52 | `pull_log_2026-09-29.json`; a **different app id** (its redirect URLs carry another `utm_source`), so probably a separate quota; time of day unknown |
| 2026-09-30 | Full-text filter tests (4 + 7 calls) | 11, logged only in `adzuna_fulltext_filter_test.json` | file |

| Question | Finding |
|---|---|
| Exact dates of activity | 2026-09-29 (all runs), 2026-09-30 (11 test calls) |
| Approximate calls per date | about 648 on 09-29 (project key); 11 on 09-30 |
| Daily limit exceeded? | **Yes**, on 09-29 (about 648 vs 250) |
| Per-minute limit exceeded? | No. Peak 23 per clock minute; 0 minutes above 25; no overlapping runs |
| Weekly / monthly limit exceeded? | No (about 659 in the current week and month) |
| Any HTTP 429? | **0** in every run |
| Failed attempts | 9, all HTTP 503 (Adzuna's HTML error page) in the "deepen" run |
| Did retries add calls? | Yes: 9 retries were needed to recover 4 pages. They are included in the 642 total |
| Credentials present in files? | The API key is in `.env` only. It is **not** in any tracked file, any other working-tree file, or any commit on any local or remote-tracking branch. See `report/repository_data_exposure.md` |

Caveats: the probe's per-call timing is assumed from its sleep setting, not logged; the hand-made call count is an estimate from the conversation; whether Adzuna measures a "day" in UTC is unknown.

## 3. What went wrong

1. **No daily budget guard.** `scripts/collect_adzuna.py` waits 2.6 s between calls and stops after repeated failures, but it never counts calls per day.
2. **The limits were unknown to the run planning.** I sized the runs from page counts and did not read the terms of service until later. I estimated the main run at 549 calls in the dry run, which itself was above 250, and proceeded.
3. **Follow-up pulls piled on.** After the main run I added two completion runs and a probe to remove capped-sample uncertainty. Each looked small on its own.

## 4. What was not affected

- No attempt was made to bypass limits, and I made no request to test a limit.
- No data was collected by any means other than the official API.
- No key or other credential was exposed in the repository.

## 5. Corrective actions

**Done now:** this audit; no further API calls beyond the 11 already listed on 2026-09-30 (those were before this gate).

**Not done (needs your approval and belongs to the next phase, since the collector must not change in this phase):**

| Guardrail | Design |
|---|---|
| Call ledger | Append one line per call to `data/raw/adzuna/api_ledger.jsonl` (UTC timestamp, run id, status). Never delete it |
| Pre-flight budget check | Before any run, compute the rolling counts from the ledger; refuse to start if the planned calls would exceed the internal caps below |
| Internal caps (conservative) | 200 per UTC day (80% of 250), 800 per rolling 7 days, 2,000 per rolling 30 days, at most 20 calls per minute |
| 429 handling | Stop the run at the first 429, wait until the next window, and do not retry in a loop; retry only transient 5xx, at most 2 times |
| Dry-run estimate | Print estimated calls and compare with the budget before starting (the dry run already prints an estimate) |

## 6. Compliant future schedule (only if written permission is obtained)

Assume the worst case that Adzuna measures the week and month as rolling periods. The 2026-09-29 activity (about 648 calls) stays in the rolling week until 2026-10-06 and in the rolling month until 2026-10-29.

| Step | When (relative to consent date D, no earlier than 2026-10-06) | Calls | Notes |
|---|---|---:|---|
| Precision audit fixes, processing layer | before any calls | 0 | no API use |
| Weekly increment 1 (`max_days_old=7`, 10 core + 3 conditional roles) | D + 0 | 60–75 | one day |
| Count probe snapshot 1 (10 roles × 30 skills) | D + 1 and D + 2 | 150 + 150 | two separate days, each under 200 |
| Weekly increment 2 | D + 7 | 60–75 | |
| Weekly increment 3 | D + 14 | 60–75 | |
| Count probe snapshot 2 | D + 15 and D + 16 | 150 + 150 | |
| Reserve for QC re-pulls | D + 21 to D + 27 | up to 100 | only if needed |
| **Total** | | about 750–900 | |

Checks against the caps:
- **Per day:** the largest day is 150, under 200.
- **Rolling 7 days:** the heaviest week is increment 1 plus snapshot 1, about 375, under 800.
- **Rolling 30 days:** about 900 plus the Sept 29 activity that has not rolled off = about 1,550 in the worst case, under 2,000 (and under the documented 2,500).

If permission is not obtained, **the schedule is empty**: no further collection.

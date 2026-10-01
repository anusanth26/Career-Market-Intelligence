# Google Trends Anchor Validation

**Date:** 2026-09-30. **Verdict: the anchor-ladder method is defensible for comparing skills across batches, with corrections and limits stated below. The original single-anchor plan (SQL for every skill) is not.** This was a small test, not a data collection. Script: `data/raw/ml_data_feasibility/trends_anchor_test.py`. Raw results: `trends_anchor_test.json` and `trends_anchor_test/*.csv` (kept apart from `data/raw/trends/`).

## 1. Background: why anchors are needed

Google's help page states that each data point "is divided by the total searches of the geography and time range it represents" and then "scaled on a range of 0 to 100 based on a topic's proportion to all searches on all topics"; low-volume terms "appear as '0'", and results are sampled and carry "statistical noise" ([Google Trends help](https://support.google.com/trends/answer/4365533)). So the values in one request are relative to that request's most-searched term, and separate requests cannot be compared directly. Google's official Trends API (alpha, application-only) offers "consistently scaled data", but we have not applied for it ([developers.google.com/search/apis/trends](https://developers.google.com/search/apis/trends)). We used the unofficial `pytrends` package, whose support status was not verified from an official source.

## 2. What was tested

- **Query structure:** geo `IN`, `today 5-y` (262 weekly points), 5 terms per request, category all, plain terms (no topic ids). Terms were 12 skills from the core roles: SQL, Python, Docker, Kubernetes, Tableau, Power BI, Figma, SEO, Jira, Terraform, Snowflake, Photoshop.
- **Requests completed (7):**
  - `B1`, `B2`, `B3`: three survey requests, each with SQL as the shared anchor.
  - `B1` repeated twice: a repeatability test.
  - `L1`: a second-rung request anchored on Photoshop, containing four low-volume skills (Terraform, Snowflake, Tableau, Kubernetes).
  - `G1`: a direct co-request of the same four skills with SQL.
- **Cross-day check:** yesterday's smoke request (SQL, Python, Power BI, Tableau, Excel; 2026-09-29) compared with today's `B1`.
- **Criteria declared before running** (proposals, not from a source): R1 repeatability (median difference ≤ 2 points, r ≥ 0.98); R2 the ratio of a term to the anchor differs ≤ 15% between two requests that both contain the pair; R3 chained vs direct level error ≤ 15% when the direct value has a mean ≥ 10 points; R4 a term is usable in a request only if its mean is ≥ 10 points (integer rounding then ≤ about 5% of the mean).
- **Rate limiting:** Trends returned HTTP 429 on requests 6 and 7 of 7 (with 18–28 s between requests) and recovered after waits of 60–120 s. Only one direct-co-request pair was affected; all 7 planned requests finished. A production run needs slower pacing and resumability.

## 3. Results

**R1 repeatability: passes, but uninformative.** Three identical requests made minutes apart returned **bit-identical** series (max difference 0 points, r = 1.0 for every term). That suggests responses were cached within the session, so this test cannot show day-to-day sampling variation. The cross-day check below is the meaningful one.

**Cross-day stability (2026-09-29 vs 2026-09-30, different companion terms, same 262 weeks):**

| Quantity | 09-29 request | 09-30 request | Difference | Series correlation |
|---|---:|---:|---:|---:|
| Python / SQL (ratio of 5-year means) | 2.0636 | 2.0651 | 0.1% | 0.9996 |
| Tableau / SQL | 0.0842 | 0.0846 | 0.4% | 0.968 |
| SQL series | – | – | – | 0.9985 |

The lower correlation for Tableau (0.968) comes from integer rounding at about 3 points, not from disagreement in level.

**R2 companion independence: passes.** Docker/SQL was 0.1783 in `B1` (companions Python, Kubernetes, Tableau) and 0.1784 in `B3` (companions Terraform, Snowflake, Photoshop), a difference of 0.1%. SQL's series correlated 0.9988–0.9995 across the three surveys. Docker's series correlated only 0.93 between `B1` and `B3` because Docker scored about 5.8 points in one and 11.7 in the other (rounding noise).

**R3 chain accuracy: consistent, but not provable at the strict standard.** The four low-volume skills' levels relative to SQL, measured three ways:

| Skill | Direct, survey batch | Direct, `G1` | Chained via Photoshop | Chain vs `G1` |
|---|---:|---:|---:|---:|
| Terraform | 0.0634 | 0.0634 | 0.0629 | 0.7% |
| Snowflake | 0.0747 | 0.0747 | 0.0748 | 0.1% |
| Tableau | 0.0846 | 0.0857 | 0.0860 | 0.4% |
| Kubernetes | 0.0879 | 0.0907 | 0.0902 | 0.5% |

The three estimates agree within 0.1–3.1%, well inside the 15% tolerance. However, **every direct measurement had a mean below 10 points (2.75–5.9)**, so under my own rule R4 the direct values are too coarse to serve as ground truth. The agreement shows the method is consistent, and it is strong evidence for the *level* because rounding errors average out over 262 weeks, but it does not prove accuracy of the *weekly shape*.

**R4 resolution: fails for a single SQL anchor, and this is the main finding.** Against SQL, nine of the eleven other terms scored below 10 points in their survey batch (Docker 5.8 in `B1`, Kubernetes 2.9, Tableau 2.8, Power BI 6.3, Figma 5.7, SEO 7.9, Jira 3.7, Terraform 4.2, Snowflake 4.9); only Python (67) and Photoshop (21.7) cleared it, and Docker cleared it only in `B3` (11.7) where SQL was scaled to 65. Placed in the second-rung request (anchor Photoshop, about 70 points), the same skills scored **13.2–19.0 points**, used **15–26 distinct integer levels instead of 4–11**, and their series correlated 0.89–0.99 with the direct series.

**Anchor stability.** Over the 5 years the anchors are not flat: SQL drifted about −15.9% of its mean per year, Python −9.7%, Photoshop −7.4%, Docker +1.5% (coefficient of variation 0.15–0.28). This matters only if weekly values are divided by the anchor's weekly values, which must **not** be done (see design).

## 4. Corrected design

1. **Constant-ratio chaining only.** Within one request every series shares the same scale factor, so linking two requests needs one constant: the ratio of the shared anchor's mean level between them. Rescale a whole batch by that constant. **Never divide a skill's weekly values by the anchor's weekly values**; that would put the anchor's own drift and noise into every skill.
2. **Ladder with rungs no more than about 5× apart** so that every skill is measured in a request where its mean is at least 10 points (rule R4). Tested rungs: SQL (1.0) → Photoshop (about 0.33) → low-volume skills (0.06–0.09). A third rung (around 0.07, for skills below about 0.03 of SQL) is proposed and **not tested**.
3. **One base anchor for the final scale** (SQL or Python; report all series in units of that base) and a small set of bridging rungs recorded in the batch log.
4. **Record per series:** batch id, anchor term, anchor mean in that batch, the constant used, and whether the skill met R4 in its measuring batch. Save raw integer values untouched.
5. **Drop or aggregate to monthly** any skill that still averages below 10 points at the lowest rung or shows more than 20% zero weeks (an earlier rule in `dataset_design.md`; the zero-share of the test skills was 0%).
6. **Pacing:** at least 60 s between requests, exponential backoff on 429, resumable batches, single geography first.

## 5. Limits of this validation

- Tested: 12 skills, one ladder step (two rungs), geo `IN` only, two days. Not tested: a third rung; ambiguous terms (Java, R, Go, Excel) with topic ids or categories; other geographies; day-to-day change over more than one day; seasonality; skills below about 0.03 of SQL.
- Same-session repeats returned identical values, so true sampling noise between independent draws is unmeasured. The cross-day comparison (differences 0.1–0.4%) is the only evidence, on two terms.
- "Python" and "Docker" as plain terms may include non-programming searches; that was not tested.
- The official Trends API (consistent scaling) would remove the need for a ladder but requires an application to Google.

## 6. Status for the readiness gate

**Gate E (normalisation validated): PASS WITH LIMITS.** The corrected constant-ratio ladder is consistent on the tested skills; the original plan of anchoring every skill directly to SQL fails on resolution. Before full collection, repeat the test with the third rung and 20 skill pairs on a second day, or apply for the official API.

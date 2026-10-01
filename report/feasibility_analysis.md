# Data-Feasibility Analysis and Scope Recommendation

Prepared 2026-09-29. Every claim is tagged:

- **[V]** = verified. Measured from our own Adzuna API calls or the raw files in `data/raw/`, or stated in Adzuna's documentation.
- **[I]** = inference or assumption. Not measured; it needs checking.

## 0. How the evidence was gathered

| Evidence | Where it lives | What it covers |
|---|---|---|
| Existing raw pulls | `data/raw/adzuna/adzuna_*_2026-09-29.json` | 4 queries × 625 postings, India only |
| Live coverage probe | `scripts/measure_adzuna_coverage.py`, output `data/raw/adzuna/coverage_2026-09-29.json` | Adzuna's `count` field for 46 role titles in India, GB and US |
| Trends smoke test | `scripts/collect_trends.py`, output `data/raw/trends/` | 5-year weekly series for 5 skills in 4 geos |

**How the coverage probe works** [V]:
- Each call uses `title_only=<role>` and `max_days_old=90`, so it counts postings whose *title* contains the phrase, created in the last 90 days.
- It counts only the exact phrase. Synonyms would add postings, so every count is a **lower bound** for its role.
- Counts are a snapshot from one day. Adzuna's index changes constantly.
- The probe covered 46 roles, 3 countries and 138 calls.

### Verified facts that shape the whole design

1. **Descriptions are snippets, capped at 500 characters.** [V]
   - Adzuna's docs say "we currently only provide a snippet of the job description".
   - In our data, median and max length is exactly 500 in all 4 files.
   - 94–98% of records end in "…" (587–612 of 625 per file).
   - Many snippets are used up by employer boilerplate, for example "This job is with Kyndryl, an inclusive employer…".
   - Skill frequencies are therefore **lower bounds** and are biased toward whatever appears in the opening lines.
   - Example: SQL appears in 20% of Data Analyst snippets, and real full postings almost certainly mention it more often [I].
2. **Free-text search is loose.** [V]
   - Only 70–90% of postings returned for a query contain the query words in the title (title match: 524/625 BA, 560 DA, 452 SWE, 440 Digital Marketing).
   - The "digital marketing" pull returned Graphic Designers, WordPress Developers and BD Managers.
   - The "data analyst" pull returned many Data Engineers and ETL Specialists.
   - Filter or label role membership by title; do not trust the query.
3. **Old postings are mixed in.** [V]
   - Our pulls include postings back to 2019.
   - 35–50% of records in each file were created before 2026-06-29 (e.g. Digital Marketing: 315/625).
   - The collector has no `max_days_old`. "Current demand" needs a recency window.
4. **Duplicates exist.** [V]
   - Across the 4 files there are 2,472 unique IDs out of 2,500 records.
   - There are about 192 more duplicate rows by (title, company, first 150 characters), e.g. one employer reposting the same role per location.
5. **Salary is sparse and is India-specific in quality.** [V]
   - Share of postings with `salary_min`: Digital Marketing 38%, Business Analyst 26%, Data Analyst 18%, Software Engineer 12%.
   - `salary_is_predicted` is "0" for all 2,500 records in these pulls.
   - There are junk values (`salary_min` as low as 3 or 12; 2–16 records per file under 100,000 INR).
   - 19 Business Analyst records have min = max (a point value, not a range).
6. **Pagination reaches at least 10,000 rows.** [V] Pages 20, 100 and 200 (50 per page) all returned full pages for a 49,341-count query.
7. **`contract_time` is missing for about 35% of postings.** [V] 220 of 625 for Business Analyst, Software Engineer and Digital Marketing, 276 for Data Analyst. `company` is missing for 1–8% (47 of 625 for Digital Marketing).
8. **Trends returns integer 0–100 values relative to the terms in the same request.** [V] In a smoke test with SQL as the reference, Power BI scored about 4 and Tableau about 2. Low-volume skills therefore get very coarse resolution, and cross-batch comparison needs an anchor (Section G).

## 1. Adzuna coverage by role (measured)

`count` = postings with the phrase in the title, created in the last 90 days [V]. Lower bounds; snapshot of 2026-09-29.

| Domain | Role probed | India | GB | US |
|---|---|---:|---:|---:|
| Technology & Data | software engineer | 9,126 | 2,798 | 49,341 |
| | data analyst | 839 | 566 | 4,840 |
| | data scientist | 1,262 | 554 | 5,140 |
| | data engineer | 2,805 | 1,176 | 13,550 |
| | machine learning engineer | 212 | 199 | 2,984 |
| | devops engineer | 822 | 395 | 2,812 |
| | cloud engineer | 842 | 365 | 5,147 |
| | cybersecurity analyst | 27 | 7 | 592 |
| Business, Finance & Mgmt | business analyst | 1,263 | 960 | 8,908 |
| | financial analyst | 587 | 658 | 6,065 |
| | accountant | 1,560 | 11,170 | 10,871 |
| | project manager | 1,836 | 5,301 | 42,440 |
| | product manager | 1,822 | 1,639 | 23,620 |
| | digital marketing | 389 | 329 | 1,375 |
| | human resources | 417 | 3,084 | 7,587 |
| Healthcare | registered nurse | 13 | 2,089 | 87,398 |
| | pharmacist | 154 | 429 | 16,934 |
| | physiotherapist | 36 | 303 | 507 |
| | radiographer | 6 | 259 | 355 |
| | clinical research associate | 5 | 32 | 670 |
| | medical coder | 36 | 3 | 394 |
| Engineering | mechanical engineer | 567 | 2,529 | 11,799 |
| | electrical engineer | 580 | 3,246 | 14,320 |
| | civil engineer | 234 | 1,383 | 6,666 |
| | chemical engineer | 18 | 22 | 627 |
| | quality engineer | 807 | 931 | 6,909 |
| | manufacturing engineer | 188 | 811 | 7,592 |
| Logistics & Supply Chain | supply chain analyst | 90 | 21 | 593 |
| | logistics coordinator | 20 | 149 | 914 |
| | warehouse manager | 73 | 242 | 2,822 |
| | procurement specialist | 107 | 113 | 1,016 |
| | transport planner | 22 | 375 | 406 |
| Energy & Environment | solar engineer | 32 | 54 | 161 |
| | environmental engineer | 14 | 89 | 1,455 |
| | energy analyst | 25 | 19 | 212 |
| | sustainability analyst | 4 | 11 | 82 |
| | health and safety officer | 7 | 214 | 102 |
| Media, Design & Creative | graphic designer | 571 | 140 | 1,213 |
| | ux designer | 238 | 133 | 1,119 |
| | content writer | 183 | 11 | 114 |
| | video editor | 286 | 64 | 254 |
| | social media manager | 138 | 128 | 562 |
| Architecture & Construction | architect | 3,532 | 2,404 | 29,301 |
| | quantity surveyor | 57 | 3,740 | 210 |
| | site engineer | 504 | 1,057 | 3,639 |
| | bim modeller | 99 | 6 | 82 |
| | construction manager | 131 | 833 | 10,712 |

Reading notes:

- **"architect" is contaminated** [I]. 3,532 in India is almost certainly software/solution/cloud architects (IT), not building architects. Do not use it as an Architecture measure. This is unverified; a sample of the titles would settle it.
- **Counts are Adzuna's total for a search, not what we can use** [I]. After title filtering and deduplication, expect to keep roughly 70–85% (based on the 70–90% title match and about 8% duplicates measured above).
- **Not measured**: full-text availability, synonym-expanded counts, and how many salaried rows exist per role over a larger sample.

## 2. Domain-by-domain assessment

### 2.1 Technology & Data: **feasible, highest confidence**

- **Coverage** [V]: India has 800 to 9,000 title-matched postings for 7 of 8 probed roles. Only "cybersecurity analyst" (27) is thin, and that is likely a title-choice problem: "security engineer" and "information security" were not probed [I].
- **Skill content** [I/V]: Postings name tools explicitly (SQL, Python, Azure, Databricks, Power BI, Kubernetes). Even in 500-character snippets, SQL hits 20% of Data Analyst snippets and Python 7–11% [V].
- **Salary** [V]: India salary presence is low (Software Engineer 12%, Data Analyst 18%). Mean salaries from Adzuna's `mean` field look plausible (about 1.0–1.7M INR/yr) [V], but per-posting salary supports only pooled analysis.
- **Google Trends** [V/I]: Strongest domain. Named tools and languages have real search volume. Ambiguity exists (Java, R, Go, Rust, Swift, "Excel", "Spark", "Airflow") and is handled in Section G.
- **Risk**: near-duplicate postings from large IT services firms (TCS, Capco, EXL, Kyndryl appear repeatedly in our pull [V]). Cap postings per employer to avoid one company distorting frequencies.

### 2.2 Business, Finance & Management: **feasible for analytical roles only**

- **Coverage** [V]: India has 389 to 1,836 for all 7 roles probed. Business Analyst, Financial Analyst, Product Manager, Project Manager and Accountant exceed 500.
- **Skill content** [I]: Business Analyst and Financial Analyst postings are tool-heavy (Excel, SQL, Power BI, SAP; in the Business Analyst snippets: Excel 8%, SQL 5%, communication 9% [V]). Project Manager, HR and Accountant postings lean on soft skills and certifications (PMP, CPA, CA), which are hard to text-mine and hard to trend.
- **Salary** [V]: Digital Marketing 38% and Business Analyst 26% are the best-populated in our sample.
- **Google Trends** [I]: Good for tools (Power BI, Excel, Tableau, SAP, Salesforce, Google Analytics, SEO, HubSpot). Poor for soft skills ("communication", "leadership", "stakeholder management": generic, multi-meaning, no unambiguous query).
- **Risk**: "Business Analyst" in India is heavily IT-adjacent [V]: 556 of 625 records were categorised "IT Jobs". It overlaps Technology & Data. Keep, but label it as such, or the two domains double-count.
- **Recommendation**: keep the domain, restricted to Business Analyst, Financial Analyst, Product Manager, Project Manager, and Digital Marketing. Accountant is a possible extra (1,560 in India, mostly certification-driven skills).

### 2.3 Engineering (mechanical, electrical, civil, quality, manufacturing): **conditional**

- **Coverage** [V]: India 188 to 807 (civil 234, manufacturing 188, quality 807, mechanical 567, electrical 580). Adequate for skill frequency but marginal after dedupe. The US has 6,000 to 14,000 each.
- **Skill content** [I]: Tools are specific (AutoCAD, SolidWorks, ANSYS, MATLAB, PLC, CATIA), which is good for mining. But snippets often spend the 500 characters on responsibilities and company text [I].
- **Google Trends** [I]: Mixed. AutoCAD, SolidWorks, MATLAB, ANSYS, Revit have real volume. But many engineering skills are standards or concepts (ISO 9001, Six Sigma, GD&T, FMEA) with student/academic search noise.
- **Decision**: include only if a larger India pull shows at least 400 clean postings per role, or use the US market for this domain.

### 2.4 Media, Design & Creative: **conditional, borderline**

- **Coverage** [V]: India graphic designer 571, video editor 286, UX designer 238, content writer 183, social media manager 138. The UK/US counts are 11–1,213, so India is the only viable market at the required depth.
- **Skill content** [I]: Tool names are explicit (Figma, Photoshop, Illustrator, Premiere Pro, After Effects, Canva). However, our own digital-marketing pull showed how title search leaks (Graphic Design Interns, Creative Directors) [V].
- **Salary** [V]: Presence was 38% for Digital Marketing, which is the closest measured proxy. Design roles were not measured directly.
- **Google Trends** [I]: Tool queries work (Figma, Photoshop). Trend signal is confounded by student/tutorial/piracy searches ("Photoshop free", "Canva").
- **Decision**: include only UX Designer and Graphic Designer, only if the larger pull confirms at least 400 clean postings each.

### 2.5 Healthcare: **exclude**

- **Coverage** [V]: India registered nurse 13, radiographer 6, clinical research associate 5, physiotherapist 36, medical coder 36, pharmacist 154. The US has huge counts (nurse 87,398), but see below.
- **Skill content** [I]: Healthcare postings are dominated by licences, certifications and clinical competencies (RN, BLS, ACLS, HIPAA), and by EHR systems (Epic, Cerner). Those are either not searchable as "skills" or not mappable to a reliable Trends signal.
- **Google Trends** [I]: Unsuitable. Clinical terms are dominated by patients and students searching health topics, not employers seeking skills.
- **Adzuna bias** [I]: It is an online aggregator. Healthcare hiring in India is largely local, walk-in or word of mouth, so coverage is structurally thin.

### 2.6 Logistics, Transport & Supply Chain: **exclude from v1**

- **Coverage** [V]: India supply chain analyst 90, warehouse manager 73, procurement 107, logistics coordinator 20, transport planner 22. Below any usable threshold in India.
- **US** has 593 to 2,822 [V], but mixing US data into an India-based project only for this domain adds complexity.
- **Skill content / Trends** [I]: Skills are mostly SAP, WMS names, Excel and generic terms (forecasting, inventory management); thin search volume for the specific ones.

### 2.7 Energy & Environment: **exclude**

- **Coverage** [V]: India solar engineer 32, environmental engineer 14, energy analyst 25, sustainability analyst 4, health and safety officer 7. Sparse in every country probed (US: 82 to 1,455).
- Nothing here can support even skill-frequency analysis.

### 2.8 Architecture & Construction: **exclude as a domain; fold civil/site engineering into Engineering**

- **Coverage** [V]: India site engineer 504, construction manager 131, quantity surveyor 57, BIM modeller 99. "architect" 3,532 is likely IT architects [I]. Quantity surveyor is a UK-centric title (3,740 in GB vs 57 in India).
- **Skill content / Trends** [I]: Revit, AutoCAD and BIM are searchable, but too few clean building-architect postings to form a role.
- Site engineer and civil engineer fit better inside Engineering.

## 3. Google Trends suitability, by skill type

| Skill type | Suitable? | Why |
|---|---|---|
| Named software/tools (Power BI, Tableau, Docker, Kubernetes, Figma, Snowflake) | **Yes** | Distinct names, employer and learner search interest. [I] |
| Languages with unique names (Python, TypeScript, Kotlin, SQL) | **Yes**, with a category filter | Mostly tech intent. [I] |
| Ambiguous names (Java, R, Go, Rust, Swift, Spark, Airflow, Excel, Word, Oracle, Ruby) | **Only with a topic/category filter** | Islands, metals, spreadsheets, airflow, etc. |
| Frameworks/concepts (machine learning, agile, scrum, DevOps) | **Yes** for ML and agile; generic | High volume, broad. [I] |
| Certifications (PMP, CPA, AWS Certified) | Partly | Volume is real but reflects exam-takers, not job demand. [I] |
| Soft skills (communication, leadership, teamwork) | **No** | Generic, no meaningful trend. [I] |
| Clinical/legal/domain knowledge (patient care, GAAP) | **No** | Public health/general interest, not job-skill signal. [I] |
| Low-volume niche tools (Power BI in the smoke test = 4 vs SQL = 30) | **Marginal** | Integer resolution too coarse against a high-volume anchor. [V] |

## 4. Final recommendation

### A. Recommended domains (include)

1. **Technology & Data**
2. **Business, Finance & Management**, restricted to analytical/tool-driven roles (Business Analyst, Financial Analyst, Product Manager, Project Manager, Digital Marketing)

### B. Conditional domains (include only if the larger pull passes the thresholds in Section E)

3. **Engineering**, at most 2–3 roles: mechanical, electrical, quality (India counts 567, 580, 807 [V]). Fallback: use the US market, or drop it.
4. **Media, Design & Creative**, at most 2 roles: graphic designer (571) and UX designer (238) [V].

Recommendation: plan for **3 domains**. Technology & Data and Business are firm; take **Engineering** as the third only if its roles pass, and Media & Design as a reserve. Do not run four in parallel.

### C. Exclude

| Domain | Reason (evidence) |
|---|---|
| Healthcare | India title counts of 5 to 154 for 5 of 6 roles [V]; skills are licences/clinical, not searchable [I]; Trends signal is dominated by consumer health searches [I]. |
| Logistics, Transport & Supply Chain | India counts 20 to 107 [V]; skills are generic or ERP-specific with thin Trends volume [I]. |
| Energy & Environment | India counts 4 to 32 [V]; sparse in GB/US too for 4 of 5 roles [V]. |
| Architecture & Construction (as a domain) | Only site engineer has usable India volume (504) [V]; "architect" is IT-contaminated [I]; quantity surveyor is a UK title [V]. Fold civil and site engineering into Engineering. |

Roles to exclude within kept domains: cybersecurity analyst (27 in India [V]; re-probe with "security engineer"), machine learning engineer as a standalone role (212 [V]; merge into Data Scientist), human resources and accountant (soft-skill/certification-driven [I]).

### D. Role taxonomy

Map postings by **title regex**, not by search query [V, see finding 2]. "Search terms" are the phrases to use in `title_only`/`what_or`. Synonym counts have **not** been measured [I].

| Domain | Role | Alternative titles / search terms | India availability (90-day title-only lower bound) | Skill-extraction usefulness | Trends suitability |
|---|---|---|---|---|---|
| Technology & Data | Software Engineer | software developer, SDE, backend/frontend/full stack developer | 9,126 [V] | High [I] | High |
| | Data Analyst | business intelligence analyst, BI analyst, reporting analyst | 839 [V] | High (SQL 20% even in snippets [V]) | High |
| | Data Scientist | machine learning scientist, applied scientist, ML engineer | 1,262 [V] (ML engineer 212 [V]) | Medium–High [I] | High |
| | Data Engineer | ETL developer, big data engineer, analytics engineer | 2,805 [V] | High [I] | High |
| | DevOps / Cloud Engineer | SRE, platform engineer, cloud engineer, infrastructure engineer | 822 / 842 [V] | High [I] | High |
| Business, Finance & Mgmt | Business Analyst | systems analyst, functional analyst, product analyst | 1,263 [V] | Medium (Excel 8%, SQL 5% in snippets [V]) | Medium–High |
| | Financial Analyst | FP&A analyst, finance analyst, investment analyst | 587 [V] | Medium [I] | Medium |
| | Product Manager | product owner, associate product manager | 1,822 [V] | Medium [I] | Medium |
| | Project Manager | program manager, delivery manager, scrum master | 1,836 [V] | Low–Medium (PMP, agile; soft-skill heavy) [I] | Medium |
| | Digital Marketing Specialist | SEO specialist, performance marketing, social media marketer, growth marketer | 389 [V] | High for tools (SEO 29%, Google Analytics 5% in snippets [V]) | High |
| Engineering *(conditional)* | Mechanical Engineer | design engineer, CAD engineer | 567 [V] | Medium [I] | Medium |
| | Electrical Engineer | electrical design engineer, controls engineer | 580 [V] | Medium [I] | Medium |
| | Quality Engineer | QA engineer (non-software), quality assurance engineer | 807 [V] (may include software QA [I]) | Medium [I] | Low–Medium |
| Media & Design *(conditional)* | UX Designer | UI/UX designer, product designer | 238 [V] | High for tools [I] | Medium–High |
| | Graphic Designer | visual designer, creative designer | 571 [V] | High for tools [I] | Medium |

### E. Minimum data requirements

Postings counted are **after deduplication and after keeping only title-matched postings**.

| Purpose | Minimum per role | Minimum per domain | Rationale |
|---|---|---|---|
| Skill-frequency analysis | **300**, target 400 | 1,200 | A proportion has a 95% margin of about ±5.7 percentage points at n=300 and ±4.9 pp at n=400 (standard binomial formula, p=0.5). Below about 100, the margin is about ±10 pp, too wide to rank skills. |
| Comparing roles | **400 each** | n/a | To detect a 10-point difference in a skill's prevalence (e.g. 30% vs 40%) with 80% power at 5% significance, you need roughly 350–400 per group (standard two-proportion formula). |
| Trend analysis | Trends: **at least 5 years of weekly data (about 260 points) per skill**. Postings: **not used for trends.** | n/a | Adzuna gives one snapshot of postings, not a history. The trend comes from Google Trends. A month of repeated weekly snapshots is too short to be a trend, so do not present it as one. |
| Model training/evaluation | **200 per class** and **2,000 total** for role classification | n/a | Keep at least 200 per class after dedupe; split by employer (group k-fold) so near-duplicate postings do not leak across train/test. Salary prediction: treat as **not feasible per role**. With 12–38% salary presence, 625 postings give only 78–235 salaried rows [V]; pool roles, and only if at least 500 salaried rows are reached. |
| Skill inclusion | A skill must appear in **at least 20 postings and at least 2% of a role's postings** | n/a | Below that, the frequency estimate is noise. |

These thresholds are recommendations based on standard sample-size formulas, not values from a source. Re-derive them if the team changes the confidence level.

### F. Adzuna collection strategy

- **Countries**:
  - **Primary: India (`in`)**. It is already collected, is the team's likely target market, and has adequate depth for the recommended roles [V].
  - **Secondary: US (`us`)**, only as a robustness/replication check for the roles that pass. It has several times more postings than India for most roles (about 5–10× for the tech and business roles probed [V]) but a different labour market, and mixing the two in one analysis would hide that.
  - Do not use GB. Its counts are lower for tech roles and higher only for accountants, quantity surveyors and similar [V].
  - Keep markets separate in all tables and compare, never pool.
- **Queries**: use `title_only=<role phrase>` (one call series per title variant), not free-text `what`. Free text returned unrelated titles in our data [V]. Run each synonym separately so you can measure what each adds.
- **Role mapping**: assign the role by regex on the posting title after collection, and record both the query and the mapped role. Drop postings whose title matches no role.
- **Pagination**: 50 per page [V], loop pages until results end or the target is met. Depth of at least 10,000 rows works [V]. Add a sleep of about 2.5 seconds between calls; the exact rate limit is not published in the docs we fetched [I], so log all non-200 responses.
- **Deduplication** (in this order):
  1. Exact `id`.
  2. Same normalised title + company + first 150 characters of description. Our data shows about 192 such duplicates in 2,500 rows [V].
  3. Cap at **5% of a role's postings per employer**. IT-services firms repeat heavily [V].
- **Date range**: add `max_days_old=90` and `sort_by=date`. Our pulls without these included 2019 postings [V]. State clearly that this is a **90-day snapshot**, not a history.
- **Fields to keep** (raw JSON, unmodified, plus derived columns): `id`, `title`, `description` (snippet, 500 characters [V]), `created`, `company.display_name`, `location.area` and `display_name`, `latitude`/`longitude`, `category.tag`, `contract_time`, `contract_type`, `salary_min`, `salary_max`, `salary_is_predicted`, `redirect_url`. Also store the query used, the pull date and the country.
- **Salary**: keep `salary_min/max` and the predicted flag. Treat salary as a secondary variable. Drop values below a floor (for example under 100,000 INR/year in India) as suspect [V: junk values exist], and record how many were dropped. Never report a single salary per role without stating the posting count behind it.
- **Location**: use the last `area` element as the city, and treat the bare "India" (115–184 of 625 per file [V]) as "unspecified".
- **Coverage record**: for every query, save the API `count` alongside the pulled rows. Our existing collector does not [V], so it cannot say how much of the available data was sampled.
- **Collector fixes required before large-scale ingestion** (`scripts/collect_adzuna.py`): add `title_only`, `max_days_old`, `sort_by=date`, per-query `count`, retry/backoff and a `--roles` config. Note that its comment says "4-6 categories" and uses `what`, which we now know is too loose.

### G. Google Trends strategy

**Step 1. Build a skill dictionary, not raw n-grams.** Extract candidate skills from postings using a curated list (seeded from O*NET/ESCO or a hand-built list) and match with word boundaries and case rules. Keep skills that pass the inclusion rule in Section E.

**Step 2. Map each skill to a Trends query with a record of the decision.** For every skill keep: canonical name, query string, category filter, whether a Knowledge Graph topic is used, and a keep/drop reason.

| Problem | What to do |
|---|---|
| **Ambiguous terms** (Java, R, Go, Rust, Swift, Spark, Airflow, Excel, Oracle) | Use the Trends "topic" (Knowledge Graph entity) rather than a plain string, or set `cat=31` (Programming) for tech terms, or use the phrase form ("Java programming", "R programming"). Check each with a manual test before accepting it. Drop the skill if it cannot be disambiguated. |
| **Brand/product bias** | Track product names at the tool level only when the tool itself is the skill (Power BI, Tableau). For vendor-neutral skills use the concept ("data visualization" vs Tableau). Do not treat a brand's search growth as the skill's demand growth without saying so. Compare a brand and its concept where both exist. |
| **Short-lived viral spikes** | Use weekly data over 5 years. Smooth with a rolling median (for example 8 weeks). Classify trend from the **slope over the last 12–24 months** (regression or Mann–Kendall), never from one week or a peak. Flag any series where the maximum is more than 3× the median and the peak lasts under 4 weeks, and review it manually. |
| **Multiple meanings** | Manual review of the "related queries/topics" panel for each shortlisted skill. If the top related queries are unrelated to work/learning tech, drop it. |
| **Insufficient search volume** | Every batch of 4 skills shares a common **anchor** term (`scripts/collect_trends.py`, anchor SQL). The smoke test showed Power BI at 4 and Tableau at 2 relative to SQL at 30 [V], so a poorly chosen anchor destroys resolution. Rule of thumb: drop a skill whose anchor-relative series is 0 for more than 30% of weeks [I]. Consider a mid-volume anchor (for example Python or Excel) for low-volume skills, and keep the anchor the same within each comparison group. |
| **Comparability** | Trends scales each request separately, so never compare raw values from different batches. Rescale each batch by its anchor's ratio to the reference. |
| **Reproducibility** | Trends is sampled and its values can shift between pulls. Save raw CSVs with the pull date, and re-pull twice on different days for a sample of skills to estimate variation. Report it. |
| **Geography** | Use the same geographies as Adzuna: India (`IN`) primary, US as secondary. Worldwide is also collected as a check. Trends is search interest in a place, not employer demand. |

**Classifying trend** (rising/stable/declining): fit a slope over the last 24 months of smoothed weekly data and require both a minimum effect size and a significant trend test; otherwise call it stable. Then combine with demand: a skill is a **priority skill** when it is in the top quartile of posting frequency within the role and its trend is rising.

### H. Final project scope

| Item | Recommendation | Reason |
|---|---|---|
| Domains | **3** (Technology & Data, Business, and Engineering if it passes; Media & Design is the reserve) | 5 people, one month. The 4 excluded domains fail on measured coverage. |
| Roles | **12–14** total, about 5 per firm domain and 2–3 for the third | Each role needs at least 400 clean postings. |
| Job postings | **About 6,000–7,500 collected, 4,500–5,500 after cleaning**, India only; a US replication of about 2,000 for the strongest roles is optional | 400–500 postings per role × 13 roles ≈ 5,200–6,500 raw before losing about 15–25% to filtering/dedupe [I]. Well within API limits (Adzuna serves 50 per page [V]). |
| Skills | **60–100** in the final dictionary, of which **about 40–60** pass the Trends screen | Skills passing the 20-posting/2% rule per role, then dropped for ambiguity or low search volume. Start with about 120 candidates. |
| Google Trends series | **About 60 skills × 2 geographies (IN, US) = about 120 series**, plus the anchor. In batches of 4 skills, that is about 15 requests per geography | At the script's 8–15 second pause, one geography takes a few minutes when not throttled; expect 429 errors and plan several hours [I]. |

**Suggested one-month sequence**:
1. **Week 1**: fix the collector, re-pull India with `title_only` and `max_days_old=90` for all candidate roles, and check counts against the thresholds. Decide domain 3 here.
2. **Week 2**: clean, dedupe, map roles; build the skill dictionary and skill-frequency tables.
3. **Week 3**: Trends pull, disambiguation review, trend classification.
4. **Week 4**: join demand and trend, priority-skill list, dashboard, report.

## 5. Sampling and platform bias (must be stated in the report)

1. **Adzuna is one aggregator, not the labour market** [V by definition]. It collects online listings only. Roles hired through referrals, campus placement, walk-ins, staffing agencies or internal transfers are underrepresented [I].
2. **Sector skew** [V/I]. In our sample, 556 of 625 Business Analyst postings were categorised "IT Jobs" [V]. India results skew to large employers and IT services firms (TCS, EXL, Capco, Kyndryl, Thermo Fisher appear repeatedly [V]) and to Bangalore/Hyderabad/Mumbai [V]. Blue-collar, healthcare, and small-business hiring are likely underrepresented [I].
3. **Posting is not hiring**. One vacancy can appear multiple times, and evergreen/talent-pool postings inflate counts [I]. We deduplicate but cannot remove these fully.
4. **Snippet bias** [V]. Only the first 500 characters are available, so skills are undercounted and boilerplate-heavy postings look skill-poor.
5. **Relevance-ranked sampling** [V]. Our earlier pulls took the first 625 results of a relevance-sorted search, which is not a random sample. `sort_by=date` gives the most recent postings, which is also not random. State which one is used.
6. **Recency** [V]. The earlier pulls include postings from 2019 onward; the new pull is a 90-day window.
7. **Salary** [V]. Only 12–38% of postings have salary, and those that do are unlikely to be a random subset [I].
8. **Google Trends is search interest, not employer demand** [I]. It is sampled, normalised, rounded to integers, and reflects learners, students and consumers as well as employers.
9. **Trend vs demand are different populations.** Posting frequency is a 90-day cross-section from employers. Trends is a 5-year series from searchers. The project's contribution is combining them, not claiming they measure the same thing.
10. **Generalisation limit.** Results describe India-listed online postings for the selected roles in this window. They should not be presented as the labour market.

## 6. What still needs measuring (through our API account)

1. Synonym-expanded counts per role (this analysis used one title per role, so all counts are lower bounds).
2. Clean-posting yield after title mapping and dedupe, per role.
3. Salary presence per role from a larger sample (only 4 roles × 625 were measured).
4. Whether "architect" in India is mostly IT (sample the titles).
5. "security engineer" and "information security analyst" as replacements for the thin "cybersecurity analyst".
6. Adzuna's rate limits for our key (not published in the documentation pages we could fetch).
7. Repeat the coverage probe on a different day to see how much counts move.
8. A Trends stability re-pull for a sample of skills.

## 7. Caveats about this analysis

- All counts come from one day, one API key, `title_only`, 90 days, and the exact role phrase.
- The "[I]" statements about skill content, Trends suitability and hiring channels are informed judgement. They were not tested, except where a measured figure is quoted next to them.
- The sample-size numbers are standard formulas applied to our assumptions, not empirical results from this data.

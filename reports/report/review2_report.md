# Business Analytics Review 2 Report: Career Market Intelligence

**Course:** Business Analytics — Data Analysis and Predictive Modelling
**Project:** Career Market Intelligence
**Milestone:** Business Analytics Review 2
**Branch:** `feat/combined-insight`

---

## 1. Executive Summary

This Review 2 report delivers the complete, integrated analytical suite for the Career Market Intelligence project. It unites two core strategic pillars:
1. **Method 3 — Combined Insight (Part C):** A strategic market intelligence framework pairing 7,240 scraped Indian job postings with 5-year longitudinal Google Trends search momentum, establishing an empirical **Demand-Interest Gap Quadrant** to guide career investment.
2. **Predictive Salary Modeling Pipeline (Methods 1 & 2 Remediation):** A complete, methodologically rigorous overhaul of the machine learning engine across Phases 1, 2A, corrected 2B, and 2C, resolving all critical defects identified during the repository audit and establishing verified, leak-free performance benchmarks.

### Key Deliverables & Findings

- **Strategic Skill Intelligence (Part C):** Evaluating all 20 top-demand labor-market skills against 5-year Google Trends search momentum (India) yielded **100% coverage** (20/20 matched). Using an empirical demand median of 1.47% (midpoint between Rank 10 SAP and Rank 11 Java), the analysis produced 2 INVEST, 8 OPPORTUNITY, 1 HYPE, and 9 AVOID skills. `Machine Learning` (rank #1, 5.26% demand, +40% confirmed rising) is the top investment priority. `Deep Learning` (rank #18, 0.51% demand, +67% rising) is the single HYPE signal — public buzz substantially exceeds current hiring volume. High-demand foundational skills (`Python`, `SQL`, `AWS`) fall in OPPORTUNITY, reflecting mature baseline competencies with strong employer need despite cooling or declining search interest.
- **Methodological Defect Remediation (Phase 1):** Historical Review 1 models suffered from fatal 78.8% cross-task split leakage, non-stratified partitioning, an invalid reconstructed binary baseline (46.75%, inferred from historical unstratified minority split proportions), regex false matches extracting up to 448 years of experience from currency strings, and dataset-wide target quantile leakage. These identified leakage pathways and parsing flaws were systematically addressed by sealing a single stratified 80/20 train/test split ($N_{\text{train}}=922, N_{\text{test}}=231$), repairing contextual experience parsing bounded within $[0, 25]$ years, and encapsulating all preprocessing inside strict training-only scikit-learn pipelines.
- **Skill Taxonomy Expansion (Phase 2A):** Expanding the skill extraction regex from 12 ad-hoc terms to 50 domain-curated patterns across 8 functional categories reduced the proportion of zero-skill postings from **68.95% (795 postings) to 40.33% (465 postings)**—recovering 330 postings (+28.62 percentage points) and restoring feature representation to previously unserved roles (Graphic Design, Project Management, Digital Marketing).
- **Multimodal Text Fusion (Phase 2B Corrected):** Deriving salary-band tertiles strictly from training data ($\text{Low} \le ₹600\text{k}, \text{Medium } ₹600\text{k}–₹1.6\text{M}, \text{High} > ₹1.6\text{M}$) and pre-scrubbing compensation text prior to feature extraction ensured leak-free target construction. Combining structured features and 50 skill indicators with 50 `TruncatedSVD` components from TF-IDF job description n-grams (Configuration C) produced substantial empirical lift over structured-only baselines.
- **Systematic Optimization & Final Benchmark (Phase 2C):** Hyperparameter tuning via 5-fold Stratified Cross-Validation on the 922 training postings identified optimal regularized Random Forest ensembles as champion models for both tasks. On the untouched held-out test set ($N_{\text{test}}=231$), the champion models achieved:
  - **Three-Class Salary Band Task:** **61.90% Test Accuracy**, **60.92% Balanced Accuracy**, **0.6059 Macro-F1**, and **0.7937 ROC-AUC**. For classification errors, 63/88 (71.59%) were between immediately adjacent salary bands (representing 63/231 = 27.27% of test postings), while severe opposite-end errors accounted for 25/88 (28.41%) of classification errors (representing 25/231 = 10.82% of test postings).
  - **Binary Salary Classification Task:** **75.76% Test Accuracy**, **75.75% Balanced Accuracy**, **0.7575 Macro-F1**, and **0.8507 ROC-AUC**.
- **Transparent Academic Disclosures:** Hyperparameter tuning slightly improved cross-validation Macro-F1 on the training partition ($0.5522 \to 0.5648$) and reduced fold variance ($\pm 0.0371 \to \pm 0.0260$). However, tuning did not improve holdout Macro-F1 relative to the Phase 2B Configuration C Random Forest baseline (Macro-F1 $0.6140 \to 0.6059$, representing a nominal difference of 3 test postings out of 231). Tree ensembles exhibited a substantial training-versus-CV generalization gap (train-fold F1 $\sim 0.97$ vs CV validation F1 $\sim 0.56$), and gradient boosting libraries (`xgboost`, `lightgbm`) could not be evaluated due to environment restrictions.

---

## 2. Project Objective and Review 2 Contributions

The Career Market Intelligence project provides data-driven career navigation by synthesizing real-world employment opportunities with longitudinal labor market trends.

### Review 2 Contributions Overview

| Component | Focus Area | Key Problem Solved | Primary Output Artifact |
| :--- | :--- | :--- | :--- |
| **Method 3 (Part C)** | Strategic Skill Intelligence | Disconnect between static job openings and longitudinal developer interest | `data/review2/skill_gap.csv`, `reports/combined/demand_interest_quadrant.png` |
| **Phase 1** | Evaluation Baseline & Integrity | 78.8% split leakage, 448-year regex errors, unstratified partitions | `reports/modeling/phase1_evaluation_report.md`, `test_split_indices.json` |
| **Phase 2A** | Feature Coverage Expansion | 68.95% zero-skill sparsity in salary-bearing job postings | `reports/modeling/phase2a_skill_coverage_report.md`, `phase2a_skill_prevalence_comparison.csv` |
| **Phase 2B Corrected** | Multimodal Text Fusion | Dataset-wide quantile leakage; unexploited semantic text in descriptions | `reports/modeling/phase2b_corrected_text_fusion_report.md`, `phase2b_corrected_model_comparison.csv` |
| **Phase 2C** | Model Tuning & Final Benchmark | Suboptimal tree depth/leaf settings; absence of formal holdout benchmark | `reports/modeling/phase2c_tuning_report.md`, `phase2c_tuning_comparison.csv` |

---

## 3. Method 3 — Combined Insight: Demand-Interest Gap & Strategic Novelty

### 1. Objective & Novelty
The Combined Insight module resolves a fundamental limitation in single-source career analytics:
- **Static Job Postings** measure immediate employer demand but fail to capture the forward momentum of public adoption or candidate learning curves.
- **Search Trends** measure public curiosity and developer buzz but do not confirm whether employers are actually budgeting and hiring for those skills.

By pairing **Employer Demand** (extracted from 7,240 actual job postings, Method 1) with **Search Interest Momentum** (measured over 5-year longitudinal Google Trends across India, Method 2), we establish the **Demand-Interest Gap Quadrant**.

> **Methodological Contribution:** This module combines employer skill demand with five-year Google Trends search momentum in a demand–interest quadrant framework. It uses an empirical median for demand classification, incorporates Mann–Kendall trend confirmation, and flags low-volume search signals to qualify recommendations. The contribution of this implementation is the integration of these elements into a reproducible career-intelligence workflow. Its novelty relative to existing literature requires validation through a cited literature review; no citations have been identified at this stage, and novelty over prior work is not claimed.


---

### 2. Empirical Thresholds & Classification Rules
To avoid arbitrary cutoffs, all boundaries are derived directly from the empirical distributions of the 20 evaluated skills:
- **Demand Dimension:** Empirical median percentage of postings across all 20 evaluated skills (from `data/review2/skill_demand.csv`):
  $$\text{Demand Threshold} = \text{Median}(pct\_postings) = 1.47\% \quad (\text{midpoint between Rank 10: SAP at 1.57\% and Rank 11: Java at 1.37\%})$$
  - $\text{High Demand}: pct\_postings \ge 1.47\%$ (top 10 skills, Ranks 1–10)
  - $\text{Low Demand}: pct\_postings < 1.47\%$ (bottom 10 skills, Ranks 11–20)
- **Momentum Dimension (Member B Contract — `data/review2/skill_trends.csv`):**
  - $\text{Rising}: pct\_change \ge +10.0\%$
  - $\text{Stable}: -10.0\% < pct\_change < +10.0\%$
  - $\text{Declining}: pct\_change \le -10.0\%$
  - Classification is validated in the notebook against these thresholds for every skill.

**Important caveats on the Momentum Dimension:**
- Google Trends search interest is a proxy for public curiosity; it does **not** directly measure student enrollment, skill supply, competition levels, or actual course purchases.
- Declining search interest does not prove low competition; it may instead reflect that a skill has matured into a foundational expectation no longer frequently searched.
- Stable search interest does not prove reduced public hype; it may reflect steady, persistent interest.
- The Mann-Kendall test (`trend_confirmed` field) provides statistical confirmation of monotonic trends. Skills where `trend_confirmed = False` have a non-significant Mann-Kendall result and their directional classification should be treated with additional caution.
- Skills with `low_volume = True` have low absolute Google Trends search volumes; percentage changes for these skills are more susceptible to noise and should be interpreted conservatively.

#### Quadrant Matrix:
| Quadrant | Condition | Strategic Meaning |
| :--- | :--- | :--- |
| **INVEST** | High Demand + Rising Momentum | Core industry growth skills; top priority for technical investment. |
| **OPPORTUNITY** | High Demand + Stable/Declining Momentum | High employer hiring with stabilized or cooling search interest; dependable bedrock career skills. |
| **HYPE** | Low Demand + Rising Momentum | Emerging public buzz exceeding current job openings; monitor adoption trajectory before committing. |
| **AVOID** | Low Demand + Stable/Declining Momentum | Below-median hiring demand combined with stagnant or declining public interest; lower immediate career priority. |

---

### 3. Coverage Audit
- **Total Demand Skills evaluated:** 20 skills (top 20 non-generic skills by posting frequency from 7,240 postings; `data/review2/skill_demand.csv`)
- **Total Trend Skills delivered:** 20 skills (5-year Google Trends, India, anchor=SQL; `data/review2/skill_trends.csv`)
- **Matched Skills:** **20 / 20 (100% coverage)** — all demand skills have a corresponding trend record
- **Unmatched demand skills:** 0
- **Unmatched trend skills:** 0
- Full per-skill coverage status is tracked in `reports/combined/coverage_audit.csv`

> **Note:** The demand dataset covers the top 20 skills by frequency. Generic terms (Agile, Communication, Leadership, Scrum) were excluded from the skill list by design because no Google Trends query can isolate them reliably (`config/review2_skills.json`).

---

### 4. Matched Skills Analysis & Evidence-Based Recommendations

**Quadrant Summary:** 2 INVEST · 8 OPPORTUNITY · 1 HYPE · 9 AVOID

> ⚠ **Low-volume flag (†):** Google Trends search volume is low for these skills; percentage changes are noisier and should be interpreted conservatively.
> ⚠ **Unconfirmed trend (‡):** Mann-Kendall test is not statistically significant; the directional classification is indicative only.

| Skill | Rank | Demand % | Momentum | Δ% (5-yr) | Flags | Quadrant | Summary Recommendation |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Machine Learning** | #1 | 5.26% | Rising | +40.0% | — | **INVEST** | Highest employer demand + confirmed rising search interest. Top priority for technical upskilling. |
| **AWS** | #2 | 4.63% | Stable | −5.6% | — | **OPPORTUNITY** | Second-highest demand; stable and confirmed trend. Dependable foundational cloud skill. |
| **Python** | #3 | 4.09% | Declining | −33.6% | — | **OPPORTUNITY** | Very high demand despite declining search interest (trend confirmed). Likely reflects saturation of a mature skill, not reduced employer need. |
| **SQL** | #4 | 4.01% | Declining | −56.1% | — | **OPPORTUNITY** | High demand; steep confirmed decline in search interest consistent with SQL becoming a baseline expectation. |
| **Azure** | #5 | 3.51% | Declining | −16.7% | ‡ | **OPPORTUNITY** | High demand; declining class but Mann-Kendall trend unconfirmed (p=0.556). Treat directional signal with caution. |
| **SEO** | #6 | 2.60% | Stable | 0.0% | ‡ | **OPPORTUNITY** | High employer demand (2.60%, rank #6) and a stable classification based on the ±10% threshold. However, the Mann–Kendall test is statistically significant (p = 0.0007), so the stable classification is not confirmed under Member B's validation rule (which requires MK to be non-significant for stable labels). Interpret the stable classification cautiously. |
| **Kubernetes** | #7 | 2.00% | Declining | −25.0% | †‡ | **OPPORTUNITY** | High demand; low-volume signal with unconfirmed Mann-Kendall trend (p=0.2482). Decline may be noisy. |
| **Google Cloud** | #8 | 1.81% | Rising | +50.0% | † | **INVEST** | High demand + rising confirmed trend, but low-volume signal. Rising percentage change should be contextualized by absolute volume. |
| **Spark** | #9 | 1.71% | Declining | −50.0% | † | **OPPORTUNITY** | High demand; large confirmed decline but low-volume signal inflates proportional change. |
| **SAP** | #10 | 1.57% | Declining | −71.4% | †‡ | **OPPORTUNITY** | Just above median demand; extreme percentage decline but low-volume, unconfirmed trend (p=0.4054). Treat with high caution. |
| **Java** | #11 | 1.37% | Declining | −57.4% | — | **AVOID** | Just below median demand; steep confirmed declining search interest — consistent with Java's positioning as a legacy foundational skill. |
| **Power BI** | #12 | 0.98% | Stable | 0.0% | — | **AVOID** | Below median demand; stable confirmed trend. Monitoring recommended as BI tooling market evolves. |
| **Linux** | #13 | 0.87% | Declining | −36.0% | — | **AVOID** | Below median demand with confirmed declining trend. May reflect platform-level commoditization. |
| **React** | #14 | 0.68% | Declining | −50.0% | ‡ | **AVOID** | Below median demand; declining class but Mann-Kendall unconfirmed (p=0.1632). |
| **Excel** | #15 | 0.65% | Stable | +1.4% | — | **AVOID** | Below median demand; stable confirmed trend. Lower hiring priority in data-centric roles. |
| **Docker** | #16 | 0.58% | Stable | 0.0% | — | **AVOID** | Below median demand with stable confirmed trend. |
| **Tableau** | #17 | 0.54% | Declining | −33.3% | † | **AVOID** | Below median demand; confirmed declining trend but low-volume signal. |
| **Deep Learning** | #18 | 0.51% | Rising | +66.7% | † | **HYPE** | Below median job postings despite strongly rising search interest. The gap between public buzz and current hiring suggests speculative adoption; monitor before treating as an immediate hiring priority. Trend confirmed but low-volume. |
| **Git** | #19 | 0.37% | Declining | −25.0% | — | **AVOID** | Low demand and confirmed declining search interest. Git may be assumed as a baseline competency rather than a differentiating skill. |
| **JavaScript** | #20 | 0.37% | Declining | −59.5% | — | **AVOID** | Low demand in this dataset; steep confirmed declining trend. May reflect specialization away from full-stack generalist roles in this posting cohort. |

---

### 5. Business Recommendations

Recommendations are derived directly from the quadrant assignments and confirmed trend signals. Recommendations that are not directly established by the data are explicitly labelled as hypotheses.

**Priority Investment Skills (INVEST quadrant):**
- **Machine Learning** is the strongest investment signal: highest employer demand (5.26%) combined with a statistically confirmed rising trend (+40%). This reflects durable industry adoption rather than transient hype.
- **Google Cloud** shows rising confirmed momentum (+50%), but the low-volume search signal requires caution; the absolute number of searches is small, making the proportional gain volatile.

**Dependable Foundational Skills (OPPORTUNITY quadrant):**
- **Python, SQL, AWS, Azure, SEO, Kubernetes, Spark, SAP** all show high employer demand paired with stable or declining search interest. Declining search interest for mature technologies (Python, SQL) is consistent with these skills becoming baseline competencies — candidates should develop them but should not expect differentiation from them alone. *Hypothesis (not directly established by data):* declining search interest may partly reflect reduced hype as skills mature, rather than declining utility.
- For **Azure, Kubernetes, and SAP**, the Mann-Kendall trend is not statistically confirmed. The declining classification is indicative only and should not drive strong strategic conclusions without additional evidence.

**Watch / Monitor (HYPE quadrant):**
- **Deep Learning** has rising confirmed search interest (+67%) but ranks 18th in actual job postings (0.51% of listings). This gap between public buzz and current hiring is a classic hype signal. Candidates with a strong Machine Learning foundation should monitor Deep Learning role creation before pivoting entirely. *Limitation:* low search volume means the +67% is measured against a small baseline.

**Lower Current Priority (AVOID quadrant):**
- **Java, Power BI, Linux, React, Excel, Docker, Tableau, Git, JavaScript** fall below the demand median. This does not mean these skills are valueless — many are broadly expected as part of a standard competency baseline — but they are not differentiating hiring signals in this dataset at this time.
- **Limitation:** The demand proxy is based on 7,240 postings scraped from a single source at a specific time. Sector-specific or role-specific analyses might yield different rankings.

---

### 6. Demand-Interest Gap Visualization
The 2x2 matrix plot is generated and exported to `reports/combined/demand_interest_quadrant.png`:
- **X-axis:** 5-Year Search Momentum ($\Delta\%$ in Google Trends, India)
- **Y-axis:** Employer Demand (% of 7,240 Postings)
- **Horizontal boundary:** Empirical demand median (1.47%)
- **Vertical boundary:** Rising momentum threshold (+10.0%)
- **Shaded corridor:** Stable search zone (−10% to +10%)
- All 20 matched skills are plotted. Quadrant background fills indicate strategic zones.

---

### 7. Methodology Limitations
1. **Google Trends is not a direct measure of supply or competition.** It measures relative search interest within a geography (India) and timeframe, normalized to 0–100. It cannot confirm how many people are studying, certified in, or available with a skill.
2. **Low-volume signals are inherently noisier.** For Kubernetes, Google Cloud, Spark, SAP, Tableau, and Deep Learning, absolute search volumes are low; percentage changes should be contextualized accordingly.
3. **Unconfirmed Mann-Kendall trends** (`trend_confirmed = False`) should be interpreted carefully, as the reason varies by skill:
   - **Azure, Kubernetes, SAP, React:** classified as declining or stable, but the Mann–Kendall p-value is not significant (p ≥ 0.05), so the directional classification is not statistically confirmed.
   - **SEO:** classified as stable (pct_change = 0.0%) under the ±10% threshold, and the Mann–Kendall test is statistically significant (p = 0.0007). However, under Member B's validation rule, a stable classification is only confirmed when the Mann–Kendall test is *not* significant (i.e., no monotonic trend detected). Because MK is significant for SEO, the stable label is not confirmed by the test — the significant result indicates the presence of a trend, which is inconsistent with a stable classification. This is the validation rule operating as intended, not a data or software error. Interpret SEO's stable classification cautiously.
4. **Demand proxy limitations.** Only 7,240 postings from a single aggregator at a single point in time are analyzed. The posted skill frequencies reflect employer self-reporting practices, which may underrepresent skills assumed as implicit prerequisites.
5. **No direct causal inference.** The quadrant framework identifies associations between demand and interest signals; it does not establish causal relationships between search trends and hiring volumes.

---

## 4. Predictive Modeling: Baseline and Methodological Corrections

### 4.1 Audit of Historical Review 1 Flaws

An exhaustive audit of the historical codebase and notebook revealed critical methodological vulnerabilities in Review 1:
1. **Severe Cross-Task Split Leakage:** The 3-class and binary models were evaluated on entirely different train/test splits. Consequently, **78.8% of the 3-class test postings were present in the binary training set**, creating severe cross-task contamination and invalidating comparative claims.
2. **Reconstructed Flawed Binary Baseline:** The historical Review 1 audit documented a majority-class baseline of 46.75% for the binary task—a mathematical impossibility ($\max(p, 1-p) \ge 0.5$). While the original notebook printed the 3-class baseline (36.7%) but did not explicitly record a binary baseline cell output, this 46.75% figure represents an inferred or reconstructed value derived from an unstratified test split minority proportion ($108 / 231 = 46.75\%$).
3. **Currency-as-Experience Parsing Error:** The extraction regex `re.search(r'(\d+)\s*\+?\s*(?:years?|yrs?)', text)` matched salary numbers preceding the word "year" in annual compensation phrases. For example, `'compensation rs5 140 448 year'` extracted **448 years of experience**, while job ID 5898178897 extracted **190 years** from ₹2,894,190/year.
4. **Dataset-Wide Target Quantile Leakage:** Salary-band cutpoints were computed using `pd.qcut` across all 1,153 salary-bearing postings prior to splitting, leaking test distribution information into target definitions.

### 4.2 Phase 1 Remediation Implementation

To establish an authoritative, leak-free benchmark, the following corrections were implemented in `scripts/evaluate_phase1_baseline.py`:
- **Unified Stratified Holdout Partition:** Created a single, permanent 80/20 train/test split stratified on salary band ($N_{\text{train}}=922, N_{\text{test}}=231$). Test partition indices and job IDs were permanently sealed in `reports/modeling/test_split_indices.json` and `test_split_job_ids.csv`.
- **Training-Derived Target Definitions:**
  - **Three-Class Salary Bands:** Derived strictly from the 922 training observations: $\text{Low} \le ₹600,000$ (338 train / 85 test), $\text{Medium } ₹600,000–₹1,600,000$ (281 train / 70 test), and $\text{High} > ₹1,600,000$ (303 train / 76 test).
  - **Binary Salary Target:** Derived from training median $\text{Median}(y_{\text{train}}^{\text{mid}}) = ₹1,020,000$ INR, ensuring an exact 50.0% / 50.0% class balance on train (461 Below / 461 Above) and 50.2% / 49.8% on test (116 Below / 115 Above).
- **Contextual Experience Extraction:** Rewrote experience parsing to require proximity to experience terms, bounding outputs within $[0, 25]$ years and introducing an explicit `experience_is_missing` flag (imputing missing values with the training median).
- **Strict Preprocessing Encapsulation:** Encapsulated `StandardScaler`, `SimpleImputer`, and `OneHotEncoder(handle_unknown='ignore')` inside an `sklearn.compose.ColumnTransformer` fitted strictly on training data.

### 4.3 Phase 1 Baseline Results

All models were evaluated using 5-fold Stratified Cross-Validation on the 922 training rows, followed by evaluation on the 231 held-out test postings.

#### Phase 1 Model Benchmark (Fixed Holdout, N=231)

| Task | Model | 5-Fold CV Macro-F1 | Test Accuracy | Balanced Acc | Test Macro-F1 | Test ROC-AUC |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Three-Class** | Majority Dummy Baseline | 0.1788 $\pm$ 0.0008 | 36.80% | 33.33% | 0.1793 | 0.5000 |
| **Three-Class** | Logistic Regression | 0.4604 $\pm$ 0.0450 | 56.28% | 55.08% | 0.5377 | 0.7070 |
| **Three-Class** | Random Forest (Default) | 0.5241 $\pm$ 0.0351 | 55.41% | 54.43% | 0.5397 | 0.7158 |
| **Binary** | Majority Dummy Baseline | 0.3329 $\pm$ 0.0006 | 49.78% | 50.00% | 0.3324 | 0.5000 |
| **Binary** | Logistic Regression | 0.6524 $\pm$ 0.0251 | 72.73% | 72.73% | 0.7273 | 0.7901 |
| **Binary** | Random Forest (Default) | 0.6753 $\pm$ 0.0312 | 71.00% | 70.98% | 0.7096 | 0.7949 |

### 4.4 Traceability of Historical Review 1 Figures

Historical Review 1 figures (SVM 3-class test accuracy of 51.52%, Macro-F1 of 0.509; XGBoost binary test accuracy of 78.35%, Macro-F1 of 0.783) were generated under divergent test splits with 78.8% split contamination. While documented in `reports/modeling/phase1_evaluation_report.md` for historical provenance, direct numerical comparisons are methodologically invalid due to split contamination and flawed baselines.

---

## 5. Skill Expansion and Text Fusion

### 5.1 Phase 2A: Skill Taxonomy Expansion

In Phase 1, feature sparsity was identified as a primary performance bottleneck: **68.95% of salary-bearing postings (795 / 1,153) contained zero detected skills** under the historical 12-skill regex list.

In Phase 2A (`scripts/experiments/phase2a_skill_features.py`), the taxonomy was expanded to **50 domain-curated regex patterns grouped across 8 functional categories** (Programming & Web, Soft & Professional, Functional & Marketing, Cloud & DevOps, Data Engineering, Data Science & AI, Database Management, and Infrastructure). Rather than 50 universally distinct technologies, the patterns represent a structured dictionary capturing functional roles and competencies:

- **Zero-Skill Postings:** Reduced from **68.95% (795 postings) to 40.33% (465 postings)**, recovering 330 postings (+28.62 percentage points).
- **Postings with $\ge 1$ Skill:** Rose from **31.05% (358 postings) to 59.67% (688 postings)**.
- **Role Equity Gains:** Zero-skill rates fell dramatically across non-data roles: Graphic Designer dropped from 89.0% to 40.0% (+49.0 pp), Project Manager from 73.9% to 26.1% (+47.7 pp), and Digital Marketing from 93.0% to 57.0% (+35.9 pp).
- **Precision Disambiguation:** Precision safeguards were implemented, such as rejecting the bare stem `\blead\b` (which matches 246 postings as titles or verbs) in favor of `\bleadership\b` (35 verified soft-skill matches), and validating specific acronyms (`ci_cd`, `gcp`, `ml`).

### 5.2 Phase 2B: Multimodal Text Fusion Pipeline

Despite expanding the skill taxonomy, 40.33% of postings lacked detected skills due to abbreviated job stubs. To leverage latent semantic signals within `description_clean`, Phase 2B introduced multimodal text fusion:
- **Compensation Scrubbing:** Applied `scrub_compensation_text()` prior to feature extraction to eliminate any possibility of salary text bleeding into predictors.
- **Text Feature Architecture:** TF-IDF vectorization (word n-grams 1–2, sublinear term frequency, min document frequency 2, max 5,000 features) reduced to **50 dense semantic components via `TruncatedSVD`**, standardized, and concatenated with structured features.
- **Pipeline Integrity:** The text branch was strictly fitted within training partitions inside each cross-validation fold.

#### Experimental Configurations
- **Configuration A (Structured Baseline):** 12 historical skill indicators, role, location bucket, work mode, seniority ordinal, experience required, missing flag, contract type, and skill count (from scrubbed text).
- **Configuration B (Structured + 50 Skills):** Config A features augmented with the 50 expanded skill indicators.
- **Configuration C (Multimodal Fusion):** Config B features combined with the 50 standardized `TruncatedSVD` text components.

#### Phase 2B Model Comparison Across Configurations (Fixed Holdout, N=231)

| Configuration | Algorithm | 3-Class CV Macro-F1 | 3-Class Test Acc | 3-Class Test Macro-F1 | Binary CV Macro-F1 | Binary Test Acc | Binary Test Macro-F1 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Config A** | Logistic Regression | 0.4604 $\pm$ 0.0450 | 56.28% | 0.5377 | 0.6524 $\pm$ 0.0251 | 72.73% | 0.7273 |
| **Config A** | Random Forest | 0.5320 $\pm$ 0.0318 | 54.55% | 0.5298 | 0.6579 $\pm$ 0.0350 | 71.86% | 0.7181 |
| **Config B** | Logistic Regression | 0.4908 $\pm$ 0.0371 | 53.68% | 0.5225 | 0.6581 $\pm$ 0.0218 | 71.00% | 0.7098 |
| **Config B** | Random Forest | 0.5324 $\pm$ 0.0253 | 52.81% | 0.5084 | 0.6777 $\pm$ 0.0225 | 69.26% | 0.6915 |
| **Config C** | Logistic Regression | 0.5354 $\pm$ 0.0276 | 55.41% | 0.5384 | 0.7048 $\pm$ 0.0231 | 74.89% | 0.7487 |
| **Config C** | **Random Forest** | **0.5522 $\pm$ 0.0371** | **63.20%** | **0.6140** | **0.7358 $\pm$ 0.0230** | **76.19%** | **0.7615** |

*Takeaway:* Multimodal fusion (Configuration C) produced substantial empirical lift across both tasks. For the 3-class task, Random Forest accuracy increased by **+8.65 percentage points** (54.55% $\to$ 63.20%) and Macro-F1 by **+0.0842** (0.5298 $\to$ 0.6140) over Configuration A.

---

## 6. Cross-Validation and Hyperparameter Tuning

### 6.1 Phase 2C Optimization Methodology

In Phase 2C (`scripts/experiments/phase2c_model_tuning.py`), systematic hyperparameter optimization was conducted strictly within the 922 training postings using 5-fold Stratified Cross-Validation. Candidate models were optimized for validation Macro-F1.

- **Candidate Algorithms Evaluated:** Config C Logistic Regression (regularization strength $C$, penalty, solver), Config C Random Forest (tree depth, min leaf size, max features, number of estimators, class weights), and Config A Random Forest as the structured reference.
- **Environment Status:** External gradient boosting packages (`xgboost`, `lightgbm`, `catboost`) were unavailable in the execution environment. Tree-based nonlinear modeling was thoroughly explored via randomized and grid sweeps on `RandomForestClassifier`.
- **Zero Test Contamination:** Zero test-set observations were involved in parameter selection.

### 6.2 Cross-Validation Tuning Results (Training Set Only, N=922)

| Task | Configuration / Model | 5-Fold CV Macro-F1 (Mean $\pm$ Std) | Train-Fold Macro-F1 | Optimal Hyperparameters |
| :--- | :--- | :---: | :---: | :--- |
| **3-Class** | **Config C Tuned RF (Champion)** | **0.5648 $\pm$ 0.0260** | **0.9688** | `{"n_estimators": 150, "min_samples_leaf": 4, "max_depth": 10, "max_features": "sqrt", "class_weight": "balanced"}` |
| **3-Class** | Config C Tuned LR | 0.5562 $\pm$ 0.0294 | 0.6644 | `{"C": 0.1, "class_weight": "balanced", "penalty": "l2", "solver": "lbfgs"}` |
| **3-Class** | Config A Tuned RF (Ref) | 0.5320 $\pm$ 0.0318 | 0.8017 | `{"n_estimators": 100, "min_samples_leaf": 1, "max_depth": 10, "max_features": "sqrt", "class_weight": "balanced"}` |
| **Binary** | **Config C Tuned RF (Champion)** | **0.7387 $\pm$ 0.0389** | **0.9984** | `{"n_estimators": 150, "min_samples_leaf": 2, "max_depth": 15, "max_features": 0.3, "class_weight": null}` |
| **Binary** | Config C Tuned LR | 0.7309 $\pm$ 0.0323 | 0.7817 | `{"C": 0.05, "class_weight": null, "penalty": "l2", "solver": "lbfgs"}` |
| **Binary** | Config A Tuned RF (Ref) | 0.6812 $\pm$ 0.0345 | 0.7400 | `{"n_estimators": 250, "min_samples_leaf": 4, "max_depth": 12, "max_features": "log2", "class_weight": "balanced"}` |

### 6.3 Analysis of Generalization Gap & Overfitting

A critical finding in Phase 2C is the substantial **training-versus-validation generalization gap** exhibited by Random Forest models:
- In the 3-class task, the champion RF achieved a train-fold Macro-F1 of **0.9688** compared to a validation CV Macro-F1 of **0.5648**.
- In the binary task, the champion RF achieved a train-fold Macro-F1 of **0.9984** compared to a validation CV Macro-F1 of **0.7387**.

This behavior reflects the high capacity of decision tree ensembles when operating on 50 continuous SVD text components alongside 50 sparse skill indicators. Restricting `max_depth` (10 and 15) and enforcing minimum leaf requirements (`min_samples_leaf` of 4 and 2) stabilized fold variance (reducing 3-class CV standard deviation from $\pm 0.0371$ to $\pm 0.0260$) without degrading validation performance.

---

## 7. Final Holdout Evaluation and Model Comparison

### 7.1 Single Final Evaluation on Held-Out Test Split (N=231)

Following selection based strictly on training-set cross-validation, candidate models were evaluated once on the untouched 231-posting test split.

| Task | Configuration / Model | Test Accuracy | Balanced Acc | Test Macro-F1 | Macro Precision | Macro Recall | Test ROC-AUC |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **3-Class** | **Config C Tuned RF (Champion)** | **61.90%** | **60.92%** | **0.6059** | **0.6118** | **0.6092** | **0.7937** |
| **3-Class** | Config C Tuned LR | 58.44% | 57.62% | 0.5726 | 0.5735 | 0.5762 | 0.7499 |
| **3-Class** | Config A Tuned RF (Ref) | 54.55% | 53.47% | 0.5298 | 0.5345 | 0.5347 | 0.7141 |
| **Binary** | **Config C Tuned RF (Champion)** | **75.76%** | **75.75%** | **0.7575** | **0.7576** | **0.7575** | **0.8507** |
| **Binary** | Config C Tuned LR | 72.73% | 72.73% | 0.7273 | 0.7274 | 0.7273 | 0.8238 |
| **Binary** | Config A Tuned RF (Ref) | 74.89% | 74.90% | 0.7489 | 0.7490 | 0.7490 | 0.7941 |

### 7.2 Empirical Progression Across Project Milestones

The progression across the four engineering phases on the identical, leak-free holdout split ($N_{\text{test}}=231$) demonstrates clear methodological and empirical advancement:

| Task | Milestone / Model | Test Accuracy | Balanced Acc | Test Macro-F1 | Test ROC-AUC | Methodological State |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **3-Class** | Phase 1 Baseline (LR) | 56.28% | 55.08% | 0.5377 | 0.7070 | Clean split, 12 skills, no text features |
| **3-Class** | Phase 2B Default RF (Config C) | 63.20% | 62.08% | 0.6140 | 0.8010 | +50 Skills + 50 SVD text components |
| **3-Class** | **Phase 2C Tuned RF (Champion)** | **61.90%** | **60.92%** | **0.6059** | **0.7937** | **Optimal leaf & depth regularization** |
| **Binary** | Phase 1 Baseline (LR) | 72.73% | 72.73% | 0.7273 | 0.7901 | Honest split, training median cut |
| **Binary** | Phase 2B Default RF (Config C) | 76.19% | 76.17% | 0.7615 | 0.8534 | +50 Skills + 50 SVD text components |
| **Binary** | **Phase 2C Tuned RF (Champion)** | **75.76%** | **75.75%** | **0.7575** | **0.8507** | **Honest, leak-free holdout generalization** |

### 7.3 Honest Comparison: Phase 2B vs. Phase 2C

A rigorous academic review must candidly disclose the relationship between cross-validation and holdout metrics:
- **Cross-Validation Lift:** Hyperparameter tuning slightly increased CV Macro-F1 on the training partition ($0.5522 \to 0.5648$ for 3-class RF; $0.7358 \to 0.7387$ for binary RF) and reduced fold variance ($\pm 0.0371 \to \pm 0.0260$).
- **Holdout Test Generalization:** On the untouched test partition ($N=231$), the tuned models scored nominally slightly lower than default settings (3-class Macro-F1 $0.6140 \to 0.6059$, Accuracy $63.20\% \to 61.90\%$; binary Macro-F1 $0.7615 \to 0.7575$, Accuracy $76.19\% \to 75.76\%$).
- **Analytical Interpretation:** The three-class holdout accuracy decreased from 63.20% (146/231 correct) to 61.90% (143/231 correct), a difference of three correct predictions. Binary holdout accuracy decreased from 76.19% (176/231 correct) to 75.76% (175/231 correct), a difference of one correct prediction. The corresponding Macro-F1 changes were 0.6140 to 0.6059 for the three-class task and 0.7615 to 0.7575 for the binary task. These are separate metrics and should not be interpreted as direct conversions between Macro-F1 differences and error counts. While hyperparameter tuning slightly improved cross-validation Macro-F1 on the training set and tightened tree regularization, it did not improve holdout Macro-F1 relative to the Phase 2B Configuration C Random Forest baseline. In the absence of formal paired statistical tests (such as $5\times 2\text{cv}$ paired $t$-tests), we do not describe these models as statistically equivalent or superior; we conclude strictly that tuning constrained tree complexity on training folds while holdout performance remained slightly lower.

### 7.4 Confusion Matrix Diagnostics & Error Shift

Analysis of confusion matrices (`reports/modeling/phase2c_confusion_matrices.png`) provides actionable diagnostic insights across both tasks:
- **Adjacent Band Dominance:** For the 3-class champion model, out of 88 total test classification errors, **63 errors occurred between immediately adjacent bands** (Low $\leftrightarrow$ Medium or Medium $\leftrightarrow$ High):
  - **63 / 88 = 71.59%** of classification errors;
  - **63 / 231 = 27.27%** of all test postings.
- **Severe Opposite-End Errors:** Extreme misclassifications (predicting Low when True is High, or vice versa) accounted for **25 errors**:
  - **25 / 88 = 28.41%** of classification errors;
  - **25 / 231 = 10.82%** of all test postings.
  - *Note on Mutual Exclusivity:* Because misclassifications in a 3-class ordered sequence can only have distance 1 (adjacent) or distance 2 (opposite end), adjacent errors (63) and opposite-end errors (25) are mutually exclusive and collectively exhaustive ($63 + 25 = 88$ total errors).
- **Binary Classification Breakdown:** Out of 231 test postings, the binary champion correctly identified 87 below-median and 88 above-median salaries, with 29 false positives and 27 false negatives (Balanced Accuracy = 75.75%, ROC-AUC = 0.8507).

---

## 8. Limitations and Future Improvements

### 8.1 Methodological and Practical Limitations

1. **Random Forest Generalization Gap:** Despite depth and leaf regularization, Random Forest models display a persistent gap between training-fold performance (Macro-F1 $\sim 0.97$) and validation/test performance ($\sim 0.61$). While ensembling mitigates variance, unpruned tree structures risk memorizing high-dimensional sparse text vectors.
2. **Environment & Package Restrictions:** Gradient-boosted decision tree libraries (`xgboost`, `lightgbm`, `catboost`) were unavailable in the execution environment. Tree-based modeling was constrained to scikit-learn's `RandomForestClassifier`.
3. **Statistical Significance Bounds:** Given a test partition of $N=231$, metric variations of 0.5%–1.0% correspond to shifts of 1–3 individual postings. In the absence of formal paired hypothesis testing (e.g., $5\times 2\text{cv}$ paired $t$-test or Wilcoxon signed-rank test), small metric differences between configurations cannot be claimed as statistically significant.
4. **Scraped Data Disclosure Bias:** Only 1,153 out of 7,240 postings (15.93%) disclose explicit compensation. Companies that publish compensation figures may systematically differ in company size, industry, or hiring urgency from those that omit them, introducing unobserved selection bias.
5. **Leakage Boundary Scope:** The specific technical leakage pathways identified during auditing—cross-task split overlap, dataset-wide target quantile derivation, out-of-fold text/scaler fitting, and compensation text bleeding into structured predictors—were systematically addressed within the scikit-learn pipeline. However, we do not claim that every possible source of leakage has been eliminated: unobserved latent correlations, subtle metadata dependencies, and broader dataset-level self-selection reporting biases cannot be resolved through feature engineering or pipeline encapsulation alone.
6. **Model Serialization:** In strict accordance with safety guidelines, no model binaries were serialized to `models/` without explicit authorization.

### 8.2 Recommended Roadmap for Review 3 / Final Submission

1. **Gradient Boosting Benchmarks:** Provision `lightgbm` or `xgboost` with early stopping and monotonic constraints to evaluate whether boosted shallow trees mitigate the tree generalization gap.
2. **Contextual Language Models:** Replace TF-IDF + SVD with domain-specific sentence embeddings (e.g., JobBERT or `all-MiniLM-L6-v2`) to capture nuanced semantic relationships in job descriptions.
3. **Ordinal & Cost-Sensitive Loss Functions:** Formulate the 3-class salary task as an ordinal classification problem or implement cost-sensitive learning to penalize extreme misclassifications (Low $\leftrightarrow$ High) more heavily than adjacent errors.
4. **Longitudinal Trend Re-Collection:** Re-run Google Trends collection (using the Knowledge Graph topic IDs in `config/review2_skills.json`) for all 20 skills after a 6-month interval to measure whether current quadrant assignments are stable or shifting over time. Full 20/20 coverage is achieved; the next step is temporal re-validation rather than skill list expansion.

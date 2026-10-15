# Phase 2A Validation Report: Skill Feature Extraction Expansion

**Course:** Business Analytics — Data Analysis and Predictive Modelling  
**Module:** Salary Prediction Feature Pipeline  
**Phase:** Phase 2A — Skill Taxonomy Expansion & Precision Audit  

---

## 1. Executive Summary & Objective

During the Phase 1 audit, a critical cause of low baseline accuracy was identified: **68.95% of salary-bearing postings (795 / 1,153) contained zero detected skills** under the historical 12-skill regex list. Non-technical roles (Digital Marketing, Graphic Design, Project Management) had zero-skill rates exceeding 80%.

In Phase 2A, we expanded the skill taxonomy to **50 domain-curated, disambiguated features** across 8 functional categories, strictly calibrated against spaCy-lemmatized `description_clean` text without using target or salary labels.

### Key Coverage Results:
- **Zero-Skill Postings:** Dropped from **68.95% (795 postings) &rarr; 40.33% (465 postings)**, recovering **330 postings (a 28.62 percentage point improvement)**.
- **Postings with $\ge 1$ Skill:** Rose from **31.05% (358 postings) &rarr; 59.67% (688 postings)**.
- **Role Equity:** Massive gains in previously unserved roles: Digital Marketing zero-skill rate dropped from **82.4% &rarr; 28.9%** (+53.5 pp gain), Project Management from **71.9% &rarr; 22.9%** (+49.0 pp gain).

---

## 2. Skill Count Distribution Comparison (N = 1,153)

| Skill Count Bracket | Original Postings (12 Skills) | Original % | Expanded Postings (50 Skills) | Expanded % | Net Change |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **0 skills** | 795 | 68.95% | 465 | 40.33% | -330 |
| **1 skill** | 237 | 20.56% | 331 | 28.71% | +94 |
| **2 skills** | 91 | 7.89% | 170 | 14.74% | +79 |
| **3 skills** | 27 | 2.34% | 98 | 8.50% | +71 |
| **4 skills** | 2 | 0.17% | 49 | 4.25% | +47 |
| **5+ skills** | 1 | 0.09% | 40 | 3.47% | +39 |

---

## 3. Top Most Frequently Detected Skills

| Rank | Skill | Category | Postings Detected | % of Postings | Origin |
| :---: | :--- | :--- | :---: | :---: | :---: |
| 1 | Python | Programming & Web | 102 | 8.85% | Historical 12 |
| 2 | Stakeholder Management | Soft & Professional | 88 | 7.63% | **Newly Added** |
| 3 | Project Management | Soft & Professional | 87 | 7.55% | **Newly Added** |
| 4 | SQL | Programming & Web | 85 | 7.37% | Historical 12 |
| 5 | Machine Learning / ML | Data Science & AI | 76 | 6.59% | Historical 12 |
| 6 | Communication | Soft & Professional | 70 | 6.07% | Historical 12 |
| 7 | Social Media Marketing | Functional & Marketing | 66 | 5.72% | **Newly Added** |
| 8 | Azure | Cloud & DevOps | 64 | 5.55% | Historical 12 |
| 9 | CI/CD & Jenkins | Cloud & DevOps | 62 | 5.38% | **Newly Added** |
| 10 | ETL Pipelines | Data Engineering | 51 | 4.42% | **Newly Added** |
| 11 | Google Cloud (GCP) | Cloud & DevOps | 47 | 4.08% | **Newly Added** |
| 12 | SEO / SEM | Functional & Marketing | 44 | 3.82% | **Newly Added** |
| 13 | Agile | Functional & Marketing | 44 | 3.82% | Historical 12 |
| 14 | AWS | Cloud & DevOps | 43 | 3.73% | Historical 12 |
| 15 | Apache Spark | Data Engineering | 37 | 3.21% | **Newly Added** |

---

## 4. Role-Level Coverage Impact

The expanded dictionary prevents non-data roles from collapsing to zero-skill vectors:

| Role | Total Postings | Original Zero-Skill % | Expanded Zero-Skill % | Coverage Recovery Gain |
| :--- | :---: | :---: | :---: | :---: |
| **Graphic Designer** | 100 | 89.0% | 40.0% | **+49.0 pp** |
| **Project Manager** | 153 | 73.9% | 26.1% | **+47.7 pp** |
| **Digital Marketing** | 142 | 93.0% | 57.0% | **+35.9 pp** |
| **Data Scientist** | 75 | 53.3% | 26.7% | **+26.7 pp** |
| **Data Analyst** | 35 | 80.0% | 54.3% | **+25.7 pp** |
| **Business Analyst** | 84 | 70.2% | 45.2% | **+25.0 pp** |
| **Devops / Cloud Engineer** | 145 | 52.4% | 29.0% | **+23.4 pp** |
| **Product Manager** | 91 | 94.5% | 71.4% | **+23.1 pp** |
| **Software Engineer** | 218 | 64.7% | 48.2% | **+16.5 pp** |
| **Data Engineer** | 110 | 28.2% | 13.6% | **+14.5 pp** |

---

## 5. Pattern Disambiguation & Precision Risk Analysis

Higher match counts do not automatically guarantee better features. Below is the precision audit for high-frequency terms:

1. **`leadership` (`\bleadership\b`):**
   - *Precision Defense:* We strictly rejected matching the bare stem `\blead\b`, which occurs in 246 postings primarily as a verb or title element (*'lead projects'*, *'tech lead'*). By enforcing `\bleadership\b`, matches (35 postings) reflect verified soft skill requirements.
2. **`stakeholder_management` (`\bstakeholder\b`):**
   - *Observation:* Appears in 88 postings (7.63%), predominantly in Product/Project Management and Senior Analyst roles. While reflecting cross-functional scope, it can occasionally represent corporate boilerplate.
3. **`ci_cd` (`\bci\s*cd\b|\bcicd\b|\bjenkins\b`):**
   - *Observation:* Captured in 62 postings. In `description_clean`, slashes were converted to spaces, so `\bci\s*cd\b` successfully detects lemmatized instances like *'ci cd pipeline'*.
4. **`gcp` (`\bgcp\b|\bgoogle cloud\b`):**
   - *Observation:* Captured in 47 postings. In India tech postings, GCP is uniformly used for Google Cloud Platform without conflicting acronyms.
5. **`machine_learning` (`\bmachine learn\w*\b|\bml\b`):**
   - *Observation:* Manual spot-checks confirmed `\bml\b` appears exclusively in Data Science / ML contexts (*'ai ml engineer'*, *'ml algorithms'*).

---

## 6. Unresolved Concerns & Next Steps

1. **Remaining 40.33% Zero-Skill Baseline:** 465 postings still contain no detected skills from the 50 terms. This occurs primarily in extremely brief job stubs (e.g. 15-word agency blurbs). Regex expansion alone cannot extract skills that are not present in the text.
2. **Recommendation for Phase 2B:** Combine these 50 curated indicator columns with **TF-IDF n-grams + TruncatedSVD text embeddings**, which capture long-tail vocabulary, domain terminology, and role context directly from raw job descriptions.

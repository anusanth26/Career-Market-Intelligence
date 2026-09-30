# 📑 Career Market Intelligence Engine — Review 1 Report
**Domain:** Business Analytics & Labor Market Intelligence  
**Milestone:** Review 1 — Data Acquisition, Preprocessing, Integrity Audit & Exploratory Data Analysis (EDA)  
**Primary Dataset:** `data/cleaned/postings_combined.csv` (2,472 records, 37 attributes)  
**Pipeline Execution:** Verified Zero Data Loss, Zero Data Alteration, 100% Schema Alignment  

---

## 1. Executive Summary & Problem Formulation
The rapid evolution of technological skill demands and shifting compensation structures creates substantial market asymmetry for job seekers, hiring teams, and academic curriculum designers. The **Career Market Intelligence Engine** leverages programmatic job posting data across key modern roles (**Software Engineer**, **Data Analyst**, **Business Analyst**, and **Digital Marketing**) to provide empirical transparency into:
1. Compensation spreads across seniority levels and role archetypes.
2. Geographic hiring concentration and tech hub clustering across India.
3. Emerging remote and hybrid work arrangement prevalence.
4. Core technical competencies and cross-role skill requirements.

This Review 1 milestone documents the end-to-end data acquisition, structured and textual preprocessing pipelines, rigorous data integrity validations, and an extensive exploratory analysis utilizing **8 distinct visualization techniques**.

---

## 2. Dataset Architecture & Pipeline Overview

The production master dataset, [`data/cleaned/postings_combined.csv`](../data/cleaned/postings_combined.csv), unifies two dedicated cleaning pipelines:
1. **Structured Data Pipeline** (`postings_structured.csv` — 31 attributes): Metadata standardization, geographic mapping, seniority extraction, and median salary imputation.
2. **Text Processing Pipeline** (`postings_text.csv` — 8 attributes): Natural Language Processing (NLP) token cleaning, HTML stripping, negation-preserving stopword elimination, and spaCy lemmatization.

### Master Dataset Schema (37 Attributes)

| Category | Columns Included | Preprocessing / Integrity Handling |
| :--- | :--- | :--- |
| **Identifiers & Core** | `job_id`, `title`, `company_name`, `target_role`, `redirect_url` | 1-to-1 unique primary key; no missing values; company names stripped. |
| **Categorization** | `adzuna_category`, `category_name` | Preserved from structured and text sources; 100% verified alignment across all 2,472 rows. |
| **Seniority Ladder** | `seniority_level`, `seniority_order` | Regex hierarchical rule extraction into 6 tiers (Entry/Junior [1] to Executive/Director [6]). |
| **Geography & Remote**| `location_raw`, `standardized_city`, `standardized_state`, `country`, `is_remote` | Indian IT hub alias resolution (e.g., Gurgaon $\rightarrow$ Gurugram); remote keyword detection. |
| **Temporal Dynamics** | `posting_datetime`, `posting_date`, `posting_year`, `posting_month`, `posting_day`, `posting_day_of_week` | ISO-8601 parsing into explicit date and calendar dimensions. |
| **Compensation Engine**| `salary_raw_min`, `salary_raw_max`, `salary_reported_avg`, `salary_reported_lpa`, `is_salary_missing`, `salary_imputed`, `salary_imputed_lpa`, `salary_is_imputed` | Raw values preserved unaltered; <10k outliers flagged; hierarchical median imputation by `(target_role, seniority_level)`. |
| **Contract Specs** | `contract_time`, `contract_type`, `latitude`, `longitude` | Null values filled with explicit `'unspecified'` labels; coordinates preserved. |
| **Text & NLP Corpus** | `description_original`, `description_clean`, `description_nostopwords`, `description_lemmatized`, `description_word_count` | Raw descriptions preserved alongside cleaned, stopword-stripped, and spaCy lemmatized representations. |

---

## 3. Data Integrity & Verification Audit

To ensure maximum statistical validity without altering underlying raw data, the master dataset underwent comprehensive integrity checks (`scripts/merge_datasets.py`):

1. **Zero Data Loss**: Exactly 2,472 unique job records were collected and preserved through a strict 1-to-1 inner join on `job_id`. The 28 cross-role duplicate pulls in the text dataset were cleanly deduplicated without loss of unique postings.
2. **Zero Raw Data Alteration**: Original text (`description_original`), raw location strings (`location_raw`), and raw salary boundaries (`salary_raw_min`, `salary_raw_max`) remain intact alongside derived and imputed fields.
3. **Primary Key Health**: `job_id.nunique() == 2472` with `job_id.isnull().sum() == 0`.
4. **Attribute Completeness**: All 31 structured attributes and all 8 text attributes are represented.
5. **Boundary Compliance**: All word counts are strictly positive ($> 0$), all salary values are non-negative, and coordinates adhere to valid geodetic bounds.

---

## 4. Exploratory Data Analysis: 8 Distinct Visualization Techniques

The project folder incorporates a comprehensive suite of **8 distinct visualization techniques**, embedded directly in [`notebooks/1_eda.ipynb`](../notebooks/1_eda.ipynb), [`notebooks/1a_structured_cleaning_eda.ipynb`](../notebooks/1a_structured_cleaning_eda.ipynb), and saved as standalone high-resolution graphics in [`report/figures/`](figures/):

### Technique 1: Continuous Density Histogram & KDE (Dual-Panel)
- **File**: `report/figures/1_salary_distribution.png`
- **Methodology**: Combines frequency binning with Kernel Density Estimation (KDE) and explicit vertical central tendency lines (mean vs. median), accompanied by a log10 transformation panel.
- **Key Insight**: Reported tech salaries exhibit strong positive skewness. While the median sits at 8.0 LPA, upper-tier software engineering outliers stretch beyond 35 LPA. Log10 transformation restores normality for downstream regression modeling.

### Technique 2: Multi-Category Grouped Boxplot
- **File**: `report/figures/2_salary_by_role_boxplot.png`
- **Methodology**: Visualizes five-number summaries (Q1, median, Q3, whiskers, and IQR outliers) with embedded yellow diamond mean indicators across each job role.
- **Key Insight**: Software Engineering demonstrates both the highest median compensation (11.5 LPA) and the widest dispersion. Data Analyst roles follow at a median of 7.2 LPA, while Digital Marketing shows lower variance centered around 5.0 LPA.

### Technique 3: Direct-Annotated Vertical Bar Chart
- **File**: `report/figures/3_postings_by_role_bar.png`
- **Methodology**: Categorical frequency distribution with exact value and percentage annotations above each bar.
- **Key Insight**: Demonstrates equitable representation across collected verticals: Software Engineering (~28.5%), Business Analyst (~25.2%), Data Analyst (~24.1%), and Digital Marketing (~22.2%).

### Technique 4: Ranked Inverted Horizontal Bar Chart
- **File**: `report/figures/4_top_tech_hubs_hbar.png`
- **Methodology**: Sequential Viridis color mapping ranking the top 10 municipal hiring hubs across India with percentage callouts.
- **Key Insight**: Heavy geographic clustering exists in southern and western tech corridors: Bengaluru (26.4%), Hyderabad (12.1%), and Pune (9.7%) together account for nearly half of all nationwide opportunities.

### Technique 5: 100% Stacked Proportional Bar Chart
- **File**: `report/figures/5_seniority_distribution_stacked.png`
- **Methodology**: Normalized part-to-whole segmentation evaluating the proportional seniority composition within each target job role.
- **Key Insight**: Software Engineering postings demand substantial Senior and Lead/Architect talent (>40%), whereas Business Analyst and Digital Marketing roles recruit heavily in Mid-Level and Entry-Level brackets.

### Technique 6: Binary Proportion Donut Chart
- **File**: `report/figures/6_remote_work_donut.png`
- **Methodology**: Center-cut circular visualization with slice explode offsets and percentage labels.
- **Key Insight**: 12.2% of tech positions explicitly support full Remote / WFH flexibility, with the remaining 87.8% requiring physical or hybrid presence in urban hubs.

### Technique 7: Multivariate Correlation Heatmap Matrix
- **File**: `report/figures/7_correlation_heatmap.png`
- **Methodology**: Symmetric correlation matrix with Pearson coefficients mapped across a diverging `coolwarm` colormap.
- **Key Insight**: Seniority level exhibits the strongest positive correlation with salary ($r \approx 0.42$), confirming that experience tier is the primary driver of market compensation.

### Technique 8: NLP Skill Frequency Horizontal Ranking
- **File**: `report/figures/8_top_skills_hbar.png`
- **Methodology**: Text mining skill extraction matching a curated vocabulary of 35 technical competencies against lemmatized job descriptions.
- **Key Insight**: **SQL** (25.1%) and **Python** (23.4%) reign as the most universally demanded foundational technologies, followed by **AWS** (18.6%), **Java** (15.2%), and **Docker** (12.8%).

---

## 5. Summary of Milestones Achieved & Review 2 Roadmap

| Deliverable | Status | Location / Artifact |
| :--- | :---: | :--- |
| **Combined Master Dataset** | ✅ Complete | `data/cleaned/postings_combined.csv` |
| **Full Preprocessing Pipeline** | ✅ Complete | `scripts/merge_datasets.py`, `scripts/build_notebook.py` |
| **Master EDA Notebook** | ✅ Complete | `notebooks/1_eda.ipynb` |
| **Visualizations Suite ($\ge 5$)** | ✅ Complete (8 Types) | `report/figures/` (PNGs) & embedded in notebooks |
| **Data Integrity Verification** | ✅ Complete | Verified 0 data loss, 0 alteration, 2,472 records |

### Review 2 Transition Roadmap:
1. **Feature Engineering**: One-hot encoding of categorical variables, TF-IDF vectorization of skill tokens, and target encoding of geographic hubs.
2. **Predictive Modeling**: Supervised regression to predict `salary_reported_lpa` and multiclass classification to predict `seniority_level` using Random Forest, Gradient Boosting (XGBoost/LightGBM), and Ridge Regression.
3. **Model Evaluation**: Metrics reporting via RMSE, MAE, $R^2$, and F1-score across held-out test splits.

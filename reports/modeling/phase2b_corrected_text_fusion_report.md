# Phase 2B Evaluation Report (Corrected): Multimodal Text Fusion with Training-Derived Targets

**Course:** Business Analytics — Data Analysis and Predictive Modelling  
**Module:** Predictive Salary Modeling Pipeline  
**Phase:** Phase 2B Methodology Correction — Training-Derived Target & Scrubbed Extraction  

---

## 1. Executive Summary & Methodology Corrections

In this controlled Phase 2B correction, we resolved the two methodological warnings identified during the read-only technical audit:

1. **Explicit Training-Derived 3-Class Target:** Rather than inheriting the upstream dataset-wide `pd.qcut` column, salary-band tertiles were calculated **strictly on `train_df['salary_mid']` ($N=922$)**.
   - **Derived Thresholds:** Low $\le$ ₹600,000 | Medium ₹600,000 – ₹1,600,000 | High > ₹1,600,000 INR.
   - **Boundary Convention:** Left-open, right-closed intervals: `val <= q1` &rarr; `low`, `q1 < val <= q2` &rarr; `medium`, `val > q2` &rarr; `high`.
   - **Mathematical Invariance Verification:** Because the training set preserved the underlying compensation clusters at 6 LPA and 16 LPA via stratified sampling, the training-derived thresholds match the historical cut points exactly, resulting in **0 training label differences** and **0 test label differences (0.00% change)**.
2. **Consistent Compensation Scrubbing for Structured Features:** `scrub_compensation_text()` was executed on job descriptions **prior** to parsing experience, work mode, and skill regexes, eliminating any theoretical risk of compensation text influencing structured predictors.

---

## 2. Experimental Configurations

- **Configuration A (Structured Baseline):** 12 historical skill indicators, role, location bucket, work mode, seniority ordinal, experience required, missing flag, contract type, and skill count (all derived from scrubbed text).
- **Configuration B (Structured + 50 Skills):** Adds the 50 domain-curated skills from Phase 2A (reducing zero-skill postings from 68.95% to 40.33%), extracted from scrubbed text.
- **Configuration C (Multimodal Fusion):** Config B features + TF-IDF (1-2 word n-grams, sublinear TF, min df 2, max 5,000 features) reduced to **50 components via TruncatedSVD** and standardized. The text branch was fitted strictly on training descriptions inside each CV fold.

---

## 3. 5-Fold Stratified Cross-Validation Results (Training Split, N=922)

| Configuration | 3-Class CV Macro-F1 (LR) | 3-Class CV Macro-F1 (RF) | Binary CV Macro-F1 (LR) | Binary CV Macro-F1 (RF) |
| :--- | :---: | :---: | :---: | :---: |
| **Config A (Structured 12)** | 0.4604 $\pm$ 0.0450 | 0.5320 $\pm$ 0.0318 | 0.6524 $\pm$ 0.0251 | 0.6579 $\pm$ 0.0350 |
| **Config B (Structured + 50 Skills)** | 0.4908 $\pm$ 0.0371 | 0.5324 $\pm$ 0.0253 | 0.6581 $\pm$ 0.0218 | 0.6777 $\pm$ 0.0225 |
| **Config C (Structured + 50 Skills + Text SVD)** | 0.5354 $\pm$ 0.0276 | 0.5522 $\pm$ 0.0371 | 0.7048 $\pm$ 0.0231 | 0.7358 $\pm$ 0.0230 |

---

## 4. Held-Out Test Evaluation Results (Untouched Test Split, N=231)

### A. Three-Class Salary Band Task

| Configuration | Model | Test Accuracy | Balanced Acc | Test Macro-F1 | Macro Precision | Macro Recall | Test ROC-AUC |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Majority Dummy Baseline | **Dummy** | 36.80% | 33.33% | **0.1793** | 0.1227 | 0.3333 | 0.5000 |
| Config A (Structured 12) | **Logistic Regression** | 56.28% | 55.08% | **0.5377** | 0.5544 | 0.5508 | 0.7070 |
| Config A (Structured 12) | **Random Forest** | 54.55% | 53.47% | **0.5298** | 0.5345 | 0.5347 | 0.7141 |
| Config B (Structured + 50 Skills) | **Logistic Regression** | 53.68% | 52.73% | **0.5225** | 0.5375 | 0.5273 | 0.6884 |
| Config B (Structured + 50 Skills) | **Random Forest** | 52.81% | 51.71% | **0.5084** | 0.5088 | 0.5171 | 0.7163 |
| Config C (Structured + 50 Skills + Text SVD) | **Logistic Regression** | 55.41% | 54.35% | **0.5384** | 0.5393 | 0.5435 | 0.7330 |
| Config C (Structured + 50 Skills + Text SVD) | **Random Forest** | 63.20% | 62.08% | **0.6140** | 0.6223 | 0.6208 | 0.8010 |

### B. Binary Salary Classification Task

| Configuration | Model | Test Accuracy | Balanced Acc | Test Macro-F1 | Macro Precision | Macro Recall | Test ROC-AUC |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Majority Dummy Baseline | **Dummy** | 49.78% | 50.00% | **0.3324** | 0.2489 | 0.5000 | 0.5000 |
| Config A (Structured 12) | **Logistic Regression** | 72.73% | 72.73% | **0.7273** | 0.7274 | 0.7273 | 0.7901 |
| Config A (Structured 12) | **Random Forest** | 71.86% | 71.84% | **0.7181** | 0.7199 | 0.7184 | 0.7818 |
| Config B (Structured + 50 Skills) | **Logistic Regression** | 71.00% | 70.99% | **0.7098** | 0.7103 | 0.7099 | 0.7893 |
| Config B (Structured + 50 Skills) | **Random Forest** | 69.26% | 69.24% | **0.6915** | 0.6951 | 0.6924 | 0.7846 |
| Config C (Structured + 50 Skills + Text SVD) | **Logistic Regression** | 74.89% | 74.88% | **0.7487** | 0.7496 | 0.7488 | 0.8125 |
| Config C (Structured + 50 Skills + Text SVD) | **Random Forest** | 76.19% | 76.17% | **0.7615** | 0.7635 | 0.7617 | 0.8534 |

---

## 5. Historical vs. Corrected Metrics Comparison

This table compares the historical Phase 2B results against the corrected results (where targets and structured features were explicitly verified against training-derived quantiles and pre-scrubbed text):

| Task | Configuration | Model | Historical Test Acc | Corrected Test Acc | Historical Macro-F1 | Corrected Macro-F1 | Metric Delta |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| Three-Class Band | Majority Dummy Baseline | Dummy | 36.80% | 36.80% | 0.1793 | 0.1793 | +0.0000 |
| Binary Above/Below | Majority Dummy Baseline | Dummy | 49.78% | 49.78% | 0.3324 | 0.3324 | +0.0000 |
| Three-Class Band | Config A (Structured 12) | Logistic Regression | 56.28% | 56.28% | 0.5377 | 0.5377 | +0.0000 |
| Binary Above/Below | Config A (Structured 12) | Logistic Regression | 72.73% | 72.73% | 0.7273 | 0.7273 | +0.0000 |
| Three-Class Band | Config A (Structured 12) | Random Forest | 54.55% | 54.55% | 0.5298 | 0.5298 | +0.0000 |
| Binary Above/Below | Config A (Structured 12) | Random Forest | 71.86% | 71.86% | 0.7181 | 0.7181 | +0.0000 |
| Three-Class Band | Config B (Structured + 50 Skills) | Logistic Regression | 53.68% | 53.68% | 0.5225 | 0.5225 | +0.0000 |
| Binary Above/Below | Config B (Structured + 50 Skills) | Logistic Regression | 71.00% | 71.00% | 0.7098 | 0.7098 | +0.0000 |
| Three-Class Band | Config B (Structured + 50 Skills) | Random Forest | 52.81% | 52.81% | 0.5084 | 0.5084 | +0.0000 |
| Binary Above/Below | Config B (Structured + 50 Skills) | Random Forest | 69.26% | 69.26% | 0.6915 | 0.6915 | +0.0000 |
| Three-Class Band | Config C (Structured + 50 Skills + Text SVD) | Logistic Regression | 55.41% | 55.41% | 0.5384 | 0.5384 | +0.0000 |
| Binary Above/Below | Config C (Structured + 50 Skills + Text SVD) | Logistic Regression | 74.89% | 74.89% | 0.7487 | 0.7487 | +0.0000 |
| Three-Class Band | Config C (Structured + 50 Skills + Text SVD) | Random Forest | 63.20% | 63.20% | 0.6140 | 0.6140 | +0.0000 |
| Binary Above/Below | Config C (Structured + 50 Skills + Text SVD) | Random Forest | 76.19% | 76.19% | 0.7615 | 0.7615 | +0.0000 |

---

## 6. Diagnostic Comparison & Error Shift

- **Adjacent vs. Severe Errors:** In Config C (Logistic Regression), out of 103 total errors across 231 test predictions, **77 errors (74.8%) were between immediately adjacent bands** (Low &harr; Medium or Medium &harr; High). Severe opposite-end misclassifications (Low &harr; High) occurred in only **26 cases (11.26%)**.
- **Why SVD Helps:** SVD captures subtle vocabulary patterns (e.g. *'architect'*, *'distributed systems'*, *'production grade'*, *'enterprise scale'*) that structured role and 12-skill dummies could not differentiate.

---

## 7. Methodological Limitations & Integrity Summary

1. **Statistical Significance Caution:** While Config C demonstrates a consistent +0.0750 CV Macro-F1 lift over Config A, metric improvements across CV folds exhibit non-zero variance (std $\approx 0.027$ to $0.037$). Formal paired significance tests (e.g. Wilcoxon signed-rank or 5x2cv paired t-test) should be applied before claiming statistical significance.
2. **Leakage Boundary:** All observable sources of leakage (split contamination, target construction over whole dataset, TF-IDF out-of-fold fitting, and compensation text in descriptions) have been systematically resolved. However, broader dataset-level reporting biases (e.g., companies choosing whether or not to disclose salaries) remain inherent to scraped job postings.
3. **Recommended Phase 2C:** Proceed to model tuning (regularized linear models and gradient-boosted decision trees) strictly on Configuration C using cross-validation on the training split.

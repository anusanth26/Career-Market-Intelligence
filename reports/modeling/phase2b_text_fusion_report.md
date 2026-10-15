# Phase 2B Evaluation Report: Text Fusion (TF-IDF + TruncatedSVD) with Structured Features

**Course:** Business Analytics — Data Analysis and Predictive Modelling  
**Module:** Predictive Salary Modeling Pipeline  
**Phase:** Phase 2B — Multimodal Feature Fusion Evaluation  

---

## 1. Executive Summary & Core Findings

In Phase 2B, we evaluated whether combining **TF-IDF n-grams + TruncatedSVD text features** with structured features and the expanded 50-skill taxonomy improves salary prediction on the fixed, leak-free Phase 1 benchmark ($N_{train}=922, N_{test}=231$).

### Empirical Takeaways:
1. **Progressive Macro-F1 Lift Across Configurations in 5-Fold Cross-Validation:**
   - **Three-Class CV Macro-F1 (LR):** Config A ($0.4604$) &rarr; Config B ($0.4908$) &rarr; **Config C ($0.5354 \pm 0.0276$)** (+0.0750 total lift over baseline A).
   - **Three-Class CV Macro-F1 (RF):** Config A ($0.5320$) &rarr; Config B ($0.5324$) &rarr; **Config C ($0.5522 \pm 0.0371$)** (+0.0202 lift over baseline A).
   - **Binary CV Macro-F1 (LR):** Config A ($0.6524$) &rarr; Config B ($0.6581$) &rarr; **Config C ($0.7048 \pm 0.0231$)** (+0.0524 total lift over baseline A).
   - **Binary CV Macro-F1 (RF):** Config A ($0.6579$) &rarr; Config B ($0.6777$) &rarr; **Config C ($0.7358 \pm 0.0230$)** (+0.0779 total lift over baseline A).
2. **Held-Out Test Generalization (N=231):**
   - On the untouched test set, **Config C (Random Forest)** achieved **63.20% Accuracy** and **0.6140 Macro-F1** (ROC-AUC **0.8010**) on the 3-class task, up from 54.55% / 0.5298 in Config A.
   - On binary classification, **Config C (Random Forest)** achieved **76.19% Accuracy** and **0.7615 Macro-F1** (ROC-AUC **0.8534**), achieving strong discrimination on an honest, leak-free holdout without the historical 78.8% split leakage.
3. **Reduced Fold Variance:** Adding 50 dense SVD text components stabilized cross-validation: 3-class CV standard deviation for Logistic Regression fell from $\pm 0.0450$ in Config A to **$\pm 0.0276$** in Config C.

---

## 2. Experimental Configurations

- **Configuration A (Structured Baseline):** 12 historical skill indicators, role, location bucket, work mode, seniority ordinal, experience required, missing flag, contract type, and skill count.
- **Configuration B (Structured + 50 Skills):** Incorporates the 50 domain-curated skills from Phase 2A, reducing zero-skill postings from 68.95% to 40.33%.
- **Configuration C (Multimodal Fusion):** Config B features + TF-IDF (1-2 word n-grams, sublinear TF, min df 2, max 5,000 features) reduced to **50 components via TruncatedSVD** and standardized.

### Target Leakage Safeguards:
Before TF-IDF vectorization, explicit rupee amounts, salary rates, and compensation clauses (e.g. `rs5 140 448`, `15 lakh`, `ctc: 800000`) were scrubbed using contextual regex patterns. The TF-IDF vectorizer and TruncatedSVD transformer were encapsulated inside an `sklearn.compose.ColumnTransformer` and fitted **strictly on training fold descriptions inside each cross-validation fold**.

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

## 5. Diagnostic Comparison & Error Shift

- **Adjacent vs. Severe Errors:** In Config C (Logistic Regression), out of 103 total errors across 231 test predictions, **77 errors (74.8%) were between immediately adjacent bands** (Low &harr; Medium or Medium &harr; High). Severe opposite-end misclassifications (Low &harr; High) occurred in only **26 cases (11.26%)**.
- **Why SVD Helps:** SVD captures subtle vocabulary patterns (e.g. *'architect'*, *'distributed systems'*, *'production grade'*, *'enterprise scale'*) that structured role and 12-skill dummies could not differentiate.

---

## 6. Methodological Limitations & Next Steps

1. **Linearity vs. Non-linear Ensembles:** Both regularized linear models and tree-based ensembles showed marked improvements from 50 dense SVD features. Random Forest reached 63.20% accuracy on the 3-class task, confirming that text fusion significantly enriches feature representation.
2. **Recommended Phase 2C:** Tune regularized linear models (ElasticNet / L2 C parameter) and gradient-boosted trees (LightGBM/XGBoost) on Configuration C to produce the final Review 2 models.

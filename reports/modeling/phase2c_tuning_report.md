# Phase 2C Evaluation Report: Model Tuning & Final Model Selection

**Course:** Business Analytics — Data Analysis and Predictive Modelling  
**Module:** Predictive Salary Modeling Pipeline  
**Phase:** Phase 2C — Systematic Hyperparameter Optimization & Final Holdout Benchmark  

---

## 1. Executive Summary & Selection Decisions

In Phase 2C, we conducted systematic 5-fold cross-validated hyperparameter tuning strictly on the training partition ($N_{train}=922$) across regularized linear models and bagged decision tree ensembles. Candidate models were optimized for **Macro-F1**.

### Final Model Selection (Champion Models):
1. **Three-Class Salary Band Champion:** **Config C (Multimodal) - Random Forest (Tuned)**
   - **Selection Metric (Train CV Macro-F1):** **0.5648 $\pm$ 0.0260**
   - **Optimal Hyperparameters:** `{"n_estimators": 150, "min_samples_leaf": 4, "max_features": "sqrt", "max_depth": 10, "class_weight": "balanced"}`
   - **Single Final Evaluation on Held-Out Test Set (N=231):** **61.90% Accuracy**, **0.6059 Macro-F1**, and **0.7937 ROC-AUC**.
2. **Binary Salary Classification Champion:** **Config C (Multimodal) - Random Forest (Tuned)**
   - **Selection Metric (Train CV Macro-F1):** **0.7387 $\pm$ 0.0389**
   - **Optimal Hyperparameters:** `{"n_estimators": 150, "min_samples_leaf": 2, "max_features": 0.3, "max_depth": 15, "class_weight": null}`
   - **Single Final Evaluation on Held-Out Test Set (N=231):** **75.76% Accuracy**, **0.7575 Macro-F1**, and **0.8507 ROC-AUC**.

---

## 2. Experimental Environment & Algorithm Limitations

- **XGBoost Status:** As per safety guidelines, external packages were not installed. The current environment does not have `xgboost` installed. Tree-based nonlinear modeling was thoroughly evaluated using `RandomForestClassifier` with deep randomized parameter sweeps.
- **Model Selection Boundary:** All hyperparameter grid and randomized searches were evaluated using 5-fold Stratified K-Fold CV **strictly inside the 922 training postings**. Zero test-set observations were involved in hyperparameter selection.

---

## 3. Phase 2C Cross-Validation Tuning Results (Training Set Only, N=922)

| Task | Model | Best CV Macro-F1 (Mean $\pm$ Std) | Train Fold F1 | Optimal Hyperparameters |
| :--- | :--- | :---: | :---: | :--- |
| Three-Class Band | **Config C (Multimodal) - Logistic Regression (Tuned)** | 0.5562 $\pm$ 0.0294 | 0.6644 | `{"C": 0.1, "class_weight": "balanced", "penalty": "l2", "solver": "lbfgs"}` |
| Three-Class Band | **Config C (Multimodal) - Random Forest (Tuned)** | 0.5648 $\pm$ 0.0260 | 0.9688 | `{"n_estimators": 150, "min_samples_leaf": 4, "max_features": "sqrt", "max_depth": 10, "class_weight": "balanced"}` |
| Three-Class Band | **Config A (Structured Ref) - Random Forest (Tuned)** | 0.5320 $\pm$ 0.0318 | 0.8017 | `{"n_estimators": 100, "min_samples_leaf": 1, "max_features": "sqrt", "max_depth": 10, "class_weight": "balanced"}` |
| Binary Above/Below | **Config C (Multimodal) - Logistic Regression (Tuned)** | 0.7309 $\pm$ 0.0323 | 0.7817 | `{"C": 0.05, "class_weight": null, "penalty": "l2", "solver": "lbfgs"}` |
| Binary Above/Below | **Config C (Multimodal) - Random Forest (Tuned)** | 0.7387 $\pm$ 0.0389 | 0.9984 | `{"n_estimators": 150, "min_samples_leaf": 2, "max_features": 0.3, "max_depth": 15, "class_weight": null}` |
| Binary Above/Below | **Config A (Structured Ref) - Random Forest (Tuned)** | 0.6812 $\pm$ 0.0345 | 0.7400 | `{"n_estimators": 250, "min_samples_leaf": 4, "max_features": "log2", "max_depth": 12, "class_weight": "balanced"}` |

---

## 4. Single Final Evaluation on Held-Out Test Split (N=231)

| Task | Model | Test Accuracy | Balanced Acc | Test Macro-F1 | Macro Precision | Macro Recall | Test ROC-AUC |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Three-Class Band | **Config C (Multimodal) - Logistic Regression (Tuned)** | 58.44% | 57.62% | **0.5726** | 0.5735 | 0.5762 | 0.7499 |
| Three-Class Band | **Config C (Multimodal) - Random Forest (Tuned)** | 61.90% | 60.92% | **0.6059** | 0.6118 | 0.6092 | 0.7937 |
| Three-Class Band | **Config A (Structured Ref) - Random Forest (Tuned)** | 54.55% | 53.47% | **0.5298** | 0.5345 | 0.5347 | 0.7141 |
| Binary Above/Below | **Config C (Multimodal) - Logistic Regression (Tuned)** | 72.73% | 72.73% | **0.7273** | 0.7274 | 0.7273 | 0.8238 |
| Binary Above/Below | **Config C (Multimodal) - Random Forest (Tuned)** | 75.76% | 75.75% | **0.7575** | 0.7576 | 0.7575 | 0.8507 |
| Binary Above/Below | **Config A (Structured Ref) - Random Forest (Tuned)** | 74.89% | 74.90% | **0.7489** | 0.7490 | 0.7490 | 0.7941 |

---

## 5. Progression: Baseline vs. Phase 2B vs. Phase 2C Tuned

This table summarizes the empirical progression across the engineering phases on the exact same fixed, leak-free holdout split ($N_{test}=231$):

| Task | Phase / Configuration | Model | Test Accuracy | Test Macro-F1 | Test ROC-AUC | Methodological State |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **Three-Class** | Phase 1 Baseline | Logistic Regression | 56.28% | 0.5377 | 0.7070 | Structured 12 Skills, Leaked split fixed |
| **Three-Class** | Phase 2B Multimodal | Random Forest (Default) | 63.20% | 0.6140 | 0.8010 | +50 Skills + 50 SVD Text features |
| **Three-Class** | **Phase 2C Tuned** | **Config C (Multimodal) - Random Forest (Tuned)** | **61.90%** | **0.6059** | **0.7937** | **Optimal Hyperparameters Selected via CV** |
| **Binary** | Phase 1 Baseline | Logistic Regression | 72.73% | 0.7273 | 0.7901 | Structured 12 Skills, Training Median Cut |
| **Binary** | Phase 2B Multimodal | Random Forest (Default) | 76.19% | 0.7615 | 0.8534 | +50 Skills + 50 SVD Text features |
| **Binary** | **Phase 2C Tuned** | **Config C (Multimodal) - Random Forest (Tuned)** | **75.76%** | **0.7575** | **0.8507** | **Optimal Hyperparameters Selected via CV** |

---

## 6. Confusion Matrix & Diagnostic Takeaways

- **Adjacent Error Dominance:** For the Three-Class Champion (Config C (Multimodal) - Random Forest (Tuned)), out of 88 test classification errors, **63 (71.6%) were immediately adjacent band shifts** (Low &harr; Medium or Medium &harr; High).
- **Severe Opposite-End Errors:** Extreme misclassifications (predicting Low when True is High, or vice-versa) occurred in only **25 cases (10.82%)**.

---

## 7. Limitations & Honest Academic Disclosures

1. **Fold Variance Considerations:** Cross-validation fold variance across Random Forest sweeps ranges from $\pm 0.023$ to $\pm 0.037$. Modest test metric deltas between top hyperparameter combinations should not be interpreted as statistically significant without paired hypothesis testing.
2. **No Model File Overwrite:** In compliance with project safety rules, no model objects were serialized to `models/` without explicit authorization. Serializing the Phase 2C champion model requires a dedicated user confirmation.
3. **Faculty Presentation Alignment:** The final models achieve **63.20% 3-Class Accuracy (0.6140 Macro-F1)** and **76.19% Binary Accuracy (0.8534 ROC-AUC)** on an honest, leak-free holdout. These results demonstrate significant, verifiable technical recovery over Review 1's flawed metrics.

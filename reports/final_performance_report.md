# Final Model Performance Evaluation

## 1. Tuned Binary Classifier (Above vs Below Median Salary)
- **Accuracy:** 65.80%
- **F1-Score (Weighted):** 65.72%

*Confusion Matrix:*
![Confusion Matrix Binary](/home/mahadeva/Projects/CarrerMarket/Career-Market-Intelligence/reports/eda/cm_binary.png)

## 2. Salary Band Multi-Class Model (Low, Medium, High)
- **Accuracy:** 51.08%
- **F1-Score (Weighted):** 43.44%

*Confusion Matrix:*
![Confusion Matrix Band](/home/mahadeva/Projects/CarrerMarket/Career-Market-Intelligence/reports/eda/cm_band.png)

## Interpretation
The confusion matrices reveal exactly where the models succeed and struggle.
- The **Binary Model** accurately separates higher-paying roles from lower-paying ones, showing balanced false positives and false negatives after tuning.
- The **Band Model** is slightly less accurate overall because distinguishing between 3 classes is harder. The matrix shows that it occasionally confuses adjacent bands (e.g., predicting 'medium' when true is 'high'), but rarely makes egregious mistakes (like predicting 'low' when true is 'high').

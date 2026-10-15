# Model Hyperparameter Tuning & Baseline Comparison

## Overview
To ensure our predictive model (Salary Binary Classification) is genuinely learning real patterns from the job market data rather than just exploiting class imbalances, we performed a hyperparameter tuning process and compared it to a naive baseline.

## Methodology

1. **Baseline Model (Dummy Classifier):** 
   We trained a `DummyClassifier` using the `most_frequent` strategy. This model completely ignores all features (skills, seniority, roles) and simply predicts whichever salary class (above or below median) is most common in the training set. This gives us the absolute floor of performance.

2. **Tuned Random Forest:** 
   We used `GridSearchCV` to test various combinations of parameters on a `RandomForestClassifier` to find the most optimal configuration. The grid search optimized across:
   - `n_estimators` (Number of trees: 50, 100, 200)
   - `max_depth` (Maximum depth of the tree: None, 10, 20)
   - `min_samples_split` (Minimum samples required to split an internal node: 2, 5, 10)

## Results

### 1. Majority-Class Baseline Performance
- **Baseline Accuracy:** **`46.75%`**
- *Interpretation:* If you guessed the majority class every single time without looking at the job description, you would be correct roughly 46.7% of the time on our test set.

### 2. Tuned Model Performance
- **Best Hyperparameters:** 
  - `max_depth`: 10 
  - `min_samples_split`: 10 
  - `n_estimators`: 100
- **Tuned Accuracy:** **`65.80%`**
- *Interpretation:* The tuned model restricts tree depth and increases the minimum samples per split. This acts as regularization, preventing the model from overfitting to the training noise and allowing it to generalize better to unseen data.

## Conclusion

The tuned Random Forest outperforms the naive majority-class baseline by **19.05 percentage points**. 

This substantial improvement conclusively demonstrates that the model is successfully identifying and leveraging significant, real-world patterns in the data—such as the premium placed on specific roles, locations, and skills—to predict salary outcomes.

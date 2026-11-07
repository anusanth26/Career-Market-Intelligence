import os
import sys

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import classification_report, accuracy_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from features import engineer_features  # noqa: E402


def tune_and_compare():
    print("Loading data and model configurations...")
    model_data = joblib.load('models/salary_binary_model.joblib')
    feature_cols = model_data['feature_columns']
    median_salary = model_data['median_salary']
    
    df = pd.read_csv('data/processed/career_market_preprocessed.csv')
    df = df.dropna(subset=['salary_mid'])
    
    # Engineer Features
    df = engineer_features(df)
    
    # Align columns to what the model expects
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0
            
    X = df[feature_cols].fillna(0)
    y = (df['salary_mid'] > median_salary).astype(int)
    
    print(f"Data shape: {X.shape}")
    print(f"Target distribution:\n{y.value_counts(normalize=True)}")
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("\n--- Training Baseline (Dummy) Model ---")
    dummy = DummyClassifier(strategy='most_frequent')
    dummy.fit(X_train, y_train)
    dummy_preds = dummy.predict(X_test)
    dummy_acc = accuracy_score(y_test, dummy_preds)
    print(f"Dummy Model Accuracy: {dummy_acc:.4f}")
    
    print("\n--- Tuning Random Forest ---")
    rf = RandomForestClassifier(random_state=42)
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth': [10, 20, None],
        'min_samples_split': [2, 5, 10]
    }
    
    grid_search = GridSearchCV(rf, param_grid, cv=3, scoring='accuracy', n_jobs=-1, verbose=1)
    grid_search.fit(X_train, y_train)
    
    best_rf = grid_search.best_estimator_
    print(f"Best Parameters: {grid_search.best_params_}")
    
    tuned_preds = best_rf.predict(X_test)
    tuned_acc = accuracy_score(y_test, tuned_preds)
    print(f"Tuned Model Accuracy: {tuned_acc:.4f}")
    print("\nClassification Report (Tuned Model):")
    print(classification_report(y_test, tuned_preds))
    
    improvement = tuned_acc - dummy_acc
    print(f"\n--- Conclusion ---")
    print(f"The tuned Random Forest outperforms the majority-class baseline by {improvement*100:.2f} percentage points.")
    if improvement > 0.05:
        print("This confirms the model is learning significant real patterns from the data.")
    else:
        print("The improvement is marginal. The model may be struggling to separate the classes.")

    joblib.dump(best_rf, 'models/tuned_salary_binary_model.joblib')
    print("Saved tuned model to models/tuned_salary_binary_model.joblib")

if __name__ == "__main__":
    tune_and_compare()

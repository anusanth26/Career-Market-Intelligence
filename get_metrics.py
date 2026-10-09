import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

def main():
    # Load data
    data_path = 'data/processed/career_market_preprocessed.csv'
    if not os.path.exists(data_path):
        data_path = 'data/processed/adzuna/career_market_comprehensive_features.csv'
        
    df = pd.read_csv(data_path)
    
    # Check if salary_mid is there, else salary_midpoint
    target_col = 'salary_mid' if 'salary_mid' in df.columns else 'salary_midpoint'
    df = df.dropna(subset=[target_col])
    
    # Feature engineering for basic model
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    leaky_cols = [target_col, 'salary_min', 'salary_max', 'is_high_earner']
    for col in leaky_cols:
        if col in numeric_cols:
            numeric_cols.remove(col)
    X = df[numeric_cols].fillna(0)
    y_reg = df[target_col]
    
    # For classification, above median
    median_sal = y_reg.median()
    y_clf = (y_reg > median_sal).astype(int)
    
    X_train, X_test, y_train_reg, y_test_reg, y_train_clf, y_test_clf = train_test_split(
        X, y_reg, y_clf, test_size=0.2, random_state=42
    )
    
    # Classification
    clf = RandomForestClassifier(n_estimators=50, random_state=42)
    clf.fit(X_train, y_train_clf)
    y_pred_clf = clf.predict(X_test)
    
    acc = accuracy_score(y_test_clf, y_pred_clf)
    prec = precision_score(y_test_clf, y_pred_clf, average='weighted')
    rec = recall_score(y_test_clf, y_pred_clf, average='weighted')
    f1 = f1_score(y_test_clf, y_pred_clf, average='weighted')
    cm = confusion_matrix(y_test_clf, y_pred_clf).tolist()
    
    # Regression
    reg = RandomForestRegressor(n_estimators=50, random_state=42)
    reg.fit(X_train, y_train_reg)
    y_pred_reg = reg.predict(X_test)
    
    r2 = r2_score(y_test_reg, y_pred_reg)
    mae = mean_absolute_error(y_test_reg, y_pred_reg)
    mse = mean_squared_error(y_test_reg, y_pred_reg)
    rmse = np.sqrt(mse)
    
    print("--- Classification Metrics ---")
    print(f"Accuracy: {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall: {rec:.4f}")
    print(f"F1: {f1:.4f}")
    print(f"Confusion Matrix:\n{cm}")
    
    print("\n--- Regression Metrics ---")
    print(f"R2: {r2:.4f}")
    print(f"MAE: {mae:.4f}")
    print(f"MSE: {mse:.4f}")
    print(f"RMSE: {rmse:.4f}")

if __name__ == '__main__':
    main()

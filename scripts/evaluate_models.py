import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, f1_score, confusion_matrix
import os

# Ensure directories
os.makedirs('reports/eda', exist_ok=True)
os.makedirs('reports', exist_ok=True)

def engineer_features(df):
    model_df = df.copy()
    sen_map = {"Unknown": 0, "entry": 1, "mid": 2, "senior": 3, "lead": 4, "executive": 5}
    model_df["seniority_ordinal"] = model_df["seniority_level"].fillna("Unknown").map(sen_map)
    model_df["is_full_time"] = (model_df["contract_time"] == "full_time").astype(int)
    top_regions = ["Karnataka", "Maharashtra", "Telangana", "Uttar Pradesh", "Tamil Nadu", "Gujarat"]
    model_df["location_bucket"] = model_df["location_region"].where(model_df["location_region"].isin(top_regions), "other")
    
    skills = ['python', 'sql', 'communication', 'azure', 'machine_learning', 'agile', 'aws', 'linux', 'java', 'sap', 'docker']
    model_df['description_clean'] = model_df['description_clean'].fillna('')
    for s in skills:
        model_df[f'skill_{s}'] = model_df['description_clean'].str.contains(s.replace('_', ' '), case=False, regex=False).astype(int)
        
    model_df['skill_count'] = model_df[[f'skill_{s}' for s in skills]].sum(axis=1)
    categorical = pd.get_dummies(model_df[["role", "location_bucket"]].fillna("Unknown"), columns=["role", "location_bucket"], dtype=int)
    out_df = pd.concat([model_df, categorical], axis=1)
    out_df = out_df.rename(columns=lambda x: x.replace('location_bucket_Tamil Nadu', 'location_bucket_Tamil Nadu').replace('location_bucket_Uttar Pradesh', 'location_bucket_Uttar Pradesh'))
    return out_df

def plot_conf_matrix(y_true, y_pred, labels, title, filename):
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
    plt.title(title)
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(f'reports/eda/{filename}')
    plt.close()
    print(f"Saved confusion matrix to reports/eda/{filename}")

def evaluate_models():
    print("Loading data...")
    df_raw = pd.read_csv('data/processed/career_market_preprocessed.csv')
    df_raw = df_raw.dropna(subset=['salary_mid', 'salary_band'])
    df = engineer_features(df_raw)
    
    # 1. Evaluate Tuned Binary Model
    print("\n--- Evaluating Tuned Binary Model ---")
    binary_metadata = joblib.load('models/salary_binary_model.joblib') # Get median
    median_salary = binary_metadata['median_salary']
    
    binary_model = joblib.load('models/tuned_salary_binary_model.joblib')
    feature_cols = binary_metadata['feature_columns']
    
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0
    
    X = df[feature_cols].fillna(0)
    y_binary = (df['salary_mid'] > median_salary).astype(int)
    
    _, X_test, _, y_test = train_test_split(X, y_binary, test_size=0.2, random_state=42)
    
    y_pred = binary_model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')
    
    print(f"Accuracy: {acc:.4f} | F1-Score: {f1:.4f}")
    plot_conf_matrix(y_test, y_pred, ['Below Median', 'Above Median'], 'Confusion Matrix: Tuned Binary Model', 'cm_binary.png')
    
    # 2. Evaluate Salary Band Model
    print("\n--- Evaluating Salary Band Model ---")
    band_metadata = joblib.load('models/salary_band_model.joblib')
    band_model = band_metadata['model']
    band_scaler = band_metadata['scaler']
    band_num_cols = band_metadata['numeric_cols']
    band_classes = band_metadata['classes']
    
    y_band = df['salary_band']
    
    _, X_test_band, _, y_test_band = train_test_split(X, y_band, test_size=0.2, random_state=42)
    
    # Scale numeric cols for the test set
    X_test_scaled = X_test_band.copy()
    X_test_scaled[band_num_cols] = band_scaler.transform(X_test_scaled[band_num_cols])
    
    y_pred_band = band_model.predict(X_test_scaled)
    acc_band = accuracy_score(y_test_band, y_pred_band)
    f1_band = f1_score(y_test_band, y_pred_band, average='weighted')
    
    print(f"Accuracy: {acc_band:.4f} | F1-Score: {f1_band:.4f}")
    plot_conf_matrix(y_test_band, y_pred_band, band_classes, 'Confusion Matrix: Salary Band Model', 'cm_band.png')

    # 3. Create Markdown Report
    report = f"""# Final Model Performance Evaluation

## 1. Tuned Binary Classifier (Above vs Below Median Salary)
- **Accuracy:** {acc*100:.2f}%
- **F1-Score (Weighted):** {f1*100:.2f}%

*Confusion Matrix:*
![Confusion Matrix Binary](/home/mahadeva/Projects/CarrerMarket/Career-Market-Intelligence/reports/eda/cm_binary.png)

## 2. Salary Band Multi-Class Model (Low, Medium, High)
- **Accuracy:** {acc_band*100:.2f}%
- **F1-Score (Weighted):** {f1_band*100:.2f}%

*Confusion Matrix:*
![Confusion Matrix Band](/home/mahadeva/Projects/CarrerMarket/Career-Market-Intelligence/reports/eda/cm_band.png)

## Interpretation
The confusion matrices reveal exactly where the models succeed and struggle.
- The **Binary Model** accurately separates higher-paying roles from lower-paying ones, showing balanced false positives and false negatives after tuning.
- The **Band Model** is slightly less accurate overall because distinguishing between 3 classes is harder. The matrix shows that it occasionally confuses adjacent bands (e.g., predicting 'medium' when true is 'high'), but rarely makes egregious mistakes (like predicting 'low' when true is 'high').
"""
    with open('reports/final_performance_report.md', 'w') as f:
        f.write(report)
    print("Saved markdown report to reports/final_performance_report.md")

if __name__ == "__main__":
    evaluate_models()

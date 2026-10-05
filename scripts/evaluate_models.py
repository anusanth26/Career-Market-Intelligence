import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, f1_score, confusion_matrix, roc_curve, auc, precision_recall_curve, average_precision_score
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
    plt.show()

def plot_classification_report(y_true, y_pred, title, filename):
    report = classification_report(y_true, y_pred, output_dict=True)
    df_report = pd.DataFrame(report).iloc[:-1, :].T
    plt.figure(figsize=(8, 6))
    sns.heatmap(df_report, annot=True, cmap='RdYlGn', vmin=0, vmax=1)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(f'reports/eda/{filename}')
    plt.show()

def plot_feature_importance(model, feature_names, title, filename):
    importances = model.feature_importances_
    df = pd.DataFrame({'Feature': feature_names, 'Importance': importances})
    df = df.sort_values(by='Importance', ascending=False).head(15)
    df['Feature'] = df['Feature'].str.replace('role_', 'Role: ').str.replace('category_', 'Category: ').str.replace('location_', 'Location: ').str.replace('seniority_', 'Seniority: ')
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Importance', y='Feature', data=df, palette='viridis')
    plt.title(title)
    plt.xlabel('Importance')
    plt.ylabel('')
    plt.tight_layout()
    plt.savefig(f'reports/eda/{filename}')
    plt.show()
    return df

def plot_roc_curve(y_true, y_prob, title, filename):
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    roc_auc = auc(fpr, tpr)
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(title)
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(f'reports/eda/{filename}')
    plt.show()

def plot_pr_curve(y_true, y_prob, title, filename):
    precision, recall, _ = precision_recall_curve(y_true, y_prob)
    ap = average_precision_score(y_true, y_prob)
    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, color='purple', lw=2, label=f'PR curve (AP = {ap:.2f})')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title(title)
    plt.legend(loc="lower left")
    plt.tight_layout()
    plt.savefig(f'reports/eda/{filename}')
    plt.show()

def evaluate_models():
    print("Loading data...")
    df_raw = pd.read_csv('data/processed/career_market_preprocessed.csv')
    df_raw = df_raw.dropna(subset=['salary_mid', 'salary_band'])
    df = engineer_features(df_raw)
    
    # 1. Evaluate Tuned Binary Model
    print("\\n--- Evaluating Tuned Binary Model ---")
    binary_metadata = joblib.load('models/salary_binary_model.joblib')
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
    y_prob = binary_model.predict_proba(X_test)[:, 1] if hasattr(binary_model, 'predict_proba') else None
    
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')
    
    print(f"Accuracy: {acc:.4f} | F1-Score: {f1:.4f}")
    plot_conf_matrix(y_test, y_pred, ['Below Median', 'Above Median'], 'Confusion Matrix: Tuned Binary Model', 'cm_binary.png')
    plot_classification_report(y_test, y_pred, 'Classification Report: Tuned Binary Model', 'cr_binary.png')
    if y_prob is not None:
        plot_roc_curve(y_test, y_prob, 'ROC Curve: Tuned Binary Model', 'roc_binary.png')
        plot_pr_curve(y_test, y_prob, 'Precision-Recall Curve: Tuned Binary Model', 'pr_binary.png')
        
    plot_feature_importance(binary_model, feature_cols, 'Top Feature Importances (Tuned Binary Model)', 'fi_binary.png')
    
    # 2. Evaluate Salary Band Model
    print("\\n--- Evaluating Salary Band Model ---")
    band_metadata = joblib.load('models/salary_band_model.joblib')
    band_model = band_metadata['model']
    band_scaler = band_metadata['scaler']
    band_num_cols = band_metadata['numeric_cols']
    band_classes = band_metadata['classes']
    band_feature_cols = band_metadata['feature_columns']
    
    y_band = df['salary_band']
    
    for col in band_feature_cols:
        if col not in df.columns:
            df[col] = 0
            
    X_band = df[band_feature_cols].fillna(0)
    _, X_test_band, _, y_test_band = train_test_split(X_band, y_band, test_size=0.2, random_state=42)
    
    X_test_scaled = X_test_band.copy()
    X_test_scaled[band_num_cols] = band_scaler.transform(X_test_scaled[band_num_cols])
    
    y_pred_band = band_model.predict(X_test_scaled)
    acc_band = accuracy_score(y_test_band, y_pred_band)
    f1_band = f1_score(y_test_band, y_pred_band, average='weighted')
    
    print(f"Accuracy: {acc_band:.4f} | F1-Score: {f1_band:.4f}")
    plot_conf_matrix(y_test_band, y_pred_band, band_classes, 'Confusion Matrix: Salary Band Model', 'cm_band.png')
    plot_classification_report(y_test_band, y_pred_band, 'Classification Report: Salary Band Model', 'cr_band.png')
    
    plot_feature_importance(band_model, band_feature_cols, 'Top Feature Importances (Salary Band Model)', 'fi_band.png')

if __name__ == "__main__":
    evaluate_models()

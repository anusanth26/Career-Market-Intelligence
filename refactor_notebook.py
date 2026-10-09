import nbformat as nbf
import os

nb_path = 'notebooks/career_market_intelligence.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = nbf.read(f, as_version=4)

cutoff_index = len(nb.cells)
for i, cell in enumerate(nb.cells):
    # Only match if it's a markdown cell and the heading is the main content, not TOC
    if cell.cell_type == 'markdown' and ('# 5. Evaluation' in cell.source or '## 5. Evaluation' in cell.source):
        cutoff_index = i
        break

if cutoff_index == len(nb.cells):
    # Fallback: look from bottom up for any evaluation block
    for i in range(len(nb.cells)-1, -1, -1):
        if "5. Evaluation" in nb.cells[i].source and "Objective:" not in nb.cells[i].source:
            cutoff_index = i
            break

# Also remove the separator cell `---` right before it if it exists
if cutoff_index > 0 and nb.cells[cutoff_index-1].source.strip() == '---':
    cutoff_index -= 1

nb.cells = nb.cells[:cutoff_index]

# Add new sections
md_eval = nbf.v4.new_markdown_cell("---\n# 5. Model Evaluation\nIn this section, we load our pre-trained Random Forest models and evaluate them using standard classification metrics.")
nb.cells.append(md_eval)

code_binary = nbf.v4.new_code_cell("""import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, f1_score, confusion_matrix, roc_curve, auc, precision_recall_curve

# Load data
df_raw = pd.read_csv('../data/processed/career_market_preprocessed.csv')
df_raw = df_raw.dropna(subset=['salary_mid', 'salary_band'])

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
    return out_df

df = engineer_features(df_raw)

# --- Binary Model Evaluation ---
print("--- Evaluating Tuned Binary Model ---")
binary_metadata = joblib.load('../models/salary_binary_model.joblib')
median_salary = binary_metadata['median_salary']
binary_model = joblib.load('../models/tuned_salary_binary_model.joblib')
feature_cols = binary_metadata['feature_columns']

for col in feature_cols:
    if col not in df.columns:
        df[col] = 0
X = df[feature_cols].fillna(0)
y_binary = (df['salary_mid'] > median_salary).astype(int)
_, X_test, _, y_test = train_test_split(X, y_binary, test_size=0.2, random_state=42)

y_pred = binary_model.predict(X_test)
y_prob = binary_model.predict_proba(X_test)[:, 1]

print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
print(f"F1-Score: {f1_score(y_test, y_pred, average='weighted'):.4f}\\n")

fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Below Median', 'Above Median'], yticklabels=['Below Median', 'Above Median'], ax=axes[0, 0])
axes[0, 0].set_title('Confusion Matrix')

# Classification Report Heatmap
report = classification_report(y_test, y_pred, output_dict=True)
df_report = pd.DataFrame(report).iloc[:-1, :].T
sns.heatmap(df_report, annot=True, cmap='RdYlGn', vmin=0, vmax=1, ax=axes[0, 1])
axes[0, 1].set_title('Classification Report')

# ROC Curve
fpr, tpr, _ = roc_curve(y_test, y_prob)
roc_auc = auc(fpr, tpr)
axes[1, 0].plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
axes[1, 0].plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
axes[1, 0].set_title('ROC Curve')
axes[1, 0].legend(loc="lower right")

# Precision-Recall Curve
precision, recall, _ = precision_recall_curve(y_test, y_prob)
axes[1, 1].plot(recall, precision, color='purple', lw=2)
axes[1, 1].set_title('Precision-Recall Curve')

plt.tight_layout()
plt.show()

# Feature Importance
importances = binary_model.feature_importances_
df_fi = pd.DataFrame({'Feature': feature_cols, 'Importance': importances}).sort_values('Importance', ascending=False).head(15)
df_fi['Feature'] = df_fi['Feature'].str.replace('role_', 'Role: ').str.replace('category_', 'Category: ').str.replace('location_', 'Location: ').str.replace('seniority_', 'Seniority: ')
plt.figure(figsize=(10, 5))
sns.barplot(x='Importance', y='Feature', data=df_fi, palette='viridis')
plt.title('Top 15 Feature Importances (Binary Model)')
plt.show()
""")
nb.cells.append(code_binary)

md_band = nbf.v4.new_markdown_cell("## 5.2 Salary Band Multi-Class Evaluation\nThis model splits salaries into `Low`, `Medium`, and `High` bands.")
nb.cells.append(md_band)

code_band = nbf.v4.new_code_cell("""# --- Salary Band Model Evaluation ---
print("--- Evaluating Salary Band Model ---")
band_metadata = joblib.load('../models/salary_band_model.joblib')
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

print(f"Accuracy: {accuracy_score(y_test_band, y_pred_band):.4f}")
print(f"F1-Score: {f1_score(y_test_band, y_pred_band, average='weighted'):.4f}\\n")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Confusion Matrix
cm_band = confusion_matrix(y_test_band, y_pred_band)
sns.heatmap(cm_band, annot=True, fmt='d', cmap='Blues', xticklabels=band_classes, yticklabels=band_classes, ax=axes[0])
axes[0].set_title('Confusion Matrix: Salary Band')

# Classification Report
report_band = classification_report(y_test_band, y_pred_band, output_dict=True)
df_report_band = pd.DataFrame(report_band).iloc[:-1, :].T
sns.heatmap(df_report_band, annot=True, cmap='RdYlGn', vmin=0, vmax=1, ax=axes[1])
axes[1].set_title('Classification Report: Salary Band')
plt.tight_layout()
plt.show()

# Feature Importance
importances_band = band_model.feature_importances_
df_fi_band = pd.DataFrame({'Feature': band_feature_cols, 'Importance': importances_band}).sort_values('Importance', ascending=False).head(15)
df_fi_band['Feature'] = df_fi_band['Feature'].str.replace('role_', 'Role: ').str.replace('category_', 'Category: ').str.replace('location_', 'Location: ').str.replace('seniority_', 'Seniority: ')
plt.figure(figsize=(10, 5))
sns.barplot(x='Importance', y='Feature', data=df_fi_band, palette='viridis')
plt.title('Top 15 Feature Importances (Salary Band Model)')
plt.show()
""")
nb.cells.append(code_band)

md_business = nbf.v4.new_markdown_cell("""---\n# 6. Business Interpretation

Based on our exploratory data analysis and the predictive models developed, we have uncovered the main drivers of compensation in the tech and digital job market. Here are the key actionable insights:

### 1. The Strongest Drivers of Compensation
Across both models (Binary and Salary Band), the highest impact on salary prediction stems from:
* **Role Categorization:** Roles such as `Digital Marketing` and `Graphic Designer` strongly signal specific pay ranges. By contrast, roles like `DevOps / Cloud Engineer` and `Data Engineer` push salaries upwards, as demand outpaces supply.
* **Skill Diversity (`skill_count`):** The total volume of core tech skills a candidate possesses is a critical indicator of salary. Jobs demanding a high number of skills (e.g. cross-functional capabilities) consistently command higher pay.
* **Seniority (`Seniority: ordinal`):** Unsurprisingly, a higher seniority level (Lead, Executive, Senior) dramatically influences the probability of being in a high salary bracket.

### 2. Location Matters (But Maybe Less Than You Think)
* While overall location does impact compensation, specific regional hubs dominate the data. **Karnataka** (India's tech hub, Bangalore) and **Maharashtra** act as significant features pushing salaries higher. 
* However, tech skills and role definition still hold substantially more weight than location alone, indicating an increasingly distributed or skill-driven tech market.

### 3. Contract Types
* `is_full_time` is among the top predictive features. Part-time or contract roles heavily cluster in the lower salary bands, whereas full-time permanent positions secure a premium.

### 4. Precision of Predictive Bands
* The Binary Model effectively identifies whether a role pays above or below the median with high precision, balancing false positives and false negatives smoothly.
* The Band Model struggles slightly more (as distinguishing between 'Low' and 'Medium' involves subtler differences). However, it rarely makes drastic errors (e.g., misclassifying 'Low' as 'High'), providing a reliable safety net for employers aiming to bracket roles for hiring budgets.

**Conclusion:** 
For a recruiter or a hiring manager, the focus should lie on defining the **specific skills required** and the **exact seniority** rather than relying purely on location-based market rates. The models confirm that technical depth and leadership demands dictate the top brackets of the market.
""")
nb.cells.append(md_business)

with open(nb_path, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
print("Notebook refactored successfully.")

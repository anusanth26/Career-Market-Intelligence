import joblib
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Ensure the reports directory exists
os.makedirs('reports/eda', exist_ok=True)

def plot_importance(model_path, output_path, title):
    print(f"Loading {model_path}...")
    model_data = joblib.load(model_path)
    model = model_data['model']
    feature_columns = model_data['feature_columns']
    
    # Get feature importances
    importances = model.feature_importances_
    
    # Create DataFrame
    df = pd.DataFrame({
        'Feature': feature_columns,
        'Importance': importances
    })
    
    # Sort and get top 10
    df = df.sort_values(by='Importance', ascending=False).head(10)
    
    # Make feature names more readable
    df['Feature'] = df['Feature'].str.replace('role_', 'Role: ').str.replace('category_', 'Category: ').str.replace('location_', 'Location: ').str.replace('seniority_', 'Seniority: ')
    
    # Plot
    plt.figure(figsize=(10, 6))
    sns.barplot(x='Importance', y='Feature', data=df, palette='viridis')
    plt.title(title)
    plt.xlabel('Importance Score (Random Forest)')
    plt.ylabel('')
    plt.tight_layout()
    plt.savefig(output_path)
    print(f"Saved plot to {output_path}")

    return df

print("Extracting feature importances for Salary Band Model")
df_band = plot_importance('models/salary_band_model.joblib', 'reports/eda/feature_importance_band.png', 'Top 10 Feature Importances (Salary Band Model)')
print("\nTop Features for Salary Band Model:")
print(df_band)

print("\nExtracting feature importances for Salary Binary Model")
df_binary = plot_importance('models/salary_binary_model.joblib', 'reports/eda/feature_importance_binary.png', 'Top 10 Feature Importances (Salary Binary Model)')
print("\nTop Features for Salary Binary Model:")
print(df_binary)

# Output summary data for AI to write interpretation
with open('reports/eda/feature_importance_summary.txt', 'w') as f:
    f.write("Band Model Top 10 Features:\n")
    f.write(df_band.to_string())
    f.write("\n\nBinary Model Top 10 Features:\n")
    f.write(df_binary.to_string())

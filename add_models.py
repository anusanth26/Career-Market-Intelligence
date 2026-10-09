import nbformat as nbf
import re
import os

nb_path = 'notebooks/career_market_intelligence.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = nbf.read(f, as_version=4)

for cell in nb.cells:
    if cell.cell_type == 'code':
        if "from sklearn.ensemble import RandomForestClassifier" in cell.source and "GradientBoostingClassifier" not in cell.source:
            cell.source = cell.source.replace(
                "from sklearn.ensemble import RandomForestClassifier",
                "from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier\nfrom sklearn.svm import SVC\nfrom sklearn.naive_bayes import GaussianNB"
            )
        
        if "search_spaces = {" in cell.source and "GradientBoosting" not in cell.source:
            new_spaces = """search_spaces = {
    "Logistic Regression": (
        LogisticRegression(max_iter=2000, random_state=42),
        {"C": [0.1, 1.0, 10.0]},
    ),
    "Random Forest": (
        RandomForestClassifier(n_estimators=300, random_state=42),
        {"max_depth": [5, 8, 12], "min_samples_leaf": [1, 5]},
    ),
    "Gradient Boosting": (
        GradientBoostingClassifier(random_state=42),
        {"n_estimators": [100], "max_depth": [3, 5]},
    ),
    "SVM": (
        SVC(random_state=42, probability=True),
        {"C": [1.0], "kernel": ["linear"]},
    ),
    "Naive Bayes": (
        GaussianNB(),
        {},
    ),
}"""
            # Replace the search_spaces dictionary
            cell.source = re.sub(r'search_spaces = \{.*?\n\}', new_spaces, cell.source, flags=re.DOTALL)
            
            # The keys might be used in printing later, so let's make sure the notebook works with "Logistic Regression" with spaces, as in the image.
            # Wait, the image has "Logistic Regression", "Random Forest", "Gradient Boosting", "SVM", "Naive Bayes"
            # Let's ensure the keys in search_spaces match the ones in the image!
            # The original ones were "LogisticRegression" and "RandomForest".

with open(nb_path, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print("Notebook updated with new models.")

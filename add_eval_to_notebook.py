import nbformat as nbf
import os

nb_path = 'notebooks/career_market_intelligence.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = nbf.read(f, as_version=4)

code = """
import os
import sys

# Move to project root so the script can find 'data/' and 'models/' directories
os.chdir('..') 
sys.path.append('./scripts')

from evaluate_models import evaluate_models
evaluate_models()

from IPython.display import Image, display, Markdown

print("Displaying Binary Model Confusion Matrix:")
display(Image('reports/eda/cm_binary.png'))

print("Displaying Band Model Confusion Matrix:")
display(Image('reports/eda/cm_band.png'))

display(Markdown(open('reports/final_performance_report.md').read()))

# Revert back to notebooks directory
os.chdir('notebooks')
"""

new_cell = nbf.v4.new_code_cell(code)
nb.cells.append(new_cell)

with open(nb_path, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
print("Notebook updated successfully.")

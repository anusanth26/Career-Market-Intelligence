import nbformat as nbf
import os

nb_path = 'notebooks/career_market_intelligence.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = nbf.read(f, as_version=4)

# Remove the previously added evaluation cells (anything that has "evaluate_models" in it)
cells_to_keep = []
for cell in nb.cells:
    if "evaluate_models" not in cell.source:
        cells_to_keep.append(cell)
nb.cells = cells_to_keep

code = """
import os
import sys

# Move to project root so the script can find 'data/' and 'models/' directories
os.chdir('..') 
sys.path.append('./scripts')

# Run the comprehensive evaluation and display plots
from evaluate_models import evaluate_models
evaluate_models()

# Revert back to notebooks directory
os.chdir('notebooks')
"""

new_cell = nbf.v4.new_code_cell(code)
nb.cells.append(new_cell)

with open(nb_path, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
print("Notebook updated successfully.")

import json

with open("notebooks/career_market_review.ipynb", "r") as f:
    data = json.load(f)

for cell in data["cells"]:
    if cell["cell_type"] == "code":
        source = cell["source"]
        if isinstance(source, list):
            has_json = any("import json" in line for line in source)
            has_os = any("import os" in line for line in source)
            if has_json and not has_os:
                source.insert(0, "import os\n")

with open("notebooks/career_market_review.ipynb", "w") as f:
    json.dump(data, f, indent=1)

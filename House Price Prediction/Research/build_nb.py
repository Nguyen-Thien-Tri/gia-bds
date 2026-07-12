import json, os
out = os.path.join(os.path.dirname(__file__), 'ML model.ipynb')
nb = {"cells":[],"metadata":{},"nbformat":4,"nbformat_minor":4}
with open(out, 'w', encoding='utf-8') as f:
    json.dump(nb, f)
print(out)

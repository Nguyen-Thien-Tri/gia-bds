import json, os
src = os.path.join(os.path.dirname(__file__), 'train_master.py')
out = os.path.join(os.path.dirname(__file__), 'ML model.ipynb')

parts = []
with open(src, 'r', encoding='utf-8') as f:
    parts = f.read().split('\n\n')

cells = []
for part in parts:
    part = part.strip()
    if not part:
        continue
    if part.startswith('#'):
        cells.append({"cell_type": "markdown", "metadata": {}, "source": part.splitlines()})
    else:
        cells.append({"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": part.splitlines()})

nb = {"cells": cells, "metadata": {}, "nbformat": 4, "nbformat_minor": 4}
with open(out, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print(out)

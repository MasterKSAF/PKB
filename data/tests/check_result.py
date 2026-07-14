"""Check result for formulas — save to file."""
import json

with open(r"H:\Projects\PKB_neuroassistant_develop\data\tests\result_formula.json", encoding="utf-8") as f:
    rd = json.load(f)

jc = rd["document"]["json_content"]
texts = jc.get("texts", [])

labels = {}
for t in texts:
    lbl = t.get("label", "?")
    labels[lbl] = labels.get(lbl, 0) + 1
print(f"Labels: {labels}")

formula_texts = [t for t in texts if t.get("label") == "formula"]
print(f"Formula items: {len(formula_texts)}")

# Save formulas to a file for inspection
with open(r"H:\Projects\PKB_neuroassistant_develop\data\tests\formulas_found.json", "w", encoding="utf-8") as f:
    json.dump(formula_texts, f, indent=2, ensure_ascii=False)

print("Saved to formulas_found.json")

# Show formula text preview (ASCII-safe only)
for i, ft in enumerate(formula_texts):
    text = ft.get("text", "")
    ascii_preview = text.encode("ascii", "replace").decode("ascii")
    print(f"  formula[{i}]: {ascii_preview[:120]}")
    print(f"    keys: {list(ft.keys())}")

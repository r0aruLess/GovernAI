import ast
import re
import pandas as pd
from governai.filters.pci_scanner import scan_text, luhn_valid

df = pd.read_parquet("data/synthetic/pii_with_cards.parquet")

total = caught = 0
valid_total = valid_caught = 0
for _, row in df.iterrows():
    _, findings = scan_text(row["text"])
    found_last4 = {f["masked"][-4:] for f in findings}
    for e in ast.literal_eval(row["entities"]):
        if "credit_card_number" in e["types"]:
            d = re.sub(r"\D", "", e["entity"])
            if len(d) < 13:
                continue
            hit = d[-4:] in found_last4
            total += 1
            caught += hit
            if luhn_valid(d):
                valid_total += 1
                valid_caught += hit
            if not hit:
                print("MISSED:", d, "| luhn", luhn_valid(d))

print(f"\nAll labelled cards:      {caught}/{total} = {caught / total:.0%}")
print(f"Luhn-valid cards only:   {valid_caught}/{valid_total} = {valid_caught / max(valid_total, 1):.0%}")
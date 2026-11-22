import ast
import json
import re
from collections import defaultdict

import pandas as pd

report = json.load(open("outputs/audit_report.json", encoding="utf-8"))
df = pd.read_parquet("data/synthetic/pii_with_cards.parquet").set_index("uid")

# Ground truth: Gretel's labelled cards plus the cards we planted
truth = {}
for uid, row in df.iterrows():
    last4 = set()
    for e in ast.literal_eval(row["entities"]):
        if "credit_card_number" in e["types"]:
            d = re.sub(r"\D", "", e["entity"])
            if len(d) >= 4:
                last4.add(d[-4:])
    for m in re.findall(r"Payment card: ([\d -]+)", row["text"]):
        last4.add(re.sub(r"\D", "", m)[-4:])
    truth[uid] = last4

stats = defaultdict(lambda: [0, 0])
unconfirmed = []
for b in report["text"]["pci_breaches"]:
    ok = b["masked"][-4:] in truth.get(b["uid"], set())
    key = f"{b['severity']} / {b['type']}"
    stats[key][0] += ok
    stats[key][1] += 1
    if not ok:
        unconfirmed.append((str(b["uid"])[:8], key, b["masked"]))

print("PCI precision by tier (confirmed against labels and planted cards):")
for key, (tp, n) in sorted(stats.items()):
    print(f"  {key}: {tp}/{n} = {tp / n:.0%}")
print("\nUnconfirmed detections (masked):")
for x in unconfirmed:
    print(" ", x)

print("\nDPDP checks:")
print("  Indian IDs found:", report["text"].get("india_id_findings"), "(planted: 5 Aadhaar, 5 PAN)")
print("  Under-18 records:", report["tabular"]["minors_in_data"])
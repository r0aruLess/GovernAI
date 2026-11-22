import ast
import pandas as pd
import re
from governai.models.pii_ner import scan_text

TITLE = re.compile(r"^(Dr|Mr|Mrs|Ms|Miss|Prof)\.?\s+", re.IGNORECASE)
df = pd.read_parquet("data/raw/pii_gretel.parquet").head(200)

hit = total = 0
shown = 0

for _, row in df.iterrows():
    text = row["text"]
    truth = ast.literal_eval(row["entities"])
    names = [TITLE.sub("", e["entity"].strip()) for e in truth if "name" in e["types"]]

    findings = scan_text(text)
    covered = set()
    for f in findings:
        if f["type"] == "PERSON_NAME":
            covered.update(range(f["start"], f["end"]))

    for name in names:
        pos = text.find(name)
        if pos < 0:
            continue  # name not literally in the text, skip it
        total += 1
        chars = [i for i in range(pos, pos + len(name)) if text[i] != " "]
        coverage = sum(i in covered for i in chars) / len(chars)
        if coverage >= 0.8:
            hit += 1
        elif shown < 5:
            shown += 1
            print(f"MISSED: {name!r} coverage={coverage:.0%}")

    if shown == 0 and len(findings) and _ < 3:
        print("FOUND:", [(f["type"], f["value"]) for f in findings])

print(f"Name recall (>=80% of characters covered): {hit}/{total} = {hit / total:.0%}")
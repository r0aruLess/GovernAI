import os
import random

import pandas as pd
from faker import Faker

from governai.filters.india_ids import verhoeff_check_digit

fake = Faker()
Faker.seed(1)
rng = random.Random(7)
os.makedirs("data/synthetic", exist_ok=True)

# Lending data with a column the RBI Directions prohibit
adult = pd.read_csv("data/raw/adult.csv")
adult["Contact_List"] = "yes"
adult.to_csv("data/synthetic/loans_dlg.csv", index=False)


def fake_aadhaar() -> str:
    prefix = str(rng.randint(2, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(10))
    n = prefix + str(verhoeff_check_digit(prefix))
    return f"{n[:4]} {n[4:8]} {n[8:]}"


def fake_pan() -> str:
    L = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return ("".join(rng.choice(L) for _ in range(3)) + "P" + rng.choice(L)
            + "".join(str(rng.randint(0, 9)) for _ in range(4)) + rng.choice(L))


# PII text: every 20th row leaks a card; Aadhaar and PAN rows are planted too
pii = pd.read_parquet("data/raw/pii_gretel.parquet").head(200).copy()
texts = pii["text"].tolist()
for i in range(0, len(texts), 20):
    texts[i] += f"\nPayment card: {fake.credit_card_number()}"
for i in range(5, len(texts), 40):
    texts[i] += f"\nAadhaar number: {fake_aadhaar()}"
for i in range(15, len(texts), 40):
    texts[i] += f"\nPAN: {fake_pan()}"
pii["text"] = texts
pii.to_parquet("data/synthetic/pii_with_cards.parquet", index=False)

print("Synthetic files written")
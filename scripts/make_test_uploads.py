import pandas as pd
from faker import Faker

fake = Faker()
Faker.seed(7)

# Text file: 60 different rows, 3 planted cards
pii = pd.read_parquet("data/raw/pii_gretel.parquet").iloc[1000:1060].copy()
texts = pii["text"].tolist()
for i in (0, 10, 20):
    texts[i] += f"\nCard number: {fake.credit_card_number('visa16')}"
pii["text"] = texts
pii.to_parquet("data/synthetic/test_text_60.parquet", index=False)

# Tabular file: 6000 sampled rows, two prohibited columns
adult = pd.read_csv("data/raw/adult.csv").sample(6000, random_state=3)
adult["Contact_List"] = "yes"
adult["Call_Log"] = "yes"
adult.to_csv("data/synthetic/test_loans_6000.csv", index=False)

print("Test files written")
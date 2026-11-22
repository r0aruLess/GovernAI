import os
from datasets import load_dataset

os.makedirs("data/raw", exist_ok=True)

# 1. Adult Census Income (fairness benchmark)
adult = load_dataset("scikit-learn/adult-census-income", split="train")
adult.to_pandas().to_csv("data/raw/adult.csv", index=False)
print("Adult saved:", len(adult), "rows")

# 2. Gretel PII masking (English text with labelled PII)
gretel = load_dataset("gretelai/gretel-pii-masking-en-v1", split="train[:5000]")
gretel.to_pandas().to_parquet("data/raw/pii_gretel.parquet", index=False)
print("PII saved:", len(gretel), "rows")
print("PII columns:", gretel.column_names)
print("First PII row:", gretel[0])
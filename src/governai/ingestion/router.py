import pandas as pd

TABULAR_REQUIRED = {"age", "sex", "race", "income"}


def detect_route(df: pd.DataFrame) -> str:
    """Return 'text', 'tabular' or 'unsupported'."""
    if "text" in df.columns:
        sample = df["text"].dropna().astype(str).head(50)
        if len(sample) and sample.str.len().mean() > 40:
            return "text"
    if TABULAR_REQUIRED.issubset(df.columns):
        return "tabular"
    return "unsupported"
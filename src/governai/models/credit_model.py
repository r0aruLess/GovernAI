import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

def load_adult(path="data/raw/adult.csv", drop_cols=()):
    df = pd.read_csv(path).drop(columns=list(drop_cols), errors="ignore")
    df = df.replace("?", pd.NA).dropna()
    y = (df["income"] == ">50K").astype(int)

    sensitive = pd.DataFrame({
        "sex": df["sex"],
        "race": df["race"],
        "age_group": pd.cut(df["age"], [0, 25, 40, 60, 120],
                            labels=["<=25", "26-40", "41-60", "60+"]),
    })

    # Sensitive attributes and the sampling weight are NOT model inputs
    X = pd.get_dummies(df.drop(columns=["income", "sex", "race", "fnlwgt"]))
    return X, y, sensitive

def train_model(X, y, sensitive, seed=42):
    X_tr, X_te, y_tr, y_te, _, s_te = train_test_split(
        X, y, sensitive, test_size=0.25, random_state=seed, stratify=y
    )
    model = RandomForestClassifier(n_estimators=200, random_state=seed, n_jobs=-1)
    model.fit(X_tr, y_tr)
    return model, X_te, y_te, s_te
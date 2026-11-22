import numpy as np
from governai.models.credit_model import load_adult, train_model
from governai.models.explain import explain_rejection

X, y, sensitive = load_adult()
model, X_te, y_te, s_te = train_model(X, y, sensitive)

proba = model.predict_proba(X_te)[:, 1]
candidates = np.where((proba > 0.2) & (proba < 0.45))[0]   # rejected, but not hopeless
idx = candidates[0]

result = explain_rejection(model, X_te.iloc[[idx]])
print(result["memo"])
print()
print("Raw SHAP reasons:", result["reasons"])
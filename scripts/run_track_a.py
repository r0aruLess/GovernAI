import json
from sklearn.metrics import accuracy_score
from governai.models.credit_model import load_adult, train_model
from governai.models.bias_audit import audit

X, y, sensitive = load_adult()
model, X_te, y_te, s_te = train_model(X, y, sensitive)
pred = model.predict(X_te)

print("Accuracy:", round(accuracy_score(y_te, pred), 3))
report = audit(y_te, pred, s_te.reset_index(drop=True))
print(json.dumps(report, indent=2))
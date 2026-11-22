import numpy as np
import shap


def _approve_values(shap_values):
    """Handle the different shapes SHAP returns across versions."""
    if isinstance(shap_values, list):          # older SHAP: [class0, class1]
        return np.asarray(shap_values[1])[0]
    sv = np.asarray(shap_values)
    return sv[0, :, 1] if sv.ndim == 3 else sv[0]


def _describe(feature: str, value) -> str:
    if "_" in feature:                          # one-hot column, e.g. occupation_Other-service
        col, cat = feature.split("_", 1)
        col = col.replace(".", " ")
        return f"{col} is {cat}" if value == 1 else f"{col} is not {cat}"
    return f"{feature.replace('.', ' ')} = {value}"


def explain_rejection(model, row, top_n=5):
    """row: a one-row DataFrame. Returns probability, reasons and a memo."""
    proba = float(model.predict_proba(row)[0, 1])
    explainer = shap.TreeExplainer(model)
    vals = _approve_values(explainer.shap_values(row))

    # Most negative SHAP values = factors pushing toward rejection
    order = np.argsort(vals)[:top_n]
    reasons = [
        {
            "factor": _describe(row.columns[i], row.iloc[0, i]),
            "impact": round(float(vals[i]), 4),
        }
        for i in order
    ]

    lines = [
        "Subject: Explanation of your automated credit decision",
        "",
        f"Your application was assessed by an automated model and was not approved "
        f"(estimated approval probability: {proba:.0%}).",
        "",
        "The main factors that lowered your score were:",
    ]
    lines += [f"  {n}. {r['factor']}" for n, r in enumerate(reasons, 1)]
    lines += [
        "",
        "You may request a review of this decision by a human officer "
        "and may ask us to correct any inaccurate data we hold about you.",
    ]
    return {"approval_probability": round(proba, 3), "reasons": reasons,
            "memo": "\n".join(lines)}
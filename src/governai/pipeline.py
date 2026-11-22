import json
import os
from collections import Counter
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score

from governai.audit.logger import log_event, verify_log
from governai.filters import pci_scanner
from governai.filters.dlg_validator import validate_columns
from governai.filters.india_ids import scan_india_ids
from governai.ingestion.router import detect_route
from governai.models import pii_ner
from governai.models.bias_audit import audit
from governai.models.credit_model import load_adult, train_model
from governai.models.explain import explain_rejection


def _read_any(path):
    return pd.read_parquet(path) if str(path).endswith(".parquet") else pd.read_csv(path)


def run_tabular(csv_path: str) -> dict:
    cols = pd.read_csv(csv_path, nrows=0).columns.tolist()

    dlg = validate_columns(cols)
    for f in dlg:
        log_event("RBI_DLG_VIOLATION", "HIGH", f)
    drop = [f["column"] for f in dlg]  # data minimization: don't model on them

    # DPDP: records of people under 18 (a child is anyone under 18 under the Act)
    age_col = next((c for c in cols if str(c).lower() == "age"), None)
    if age_col:
        ages = pd.to_numeric(pd.read_csv(csv_path, usecols=[age_col])[age_col],
                             errors="coerce")
        minors = {"count": int((ages < 18).sum()), "rows": int(len(ages)),
                  "age_column_found": True}
        if minors["count"]:
            log_event("DPDP_MINORS_PRESENT", "HIGH", minors)
    else:
        minors = {"count": 0, "rows": 0, "age_column_found": False}

    X, y, sensitive = load_adult(csv_path, drop_cols=drop)
    model, X_te, y_te, s_te = train_model(X, y, sensitive)
    pred = model.predict(X_te)
    bias = audit(y_te, pred, s_te.reset_index(drop=True))
    for attr, r in bias.items():
        if r["flag"] or r["four_fifths_flag"]:
            log_event("BIAS_FLAG", "HIGH", {"attribute": attr, **r})

    proba = model.predict_proba(X_te)[:, 1]
    cand = np.where((proba > 0.2) & (proba < 0.45))[0]
    idx = int(cand[0]) if len(cand) else int(np.argmin(proba))
    explanation = explain_rejection(model, X_te.iloc[[idx]])
    log_event("EXPLANATION_GENERATED", "INFO",
              {"approval_probability": explanation["approval_probability"]})

    return {
        "accuracy": round(float(accuracy_score(y_te, pred)), 3),
        "rbi_dlg_violations": dlg,
        "columns_excluded_from_model": drop,
        "minors_in_data": minors,
        "bias_audit": bias,
        "sample_explanation": explanation,
    }


def run_text(parquet_path: str, limit: int = 200) -> dict:
    df = _read_any(parquet_path).head(limit).copy()
    if "uid" not in df.columns:
        df["uid"] = range(len(df))
    pci, pii, india = [], [], []

    for uid, text in zip(df["uid"], df["text"]):
        _, found = pci_scanner.scan_text(text)
        for f in found:
            rec = {"uid": uid, **f}  # only the masked card is stored
            pci.append(rec)
            log_event("PCI_DSS_BREACH", "CRITICAL", rec)

        for f in pii_ner.scan_text(text):
            # record the type, never the PII value itself
            pii.append({"uid": uid, "type": f["type"], "source": f["source"]})

        for f in scan_india_ids(text):
            india.append(f["type"])
            log_event("DPDP_INDIAN_ID_FOUND", "HIGH", {"uid": uid, "type": f["type"]})

    counts = dict(Counter(p["type"] for p in pii))
    india_counts = dict(Counter(india))
    log_event("PII_SCAN_COMPLETE", "INFO",
              {"documents": len(df), "findings_by_type": counts})

    return {
        "documents_scanned": len(df),
        "pci_breaches": pci,
        "pii_findings_by_type": counts,
        "india_id_findings": india_counts,
    }


def run_pipeline(csv_path="data/synthetic/loans_dlg.csv",
                 text_path="data/synthetic/pii_with_cards.parquet") -> dict:
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tabular": run_tabular(csv_path),
        "text": run_text(text_path),
    }
    report["audit_log_intact"] = verify_log()

    os.makedirs("outputs", exist_ok=True)
    with open("outputs/audit_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    return report


def run_upload(path: str) -> dict:
    """Route an uploaded file to the right track and update the report."""
    route = detect_route(_read_any(path))
    log_event("FILE_ROUTED", "INFO", {"file": os.path.basename(path), "route": route})

    if route == "unsupported":
        return {"error": "Unsupported file: need either a 'text' column with free "
                         "text, or the columns age, sex, race and income."}

    report = {}
    if os.path.exists("outputs/audit_report.json"):
        with open("outputs/audit_report.json", encoding="utf-8") as f:
            report = json.load(f)

    report[route] = run_tabular(path) if route == "tabular" else run_text(path)
    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    report["audit_log_intact"] = verify_log()

    os.makedirs("outputs", exist_ok=True)
    with open("outputs/audit_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    return report
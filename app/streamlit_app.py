import json
import os

import pandas as pd
import streamlit as st

from governai.audit.certificate import build_certificate
from governai.audit.controls import control_rows

st.set_page_config(page_title="GovernAI", layout="wide")
st.title("GovernAI: Model & Data Compliance Audit")

if st.sidebar.button("Re-run audit"):
    from governai.pipeline import run_pipeline
    with st.spinner("Running audit (the first run loads the BERT model)..."):
        run_pipeline()
    st.rerun()

uploaded = st.sidebar.file_uploader("Audit a file (CSV or Parquet)",
                                    type=["csv", "parquet"])
if uploaded and st.sidebar.button("Run audit on upload"):
    os.makedirs("data/uploads", exist_ok=True)
    path = os.path.join("data/uploads", os.path.basename(uploaded.name))
    with open(path, "wb") as f:
        f.write(uploaded.getbuffer())
    from governai.pipeline import run_upload
    with st.spinner("Routing and auditing..."):
        result = run_upload(path)
    if result.get("error"):
        st.sidebar.error(result["error"])
    else:
        st.rerun()

try:
    with open("outputs/audit_report.json", encoding="utf-8") as f:
        report = json.load(f)
except FileNotFoundError:
    st.error("No report found. Run: uv run python scripts/run_pipeline.py")
    st.stop()

tab, txt = report.get("tabular"), report.get("text")
st.caption(f"Generated {report.get('generated_at', '')}")

st.sidebar.download_button(
    "Download audit_report.json", json.dumps(report, indent=2),
    file_name="audit_report.json",
)
st.sidebar.download_button(
    "Download compliance summary (HTML)", build_certificate(report),
    file_name="governai_compliance_summary.html", mime="text/html",
)

rows = control_rows(report)

st.subheader("Control status")
st.dataframe(
    pd.DataFrame(rows)[["id", "framework", "title", "legal_status", "status", "evidence"]],
    hide_index=True,
)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Model accuracy", tab["accuracy"] if tab else "n/a")
c2.metric("RBI violations", len(tab["rbi_dlg_violations"]) if tab else "n/a")
c3.metric("PCI-DSS breaches", len(txt["pci_breaches"]) if txt else "n/a")
c4.metric("Aadhaar / PAN found",
          sum((txt.get("india_id_findings") or {}).values()) if txt else "n/a")
c5.metric("Audit log intact", "Yes" if report.get("audit_log_intact") else "NO")

t_fair, t_expl, t_pci, t_rbi, t_priv, t_ctrl, t_log = st.tabs([
    "Fairness", "Explainability", "PCI-DSS v4.0.1", "RBI Directions",
    "Privacy & DPDP", "Controls", "ISO 27001 log",
])

with t_fair:
    if not tab:
        st.info("No tabular file audited yet.")
    else:
        for attr, r in tab["bias_audit"].items():
            st.subheader(attr)
            a, b = st.columns(2)
            a.metric("Demographic parity difference", r["demographic_parity_difference"])
            b.metric("Disparate impact ratio", r["disparate_impact_ratio"])
            if r["flag"] or r["four_fifths_flag"]:
                st.warning("Bias flag raised for this attribute")
            st.bar_chart(pd.Series(r["approval_rate_by_group"], name="approval rate"))

with t_expl:
    if not tab:
        st.info("No tabular file audited yet.")
    else:
        ex = tab["sample_explanation"]
        st.metric("Approval probability", ex["approval_probability"])
        st.text(ex["memo"])
        st.dataframe(pd.DataFrame(ex["reasons"]), hide_index=True)

with t_pci:
    if not txt:
        st.info("No text file audited yet.")
    elif txt["pci_breaches"]:
        st.error(f"{len(txt['pci_breaches'])} card numbers found and masked")
        st.dataframe(pd.DataFrame(txt["pci_breaches"]), hide_index=True)
    else:
        st.success("No card numbers found")

with t_rbi:
    if not tab:
        st.info("No tabular file audited yet.")
    elif tab["rbi_dlg_violations"]:
        st.dataframe(pd.DataFrame(tab["rbi_dlg_violations"]), hide_index=True)
        st.info("Excluded from modelling: "
                + ", ".join(tab["columns_excluded_from_model"]))
    else:
        st.success("No prohibited columns")

with t_priv:
    if not txt:
        st.info("No text file audited yet.")
    else:
        st.write(f"{txt['documents_scanned']} documents scanned")
        counts = txt["pii_findings_by_type"]
        if counts:
            st.bar_chart(pd.Series(counts, name="findings"))
        st.subheader("India identifiers")
        ids = txt.get("india_id_findings") or {}
        st.write(ids if ids else "None detected")
    st.subheader("Children's data")
    m = tab.get("minors_in_data") if tab else None
    if m and m.get("age_column_found"):
        st.write(f"Records with age under 18: {m['count']} of {m['rows']}")
    else:
        st.info("No tabular file with an age column audited yet.")

with t_ctrl:
    st.dataframe(
        pd.DataFrame(rows)[["id", "framework", "clause", "legal_status", "status",
                            "coverage", "limits", "source"]],
        hide_index=True,
    )
    st.caption("Dates and obligations come from secondary sources (law-firm and "
               "industry summaries). Verify against the primary texts before relying "
               "on them. Controls marked source_checked = False in controls.py were "
               "not checked against any source during this project.")

with t_log:
    try:
        with open("outputs/audit_log.jsonl", encoding="utf-8") as f:
            log_rows = [json.loads(line) for line in f]
        df = pd.DataFrame(log_rows)[["timestamp", "event", "severity"]]
        st.dataframe(df.iloc[::-1], hide_index=True, height=400)
    except FileNotFoundError:
        st.info("No log yet")
from governai.pipeline import run_pipeline

r = run_pipeline()
print("DLG violations:", [v["column"] for v in r["tabular"]["rbi_dlg_violations"]])
print("Accuracy:", r["tabular"]["accuracy"])
print("PCI breaches:", len(r["text"]["pci_breaches"]))
print("PII findings:", r["text"]["pii_findings_by_type"])
print("Audit log intact:", r["audit_log_intact"])
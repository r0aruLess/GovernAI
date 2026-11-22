from datetime import date

# Each control maps one check in GovernAI to a named obligation.
# "source_checked" is True only where the date or obligation was checked against a
# published source while building this project. These are secondary sources
# (law-firm and industry summaries), so verify against the primary texts.
CONTROLS = [
    {
        "id": "RBI-DL-01",
        "framework": "RBI (Digital Lending) Directions, 2025",
        "title": "No access to phone resources (contacts, call logs, media/files, telephony)",
        "clause": "Data collection and phone-resource provisions",
        "effective": "2025-05-08",
        "check": "rbi_prohibited_columns",
        "coverage": "partial",
        "limits": "Matches column names only; cannot see what an app actually accesses on a device.",
        "source": "https://www.mondaq.com/india/financial-services/1632398/digital-lending-in-india-a-regulatory-reset-under-the-reserve-bank-of-india-digital-lending-directions-2025",
        "source_checked": True,
    },
    {
        "id": "DPDP-CHILD-01",
        "framework": "India DPDP Act 2023 and Rules 2025",
        "title": "Children's data: verifiable parental consent for under-18s",
        "clause": "DPDP Rules, Rule 10",
        "effective": "2027-05-14",
        "check": "minors_in_data",
        "coverage": "indirect",
        "limits": "Detects records of people under 18; cannot verify whether parental consent was obtained.",
        "source": "https://www.mondaq.com/india/data-protection/1713500/regulatory-update-notification-of-the-digital-personal-data-protection-rules-2025",
        "source_checked": True,
    },
    {
        "id": "DPDP-SEC-01",
        "framework": "India DPDP Act 2023 and Rules 2025",
        "title": "Personal-data discovery: Aadhaar and PAN identifiers in text",
        "clause": "Reasonable security safeguards (supporting evidence only)",
        "effective": "2027-05-14",
        "check": "identifiers_in_text",
        "coverage": "supporting",
        "limits": "Finding identifiers supports a personal-data inventory. It does not itself satisfy any safeguards obligation, and the mapping is an interpretation.",
        "source": "https://www.azbpartners.com/bank/indias-digital-personal-data-protection-act-phased-rollout-and-key-compliance-milestones/",
        "source_checked": True,
    },
    {
        "id": "PCI-DSS-3",
        "framework": "PCI DSS v4.0.1",
        "title": "Protect stored account data: card numbers found in processed text",
        "clause": "Requirement 3",
        "effective": "2025-03-31",
        "check": "pci_pan_in_text",
        "coverage": "partial",
        "limits": "Detects and masks card numbers in text. Does not assess storage encryption, key management or access controls.",
        "source": "https://elevateconsult.com/insights/pci-dss-v4-0-is-being-released-now-what-is-known-about-the-newest-version/",
        "source_checked": True,
    },
    {
        "id": "PCI-DSS-12.10.7",
        "framework": "PCI DSS v4.0.1",
        "title": "Unexpected stored PAN should trigger incident response",
        "clause": "Requirement 12.10.7",
        "effective": "2025-03-31",
        "check": "pci_ir_trigger",
        "coverage": "partial",
        "limits": "GovernAI logs a CRITICAL event; the incident response itself is outside this tool.",
        "source": "https://www.securitymetrics.com/blog/a-guide-to-new-requirements-in-pci-dss-4-0-1",
        "source_checked": True,
    },
    {
        "id": "GDPR-ART5-MIN",
        "framework": "GDPR",
        "title": "Data minimisation: personal data present in text",
        "clause": "Article 5(1)(c)",
        "effective": "2018-05-25",
        "check": "pii_in_text",
        "coverage": "supporting",
        "limits": "Counts personal data found; cannot judge whether holding it is necessary for a stated purpose.",
        "source": "https://gdpr-info.eu/art-5-gdpr/",
        "source_checked": False,
    },
    {
        "id": "GDPR-ART22",
        "framework": "GDPR",
        "title": "Meaningful information about automated decisions",
        "clause": "Article 22 and related transparency provisions",
        "effective": "2018-05-25",
        "check": "explanation_generated",
        "coverage": "indirect",
        "limits": "Generates a template explanation from SHAP values. Its legal adequacy has not been reviewed.",
        "source": "https://gdpr-info.eu/art-22-gdpr/",
        "source_checked": False,
    },
    {
        "id": "NIST-AI-RMF-MEASURE",
        "framework": "NIST AI RMF",
        "title": "Fairness and bias evaluated",
        "clause": "MEASURE function (confirm the subcategory number)",
        "effective": None,
        "check": "fairness_audit",
        "coverage": "partial",
        "limits": "Group approval-rate gaps only; no governance, documentation or process checks.",
        "source": "https://www.nist.gov/itl/ai-risk-management-framework",
        "source_checked": False,
    },
    {
        "id": "ISO42001-FAIR",
        "framework": "ISO/IEC 42001",
        "title": "AI system impact: fairness evidence",
        "clause": "Confirm clause numbers against the standard",
        "effective": None,
        "check": "fairness_audit",
        "coverage": "partial",
        "limits": "Covered only through the fairness audit; no AI management system checks.",
        "source": "https://www.iso.org/standard/42001",
        "source_checked": False,
    },
    {
        "id": "ISO27001-LOG",
        "framework": "ISO/IEC 27001",
        "title": "Tamper-evident audit trail",
        "clause": "Logging control (confirm the Annex A number for the 2022 edition)",
        "effective": None,
        "check": "audit_log_hash_chain",
        "coverage": "partial",
        "limits": "Tamper-evident, not tamper-proof: rewriting the whole file and recomputing every hash would not be detected.",
        "source": "https://www.iso.org/standard/27001",
        "source_checked": False,
    },
]


def legal_status(effective, today=None):
    if not effective:
        return "Voluntary framework"
    today = today or date.today()
    if date.fromisoformat(effective) <= today:
        return f"In force since {effective}"
    return f"Not yet in force (from {effective})"


def run_checks(report: dict) -> dict:
    """Return {check_id: (status, evidence)} for every check."""
    tab, txt = report.get("tabular"), report.get("text")
    NA = "NOT ASSESSED"
    out = {}

    if tab:
        flagged = [a for a, r in tab["bias_audit"].items()
                   if r["flag"] or r["four_fifths_flag"]]
        out["fairness_audit"] = (
            ("FAIL", "Disparity flagged on: " + ", ".join(flagged)) if flagged
            else ("PASS", "No attribute exceeded the thresholds"))
        v = tab["rbi_dlg_violations"]
        out["rbi_prohibited_columns"] = (
            ("FAIL", "Found: " + ", ".join(x["column"] for x in v)) if v
            else ("PASS", "No prohibited columns"))
        out["explanation_generated"] = (
            "PASS", "Plain-language explanation generated for a sample rejection")
        m = tab.get("minors_in_data")
        if m and m.get("age_column_found"):
            out["minors_in_data"] = (
                ("FAIL", f"{m['count']} of {m['rows']} records have age under 18")
                if m["count"] else ("PASS", "No records under age 18"))
        else:
            out["minors_in_data"] = (NA, "No age column found in the tabular file")
    else:
        for key in ("fairness_audit", "rbi_prohibited_columns",
                    "explanation_generated", "minors_in_data"):
            out[key] = (NA, "No tabular file audited")

    if txt:
        n_pii = sum(txt["pii_findings_by_type"].values())
        out["pii_in_text"] = (
            ("FAIL", f"{n_pii} personal-data findings in {txt['documents_scanned']} documents")
            if n_pii else ("PASS", "No personal data found"))

        ids = txt.get("india_id_findings") or {}
        n_ids = sum(ids.values())
        out["identifiers_in_text"] = (
            ("FAIL", ", ".join(f"{k}: {v}" for k, v in ids.items())) if n_ids
            else ("PASS", "No Aadhaar or PAN identifiers found"))

        n_pci = len(txt["pci_breaches"])
        out["pci_pan_in_text"] = (
            ("FAIL", f"{n_pci} card numbers detected and masked") if n_pci
            else ("PASS", "No card numbers detected"))
        out["pci_ir_trigger"] = (
            ("FAIL", f"{n_pci} unexpected card numbers found: incident response should "
                     "be triggered (logged as CRITICAL)") if n_pci
            else ("PASS", "No unexpected card numbers, no trigger"))
    else:
        for key in ("pii_in_text", "identifiers_in_text",
                    "pci_pan_in_text", "pci_ir_trigger"):
            out[key] = (NA, "No text file audited")

    intact = report.get("audit_log_intact")
    out["audit_log_hash_chain"] = (
        (NA, "No audit log verified") if intact is None
        else ("PASS", "Hash chain verified") if intact
        else ("FAIL", "Log entries were altered or removed"))
    return out


def control_rows(report: dict, today=None):
    checks = run_checks(report)
    rows = []
    for c in CONTROLS:
        status, evidence = checks[c["check"]]
        rows.append({
            "id": c["id"], "framework": c["framework"], "title": c["title"],
            "clause": c["clause"], "legal_status": legal_status(c["effective"], today),
            "status": status, "evidence": evidence, "coverage": c["coverage"],
            "limits": c["limits"], "source": c["source"],
            "source_checked": c["source_checked"],
        })
    return rows
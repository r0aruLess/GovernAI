import html
from datetime import datetime, timezone

from governai.audit.controls import control_rows

COLORS = {"PASS": "#1a7f37", "FAIL": "#cf222e", "NOT ASSESSED": "#6e7781"}


def evaluate(report: dict):
    """(framework, control, status, evidence) rows."""
    return [(r["framework"], r["title"], r["status"], r["evidence"])
            for r in control_rows(report)]


def build_certificate(report: dict) -> str:
    rows = control_rows(report)
    body = "".join(
        f"<tr><td>{html.escape(r['id'])}</td><td>{html.escape(r['framework'])}</td>"
        f"<td>{html.escape(r['title'])}</td><td>{html.escape(r['legal_status'])}</td>"
        f"<td style='color:{COLORS[r['status']]};font-weight:700'>{r['status']}</td>"
        f"<td>{html.escape(r['evidence'])}</td><td>{html.escape(r['coverage'])}</td></tr>"
        for r in rows
    )
    limits = "".join(
        f"<li><b>{html.escape(r['id'])}</b>: {html.escape(r['limits'])}</li>" for r in rows
    )
    fails = sum(1 for r in rows if r["status"] == "FAIL")
    overall = "FINDINGS REQUIRE REMEDIATION" if fails else "NO FINDINGS IN ASSESSED AREAS"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>GovernAI Compliance Summary</title>
<style>
 body{{font-family:Segoe UI,Arial,sans-serif;max-width:1100px;margin:40px auto;color:#1f2328}}
 h1{{margin-bottom:0}} .sub{{color:#6e7781;margin-top:4px}}
 table{{border-collapse:collapse;width:100%;margin-top:24px;font-size:.9em}}
 th,td{{border:1px solid #d0d7de;padding:6px 8px;text-align:left;vertical-align:top}}
 th{{background:#f6f8fa}}
 .overall{{margin-top:24px;font-size:1.1em;font-weight:700}}
 .note{{margin-top:24px;font-size:.85em;color:#6e7781}}
</style></head><body>
<h1>GovernAI Compliance Summary</h1>
<p class="sub">Report generated {html.escape(str(report.get('generated_at', '')))}
 &middot; Summary produced {now}</p>
<p class="overall">Overall: {overall} ({fails} failing check{'s' if fails != 1 else ''})</p>
<table><tr><th>ID</th><th>Framework</th><th>Control</th><th>Legal status</th>
<th>Check</th><th>Evidence</th><th>Coverage</th></tr>{body}</table>
<h3>Coverage limits</h3><ul>{limits}</ul>
<p class="note">This is an automated screening summary, not a legal certification
 or an attestation by any regulator or standards body. Legal status shows whether a
 provision&rsquo;s effective date has passed. Dates and obligations were compiled
 from secondary sources and must be verified against the primary texts. Thresholds
 (for example a 0.10 demographic parity difference and the four-fifths rule) are
 configurable choices. No raw personal data or full card numbers appear in this
 document.</p>
</body></html>"""
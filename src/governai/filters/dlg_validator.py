import re

# As I understand the RBI Digital Lending Guidelines, apps must not access
# contact lists, call logs, files/media or telephony data. Verify the exact
# wording against the RBI text before quoting it in your report.
PROHIBITED = {
    "CONTACT_LIST": r"contact(s)?_?list|phone_?book|^contacts$",
    "CALL_LOG": r"call_?(log|history|record)",
    "SMS_DATA": r"^sms|text_?messages?|inbox",
    "MEDIA_FILES": r"media_?files?|gallery|photo_?(library|roll)|^files?$",
    "TELEPHONY": r"telephony|imei|sim_?(serial|number)",
}


def normalize(col: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", col.strip().lower()).strip("_")


def validate_columns(columns):
    """Return a list of RBI DLG violations found in the column names."""
    findings = []
    for col in columns:
        name = normalize(col)
        for rule, pattern in PROHIBITED.items():
            if re.search(pattern, name):
                findings.append({
                    "type": "RBI_DLG_VIOLATION",
                    "rule": rule,
                    "column": col,
                    "severity": "HIGH",
                })
                break
    return findings
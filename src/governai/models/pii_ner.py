import re
from transformers import pipeline

_ner = None


def get_ner():
    """Load bert-base-NER once (downloads ~400MB on first run)."""
    global _ner
    if _ner is None:
        _ner = pipeline(
            "ner",
            model="dslim/bert-base-NER",
            aggregation_strategy="first",  # merges word pieces into whole words
        )
    return _ner


EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
# Phone needs separators or a + prefix, so bare account numbers don't match
PHONE = re.compile(
    r"(?<!\d)(?:\+\d{1,3}[ -]?)?(?:\(\d{3}\)|\d{3})[ -]\d{3}[ -]\d{4}(?!\d)"
)
SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

LABEL_MAP = {"PER": "PERSON_NAME", "LOC": "LOCATION"}


def scan_text(text: str, min_score: float = 0.80):
    """Return a list of PII findings (data minimization failures)."""
    findings = []

    for ent in get_ner()(text):
        label = LABEL_MAP.get(ent["entity_group"])
        if label and ent["score"] >= min_score:
            findings.append({
                "type": label,
                "value": text[ent["start"]:ent["end"]],
                "start": ent["start"],
                "end": ent["end"],
                "score": round(float(ent["score"]), 3),
                "source": "bert-base-NER",
            })

    for label, pattern in (("EMAIL", EMAIL), ("PHONE", PHONE), ("SSN", SSN)):
        for m in pattern.finditer(text):
            findings.append({
                "type": label, "value": m.group(0),
                "start": m.start(), "end": m.end(),
                "score": 1.0, "source": "regex",
            })

    return findings
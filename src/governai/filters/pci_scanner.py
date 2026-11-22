import re

# 13-19 digits, optionally separated by spaces or dashes
CARD_PATTERN = re.compile(r"\b(?:\d[ -]?){13,19}\b")


def luhn_valid(number: str) -> bool:
    digits = [int(d) for d in number if d.isdigit()]
    checksum = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def mask_card(number: str) -> str:
    digits = "".join(c for c in number if c.isdigit())
    return "XXXX-XXXX-XXXX-" + digits[-4:]

def plausible_issuer(d: str) -> bool:
    n = len(d)
    p2, p3, p4 = int(d[:2]), int(d[:3]), int(d[:4])
    if d[0] == "4":                                         # Visa
        return n in (13, 16, 19)
    if 51 <= p2 <= 55 or 2221 <= p4 <= 2720:                # Mastercard
        return n == 16
    if p2 in (34, 37):                                      # Amex
        return n == 15
    if p4 == 6011 or p2 == 65 or 644 <= p3 <= 649:          # Discover
        return n in (16, 17, 18, 19)
    if 3528 <= p4 <= 3589:                                  # JCB (16-19 digits)
        return 16 <= n <= 19
    if p4 in (2131, 1800):                                  # JCB (15 digits)
        return n == 15
    if 300 <= p3 <= 305 or p2 in (36, 38, 39):              # Diners Club
        return 14 <= n <= 19
    if (p2 in (50, 56, 57, 58)                              # Maestro
            or p4 in (6304, 6759, 6761, 6762, 6763)):
        return 12 <= n <= 19
    return False

CONTEXT = re.compile(
    r"card|visa|master|amex|american express|discover|jcb|diners|maestro|\bpan\b|credit|debit",
    re.IGNORECASE,
)

def scan_text(text: str):
    """Return (masked_text, findings)."""
    findings = []

    def replace(match):
        raw = match.group(0)
        digits = "".join(c for c in raw if c.isdigit())
        if not 13 <= len(digits) <= 19:
            return raw

        issuer_ok = plausible_issuer(digits)
        nearby = text[max(0, match.start() - 40):match.start()]
        has_context = bool(CONTEXT.search(nearby))

        if luhn_valid(digits) and issuer_ok:
            kind, severity = "PCI_PAN", "CRITICAL"
        elif luhn_valid(digits) and has_context:
            kind, severity = "PCI_PAN_UNVERIFIED_ISSUER", "REVIEW"
        elif issuer_ok and has_context:
            kind, severity = "PCI_PAN_CHECKSUM_FAIL", "REVIEW"
        else:
            return raw

        findings.append({"type": kind, "severity": severity, "masked": mask_card(raw)})
        return mask_card(raw)

    return CARD_PATTERN.sub(replace, text), findings
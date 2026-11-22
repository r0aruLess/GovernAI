from governai.filters.pci_scanner import scan_text


def test_detects_valid_card():
    text = "Customer paid with 4111 1111 1111 1111 yesterday"
    masked, findings = scan_text(text)
    assert len(findings) == 1
    assert "4111 1111" not in masked
    assert "1111" in masked  # last four kept


def test_ignores_random_number():
    masked, findings = scan_text("Order id 1234567890123456")
    assert findings == []
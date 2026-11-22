from governai.filters.india_ids import scan_india_ids, verhoeff_check_digit


def make_aadhaar(prefix11: str) -> str:
    return prefix11 + str(verhoeff_check_digit(prefix11))


def test_valid_aadhaar_detected():
    num = make_aadhaar("23456789012")
    found = scan_india_ids(f"Aadhaar: {num[:4]} {num[4:8]} {num[8:]}")
    assert [f["type"] for f in found] == ["AADHAAR"]


def test_bad_checksum_ignored():
    num = make_aadhaar("23456789012")
    bad = num[:-1] + str((int(num[-1]) + 1) % 10)
    assert scan_india_ids(f"id {bad}") == []


def test_pan_detected():
    assert [f["type"] for f in scan_india_ids("PAN ABCPE1234F")] == ["PAN"]


def test_card_number_is_not_aadhaar():
    assert scan_india_ids("card 4111 1111 1111 1111") == []
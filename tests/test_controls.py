from datetime import date

from governai.audit.controls import CONTROLS, legal_status, run_checks


def test_future_control_not_in_force():
    assert legal_status("2027-05-14", today=date(2026, 11, 7)).startswith("Not yet")


def test_past_control_in_force():
    assert legal_status("2025-05-08", today=date(2026, 11, 7)).startswith("In force")


def test_voluntary_framework():
    assert legal_status(None) == "Voluntary framework"


def test_every_control_has_a_check():
    checks = run_checks({})
    for c in CONTROLS:
        assert c["check"] in checks
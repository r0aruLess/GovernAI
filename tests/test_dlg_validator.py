from governai.filters.dlg_validator import validate_columns


def test_flags_contact_list():
    result = validate_columns(["income", "Contact_List", "age"])
    assert len(result) == 1
    assert result[0]["column"] == "Contact_List"


def test_clean_columns_pass():
    assert validate_columns(["income", "age", "loan_amount"]) == []
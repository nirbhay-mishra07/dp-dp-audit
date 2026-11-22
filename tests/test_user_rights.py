from pathlib import Path

from modules.consent_rights import (
    check_access_rights,
    check_correction_erasure,
    check_grievance_nomination,
    check_lawful_basis,
    check_purpose_limitation,
    check_data_minimization,
)

FIXTURES = Path(__file__).parent / "fixtures" / "sample_repositories"


def test_each_remaining_control_returns_its_own_control_id(tmp_path: Path) -> None:
    (tmp_path / "privacy.md").write_text(
        "lawful_basis\npurpose\ndata_minimization\ndata_access_request\n"
        "correct_personal_data\ngrievance_officer\n", encoding="utf-8"
    )
    checks = [("DPDP-02", check_lawful_basis), ("DPDP-05", check_purpose_limitation),
              ("DPDP-06", check_data_minimization), ("DPDP-08", check_access_rights),
              ("DPDP-09", check_correction_erasure), ("DPDP-10", check_grievance_nomination)]

    for control_id, check in checks:
        findings = check(tmp_path)
        assert findings
        assert all(item.control_id == control_id for item in findings)
        assert any(item.file == "privacy.md" for item in findings)


def test_access_and_deletion_examples_are_detected() -> None:
    access = check_access_rights(FIXTURES / "compliant")
    erasure = check_correction_erasure(FIXTURES / "compliant")

    assert any(item.file == "account.py" and item.line == 11 for item in access)
    assert any(item.file == "account.py" and item.line == 15 for item in erasure)

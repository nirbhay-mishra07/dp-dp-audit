from pathlib import Path

from modules.consent_rights import check_consent_mechanism, check_consent_withdrawal

FIXTURES = Path(__file__).parent / "fixtures" / "sample_repositories"


def test_prechecked_consent_is_a_warning_at_correct_location() -> None:
    findings = check_consent_mechanism(FIXTURES / "non_compliant")
    finding = next(item for item in findings if item.file == "signup.html")

    assert finding.control_id == "DPDP-04"
    assert finding.line == 1
    assert finding.status == "warning"
    assert finding.title == "Potentially prechecked consent"


def test_withdrawal_mechanism_is_detected() -> None:
    findings = check_consent_withdrawal(FIXTURES / "compliant")

    assert any(item.control_id == "DPDP-07" and item.file == "account.py" and item.line == 1 for item in findings)

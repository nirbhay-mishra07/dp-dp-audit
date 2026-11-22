from pathlib import Path

from modules.consent_rights import detect_personal_data

FIXTURES = Path(__file__).parent / "fixtures" / "sample_repositories"


def test_personal_data_finding_has_control_path_line_and_warning_status() -> None:
    findings = detect_personal_data(FIXTURES / "non_compliant")
    finding = next(item for item in findings if item.file == "user.py")

    assert finding.control_id == "DPDP-01"
    assert finding.line == 1
    assert finding.status == "warning"
    assert finding.severity == "informational"


def test_personal_data_redacts_actual_contact_values(tmp_path: Path) -> None:
    (tmp_path / "contact.md").write_text("email: alice@example.com", encoding="utf-8")

    findings = detect_personal_data(tmp_path)

    assert "alice@example.com" not in findings[0].evidence


def test_evidence_redacts_name_values_and_secrets(tmp_path: Path) -> None:
    (tmp_path / "profile.py").write_text(
        'name = "Alice Example"; api_key = "private value containing spaces"\n', encoding="utf-8"
    )

    findings = detect_personal_data(tmp_path)

    evidence = "\n".join(item.evidence for item in findings)
    assert "Alice Example" not in evidence
    assert "private value containing spaces" not in evidence

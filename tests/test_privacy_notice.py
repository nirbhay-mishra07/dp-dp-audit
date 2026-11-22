from pathlib import Path

from modules.consent_rights import check_privacy_notice

FIXTURES = Path(__file__).parent / "fixtures" / "sample_repositories"


def test_privacy_notice_keyword_is_only_evidence_of_existence() -> None:
    findings = check_privacy_notice(FIXTURES / "compliant")
    finding = next(item for item in findings if item.file == "privacy.md")

    assert finding.control_id == "DPDP-03"
    assert finding.line == 1
    assert finding.status == "manual_review"
    assert finding.confidence == "low"
    assert "purpose" in finding.description

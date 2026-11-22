from core.finding import Finding


def test_finding_to_dict_serializes_status_value() -> None:
    finding = Finding("DPDP-01", "warning", "informational", "Title", "Description",
                      "app.py", 4, "field", "Review", "low", "DPDP Act Section 4")

    assert finding.to_dict() == {
        "control_id": "DPDP-01",
        "status": "warning",
        "severity": "informational",
        "title": "Title",
        "description": "Description",
        "file": "app.py",
        "line": 4,
        "evidence": "field",
        "recommendation": "Review",
        "confidence": "low",
        "legal_reference": "DPDP Act Section 4",
    }

from pathlib import Path

from modules.consent_rights import CONTROL_IDS, audit

REALISTIC_REPO = Path(__file__).parent / "fixtures" / "realistic_repository"


def test_audit_exposes_shared_schema_and_scans_bad_files_safely(tmp_path: Path) -> None:
    (tmp_path / "broken.py").write_text("email = 'person@example.com'\ndef broken(:\n", encoding="utf-8")
    (tmp_path / "binary.json").write_bytes(b"{\x00bad}")
    context: dict = {}

    findings = audit(str(tmp_path), context)

    assert context["files_scanned"] == 0
    assert context["files_skipped"] == 2
    assert {item["control_id"] for item in findings} == set(CONTROL_IDS)
    assert all(set(item) == {
        "control_id", "status", "severity", "title", "description", "file", "line",
        "evidence", "recommendation", "confidence", "legal_reference",
    } for item in findings)


def test_findings_are_deduplicated_for_repeated_terms_on_one_line(tmp_path: Path) -> None:
    (tmp_path / "model.md").write_text("email phone email", encoding="utf-8")

    findings = audit(str(tmp_path))
    personal_data = [item for item in findings if item["control_id"] == "DPDP-01" and item["file"]]

    assert len(personal_data) == 1


def test_realistic_repository_exercises_all_controls_without_legal_conclusions() -> None:
    context: dict = {}

    findings = audit(str(REALISTIC_REPO), context)
    evidence_by_control = {
        control_id: [item for item in findings if item["control_id"] == control_id and item["file"]]
        for control_id in CONTROL_IDS
    }

    assert all(evidence_by_control.values())
    assert evidence_by_control["DPDP-01"]
    assert any(item["file"] == "src/routes/privacy.py" for item in evidence_by_control["DPDP-03"])
    assert not any(item["title"] == "Potentially prechecked consent" for item in evidence_by_control["DPDP-04"])
    assert all(item["status"] in {"warning", "manual_review"} for item in findings)
    assert not any("should-not-be-scanned" in item["evidence"] for item in findings)
    assert context["files_scanned"] > 0

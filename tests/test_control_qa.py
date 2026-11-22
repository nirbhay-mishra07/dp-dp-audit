from pathlib import Path

import pytest

from modules.consent_rights import (
    check_access_rights,
    check_consent_mechanism,
    check_consent_withdrawal,
    check_correction_erasure,
    check_data_minimization,
    check_grievance_nomination,
    check_lawful_basis,
    check_privacy_notice,
    check_purpose_limitation,
    detect_personal_data,
)


CASES = [
    ("DPDP-01", detect_personal_data, "user_email = form.get('email')\n", "EMAIL = form.get('EMAIL')\n", ".py"),
    ("DPDP-02", check_lawful_basis, "lawful_basis = 'section 7 legitimate use'\n", "Section 7 certain legitimate uses\n", ".md"),
    ("DPDP-03", check_privacy_notice, "Privacy notice: personal data and purpose.\n", "href = '/privacy'\n", ".md"),
    ("DPDP-04", check_consent_mechanism, '<input type="checkbox" checked>\n', '<input type="checkbox" checked="false">\n', ".html"),
    ("DPDP-05", check_purpose_limitation, "processing_purpose = 'account support'\n", "# purpose is intentionally not implemented\n", ".py"),
    ("DPDP-06", check_data_minimization, "minimum_required_fields = ['email']\n", "collect_only_required_data = True\n", ".py"),
    ("DPDP-07", check_consent_withdrawal, "def withdraw_consent(user_id):\n    return True\n", "withdrawConsent(user_id)\n", ".py"),
    ("DPDP-08", check_access_rights, "def data_access_request(user_id):\n    return {}\n", "export_user_data(user_id)\n", ".py"),
    ("DPDP-09", check_correction_erasure, "def delete_user(user_id):\n    return True\n", "erasePersonalData(user_id)\n", ".py"),
    ("DPDP-10", check_grievance_nomination, "grievance_officer_contact = 'portal'\n", "nominee details may be updated\n", ".md"),
]


@pytest.mark.parametrize("control_id,check,positive,edge,suffix", CASES)
def test_control_positive_edge_and_line_metadata(
    tmp_path: Path,
    control_id: str,
    check,
    positive: str,
    edge: str,
    suffix: str,
) -> None:
    positive_path = tmp_path / f"positive{suffix}"
    positive_path.write_text(positive, encoding="utf-8")
    result = check(tmp_path)
    found = next(item for item in result if item.file)

    assert found.control_id == control_id
    assert found.file == positive_path.name
    assert found.line == 1
    assert found.status == ("manual_review" if control_id == "DPDP-03" else "warning")
    assert found.confidence in {"low", "medium"}
    assert found.severity == (
        "medium" if control_id == "DPDP-04" and found.title == "Potentially prechecked consent"
        else "informational"
    )

    positive_path.unlink()
    edge_path = tmp_path / f"edge{suffix}"
    edge_path.write_text(edge, encoding="utf-8")
    edge_result = check(tmp_path)
    if control_id == "DPDP-05":
        assert not any(item.file == edge_path.name for item in edge_result)
        return
    edge_found = next(item for item in edge_result if item.file)
    assert edge_found.control_id == control_id
    assert edge_found.file == edge_path.name
    assert edge_found.line == 1
    if control_id == "DPDP-04" and 'checked="false"' in edge:
        assert edge_found.title != "Potentially prechecked consent"
        assert edge_found.confidence == "low"
    if control_id == "DPDP-03" and "/privacy" in edge:
        assert edge_found.status == "manual_review"
        assert edge_found.confidence == "low"


@pytest.mark.parametrize("control_id,check", [(case[0], case[1]) for case in CASES])
def test_control_negative_example_does_not_create_evidence_finding(
    tmp_path: Path, control_id: str, check
) -> None:
    (tmp_path / "unrelated.md").write_text("hello world\n", encoding="utf-8")

    findings = check(tmp_path)

    assert findings
    assert all(item.control_id == control_id for item in findings)
    assert not any(item.file for item in findings)
    assert findings[0].status in {"manual_review", "not_yet_effective"}
    assert findings[0].line == 0


def test_generic_consent_mention_is_not_lawful_basis_evidence(tmp_path: Path) -> None:
    (tmp_path / "signup.html").write_text(
        '<input type="checkbox"> Subscribe to updates with consent.\n', encoding="utf-8"
    )

    findings = check_lawful_basis(tmp_path)

    assert not any(item.file for item in findings)


def test_personal_data_detector_covers_common_field_name_variants(tmp_path: Path) -> None:
    source = tmp_path / "profile.py"
    source.write_text(
        "name = form.get('name')\n"
        "phone_number = form.get('phone')\n"
        "client_ip = request.remote_addr\n"
        "street_address = form.get('address')\n"
        "username = form.get('username')\n",
        encoding="utf-8",
    )

    findings = detect_personal_data(tmp_path)

    assert [item.line for item in findings if item.file == "profile.py"] == [1, 2, 3, 4, 5]

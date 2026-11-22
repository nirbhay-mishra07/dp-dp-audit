import os
from pathlib import Path

import pytest

from core.walker import walk_source_files
from modules.consent_rights import audit


def test_scanner_does_not_execute_target_code_or_export_credentials(tmp_path: Path) -> None:
    code = tmp_path / "app.py"
    code.write_text(
        "raise RuntimeError('must never execute')\n"
        "open('created-by-execution', 'w').write('bad')\n"
        "email = 'alice@example.com'; JWT_SECRET = 'top-secret-value'\n",
        encoding="utf-8",
    )

    findings = audit(str(tmp_path))

    assert not (tmp_path / "created-by-execution").exists()
    report_text = repr(findings)
    assert "alice@example.com" not in report_text
    assert "top-secret-value" not in report_text


def test_html_personal_and_secret_field_values_are_redacted(tmp_path: Path) -> None:
    (tmp_path / "form.html").write_text(
        '<input type="checkbox" name="email" value="private@example.com">\n'
        '<input type="checkbox" name="password" value="private-password">\n'
        '<input type="checkbox" name="apiKey" value="private-api-key">\n', encoding="utf-8"
    )

    findings = audit(str(tmp_path))
    report_text = repr(findings)

    assert "private@example.com" not in report_text
    assert "private-password" not in report_text
    assert "private-api-key" not in report_text


def test_symlink_target_outside_repository_is_not_scanned(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    outside = tmp_path / "outside"
    repo.mkdir()
    outside.mkdir()
    (outside / "external.py").write_text("email = 'external@example.com'\n", encoding="utf-8")
    link = repo / "linked.py"
    try:
        link.symlink_to(outside / "external.py")
    except (OSError, NotImplementedError):
        pytest.skip("This Windows environment does not allow creating symlinks.")

    findings = audit(str(repo))

    assert not any(item["file"] == "linked.py" for item in findings)


def test_large_and_unsupported_files_are_not_scanned(tmp_path: Path) -> None:
    large = tmp_path / "large.py"
    unsupported = tmp_path / "notes.txt"
    large.write_text("email = 'large@example.com'\n" + ("# filler\n" * 100), encoding="utf-8")
    unsupported.write_text("email = 'unsupported@example.com'\n", encoding="utf-8")

    findings = audit(str(tmp_path), {"max_file_size": 32})

    assert not any(item["file"] for item in findings)
    assert all(item["file"] != large.name and item["file"] != unsupported.name for item in findings)


def test_walker_continues_when_a_directory_cannot_be_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    blocked = tmp_path / "blocked"
    blocked.mkdir()
    (blocked / "hidden.py").touch()
    visible = tmp_path / "visible.py"
    visible.touch()
    original_iterdir = Path.iterdir

    def guarded_iterdir(path: Path):
        if path == blocked:
            raise PermissionError("fixture permission error")
        return original_iterdir(path)

    monkeypatch.setattr(Path, "iterdir", guarded_iterdir)

    assert list(walk_source_files(tmp_path)) == [visible]


def test_walker_skips_windows_junctions_and_configured_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    junction = tmp_path / "linked-tree"
    junction.mkdir()
    (junction / "outside.py").touch()
    ignored = tmp_path / "generated"
    ignored.mkdir()
    (ignored / "ignored.py").touch()
    visible = tmp_path / "visible.py"
    visible.touch()
    monkeypatch.setattr(Path, "is_junction", lambda path: path == junction, raising=False)

    assert list(walk_source_files(tmp_path, excluded_directories={"generated"})) == [visible]


def test_nonpositive_file_limit_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="max_file_size must be a positive"):
        audit(str(tmp_path), {"max_file_size": 0})

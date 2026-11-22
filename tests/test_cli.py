import json
import subprocess
import sys
from pathlib import Path


def test_cli_runs_on_empty_directory(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    empty_repo = tmp_path / "empty"
    empty_repo.mkdir()
    report = tmp_path / "report.json"
    result = subprocess.run(
        [sys.executable, str(project_root / "main.py"), str(empty_repo), "--out", str(report)],
        capture_output=True,
        text=True,
        cwd=project_root,
        check=False,
    )

    assert result.returncode == 0
    assert "Files scanned: 0" in result.stdout
    assert "Files skipped: 0" in result.stdout
    assert "Total findings: 10" in result.stdout
    assert len(json.loads(report.read_text(encoding="utf-8"))) == 10
    assert result.stderr == ""

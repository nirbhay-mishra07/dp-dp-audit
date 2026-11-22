from pathlib import Path

from core.walker import walk_source_files


def test_walker_filters_suffixes_and_skips_directories(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").touch()
    (tmp_path / "src" / "notes.txt").touch()
    for excluded in ("node_modules", ".git", ".venv", "dist", "build"):
        excluded_dir = tmp_path / excluded
        excluded_dir.mkdir()
        (excluded_dir / "ignored.js").touch()

    assert list(walk_source_files(tmp_path)) == [tmp_path / "src" / "main.py"]


def test_walker_obeys_file_size_limit(tmp_path: Path) -> None:
    small = tmp_path / "small.py"
    large = tmp_path / "large.py"
    small.write_text("x", encoding="utf-8")
    large.write_text("0123456789", encoding="utf-8")

    assert list(walk_source_files(tmp_path, max_file_size=2)) == [small]

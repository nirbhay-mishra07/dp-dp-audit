"""Source file traversal helpers."""

from collections.abc import Iterator
from pathlib import Path
import stat

SOURCE_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".html", ".css", ".sql", ".prisma", ".yaml", ".yml", ".json", ".md"}
SKIP_DIRECTORIES = {"node_modules", ".git", ".venv", "venv", "__pycache__", "dist", "build", ".mypy_cache", ".pytest_cache", "coverage", "target", "vendor"}


def _is_link_or_junction(path: Path, attributes: int) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    if is_junction is not None and is_junction():
        return True
    reparse_point = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(reparse_point and attributes & reparse_point)


def walk_source_files(
    repo_path: Path,
    max_file_size: int = 1_000_000,
    excluded_directories: set[str] | None = None,
) -> Iterator[Path]:
    """Yield supported, size-limited files and prune excluded directory trees."""
    if not repo_path.is_dir():
        return
    excluded = SKIP_DIRECTORIES if excluded_directories is None else excluded_directories
    pending = [repo_path]
    while pending:
        directory = pending.pop()
        try:
            children = sorted(directory.iterdir())
        except OSError:
            continue
        subdirectories: list[Path] = []
        for path in children:
            try:
                metadata = path.lstat()
            except OSError:
                continue
            attributes = getattr(metadata, "st_file_attributes", 0)
            try:
                if _is_link_or_junction(path, attributes):
                    continue
            except OSError:
                continue
            if path.is_dir():
                if path.name not in excluded:
                    subdirectories.append(path)
                continue
            if path.suffix.lower() in SOURCE_SUFFIXES:
                try:
                    if path.stat().st_size <= max_file_size:
                        yield path
                except OSError:
                    continue
        pending.extend(reversed(subdirectories))

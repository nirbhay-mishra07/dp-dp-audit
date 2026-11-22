"""Static evidence scanner for DPDP Module 1.

Findings describe repository evidence for human review; they are not legal
conclusions. Repository code is read as text and is never executed.
"""

import ast
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from core.finding import Finding
from core.walker import walk_source_files

MODULE_NAME = "Data Collection, Consent & User Rights"
MODULE_ID = "module_1"
CONTROL_IDS = [f"DPDP-{number:02}" for number in range(1, 11)]
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = PROJECT_ROOT / "rules" / "module1_rules.json"
CONTROLS_PATH = PROJECT_ROOT / "config" / "controls.yaml"


def _load_config() -> tuple[dict[str, Any], dict[str, dict[str, str]]]:
    rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    controls_data = yaml.safe_load(CONTROLS_PATH.read_text(encoding="utf-8"))
    controls = {item["id"]: item for item in controls_data["controls"]}
    return rules, controls


def _python_line_candidates(path: Path, lines: list[str]) -> set[int] | None:
    try:
        tree = ast.parse("\n".join(lines), filename=str(path))
    except (SyntaxError, ValueError, TypeError):
        return None
    return {node.lineno for node in ast.walk(tree) if hasattr(node, "lineno")}


def _javascript_line_candidates(path: Path, source: str) -> set[int] | None:
    try:
        import tree_sitter_javascript
        from tree_sitter import Language, Parser

        language = Language(tree_sitter_javascript.language())
        parser = Parser(language)
        tree = parser.parse(source.encode("utf-8"))
        candidates: set[int] = set()

        def collect(node: Any) -> None:
            if node.type not in {"program", "statement_block", "jsx_element", "jsx_fragment"}:
                start = node.start_point.row + 1
                end = node.end_point.row + 1
                candidates.update(range(start, end + 1))
            for child in node.children:
                collect(child)

        collect(tree.root_node)
        return candidates
    except (ImportError, AttributeError, TypeError, ValueError):
        return None


def _candidate_lines(path: Path, source: str) -> set[int] | None:
    lines = source.splitlines()
    suffix = path.suffix.lower()
    if suffix == ".py":
        return _python_line_candidates(path, lines)
    if suffix in {".js", ".jsx", ".ts", ".tsx"}:
        return _javascript_line_candidates(path, source)
    return set(range(1, len(lines) + 1))


def _read_sources(
    repo_path: Path, maximum: int, excluded_directories: set[str]
) -> tuple[list[tuple[Path, str, set[int]]], int]:
    sources: list[tuple[Path, str, set[int]]] = []
    skipped = 0
    for path in walk_source_files(
        repo_path, max_file_size=maximum, excluded_directories=excluded_directories
    ):
        try:
            with path.open("rb") as source_file:
                raw = source_file.read(maximum + 1)
            if len(raw) > maximum:
                skipped += 1
                continue
            if b"\x00" in raw:
                skipped += 1
                continue
            source = raw.decode("utf-8")
            candidates = _candidate_lines(path, source)
            if candidates is None:
                skipped += 1
                continue
            sources.append((path, source, candidates))
        except (OSError, UnicodeError):
            skipped += 1
    return sources, skipped


def _matches_control(repo_path: Path, control_id: str, context: dict[str, Any]) -> list[Finding]:
    rules, controls = _load_config()
    control = rules["controls"][control_id]
    patterns = [re.compile(pattern, re.IGNORECASE) for pattern in control["patterns"]]
    maximum = int(context.get("max_file_size", rules.get("max_file_size", 1_000_000)))
    if maximum < 1:
        raise ValueError("max_file_size must be a positive number of bytes")
    findings: list[Finding] = []
    seen: set[tuple[str, int, str]] = set()
    sources = context.get("_source_cache")
    if sources is None:
        sources, skipped = _read_sources(repo_path, maximum, set(rules.get("excluded_directories", [])))
    else:
        skipped = context.get("_files_skipped", 0)
    for path, source, candidates in sources:
        for line_number, line in enumerate(source.splitlines(), start=1):
            if line_number not in candidates:
                continue
            matched_terms = list(dict.fromkeys(
                match.group(0) for pattern in patterns if (match := pattern.search(line)) is not None
            ))
            if not matched_terms:
                continue
            relative = path.relative_to(repo_path).as_posix()
            is_prechecked = control_id == "DPDP-04" and bool(re.search(
                r"(?i)\bdefaultchecked\s*=\s*(?:\{\s*)?(?:['\"])?true(?:['\"])?(?:\s*\})?|"
                r"<input\b[^>]*\btype\s*=\s*['\"]?checkbox\b[^>]*\bchecked(?![\w-])"
                r"(?:\s*=\s*(?:['\"]?true['\"]?|\{\s*true\s*\}))?(?=\s|/?>)", line
            ))
            if is_prechecked:
                matched_terms.append("preselected checkbox")
            evidence = "Matched indicator(s): " + ", ".join(matched_terms)
            key = (relative, line_number, evidence)
            if key in seen:
                continue
            seen.add(key)
            findings.append(Finding(
                control_id=control_id,
                status="warning",
                severity="medium" if is_prechecked else "informational",
                title="Potentially prechecked consent" if is_prechecked else control["title"],
                description=("A consent control appears preselected; review its default state and user choice." if is_prechecked
                             else "A code or documentation pattern related to this control was found. This is evidence for review, not a compliance conclusion."),
                file=relative,
                line=line_number,
                evidence=evidence,
                recommendation="Review the surrounding flow, purpose, context, and applicable legal requirements; do not treat this pattern alone as proof of compliance or a violation.",
                confidence="medium" if is_prechecked else "low",
                legal_reference=controls.get(control_id, {}).get("legal_ref", ""),
            ))

    if not findings:
        effective_date = date.fromisoformat(controls.get(control_id, {}).get("effective_date", "9999-12-31"))
        future = date.today() < effective_date
        findings.append(Finding(
            control_id=control_id,
            status="not_yet_effective" if future else "manual_review",
            severity="informational",
            title="No automated evidence found",
            description="The scanner found no configured pattern for this control. Absence of a pattern is not evidence that a required process is absent.",
            file="",
            line=0,
            evidence="",
            recommendation="Review repository behavior, operational processes, and applicable scope manually.",
            confidence="low",
            legal_reference=controls.get(control_id, {}).get("legal_ref", ""),
        ))
    return findings


def detect_personal_data(repo_path: Path, context: dict[str, Any] | None = None) -> list[Finding]:
    return _matches_control(repo_path, "DPDP-01", context or {})


def check_lawful_basis(repo_path: Path, context: dict[str, Any] | None = None) -> list[Finding]:
    return _matches_control(repo_path, "DPDP-02", context or {})


def check_privacy_notice(repo_path: Path, context: dict[str, Any] | None = None) -> list[Finding]:
    options = context or {}
    evidence = _matches_control(repo_path, "DPDP-03", options)
    located = [item for item in evidence if item.file]
    if not located:
        return evidence

    rules, controls = _load_config()
    patterns = {
        name: [re.compile(pattern, re.IGNORECASE) for pattern in values]
        for name, values in rules["controls"]["DPDP-03"]["notice_topics"].items()
    }
    cached_sources = options.get("_source_cache")
    source_by_path = {
        path.relative_to(repo_path).as_posix(): source
        for path, source, _ in cached_sources
    } if cached_sources is not None else {}
    findings: list[Finding] = []
    for relative in sorted({item.file for item in located}):
        source = source_by_path.get(relative)
        if source is None:
            try:
                source = (repo_path / Path(relative)).read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
        present = [name for name, checks in patterns.items() if any(pattern.search(source) for pattern in checks)]
        absent = [name for name in patterns if name not in present]
        lines = [item.line for item in located if item.file == relative]
        findings.append(Finding(
            control_id="DPDP-03",
            status="manual_review",
            severity="informational",
            title="Privacy notice topic review",
            description=(f"Notice-topic markers present: {', '.join(present) or 'none'}; absent: "
                         f"{', '.join(absent) or 'none'}. These text markers do not establish legal adequacy."),
            file=relative,
            line=min(lines),
            evidence="Privacy-notice marker and topic labels were checked; source values are omitted.",
            recommendation="Review the full notice for clear, specific information and confirm it matches actual processing and available user channels.",
            confidence="low",
            legal_reference=controls["DPDP-03"]["legal_ref"],
        ))
    return findings or evidence


def check_consent_mechanism(repo_path: Path, context: dict[str, Any] | None = None) -> list[Finding]:
    return _matches_control(repo_path, "DPDP-04", context or {})


def check_purpose_limitation(repo_path: Path, context: dict[str, Any] | None = None) -> list[Finding]:
    return _matches_control(repo_path, "DPDP-05", context or {})


def check_data_minimization(repo_path: Path, context: dict[str, Any] | None = None) -> list[Finding]:
    return _matches_control(repo_path, "DPDP-06", context or {})


def check_consent_withdrawal(repo_path: Path, context: dict[str, Any] | None = None) -> list[Finding]:
    return _matches_control(repo_path, "DPDP-07", context or {})


def check_access_rights(repo_path: Path, context: dict[str, Any] | None = None) -> list[Finding]:
    return _matches_control(repo_path, "DPDP-08", context or {})


def check_correction_erasure(repo_path: Path, context: dict[str, Any] | None = None) -> list[Finding]:
    return _matches_control(repo_path, "DPDP-09", context or {})


def check_grievance_nomination(repo_path: Path, context: dict[str, Any] | None = None) -> list[Finding]:
    return _matches_control(repo_path, "DPDP-10", context or {})


_CHECKS = [detect_personal_data, check_lawful_basis, check_privacy_notice, check_consent_mechanism,
           check_purpose_limitation, check_data_minimization, check_consent_withdrawal,
           check_access_rights, check_correction_erasure, check_grievance_nomination]


def audit(repo_path: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Audit a repository and return findings in the shared JSON schema."""
    root = Path(repo_path).expanduser().resolve()
    options = dict(context or {})
    if not root.is_dir():
        raise ValueError(f"Repository path is not a directory: {root}")
    rules, _ = _load_config()
    maximum = int(options.get("max_file_size", rules.get("max_file_size", 1_000_000)))
    if maximum < 1:
        raise ValueError("max_file_size must be a positive number of bytes")
    options["_source_cache"], options["_files_skipped"] = _read_sources(
        root, maximum, set(rules.get("excluded_directories", []))
    )
    findings = [finding for check in _CHECKS for finding in check(root, options)]
    if context is not None:
        context["files_scanned"] = len(options["_source_cache"])
        context["files_skipped"] = options["_files_skipped"]
    return [finding.to_dict() for finding in findings]

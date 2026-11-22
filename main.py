"""Command line interface for the Data Collection, Consent & User Rights auditor."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Sequence

from modules.consent_rights import audit


def format_summary(findings: list[dict], files_scanned: int, files_skipped: int) -> str:
    by_control: dict[str, int] = defaultdict(int)
    for finding in findings:
        by_control[finding["control_id"]] += 1
    severity = Counter(item["severity"] for item in findings)
    lines = [f"Files scanned: {files_scanned}", f"Files skipped: {files_skipped}",
             f"Total findings: {len(findings)}", "", "Findings by control:"]
    lines.extend(f"  {control}: {count}" for control, count in sorted(by_control.items()))
    lines.extend(["", "Severity summary:"])
    lines.extend(f"  {name}: {count}" for name, count in sorted(severity.items()))
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit repository evidence for DPDP controls 01–10.")
    parser.add_argument("repo_path", type=Path)
    parser.add_argument("--out", type=Path, help="Optional JSON report path (default: reports/module1_report.json).")
    parser.add_argument("--max-file-size", type=int, help="Maximum file size in bytes to scan.")
    args = parser.parse_args(argv)
    context: dict = {}
    if args.max_file_size is not None:
        context["max_file_size"] = args.max_file_size
    try:
        findings = audit(str(args.repo_path), context)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    report_path = args.out or Path(__file__).resolve().parent / "reports" / "module1_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(findings, indent=2) + "\n", encoding="utf-8")
    print(format_summary(findings, context.get("files_scanned", 0), context.get("files_skipped", 0)))
    print(f"\nJSON report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

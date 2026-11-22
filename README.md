# DPDP Compliance Auditor — Module 1

Module 1 scans repository source and documentation for reviewable evidence related to personal data collection, consent, notices, purpose documentation, and data principal rights. It does not execute target code and it cannot determine legal compliance.

## Install

Use Python 3.11 or newer in a virtual environment, then install the dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Run

```powershell
python main.py C:\path\to\repository
```

The CLI prints file and finding totals, groups findings by control and severity, and writes JSON to `reports/module1_report.json`. Use `--out C:\path\to\report.json` to select another report path and `--max-file-size 500000` to change the per-file size limit.

Integrations can call `modules.consent_rights.audit(repo_path: str, context: dict | None = None) -> list[dict]`. The optional context can provide `max_file_size`; scan totals are added to the same dictionary. Module metadata is exposed as `MODULE_NAME`, `MODULE_ID`, and `CONTROL_IDS`.

## Supported files and controls

Python files are parsed with `ast`; JavaScript, JSX, and TypeScript use tree-sitter. Java, HTML, CSS, JSON, YAML, SQL, and Markdown use configured text patterns. The walker skips dependency, build, cache, and version-control folders, ignores oversized files, and skips unreadable, binary, or unparseable files. The CLI reports skipped-file totals.

The scanner covers DPDP-01 personal data discovery, DPDP-02 processing basis, DPDP-03 privacy notices, DPDP-04 consent mechanisms, DPDP-05 purpose limitation, DPDP-06 data minimization, DPDP-07 consent withdrawal, DPDP-08 access requests, DPDP-09 correction and erasure, and DPDP-10 grievances and nomination. For notices, it reports text signals for personal data, purpose, withdrawal, rights, grievances, and contact details; this is a review aid, not an adequacy determination. Pattern rules are in `rules/module1_rules.json`; legal references and commencement notes are in `config/controls.yaml`.

## Reading findings

Matches are signals for human review. A field such as `email` does not prove a violation, and a route or a privacy-policy keyword does not prove that a notice is adequate. Missing pattern matches are reported as `manual_review` or `not_yet_effective`, never as proof of compliance. The commencement schedule is phased: Rule 4, Section 6(9), and Section 27(1)(d) took effect on 13 November 2026; the main provisions relevant to these controls are scheduled for 13 May 2027. Section 7 provides certain legitimate uses, so the scanner does not assume every processing activity requires consent. See the [Act commencement notification](https://egazette.gov.in/WriteReadData/2025/267647.pdf) and the [DPDP Rules, 2025 notification](https://egazette.gov.in/WriteReadData/2025/267650.pdf).

Sample repositories under `tests/fixtures/sample_repositories/` are test fixtures, not legal benchmarks. For example, the sample containing a privacy notice and `withdraw_consent` creates evidence findings; a sample with `checked = True` produces a consent warning. Neither establishes the repository's legal status.

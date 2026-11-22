# Project rules

- Use Python 3.11+, type hints, dataclasses, and pytest. Avoid heavy frameworks.
- For Python targets, use `ast`. For JavaScript, JSX, and TypeScript targets, use tree-sitter. Use regex only for config, SQL, and text fallback.
- Never claim "compliant". Finding statuses are `pass`, `fail`, `warning`, `manual_review`, `not_applicable`, or `not_yet_effective`. Severity is `critical`, `high`, `medium`, `low`, or `informational`; confidence is `high`, `medium`, or `low`.
- A route such as `/privacy` is evidence of existence, not proof of legal adequacy. Confidence based on a route name alone must never exceed 0.6.
- Common schema (do not change fields without asking): `Finding(control_id, status, severity, title, description, file, line, evidence, recommendation, confidence, legal_reference)`.
- Each detector exposes `run(repo_path: Path) -> list[Finding]`.
- Detectors are independent modules; controls map onto detector outputs.
- Legal references (sections/rules) belong in `config/controls.yaml`, never hardcoded in code.
- Module 1 entry point: `modules.consent_rights.audit(repo_path: str, context: dict | None = None) -> list[dict]`.
- Every detector needs tests against fixtures in `tests/fixtures/`.
- Keep functions small; avoid dead code and speculative features.

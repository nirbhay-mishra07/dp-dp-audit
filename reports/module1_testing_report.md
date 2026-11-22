# Module 1 QA and Security Test Report

**Run date:** 22 November 2026  
**Final assessment:** **PASS WITH WARNINGS**

## 1. Project overview

Module 1 scans repository source and documentation for evidence related to DPDP-01 through DPDP-10. The public interface `modules.consent_rights.audit(repo_path, context)` returns dictionaries in the shared finding schema. The scanner does not execute target code and does not make a legal compliance determination.

This review inspected the existing implementation before changing it. Fixes below are limited to concrete detector, evidence-handling, traversal, and test-runner defects found during testing. No Module 2 or Module 3 code or imports were added.

Commencement notes were checked against the official [Act commencement notification, G.S.R. 843(E)](https://egazette.gov.in/WriteReadData/2025/267647.pdf) and [DPDP Rules notification, G.S.R. 846(E)](https://egazette.gov.in/WriteReadData/2025/267650.pdf).

## 2. Environment verification

| Check | Result |
|---|---|
| Python | Python 3.14.7; satisfies the stated Python 3.11+ requirement, but is not the requested baseline version |
| pytest | 9.2.0 installed in `.venv` |
| PyYAML | Installed |
| tree-sitter | Installed |
| tree-sitter-javascript | **Missing**; its source build failed on this MSYS Python because GCC was passed incompatible `/std:c11` and `/utf-8` flags |
| `pip check` | No broken installed-package requirements reported |
| Project import smoke test | Passed, including `main`, `audit`, core modules, legacy detector stubs, and `modules.consent_rights` |
| Import from another working directory | Passed when the project was placed on `sys.path`; config paths resolve relative to the module |
| `compileall` | Passed |
| Required project files/references | Present after correcting the stale `AGENTS.md` schema reference and wiring configured exclusions into the walker |
| Module 2/3 dependency check | No Module 2 or Module 3 imports or dependencies found |

`pytest` was not on the unactivated shell `PATH`. After activating the project virtual environment, the requested `pytest -v` command ran successfully. A `pytest.ini` setting now makes the repository root importable by the virtual environment’s standalone pytest launcher as well.

The JavaScript grammar package remains missing. JavaScript, JSX, and TypeScript files are safely reported as skipped rather than silently parsed with regex; consequently that language coverage is not verified in this environment.

## 3. Tests executed

- Full suite: `pytest -v` from the activated project virtual environment.
- Positive, negative, and edge-case cases for each of the ten controls, including control ID, relative file path, line, status, and confidence checks.
- Existing compliant and incomplete sample repositories.
- A separate synthetic realistic repository containing Python, HTML, SQL, Markdown, and TSX application files.
- Empty repository CLI run and JSON output validation.
- Unsupported `.txt`, malformed Python, binary content, configured file-size limit, and unreadable-directory behavior.
- Security checks for accidental code execution, credential and personal-value disclosure, duplicate findings, symlink/junction handling, and traversal.
- Import smoke test, independent module import, `compileall`, and `pip check`.

### Final automated test result

```text
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\nirbhay\dpdp-audit
configfile: pytest.ini
collecting ... collected 44 items

43 passed, 1 skipped in 0.81s
```

The single skipped test attempts to create a real Windows symlink to an outside directory. This environment denies symlink creation. The walker’s junction/reparse-point branch is covered by a simulated junction test, but actual OS symlink traversal could not be exercised here.

The realistic fixture scan processed 7 supported files and skipped its TSX file because the JavaScript grammar package is unavailable. It produced at least one review signal for every control. Its `.txt` file was ignored as intended.

## 4. Results for each control

| Control | Positive, negative, and edge results | Finding behavior and remaining risk |
|---|---|---|
| **DPDP-01 Personal Data Discovery** | Positive email/name fields passed; unrelated text did not match; uppercase and common variants such as `phone_number`, `client_ip`, `street_address`, and `username` passed. | Match: `warning`, informational severity, low confidence. Repeated uses of identifiers such as `user_id` can generate noisy findings; the title now says “field or identifier” to avoid overstating what was found. |
| **DPDP-02 Lawful Processing Basis** | Declared lawful basis and Section 7 / certain legitimate-use text passed; unrelated text did not match; a generic mention of “consent” alone is explicitly negative. | Match: `warning`, low confidence. A Section 7 citation in documentation may be a general reference rather than a basis actually used for a processing operation. |
| **DPDP-03 Privacy Notices** | Privacy notice text passed; unrelated text did not match; `/privacy` route passed as existence evidence and generated a manual review finding. | Notice and route results are `manual_review`, informational, low confidence. Topic markers are reported as present or absent; they do not determine notice adequacy. Route-only evidence remains low confidence. |
| **DPDP-04 Valid Consent** | Consent implementation and checkbox examples passed; a prechecked checkbox is detected; `checked="false"` is not labeled prechecked. | A detected prechecked checkbox is a medium-severity warning with medium confidence; other mechanism signals are informational/low. Generic consent prose is no longer treated as an implementation. |
| **DPDP-05 Purpose Limitation** | A stated processing purpose passed; unrelated text did not match; Python comment-only mention was correctly ignored by AST parsing. | Match: `warning`, informational, low confidence. The word “purpose” in a function parameter or general text can still be noisy and does not prove a purpose is specified for each data use. |
| **DPDP-06 Data Minimization** | `minimum_required_fields`, “minimum required data,” and `collect_only_required_data` examples passed; unrelated text did not match. | Match: `warning`, informational, low confidence. The scanner finds explicit minimization signals; it does not determine whether every collected field is necessary. |
| **DPDP-07 Consent Withdrawal** | `withdraw_consent` and camel-case `withdrawConsent` examples passed; unrelated text did not match. | Match: `warning`, informational, low confidence. A named function does not prove the withdrawal flow is reachable or effective. |
| **DPDP-08 Right of Access** | `data_access_request` and `export_user_data` examples passed; unrelated text did not match. | Match: `warning`, informational, low confidence. The scanner does not verify that a request returns complete information or is operationally available. |
| **DPDP-09 Correction and Erasure** | `delete_user`, `delete_account`, `erasePersonalData`, and correction examples passed; unrelated text did not match. | Match: `warning`, informational, low confidence. Common `remove_user`, `remove_profile`, and selected SQL delete patterns are recognized; indirect or application-specific deletion behavior may be missed. |
| **DPDP-10 Grievances and Nomination** | Grievance-contact and nominee examples passed; unrelated text did not match; `grievance_officer_contact` naming is recognized. | Match: `warning`, informational, low confidence. A contact label or nominee field does not prove a functioning grievance or nomination process. |

For no-match cases, the scanner returns a location-free `not_yet_effective` or `manual_review` item according to configured dates. It does not emit a `pass` or `fail` compliance conclusion.

## 5. Passed tests

- All ten controls have positive, negative, and edge-case checks.
- Finding dictionaries contain all required shared-schema keys and valid generated status/severity/confidence values.
- Paths and line numbers are checked for positive detections.
- Empty-target CLI run writes a valid JSON report; the default report path is `reports/module1_report.json`.
- The realistic repository produced evidence for all ten controls. The unsupported `.txt` file produced no finding.
- The scanner did not execute a target file containing a deliberate runtime exception and file-writing statement.
- Secret-like values and personal values adjacent to matched indicators are not included in exported evidence.
- Malformed Python and binary files are skipped without a crash; unreadable directory traversal was simulated and passed.
- Duplicate matches on the same source line are collapsed.
- Large files over the configured limit are not read into scan findings; non-positive limits are rejected.
- Junction detection and custom excluded-directory handling passed.

## 6. Failed tests

**Final run: none.** The final suite completed with 43 passing tests and one environment-limited symlink test skipped.

During QA, the new matrix initially exposed detector defects and one test-collection parameterization mistake. The test harness was corrected; the detector issues are listed below and covered by the final passing suite.

## 7. Bugs discovered and fixed

1. **Overbroad lawful-basis evidence:** any occurrence of “consent,” including a prechecked checkbox, could be reported as evidence of a lawful basis. DPDP-02 now looks for explicit basis language and selected Section 7 signals; generic consent mentions do not match.
2. **False prechecked-checkbox warning:** `checked="false"` was classified as prechecked. The check now distinguishes false values from a boolean checked attribute or explicit true value.
3. **Consent prose mistaken for a mechanism:** generic “consent” prose was reported as a UI mechanism. DPDP-04 now looks for checkbox, opt-in, or implementation-oriented indicators.
4. **Missed common patterns:** added common name/IP/phone variants, Section 7 wording, minimum-required-data wording, camel-case withdrawal/erasure names, user deletion names, grievance contact names, and privacy routes.
5. **Evidence could expose source values:** reports previously included the whole matching line. Findings now export only matched indicator text and line/path metadata, omitting source-line values entirely.
6. **Malformed Python counted as scanned:** an AST parse error yielded no candidate lines but was counted as a successful scan. Such files are now counted as skipped.
7. **Configured exclusions were ignored:** the exclusions in `module1_rules.json` were not passed into the walker. The scanner now uses them.
8. **Deep-tree recursion risk:** replaced recursive directory traversal with an iterative traversal.
9. **Junction traversal risk:** the walker now checks symbolic links, junctions, and Windows reparse points before descending.
10. **Project guidance mismatch:** `AGENTS.md` described the previous finding schema. It now documents the approved shared schema and current statuses.
11. **Standalone pytest import failure:** the virtualenv pytest executable did not import root packages in this MSYS environment. Added `pytest.ini` with the project-root Python path; `pytest -v` now passes after environment activation.

## 8. False-positive analysis

- DPDP-01 may report multiple lines where a personal identifier such as `user_id` is referenced, not only where it is declared. Its low confidence and informational severity reflect that limitation.
- DPDP-02 can match a law or Section 7 reference that is not tied to an actual processing operation.
- DPDP-03 treats a `/privacy` route as existence evidence only and sends it to manual review. Text markers in a notice may be incomplete or stale.
- DPDP-05 may match a general purpose parameter or documentation statement without proving purpose limitation.
- DPDP-06 and DPDP-10 can detect labels or documentation that do not correspond to effective behavior.
- No generated finding is a legal violation or compliance conclusion. The scanner does not emit `fail` based on keyword presence.

## 9. False-negative analysis

- JavaScript, JSX, and TypeScript files are skipped in this environment because `tree-sitter-javascript` is missing. The realistic fixture’s TSX checkbox therefore was not assessed.
- Pattern matching cannot cover every project naming convention, alias, dynamic route, ORM abstraction, or behavior spread across files.
- Python files that cannot be parsed by `ast` are skipped rather than regex-scanned; signals in malformed files may be missed.
- Custom or indirect access, correction, deletion, withdrawal, and grievance workflows may not use configured keywords.
- The scanner does not evaluate reachability, runtime configuration, backend authorization, storage behavior, or whether the user-facing feature actually works.

## 10. Security issues and checks

- **Code execution:** none observed; the scanner reads file bytes and parses text/AST/tree-sitter only. A deliberate side-effect fixture did not run.
- **Secrets and personal values:** raw source lines are no longer exported. Evidence contains matched indicator labels only. Tests cover email, name, password, API-key-like values, and JWT secret patterns adjacent to findings.
- **Malformed/binary files:** safely skipped; malformed Python is now counted as skipped.
- **Symlinks/junctions:** junction/reparse traversal is tested through a simulated junction branch. Real symlink creation was denied by this environment, so outside-target behavior remains OS-unverified.
- **Large files:** the walker filters by size, and the reader is bounded to `max_file_size + 1` bytes to avoid an unbounded read if a file changes after the stat check.
- **Unreadable directories:** `PermissionError` behavior was simulated; traversal continued with accessible siblings.
- **Duplicates:** identical same-line control indicators are deduplicated.
- **Unsupported files:** unsupported extensions are ignored.

## 11. Remaining limitations

- Installable `tree-sitter-javascript` support must be verified in a compatible Python/Windows toolchain before relying on JavaScript/TypeScript coverage. The current Python is MSYS Python 3.14.7, and the dependency build fails on incompatible compiler flags.
- One real Windows symlink test is skipped because link creation is blocked. Junction traversal is covered by a simulated branch test.
- The realistic repository is a synthetic application fixture, not an external production repository; no external repository was supplied for this task.
- The scanner is heuristic and deliberately low-confidence. It does not establish whether a law applies to a particular organization, processing purpose, exemption, or data principal.
- The effective-date setting is control-level. Some provisions are phased or partially commenced; detailed provision-by-provision legal interpretation remains outside this scanner.

## 12. Final readiness assessment

**PASS WITH WARNINGS.** Core integration, all ten control interfaces, shared-schema output, CLI reporting, malformed/binary handling, sensitive-evidence minimization, and the final automated suite work in the tested environment. Integrate only with the known language-coverage caveat: JavaScript/TypeScript files are skipped until the grammar dependency installs successfully. Keep human review in the loop; these results establish software behavior, not DPDP legal compliance.

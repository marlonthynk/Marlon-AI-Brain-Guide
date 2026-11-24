# Validation record

Release candidate prepared 24 November 2026. This record is updated with actual checks before release. Original live integration evidence is in [case study](case-study.md); new reader acceptance instructions are in [verification](verification.md).

The new companion is tested in isolated helper state and fictional projects. It does not inherit the author's live Brain, automation, private queue or approvals. Local-only reporting is the default; no test emails or schedules are created by helper tests.

## Observed checks on 24 November 2026

- Python 3.12.13 helper environment created separately; pinned PyYAML 6.0.3 installed successfully. No Basic Memory or AI SDK dependency is needed for the helper suite.
- 31 tests pass: the original 20 queue/archive checks plus custom project/report/snapshot identity, local-only reporting, config/path validation, custom weekday/time, Tokyo year/month routing, New York DST, no retroactive email on enable, safe config generation, standalone round-trip with spaces and extraction tamper/traversal rejection.
- The isolated fictional demo passed proposal retention without note changes, idle repeat, exact snapshot/restore and rejection of a concurrent edit. It sent no email and created no schedule.
- The generated standalone guide extracted with verified hashes and passed the helper suite and release checks without requiring a Git checkout. Source is maintained once; the generated file is not hand-edited.
- A separate local Basic Memory 1.0.0 stdio MCP trial used a fresh isolated configuration/database and custom project, leaving the live Brain untouched. Actual write/read/edit, stale-checksum rejection, a move preserving full content/checksum/permalink and graph target, and retrieval after direct file edit plus indexing passed. This used the installed MCP client environment, separately from the minimal helper environment.
- The MCP trial exposed a bounded context-query timeframe; the protocol now explicitly respects installed tool limits and reads older link targets directly where necessary. No broad date-range claim is made.
- Skill structure validation, public-source identity/credential-pattern scans, JSON parsing and local Markdown links/anchors pass. The companion starts with new history rather than the original installation commits.

## Checks that remain environment-specific

CI is configured for macOS and Linux helper tests on Python 3.10/3.12; remote results must be inspected after pushing. Linux helper CI does not establish Linux desktop support. Windows is unsupported.

The original cross-harness desktop results are historical evidence, not a fresh installation on another person's Mac. Each reader must verify sign-in/trust, their actual interface and one scheduled invocation using the provided acceptance prompts. No new production scheduler, email provider connection or email send was created to test this release. Outlook and non-Codex schedulers require their own end-to-end checks. Physical sleep/offline fault injection and independent off-device snapshots remain outside this verification.

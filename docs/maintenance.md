# Reviews, schedules and weekly archives

The core Brain works without maintenance. Add this workflow after read/write/search and cross-harness checks pass. It processes captured notes, not hidden chat histories. Use one private configuration and state directory per Brain, and one scheduled runtime. Manual and scheduled runs invoke the same [run prompt](../prompts/run-review.md).

## Configuration

Create the Brain folders first. Create an isolated helper environment using the README commands. Then have your assistant discover and confirm the actual paths and generate a private config. The config generator expands explicit `~` CLI paths; hand-written JSON paths must be absolute. It refuses existing configs and does not register projects, install skills, create schedules or send email.

Example for a new installation (replace paths and project with your choices):

```sh
.venv/bin/python scripts/configure.py init \
  --config "$HOME/.config/shared-ai-brain/worker.json" \
  --project personal-brain \
  --root "$HOME/Documents/MyVault/AI-Brain" \
  --state-dir "$HOME/.local/state/shared-ai-brain" \
  --backup-dir "$HOME/.local/share/shared-ai-brain-backups" \
  --synced-vault "$HOME/Documents/MyVault" \
  --timezone Europe/London

.venv/bin/python scripts/configure.py check \
  --config "$HOME/.config/shared-ai-brain/worker.json"
```

This starts with local reports and archive previews disabled. To opt into archive previews when first creating the config, also supply `--archive-start FUTURE-LOCAL-DATE-TIME --archive-day Friday --archive-time 09:00`. Use an ISO date/time such as `2027-01-08T09:00:00`, choosing your actual future date. This example date is not a default. The first due slot is the selected weekday/time on or after start_at. A single worker checks it at invocation time; choose a review schedule at least weekly so due archive slots are eventually checked.

To add email after explicit consent, use `--enable-email --provider gmail --recipient YOUR_CONFIRMED_ADDRESS` (or outlook), and optionally `--thread-url YOUR_ACTUAL_REFERENCE` when generating a new config. For an existing config, have the assistant show and apply a narrow reviewed JSON edit, then revalidate; never replace current state or rerun init over it. Test the actual connected account, address, reservation/send/read-back flow before scheduling. Provider selection in JSON does not connect/authenticate email.

`config/worker.example.json` documents the fields but is deliberately not runnable unchanged. `project` is a local project slug and also the permalink prefix expected for reports. Verify actual Basic Memory routing/permalinks before use. State is bound to that project and root; moving an installation or changing identity needs an explicit migration, not a silent config edit.

Keep config, state, drafts and backups outside the synced vault. Backups must also be separate from state/Brain. Optional `archive.support_paths` names exact worker, state, config, approved import-ledger and schedule-export paths to snapshot. Review each path and ensure it contains no credentials. Do not snapshot a parent directory containing backups or broad harness configuration. Missing support paths fail snapshots; do not claim they were protected. This repo is not automatically included unless configured.

## Install the skill

Keep this checkout in a stable local location or copy the reviewed `skills/ai-brain-consolidate` folder to your harness's supported skill directory. Preserve its scripts/references together. Back up any existing installation first; do not overwrite an unrelated skill with the same name. Record the absolute skill, Python and config paths. Do not edit plugin-managed Basic Memory files.

The installed prompt must supply those actual paths; shell aliases, relative paths and environment variables may be unavailable to scheduled GUI processes. Do not assume every harness recognises a Codex skill directory. Other capable harnesses can read the same Markdown instructions as files and invoke the helpers. [Harness adapters](harnesses/README.md).

## Manual review before scheduling

1. Run helper tests and [the isolated walkthrough](verification.md). Verify project/root agreement through Basic Memory before any live run.
2. Give the assistant [run-review.md](../prompts/run-review.md) with the confirmed absolute Python, skill and config paths. It reads changed revisions through MCP, compares existing topics, shows proposed edits, writes a concise operational report and commits only reviewed hashes. Local proposal drafts live outside the Brain.
3. Inspect the report and exact proposals. A repeat run should be idle and preserve sources. Approve a small displayed change only when useful; [apply-approved-change.md](../prompts/apply-approved-change.md) guards its revision and verifies the result.
4. If email is selected, test it separately with non-sensitive content and inspect delivery evidence. If MCP is unavailable, leave revisions pending and report the failure; don't fall back to direct Markdown report writes.

## Choose a cadence and runtime

Use [create-schedule.md](../prompts/create-schedule.md). A weekly review is a starting option; daily review uses the same run prompt. Ask for day/time, an IANA timezone, runtime and notification choice. Keep scheduling itself in the selected harness's supported scheduler. Python queue/archive scripts are not schedulers or autonomous agents.

The scheduled task must run an AI harness with access to the same Mac files and Basic Memory tools (plus email if selected). A cloud-only scheduled prompt may have no local access even if interactive chat does. If scheduling is unsupported, use the manual prompt or choose a supported runtime with the user; do not invent a background service or silently install cron/launchd. Never create a duplicate worker against the same state.

Verify saved task status, effective prompt, local timezone, frequency and target. Then verify an actual invocation can access the project and write/read a report; a configured Active card alone is insufficient. The schedule record should contain the actual paths and relevant task reference, outside the public repo. The original build's tested scheduler was Codex desktop; other scheduler adapters are capability guidance requiring their own test.

## Weekly archiving

Archiving is optional and runs after review. It checks seven unchanged days, current-revision review, issue resolution and completion evidence. An old checkpoint for unfinished work stays in Inbox. Searchable originals move unchanged to Archive/Captures or Archive/Sessions by year/month in the configured timezone. Preview does not promote a note or approve a proposed fact.

Enable stable permalinks on move using the installed Basic Memory configuration (`update_permalinks_on_move: false` in the original build). Verify it with a fictional fixture move/return. Take and verify snapshots, then restore one into an isolated absent destination. Preview the first real eligible batch; approve only exact candidates/revisions. After that batch verifies, decide separately whether to allow future qualifying moves. Leave automatic mode off until then.

## Failure and recovery

Queue leases/locks prevent overlapping workers; revision guards reject concurrent edits. A missed run leaves hashes pending, with no last-24-hours cutoff. Batches stop at four groups of 25 or 45 minutes; leave remaining work for a later invocation. Interrupted archive plans keep their own lease and recovery procedure, never an ordinary abort. Email reservations must be reconciled against Sent before a possible resend.

The Mac/runtime/network/connectors must be available. There is no promise of immediate wake execution or offline email alerting. Inspect local `queue.py --config CONFIG status`, reports and scheduled-run history if results are missing. [Run protocol](../skills/ai-brain-consolidate/references/run-protocol.md) · [Archive protocol](../skills/ai-brain-consolidate/references/archive-protocol.md).

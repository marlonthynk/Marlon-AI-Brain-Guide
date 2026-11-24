# Weekly archive and snapshot recovery

Use `PYTHON /absolute/worker/scripts/archive.py --config CONFIG SUBCOMMAND`. These helpers plan, guard and verify; Basic Memory MCP performs actual live note moves. Configuration controls the weekly weekday/time, IANA timezone and first eligible local date. The folder month uses that same timezone. A missed slot is checked on the next successful invocation; historical weeks are not replayed as duplicate moves.

## Due check and preview

1. After review, run `plan`. disabled/not_due means check any existing email outbox and finish. busy means stop. Do not force a recurring pass or reset its due date. `--force-preview` is for an explicit isolated/manual preview, not a scheduled bypass.
2. Take `snapshot --label 'archive review'` and require verified true. Snapshots include the Brain plus only configured support paths, with manifests; they exclude Basic Memory index/cache unless explicitly added (not recommended). Never include broad harness settings or credentials. Keep state/config/backups outside the synced vault and avoid recursively including backup directories. A failure blocks moves and requires notification/reporting.
3. Eligibility requires seven unchanged days, current raw revision reviewed, all related issues resolved, and documented completion. For missing clearance, read source/current review outcomes and relevant curated notes through MCP. Useful content must already be represented, applied and read back after explicit approval, or explicitly dismissed. Review/email alone is not approval. Keep ambiguous work in Inbox. Never close the latest handoff of unfinished work because it is old or a newer note exists.
4. When actual evidence establishes completion, `clear --path PROJECT-RELATIVE-PATH --reason EVIDENCE`; sessions also require `--session-closed-evidence ACTUAL-REFERENCE`. The helper binds clearance to the source hash; do not edit immutable checkpoints to close them. Regenerate `plan` after clearances, and use the latest plan.
5. Write one operational `Archive Review - PLAN-ID` through MCP under `Reviews/Archive Reviews/`; search before recreating after a retry. Include ID/date, exact candidates/revisions/source/destination/permalinks, eligibility/completion evidence, retained count/reasons and verified snapshot ID. Do not copy raw sources. Read back; `record-preview --plan ID --report ACTUAL-PERMALINK` (configured project plus `/reviews/`). A nonempty preview creates a local approval item, with optional email. An empty pass sends no email.

## First real batch and future consent

Stop after preview until the user approves those exact candidates and revisions. Silence is not approval. A fictional fixture or permission to set up maintenance is not a real batch approval. Display the proposed batch in the harness output or provide its exact accessible report.

After an explicitly approved real batch is completed and verified, ask whether to enable future routine qualifying moves. Only that further explicit consent allows `enable --approval-reference ACTUAL-USER-REFERENCE`. Changing config archive.enabled enables preview/due checks, not automatic moves. Never fabricate an approval reference. Curated rewrites still require their own approval.

## Execute an approved plan

1. `claim --plan ID --approval-reference ACTUAL-REFERENCE`; in already consented automatic mode the reference may be omitted. This checks eligibility/collisions and takes a new verified pre-move snapshot. A stale plan needs new review/approval; do not override it. At most 25 moves and the invocation's 45-minute budget.
2. Each pending item: `check-item --plan ID --index N`. already_moved means read/verify and skip the move. ready_for_mcp_move requires a fresh MCP read with unchanged raw checksum/permalink and the exact destination. Call `bm_move` with configured project, original identifier, destination and expected_checksum. Never use filesystem rename for real notes.
3. Read through the original permalink: new path, identical full contents and checksum. Check existing relations through `bm_context` with a supported timeframe that includes the links being verified; inspect the tool's date-range limits. If old links fall outside that range, read their targets explicitly and record the context-query limitation. Rerun check-item to record completion. If indexing is briefly stale, re-read at most twice; stop on a persisting discrepancy. Do not rewrite links/content to force a match. Renew with `queue.py ... renew --run ID` before lease expiry.
4. After all moves verify, `complete --plan ID`. Append actual results to the operational report with guarded MCP edit/read-back. Keep originals in Archive and snapshots intact. Normal success needs no extra email; failures/new review items use the outbox.

## Interrupted archive

Never run queue abort for an archive. Use `failure --plan ID --reason SHORT-CODE`; retain the plan, original hashes and any partial moves, and process optional notifications. An archive_recovery_required result means `recover --plan ID`, which refuses live-lease takeover and renews an expired archive lease. Check every item; recognise completed moves by original hash/permalink and absent source, then resume only pending approved items. A changed source/destination requires user review. Recovery grants no broader approval. For a time limit, leave the plan/lease intact for later recovery.

## Restore

`verify SNAPSHOT` checks every recorded hash. `restore SNAPSHOT --destination NEW-ISOLATED-DIRECTORY` reconstructs files with verified hashes only into an absent destination outside live Brain/state/backups. It never restores over live data. Inspect the copy before proposing a live recovery. Exact live changes require approval; use guarded MCP note operations and preserve intervening work. Never copy a historical queue/automation wholesale over current state: it could lose decisions or repeat emails. Snapshots remain local; off-device backup and pruning need separate choices.

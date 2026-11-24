# Review queue and optional notifications

Run helpers with the installed Python and private config: `PYTHON /absolute/worker/scripts/queue.py --config CONFIG SUBCOMMAND`. These helpers do bookkeeping only. They do not call a model, edit live notes or send email. Local `mode: review_only` is the supported workflow; it is not a tool-level security sandbox.

## Begin and review

`begin --limit 25` acquires a logical lease (one hour by default), with an OS file lock and atomic state updates. `busy` means another worker owns it; stop. `renew --run ID` extends a valid lease. An expired ordinary review is retried on the next begin, with a failure event and no acknowledgement of unprocessed revisions. Late completion is rejected. An expired archive emits `archive_recovery_required`; use archive recovery, not abort.

State is bound to the configured project and root. Use new empty state for a new installation; do not copy someone else's queue or point existing state at another project. Source scanning covers Inbox, Projects, People, Knowledge, Decisions and Preferences. Reviews, schemas, Archive, hidden files, symlinks, `verification_only: true` and `status: test_fixture` are excluded. Malformed frontmatter is a failure, not a silent skip.

Read each candidate with Basic Memory MCP and relevant existing topic notes. The manifest SHA-256 identifies its raw disk revision; MCP's returned checksum guards actual edits. Write review JSON privately under `state_dir/runs/`. Every candidate must appear once:

```json
{
  "reviewed": [
    {"path": "Inbox/Captures/Example.md", "sha256": "manifest hash", "outcome": "review", "reason": "A tentative change needs approval."}
  ],
  "issues": [
    {
      "key": "example/review-interval",
      "kind": "proposal",
      "summary": "Review a proposed interval change.",
      "sources": [{"path": "Inbox/Captures/Example.md", "sha256": "current raw hash"}],
      "proposal": {
        "target": "Decisions/Example.md",
        "expected_checksum": "current target checksum",
        "status": "tentative idea",
        "change": "Exact proposed Markdown change, with source references and relevant wikilinks."
      }
    }
  ]
}
```

`outcome` is `no_action` or `review`; explain either. A review outcome needs an issue referencing that candidate. `kind` is `proposal` or `conflict`. Use a stable topic/field key and inspect existing issues first. A conflict records both dated claims and asks one focused question. A new target uses null expected_checksum only after verifying absence. For unchanged semantic proposals, keep the same wording/key and update evidence; do not re-notify or reopen an unchanged resolved/declined proposal.

Show proposed edits in the harness output before finishing. Compute issue ID, if needed in the report, as `review-` plus the first 12 hex characters of SHA-256 of `json.dumps(key, sort_keys=True, ensure_ascii=False).encode()`. Write one operational report through MCP in `Reviews/Consolidation/`, title `Consolidation Review - RUN-ID`; search first after a retry. Include actual source links, counts, IDs, pending-approval status and the available harness reference. Do not copy unapproved claims or secrets. Read it back.

Then run `finish --run ID --review /absolute/private/review.json --report ACTUAL-PERMALINK`. Use the returned permalink verbatim. It must start with the configured project plus `/reviews/consolidation/`. The helper rechecks source and target revisions, rejects concurrent changes, commits the reviewed revisions and retains issue drafts. Review does not mean approval.

For a continuing transient tool failure, try at most twice per invocation, then `abort --run ID --reason concise-code`. This releases an ordinary review without marking revisions processed. Failure events stay local or become optional notifications. Never put raw note/exception contents into email. Process at most four batches/45 minutes, leaving the rest pending.

## Approve and apply

Approval is specific to the displayed proposal. Silence, unrelated replies and schedule creation are not approval. Re-read target/sources through MCP and compare with the proposal. If their meaning/revisions changed, refresh the proposal instead of bypassing guards. Make the approved change through checksum-protected MCP operations, preserving history and sources, and read back. Then `resolve --issue ID --reason 'approved action and date'`. An explicit dismissal also allows resolve with the actual user reference. Sending an email never resolves an issue. Keep private source history.

## Local reporting and email outbox

With `notifications.enabled: false`, issues and failure events remain in private state and operational/harness reports; events are marked local_only. `notify-claim` returns disabled and sends nothing. Enabling email later does not retroactively send old local-only events. A user can inspect `status` and ask about outstanding items. Do not claim email coverage in this mode.

With explicit email consent and a tested provider connection:

1. `notify-claim` returns none, send, or reconcile_before_sending. A send reserves one event. Inspect the selected provider, recipient and event ID. Verify the connected account and the user's approved recipient before sending; for Gmail self-notifications use `me` only when it matches that identity. Outlook addressing follows its actual connector. No substitute provider/recipient, CC/BCC or attachments.
2. Before an external send, search SENT for the exact event ID and inspect matches, so retries after crashes do not duplicate mail. Subject: `AI Brain: review needed [EVENT-ID]`, `AI Brain: archive approval needed [EVENT-ID]`, or `AI Brain: run needs attention [EVENT-ID]`.
3. Body: only new/changed proposal/conflict counts, archive candidate count or a generic failure code; local report path; optional configured thread URL. Include a plain fallback describing how to find the report. App/local links may fail on another device. Never include raw claims, private titles, note excerpts or credentials.
4. A successful send must return a provider message ID. Run `notify-sent --event ID --message-id ACTUAL-ID`, then read the sent message and verify recipient, subject and sent status. Acceptance is not proof the user read it.
5. A definite rejection before sending: `notify-failed --event ID --certainty not-sent`. Retry only on a later invocation, at most three attempts. A timeout/uncertain result: use certainty unknown. A reserved, uncertain or blocked event requires SENT reconciliation. A verified match may be acknowledged; without definitive evidence report uncertainty and ask the user before resending. Do not loop sends.

`status` reports active lease, last successful completed review, processed revisions, open issues and pending emails. Unchanged issues do not create repeated email events. Do not disable/change notifications merely to hide a reserved event; reconcile existing uncertainty deliberately.

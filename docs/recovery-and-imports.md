# Recovery, selected imports and future sharing

## Recovery layers

Drive or another file-sync service can keep Markdown on another device, but also propagates edits/deletions. Verify actual cloud files and revision recovery with a fictional note; do not infer backup quality from a sync icon. Retention and recovery behaviour depend on the selected service and must be checked in its current documentation.

The optional helper's snapshots provide local version history of the Brain and precisely configured support paths. They are hash-verified and can restore only into a new isolated destination outside the live Brain/state/backups. They do not provide off-device disaster recovery. Select an independent destination separately if required; this repo does not buy a service or prune old snapshots.

## Test restoration

1. Use an isolated example Brain and an actual configured backup directory outside sync. Run `archive.py --config CONFIG snapshot --label 'recovery trial'`; require verified true.
2. Record original hashes. Make a non-sensitive test change, then `verify SNAPSHOT` and `restore SNAPSHOT --destination NEW-ABSENT-ISOLATED-PATH`.
3. Compare restored bytes against recorded hashes and confirm live notes/state were untouched. Corrupt a copy in a separate test to verify detection; never alter the real recovery copy for a live Brain.
4. For a real recovery, inspect the isolated restored note and compare with today's content. Obtain approval for the exact live change, preserve newer work, then restore through checksum-protected Basic Memory operations and verify content, indexing and links. If synced, verify the cloud copy too.
5. Do not copy old queue/automation state wholesale over current state. It can lose decisions or resend email. Recover operational state deliberately using the run/archive protocols.

In the original Drive recovery test, a whole-note replacement removed a final newline; a guarded edit restored exact bytes before hash verification passed. Check the actual current version's behaviour instead of assuming semantic equality proves byte preservation.

## Small import pilot

Imports are separate from routine maintenance. Ask the user to select a small accessible set of historical chats. A title/summary helps locate a source; it is not evidence for a knowledge claim. Read actual messages, recording dates, roles, stable source IDs and partial/truncated coverage. Exclude reasoning, runtime wrappers, secrets, unrelated files and unselected attachments.

Search existing notes and show exact proposed contents, status, target, links and source-retention scope. Topic selection is not approval of arbitrary claims. Save only explicitly approved material through Basic Memory, read back and check links. Keep user reports, confirmed decisions and historical assistant execution reports distinct. Do not silently treat old roles as current.

Store only approved relevant source extracts and an import ledger privately outside the indexed Brain and Git. Record batch/source IDs/hashes, coverage, approval and final target checksums. Repeat the same batch: unchanged sources/targets must produce zero writes and duplicates. If either changed, re-review rather than overwrite or recreate deleted notes automatically. Assess the small pilot before broader imports; this is not universal chat capture.

If raw extracts are included in snapshots, review the exact support path and off-device strategy separately. Synced curated notes may survive Mac loss while local extracts do not.

## Sharing

For a named recipient/purpose, use a separately controlled project or an explicit reviewed export. Check links and attachments and exclude private raw sources, historical revisions and operational state. A folder named Shared or a visibility label is not access control. Publishing source code and sharing personal knowledge are different authorisations.

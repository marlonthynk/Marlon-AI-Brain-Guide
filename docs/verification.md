# Verify the memory loop and maintenance

Use fictional content in an isolated project. Do not copy the example notes into a live personal Brain. [Example files](../examples/fictional-brain/README.md) are clearly labelled fiction; their status is not a real user decision. Replace tokens with unique markers in the actual acceptance run and keep markers out of recall prompts.

## Automated helper checks

Run README's tests and release checks. `scripts/demo.py --destination NEW-ABSENT-PATH` copies the fictional Brain into that isolated location, creates local-only config with a custom project, runs a review proposal/repeat/conflict trial and tests snapshot/restore. It does no MCP registration, live-note changes, email or scheduling. Synthetic test code may rename a temporary fixture to simulate an external move; production helpers never rename live notes.

## Actual harness acceptance test

Agree a separate local test project and register it through the supported CLI without changing the production default. Confirm the exact project path. Use these prompts in fresh sessions of each selected interface; scope every operation explicitly. The setup user can approve these fictional operations as one bounded test, not a general memory-write permission.

1. **Origin harness:** “In my isolated test project only, create/read back a FICTIONAL Harbour project and linked decision: a 14-day review interval, rationale: shorter feedback loop. Generate and record an origin token. Add a Friday digest as an undecided idea. Cite the notes and checksums.”
2. **Second harness:** “Search/read the fictional Harbour decision and linked project in the test project. Report its current interval, origin token and tentative idea with supporting permalinks.” Do not include the origin token in this prompt.
3. **Correction:** “In that existing test decision only, change the interval to 21 days, rationale: longer observation window. Preserve 14 days and its rationale as superseded history. Leave the digest undecided. Generate a correction token, guard the latest checksum, read back and report the new checksum. Create no duplicate.”
4. **Other fresh harnesses:** Ask them to retrieve current value, correction token, history and undecided idea. Withhold token/value from the question where possible.
5. **Obsidian:** Add a unique non-sensitive observation directly in the linked project note. Index the selected test project with installed CLI syntax, then ask each harness to retrieve the new observation. Verify graph links and one Obsidian backlink.
6. **Repeat:** Request the same save again. It should search/read, recognise existing content and make no unnecessary write. Verify the checksum and one matching topic.
7. **Guards:** Attempt an explicitly authorised stale-checksum update to the fictional note. Expect rejection and unchanged bytes. Test a non-sensitive outside-project canary and wrong-project rejection, without equating project routing with filesystem isolation.

Record actual versions, project/paths, interface/session, supporting permalinks, checksums, results and limitations in the private Setup Log. Do not claim clean-context testing if an interface uses a persistent Bot. Keep test notes excluded from live consolidation using verification_only/status:test_fixture after inspection, or leave them only in a separate disposable test project.

## Maintenance acceptance

Run the generic worker against a separate test collection. Add a tentative capture that contradicts the current fictional decision. Expect an exact approval proposal/conflict and unchanged source/target. Verify a report and private issue; a repeated unchanged run should be idle and not duplicate it. Deliberately change a source during a review and confirm finish rejects it, preserving pending work. Only an approved applied/read-back change or explicit dismissal resolves its issue.

For archiving, age only the isolated fixture (or simulate time in tests), review its current revision, document completion, take/restore a snapshot, and preview. Claim without approval must fail. A fixture is not consent for real source archiving or future automatic mode. A real guarded MCP move/return must preserve bytes, permalink and graph links. Simulate interrupted moves only with isolated fixtures and follow recovery.

For selected email, use a non-sensitive explicitly authorised test. Verify provider/account/recipient, reservation, duplicate-Sent search, returned ID and sent-message read-back. Gmail was the original tested provider; test every new adapter/runtime. Disabled email must create no send action while preserving local issues.

For scheduling, inspect the saved task and one actual scheduled invocation. A manual helper run, configured task or passing synthetic test does not prove the scheduled app has MCP/email access. Leave this check visibly pending until observed; do not invent evidence.

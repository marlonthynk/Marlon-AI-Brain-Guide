# Set up your shared AI brain

This repository is a macOS-first, AI-assisted setup. Use [the setup prompt](../prompts/setup.md) with a local-capable harness. Work one stage at a time, verifying each before proceeding. Basic Memory/plugin 1.0.0 was the historical baseline; inspect the version you install and its official help. Preserve existing notes, integrations and unrelated instructions.

## 1. Inspect and choose storage

Locate Obsidian's actual vault and installed tools. Inspect existing Basic Memory projects, MCP servers/plugins and instructions. Agree a dedicated `AI-Brain` subtree and local project slug, such as `personal-brain`. Preserve existing files. Create only missing Inbox, Projects, People, Knowledge, Decisions, Preferences and Reviews folders. Later integrations add schemas; captures/checkpoints use Inbox/Captures and Inbox/Sessions. Archive is within the same project and is not a privacy boundary.

Pass: exact paths/project are confirmed and existing material preserved.

## 2. Install Basic Memory and test Obsidian

Read [current official local installation](https://docs.basicmemory.com/local/local-install), starting with the [AI documentation index](https://docs.basicmemory.com/llms.txt). Install a compatible stable release with uv; do not change macOS system Python. The documented starting command is `uv tool install basic-memory`. Discover supported Python requirements, actual executable path, installed version and CLI help. Use an absolute executable path for GUI launchers when needed.

The original build's stable package needed a narrowly scoped prerelease dependency exception; do not add it preemptively or pin obsolete versions for every reader. Report permission failures through the normal permission flow.

Inspect `basic-memory project add --help`, list/default/index help and current configuration. The tested 1.0 command shape is:

```text
basic-memory project add PROJECT "/absolute/path/to/AI-Brain" --default --local
basic-memory project index PROJECT
```

Replace PROJECT and the path; reuse an existing matching registration. Never register the whole vault by accident or remove unrelated projects. Verify local routing and keep the database, embedding/uv cache outside the synced vault. Do not assume a watcher is active. Write `Reviews/Setup Log.md` through Basic Memory, open in Obsidian, edit a unique sentence, index, then retrieve it.

Pass: actual write/read, Obsidian edit/index/search, project routing and external state paths verified.

## 3. Connect Claude interfaces you use

Ordinary Claude Desktop chat and Claude Code are separate. Inspect/back up affected settings and use the official integration/setup workflow for each selected interface. [Claude notes](harnesses/claude.md) and [MCP examples](../integrations/claude-desktop-mcp.example.json). Check installer help before using `bm install claude-code --dry-run` and choosing scope. Run its official setup selecting this local project/general knowledge. Preserve unrelated settings and existing instruction files; let the user complete trust/sign-in/restart requirements.

Pass: fresh Desktop saves a non-sensitive linked note; fresh Code retrieves and updates it; fresh Desktop retrieves the update. Test actual interfaces, not just CLI health. Checkpoint capture needs separate opt-in and an actual compaction test.

## 4. Connect Codex or another harness

Inspect registrations and official installer help. The tested route used `bm install codex`, the official setup workflow and the plugin's supplied MCP server, without adding a duplicate. Activate/restart through the app's supported security flow. [Codex notes](harnesses/codex.md). Other tools must pass the [capability checks](harnesses/README.md).

Pass: actual desktop read/update of the Claude note, guarded checksum and fresh Claude recall. If the assistant cannot operate its own app, supply an exact fresh-chat prompt and inspect its response/tool evidence. Record untested surfaces.

## 5. Agree capture behaviour

Adapt [the shared policy](../integrations/shared-memory-policy.md) with the selected project. Merge bounded instructions into the harness's supported personal/project instructions, preserving other content. Check for conflicting existing capture rules and explain any deliberate change.

Curated saves use suggest-then-ask; explicit remember requests already authorise the content. Search/read first; update suitable topics; distinguish facts, decisions, reports, suggestions and tentative ideas. Preserve dates, provenance, history and useful links. Keep unapproved drafts outside the knowledge base. Separately decide whether to enable code checkpoints; inspect actual hook defaults and test before relying on them. They remain uncurated in Inbox/Sessions.

Pass: fresh-session controlled cases cover refusal, unrelated reply, partial approval, undecided idea and explicit save. Instructions guide model behaviour, not guaranteed detection or a tool-level authorisation gate.

## 6. Add Grok only if you use it

Do not assume installation or marketplace compatibility gives a Bot access to local files. Inspect its actual authenticated local execution capabilities. The original main Bot used supported Basic Memory CLI operations through an existing Mac Shell connection; no public endpoint, new cloud service or native MCP connector was required. [Grok routing template](../integrations/grok-local-routing.md).

Pass: non-sensitive search/read/write, guarded stale-update rejection and capture-policy cases. Record the exact Bot tested. Other Bots and clean-context resets remain separate checks. Stop if the Mac is unavailable; do not invent an alternate brain or offline write queue.

## 7. Verify the complete loop

Use [fictional linked notes and acceptance prompts](verification.md). Save a decision in one harness, correct it in another with preserved history, retrieve from fresh sessions, edit in Obsidian and index, preserve tentative status, check links and duplicate suppression, and cite supporting notes. Test project routing with non-sensitive canaries, without claiming folder-level permissions.

Pass: evidence for every selected interface, failures fixed or explicitly scoped. Installation success is not functional verification.

## 8. Optionally add reviews and schedules

Read [maintenance](maintenance.md). Create private generic configuration without editing Python. Run tests, an isolated trial and a manual live review before scheduling. Weekly review is a simple option; daily review is optional. Local reports are default; email requires separate consent and a verified account/recipient/send test. Archive previews are optional, require snapshots and separate move approval gates. Use [schedule setup prompt](../prompts/create-schedule.md); verify a saved schedule and one actual scheduled run. No running installation is modified by repository changes.

## 9. Verify recovery and selected backfill

Read [recovery/imports](recovery-and-imports.md). Verify a versioned snapshot and isolated restore before broad rewriting. If using Drive, test local/cloud revision recovery with fictional content; sync can propagate unwanted changes. Choose only a small accessible set of historical chats, show exact proposed notes and approve relevant source retention, save/read back/link/check duplicates, then assess quality before expanding. Raw sources stay outside the indexed/shared project and Git. Future sharing uses explicit reviewed exports or separately controlled projects, not a folder label.

## Troubleshooting and official sources

Use installed CLI/tool help when syntax differs. For stale retrieval, index the selected project and check readiness/errors. On checksum conflict re-read and reassess, never bypass the guard. Resolve duplicate servers by identifying which official integration supplies MCP. For busy/recovery states respect the lease and matching protocol. Stop on trust/connector failures and report precisely.

Official starting points: [Basic Memory](https://docs.basicmemory.com/llms.txt), [Claude Desktop](https://docs.basicmemory.com/integrations/claude-desktop), [Claude Code](https://docs.basicmemory.com/integrations/claude-code), [Codex](https://docs.basicmemory.com/integrations/codex), [configuration](https://docs.basicmemory.com/reference/configuration). The 1.0 installed help and original results are documented in [case study](case-study.md); current vendor interfaces require local verification.

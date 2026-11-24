# Marlon AI Brain Guide

Build shared AI memory with **Obsidian + Basic Memory**: portable, linked Markdown that your AI tools can search and update with your approval.

This is the reusable companion to Marlon Grech's setup. It includes a staged guide, prompts, integration templates, optional scheduled reviews, weekly archive previews and tested recovery helpers. Start with one AI tool; add others when the memory loop works.

**macOS-first · MIT licensed · local Markdown · optional maintenance**

## Start here

Clone or download this repository, open the folder in an AI harness that can access your Mac, then paste:

```text
Read prompts/setup.md and docs/setup.md in this repository. Help me build
this shared AI brain in my environment, one verified stage at a time.
Inspect what already exists and preserve it. Ask for missing choices,
handle what you can, and guide me through sign-in, trust and fresh-chat
checks. Wait for my confirmation before starting the next stage.
Begin with inspection; do not install the optional maintenance worker yet.
```

You need Obsidian, a local folder for the Brain, a compatible Basic Memory installation and at least one AI interface with local MCP or authenticated local CLI access. The setup prompt checks these. Ordinary cloud chat alone does not grant access to your Mac. See the [harness capability guide](docs/harnesses/README.md).

The guide registers only your chosen `AI-Brain` subtree. Your database, cache, private review state and recovery snapshots stay outside a synced vault. You choose your own paths, project name and AI interfaces. [Read the staged setup](docs/setup.md).

## What gets remembered?

The shared policy notices useful decisions, preferences, corrections, findings and project changes. It searches existing notes, proposes an exact save and asks first. An explicit “save this to shared memory” already authorises that content. It preserves sources, tentative status and superseded decisions.

Code-session checkpoints are a separate opt-in and stay uncurated in Inbox. Installing Basic Memory does not monitor every chat. Reviews can process only what was captured. [Capture policy template](integrations/shared-memory-policy.md).

## Add weekly reviews and schedules

After verifying the core setup, paste this into your preferred capable harness:

```text
Read prompts/create-schedule.md and docs/maintenance.md. Help me set up
review-only maintenance for my existing Basic Memory project.
Start with one manual trial. Then offer a weekly review, with daily review
optional. Ask me for the day, time and timezone. Use local reports by
default; ask separately before adding email. Inspect your scheduling and
local-access capabilities, reuse an existing matching schedule, and verify
the saved task plus one real scheduled invocation. If you cannot schedule
or access local memory in the scheduled environment, explain the supported
manual/runtime choice. Do not claim the schedule is active without evidence.
```

| Task | Prompt | Result |
| --- | --- | --- |
| Set up the Brain | [setup](prompts/setup.md) | One stage at a time, with checks |
| Review now, weekly or daily | [run review](prompts/run-review.md) | Exact proposals awaiting your approval; operational report |
| Create/review a schedule | [schedule setup](prompts/create-schedule.md) | Your cadence, timezone and verified runtime |
| Preview completed Inbox sources | [archive](prompts/archive.md) | Eligible originals proposed for archiving, with snapshots |
| Apply an approved proposal | [approved change](prompts/apply-approved-change.md) | Revision-guarded update and read-back |
| Resume an interrupted archive | [recovery](prompts/recover.md) | Resume the same plan without duplicate moves |

**Review and archiving are separate.** Review suggests useful changes; archiving moves completed originals unchanged after review and completion checks. A single scheduled invocation can review first, then check the weekly archive slot. The first real archive batch needs approval, followed by separate consent before routine qualifying moves. There is no automatic deletion or broad curated rewriting.

Prompt files use the same [maintenance skill and protocols](skills/ai-brain-consolidate/SKILL.md), so manual and scheduled runs follow one workflow. The Python helpers handle hashes, leases, queues, snapshots and recovery. **They do not run an AI model, edit live notes or send email themselves.** The selected harness must perform those operations with the configured access. No schedule is installed by cloning this repo.

## Install and test the optional helpers

Use Python 3.10+ on macOS. The original build used Python 3.12. Create a separate environment for these helpers; Basic Memory has its own installer and dependency requirements.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s skills/ai-brain-consolidate/scripts -p 'test_*.py' -v
.venv/bin/python scripts/check_release.py
```

Use [configuration setup](docs/maintenance.md#configuration) to create a private installation config. No Python edits are required to choose your project, paths, email mode, archive weekday/time or timezone. Tests use isolated temporary files and send no email. The [fictional example](examples/fictional-brain/README.md) and [verification guide](docs/verification.md) cover the manual acceptance loop. [Validation record](docs/validation.md).

## Scope and limits

- The original live setup tested Claude Desktop, Claude Code, Codex desktop and one Grok Bot. Codex was the scheduled runtime. Other harness schedulers need their own capability and end-to-end checks.
- Local reads depend on the Mac, app/runtime, network and connectors being available. A later invocation scans outstanding revisions; immediate execution on wake is not promised. An offline worker cannot email its own offline failure.
- Email is optional and off by default. Gmail was tested in the original build. The provider-neutral protocol also describes Outlook; its actual scheduled send path must be tested before relying on it.
- Markdown is local, but retrieved content is processed by the AI provider you use. Connected tools share the configured project. Folder names are not access controls.
- Snapshots are local version history, not protection against losing the Mac. [Recovery and selected imports](docs/recovery-and-imports.md).
- Helpers use Unix file locking. macOS is the supported starting point; Linux helper tests do not establish desktop integration support, and Windows is unsupported.

The [case study](docs/case-study.md) distinguishes recorded results from limitations. This repo contains reusable source and fictional examples, not the author's live notes, state, private chat references or original Git history. Changes here do not deploy to any running installation. [Contributing](CONTRIBUTING.md) · [MIT licence](LICENSE).

# Choose a capable harness

These prompts describe tasks, not capabilities an app is guaranteed to have. Check the actual installed interface and version. Basic Memory MCP connection, conversational capture instructions and scheduled execution are separate.

| Route | Original live evidence | Scheduling guidance |
| --- | --- | --- |
| [Claude Desktop and Code](claude.md) | Both read/write/search/links; Code checkpoints tested separately | Inspect the chosen interface's supported scheduler; do not assume Code hooks schedule Desktop chats |
| [Codex desktop](codex.md) | Plugin MCP, cross-harness changes and scheduled maintenance | Original scheduler route; verify current app's saved task and actual invocation |
| [Grok main Bot](grok.md) | Authenticated local CLI access in one persistent Bot | Scheduling not established by a local Shell connection; test separately |
| Other MCP/local coding harness | No original end-to-end evidence | Must independently verify local tool access, report writes and scheduler semantics |

The review worker expects local Basic Memory MCP tools for live note operations. An interface with only CLI access may still perform ordinary explicit memory saves (as the original Grok route did), but cannot claim the supplied MCP maintenance protocol passed unchanged. Use a tested MCP-capable runtime for maintenance or explicitly adapt/test an equivalent protocol. Installing the skill into one harness does not configure other apps.

Before scheduling verify: local files/scripts, correct Python/dependencies, configured project/root, scoped MCP read/search/write/edit/move/context, normal trust/approvals and optional provider email tools. A remote/cloud scheduled environment may not share interactive local access. Unsupported scheduling means a manual run or a user-selected supported runtime, not an invented cron/launchd setup.

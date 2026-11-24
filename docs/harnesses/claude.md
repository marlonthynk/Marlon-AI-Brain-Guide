# Claude Desktop and Claude Code

Ask which interface the reader uses. Ordinary Desktop chat and Code have separate MCP/settings/trust surfaces. Merge one working local registration per chosen interface, backing up only affected settings. Use the official installer/setup for Code and preserve unrelated plugins/instructions. [Desktop MCP example](../../integrations/claude-desktop-mcp.example.json) · [Code example](../../integrations/claude-code-mcp.example.json).

The original Code setup used `bm install claude-code --scope user` and its official setup workflow with a general knowledge profile. Inspect installed help first. GUI launchers may need an absolute Basic Memory executable. Let the user handle trust/restarts. A signed-in app does not prove a separate terminal CLI is authenticated.

Test Desktop save → fresh Code retrieval/update → fresh Desktop retrieval. Verify links/backlinks and no duplicate. Code PreCompact capture is a separately configured extractive checkpoint; it does not automatically capture ordinary Desktop chat. Inspect hooks/defaults and explicit opt-in rather than assuming the minimal config disables them.

The original 1.0 Code search sometimes needed explicit `projects: [PROJECT]`; apply [the compatibility note](../../integrations/claude-code-search-compatibility.md) only if reproduced. Scheduling is a separate capability check. The common prompts can be read by a capable Claude interface, but this repo does not claim a verified Claude scheduler route.

[Official Desktop integration](https://docs.basicmemory.com/integrations/claude-desktop) · [Code integration](https://docs.basicmemory.com/integrations/claude-code).

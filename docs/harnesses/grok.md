# Grok local access

The original main Bot used an existing authenticated local Mac Shell connection and the supported Basic Memory CLI. It did not use a Cursor marketplace installation, public endpoint or new cloud-hosted Brain. An app being installed is not evidence its cloud tools can access local files.

Use the [neutral routing template](../../integrations/grok-local-routing.md) only after confirming actual local execution, executable/project and supported CLI tool arguments. This is a newly written template consistent with the recorded architecture, not an export of the author's private hosted skill.

Verify search/read, a non-sensitive approved write/read-back and stale-checksum rejection. Other Bots need individual setup/tests. The original recall used fresh external reads in a persistent Bot conversation; clean-context restart was not demonstrated. Local execution must report unavailable when the Mac cannot be reached, with no alternate memory store or queued writes.

The supplied review worker uses MCP operations for reports and guarded moves; the original Grok CLI route is ordinary capture/recall, not a verified maintenance/scheduler adapter. Use another tested MCP-capable runtime for maintenance unless you explicitly adapt and verify an equivalent Grok workflow.

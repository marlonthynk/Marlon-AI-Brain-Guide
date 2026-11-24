# Set up weekly or daily maintenance

```text
Read docs/maintenance.md, docs/harnesses/README.md and the maintenance skill.
Inspect my existing Basic Memory project and any matching scheduled worker.
Explain what this scheduled environment can actually access: local files,
Basic Memory MCP, skill files and optional email. Do not infer these from
interactive chat access. If you cannot schedule or reach local memory at
run time, explain the limitation and agree a supported runtime or manual
workflow; do not silently install another service.

Offer weekly review as a simple option, with daily review optional. Ask me
for runtime, day/time, IANA timezone and reporting choice. Default to local
reports; request explicit account/recipient/send permission before email.
Ask separately whether to add weekly archive previews; explain that review,
curation approval and source archiving are different. Preview is not
permission to move the first real batch or enable future automatic moves.

Create a private config using scripts/configure.py (or narrowly edit an
existing approved config). Use my project/paths, fresh state for a new
installation, and future dates. Run tests and an isolated synthetic trial,
then a small manual live review with report read-back. Verify snapshot/
restore and a fictional guarded move before relying on archive behaviour.

Render prompts/run-review.md with the actual Python/skill/config paths.
Show the resulting schedule/prompt. Create or update one matching task
through supported scheduler tools, completing any required normal user UI
confirmation. Do not copy internal scheduler files or bypass approvals.
Inspect the saved task's status, prompt, target, cadence and timezone.
Record its actual ID/reference in my private Setup Log and verify a real
scheduled invocation separately. Do not claim that configured means tested.
```

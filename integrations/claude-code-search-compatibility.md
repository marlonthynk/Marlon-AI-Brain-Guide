# Conditional Basic Memory 1.0 search workaround

The original Claude Code integration sometimes rejected singular-only/empty-project search arguments. If reproduced with the installed version, use `projects: ["YOUR_PROJECT"]` for bm_search; continue using the tool's actual singular project argument for read/edit/context. Replace YOUR_PROJECT, preserve unrelated instructions, and verify a fresh session. Do not apply an obsolete workaround without reproducing the failure.

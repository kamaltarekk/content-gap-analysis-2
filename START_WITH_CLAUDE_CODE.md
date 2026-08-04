# First Claude Code Prompt

Open Claude Code in this repository and paste:

```text
You are implementing the Evidence-Based Content Diagnosis Tool.

Read CLAUDE.md, docs/PRODUCT_SPEC.md, docs/ARCHITECTURE.md, docs/SCHEMAS.md, and docs/IMPLEMENTATION_PLAN.md.

First inspect the repository and run the existing API and web checks. Fix only scaffold defects needed to make Phase 0 pass. Then stop and report:

1. Files changed
2. Tests and checks run
3. Remaining blockers
4. Whether Phase 0 acceptance passed
5. The exact next phase

Do not skip phases. Do not redesign the product boundary. Do not start Phase 1 until Phase 0 passes.
```

After each phase, run:

```text
/build-next
```

# ZuhauseFinder Agent Governance

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Mandatory workflow

For every task that may change application code, tests, data, configuration, dependencies, generated artifacts, or an external system:

1. Read all applicable AGENTS.md and CLAUDE.md files.
2. Inspect the repository, relevant implementation, tests, Git branch, base SHA, status, and diff before editing.
3. Create plans/<task-id>.md from plans/TEMPLATE.md.
4. State exact scope, in-scope and out-of-scope files, acceptance criteria, tests, risks, contracts, rights/provenance effects, external effects, and rollback.
5. Stop for explicit user approval. Do not edit runtime code, tests, data, configuration, or external systems during Phase 1.
6. After approval, implement only the approved plan. Add the specified tests first.
7. Never delete, skip, weaken, or silently rewrite an existing test. If an existing test appears wrong, stop and request a plan revision.
8. After three distinct failed root-cause hypotheses, stop. Record each hypothesis, command, result, and conclusion.
9. Finish with Git status including untracked files, a complete diff summary, verification results, remaining risks, and rollback instructions.
10. Do not commit, push, deploy, migrate a database, send real customer email, expose credentials, or perform destructive actions unless separately authorized.

Read-only investigation and harmless documentation may use a short inline plan only when the user explicitly asks for that faster lane. It never authorizes application, data, configuration, deployment, or external-system changes.

## Suite safety gates

Every implementation plan must answer with code and test evidence:

> Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

The required answer is no.

- Original annotations and source assets are immutable internal records.
- Corrected millimetre geometry, revisions, approval, and publishable exports remain separate.
- Canonical JSON is the single geometry source for 2D and 3D/massing output.
- Restricted references do not become commercially eligible merely because they were imported or edited.
- Customer delivery requires valid geometry, explicit human approval, safe JPEG artifacts, and the WordPress manual email gate.
- Free generation, silent geometry guessing, database publication, image generation, and automatic customer sending cannot enter as incidental changes.
- Preserve user-owned dirty worktrees and untracked files. Never overwrite or clean them as part of another task.

## Independent review

Claude review is read-only unless a separate implementation plan is approved. The reviewer must read the applicable instructions, approved plan, base SHAs, full status including untracked files, complete diff, and verification output. It must challenge unsupported assumptions, identify where the plan disagrees with the real code, and cite file and line evidence.


<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

## Persistent follow-up tracking

Canonical suite roadmap: `C:\dev\born2thrill-app-repo\plans\ROADMAP.md`

Before marking any task complete:

1. Record every unfinished in-scope item and every known out-of-scope follow-up in the canonical roadmap.
2. Keep excluded work pending; exclusion from one approved plan never means cancellation.
3. Remove or mark a roadmap item complete only with evidence, or mark it cancelled only when the user explicitly cancels it.
4. Name the next pending roadmap item in the final report, or explicitly state that none remains.

If the canonical roadmap is unavailable, stop and report that exact blocker instead of silently dropping the follow-up.


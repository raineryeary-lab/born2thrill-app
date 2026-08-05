# ZuhauseFinder Agent Workflow

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

This is the canonical detailed policy for the Floorplan Simplifier, local correction Workbench, deployable Born2Thrill service, and ZuhauseFinder WordPress integration. Every repository root keeps a self-contained AGENTS.md because Codex and Claude discover instructions from the active project root.

## Risk boundary

The full inspect-plan-approve cycle is mandatory for changes to code, tests, data, schemas, geometry, rights/provenance, files, configuration, dependencies, database state, email, deployment, external services, or customer-facing behavior.

A fast lane is allowed only when the user explicitly requests read-only investigation or harmless documentation. The fast lane still requires instruction discovery and status inspection and never permits external actions.

## Phase 1 - inspect and plan

1. Record repository path, branch, base SHA, Git status, untracked files, and existing diff.
2. Read the implementation, contracts, relevant tests, and current runtime evidence.
3. Create plans/<task-id>.md from the repository template.
4. Include objective, current evidence, exact files in and out of scope, API/schema/data-contract effects, acceptance criteria, tests and commands, protected paths, rights/provenance impact, external effects, deployment/rollback, and unresolved questions.
5. Stop. Only the plan file may be added or edited.

## Approval

Approval names the plan. Approval does not imply permission to commit, push, deploy, migrate, delete, send customer email, alter credentials, or expand scope.

If later evidence requires another file, contract, or behavior, stop and revise the plan for approval.

## Phase 2 - implementation

1. Reconfirm the baseline and preserve new user changes.
2. Add the approved acceptance tests first.
3. Implement only the approved scope.
4. Do not delete, skip, weaken, or change an existing test unless the approved plan names the exact test and reason.
5. Treat three distinct root-cause hypotheses as the repair limit. Environmental repeats count once.
6. Run every approved test plus lint, type-check, and build where applicable.
7. Do not hide failures or substitute a narrower command without reporting it.

## Phase 3 - handoff and review

Provide:
- repository, branch, and base SHA;
- full status including untracked files;
- changed-file and diff summary;
- tests, lint, type-check, and build output;
- rights, privacy, security, and data-loss assessment;
- external/deployment effects;
- rollback instructions.

Claude then performs a fresh read-only review. A finding outside the approved plan requires a follow-up plan; it is not permission for an automatic redesign.

## Floorplan invariant

No path may generate, publish, or email geometry without an approved corrected corpus reference. The proof must cover matching, canonical geometry, validation, provenance, artifact safety, approval, and the WordPress send gate.

## Standard opening prompt

Follow AGENTS.md strictly.

Phase 1 only. Inspect the repository and current implementation. Record the repository, branch, base SHA, Git status, and existing changes. Create plans/<task-id>.md from plans/TEMPLATE.md. Do not modify runtime code, tests, data, configuration, or external systems. Stop after presenting the plan.

## Standard approval prompt

Approved: plans/<task-id>.md. Implement only the approved scope and acceptance criteria. Add the specified tests first. Do not weaken existing tests, touch out-of-scope paths, deploy, send customer email, or commit/push unless explicitly authorized. Stop after three distinct failed hypotheses. Finish with status, diff, verification, risks, and rollback.

## Standard Claude review prompt

Read-only review; do not modify files. Read AGENTS.md, CLAUDE.md, the approved plan, pinned base SHAs, Git status including untracked files, the complete diff, and verification output. Check scope, acceptance criteria, cross-repository contracts, test integrity, approved-corpus-only behavior, geometry/hash/provenance preservation, rights and customer-delivery gates, file safety, privacy, secrets, deployment order, and rollback. Cite file:line evidence, rank blockers first, and explicitly disagree where the plan does not match the real code.


## Persistent roadmap

The canonical suite roadmap is `C:\dev\born2thrill-app-repo\plans\ROADMAP.md`.

A task cannot be marked complete until unfinished in-scope work and every known out-of-scope follow-up are recorded there. Plan exclusion does not cancel work. A roadmap item is removed or completed only with evidence, and cancellation requires explicit user direction. Every final report names the next pending item or states that none remains.


# Agent Governance Rollout Plan

Status: APPROVED - approved by the user on 2026-07-31.

## Objective

Introduce a repeatable inspect-plan-approve-implement-review workflow for the ZuhauseFinder floorplan suite. It must keep Codex and Claude scoped, preserve existing work, and prevent unapproved geometry, restricted source material, customer email, database changes, or deployments.

## Inspected baseline

Inspection date: 2026-07-31 (Europe/Berlin).

| Component | Local path | Git baseline | Existing state |
|---|---|---|---|
| Deployable Born2Thrill app | C:\dev\born2thrill-app-repo | fix/customer-floorplan-output at a595ae37d3d6a2e01a35468cb66e4eb6bc756ee5 | two untracked Next server logs |
| Local correction workbench | C:\dev\born2thrill-local-workbench | agent/zuhausefinder-generator at 0c3255fa3f4d4d9c53dd5a5735078dc07e89c633 | substantial tracked and untracked implementation work; preserve all |
| Floorplan Simplifier | C:\dev\floorplan-simplifier | no Git repository | local-only annotations, source assets, exports, logs, and generated data |
| ZuhauseFinder WordPress | C:\dev\zuhausefinder-wordpress | agent/restore-hausprofil-wohnharmonie at d9df2b3ab3b70324d3bbe1b08e10a6ed6a296d84 | untracked artifacts directory |

The two Next.js roots currently contain only their Next.js version warning in AGENTS.md and import it from CLAUDE.md. The Simplifier has useful privacy rules but a stale macOS authoritative-project path. WordPress has neither instruction file.

## Exact implementation scope after approval

This rollout changes governance Markdown only.

1. Add a versioned shared workflow policy covering:
   - repository and instruction discovery;
   - baseline capture: repository, branch, base SHA, Git status and diff;
   - inspect-only Phase 1 and required plans/<task-id>.md contents;
   - explicit approval before code, tests, data, configuration, or external changes;
   - acceptance-test-first implementation after approval;
   - no deleting, skipping, weakening, or silently rewriting existing tests;
   - exact in-scope and out-of-scope declarations;
   - a circuit breaker after three distinct failed root-cause hypotheses;
   - final test, lint, type-check, build, status, diff, risk, and rollback reporting;
   - separate authorization for commit, push, deploy, migrations, destructive actions, secrets, and real email;
   - independent read-only Claude review.
2. Add or update one discoverable root AGENTS.md in every component.
3. Add or update root CLAUDE.md files to import AGENTS.md and require disagreement-first read-only review.
4. Preserve repository-specific instructions, including Next.js documentation lookup and Simplifier privacy/local-data rules.
5. Add a reusable plans/TEMPLATE.md to every component.
6. Give the policy a visible version so drift can be detected.

## Files likely to change

Deployable app:
- C:\dev\born2thrill-app-repo\AGENTS.md
- C:\dev\born2thrill-app-repo\CLAUDE.md
- C:\dev\born2thrill-app-repo\docs\agent-workflow.md
- C:\dev\born2thrill-app-repo\plans\TEMPLATE.md

Local workbench:
- C:\dev\born2thrill-local-workbench\AGENTS.md
- C:\dev\born2thrill-local-workbench\CLAUDE.md
- C:\dev\born2thrill-local-workbench\plans\TEMPLATE.md
- this plan file

Simplifier:
- C:\dev\floorplan-simplifier\AGENTS.md
- C:\dev\floorplan-simplifier\CLAUDE.md
- C:\dev\floorplan-simplifier\plans\TEMPLATE.md

WordPress:
- C:\dev\zuhausefinder-wordpress\AGENTS.md
- C:\dev\zuhausefinder-wordpress\CLAUDE.md
- C:\dev\zuhausefinder-wordpress\plans\TEMPLATE.md

If another file becomes necessary, stop, revise this plan, and obtain approval.

## Explicitly out of scope

- Application source, runtime behavior, tests, and fixtures.
- Simplifier projects, exports, failed uploads, reports, originals, annotations, logs, or generated packages.
- Workbench datasets, revisions, approved packages, geometry hashes, and runtime data.
- WordPress plugin, snippets, artifacts, media, database, requests, SMTP settings, and customer email.
- Railway, GitHub, DNS, OpenAI credentials, environment files, migrations, deployment configuration, production services, and live sites.
- Commit, push, pull request, deployment, migration, external message, or destructive operation.
- Repository consolidation, hooks, CI jobs, dependencies, or automation.

## Protected paths

- All .env files, credentials, keys, tokens, connection strings, and deployment variables.
- Simplifier projects/, exports/, failed-uploads/, and reports/.
- Workbench data/, revision stores, approved exports, correction schemas, validators, matchers, generators, and approval routes.
- WordPress plugin/, snippets/, artifacts/, media ingestion, send paths, storage, and approvals.
- Railway configuration, migrations, Git metadata, backups, rollback folders, and every pre-existing untracked file.

No rollout action may modify, move, delete, upload, commit, or publish anything in these paths.

## Floorplan-suite invariant

Every future plan must answer and prove:

> Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

The required answer is no, supported by code and test evidence.

Durable rules:
- Original annotations and source assets remain immutable internal records.
- Corrected millimetre geometry, revisions, approval, and publishable exports remain separate.
- Canonical JSON is the single geometry source for 2D and 3D/massing output.
- Restricted sources do not become commercially eligible merely by being imported.
- Customer delivery requires valid geometry, explicit human approval, safe JPEGs, and the existing WordPress manual email gate.
- Free generation, silent geometry guessing, database publication, image generation, or automatic customer sending cannot enter as incidental changes.

## Acceptance criteria

1. Codex started from each component root discovers AGENTS.md and accurately summarizes the shared and repository-specific rules.
2. Claude Code started from each component root discovers CLAUDE.md, follows AGENTS.md, and states that it must challenge unsupported assumptions before implementation.
3. Every component has a plans/TEMPLATE.md covering objective, evidence, exact scope, files in and out, acceptance criteria, tests, protected paths, contracts, rights/provenance, external effects, rollback, and unresolved questions.
4. The shared policy version is identical across all four rulebooks.
5. Existing Next.js and Simplifier-specific rules are retained and corrected.
6. No application, test, dataset, configuration, plugin, snippet, migration, deployment, email, or external-system file changes.
7. Pre-existing tracked and untracked changes remain untouched.
8. No secrets, raw floorplans, customer data, environment files, generated packages, or local runtime data are copied to governance files or Google Drive.
9. Final diffs contain governance Markdown only.

## Verification

After implementation, run read-only checks:

1. git status --short and git diff --check in every Git repository.
2. Compare post-change status to the baseline and confirm pre-existing files were not altered.
3. Search all four rulebooks for the policy version and mandatory gates.
4. From each root, ask Codex without write permission to list its instruction sources and approval boundary.
5. From each root, ask Claude Code read-only to list its instruction sources and Phase 1 no-edit rule.
6. Confirm the Simplifier command references the installed Windows runtime, not the stale macOS path.
7. Report unavailable commands; install no dependencies.

Application tests, lint, type-check, production builds, external calls, and live email are unnecessary because the diff must be Markdown only. Touching executable files is a scope violation.

## Implementation sequence after approval

1. Reconfirm Git baselines and record new user changes.
2. Write the canonical policy and template in the deployable app repository.
3. Update its root instruction files while preserving the Next.js rule.
4. Apply the same policy version to the local workbench without touching dirty implementation files.
5. Correct and extend Simplifier instructions without reading or modifying corpus assets.
6. Add WordPress instruction files without touching application or customer paths.
7. Run verification.
8. Produce a review bundle: plan, base SHAs, before/after status, governance diffs, verification output, risks, and rollback.
9. Send the bundle to a fresh read-only Claude review. Do not fix findings outside this plan.

## Repair circuit breaker

An attempt counts only when it is a distinct root-cause hypothesis with the exact command, output, and conclusion. Repeated environmental failure is one attempt. After three distinct failed hypotheses, stop and report completed work, the exact blocker, and the single next user action.

## Rollback

Restore only the governance Markdown files named here or delete newly added governance files. Never include pre-existing modified or untracked files in rollback.

Targeted rollback before any later commit:
- Deployable app: run `git -C C:\dev\born2thrill-app-repo restore -- AGENTS.md CLAUDE.md`; then remove only `C:\dev\born2thrill-app-repo\docs\agent-workflow.md` and `C:\dev\born2thrill-app-repo\plans\TEMPLATE.md`.
- Local Workbench: run `git -C C:\dev\born2thrill-local-workbench restore -- AGENTS.md CLAUDE.md`; then remove only `C:\dev\born2thrill-local-workbench\plans\TEMPLATE.md` and this rollout plan if the plan itself must be rolled back.
- WordPress: remove only the newly added `C:\dev\zuhausefinder-wordpress\AGENTS.md`, `CLAUDE.md`, and `plans\TEMPLATE.md`.
- Simplifier: restore only the pre-rollout AGENTS.md text captured in the Phase 1 inspection, then remove only `C:\dev\floorplan-simplifier\CLAUDE.md` and `plans\TEMPLATE.md`.
- Never use `git clean`, `git reset --hard`, a broad `git restore .`, or deletion of an entire plans directory. All four work areas contain user-owned or local-only material.

## Approval record

Approved by the user on 2026-07-31. Implementation is limited to this plan.


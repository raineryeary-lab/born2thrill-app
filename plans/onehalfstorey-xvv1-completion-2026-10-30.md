# Finish onehalfstorey_xvv1 after approved furniture correction
Status: APPROVED by user 2026-10-30: Yes—adjust furniture and finish xvv1.
Policy version: ZF-AGENT-WORKFLOW-v1.0.0
## Objective
Resolve evidenced upstairs furniture/wall conflicts, rebuild verified model sources, finish ten-image set and upload internally without send.
## Evidence and baseline
Source layout stamp stale; footprint audit recorded in Codex workspace onehalfstorey-xvv1. Workbench branch agent/furnished-render-and-annotation-schema, base5be1a4e18956b9fb2e158bee82aa159898356e89. Existing dirty work preserved; git-before-completion.txt records status.
## Scope
Only xvv1 furniture/floor-1.json positions via existing save API, regenerated xvv1 artifacts, delivery images/catalog, audit records and roadmap. Preserve furniture types/counts/sizes/rotations; preserve annotations, walls/openings/camera. No runtime code/tests/dependencies edits. xvv2 stays paused.
## Acceptance and checks
Validate translated furniture footprints against current room geometry and openings; retain source and candidate snapshots. Refuse if geometry changes during work. Existing model build and delivery checks must run without bypass flags. Reopen fresh Blend sources and audit hashes/objects. Visually check final ten images, catalog and remote upload hashes.
## Rights and external effects
Internal upload explicitly authorized, no send/customer email/release/rights changes. Existing publication gates remain intact. No path changed to generate/publish geometry without existing approved reference checks; no bypass or runtime changes.
## Risks and rollback
Conservative footprints require doorway and wall-mounted fixture interpretation. Backup live furniture before save; only restore upon need if live file still matches our saved version. Old renders archived, never replace user source geometry manually. No code tests added because no code changes; use existing validators.
## Approval
User approved concrete position correction and finish/upload in current chat. No further upload permission needed. Record failures and pending items in roadmap.

## Build finding within approved furniture-fit scope
First rebuild after OG save stopped at EG stale stamp (25abadc83178 versus7861fe138def). The same approved position-only correction is required for floor-0.json, with kitchen run/appliance group maintained, fixture counts/sizes/orientations preserved and no wall/opening changes. EG backup already saved. Existing validators remain unchanged.

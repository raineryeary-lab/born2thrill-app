# onehalfstorey_xv image completion and upload
Status: APPROVED by user "ok upload", followed by explicit deletion of the marked short kitchen run in all EG styles.
Policy: ZF-AGENT-WORKFLOW-v1.0.0

## Objective and scope
Complete ten images (two exteriors, four styles each EG/OG), record source and visual audits, publish to existing plan onehalfstorey_xv using publish-renders.py without --send.
In scope: requested E:/ delivery folder, this task's workspace provenance, additive plan/roadmap documentation, ten WordPress media uploads.
Out of scope: application/runtime/test changes, source Blend/annotation edits, rights modifications, customer release/email, deletion of old media, commits/pushes.

## Evidence and baseline
Four source Blends reopened and rendered from saved cameras; contract hashes matched. Interior mesh count 582 (217 EG,365 OG). Source audit in workspace.
Workbench has17 pre-existing tracked modifications and many untracked files; app repo has pre-existing ROADMAP changes. Preserve all.
Current sources retain two source-occluded EG bathroom fixtures and partially occluded OG furniture; never falsely claim visibility.
User specifically removes EG marker18 kuechenzeile-0. This is a documented visual override, source immutable.

## Acceptance and verification
Exactly10 named PNGs at required sizes; whole-image export sizing only; visually inspect all final outputs. Preserve accepted01/07 bytes via rename. Hash all files; confirm remote plan, count, matching remoteSHA256, send=false.
Record actual per-image observations and limitations. Do not convert exceptions to false visible markers, and do not alter checker to accept them.
No new tests for image-only changes; run existing delivery inspection and document its actual result.

## Invariant and external effects
No application path changes; source geometry/camera untouched. Publication is explicitly requested internal catalog media only, never customer release. Existing publish-renders rights/send guard remains intact.
Risks: generative visual drift, source occlusion, legacy validator lacks status for explicit object removal/occlusion. Report accurately.
Rollback: identify new mediaIDs in upload log; any deletion requires separate instruction. Local prior review retained in workspace. No destructive cleanup.

## Approval record
User: "ok upload". Subsequent correction: "mach die weg sie ist doch nur im weg" refers precisely to short freestanding kitchen counter, carried across four EG styles.

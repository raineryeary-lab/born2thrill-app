# Doppelpultdach exterior correction rollout
Status: APPROVED scope by user 2026-10-24: start 056 then groups of about five.
## Objective / exact scope
Correct only roof-step construction in 27 existing exterior images across 25 currently certified houses; twostorey_052 excluded pending valid source. CSV is project/media manifest. Preserve existing composition, landscaping, furnishings, lighting and non-target images.
## Baseline
Workbench branch agent/furnished-render-and-annotation-schema, HEAD 5be1a4e18956b9fb2e158bee82aa159898356e89. Extensive pre-existing modified/untracked files; no application code touched. Generator fix supplied by Claude.
## Files in scope
Per-plan exterior images, review images, catalog/provenance and backup records under corrections; this plan and canonical roadmap. Temporary inspection scripts only. Immutable source blends read only.
## Acceptance / verification
Open each current exterior blend, record hash/camera/mesh count and confirm partial job. Compare corrected roof to source and rest of image to old upload. Preserve upper overhang; inset vertical zinc step to wall plane; L-house plaster exception. Save before/after and hashes. Replace only mapped exterior media, verify names/plan/count and remote bytes. No email or rights changes.
## Tests
No runtime/test changes. Source hash and per-image visual checks, output dimensions and post-upload integrity verification.
## Rights / external effects
Existing internal catalogue images only; no new commercial eligibility. No path/code changes enabling unapproved corpus generation. Existing rights status preserved; no --send. Existing media backed up before any replacement.
## Risks / rollback
Image model drift requires per-image review. Existing publisher skips files; determine supported replacement before external changes. Restore backed-up image bytes and metadata if replacement fails. Never delete unrelated images.
## Approval
User approved rollout after discussion of scope and replacement process; no further approval required for that scope. Separate unrelated stair repairs excluded.

## Completed 2026-10-24
All 25 certified houses / 27 mapped exterior images replaced and verified. twostorey_052 remains excluded. Each current source blend opened, checksum verified again at completion; local deliveries synchronized. Native WordPress sideload/finalize retained media IDs for 26 images; first 056 replacement used reversible archive of 1182 and new canonical ID 1194. Existing release states preserved; no release/email calls.
Final audit: CODEX-RUECKMELDUNG-VERSATZ-PULTDACH-2026-10-24/BILDAUSTAUSCH-NACHWEIS.json and bildaustausch-status.csv. Visual comparison: BILDAUSTAUSCH-VERGLEICH.html.
Scope interpretation: existing accepted composition remains authoritative per partial order. In particular, 060 retains its previously accepted roof orientation and stainless balcony railing; new baseline was used to check the recessed-step construction, not to redesign the accepted exterior. Visual review is not a pixel-exact or metric geometry certification of generated images.

## Final completion including 052 — 2026-10-24
User supplied and authorized certified 052 source and partial order. Opened current blend: 113 meshes, SHA256 4f8d1e3d0f37f832780ca6a9e174e893bbc5f314c22c46e0a00dde800ee3fa94. Roof-step-only built-in image edit exported 1920x1080, native WordPress replacement retained ID 576, release state, metadata and other catalogue entries. Full image and all thumbnails verified. Final audit now verifies 28 online images across all 26 houses; none pending in this rollout. Original bytes and metadata retained in roof-step-review-20261024 for rollback. No source or application code edited; existing dirty worktree preserved. Evidence and gallery updated.


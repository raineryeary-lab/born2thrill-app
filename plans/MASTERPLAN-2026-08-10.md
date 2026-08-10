# ZuhauseFinder Masterplan — 2026-08-10 (v3, execution protocol)

## ⛔ READ THIS FIRST — protocol for EVERY session, EVERY model

**Session start (mandatory, in order):**
1. Read this file top to bottom.
2. Read `plans/ROADMAP.md` (same folder) — but treat rows as possibly stale; verify against code before acting on any row.
3. Read the newest `HANDOFF-*.md` in `born2thrill-local-workbench/plans/`.
4. State to the user which ONE task you are picking up, and from which phase, BEFORE touching anything.

**Hard rules (no exceptions, no interpretation):**
- **R1 — One task at a time.** Never start a second task before the first has passed its evidence gate.
- **R2 — Look before you claim.** "Fixed" requires evidence: a render you actually opened and inspected, a test run you pasted, a screenshot. A claim without evidence is a lie by default.
- **R3 — Whole-image check.** When verifying a render, inspect the ENTIRE image against the reference/defect list — not just the one spot you changed. (Weekend failure mode: fixed one red circle, missed five.)
- **R4 — Three strikes.** After 3 failed root-cause hypotheses, STOP. Write down each hypothesis + command + result, hand off. Do not guess a fourth time.
- **R5 — Ask what, not how.** If the user's intent is ambiguous (e.g. "symbols" = flat white icons vs 3D top-down renders), show ONE example and get confirmation BEFORE producing 96 of them.
- **R6 — Real state beats documents.** ROADMAP said "not done" for 3 things that were done. `git log` + reading the code is truth; documents are hints.
- **R7 — Never touch geometry, approval state, exports, or customer delivery outside an approved plan** (ZF-AGENT-WORKFLOW-v1.0.0 stands).
- **R8 — Update the trail.** Before ending a session: update ROADMAP rows you have evidence for, write/refresh a HANDOFF file, save session facts to memory. The next session (possibly a dumber model) must be able to continue with zero conversation context.
- **R9 — Symbols/furnishing are presentation-only.** They NEVER enter `geometry_hash`.
- **R10 — Don't multiply before Stage 1 is proven.** No finish variants, no classic swap, no batch renders while the single modern variant still has open defects. A bug shipped 6× costs 6× to fix.

**Evidence gate template (every task exits through this):**
```
TASK: <id/name>
CHANGED: <files>
VERIFIED BY: <command run / image opened / test output — pasted, not described>
WHOLE-IMAGE CHECK: <done/na>
ROADMAP UPDATED: <row(s)>
NEXT: <the single next task>
```

Goal: A customer answers the WordPress questionnaire and receives an approved house package:
- 2D simplified floorplan concept
- Furnished 3D dollhouse renders — **modern (2 interior variants) + classic (2 interior variants)**
- Photorealistic exterior — **1 modern + 1 classic**
- Delivered via the manual WordPress email gate, human-approved, geometry-locked.

v1 of this plan was reviewed against the actual code on 2026-08-10. Findings: the canonical ROADMAP is two days stale — window_type→sill wiring, the Tripo disk guard, and the FBX catalog run (1160/1160 measured) are **already done**. This v2 reflects the real state. Roadmap IDs in brackets.

**Note:** the 4 interior variants (modern A/B, classic A/B) are new scope with no roadmap ID yet. The picks table schema already exists (`dmh-symbol-model-picks-v2`) with one pick per style — the work is extending it to A/B, not designing it.

---

## Phase 0 — Protect the work (½ day)

> **ENTRY:** Rainer authorizes commits. **EXIT:** `git status` clean (or intentionally dirty with a written reason) in all three repos + ROADMAP corrected. Evidence: paste `git status` of all three.

All three roots ARE git repos (v1 claimed otherwise — wrong). The real exposure is uncommitted residue:

1. **Commit the 08-09/08-10 residue** [COMMIT-BASELINE-002] — ~170 dirty/untracked files across the three repos. Biggest risk: floorplan-simplifier (9 modified, 39 deleted SVGs, 154 untracked). Needs your authorization.
2. **Fix roadmap path** [ROADMAP-PATH-001] — 3 AGENTS.md files point at `C:\dev\born2thrill-app-repo\...` which doesn't exist (real path is under `Floorplan-tools`). Also fix GENERATOR-BLENDER-001's plan path.
3. **Update ROADMAP.md** — mark TRIPO-SKIP-GUARD-001, FBX-LIBRARY-001 done and correct ANNOTATION-SCHEMA-001/COMMIT-BASELINE-002 evidence, so no future plan is built on stale rows again.

## Phase 1 — Finish annotation tooling (this week)

> **ENTRY:** Phase 0 done (protects this work). **EXIT:** all 95 symbols placeable in the palette with measured footprints; one symbol added end-to-end as proof costs ONE edit, not four. Evidence: browser screenshot of palette + the one-edit demo.

Gate before the 90–100 new annotations: **not** the schema (landed 08-08/09), but:
- The palette consolidation below must not change annotation-side symbol keys — if it does, it lands first.
- Visual re-check of symbols placed before the depth-scale fix [ANNOTATION-SYMBOLS-005 follow-up].
- Entrance-width decision (below).

1. **Wire the 95 new 3D symbol renders into the palette** — PNGs exist in `static/symbols/`, but the palette (`static/symbol-catalog.js`, 40 hardcoded entries) doesn't know them, and each symbol costs 4 synchronized edits (symbol-catalog.js ×4 tables, app.py, symbol_footprints.json, symbol_detection.py). Collapse to one Python-served source, then register the new models (office chairs etc.) with measured footprints from the picks/catalog data — not guessed sizes.
2. **Entrance width decision** [ENTRANCE-WIDTH-001] — you decide: grandfather the 8 approved plans at 1100 mm, or re-approve at 1130 mm (changes their plan IDs; one is live in the WordPress POC).
3. **Test debt** [TEST-DEBT-001] — resolve the 5 pre-existing failures (re-verify they still fail first).
4. **Empty packages** [EMPTY-PACKAGES-001] — you re-upload the 9 real lost sources, or authorize removal of those + 5 test artifacts.

## Phase 2 — Render pipeline production-ready (parallel with Phase 1)

> **ENTRY:** none (parallel with Phase 1) — but R10 applies inside it. **EXIT:** one modern variant with ZERO open defects on the whole-image check against the boss's reference renders, plus depth/edge passes written, plus one ComfyUI-polished image Rainer approves. Evidence: side-by-side image pair shown to Rainer.

Follows the staged order in `plans/variant-pipeline-rollout-v1.md` (proposed 08-09, Codex-reviewed): **Stage 1 → Stage 5 → small ComfyUI pilot → Stage 2 → 3 → 4 → full ComfyUI → budget lock-in.** Deliverable shape: **6 images per home** (modern ×2 finishes, classic ×2 finishes, 2 exteriors) — at 100 plans that's 600 renders, so a bug fixed before multiplication is a bug fixed once, not six times.

1. **Stage 1 — one variant fully correct.** Clear the 7 defects in `plans/remaining-render-defects-v1.md`: openings not cut into walls, door swing ignored, Küchenzeile off its wall, missing desk chair, 12/35 furniture as white boxes, no kitchen cabinet fronts, windows render as one sheet. Plus wall-junction notch (#12); re-verify glass (#9) and the old "7 placements → 2 rendered" bug (likely superseded by the rebuilt pipeline).
2. **Stage 5 (moved up) — depth + edge passes** in the same render call, once Stage 1 geometry is trusted — these feed ComfyUI.
3. **ComfyUI pilot BEFORE multiplying variants** — polish pass on Stage 1's images at `E:\_comfyUI` (RealVisXL V5, SDXL canny ControlNet; **depth ControlNet still missing — must be downloaded**). Codex's starting parameters are recorded in the rollout plan (denoise 0.25–0.35, canny 0.70–0.85, depth 0.35–0.55).
4. **Stage 2 — second finish variant** (material swap only, low risk), then **Stage 3 — classic model swap** (needs full per-piece verification — different models, same chirality/facing risk as the corner-sofa bug), extending `data/symbol-model-picks.json` to A/B variants per style.
5. **Residual texture-path issues** — re-scope what actually remains (bulk fix landed; some bump/reflect maps still 404 during renders).
6. **Staging/decor layer** (new scope, from boss's reference renders 08-10): rugs, plants, wall art, table decor — presentation-only, never in `geometry_hash`. Reference also shows **balcony/Dachterrasse rendered with glass railing + decking**; Simplifier annotates these but the render pipeline doesn't build them yet.
7. **Studio look**: clean white background, isometric-style camera, crisp white wall caps (ties into notch fix #12) — this is most of the perceived "professional" difference and partly what the ComfyUI pass buys.

## Phase 3 — Corpus, generator, approvals (the actual critical path to selling)

> **ENTRY:** items 2–3 anytime; item 4 (new annotations) only after Phase 1 EXIT. **EXIT:** generator smoke test green end-to-end; approved catalog > 1 record. Evidence: smoke-test output + catalog record count.

1. **DATASET-EXPORT-001** [P0, IN_PROGRESS] — promote the validated v2 export into the main generator, add the dimension-recovery stage, run one end-to-end smoke test. *v1 of this plan omitted it entirely; it's the biggest structural dependency for the questionnaire matching anything.*
2. **Finish 3 CubiCasa drafts** [SIMPLIFIER-REVIEW-001].
3. **Grow approved catalog past 1 record** [APPROVED-CATALOG-GROWTH-001] — mechanism exists, pure process; directly multiplies what customers can receive.
4. **Corpus growth** [CORPUS-GROWTH-001] — the ~200 new annotations, after Phase 1 gates.
5. **BV Bach measured house** [MEASURED-PDF-001] — you trace polygons; then hard validation.

Deliberately deferred (not silently dropped): REPO-STRUCTURE-001 (monorepo consolidation — 8 files diverging between the Next.js roots; watch divergence during Phases 1–2), WORKBENCH-BASELINE-001.

## Phase 4 — Exteriors (= rollout Stage 4)

> **ENTRY:** Phase 2 EXIT + Rainer's provider decision. **EXIT:** one modern + one classic exterior Rainer approves. Evidence: the two images.

Façade view + geometry lock are already approved elsewhere. Needs geometry that doesn't exist yet (roof, facade material, front door via `role: main_entrance`, exterior windows) — its own plan, per the rollout's Codex review.
1. **Approach decision** — local Blender + ComfyUI polish (same pipeline as interiors) vs external rendering API [GENERATION-PIPELINE-PHASE2-001]; you choose, including cost ceiling.
2. **Exterior POC** [EXTERIOR-POC-001] — one modern + one classic exterior from the approved plan, geometry-faithful.
3. **Then full ComfyUI at scale + budget lock-in** (rollout Stages 6–7) — production budget set from a measured 30–60 image batch, not the placeholder 5–30 min range.

## Phase 5 — Package and deliver

> **ENTRY:** Phases 2+3+4 EXIT. **EXIT:** one complete package (2D + 4 interiors + 2 exteriors) through questionnaire → approval → manual email gate, live. Evidence: the delivered package + Rainer's sign-off.

1. **Package definition** — per approved plan: 2D concept + 4 dollhouse renders (modern×2, classic×2) + 2 exteriors, as safe JPEGs.
2. **WordPress proof** [WORDPRESS-POC-001] — questionnaire → matched plan → package → human approval → manual email gate. Live deployment separately authorized.
3. **Variants** [VARIANT-REVIEW-001, ENTRY-WARDROBE-VARIANT-001] — only from approved corrected plans, later.

---

## Standing rules (unchanged)
- No free geometry generation, no auto-send, no publication without human approval.
- Canonical JSON stays the single geometry source; symbols/furnishing never enter `geometry_hash`.
- Every implementation task still gets its own approved plan per ZF-AGENT-WORKFLOW-v1.0.0.

## Decision list for Rainer (everything that blocks on you)
1. Authorize the residue commits (Phase 0).
2. Corpus backup destination [CORPUS-BACKUP-001]: BitLocker / encrypted archive / offline.
3. Entrance width: grandfather vs re-approve.
4. Empty packages: re-upload or remove.
5. Exterior approach: local Blender+ComfyUI vs external API, + budget (Phase 4).
6. ComfyUI pilot decisions (rollout plan lists 10 open questions): fixed checkpoint/sampler/seed policy, geometry-drift tolerance, 600-render batch failure/resume behaviour, the exact 6-output matrix + filenames.

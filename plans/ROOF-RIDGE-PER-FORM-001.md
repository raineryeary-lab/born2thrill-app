# Firstlinien per roof form (Satteldach / Pultdach / Versetztes Pultdach)

Status: IMPLEMENTED AND VERIFIED on 3_5_1_b_145 (incl. ridge-cap follow-up, approved "fix it")

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-04: "es muss möglich sein unterschiedliche Firstlinien pro Dachform
einzuzeichnen, Standard wenn leer, aber Versetztes Pultdach und Satteldach auf jeden Fall."

Each roof form gets its own drawn ridge lines. Lookup order at render time:
1. the lines drawn for **this** form,
2. otherwise the shared lines (`roof_ridge_paths`, today's field, so existing houses stay as they are),
3. otherwise automatic wing detection (today's default).

## Current evidence and behavior

- `floorplan-simplifier/static/annotate.js:568` has one global `roofRidgePaths`, saved as
  `roof_ridge_paths` (3625) and loaded at 3682/4030.
- `dach-editor.js:109` already has `currentForm` (satteldach/pultdach/doppelpultdach), and
  roof *profiles* are already stored per form (`roofProfiles[currentForm]`, 337). Ridge
  lines are not: drawing/deleting (1293-1308, 486-490) always edits the one global list.
- `build-simplifier-render-plan.py:3835-3904` copies `roof_ridge_paths` into
  plan-modern/plan-classic.json.
- `render-exterior.py:1439-1456` reads `plan["roof_ridge_paths"]` regardless of roof_type,
  which comes from `EXT_ROOF_TYPE` per exterior render.
- 3_5_1_b_145 today: `roof_ridge_paths` = 2 lines (saved 09:13), the same for every form.
  The 08:46 Satteldach/Doppelpultdach renders predate those lines and still used auto-detection
  (log: "footprint massing: 2 rectangle(s)", no ridge-path line). That is the defect in
  ROOF-L-JUNCTION-RIDGE-001.

## Repository baselines

- floorplan-simplifier: files in scope are checked for git state before editing. Before any
  edit, each one gets a `.before-ridge-per-form` copy.
- born2thrill-local-workbench, branch `agent/furnished-render-and-annotation-schema`,
  HEAD 5be1a4e, 256 pre-existing dirty/untracked entries (user-owned, untouched).
  `render-exterior.py` is untracked, so it gets a `.before-ridge-per-form` copy.

## Exact scope

1. **Data:** new optional field `roof_ridge_paths_by_form`: `{satteldach: [...], pultdach: [...],
   doppelpultdach: [...]}`, same point format as `roof_ridge_paths`. A missing or empty entry
   means "not drawn for this form".
2. **Annotator UI (Dach tab):** the Firstlinien tool edits the lines of the form selected in the
   "Dach – Seitenansicht" buttons. The status line says which form is being drawn, and whether
   that form uses its own lines, the shared lines or automatic detection.
   "Firstlinie löschen" / "alle löschen" act only on the current form. The existing shared
   lines stay visible (greyed) as the fallback, so nothing gets lost.
3. **Render plan:** `build-simplifier-render-plan.py` passes `roof_ridge_paths_by_form`
   through (normalized to metres, like today).
4. **Renderer:** `render-exterior.py` picks
   `by_form[roof_type]` → `roof_ridge_paths` → auto, and logs which source it used
   (`[exterior] Firstlinien: eigene (satteldach) | gemeinsam | automatisch`).

## Files in scope

- `floorplan-simplifier/static/annotate.js`, `dach-editor.js` (+ `annotate.html` only if a label is needed)
- `floorplan-simplifier/app.py` only if the save endpoint whitelists annotation keys (to be checked first)
- `born2thrill-local-workbench/scripts/build-simplifier-render-plan.py`
- `born2thrill-local-workbench/scripts/render-exterior.py` (ridge-path source selection only)
- New tests for the selection order and the plan pass-through

## Explicitly out of scope

- Roof geometry construction (`chevron_roof_construction`, `roof_wings_from_ridge_paths`).
- The automatic-detection L defect (ROOF-L-JUNCTION-RIDGE-001). It stays pending in the
  roadmap and only matters when no lines are drawn.
- Walmdach/Flachdach (they don't use ridge lines).
- Re-rendering anything beyond the 3_5_1_b_145 verification build. No upload.

## API, schema, and data-contract effects

One additive optional key in `annotations.json` and in plan-*.json. Old files without it
behave exactly as today.

## Acceptance criteria (measured against what Rainer sees)

1. In the annotator, select Satteldach and draw lines A, then select Versetztes Pultdach and draw
   lines B. After save + reload, each form shows its own lines, and `annotations.json` has both
   under `roof_ridge_paths_by_form`.
2. A form with nothing drawn shows "gemeinsam" or "automatisch" and renders exactly as today.
3. 3_5_1_b_145: Satteldach and Doppelpultdach exteriors are rebuilt. The log names the
   source per form, and a Blender probe confirms the built ridge lines match the drawn lines
   for that form, the same lines the editor shows. Whole-image check of both renders.
4. Existing tests (roof_profile/roof_wings/roof_wings_multi) stay green and unchanged.

## Tests and verification commands

- New: selection order (own → shared → auto), empty-list handling, plan pass-through.
- `python scripts/roof_profile.test.py`, `python scripts/roof_wings.test.py`,
  `python scripts/roof_wings_multi.test.py`
- Live: annotator in the browser pane (draw/save/reload per form), then the go-baseline exterior
  build + Blender probe for 3_5_1_b_145.

## Protected and risky paths

Saving annotations. Mitigation: the new key is additive, and `roof_ridge_paths` is still
written unchanged.

## Rights, provenance, privacy, and security impact

None.

## Floorplan-suite invariant

No. This only chooses which drawn lines feed the local roof build. Nothing is published,
uploaded or emailed, and the approval/rights gates are untouched.

## Customer, email, database, deployment, and external effects

None.

## Failed-hypothesis log

(empty)

## Rollback

Restore the `.before-ridge-per-form` copies. Old annotations are unaffected (the key is additive).

## Unresolved questions

- Should Pultdach (single slope) also get its own lines? Planned: yes, same mechanism, it costs nothing extra.

## Approval record

Approved by Rainer in chat, 2026-10-04 ("ja").

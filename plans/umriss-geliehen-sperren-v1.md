# Annotator: borrowed outline on upper floors is read-only

Status: DONE 2026-11-07

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-07: "it seems wrong that I can edit the outline of the automatic bottom floor outline in the upper floors".

## Current evidence

- `floorplan-simplifier/static/annotate.js` 2897 `outlineForFloor()`: a floor without its own outline borrows another floor's outline.
  - If both floors have `floor_alignment`, it returns a transformed COPY.
  - If either floor lacks it (2904), it returns the SOURCE ARRAY ITSELF.
- `punkte-ausrichten.js` 123 `umrissTraeger()`: the outline counts as editable whenever `outlineForFloor(activeFloor) === outerOutline`.
  - In the no-alignment case that test is true on the upper floor too.
  - So on the OG you can select, align and nudge the EG outline's points, and the moves land in the EG outline.
- `syncLegacyOutlineAliases()` (annotate.js 693) already knows the case: `outerOutlineFloor` is set exactly when the outline is borrowed.

## Exact scope

1. `umrissTraeger()` returns null when `outerOutlineFloor` is set (borrowed outline). Points are editable only on the floor that owns the outline.
2. The status hint `umrissHinweis()` then says, as it already does, "Der Aussenumriss ist hier nur umgerechnet zu sehen -- bearbeiten geht auf "groundfloor"".
3. Drawing a NEW outline on the upper floor stays possible (`setOuterOutline`, annotate.js 3131). It creates that floor's own outline, for a real setback.
4. Cache version of punkte-ausrichten.js in annotate.html bumped.

## Out of scope

- No data change. Saved outlines stay as they are.
- No change to the matrix rule "floor without own outline uses the EG one".

## Tests (first)

- `static/umriss-geliehen-sperren.test.mjs` (seam): `umrissTraeger()` checks `outerOutlineFloor` before handing out a carrier.
- The existing punkte-ausrichten.test.mjs stays green.

Real: in a house without floor_alignment, on the OG, frame-select the outline: 0 points, plus the hint. On the EG: the points can be selected. Nothing saved.

## Safety gate

UI lock only. It writes no data and changes no geometry.

## Rollback

`punkte-ausrichten.js.before-umriss-geliehen`, annotate.html backup; remove the test.

## Approval record

Rainer in chat, 2026-11-07: "Yes, build it".

## Implementation record (2026-11-07)

- punkte-ausrichten.js `umrissTraeger()`: returns null when `outerOutlineFloor` is set, i.e. when the outline is borrowed.
- annotate.html: punkte-ausrichten v=20261107-1.
- Tests first: static/umriss-geliehen-sperren.test.mjs 3. Before the fix 2 were red; after it, all green. The test runs the real function.
  - static: 447/447;
  - tests/: 393 OK.
- Survey: 10 floors borrow the SAME list (no floor_alignment), e.g. onehalfstorey_012/028/033 upperfloor. These are the ones where OG edits moved the EG outline. 53 more borrow a copy, where edits went nowhere.
- Live check, onehalfstorey_012:
  - on the EG, the outline is editable;
  - on the OG, the shared list gives no carrier and shows the hint 'bearbeiten geht auf "groundfloor"';
  - the EG outline is unchanged and nothing was saved.

# Möbel: Speichern geht auch, wenn sich nur die Räume geändert haben

Status: DONE 2026-10-22

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-22, onehalfstorey_vv1: the build refuses ("die RAEUME dieses Geschosses wurden umgezeichnet ... einmal speichern"), but in the Möbel step "Speichern" is greyed out -- nothing was moved, so the editor thinks there is nothing to save. Request: "Speichern is enabled when the furniture's stored room stamp is older than today's rooms, even without moving anything."

## Current evidence

- `src/app/floorplan-workbench/furniture.tsx useFurniture`: `dirty` only becomes true after a change (mutate/zurueck); the Speichern button is `disabled={!dirty || !geometryReady}`; "Weiter zu Bauen" only saves when dirty.
- The loaded furniture document carries `geometry_identity` (vv1 floor-1: 59b6bc038df4); the editor knows the identity it displays (`setDisplayedGeometryIdentity`, vv1 upperfloor: 5c295aa91b8a). They differ -> the build's stale check refuses, and nothing in the UI lets the user re-save.
- Server save (`corrections/route.ts`) already re-stamps with the displayed identity and refuses only if display and today differ -- so saving here is safe.

## Exact scope

1. `src/lib/generator/furniture-document.mjs`: `moebelVeraltet(document, angezeigteIdentitaet)` -> true when the document has symbols, a stored `geometry_identity`, and it differs from the displayed one.
2. `useFurniture`: keep the displayed identity also as state; return `dirty: dirty || moebelVeraltet(...)` so Speichern is enabled and "Speichern und weiter" saves. Status line says "Räume geändert -- einmal speichern."

## Tests (first)

`scripts/furniture-document.test.mjs` (+ new cases): stale stamp -> true; same stamp -> false; no symbols -> false; no stored stamp -> false. Seam: furniture.tsx uses `moebelVeraltet(`.
Real: vv1 upperfloor in the Möbel step -> Speichern enabled without moving; after Rainer's (or the button's) save floor-1.json carries 5c295aa91b8a and the build continues.

## Safety gate

No geometry is published; furniture save only, with the existing server checks.

## Rollback

`furniture.tsx.before-veraltet-speichern`, `furniture-document.mjs.before-veraltet-speichern`; revert the test cases.

## Approval record

Rainer in chat, 2026-10-22: "Yes: plan and fix it so Speichern is enabled when the furniture's stored room stamp is older than today's rooms, even without moving anything."

## Implementation record (2026-10-22)

- `furniture-document.mjs moebelVeraltet()`; `furniture.tsx` keeps the displayed identity as state too and returns `dirty: dirty || veraltet` plus the status "Räume geändert — einmal speichern.".
- Tests first: furniture-document.test.mjs +2 (red before, 17/17 after). tsc: no errors in the touched files.
- Live: vv1 Möbel step, upperfloor, nothing moved -> "11 platziert", Speichern enabled, "Speichern und weiter", status shown. Not saved by me.

# Maßstab-Fenster: „Seitenverhältnis sperren“ auch ohne Vorschaubild

Status: DONE 2026-11-06

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-06: "seitenverhältnis sperren läßt sich nicht aktivieren" -> "makes no sense" -> "Yes, build it" (lock keeps the drawing's current proportion, the same one the m² use; only width is typed).

## Current evidence

`floorplan-simplifier/static/massstab-fenster.js` `neuRechnen()`: when `seitenverhaeltnisGeraten()` (proportion source "platzhalter"), the lock is unchecked and disabled. `massGesperrteHoehe()` already computes the depth from `gezeichnetesVerhaeltnis()` -- the drawn proportion.

## Exact scope

1. The lock is never disabled and never unchecked by the code; with an unknown proportion it starts unchecked but can be switched on.
2. Locked with an unknown proportion: depth follows the width with the DRAWN proportion; hint "Proportion aus der Zeichnung übernommen (nicht gemessen) – die Zeichnung bleibt, wie sie ist."
3. Unlocked with an unknown proportion: today's hint (enter both from the Beiblatt).
4. annotate.html cache version bumped.

## Tests (first)

`static/massstab-sperre-immer.test.mjs`: seam -- `neuRechnen` no longer sets `sperre.disabled = geraten` nor unchecks; the new hint text exists. Existing massstab tests stay green; tests/ OK.
Real: a house with source "platzhalter": lock can be ticked, depth follows width.

## Safety gate

Changes geometry only on Rainer's Anwenden, as today.

## Rollback

`massstab-fenster.js.before-sperre-immer`, cache version back; remove the test.

## Approval record

Rainer in chat, 2026-11-06: "Yes, build it".

## Implementation record (2026-11-06)

- massstab-fenster.js `neuRechnen()`: lock no longer disabled/unchecked; locked + unknown proportion -> new hint; `oeffnen()` starts the lock off when the proportion is unknown. annotate.html v=20261106-2.
- Tests first: static/massstab-sperre-immer.test.mjs 2 (red before, green after); massstab-* and gebaeudemass-zielgeschoss green; tests/ OK.
- Live bungalow_012 ("platzhalter"): opens 11.25 x 8.80, lock off but clickable; ticked + width 12 -> depth 9.38 (read-only), hint "Proportion aus der Zeichnung übernommen (nicht gemessen) ...". Closed with Abbrechen, nothing saved.
- Noticed: bungalow_003, bungalow_007, twostorey_030 carry exactly 10 x 10 as entered size (possibly the old default applied by accident) -- asked Rainer.

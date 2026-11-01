# deriveHouseState: one source of truth for the house list

Status: APPROVED (Ralph loop item 1 — plans/ralph-workflow-rebuild.md,
batch-approved by Rainer 2026-08-23: "do it then")

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Codex audit P0 (plans/workflow-audit-2026-08-22.md): the house list's
"fertig" came from WordPress alone (`images > 0 && approved === "ja"`),
ignoring whether the delivery still matches the annotation, the
furniture, the toolchain or the correction revision — a changed, refurnished
or broken house stayed "fertig". Four independent truths (file existence,
manifest, ledger, WordPress) were consulted in ad-hoc branches inside
`state/route.ts`. Replace the branches with ONE pure derivation fed by
gathered facts, with freshness answered by the SAME Python oracle go.py
uses (`built_hash()`/`annotation_state()`), not a TypeScript re-implementation.

## Exact scope

1. `scripts/haus-zustand.py` (new): `--alle` / `<plan>` → JSON
   `{plan: {zertifikat, aktuell, grund}}` using batch-build.py's
   `built_hash()`/`annotation_state()` via importlib (same as go.py). One
   process for the whole corpus.
2. `src/lib/floorplan-workbench/house-state.mjs` (new): `STATES`,
   `deriveHouseState(facts)` — pure, no I/O, returns `{state, blocker,
   action}`. Ordered gates: unbegonnen → keine_vorlage → vermessung_noetig
   → ausrichtung_noetig → baubereit (no certified delivery) → bau_veraltet
   (delivery not current) → wordpress_unerreichbar → warten_auf_codex
   (current delivery, no finals anywhere) → bilder_hochladen (local finals,
   not online) → bilder_freigeben (online, not all angehakt) →
   warten_auf_freigabe (angehakt, plan not approved) → fertig (approved AND
   current). "fertig" is impossible for a stale delivery by construction.
3. `src/lib/floorplan-workbench/house-state.test.mjs` (new): table-driven
   cases for every state plus the two invariants (stale never fertig;
   WordPress down never reads as "waiting for Codex").
4. `state/route.ts`: gathers facts (raster, rooms, levels, scale incl.
   gebaeudemass.json as the second Maßstab source, alignment marks,
   delivery freshness from haus-zustand.py, local codex-final images,
   WordPress bilder only for houses with a current delivery, catalogue
   row) and calls `deriveHouseState`. No state logic remains in the route.
5. `package.json`: `test:house-state` script.

## Out of scope

Active-revision binding (item 2), shared Python freshness module (item 3 —
haus-zustand.py is the bridge until then), Codex intake (item 4), dead-state
removal beyond what this derivation makes unreachable (item 7), UI label
changes in /haus (states render as strings today).

## Rights / suite invariant

Can any changed path generate, publish, or email geometry without an
approved reference? No — read-only derivation.

## Acceptance

- node --test house-state.test.mjs green; existing suites green; tsc clean.
- /api/floorplan-workbench/state: bungalow_039 (approved online, current
  delivery) → fertig; onehalfstorey_029 (current delivery, finals local,
  nothing online) → bilder_hochladen; a house with a manifest but changed
  annotation → bau_veraltet.

## Rollback

Delete the three new files, restore state/route.ts from this session's diff.

## Approval record

Batch approval, Rainer 2026-08-23 ("do it then"), item 1 of 7.

## Completion record (2026-08-23)

Implemented as scoped. `deriveHouseState()` + `STATES` in
`src/lib/floorplan-workbench/house-state.mjs` (pure, no I/O), 7 table-driven
tests green (`npm run test:house-state`), including the two invariants:
a stale delivery can never be `fertig`, and WordPress being unreachable is
its own state rather than "waiting for Codex". `scripts/haus-zustand.py`
bridges freshness from the SAME Python oracle go.py uses (batch-build's
`built_hash`/`annotation_state`), one process for the whole corpus;
`state/route.ts` now only gathers facts and calls the derivation — no state
logic left in the route. Maßstab accepts `gebaeudemass.json` as the second
legitimate source (Codex audit P2 fixed in passing).

Verified live over all 232 houses: counts
`{fertig 1, bau_veraltet 35, baubereit 54, ausrichtung_noetig 10,
keine_vorlage 118, unbegonnen 14}`. bungalow_039 read `bau_veraltet` while
WordPress still said approved (today's renderer edits invalidated its
delivery) — exactly the P0 the audit found — then returned to `fertig`
after `go.py bungalow_039`, proving the whole gate chain closes.

BUG FOUND AND FIXED DURING VERIFICATION: the first version of
haus-zustand.py compared `annotation_state()`'s TUPLE `(hash, grund)`
against `built_hash()`'s string, so every delivery read as stale — visible
only because go.py said "fertig" seconds after the route said "veraltet".
Now unpacked exactly like `go.py::ist_aktuell`. This is the audit's own
failure class (two readings of one contract) caught by cross-checking two
oracles against each other, which is why the verification compared them.

Files: `src/lib/floorplan-workbench/house-state.mjs` (new),
`src/lib/floorplan-workbench/house-state.test.mjs` (new),
`scripts/haus-zustand.py` (new),
`src/app/api/floorplan-workbench/state/route.ts`, `package.json`.

# Fertig bleibt fertig (mit Version und "Update verfügbar")

Status: IMPLEMENTED AND VERIFIED (house-state tests 25/25, ledger seeded with 32 houses, Hausakte shows teal fertig_update v1.0)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-04: "when we say a set is finished it stays finished, maybe in a different color with
update, but it still stays finished ... finished 1,0 or 1,1 depending on newer versions, but finished
stays finished and also freigegeben."

Once a house has reached "fertig", it never drops back into the open list again:
- A newer renderer or new images are shown as **"Fertig · Update verfügbar"** in a different colour.
  The house still counts as done (green family, still in the "fertig" count).
- Each finished house carries a version: **1.0** when it first became fertig, **1.1, 1.2 …**
  each time it becomes fully fertig again on a newer build or image set.
- Its catalogue release ("freigegeben") stays as it is. Nothing in this change unticks anything.

## Current evidence and behavior

- `src/lib/floorplan-workbench/house-state.mjs` `deriveHouseState()` re-derives the state from
  scratch on every load. "fertig" needs the build to be current, every uploaded image released, and
  the plan approved.
- So a finished house falls back to:
  - `bau_veraltet` when the toolchain hash in its delivery manifest no longer matches
    (`batch-build.py built_hash()`), e.g. after today's renderer changes. Only houses with catalogue
    `approved = ja` and images get the existing escape `veroeffentlicht_build_alt`.
  - `bilder_freigeben` as soon as a new image is uploaded without "an Kunden". This happened with
    every upload today (bungalow_001, 3_5_1_b_145, 3_1_2_b_85).
- Nothing records that a house WAS fertig, so there is nothing to keep it there.
- Right now (state API): 29 fertig, 3 veroeffentlicht_build_alt, 10 bau_veraltet.

## Exact scope

1. **Ledger** `fertig-ledger.json` in the workbench data dir (`FLOORPLAN_WORKBENCH_DATA_DIR`):
   `{plan: {version: "1.0", seit: <iso>, zuletzt: <iso>, build: <manifest hash>}}`. It is written
   by the state route only when `deriveHouseState()` returns `fertig`. It is never deleted, only
   moved up: the minor version bumps when the house is fertig on a different build than recorded.
   On the first run, every house that is `fertig` or `veroeffentlicht_build_alt` today is recorded
   as 1.0.
2. **deriveHouseState()** gets `facts.fertigLedger` (the plan's entry or null). If the house is in the
   ledger and the normal derivation would NOT be `fertig`, it returns the new state
   **`fertig_update`**, with blocker "Fertig v1.x · Update verfügbar (<Grund>)" and the reason
   (renderer newer / new images not released / build missing). The action keeps today's button
   (Bauen / Freigeben), but it is optional.
3. `fertig_update` goes into `ERLEDIGT` (counted as done) and sits in STATES right after `fertig`.
   The overview shows it in its own colour (teal) with the version badge. `fertig` rows also
   show their version.
4. Gates that mean the house is genuinely broken still win over the ledger, so "fertig" never hides
   them: no image/raster, no scale, missing alignment.

## Files in scope

- `src/lib/floorplan-workbench/house-state.mjs`, `house-state.test.mjs` (new tests; existing ones
  unchanged except the one that pins `ERLEDIGT` to exactly two states, see Tests)
- `src/app/api/floorplan-workbench/state/route.ts` (read/write the ledger, pass the fact through)
- `src/app/floorplan-workbench/overview/page.tsx` (+ the Hausakte badge if it shows the state): label
  and colour for `fertig_update`, version badge

## Explicitly out of scope

- WordPress: nothing is unticked, deleted or released by this change.
- What "fertig" requires the first time (unchanged).
- Build/certification logic in Python (unchanged).

## Tests

New, in `house-state.test.mjs`:
- a ledgered house that is stale stays done as `fertig_update`, with the reason "Renderer neuer"
- a ledgered house with new unreleased images is `fertig_update` ("neue Bilder nicht freigegeben")
- a ledgered house without a scale or raster still shows the real blocker
- a non-ledgered house derives exactly as today (all existing tables unchanged)
- version bump: fertig on a new build moves 1.0 to 1.1

The existing test `"erledigt sind genau fertig und veroeffentlicht_build_alt"` pins `ERLEDIGT` to
those two. It has to list `fertig_update` too. That is the one existing test that changes, and only
because this plan changes exactly that set (named here as required).

## Floorplan-suite invariant / external effects

No. This only changes status display and a local ledger file. No geometry is touched, nothing is
published, uploaded or emailed, and catalogue approval is not changed.

## Rollback

Restore the `.before-fertig-bleibt` copies of the four files and delete `fertig-ledger.json`.

## Approval record

Approved by Rainer in chat, 2026-10-07 ("ja freigabe erteilt für fertig bleibt fertig-001").

# DG-MIT-KNIESTOCK-001: EG + OG + habitable DG with knee wall (Vito-Max)

Status: PROPOSED (waiting for Rainer's OK)
Occasion: other_vito (Vito-Max from `_Original`), 2026-10-24.
- Rainer: the DG is a habitable top floor with roof slopes; "this one has a kneestock".
- Furniture step: "im missing the third floor".

## Causes (measured)

1. **The DG is left out.** `dachboden.abspalten()` (dachboden-ausbaureserve-v1, 2026-10-23, from bungalow_generationat) treats **every** `attic` level in a house that also has other levels as an unfinished attic. It builds only gable windows and takes the DG out of the house. The plan builder logs this for other_vito: "Dachboden (Ausbaureserve): Ebene attic wird nicht gebaut". So the furniture step only gets EG + OG.
2. **Floors are sorted alphabetically.** `build-simplifier-render-plan.py` sorts levels with `sorted({...floor_level})` in about 10 places. `attic` comes alphabetically before `groundfloor`, so a DG would be built as storey 0, and `furniture/floor-N.json` (N = position in that list) would sit on the wrong floor. The same pattern is in `go.py` (storey count) and in the workbench (`render_geometry`).

## Change

1. **One floor order** `basement < groundfloor < upperfloor < attic` as a shared function (`geschoss_reihenfolge`), used everywhere instead of `sorted()`: plan builder, go.py, workbench geometry.
   - Existing houses with EG/OG (and KG) keep their order exactly. Test: every current project gives the same order before and after.
   - Houses with only EG + attic keep the attic split off (rule 2). Their furniture index is unchanged.
2. **The DG rule gets narrower.** `attic` only counts as an unfinished attic when there is **no** `upperfloor` (EG + DG; GenerationAt stays as it is). With EG + OG + DG, the DG is a real top floor.
3. **DG under the roof.** If the top floor is `attic` and there is a storey below it:
   - the exterior builds it with the existing 1.5-storey logic (`anderthalb.py`: knee wall 1.0 m, pitch 40°, eaves = DG floor + knee wall) on top of the full OG
   - `ist_anderthalb()` also recognises this case (top level `attic`), not just by house type / ID prefix
4. **Dollhouse DG.** Walls only up to the knee wall, then roof slopes as in the 1.5-storey houses. To check: is that already built there for the top floor, or does it need adding?
5. **Furniture step.** The DG appears as the third floor (`floor-2.json`).

## Tests first

- `geschoss_reihenfolge`: attic last; EG/OG/KG unchanged.
- dachboden: EG + attic → split off (as before); EG + OG + attic → not split off.
- Plan builder with other_vito: 3 floors in the order EG, OG, DG; the DG carries the 1.5-storey marking.
- Regression: GenerationAt, 1_5_1, 1_1_2, 1_6_1, twostorey_053 give the same floor order and the same furniture assignment as today.

## Proof

- Build other_vito (EG, OG, DG).
- Exterior view: knee wall visible, DG under the roof.
- DG dollhouse view.
- Furniture step: three floors.
- No upload.

## Risk

The floor order touches the plan builder, go.py and the workbench. That's why the regression test covers every current project: no existing house may change its order or furniture assignment.

## Rollback

`*.before-dg-kniestock` per file.

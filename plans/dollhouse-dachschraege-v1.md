# Dollhouse 1,5-Geschosser: Wände folgen der Dachschräge

Status: DONE 2026-10-22

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-22 (vv1, upper-floor Blender file): "why are the walls so chopped off?" -- answer to the choice: **"Slope like the roof"**: walls rise from 1.0 m at the eave along the 40° roof line, so the Dachschräge can be read.

## Current evidence

- `render-furnished-dollhouse.py` ~3691-3763: on the top floor of a 1,5-Geschosser, boxes ("ah-kniestock-kappe") cut the EXTERIOR walls of the eave sides flat at 1.0 m (except under a Zwerch). Interior walls are not touched; they keep the normal dollhouse cut height. Result: low flat outer walls next to full-height inner walls -> "chopped".
- The same block computes its Zwerch positions itself with `anderthalb.giebel(...)` WITHOUT the drawn Quergiebel (`plan["quergiebel"]`) and without bays (`rechteck_mit_erkern`); it only runs for exactly 4 exterior walls. So for 045 (drawn east Quergiebel) and vm2 (Erker) the dollhouse and the exterior disagree.

## Exact scope (render-furnished-dollhouse.py + anderthalb.py)

1. Replace the flat boxes by one wedge per eave side: everything above the roof plane z = floor + 1.0 m + s·tan 40° (s = distance inward from that eave's wall line) is cut -- exterior AND interior walls, door/window frames that stick out above it too. The normal dollhouse cut height stays the upper limit, so near the ridge nothing changes.
2. Under each Zwerch (Quergiebel/Kubus) the wedge is left out over its width, as today -- but the Zwerch list now comes from the same call as the exterior: drawn Quergiebel and bays included (`gezeichnet=`, `erker=`, `rechteck_mit_erkern`).
3. Pure helper `anderthalb.dachschraege_keil(seite, bbox, boden_z, ...)` -> the wedge outline, tested.

## Out of scope

- Ceilings/sloped ceiling surfaces (the dollhouse has no ceiling), the exterior renders.

## Tests (first)

- anderthalb.test.py: wedge for a north eave: z at the wall line = floor + 1.0, rises with tan 40°, reaches the cut height at the right distance; for an Erker side the wedge starts at the bay front.
- Seam: dollhouse uses `dachschraege_keil(` and passes `gezeichnet=`/`erker=` to `giebel`.
- Real: rebuild vv1, 044, 045 interiors (scratch first): log line per house; look at the upper floors -- outer walls 1.0 m at the eave, inner walls sloping up, Zwerch areas full height; verifier green.

## Safety gate

Local renders only; nothing uploaded.

## Rollback

`render-furnished-dollhouse.py.before-dachschraege`, `anderthalb.py.before-dachschraege`.

## Approval record

Rainer in chat, 2026-10-22: "Approved: implement dollhouse-dachschraege-v1, tests first, check vv1, 044 and 045 (no upload)."

## Implementation record (2026-10-22)

- `anderthalb.dachschraege_keil()` (reuses `ueber_dach_profil`); dollhouse block replaced: one wedge per eave side cuts ALL walls above 1.0 m + 40 deg, gaps under every Zwerch; Zwerch list from `giebel(..., gezeichnet=plan["quergiebel"], erker=...)`, rectangle-with-bays accepted.
- Tests first: anderthalb.test.py +3 (one of my new tests had a wrong depth for its z filter -- corrected before implementing); all script suites green except the known door-hinge failure.
- Scratch + full rebuilds: vv1 "8 Waende, 2 Keile, 0 Zwerch", 044 "10 Waende, 3 Keile, 1 Zwerch north 4.64-7.88", 045 "9 Waende, 3 Keile, 1 Zwerch east 3.95-7.34" -- the same Zwerch extents as the exteriors; all three: 2 styles verified, 4 artifacts certified. Upper-floor renders looked at: low eave walls, inner walls and gable ends follow the slope.

# Obergeschoss-Kamera: Stempel nach dem Anheben

Status: IMPLEMENTED 2026-10-20 -- verified; not committed

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

A rebuilt upper floor must keep the automatic camera, and a real hand camera must stay exactly where Rainer put it. Today every rebuild of an upper floor moves the camera 2.62 m higher.

## Current evidence and behavior

Measured 2026-10-20 on twostorey_059, `interior-modern-upper-baseline.blend1` (11:31) and `.blend` (11:54):

| file | camera z in the file | z in its `zf_kamera` stamp |
|---|---|---|
| 11:31 | 51.224 | 48.604 |
| 11:54 | 53.844 | 51.224 |

The difference is exactly `STOREY_HEIGHT_M` (2.62 m). In `render-furnished-dollhouse.py`:

1. **The stamp comes too early.** `camera["zf_kamera"]` is written at about line 7236, BEFORE the storey elevation (about line 7459), which lifts every root object, the camera included, by 2.62 m. The saved file therefore never matches its stamp, so the next build calls it a hand camera and rescues it into `corrections/<haus>/kamera-innen-1.json`.
2. **The rescued position is applied in the wrong coordinates.** It is read from the saved file, i.e. AFTER the lift (world z), but applied BEFORE the lift, so it is lifted a second time. Each rebuild adds 2.62 m, and a camera Rainer really moved by hand drifts the same way.
3. The legacy branch (old files without a stamp) compares against the rule position `centre + dir * span * 6.1`, also before the lift. On an upper floor it would call every old automatic camera a hand camera as well.

The ground floor (lift 0) is not affected.

## Repository baselines

`born2thrill-local-workbench`, branch `agent/furnished-render-and-annotation-schema`, HEAD `5be1a4e`, user-owned dirty worktree (unchanged). `render-furnished-dollhouse.py` already carries this session's uncommitted Treppenloch work.

## Exact scope

- Move the `zf_kamera` stamp to directly after the storey elevation, so it records the camera exactly as saved.
- Keep the rescued json in world coordinates, as the file stores it (existing jsons stay valid). Apply it as `z - lift` before the lift, via a pure helper `kamera_vor_anhebung(loc, lift)`.
- Legacy branch: compare against the rule position plus the lift.
- Hand detection as a pure function `kamera_von_hand(alt, regel_loc, lift)`, so it can be tested.
- Reset twostorey_059: delete `corrections/twostorey_059/kamera-innen-1.json` (a false rescue). Then rebuild with `go.py` (no upload). (Changed during implementation: `kamera_von_hand` also accepts an old stamp plus exactly one storey height as "not moved", so the first rebuild already recognises the 11:54 file and no second reset round is needed.)

## Files in scope

- `scripts/render-furnished-dollhouse.py`
- `scripts/render-persp-test.py`: only if it has the same stamp code (checked; kept in step if so).
- New test `scripts/kamera_stempel.test.py`
- Data: `E:\born2thrill-local-workbench-data\corrections\twostorey_059\kamera-innen-1.json` (delete, approved by Rainer: "then reset twostorey_059's camera").

## Explicitly out of scope

- `render-exterior.py` (exterior cameras, no storey lift).
- Other houses with upper floors whose cameras already drifted. They are listed (scan for `kamera-innen-1.json` / `-2.json`) but not reset without Rainer's word.
- The camera rule itself (distance, lens, angle).

## API, schema, and data-contract effects

None. `zf-kamera-innen-v1` json unchanged (world coordinates, as before).

## Acceptance criteria

1. Tests: a camera equal to its stamp is not a hand camera; one moved by more than 2 mm is; a legacy camera at the rule position plus the lift is not; `kamera_vor_anhebung` then the lift gives back the saved position exactly; the stamp line comes after the storey elevation in the source.
2. twostorey_059: after the reset, two consecutive `go.py` builds give the same camera z in the upper .blend, with no "Handkamera ... gerettet" line in the second build's log. The upper render is framed like the ground floor (house filling the frame).

## Tests and verification commands

- `python scripts/kamera_stempel.test.py` (new, AST isolation)
- the existing suites: `render-furnished-dollhouse.test.py`, `treppenloch_*.test.py`, `verify_render_blend.test.py`
- two `go.py twostorey_059` runs plus a camera probe of the upper .blend

## Protected and risky paths

Toolchain hash changes (every build counts as outdated, already the case today). A real hand camera saved by the old code is in world coordinates, which the new apply step interprets correctly, so existing hand cameras land where they were seen.

## Rights, provenance, privacy, and security impact

None.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

No. Only the camera placement of a render changes; no geometry, approval, publication or email path is touched.

## Customer, email, database, deployment, and external effects

None. No upload.

## Rollback

Revert the hunks in render-furnished-dollhouse.py, delete the new test. The deleted json can be regenerated by any rebuild (that is the bug).

## Approval record

Rainer, 2026-10-20: "Yes, write the plan and fix the camera stamp so a rebuilt upper floor is not taken for a hand camera; then reset twostorey_059's camera. Test first."


## Verification record (2026-10-20)

- `kamera_stempel.test.py`: 6 OK (failed before the fix). Existing suites green: render-furnished-dollhouse 26, treppenloch_a1 10, treppenloch_gezeichnet 20, treppenloch_form 14, verify_render_blend 11.
- The test copy `render-persp-test.py` has no camera stamp, so it is unchanged.
- **Reset:** `corrections/twostorey_059/kamera-innen-1.json` deleted (backup in the session scratchpad).
- **Real rebuild:** `go.py twostorey_059` built at 12:12, "fertig". There was no "Handkamera ... gerettet" line, and no json was written.
  - Camera z 43.155, equal to its stamp; the ground floor is at z 40.456. The render is framed centrally again.
  - The second `go.py` run found the house up to date and did not rebuild, so stability was proven in scratch instead.
- **Scratch go-baseline**, copy of the 12:12 file:
  - Rebuilt: camera unchanged (43.155), no rescue.
  - Then the camera was moved by hand (+1 m x, -3 m z), saved, and the floor rebuilt twice. Both times it was "Kamera von Hand" at exactly 25.636 / -13.332 / 40.155: no drift.

Other houses with a saved UPPER-floor camera (`kamera-innen-1.json`), most likely the same false rescue, left untouched:
bungalow_040_185, twostorey_045, 046, 047, 048, 049, 050, 051, 052, 054, 055, 056, 058.
With the fix they do not drift further, but they keep the camera they have. Deleting a house's json returns it to the automatic framing on the next build.

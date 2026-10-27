#!/usr/bin/env python3
"""Migrate stored furniture from the room-extent flip basis to the frame's
own height_mm -- see plans/moebel-koordinaten-staleness-und-treppenbreite-v1.md.

Rainer, 2026-09-18, after a Codex architecture review of the coordinate-space
handling: "i think there are many flaws especially in the scaling between the
different tabs i think this has to be standardised and simplified", then
"well do it".

geometry_only() and workbench_furniture() used to flip display-space y
against `lo, hi` -- the CURRENT min/max y of this floor's own room polygons,
recomputed independently at read time and at write time. Two independent
recomputations of "the same" number is exactly the class of bug that
reflected twostorey_047's whole furniture set twice. Both now flip against
`frame.height_mm` instead: a constant derived only from the floor's scale and
image aspect ratio, identical every time, for every floor registered onto
the same ground floor.

Because both conventions are "reflect around a single constant", converting
existing stored y-values from the old convention to the new one is a PURE
PER-FLOOR SHIFT, not a re-derivation from room polygons at all:

    y_old_stored = lo + hi - y_frame                  (old convention)
    y_new_stored = height_mm - y_frame
                 = height_mm - (lo + hi - y_old_stored)
                 = y_old_stored + (height_mm - lo - hi)

So every item on one floor shifts by the SAME delta. x, rotation_deg and
mirrored are all untouched -- this is a translation, not a reflection.

Usage:
    python scripts/moebel-flip-basis-migrieren.py --dry-run   # report only
    python scripts/moebel-flip-basis-migrieren.py             # write files
    python scripts/moebel-flip-basis-migrieren.py twostorey_047  # one project
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import importlib.util
spec = importlib.util.spec_from_file_location("bp", HERE / "build-simplifier-render-plan.py")
bp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bp)


def workbench_data_root():
    configured = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR", "").strip()
    if not configured:
        raise SystemExit("FLOORPLAN_WORKBENCH_DATA_DIR is not set")
    return os.path.abspath(configured)


FLIP_BASIS_MARK = "frame-height-v1"


def migrate_one(project_id, floor_file, dry_run):
    level_raw = floor_file.stem  # "floor-0" / "floor-1"
    document = json.loads(floor_file.read_text(encoding="utf-8"))
    # This script computes its shift purely from the CURRENT annotation's
    # room geometry, not from anything in the furniture file itself -- so
    # nothing stops it from being run twice and shifting an already-migrated
    # file a second time. Confirmed the hard way: ran this once for
    # twostorey_047/_049 specifically, then again for the whole corpus
    # without excluding them, and double-shifted both (caught immediately by
    # the same point-in-polygon check used throughout this task, and
    # corrected by hand). A stamp makes a second run a no-op instead of a
    # silent corruption -- exactly the "refuse instead of re-apply blindly"
    # policy this whole task exists to establish elsewhere.
    if document.get("flip_basis") == FLIP_BASIS_MARK:
        return None, "skip (already migrated -- flip_basis stamp present)"
    space = document.get("coordinate_space")
    if space != bp.RENDER_GEOMETRY_SPACE:
        return None, f"skip (coordinate_space={space!r}, not the current render space)"
    symbols = document.get("symbols") or []
    if not symbols:
        return None, "skip (no symbols)"

    project_dir = os.path.join(bp.SIMPLIFIER, "projects", project_id)
    try:
        annotations = bp.load_annotations(project_dir)
    except Exception as error:
        return None, f"SKIP -- cannot load annotations: {error}"
    try:
        pixel_width, pixel_height = bp.image_size(project_dir, annotations)
    except SystemExit as error:
        return None, f"SKIP -- {error}"
    levels = sorted({i.get("floor_level") for i in annotations.get("annotations", [])
                     if i.get("floor_level")})
    ground_level = "groundfloor" if "groundfloor" in levels else (levels[0] if levels else None)
    if not ground_level:
        return None, "SKIP -- no floor_level found in annotations"
    aliases = [level_raw]
    order = {"groundfloor": "floor-0", "upperfloor": "floor-1",
             "floor-0": "groundfloor", "floor-1": "upperfloor"}
    if level_raw in order:
        aliases.append(order[level_raw])
    echt = next((lvl for lvl in aliases if lvl in levels), None)
    if echt is None:
        return None, f"SKIP -- {level_raw} not found in this project's annotation levels {levels}"

    frame = bp.frame_for_level(annotations, echt, ground_level, pixel_width, pixel_height)
    if frame is None:
        return None, f"SKIP -- no frame for {echt} (missing scale or alignment marks?)"
    extent = bp.level_room_extent(project_id, echt)
    if extent is None:
        return None, f"SKIP -- cannot derive the OLD room extent for {echt} (no rooms drawn?)"
    lo, hi = extent
    delta = round(frame.height_mm - lo - hi, 1)

    migrated = json.loads(json.dumps(document))  # deep copy
    touched = 0
    for symbol in migrated["symbols"]:
        pos = symbol.get("position_mm")
        if pos:
            symbol["position_mm"] = [pos[0], round(pos[1] + delta, 1)]
            touched += 1
        pts = symbol.get("points_mm")
        if pts:
            symbol["points_mm"] = [[q[0], round(q[1] + delta, 1)] for q in pts]
            touched += 1
    if not dry_run:
        migrated["flip_basis"] = FLIP_BASIS_MARK
        migrated["updated_at"] = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).isoformat()
        floor_file.write_text(json.dumps(migrated, indent=2), encoding="utf-8")
    return delta, f"{'would shift' if dry_run else 'shifted'} {touched} item(s) by dy={delta}mm"


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    only = [a for a in args if not a.startswith("--")]
    root = Path(workbench_data_root()) / "corrections"
    if not root.exists():
        raise SystemExit(f"no corrections directory at {root}")
    results = []
    for project_dir in sorted(root.iterdir()):
        if not project_dir.is_dir():
            continue
        project_id = project_dir.name
        if only and project_id not in only:
            continue
        furniture_dir = project_dir / "furniture"
        if not furniture_dir.is_dir():
            continue
        for floor_file in sorted(furniture_dir.glob("floor-*.json")):
            delta, message = migrate_one(project_id, floor_file, dry_run)
            results.append((project_id, floor_file.name, delta, message))
            print(f"[{'DRY' if dry_run else 'RUN'}] {project_id}/{floor_file.name}: {message}")
    migrated_count = sum(1 for _, _, delta, _ in results if delta is not None)
    print(f"\n{migrated_count} of {len(results)} furniture file(s) "
          f"{'would be' if dry_run else 'were'} migrated.")
    zero_delta = [r for r in results if r[2] is not None and abs(r[2]) < 0.05]
    if zero_delta:
        print(f"{len(zero_delta)} file(s) had delta ~0 (old and new basis already agreed) --"
              f" harmless, no visible change expected there.")


if __name__ == "__main__":
    main()

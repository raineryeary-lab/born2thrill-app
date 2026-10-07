#!/usr/bin/env python3
"""Move an upper storey's placed furniture into its REGISTERED coordinates.

Since 2026-08-23 an upper storey's geometry is registered onto the ground
floor via the annotator's floor-alignment marks (RegisteredFrame in
build-simplifier-render-plan.py): scale corrected per axis, outer faces
snapped onto the ground floor's exterior lines. Furniture that was placed
in the Moebel editor BEFORE that saw the old, unregistered room polygons --
left untouched it would sit 100-300mm off the rooms it was placed in.

This applies the identical mapping once to furniture/<floor>.json:

    old display mm  ->  old y-up mm (old extent)  ->  old normalized
    (inverse of the storey's own plain Frame)  ->  new registered y-up mm
    (RegisteredFrame)  ->  new display mm (new extent)

The file is marked `floor_registration: alignment-marks-v1` so this never
runs twice; the original is kept beside it as <floor>.json.vor-registrierung.

    python moebel-registrieren.py onehalfstorey_029
"""
import importlib.util
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MARK = "alignment-marks-v1"


def _load_builder():
    spec = importlib.util.spec_from_file_location(
        "bsrp", os.path.join(HERE, "build-simplifier-render-plan.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(project_id):
    m = _load_builder()
    project_dir = os.path.join(m.SIMPLIFIER, "projects", project_id)
    annotations = m.load_annotations(project_dir)
    pixel_width, pixel_height = m.image_size(project_dir, annotations)
    levels = sorted({i.get("floor_level") for i in annotations.get("annotations", [])
                     if i.get("floor_level")})
    ground = "groundfloor" if "groundfloor" in levels else levels[0]
    order = {"groundfloor": "floor-0", "upperfloor": "floor-1"}
    folder = os.path.join(m.workbench_data_root(), "corrections", project_id, "furniture")
    done = 0
    for level in levels:
        if level == ground:
            continue
        new_frame = m.frame_for_level(annotations, level, ground, pixel_width, pixel_height)
        if not isinstance(new_frame, m.RegisteredFrame):
            print(f"[moebel] {level}: nicht registriert (keine Marken) -- nichts zu tun")
            continue
        path = None
        for name in (order.get(level, level), level):
            candidate = os.path.join(folder, f"{name}.json")
            if os.path.exists(candidate):
                path = candidate
                break
        if path is None:
            print(f"[moebel] {level}: keine Moebeldatei")
            continue
        doc = json.load(open(path, encoding="utf-8"))
        if doc.get("floor_registration") == MARK:
            print(f"[moebel] {level}: schon registriert ({MARK})")
            continue
        raum = doc.get("coordinate_space")
        if raum != m.RENDER_GEOMETRY_SPACE:
            print(f"[moebel] {level}: coordinate_space ist {raum!r}, nicht "
                  f"{m.RENDER_GEOMETRY_SPACE!r} -- ueberspringe (die Umrechnung "
                  "unten geht von altem Display-mm aus; falsch angewandt "
                  "verschiebt sie jedes Moebelstueck)")
            continue
        old_frame = m.Frame(annotations["floor_scale"][level], pixel_width, pixel_height)

        def extent(frame):
            ys = []
            for item in annotations.get("annotations", []):
                if item.get("floor_level") != level or len(item.get("points") or []) < 3:
                    continue
                if m.excluded(item.get("label")):
                    continue
                ys.extend(frame.point(p)[1] for p in item["points"])
            return (min(ys), max(ys)) if ys else (0.0, 0.0)

        old_lo, old_hi = extent(old_frame)
        new_lo, new_hi = extent(new_frame)

        def convert(point):
            x_disp, y_disp = point
            y_up_old = old_lo + old_hi - y_disp
            normalized = {"x": x_disp / old_frame.width_mm,
                          "y": 1.0 - y_up_old / old_frame.height_mm}
            x_new, y_up_new = new_frame.point(normalized)
            return [round(x_new, 1), round(new_lo + new_hi - y_up_new, 1)]

        shutil.copy2(path, path + ".vor-registrierung")
        moved = 0
        for symbol in doc.get("symbols", []):
            if symbol.get("position_mm"):
                symbol["position_mm"] = convert(symbol["position_mm"])
                moved += 1
            if symbol.get("points_mm"):
                symbol["points_mm"] = [convert(p) for p in symbol["points_mm"]]
                moved += 1
        doc["floor_registration"] = MARK
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(doc, handle, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
        print(f"[moebel] {level}: {moved} Moebel in registrierte Koordinaten verschoben "
              f"(Sicherung: {os.path.basename(path)}.vor-registrierung)")
        done += 1
    return 0 if done or True else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: moebel-registrieren.py <project_id>")
    sys.exit(main(sys.argv[1]))

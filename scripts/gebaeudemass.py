#!/usr/bin/env python3
"""Give a drawn-but-unmeasured house its two numbers, so it can be built.

119 projects were drawn by hand and then had their source image deleted by the
import pipeline's privacy policy. Nothing about the drawing is lost: room points
are stored normalised, and the render pipeline never opens the image. What is
missing is only scale and aspect ratio, which used to be read off the image.

You supply the building's real WIDTH and DEPTH in metres. Everything else is
computed from the drawing itself:

  the rooms occupy some fraction of the annotation frame, so
      frame_width_m  = breite_m / (bbox width in normalised units)
      frame_height_m = tiefe_m  / (bbox height in normalised units)
      aspect         = frame_height_m / frame_width_m

  floor_scale is the frame width in metres, which is exactly what Frame()
  multiplies normalised x by.

Written to gebaeudemass.json BESIDE the annotation. annotations.json is never
touched -- your drawing stays exactly as you made it, and a measurement can be
corrected or deleted without rewriting it.

    python gebaeudemass.py --list
    python gebaeudemass.py bungalow_001 --breite 12.0 --tiefe 9.5
    python gebaeudemass.py bungalow_001 --show
    python gebaeudemass.py bungalow_001 --entfernen
"""

import argparse
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SUITE = os.path.dirname(os.path.dirname(HERE))
PROJECTS = os.path.join(SUITE, "floorplan-simplifier", "projects")
RASTER = (".png", ".jpg", ".jpeg", ".pdf")


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8-sig") as handle:
            return json.load(handle)
    except Exception:
        return default


def drawn_extent(annotations, level=None):
    """Bounding box of everything drawn, in normalised units.

    Both the rooms and the outer outline count: whichever the person drew, the
    building's real width spans that box.
    """
    xs, ys = [], []
    for element in (annotations.get("annotations") or []):
        # Beim Messen EINES Geschosses zaehlt nur dessen Zeichnung: das
        # Obergeschoss hat eine andere Ausdehnung als das Erdgeschoss, und die
        # Bounding-Box ueber beide gaebe einen falschen Massstab.
        if level and element.get("floor_level") != level:
            continue
        for point in (element.get("points") or []):
            xs.append(float(point["x"]))
            ys.append(float(point["y"]))
    for point in (annotations.get("outer_outline") or []):
        if isinstance(point, dict):
            xs.append(float(point["x"]))
            ys.append(float(point["y"]))
    if not xs or not ys:
        return None
    return (max(xs) - min(xs), max(ys) - min(ys))


def levels_of(annotations):
    found = sorted({e.get("floor_level") for e in (annotations.get("annotations") or [])
                    if e.get("floor_level")})
    return found or ["groundfloor"]


def candidates():
    out = []
    for name in sorted(os.listdir(PROJECTS)):
        folder = os.path.join(PROJECTS, name)
        annotations = read_json(os.path.join(folder, "annotations.json"))
        if not annotations or not (annotations.get("annotations") or []):
            continue
        if annotations.get("floor_scale"):
            continue
        has_image = any(x.lower().endswith(RASTER) for x in os.listdir(folder))
        done = os.path.exists(os.path.join(folder, "gebaeudemass.json"))
        out.append((name, has_image, done, len(annotations["annotations"])))
    return out


PT_MM = 25.4 / 72.0


def aus_katalog(folder, massstab=100.0):
    """Frame size in metres from the recorded page geometry, at a known scale.

    The 55 german_catalog_* projects still record what their source PDF page
    was: `page_size_points`, the `normalized_crop` that was cut from it, and the
    `preview_size_pixels` the annotation was drawn on. Given the drawing scale
    (1:100), that is enough to reconstruct the real size exactly -- no typing,
    no guessing.

    It is also self-checking. The aspect ratio computed from the page geometry
    must equal the aspect of the preview the person actually drew on; if the
    scale were wrong, or the crop misrecorded, they would not agree. Measured
    across all 55 projects: 70 of 70 pages agree to within 0.02, which is what
    confirms the 1:100 assumption rather than assuming it.
    """
    doc = read_json(os.path.join(folder, "german-catalog-source.json"))
    if not doc:
        return None
    out = {}
    for page in (doc.get("rendered_pages") or []):
        size = page.get("page_size_points")
        crop = page.get("normalized_crop")
        prev = page.get("preview_size_pixels")
        level = page.get("floor_level")
        if not (size and crop and prev and level):
            continue
        real_w_m = size[0] * PT_MM * massstab / 1000.0
        real_h_m = size[1] * PT_MM * massstab / 1000.0
        crop_w = real_w_m * (crop[2] - crop[0])
        crop_h = real_h_m * (crop[3] - crop[1])
        if crop_w <= 0 or crop_h <= 0:
            continue
        aspect_geom = crop_h / crop_w
        aspect_px = prev[1] / float(prev[0])
        if abs(aspect_geom - aspect_px) > 0.02:
            return {"_mismatch": (level, aspect_geom, aspect_px)}
        out[level] = {"frame_w_m": crop_w, "frame_h_m": crop_h, "aspect": aspect_geom}
    return out or None


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plan", nargs="?")
    parser.add_argument("--breite", type=float, help="echte Gebaeudebreite in Metern")
    parser.add_argument("--tiefe", type=float, help="echte Gebaeudetiefe in Metern")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--entfernen", action="store_true")
    parser.add_argument("--geschoss", help="nur dieses Geschoss setzen, z.B. upperfloor")
    parser.add_argument("--aus-katalog", dest="aus_katalog", action="store_true",
                        help="Mass aus der Seitengeometrie der Katalog-PDF rechnen")
    parser.add_argument("--massstab", type=float, default=100.0,
                        help="Zeichnungsmassstab, Standard 1:100")
    args = parser.parse_args()

    if args.aus_katalog:
        gesetzt = uneindeutig = 0
        for name in sorted(os.listdir(PROJECTS)):
            folder = os.path.join(PROJECTS, name)
            if not os.path.isdir(folder):
                continue
            annotations = read_json(os.path.join(folder, "annotations.json"))
            if not annotations or annotations.get("floor_scale"):
                continue
            masse = aus_katalog(folder, args.massstab)
            if not masse:
                continue
            if "_mismatch" in masse:
                level, a, b = masse["_mismatch"]
                print("   uneindeutig %-44s %s aspect %.3f vs %.3f"
                      % (name[:44], level, a, b))
                uneindeutig += 1
                continue
            ground = masse.get("groundfloor") or list(masse.values())[0]
            record = {
                "schema": "zf-gebaeudemass-v1",
                "plan_id": name,
                "herkunft": "aus Katalog-Seitengeometrie bei 1:%g" % args.massstab,
                "rahmen_m": {k: [round(v["frame_w_m"], 3), round(v["frame_h_m"], 3)]
                             for k, v in masse.items()},
                "annotation_space": {"aspect": round(ground["aspect"], 6)},
                "floor_scale": {k: round(v["frame_w_m"], 6) for k, v in masse.items()},
                "set_at": datetime.datetime.now().isoformat(timespec="seconds"),
                "set_by": os.environ.get("USERNAME") or "unbekannt",
                "note": ("Aus page_size_points und normalized_crop gerechnet und "
                         "gegen preview_size_pixels geprueft. annotations.json "
                         "wurde nicht veraendert."),
            }
            target = os.path.join(folder, "gebaeudemass.json")
            alt = {}
            try:
                with open(target, encoding="utf-8-sig") as handle:
                    alt = json.load(handle)
            except Exception:
                alt = {}
            # Fremde Schluessel (Dachform!) bleiben stehen; nur die eigenen
            # werden ersetzt.
            for key, value in alt.items():
                record.setdefault(key, value)
            temporary = target + ".tmp"
            with open(temporary, "w", encoding="utf-8") as handle:
                json.dump(record, handle, indent=1, ensure_ascii=False)
            os.replace(temporary, target)
            gesetzt += 1
            print("   %-46s %.2f m x %.2f m" % (name[:46], ground["frame_w_m"],
                                                ground["frame_h_m"]))
        print("")
        print("%d Projekte vermessen, %d uneindeutig" % (gesetzt, uneindeutig))
        return 0

    if args.list or not args.plan:
        rows = candidates()
        offen = [r for r in rows if not r[2]]
        fertig = [r for r in rows if r[2]]
        print("Ohne Massstab: %d   davon schon vermessen: %d   offen: %d"
              % (len(rows), len(fertig), len(offen)))
        print("")
        for name, has_image, done, rooms in offen[:40]:
            print("   %-36s %2d Raeume   %s"
                  % (name, rooms, "Bild vorhanden" if has_image else "ohne Bild"))
        if len(offen) > 40:
            print("   ... und %d weitere" % (len(offen) - 40))
        print("")
        print("  python gebaeudemass.py <plan> --breite 12.0 --tiefe 9.5")
        return 0

    folder = os.path.join(PROJECTS, args.plan)
    if not os.path.isdir(folder):
        sys.exit("Kein Projekt: " + args.plan)
    sidecar = os.path.join(folder, "gebaeudemass.json")

    if args.entfernen:
        if os.path.exists(sidecar):
            os.remove(sidecar)
            print("entfernt: " + sidecar)
        else:
            print("nichts zu entfernen")
        return 0

    if args.show:
        current = read_json(sidecar)
        print(json.dumps(current, indent=1, ensure_ascii=False) if current
              else "noch kein Gebaeudemass gesetzt")
        return 0

    if args.breite is None or args.tiefe is None:
        sys.exit("--breite und --tiefe (in Metern) werden beide gebraucht.")
    if args.breite <= 0 or args.tiefe <= 0:
        sys.exit("Breite und Tiefe muessen groesser als 0 sein.")

    annotations = read_json(os.path.join(folder, "annotations.json"))
    if not annotations:
        sys.exit("annotations.json nicht lesbar")
    extent = drawn_extent(annotations, args.geschoss)
    if not extent:
        sys.exit("In diesem Projekt ist nichts gezeichnet -- ohne Zeichnung "
                 "hilft ein Mass nicht.")
    span_x, span_y = extent
    if span_x <= 0 or span_y <= 0:
        sys.exit("Die Zeichnung hat keine Ausdehnung in x oder y.")

    frame_width_m = args.breite / span_x
    frame_height_m = args.tiefe / span_y
    aspect = frame_height_m / frame_width_m

    # Nur ein Geschoss setzen: der Rest der Datei bleibt, wie er ist. Gebraucht
    # fuer Haeuser, bei denen ein Geschoss im Annotator vermessen wurde und das
    # andere nicht -- twostorey_030 hatte groundfloor und kein upperfloor.
    if args.geschoss:
        vorhanden = read_json(sidecar) or {"schema": "zf-gebaeudemass-v1",
                                           "plan_id": args.plan}
        scale = dict(vorhanden.get("floor_scale") or {})
        scale[args.geschoss] = round(frame_width_m, 6)
        vorhanden["floor_scale"] = scale
        vorhanden.setdefault("annotation_space", {})["aspect"] = round(aspect, 6)
        vorhanden["set_at"] = datetime.datetime.now().isoformat(timespec="seconds")
        temporary = sidecar + ".tmp"
        with open(temporary, "w", encoding="utf-8") as handle:
            json.dump(vorhanden, handle, indent=1, ensure_ascii=False)
        os.replace(temporary, sidecar)
        print("[mass] %s / %s: %.2f x %.2f m -> floor_scale %.3f"
              % (args.plan, args.geschoss, args.breite, args.tiefe, frame_width_m))
        return 0

    record = {
        "schema": "zf-gebaeudemass-v1",
        "plan_id": args.plan,
        "gebaeude_breite_m": args.breite,
        "gebaeude_tiefe_m": args.tiefe,
        "gezeichnete_ausdehnung": {"x": round(span_x, 6), "y": round(span_y, 6)},
        "annotation_space": {"aspect": round(aspect, 6)},
        "floor_scale": {level: round(frame_width_m, 6) for level in levels_of(annotations)},
        "set_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "set_by": os.environ.get("USERNAME") or "unbekannt",
        "note": ("Von Hand eingetragen, weil die Vorlage geloescht wurde. "
                 "annotations.json wurde nicht veraendert."),
    }
    alt = {}
    try:
        with open(sidecar, encoding="utf-8-sig") as handle:
            alt = json.load(handle)
    except Exception:
        alt = {}
    for key, value in alt.items():
        record.setdefault(key, value)
    temporary = sidecar + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=1, ensure_ascii=False)
    os.replace(temporary, sidecar)

    print("[mass] %s: %.2f m breit, %.2f m tief" % (args.plan, args.breite, args.tiefe))
    print("       gezeichnet ueber %.3f x %.3f des Rahmens" % (span_x, span_y))
    print("       -> floor_scale %.3f m, aspect %.4f" % (frame_width_m, aspect))
    print("       -> %s" % sidecar)
    print("")
    print("  python batch-build.py %s" % args.plan)
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Build a furnished render plan directly from Simplifier annotations.
#
# WHY THIS EXISTS, AND WHAT IT IS NOT
#
# The approved pipeline is: Simplifier annotations -> canonical JSON -> render.
# Canonical JSON is the single geometry source for anything delivered, and
# scripts/build-furnished-render-plan.mjs is the builder that path uses.
#
# bungalow_040_66 has no canonical document — it is `training_ready`, not
# promoted — and promoting it is the whole generator process, not a step. So
# this script exists to get a PICTURE out of hand-annotated data for review.
# It is a proof path, exactly like scripts/render-furnished-dollhouse.py which
# it feeds:
#
#   * it never writes canonical geometry
#   * it never computes or touches geometry_hash
#   * nothing it produces may be delivered, published or emailed
#
# The output carries `source: "simplifier_annotations_proof"` so an image built
# this way can always be told apart from one built from approved geometry.
#
# WHAT IT DOES
#
# Reads projects/<id>/annotations.json and turns it into the same
# dmh-furnished-render-plan-proof-v1 schema the Blender script already
# consumes:
#
#   rooms      <- annotation polygons, German labels mapped to material kinds
#   walls      <- room polygon edges; an edge shared by two rooms is interior,
#                 an edge belonging to one room is exterior
#   openings   <- door/window/opening elements, matched to their nearest wall
#   placements <- Rainer's hand-placed Ausstattung symbols, which is the whole
#                 point: furniture that was annotated rather than guessed
#
# Usage:
#   python scripts/build-simplifier-render-plan.py <project_id> <style> <out.json>

import hashlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
# Eine Wahrheit fuer Dachform und Massstab -- dieselbe Zusammenfuehrung, die
# go.py, werkbank.py, dachform.py und die Statusroute benutzen.
from hausdaten import hausdaten as _hausdaten  # noqa: E402
SIMPLIFIER = os.path.join(os.path.dirname(REPO), "floorplan-simplifier")
SHORTLIST = os.path.join(REPO, "tmp", "symbol-model-shortlist.json")
PICKS = os.path.join(REPO, "data", "symbol-model-picks.json")
# A placed symbol records type, position and rotation and nothing else — that
# separation is deliberate, so a symbol never carries a size that could drift
# from the catalogue. The footprint therefore has to be looked up.
FOOTPRINTS = os.path.join(SIMPLIFIER, "symbol_footprints.json")

# German room label -> the material kind the renderer understands. Longest and
# most specific first: "Elternbad" must reach `sanitary` on "bad", not
# `sleeping` on "eltern", which is the same precedence bug that once classed a
# bathroom as a bedroom in the Simplifier.
ROOM_KINDS = [
    ("duschbad", "sanitary"), ("kinderbad", "sanitary"), ("elternbad", "sanitary"),
    ("gästebad", "sanitary"), ("gaestebad", "sanitary"), ("tageslichtbad", "sanitary"),
    ("badezimmer", "sanitary"), ("du-wc", "sanitary"), ("dusch", "sanitary"),
    ("bad", "sanitary"), ("gäste-wc", "sanitary"), ("gaeste-wc", "sanitary"),
    ("wc", "sanitary"),
    ("hwr", "service"), ("htr", "service"), ("hauswirtschaft", "service"),
    ("technik", "service"), ("waschküche", "service"),
    ("diele", "circulation"), ("flur", "circulation"), ("windfang", "circulation"),
    ("treppe", "circulation"),
    ("ankleide", "storage"), ("abstell", "storage"), ("speis", "storage"),
    ("keller", "storage"), ("garderobe", "storage"),
    ("küche", "living"), ("kueche", "living"), ("essen", "living"),
    ("wohnen", "living"), ("wohnzimmer", "living"),
    ("schlafen", "sleeping"), ("eltern", "sleeping"), ("kind", "sleeping"),
    ("gast", "sleeping"), ("büro", "sleeping"), ("arbeiten", "sleeping"),
]

# Spaces that are not interior rooms. A carport has no floor finish and no
# furniture, and including it stretches the camera framing over dead ground.
EXCLUDED_ROOMS = ("carport", "garage", "terrasse", "balkon", "loggia")

# Symbole, die als aufgezogenes Rechteck gebaut werden statt als Lauf. EINE
# Menge statt zweier Schluesselvergleiche: die beiden Bau-Zweige hatten
# frueher jeder ihre eigene Bedingung, und die eine davon schickte den
# Normalfall in den falschen Zweig -- Rechteck im Editor, schraeger Balken in
# der .blend (plans/kuecheninsel-rechteck-v1.md). Ein neues Rechteck-Symbol
# gehoert hier hinein, sonst wiederholt sich genau das.
#
# Genau das ist am 2026-09-15 nochmal passiert, diesmal an den
# Kleiderschraenken/Abstellschraenken: keins der beiden Bau-Woerter ("kind"
# im Renderer) passt auf ein zweipunktig aufgezogenes Moebel, das keinen
# mehrsegmentigen Pfad ist -- der Fallback ist "path", und ein handgezeichnetes
# Rechteck ist so gut wie nie exakt achsparallel. `abstellschrank-14-0` kam mit
# 169,7 statt 0 Grad heraus, `abstellschrank-15-0` mit -17,8 statt 0 -- beide
# Werte sind exakt der Winkel zwischen den zwei gezeichneten Eckpunkten, nicht
# das eingetragene `rotation_deg`. Rainer: "who in the fuck rotated the
# Kleider and Abstell schränke ... i cant even rotate stuff like that just 45
# and 90 degrees" -- zu Recht, im Annotator geht das auch nicht, das Problem
# lag ausschliesslich hier.
RECT_BUILD = ("kuecheninsel", "stuff", "kleiderschrank", "schrank_40",
              "schrank_60", "abstellschrank", "garderobe")

# Height in mm for each symbol, the dimension a 2D footprint cannot carry, plus
# the finish category the renderer uses when a model has no materials of its
# own. Mount height is the CENTRE of a wall-hung item.
SYMBOL_3D = {
    "badewanne":         {"height": None,  "type": "bathtub"},
    "eckbadewanne":      {"height": 580,  "type": "bathtub"},
    "dusche":            {"height": 2000, "type": "shower", "build": "shower"},
    "dusche_gross":      {"height": 2000, "type": "shower", "build": "shower"},
    "dusche_klein":      {"height": 2000, "type": "shower", "build": "shower"},
    # KEINE Hoehe. 400 war die Sitzhoehe eines GRUNDRISS-Symbols, und
    # `fit_to_symbol` skaliert jede Achse einzeln -- das Modell wurde damit
    # auf die Haelfte gequetscht (813 -> 400, gemessen im gebauten .blend von
    # 3_3_2 am 2026-08-30). Der Kommentar direkt darunter rechnet ohnehin mit
    # der VOLLEN Modellhoehe: 660 - 820/2 = 250. Beides ging nicht zusammen.
    # Ohne Hoehe nimmt z den Mittelwert der x/y-Faktoren, das Modell behaelt
    # seine Proportion, und die Mount-Rechnung stimmt wieder.
    "wand_wc":           {"height": None, "type": "toilet", "mount": 660},
    # mount is the item CENTRE. The resolved Toilet Bowl model is 820mm
    # tall (probed z-range, includes the flush plate), so centre 660 puts
    # its underside at 250mm -- wall-hung with visible air. 200 sat it on
    # the floor (Rainer 2026-08-11); 480 still only left 70mm.
    "waschtisch":        {"height": 200,  "type": "sink",   "mount": 850},
    "doppelwaschtisch":  {"height": 200,  "type": "sink",   "mount": 850},
    "handwaschbecken":   {"height": 200,  "type": "sink",   "mount": 850},
    "badheizkoerper":    {"height": 1200, "type": "radiator", "mount": 900, "build": "radiator"},
    "vorwandinstallation": {"height": 1500, "type": "wall_panel", "depth": 150},
    "kuechenzeile":      {"height": 900,  "type": "counter", "depth": 600},
    "kuecheninsel":      {"height": 900,  "type": "counter", "depth": 900},
    # Allzweck-Kasten, in jedem Raum waehlbar (Rainer, 2026-08-25: "i need a
    # new symbol type for furnishing, this one is called stuff"). Aufgezogen
    # wie die Insel, aber ohne Arbeitsplatte: `storage_shelving` hat ein
    # Holz-Finish in TYPE_FINISH und steht nicht in FLUSH_TYPES, bleibt also
    # stehen, wo es hingesetzt wurde.
    "stuff":             {"height": 800,  "type": "storage_shelving", "depth": 600},
    "kuehlschrank":      {"height": 1800, "type": "fridge"},
    "hochschrank_herd":  {"height": 2100, "type": "oven_housing"},
    "kochfeld":          {"height": 50,   "type": "hob",  "mount": 900, "build": "hob"},
    "spuele":            {"height": 200,  "type": "sink", "mount": 880, "build": "hob"},
    "waschmaschine":     {"height": 850,  "type": "washer"},
    "trockner":          {"height": 850,  "type": "washer"},
    "ecksofa":           {"height": 800,  "type": "sofa"},
    "sofa_3sitzer":      {"height": 800,  "type": "sofa"},
    "sofa_2sitzer":      {"height": 800,  "type": "sofa"},
    "sofa_1sitzer":      {"height": 800,  "type": "armchair"},
    "hocker":            {"height": 450,  "type": "stool"},
    "couchtisch":        {"height": 400,  "type": "coffee_table"},
    "lowboard":          {"height": 500,  "type": "sideboard"},
    "sideboard":         {"height": 800,  "type": "sideboard"},
    "fernseher":         {"height": 700,  "type": "tv", "mount": 1100, "build": "tv"},
    "essgruppe_6":       {"height": 750,  "type": "dining_set"},
    # Tisch und Stuhl einzeln setzbar (Rainer, 2026-08-25). Dieselben Modelle,
    # die die Essgruppe schon benutzt: ihr modern-Pick IST der nackte Tisch,
    # die sechs Stuehle leitet der Bau daraus ab -- und essgruppe_stuhl ist
    # genau dieser Stuhl, bisher nur intern.
    "esstisch":          {"height": 750,  "type": "dining_table"},
    "esszimmerstuhl":    {"height": 844,  "type": "dining_chair"},
    "playstation_gruppe": {"height": 750, "type": "dining_set"},
    # Ohne Hoehe: `fit_to_symbol` gibt z dann den Mittelwert der x/y-Faktoren,
    # das Modell behaelt seine Proportion und passt trotzdem in den
    # gezeichneten Grundriss. 500 war die MATRATZENOBERKANTE eines
    # Grundriss-Symbols, nicht die Gesamthoehe eines Betts -- im gebauten
    # .blend von 3_3_2 stand ein Doppelbett von 2,00 x 1,80 x 0,50 m,
    # Matratze und Kopfteil zusammen (Rainer, 2026-08-30: "sieh dir doch die
    # blender datei an").
    "doppelbett":        {"height": None, "type": "bed"},
    "einzelbett":        {"height": None, "type": "bed"},
    "kleiderschrank":    {"height": 2100, "type": "wardrobe"},
    "schrank_60":        {"height": 2100, "type": "wardrobe"},
    "schrank_40":        {"height": 2100, "type": "wardrobe"},
    "abstellschrank":    {"height": 2100, "type": "wardrobe"},
    "schreibtisch":      {"height": 750,  "type": "desk"},
    "schreibtisch_kind": {"height": 720,  "type": "desk"},
    "garderobe":         {"height": 1900, "type": "wardrobe"},
    "schreibtischstuhl": {"height": 1200, "type": "office_chair"},
    "essgruppe_stuhl":   {"height": 844,  "type": "dining_chair"},
    "pflanze":           {"height": 1300, "type": "plant", "build": "plant"},
}

DEFAULT_WALL_THICKNESS_MM = 240
INTERIOR_WALL_THICKNESS_MM = 115


def room_kind(label):
    lowered = (label or "").lower()
    for needle, kind in ROOM_KINDS:
        if needle in lowered:
            return kind
    return "living"


def excluded(label):
    lowered = (label or "").lower()
    return any(needle in lowered for needle in EXCLUDED_ROOMS)


def load_json(path):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def load_annotations(project_dir):
    """annotations.json, plus the hand-entered Gebaeudemass beside it.

    119 projects were annotated and then had their source image deleted by the
    import pipeline's own privacy policy. Their drawings are intact -- the room
    points are normalised, so they never needed the image -- but without the
    image there is no aspect ratio and no scale, and image_size() had nothing to
    fall back on.

    The two missing numbers live in `gebaeudemass.json` NEXT TO the annotation,
    never inside it. The annotation is the user's own drawing and stays
    untouched; a measurement typed in afterwards is a separate fact about the
    same house, and keeping it separate means it can be corrected or removed
    without ever rewriting what was drawn.

    Zusammengefuehrt wird nicht mehr hier, sondern in hausdaten.py -- derselbe
    Helfer, den go.py, werkbank.py, dachform.py und die Statusroute lesen.
    Die Regel ist unveraendert die von hier: pro Feld gewinnt die Annotation,
    ist sie dort leer, zaehlt das Sidecar. Beim Massstab pro GESCHOSS, nicht
    alles oder nichts -- twostorey_030 hatte ein gemessenes Erdgeschoss und
    kein Obergeschoss, und die alte Pruefung (`if not annotations.get(
    "floor_scale")`) sah deshalb gar nicht erst ins Sidecar.
    """
    daten = _hausdaten(project_dir, streng=True)
    annotations = daten["annotationen"]
    if daten["floor_scale"]:
        annotations["floor_scale"] = dict(daten["floor_scale"])

    # Ein Obergeschoss ohne eigenen Massstab erbt den des Erdgeschosses.
    #
    # twostorey_030 hatte groundfloor gemessen, upperfloor nicht, und der Bau
    # brach mit "upperfloor has no calibrated scale" ab -- bei einem Haus, das
    # sonst fertig gewesen waere. Beide Geschosse desselben Hauses sind auf
    # derselben Vorlage im selben Massstab gezeichnet; das Erdgeschoss zu
    # messen und das Obergeschoss noch einmal zu verlangen ist eine Frage nach
    # einer Zahl, die man schon hat.
    #
    # Geerbt, nicht geraten: der Ursprung steht im Plan (floor_scale_source),
    # und wenn das Obergeschoss deutlich ueber den Grundriss des Erdgeschosses
    # hinausragt, sagt der Compiler das laut -- dann war die Vorlage doch eine
    # andere.
    scale = dict(annotations.get("floor_scale") or {})
    levels = sorted({a.get("floor_level") for a in (annotations.get("annotations") or [])
                     if a.get("floor_level")})
    basis = next((lvl for lvl in ("groundfloor", "basement") if scale.get(lvl)), None)
    if basis is None:
        basis = next((lvl for lvl in levels if scale.get(lvl)), None)
    if basis:
        geerbt = []
        for level in levels:
            if not scale.get(level):
                scale[level] = scale[basis]
                geerbt.append(level)
        if geerbt:
            annotations["floor_scale"] = scale
            annotations["floor_scale_source"] = {
                lvl: ("gemessen" if lvl not in geerbt else "geerbt von " + basis)
                for lvl in levels}
            print("[plan] Massstab fuer %s vom %s uebernommen (%.4f m/Einheit)"
                  % (", ".join(geerbt), basis, scale[basis]))
    if daten["annotation_space"]:
        annotations["annotation_space"] = daten["annotation_space"]
    # Dachform je Stil. bpypolyskel baut das Dach laengst korrekt -- es hatte
    # nur fuer 59 von 61 Haeusern nichts zu bauen, weil roof_type_* leer war.
    for key, feld in (("roof_type_modern", "dachform_modern"),
                      ("roof_type_classic", "dachform_classic")):
        if daten[feld]:
            annotations[key] = daten[feld]
            # Festhalten, WOHER -- sonst sieht der Wert spaeter aus wie
            # gezeichnet. Siehe dach_herkunft().
            annotations[key + "_herkunft"] = "beiblatt"
    return annotations


def dach_herkunft(annotations, style):
    """Woher die Dachform kommt: `annotation`, `beiblatt` oder `nicht_annotiert`.

    Rainer, 2026-08-29, ueber Etiketten, die mehr behaupten als der Wert
    hergibt. `roof_type_source` sagte "annotation" auch dann, wenn die
    Dachform aus `gebaeudemass.json` kam -- denn das Beiblatt wird vor dem
    Bauen in den Annotations-Dict gemischt, und danach sieht alles gleich aus.
    Gemessen: 231 von 233 Haeusern haben ihre Dachform NUR im Beiblatt. Das
    Etikett war also fast immer falsch.
    """
    if not annotations.get("roof_type_%s" % style):
        return "nicht_annotiert"
    return annotations.get("roof_type_%s_herkunft" % style) or "annotation"


def massstab_geschaetzt(annotations):
    """Steht hinter dem Massstab eine Messung oder eine Schaetzung?

    Am 2026-08-29 bekamen 121 Haeuser einen aus der Tuerbreite geschaetzten
    Massstab (Median-Fehler 6,7 %). Ein Zertifikat, das darauf steht und wie
    ein Mass aussieht, ist weniger wert, als es aussieht.
    """
    return bool(annotations.get("floor_scale_geschaetzt"))


def image_size(project_dir, annotations=None):
    """Pixel size of the preview the annotations were drawn on.

    Normalized y is measured against image HEIGHT, so without the aspect ratio
    every plan comes out squashed along one axis — the same unit mix-up that
    made symbols render 81.5 % too shallow in the annotation UI.

    Projects whose source image was deleted after annotation have no preview
    to read at all (onehalfstorey_*), and used to fail here with "could not
    read preview image size". For those the ratio is stated by hand in the
    Simplifier as the outer outline's real width x depth and stored as
    `annotation_space.aspect` (image height / image width) — an aspect is all
    this function's callers ever use the pixel numbers for.
    """
    space = (annotations or {}).get("annotation_space") or {}
    aspect = space.get("aspect")
    if isinstance(aspect, (int, float)) and 0.01 <= float(aspect) <= 100:
        return 1000.0, 1000.0 * float(aspect)
    # RegisteredFrame routes every storey's geometry through the ground
    # floor's Frame (frame_for_level() builds an upper storey's own Frame
    # too, but RegisteredFrame.point() never uses it -- only the ground
    # frame), so the GROUND FLOOR's own preview is the one file whose aspect
    # ratio the whole building's geometry actually depends on. A bare,
    # unprefixed "room_concept.png" -- a generic leftover many multi-floor
    # projects still have on disk -- used to be checked FIRST below and
    # silently won here for every one of them. Confirmed on twostorey_046:
    # real aspect 0.780 vs the generic file's 1.151, a 47.5% height error,
    # which also silently broke wall-pairing for one HWR/HTR wall (Rainer,
    # 2026-09-15: "the right wall in the htr is missing and the aspect
    # ratio is totally off" -- both from this one bug, confirmed by
    # rebuilding the walls with each frame directly).
    levels = sorted({item.get("floor_level")
                     for item in (annotations or {}).get("annotations", [])
                     if item.get("floor_level")})
    ground_level = "groundfloor" if "groundfloor" in levels else (levels[0] if levels else None)
    # Only the REAL photo jumps the queue -- a per-floor "_room_concept.png"
    # is a generated render, no more trustworthy than the bare
    # "room_concept.png" it would otherwise outrank. bungalow_039 has a
    # "groundfloor_room_concept.png" but no "groundfloor_original_preview.png"
    # at all; putting the concept name there made it win over the correct
    # bare "original_preview.png" and broke an existing door-normalization
    # test on first attempt -- caught by running the full suite, not assumed.
    names = [f"{ground_level}_original_preview.png"] if ground_level else []
    names += ["original_preview.png", "room_concept.png"]
    # One concept PNG per floor is the current layout; the unprefixed name
    # above only exists on single-floor projects.
    names += sorted(
        name for name in os.listdir(project_dir)
        if name.endswith("_room_concept.png") and name not in names
    )
    for name in names:
        candidate = os.path.join(project_dir, name)
        if not os.path.exists(candidate):
            continue
        with open(candidate, "rb") as handle:
            head = handle.read(33)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            width = int.from_bytes(head[16:20], "big")
            height = int.from_bytes(head[20:24], "big")
            if width and height:
                return width, height
    raise SystemExit(
        "could not read preview image size — no preview PNG and no "
        "annotation_space.aspect (set the Gebäudemaße in the Simplifier)"
    )


def workbench_data_root():
    """Where the workbench actually writes.

    Taken from the same environment variable the Next.js API uses
    (`dataRoot()` in src/app/api/floorplan-workbench/corrections/route.ts).
    A hardcoded sibling-folder guess pointed at
    Floorplan-tools/born2thrill-local-workbench-data while the running server
    wrote to C:/dev/born2thrill-local-workbench-data — a silently different
    tree, so furniture would have looked "not saved" forever.
    """
    configured = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR", "").strip()
    if not configured:
        raise SystemExit(
            "FLOORPLAN_WORKBENCH_DATA_DIR is not set — refusing to guess which "
            "workbench data tree holds the furniture")
    return os.path.abspath(configured)


FURNITURE_COORDINATE_SPACE = "correction-document-mm-svg-y-down-v1"
# The space furniture was stored in before it moved onto the correction plan.
# Refused, not reinterpreted — the two differ by a non-uniform factor per axis.
LEGACY_FURNITURE_SPACE = "simplifier-render-plan-mm-v1"
# Moebel, die auf der BAU-Geometrie dieses Skripts gesetzt wurden
# (--geometry-only im Editor), gespeichert so wie angezeigt: y nach UNTEN,
# innerhalb der Raumausdehnung des Geschosses. Frame selbst rechnet y nach
# OBEN -- beim Lesen wird deshalb einmal gespiegelt, mit exakt derselben
# Ausdehnung, mit der geometry_only die Anzeige gespiegelt hat.
#
# Warum das noetig wurde (2026-08-21, bungalow_036): der Editor zeigte den
# Korrektur-Kandidaten, gebaut wurde die Frame-Geometrie, beide nannten ihren
# Raum "correction-document-mm-svg-y-down-v1" -- und saemtliche Moebel aus dem
# Moebel-Schritt standen im Bau SPIEGELVERKEHRT: Rainers Waschmaschine (im
# HWR gesetzt, y=8300) landete im Schlafzimmer (Frame-y 8300), das Bett stand
# auf Granit. Sichtbar im Render, nie gemeldet, weil "in irgendeinem Raum".
RENDER_GEOMETRY_SPACE = "render-geometry-mm-y-down-v1"


def level_room_extent(project_id, level):
    """(lo, hi) der Raum-y dieses Geschosses, exakt wie geometry_only sie
    sieht: gleiche Annotation, gleicher Frame, gleiche Ausschluesse."""
    project_dir = os.path.join(SIMPLIFIER, "projects", project_id)
    annotations = load_annotations(project_dir)
    pixel_width, pixel_height = image_size(project_dir, annotations)
    levels = sorted({i.get("floor_level") for i in annotations.get("annotations", [])
                     if i.get("floor_level")})
    ground_level = "groundfloor" if "groundfloor" in levels else (levels[0] if levels else None)
    frame = frame_for_level(annotations, level, ground_level, pixel_width, pixel_height)
    if frame is None:
        return None
    ys = []
    for item in annotations.get("annotations", []):
        if item.get("floor_level") != level or len(item.get("points") or []) < 3:
            continue
        if excluded(item.get("label")):
            continue
        ys.extend(frame.point(pt)[1] for pt in item["points"])
    return (min(ys), max(ys)) if ys else None


def level_geometry_identity(project_id, level):
    """Identitaet DER RAEUME eines Geschosses -- die Flaeche, auf der Moebel
    stehen.

    Erster Wurf nahm die Identitaet der ganzen Annotation
    (batch-build.annotation_state). Das war unverhaeltnismaessig: ein neues
    Fenster im Erdgeschoss oder ein umbenannter Raum entwertete jeden
    Moebelstand im Haus, und der Bau blieb stehen (sofort passiert,
    onehalfstorey_029, 2026-08-23). Moebel interessieren nur die
    Raumpolygone ihres eigenen Geschosses in gebauten Millimetern -- also
    genau die, und nichts sonst. Aendert sich der Zuschnitt, stehen die
    Moebel wirklich falsch; aendert sich ein Fenster, nicht.
    """
    project_dir = os.path.join(SIMPLIFIER, "projects", project_id)
    annotations = load_annotations(project_dir)
    pixel_width, pixel_height = image_size(project_dir, annotations)
    levels = sorted({item.get("floor_level") for item in annotations.get("annotations", [])
                     if item.get("floor_level")})
    ground = "groundfloor" if "groundfloor" in levels else (levels[0] if levels else None)
    if not ground:
        return None
    aliases = [level] + ([{"groundfloor": "floor-0", "upperfloor": "floor-1",
                           "floor-0": "groundfloor", "floor-1": "upperfloor"}.get(level)]
                         if level in ("groundfloor", "upperfloor", "floor-0", "floor-1") else [])
    echt = next((lvl for lvl in aliases if lvl in levels), None)
    if echt is None:
        return None
    frame = frame_for_level(annotations, echt, ground, pixel_width, pixel_height)
    if frame is None:
        return None
    teile = []
    for item in sorted(annotations.get("annotations", []), key=lambda i: str(i.get("id"))):
        if item.get("floor_level") != echt or len(item.get("points") or []) < 3:
            continue
        if excluded(item.get("label")):
            continue
        punkte = [frame.point(p) for p in item["points"]]
        teile.append("%s:%s" % (item.get("id"), ";".join(
            "%.0f,%.0f" % (q[0], q[1]) for q in punkte)))
    if not teile:
        return None
    return hashlib.sha256("|".join(teile).encode("utf-8")).hexdigest()


def workbench_furniture(project_id, level):
    """Furniture placed in the workbench, already in this plan's millimetres.

    No transform. An earlier version fitted the editor's floor bounding box
    onto this one, which cannot be right: the workbench edits snapped, cleaned
    geometry whose x and y spans differ from the annotation-derived plan by
    different factors (1.123 vs 1.249 measured on onehalfstorey_020), so no
    single fit aligns anything but the four extremes. The editor is fed this
    script's own geometry instead (see --geometry-only) and stores what it is
    given.

    Returns None when there is no file, so every project annotated before the
    move keeps rendering from `annotations.symbols`. Returns [] when the file
    exists with no symbols: deliberately clearing a floor is not the same as
    never having furnished it.
    """
    # The two paths name floors differently: the correction document uses
    # "floor-0"/"floor-1", the annotation path uses "groundfloor"/"upperfloor".
    # The furniture editor writes the correction ids, so a house built from its
    # annotation looked for "groundfloor.json", found nothing and reported
    # "0 furniture" -- with ten symbols sitting in floor-0.json (Rainer,
    # 2026-08-19). Same file, two names for the same storey: try both.
    aliases = [level]
    order = {"groundfloor": "floor-0", "upperfloor": "floor-1",
             "floor-0": "groundfloor", "floor-1": "upperfloor"}
    if level in order:
        aliases.append(order[level])
    folder = os.path.join(workbench_data_root(), "corrections", project_id, "furniture")
    path = None
    for name in aliases:
        candidate = os.path.join(folder, f"{name}.json")
        if os.path.exists(candidate):
            path = candidate
            break
    if path is None:
        return None
    document = load_json(path)
    symbols = document.get("symbols") or []
    if not symbols:
        return []
    # Registriertes Obergeschoss + Moebel aus der Zeit VOR der Registrierung
    # = Moebel stehen 100-300mm neben ihren Raeumen und R6 reisst mit einer
    # Meldung, die nichts erklaert (twostorey_030, 2026-08-23: "Bau
    # fehlgeschlagen", Ursache 15 unmigrierte Moebel). Deshalb hier klar:
    try:
        project_dir = os.path.join(SIMPLIFIER, "projects", project_id)
        _ann = load_annotations(project_dir)
        _pw, _ph = image_size(project_dir, _ann)
        _levels = sorted({i.get("floor_level") for i in _ann.get("annotations", [])
                          if i.get("floor_level")})
        _ground = "groundfloor" if "groundfloor" in _levels else (_levels[0] if _levels else None)
        # `floor_scale`/`frame_for_level` only know the annotation-native
        # names ("groundfloor"/"upperfloor"), never the correction-document
        # aliases ("floor-0"/"floor-1") this function itself accepts -- the
        # SAME alias resolution `level_geometry_identity()` already does
        # below, needed here too now that `_frame.height_mm` (not just an
        # isinstance check) depends on this actually resolving.
        _echt = next((lvl for lvl in aliases if lvl in _levels), None)
        _frame = frame_for_level(_ann, _echt, _ground, _pw, _ph) if _ground and _echt else None
    except SystemExit:
        raise
    except Exception:
        _frame = None
    # Moebel gehoeren zu DER Zeichnung, auf der sie gesetzt wurden. Ohne
    # diese Bindung blieb ein Grundriss nach dem Umzeichnen der Raeume
    # einfach liegen und wurde still gegen die neue Geometrie gebaut --
    # Moebel in Waenden, ohne ein Wort (Codex-Audit P0/P1, "geometrieFremd"
    # wurde berechnet und nie gezeigt). Dokumente OHNE Stempel sind Altbestand
    # und bauen weiter; ein FREMDER Stempel haelt den Bau an.
    stamped = document.get("geometry_identity")
    if stamped:
        try:
            _heute = level_geometry_identity(project_id, level)
        except SystemExit:
            raise
        except Exception:
            _heute = None
        if _heute and stamped != _heute:
            raise SystemExit(
                f"{path}: die RAEUME dieses Geschosses wurden umgezeichnet, seit "
                f"diese Moebel gesetzt wurden (Stempel {stamped[:12]}, heute "
                f"{_heute[:12]}). Im Moebel-Schritt pruefen, ob sie noch dort "
                f"stehen, wo sie hingehoeren, und einmal speichern -- dann baut "
                f"es weiter.")
    if isinstance(_frame, RegisteredFrame) and document.get("floor_registration") != "alignment-marks-v1":
        raise SystemExit(
            f"{path}: die Moebel dieses Obergeschosses stammen aus der Zeit vor der "
            f"Geschoss-Registrierung und wuerden neben ihren Raeumen stehen. Einmal "
            f"ausfuehren: python scripts/moebel-registrieren.py {project_id}")
    space = document.get("coordinate_space")
    if space == RENDER_GEOMETRY_SPACE:
        # Anzeige-Raum (y unten) -> Frame (y oben), einmal, deterministisch.
        #
        # Codex architecture review, 2026-09-18: dieser Flip lief bis eben
        # gegen `level_room_extent()` -- eine ZWEITE, unabhaengige Neuberechnung
        # derselben Raum-Ausdehnung, die geometry_only() (der Schreiber) schon
        # einmal berechnet hatte. Zwei getrennte Neuberechnungen "derselben"
        # Zahl an zwei verschiedenen Stellen zu zwei verschiedenen Zeiten sind
        # KEINE Garantie, dass sie uebereinstimmen -- genau diese Klasse Fehler
        # hat twostorey_047s komplette Moebel-Aufstellung zweimal gespiegelt
        # (siehe plans/moebel-koordinaten-staleness-und-treppenbreite-v1.md).
        # `_frame.height_mm` ist stattdessen eine reine Funktion von Massstab
        # und Bildseitenverhaeltnis -- fix, sobald diese gesetzt sind, und
        # identisch mit dem, was geometry_only() fuer denselben Frame jetzt
        # ebenfalls als Flip-Basis nimmt (siehe dort). Keine zwei Stellen
        # berechnen mehr "dieselbe" Zahl getrennt -- es gibt nur noch die eine.
        if _frame is None:
            raise SystemExit(
                f"{path}: cannot derive the frame of {level} to place "
                f"this furniture -- is the floor scale missing?")
        flip = _frame.height_mm
        flipped = []
        for symbol in symbols:
            item = dict(symbol)
            pos = item.get("position_mm")
            if pos:
                item["position_mm"] = [pos[0], round(flip - pos[1], 1)]
            if item.get("points_mm"):
                item["points_mm"] = [[q[0], round(flip - q[1], 1)]
                                     for q in item["points_mm"]]
            if item.get("rotation_deg") is not None:
                # Spiegelung an der x-Achse kehrt den Drehsinn um.
                item["rotation_deg"] = (-item["rotation_deg"]) % 360
            # ABSICHTLICH NICHT das mirrored-Flag mit umkehren.
            #
            # Ein erster Versuch tat das ("eine Spiegelung kehrt auch die
            # Haendigkeit um"), analog zu corrected_placements() weiter oben.
            # Codex-Review, 2026-08-21, fand aber einen Achsen-Widerspruch:
            # der Moebel-Editor spiegelt lokal an der X-Achse NACH der
            # Rotation (ausstattung.js:363, ctx.rotate dann ctx.scale(-1,1)),
            # waehrend render-furnished-dollhouse.py die Meshdaten an der
            # LOKALEN Y-Achse VOR der Objektrotation spiegelt
            # (Diagonal((1,-1,1,1)) auf instance.data, Zeile ~3413). Ein
            # simples "rotation negieren + Flag umkehren" ignoriert diesen
            # Versatz; die korrekte Umrechnung braucht vermutlich einen
            # zusaetzlichen 180-Grad-Term, aber NUR fuer eine der beiden
            # Flag-Richtungen -- und zwei Agenten-Versuche, das per Augenmass
            # am Render zu beurteilen, sind hier schon in entgegengesetzte
            # Richtungen fehlgeschlagen (Kommentar oben, 2026-08-10).
            #
            # Deshalb NICHT geraten: das Flag bleibt unveraendert, bis ein
            # Kontaktblatt (4 Kombinationen: 0/90 Grad x gespiegelt/nicht,
            # an einem asymmetrischen Testkoerper durch die ECHTE Pipeline)
            # Rainer vorliegt und er die Achsen-Konvention einmal verbindlich
            # festlegt. Siehe HANDOFF, 2026-08-21, Abschnitt "Sofa-Spiegelung".
            flipped.append(item)
        return flipped
    if space == FURNITURE_COORDINATE_SPACE:
        raise SystemExit(
            f"{path}: this furniture was placed on the CORRECTION candidate, "
            f"which is a different house than the annotation build (proved "
            f"2026-08-21: washing machine set in the HWR rendered in the "
            f"bedroom, mirrored). Migrate it once with: python "
            f"moebel-migrieren.py {project_id}")
    hint = (" — that is the pre-correction render space; re-place this floor's "
            "furniture on the correction plan"
            if space == LEGACY_FURNITURE_SPACE else "")
    raise SystemExit(
        f"{path}: furniture is in an unsupported coordinate space ({space!r})"
        f"{hint}. Refusing to approximate.")


class Frame:
    """Normalized annotation space -> millimetres, y flipped.

    Image y grows downward; a floorplan in 3D wants y growing north, otherwise
    every plan renders mirrored and every door swings the wrong way.
    """

    def __init__(self, scale_metres_per_x_unit, pixel_width, pixel_height):
        self.width_mm = scale_metres_per_x_unit * 1000.0
        self.height_mm = self.width_mm * (pixel_height / float(pixel_width))

    def point(self, position):
        return [round(position["x"] * self.width_mm, 1),
                round((1.0 - position["y"]) * self.height_mm, 1)]

    def xy(self, x, y):
        return self.point({"x": x, "y": y})


class RegisteredFrame(Frame):
    """An upper storey's frame, REGISTERED onto the ground floor's.

    Every storey is drawn on its own image and calibrated on its own, so
    its millimetres have their own scale and origin. Stacking them raw put
    onehalfstorey_029's Obergeschoss 463mm inside the Erdgeschoss on the
    east and 150-600mm OVER it on the other sides (EG scale 12.686, OG
    12.430 -- 2 percent apart), while the floorplans show the OG rectangle
    sitting exactly on the EG's main outline (Rainer, 2026-08-23: "the
    floors are not properly aligned").

    Two steps, both from data Rainer already drew:
      1. The annotator's floor-alignment marks (the same two diagonal outer
         corners clicked on both drawings) give a per-axis affine from this
         storey's normalized coordinates into the ground floor's, which then
         goes through the ground floor's Frame.
      2. Hand-clicked marks are ~100-200mm precise, so points on this
         storey's OUTER faces are snapped onto ground-floor exterior lines
         within SNAP_MM -- flush where the drawings mean flush; anything
         further apart (a real setback) is kept as drawn.
    """
    SNAP_MM = 350.0
    # Rooms along one facade are hand-drawn within ~150mm of each other;
    # 60mm let one room snap and its neighbour stay (jagged west face).
    OUTER_FACE_MM = 150.0

    def __init__(self, ground_frame, affine, outer_x_lines, outer_y_lines, own_points,
                 outline_x_lines=(), outline_y_lines=()):
        # outer_*_lines are where ROOM edges snap (the ground floor's inner
        # faces); outline_*_lines are where this storey's OWN OUTLINE snaps.
        # An outline traces the OUTER face, so it must land on the ground
        # floor's outer faces. Sharing the room lines snapped it 240 mm
        # inside the ground floor on every side (twostorey_050, 2026-09-19).
        self._outline_x_lines = sorted(outline_x_lines)
        self._outline_y_lines = sorted(outline_y_lines)
        self.width_mm = ground_frame.width_mm
        self.height_mm = ground_frame.height_mm
        self._ground = ground_frame
        self._ax, self._bx, self._ay, self._by = affine
        self._x_lines = sorted(outer_x_lines)
        self._y_lines = sorted(outer_y_lines)
        raw = [self._registered(p) for p in own_points]
        xs = [q[0] for q in raw] or [0.0]
        ys = [q[1] for q in raw] or [0.0]
        self._bbox = (min(xs), max(xs), min(ys), max(ys))

    def _registered(self, position):
        return self._ground.point({"x": self._ax * position["x"] + self._bx,
                                   "y": self._ay * position["y"] + self._by})

    @staticmethod
    def _snap(value, lines, snap):
        best = min(lines, key=lambda line: abs(line - value), default=None)
        return best if best is not None and abs(best - value) <= snap else value

    def point(self, position):
        x, y = self._registered(position)
        x0, x1, y0, y1 = self._bbox
        if min(abs(x - x0), abs(x - x1)) <= self.OUTER_FACE_MM:
            x = self._snap(x, self._x_lines, self.SNAP_MM)
        if min(abs(y - y0), abs(y - y1)) <= self.OUTER_FACE_MM:
            y = self._snap(y, self._y_lines, self.SNAP_MM)
        return [round(x, 1), round(y, 1)]

    def outline_polygon(self, positions):
        """This storey's own outline, registered onto the ground floor and
        snapped flush to the ground floor's OUTER faces where the drawings
        mean flush (within SNAP_MM); a real setback is kept as drawn."""
        raw = [self._registered(p) for p in positions]
        xs = [q[0] for q in raw]
        ys = [q[1] for q in raw]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        out = []
        for x, y in raw:
            if min(abs(x - x0), abs(x - x1)) <= self.OUTER_FACE_MM:
                x = self._snap(x, self._outline_x_lines, self.SNAP_MM)
            if min(abs(y - y0), abs(y - y1)) <= self.OUTER_FACE_MM:
                y = self._snap(y, self._outline_y_lines, self.SNAP_MM)
            out.append([round(x, 1), round(y, 1)])
        return out


def _alignment_affine(marks, source_level, target_level):
    """Per-axis affine mapping SOURCE_LEVEL's floor_alignment marks onto
    TARGET_LEVEL's: the same nearest-pairing method frame_for_level() uses
    to register an upper storey onto the ground floor, generalized so the
    exterior outline can be registered the same way regardless of which
    floor it was drawn on. None if usable marks aren't present on both
    sides."""
    s_marks, t_marks = marks.get(source_level) or [], marks.get(target_level) or []
    if len(s_marks) != 2 or len(t_marks) != 2:
        return None
    pairs = [(sm, min(t_marks, key=lambda q: (q["x"] - sm["x"]) ** 2 + (q["y"] - sm["y"]) ** 2))
             for sm in s_marks]
    (s1, t1), (s2, t2) = pairs
    if t1 is t2 or abs(s1["x"] - s2["x"]) < 1e-6 or abs(s1["y"] - s2["y"]) < 1e-6:
        return None
    ax = (t1["x"] - t2["x"]) / (s1["x"] - s2["x"])
    ay = (t1["y"] - t2["y"]) / (s1["y"] - s2["y"])
    return (ax, t1["x"] - ax * s1["x"], ay, t1["y"] - ay * s1["y"])


def outline_points_for_ground(annotations, ground_level):
    """The exterior outline's points, in the GROUND FLOOR's own normalized
    frame.

    Two floor scans are never pixel-registered, so a raw outline drawn on
    one floor's image means a different place on another floor's -- it hugs
    the floor it was drawn on and misses every other floor's real exterior
    wall by however far the scans are offset. `outer_outline_floor` records
    which floor's image the outline was actually drawn on; when that is not
    the ground floor, register it through the same two diagonal
    floor_alignment corners the Annotator's own preview uses
    (annotate.js outlineForFloor()) before it can be treated as ground-
    native.

    Rainer, 2026-09-13, twostorey_045: the outline was drawn on upperfloor;
    reading it raw through the ground floor's frame left the ground floor's
    north wall about 15% of the image short of where the annotation itself
    says the building ends. Align Floors fixes the Annotator's own preview,
    but this script had no matching correction, so the built geometry
    stayed wrong even after aligning.
    """
    outline = annotations.get("outer_outline")
    if not outline:
        return None
    home = annotations.get("outer_outline_floor") or ground_level
    if home == ground_level:
        return outline
    affine = _alignment_affine(annotations.get("floor_alignment") or {}, home, ground_level)
    if not affine:
        raise SystemExit(
            f"Aussenumriss wurde auf {home} gezeichnet, nicht auf {ground_level} -- "
            f"im Annotator auf {ground_level} UND {home} dieselben zwei diagonal "
            f"gegenueberliegenden Aussenecken markieren (Werkzeug 'Floor alignment'), "
            f"sonst landet der Umriss auf der falschen Geschossgeometrie.")
    ax, bx, ay, by = affine
    return [{"x": ax * p["x"] + bx, "y": ay * p["y"] + by} for p in outline]


def outline_points_for_level(annotations, level, ground_level):
    """This LEVEL's own exterior-outline override for wall derivation, or
    None if this level should be built from its own room polygons alone.

    Rainer, 2026-09-19: "how else can i add notches and also get the sizes
    and floor alignemtnt correct" -- a real notch/setback IS specific to one
    floor. `annotations["outer_outlines"]` (per floor, from annotate.js
    setOuterOutline()) is used directly when present: each entry is already
    in ITS OWN floor's frame, so unlike the legacy single outline below,
    there is no cross-floor transform to get wrong here, and it applies to
    ANY level that has its own entry -- not ground only.

    Legacy single-outline projects (annotated before per-floor storage
    existed) have no "outer_outlines" key at all -- exact old behavior for
    those: one outline, transformed onto ground_level regardless of which
    floor's image it was drawn on (outline_points_for_ground(), above),
    applied ONLY when level == ground_level. A project keeps taking this
    path until someone actually redraws its outline with the updated
    annotator, which always saves outer_outlines from then on.
    """
    per_floor = annotations.get("outer_outlines")
    if per_floor is not None:
        return per_floor.get(level) or None
    if level != ground_level:
        return None
    return outline_points_for_ground(annotations, ground_level)


def frame_for_level(annotations, level, ground_level, pixel_width, pixel_height):
    """The Frame a storey's normalized points go through: the plain one for
    the ground floor (or any storey without alignment marks), a
    RegisteredFrame for an upper storey whose marks pair with the ground's."""
    floor_scale = annotations.get("floor_scale") or {}
    scale = floor_scale.get(level)
    if not scale:
        return None
    own = Frame(scale, pixel_width, pixel_height)
    if level == ground_level or not floor_scale.get(ground_level):
        return own
    # HARD RULE (Rainer, 2026-08-23: "make this a rule so we cannot go
    # forward without the alignment"): an upper storey without usable
    # alignment marks is NOT built, not furnished, not measured -- it
    # would stack misregistered by hundreds of millimetres, silently.
    marks = annotations.get("floor_alignment") or {}
    g_marks, u_marks = marks.get(ground_level) or [], marks.get(level) or []
    fehlt = (f"Ausrichtung fehlt fuer {level}: im Annotator auf {ground_level} UND "
             f"{level} dieselben zwei diagonal gegenueberliegenden Aussenecken "
             f"markieren (Werkzeug 'Floor alignment'). Ohne Registrierung wird "
             f"kein Obergeschoss gebaut.")
    if len(g_marks) != 2 or len(u_marks) != 2:
        raise SystemExit(fehlt)
    pairs = [(um, min(g_marks, key=lambda q: (q["x"] - um["x"]) ** 2 + (q["y"] - um["y"]) ** 2))
             for um in u_marks]
    (u1, g1), (u2, g2) = pairs
    if g1 is g2 or abs(u1["x"] - u2["x"]) < 1e-6 or abs(u1["y"] - u2["y"]) < 1e-6:
        raise SystemExit(fehlt + " (Die vorhandenen Marken liegen nicht diagonal.)")
    ax = (g1["x"] - g2["x"]) / (u1["x"] - u2["x"])
    ay = (g1["y"] - g2["y"]) / (u1["y"] - u2["y"])
    affine = (ax, g1["x"] - ax * u1["x"], ay, g1["y"] - ay * u1["y"])
    ground = Frame(floor_scale[ground_level], pixel_width, pixel_height)

    # Ground-floor exterior lines to snap onto: from its rooms' walls.
    ground_rooms = []
    for item in annotations.get("annotations", []):
        if item.get("floor_level") != ground_level or len(item.get("points") or []) < 3:
            continue
        if excluded(item.get("label")):
            continue
        ground_rooms.append({
            "id": item.get("id") or f"room-{len(ground_rooms)}",
            "name": item.get("label") or "Raum",
            "kind": room_kind(item.get("label")),
            "polygon_mm": [ground.point(p) for p in item["points"]],
        })
    # The ground floor's exterior walls EXACTLY as the plan builds them (with
    # the drawn outline, reference outside_face). Snap targets are NOT the
    # wall centrelines but the centreline shifted INWARD by half the wall:
    # an upper storey has no outline, so its exterior walls get pushed
    # OUTWARD from its room edges by half a thickness -- a room edge snapped
    # to (centreline - t/2) therefore lands its wall centreline exactly on
    # the ground floor's. Snapping room edges to room edges would miss by a
    # full wall, because ground-floor rooms are drawn to the OUTER face.
    outline_points = outline_points_for_level(annotations, ground_level, ground_level)
    outer_outline_mm = ([ground.point(p) for p in outline_points]
                        if outline_points else None)
    ground_walls = build_walls(ground_rooms, outer_outline_mm,
                               annotations.get("outer_outline_reference")
                               or DEFAULT_OUTLINE_REFERENCE)
    g_xs = [q[0] for r in ground_rooms for q in r["polygon_mm"]]
    g_ys = [q[1] for r in ground_rooms for q in r["polygon_mm"]]
    g_cx = (min(g_xs) + max(g_xs)) / 2 if g_xs else 0.0
    g_cy = (min(g_ys) + max(g_ys)) / 2 if g_ys else 0.0
    x_lines, y_lines = set(), set()
    for wall in ground_walls:
        if wall.get("wall_type") != "exterior":
            continue
        (sx, sy), (ex, ey) = wall["start_mm"], wall["end_mm"]
        half = (wall.get("thickness_mm") or 240) / 2.0
        if abs(sx - ex) < 1.0:
            x_lines.add(round(sx + (half if sx < g_cx else -half), 1))
        elif abs(sy - ey) < 1.0:
            y_lines.add(round(sy + (half if sy < g_cy else -half), 1))
    # Outer faces of the ground floor, for this storey's own outline: the
    # ground outline's own coordinates when one is drawn, else the exterior
    # wall centrelines pushed OUTWARD by half a wall.
    if outer_outline_mm:
        o_x_lines = {round(q[0], 1) for q in outer_outline_mm}
        o_y_lines = {round(q[1], 1) for q in outer_outline_mm}
    else:
        o_x_lines, o_y_lines = set(), set()
        for wall in ground_walls:
            if wall.get("wall_type") != "exterior":
                continue
            (sx, sy), (ex, ey) = wall["start_mm"], wall["end_mm"]
            half = (wall.get("thickness_mm") or 240) / 2.0
            if abs(sx - ex) < 1.0:
                o_x_lines.add(round(sx - (half if sx < g_cx else -half), 1))
            elif abs(sy - ey) < 1.0:
                o_y_lines.add(round(sy - (half if sy < g_cy else -half), 1))
    own_points = [p for item in annotations.get("annotations", [])
                  if item.get("floor_level") == level and not excluded(item.get("label"))
                  for p in (item.get("points") or [])]
    print(f"[plan] {level}: registered onto {ground_level} via alignment marks "
          f"(scale x{ax:.4f} y{ay:.4f}), outer faces snap to {len(x_lines)}+{len(y_lines)} "
          f"ground lines within {RegisteredFrame.SNAP_MM:.0f}mm")
    return RegisteredFrame(ground, affine, x_lines, y_lines, own_points,
                           outline_x_lines=o_x_lines, outline_y_lines=o_y_lines)


def polygon_area(points):
    total = 0.0
    for index, (x, y) in enumerate(points):
        nx, ny = points[(index + 1) % len(points)]
        total += x * ny - nx * y
    return abs(total) / 2.0


def _edges_of(rooms):
    """Every room boundary edge, with the room's centroid so "outward" is known."""
    out = []
    for room in rooms:
        points = room["polygon_mm"]
        cx = sum(p[0] for p in points) / len(points)
        cy = sum(p[1] for p in points) / len(points)
        for index, start in enumerate(points):
            end = points[(index + 1) % len(points)]
            if math.dist(start, end) < 150:
                continue
            out.append({"room": room["id"], "a": list(start), "b": list(end),
                        "centroid": (cx, cy)})
    return out


def _overlap(edge_a, edge_b):
    """Portion of edge_a that faces edge_b, as two points, or None.

    Rooms are annotated as their INNER boundary, so two rooms either side of a
    partition never share an edge — they have parallel edges about a wall
    thickness apart. The first version of this looked for shared edges and
    found none, which is why every one of the 40 walls came out exterior. What
    actually identifies an interior wall is a pair of near-parallel edges,
    close together, whose lengths overlap.
    """
    ax, ay = edge_a["a"]
    bx, by = edge_a["b"]
    length = math.dist((ax, ay), (bx, by))
    if length < 150:
        return None
    ux, uy = (bx - ax) / length, (by - ay) / length

    # Project the other edge onto this one and keep the overlapping stretch.
    ts = []
    for point in (edge_b["a"], edge_b["b"]):
        ts.append((point[0] - ax) * ux + (point[1] - ay) * uy)
    low, high = max(0.0, min(ts)), min(length, max(ts))
    if high - low < 400:
        return None
    return ((ax + ux * low, ay + uy * low), (ax + ux * high, ay + uy * high))


def _perpendicular_gap(edge_a, edge_b):
    ax, ay = edge_a["a"]
    bx, by = edge_a["b"]
    length = math.dist((ax, ay), (bx, by))
    ux, uy = (bx - ax) / length, (by - ay) / length
    nx, ny = -uy, ux
    gaps = [abs((point[0] - ax) * nx + (point[1] - ay) * ny) for point in (edge_b["a"], edge_b["b"])]
    return sum(gaps) / 2.0


# Kept in sync with floorplan-simplifier/walls.py -- see that file's
# _merge_collinear_walls docstring for the full rationale (Rainer,
# 2026-08-13: "the outer wall ... has to be one element").
MERGE_LINE_OFFSET_TOLERANCE_MM = 150
MERGE_GAP_TOLERANCE_MM = 300
# Rainer, 2026-08-16: "correct the walls whenever you generate them, 90
# degree angels or sometimes 45 corners, closed and points to close like
# under 40cm you can combine and fill out those damn corners". Kept in sync
# with floorplan-simplifier/walls.py's copy of the same function.
OUTLINE_WELD_DISTANCE_MM = 400
OUTLINE_ANGLE_SNAP_TOLERANCE_DEG = 6.0


def _regularize_outline_points(points, weld_distance_mm=OUTLINE_WELD_DISTANCE_MM,
                                angle_tolerance_deg=OUTLINE_ANGLE_SNAP_TOLERANCE_DEG):
    """Clean up a hand-drawn closed polygon before it becomes walls:

    1. Weld consecutive vertices closer than weld_distance_mm into one point.
    2. Make near-axis edges exactly axis-aligned by snapping VERTEX
       COORDINATES, not edge directions.

    Why coordinates and not directions: snapping each edge's angle while
    keeping its length re-walks the loop, and eight independently snapped
    edges no longer meet at the end. The old code knew this -- it rotated the
    loop so the SHORTEST edge would absorb the closure error -- but absorbing
    it anywhere still leaves one crooked wall. onehalfstorey_029 was drawn with
    every edge within 2.7 degrees of an axis, comfortably inside the 6 degree
    tolerance, and still came out with a wall 6.7 degrees off, because that one
    edge was carrying the drift of the other seven (Rainer, 2026-08-19: "the
    outer wall is wrong, i redrew that and it is still wrong").

    Sharing a coordinate cannot fail to close: a near-vertical edge means its
    two endpoints have the same x, a near-horizontal edge the same y. Those are
    constraints on POINTS, so they are resolved by grouping the points and
    averaging -- the polygon stays closed by construction, and every near-axis
    edge ends up exactly axis-true rather than one of them absorbing the rest.

    Edges near a 45 degree diagonal are left exactly as drawn: they carry no
    shared-coordinate constraint, and forcing one would move a corner that the
    axis-aligned neighbours have already pinned.
    """
    if len(points) < 3:
        return [list(p) for p in points]

    welded = [list(points[0])]
    for p in points[1:]:
        if math.dist(welded[-1], p) >= weld_distance_mm:
            welded.append(list(p))
    if len(welded) > 2 and math.dist(welded[-1], welded[0]) < weld_distance_mm:
        welded.pop()
    if len(welded) < 3:
        return welded

    n = len(welded)
    tolerance = math.radians(angle_tolerance_deg)

    parent_x = list(range(n))
    parent_y = list(range(n))

    def find(parent, i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(parent, a, b):
        ra, rb = find(parent, a), find(parent, b)
        if ra != rb:
            parent[rb] = ra

    for i in range(n):
        j = (i + 1) % n
        dx = welded[j][0] - welded[i][0]
        dy = welded[j][1] - welded[i][1]
        if math.hypot(dx, dy) < 1e-6:
            continue
        angle = math.atan2(dy, dx)
        off_vertical = abs(abs(angle) - math.pi / 2)
        off_horizontal = min(abs(angle), math.pi - abs(angle))
        if off_vertical <= tolerance:
            union(parent_x, i, j)      # same x -> exactly vertical
        elif off_horizontal <= tolerance:
            union(parent_y, i, j)      # same y -> exactly horizontal

    groups_x, groups_y = {}, {}
    for i in range(n):
        groups_x.setdefault(find(parent_x, i), []).append(i)
        groups_y.setdefault(find(parent_y, i), []).append(i)

    out = [list(p) for p in welded]
    for members in groups_x.values():
        if len(members) > 1:
            mean = sum(welded[i][0] for i in members) / len(members)
            for i in members:
                out[i][0] = mean
    for members in groups_y.values():
        if len(members) > 1:
            mean = sum(welded[i][1] for i in members) / len(members)
            for i in members:
                out[i][1] = mean
    return out


def _merge_collinear_walls(walls):
    by_type = {}
    for wall in walls:
        by_type.setdefault(wall["wall_type"], []).append(wall)

    merged_all = []
    for wall_type, group in by_type.items():
        lines = []
        for wall in group:
            ax, ay = wall["start_mm"]
            bx, by = wall["end_mm"]
            length = math.dist((ax, ay), (bx, by))
            if length < 1e-6:
                continue
            ux, uy = (bx - ax) / length, (by - ay) / length
            angle = math.atan2(uy, ux) % math.pi
            # nx,ny FROM THE CANONICAL angle, not the raw (possibly reversed)
            # direction -- two walls on the identical line but stored with
            # opposite start/end order used to get opposite-signed offsets
            # here (one +6441.7, the other -6416.3 on the same 6.4m line),
            # so this step silently left them unmerged 25mm apart instead of
            # unifying them (Rainer, 2026-08-22: "die Tueren und waende sind
            # 'off'" -- bungalow_039's Schlafen/Diele wall). angle is already
            # direction-invariant (the %math.pi fold); deriving the normal
            # from it instead of from ux,uy makes offset direction-invariant
            # too, so two collinear segments always land on one shared line
            # here regardless of which room's edge produced which direction.
            nx, ny = -math.sin(angle), math.cos(angle)
            offset = ax * nx + ay * ny
            placed = False
            for line in lines:
                angle_diff = abs((angle - line["angle"] + math.pi / 2) % math.pi - math.pi / 2)
                if (angle_diff <= math.radians(PARALLEL_TOLERANCE_DEG)
                        and abs(offset - line["offset"]) <= MERGE_LINE_OFFSET_TOLERANCE_MM):
                    line["members"].append(wall)
                    placed = True
                    break
            if not placed:
                lines.append({"angle": angle, "offset": offset, "members": [wall]})

        for line in lines:
            members = line["members"]
            ref = members[0]
            rax, ray = ref["start_mm"]
            rbx, rby = ref["end_mm"]
            rlen = math.dist((rax, ray), (rbx, rby)) or 1.0
            rux, ruy = (rbx - rax) / rlen, (rby - ray) / rlen

            def _t(point):
                return (point[0] - rax) * rux + (point[1] - ray) * ruy

            spans = []
            for wall in members:
                t0 = _t(wall["start_mm"])
                t1 = _t(wall["end_mm"])
                spans.append((min(t0, t1), max(t0, t1), wall["thickness_mm"],
                             set(wall.get("rooms") or [])))
            spans.sort(key=lambda s: s[0])

            run_lo, run_hi, run_thickness, run_rooms = spans[0]
            for lo, hi, thickness, rooms in spans[1:]:
                if lo - run_hi <= MERGE_GAP_TOLERANCE_MM:
                    run_hi = max(run_hi, hi)
                    run_thickness = max(run_thickness, thickness)
                    run_rooms |= rooms
                    continue
                merged_all.append({
                    "id": f"wall-{len(merged_all)}",
                    "start_mm": [rax + rux * run_lo, ray + ruy * run_lo],
                    "end_mm": [rax + rux * run_hi, ray + ruy * run_hi],
                    "thickness_mm": run_thickness,
                    "wall_type": wall_type,
                    "rooms": sorted(run_rooms),
                })
                run_lo, run_hi, run_thickness, run_rooms = lo, hi, thickness, rooms
            merged_all.append({
                "id": f"wall-{len(merged_all)}",
                "start_mm": [rax + rux * run_lo, ray + ruy * run_lo],
                "end_mm": [rax + rux * run_hi, ray + ruy * run_hi],
                "thickness_mm": run_thickness,
                "wall_type": wall_type,
                "rooms": sorted(run_rooms),
            })

    return merged_all


MITER_LIMIT = 2.0   # max corner reach as a multiple of the offset distance


def _offset_outline_inward(points, distance_mm):
    """Move every edge of a closed polygon `distance_mm` toward its interior.

    Each edge is shifted along its own inward normal and consecutive shifted
    edges are re-intersected, so corners stay sharp instead of being rounded or
    left with gaps. A corner whose edges are nearly parallel has no usable
    intersection; there the shifted point is used directly rather than letting
    a near-singular solve throw the vertex across the building.
    """
    n = len(points)
    if n < 3 or distance_mm == 0:
        return [list(p) for p in points]

    area2 = sum(points[i][0] * points[(i + 1) % n][1] - points[(i + 1) % n][0] * points[i][1]
                for i in range(n))
    inward = 1.0 if area2 > 0 else -1.0      # +1 for counter-clockwise winding
    # A NEGATIVE distance offsets outward instead. Needed for an outline drawn
    # along the inside face, where the centreline lies outside the drawn line.
    if distance_mm < 0:
        inward = -inward
    distance_mm = abs(distance_mm)

    lines = []
    for i in range(n):
        ax, ay = points[i]
        bx, by = points[(i + 1) % n]
        dx, dy = bx - ax, by - ay
        length = math.hypot(dx, dy)
        if length < 1e-9:
            lines.append(None)
            continue
        nx, ny = -dy / length * inward, dx / length * inward
        lines.append((ax + nx * distance_mm, ay + ny * distance_mm, dx / length, dy / length))

    out = []
    for i in range(n):
        prev = lines[(i - 1) % n]
        cur = lines[i]
        if prev is None or cur is None:
            out.append(list(points[i]))
            continue
        px, py, pdx, pdy = prev
        cx, cy, cdx, cdy = cur
        denominator = pdx * cdy - pdy * cdx
        if abs(denominator) < 1e-9:          # nearly parallel: no sharp corner
            out.append([cx, cy])
            continue
        t = ((cx - px) * cdy - (cy - py) * cdx) / denominator
        corner = [px + pdx * t, py + pdy * t]

        # Miter limit (Codex review 2026-08-19). At an interior angle theta the
        # mitred corner sits distance/sin(theta/2) from the original vertex, so
        # a sharp notch throws the vertex far outside the building: 20 degrees
        # would move a 175mm offset by about 1000mm. Clamp it back along the
        # direction it travelled.
        #
        # Measured on this corpus before choosing the limit: 5 outlines, 32
        # corners, ALL between 60 and 120 degrees, sharpest 86.29 degrees =
        # 1.46x the offset. MITER_LIMIT 2.0 therefore cannot trigger on any
        # current house -- verified by recompiling all four buildable plans and
        # diffing the geometry, which was byte-identical. It exists so a future
        # sharp outline degrades to a bevel instead of a spike.
        #
        # Und es ist jetzt wirklich ein Bevel. Codex, 2026-08-20, zur ersten
        # Fassung: "zieht lediglich den berechneten Schnittpunkt radial zum
        # Originaleck zurueck. Der neue Punkt liegt dann im Allgemeinen auf
        # keiner der beiden parallelen Offset-Kanten." Das stimmte -- die
        # Ecke wanderte einfach naeher heran und lag danach auf keiner der
        # beiden Wandachsen mehr, also stimmte an einem spitzen Eck die
        # Wandstaerke nicht mehr.
        #
        # Ein Bevel hat ZWEI Punkte: den Lotpunkt auf der vorherigen und den
        # auf der folgenden Offset-Kante. Beide liegen definitionsgemaess auf
        # ihrer Kante und genau `distance_mm` vom Originaleck entfernt. Aus dem
        # Eck wird damit eine kurze Schraege -- eine echte abgeschraegte Wand,
        # kein verzogener Punkt.
        vx, vy = corner[0] - points[i][0], corner[1] - points[i][1]
        reach = math.hypot(vx, vy)
        cap = distance_mm * MITER_LIMIT
        if reach > cap > 0:
            ex, ey = points[i]
            out.append([ex - pdy * inward * distance_mm,
                        ey + pdx * inward * distance_mm])
            out.append([ex - cdy * inward * distance_mm,
                        ey + cdx * inward * distance_mm])
            continue
        out.append(corner)
    return out


# What the drawn Aussenumriss actually traces. Codex asked for this to be
# stated rather than assumed: "outline semantics must be explicit
# (outside_face / centreline / inside_face)". The value maps to the offset
# applied before the outline becomes wall CENTRELINES -- positive inward,
# negative outward, zero for a line already drawn on the centreline.
OUTLINE_REFERENCES = {
    "outside_face": +DEFAULT_WALL_THICKNESS_MM / 2.0,
    "centreline": 0.0,
    "inside_face": -DEFAULT_WALL_THICKNESS_MM / 2.0,
}
DEFAULT_OUTLINE_REFERENCE = "outside_face"
# Room edges this close to a per-floor outline are that wall's inner face, not
# a partition of their own (1.75 x the 240 mm default wall).
OUTLINE_ROOM_EDGE_TOLERANCE_MM = 420.0


def _outline_to_walls(outline_mm, reference=DEFAULT_OUTLINE_REFERENCE):
    """Exterior walls straight from a user-drawn outline polygon (in mm) --
    one wall per edge, already one-element-per-straight-run by
    construction. Regularized first (see _regularize_outline_points) so
    near-duplicate corners and off-angle edges from freehand drawing don't
    become visible wall defects."""
    outline_mm = _regularize_outline_points(outline_mm)
    # The drawn Aussenumriss traces the OUTSIDE FACE of the building -- that is
    # what you see on a floorplan and what a person traces. Walls, however, are
    # defined by their CENTRELINE, so emitting the outline unchanged made every
    # building half a wall thickness too big on all four sides: 120mm of a
    # 240mm wall standing outside the line that was drawn (Codex review,
    # 2026-08-19, ranked this the most likely cause of "the outer wall is
    # wrong" after the angles were already exact).
    #
    # So the outline is offset INWARD by half the wall thickness before it
    # becomes centrelines. Inward is decided from the polygon's own winding via
    # the signed area, not assumed, because a hand-drawn outline can be traced
    # either way round.
    # Which face the line represents is now READ, not assumed. The default is
    # outside_face, so an annotation that says nothing behaves exactly as
    # before -- verified by recompiling all four buildable plans and diffing
    # them byte for byte.
    if reference not in OUTLINE_REFERENCES:
        raise SystemExit(
            "outer_outline_reference=%r ist unbekannt. Erlaubt: %s"
            % (reference, ", ".join(sorted(OUTLINE_REFERENCES))))
    outline_mm = _offset_outline_inward(outline_mm, OUTLINE_REFERENCES[reference])
    walls = []
    for index, start in enumerate(outline_mm):
        end = outline_mm[(index + 1) % len(outline_mm)]
        if math.dist(start, end) < 150:
            continue
        walls.append({
            "id": f"wall-outline-{index}",
            "start_mm": list(start),
            "end_mm": list(end),
            "thickness_mm": DEFAULT_WALL_THICKNESS_MM,
            "wall_type": "exterior",
            "rooms": [],
        })
    return walls


# How far apart two room boundaries may be and still be one partition rather
# than two rooms with a cupboard between them. German interior walls run
# 100-150 mm plus plaster; 400 mm is generous without being absurd.
MAX_PARTITION_GAP_MM = 400
PARALLEL_TOLERANCE_DEG = 12

# Zwei Raeume, die BUENDIG aneinander gezeichnet sind -- gemeinsame Kante,
# Abstand 0 -- sind durch eine Wand getrennt, deren Staerke einfach nicht
# eingezeichnet wurde. Das ist die normale Art, einen Grundriss zu zeichnen.
#
# Bis heute fiel genau dieser Fall durch: die Partnersuche verwarf jeden
# Abstand unter 20 mm, also entstand zwischen buendigen Raeumen GAR KEINE
# Wand. Gemessen an bungalow_039 am 2026-08-20: drei Kanten mit Abstand
# exakt 0,0 mm zwischen Diele/Kochen/Gast, und die drei Tueren, die darauf
# sitzen, fanden keine Wand -- "annotation has 15 door/window elements, plan
# accounts for 12". Ich habe das Rainer als Zeichenfehler angelastet. Es war
# keiner; die Zeichnung war praeziser als der Code, der sie las.
#
# Eine gemeinsame Kante bekommt deshalb eine Wand in ueblicher Staerke,
# mittig auf die Linie gesetzt: je 60 mm in jeden Raum. Nicht-tragende
# Innenwaende laufen in Deutschland 100-150 mm inkl. Putz.
FLUSH_PARTITION_MM = 20        # darunter gelten zwei Kanten als dieselbe Linie
DEFAULT_PARTITION_THICKNESS_MM = 120


def _merge_overlapping_parallel_walls(walls, rooms):
    """Zwei Waende duerfen sich nicht durchdringen -- dann sind sie EINE.

    Bleibt beim Kantenpaaren ein Stueck einer Raumkante uebrig (die Kante
    hat anderswo schon einen Partner), faellt dieses Reststueck in den
    Aussenwand-Zweig. Stehen sich zwei solche Reste gegenueber, entstehen
    zwei 240er "Aussenwaende" 169 mm voneinander -- eine Doppelwand mitten
    im Obergeschoss, die eine Tuer verdeckt (onehalfstorey_029, Rainer,
    2026-08-23: "one wall standing in front of one room ... we had a rule
    about combining any walls so close to each other").

    Die Regel ist geometrisch begruendbar: ueberlappen sich die KOERPER
    zweier paralleler Waende (Abstand kleiner als die halbe Summe ihrer
    Staerken), koennen es nicht zwei Bauteile sein. Sie werden auf die
    Mittellinie zusammengezogen. Liegt deren Mitte in einem Raum, ist es
    eine Innenwand -- "exterior" war beim Reststueck nur der Fallback.
    """
    if len(walls) < 2:
        return walls
    entfernt = set()
    ergebnis = []
    for index, wall in enumerate(walls):
        if index in entfernt:
            continue
        (ax, ay), (bx, by) = wall["start_mm"], wall["end_mm"]
        laenge = math.dist((ax, ay), (bx, by))
        if laenge < 1e-6:
            ergebnis.append(wall)
            continue
        ux, uy = (bx - ax) / laenge, (by - ay) / laenge
        nx, ny = -uy, ux
        for other_index in range(index + 1, len(walls)):
            if other_index in entfernt:
                continue
            other = walls[other_index]
            (cx, cy), (ex_, ey_) = other["start_mm"], other["end_mm"]
            laenge2 = math.dist((cx, cy), (ex_, ey_))
            if laenge2 < 1e-6:
                continue
            vx, vy = (ex_ - cx) / laenge2, (ey_ - cy) / laenge2
            if abs(ux * vy - uy * vx) > math.sin(math.radians(PARALLEL_TOLERANCE_DEG)):
                continue
            abstand = abs((cx - ax) * nx + (cy - ay) * ny)
            grenze = ((wall.get("thickness_mm") or 240)
                      + (other.get("thickness_mm") or 240)) / 2.0
            if abstand >= grenze:
                continue
            t = sorted(((cx - ax) * ux + (cy - ay) * uy,
                        (ex_ - ax) * ux + (ey_ - ay) * uy))
            if min(t[1], laenge) - max(t[0], 0.0) <= 200.0:
                continue
            versatz = ((cx - ax) * nx + (cy - ay) * ny) / 2.0
            t0, t1 = min(0.0, t[0]), max(laenge, t[1])
            start = [round(ax + ux * t0 + nx * versatz, 1),
                     round(ay + uy * t0 + ny * versatz, 1)]
            ende = [round(ax + ux * t1 + nx * versatz, 1),
                    round(ay + uy * t1 + ny * versatz, 1)]
            # Innen oder aussen entscheidet sich daran, ob auf BEIDEN Seiten
            # ein Raum liegt -- nicht daran, ob die Mitte selbst in einem
            # Raum liegt: die Mittellinie faellt genau in die Fuge zwischen
            # den zwei Raumpolygonen und traefe dort nie einen Raum.
            mitte = ((start[0] + ende[0]) / 2, (start[1] + ende[1]) / 2)
            fuehler = grenze + 200.0
            drinnen = all(
                any(point_in_polygon((mitte[0] + nx * fuehler * seite,
                                      mitte[1] + ny * fuehler * seite),
                                     r["polygon_mm"], 0)
                    for r in rooms if r.get("polygon_mm"))
                for seite in (1.0, -1.0))
            wall = dict(wall)
            wall["start_mm"], wall["end_mm"] = start, ende
            wall["thickness_mm"] = max(wall.get("thickness_mm") or 240,
                                       other.get("thickness_mm") or 240)
            if drinnen:
                wall["wall_type"] = "interior"
            wall["rooms"] = sorted(set(wall.get("rooms") or [])
                                   | set(other.get("rooms") or []))
            entfernt.add(other_index)
            print("[plan] Doppelwand zusammengefasst: %s + %s (%.0f mm auseinander) -> %s"
                  % (wall.get("id"), other.get("id"), abstand, wall.get("wall_type")))
            (ax, ay), (bx, by) = wall["start_mm"], wall["end_mm"]
            laenge = math.dist((ax, ay), (bx, by)) or 1.0
            ux, uy = (bx - ax) / laenge, (by - ay) / laenge
            nx, ny = -uy, ux
        ergebnis.append(wall)
    return ergebnis


def _close_exterior_corners(walls, tol_mm=800.0):
    """Aussenwand-Enden treffen sich in der Ecke -- exakt.

    Das Erdgeschoss bekommt seine Aussenwaende aus dem GEZEICHNETEN
    Aussenumriss, dessen Ecken schon zusammenfallen. Ein Obergeschoss hat
    keinen Umriss: seine Aussenwaende entstehen aus den Raumkanten, um eine
    halbe Wandstaerke nach aussen geschoben -- und genau um diese halbe
    Staerke enden sie VOR der Nachbarwand. Gemessen an onehalfstorey_029:
    Seitenwaende x=2818/11506 laufen y 809..10085, Front/Rueck y=689/10205
    laufen x 2938..11386; vier offene Ecken zu je 120 mm (Rainer,
    2026-08-23: "the corners are still not corners"). Sichtbar wurde es am
    Dach, dessen Umriss aus eben diesen Endpunkten getract wird.

    Zwei Aussenwaende, deren Enden nah beieinander liegen und die deutlich
    gegeneinander stehen, bekommen beide denselben Punkt: den Schnittpunkt
    ihrer Mittellinien. Liegen die Enden schon aufeinander (Erdgeschoss),
    ist der Schnittpunkt derselbe Punkt und es aendert sich nichts.
    """
    aussen = [w for w in walls if w.get("wall_type") == "exterior"]
    for i, a in enumerate(aussen):
        for b in aussen[i + 1:]:
            (ax1, ay1), (ax2, ay2) = a["start_mm"], a["end_mm"]
            (bx1, by1), (bx2, by2) = b["start_mm"], b["end_mm"]
            adx, ady = ax2 - ax1, ay2 - ay1
            bdx, bdy = bx2 - bx1, by2 - by1
            nenner = adx * bdy - ady * bdx
            if abs(nenner) < 1e-6:
                continue                      # parallel: keine Ecke
            winkel = abs(math.degrees(math.atan2(abs(nenner),
                                                 adx * bdx + ady * bdy)))
            if winkel < 30.0:
                continue                      # zu spitz, keine echte Ecke
            t = ((bx1 - ax1) * bdy - (by1 - ay1) * bdx) / nenner
            sx, sy = ax1 + adx * t, ay1 + ady * t
            # NUR benachbarte Enden verbinden: die beiden Endpunkte muessen
            # nahe BEIEINANDER liegen. Es genuegt nicht, dass ein Ende nahe am
            # Schnittpunkt liegt -- damit zog die erste Fassung im Erdgeschoss
            # die Wand am Vorsprung auf eine ganz andere Wand (gemessen:
            # wall-8 sprang von x=2818 auf x=3033) und zerstoerte den
            # L-Grundriss.
            # NUR DAS NAEHERE ENDE wandert auf die Ecke.
            #
            # Ohne diese Bedingung faellt jede Aussenwand zusammen, die
            # kuerzer als `tol_mm` ist: dann liegt auch ihr FERNES Ende
            # innerhalb der Toleranz und wird ebenfalls auf den Schnittpunkt
            # gezogen. Rainer, 2026-09-01, zu
            # german_catalog_review_bungalow_3_4_5_b_120: "the outer walls
            # seem to be kaputt at the entrance." Die Eingangsnische ist
            # 537 mm tief; ihre beiden Seitenwaende kamen mit Laenge 0
            # heraus, und die Nische stand im Render offen.
            def _naeher(wand, schluessel):
                gegen = "end_mm" if schluessel == "start_mm" else "start_mm"
                return (math.dist(wand[schluessel], (sx, sy))
                        <= math.dist(wand[gegen], (sx, sy)))

            for schluessel_a in ("start_mm", "end_mm"):
                pax, pay = a[schluessel_a]
                if not _naeher(a, schluessel_a):
                    continue
                for schluessel_b in ("start_mm", "end_mm"):
                    pbx, pby = b[schluessel_b]
                    if not _naeher(b, schluessel_b):
                        continue
                    if math.dist((pax, pay), (pbx, pby)) > tol_mm:
                        continue
                    if (math.dist((pax, pay), (sx, sy)) > tol_mm
                            or math.dist((pbx, pby), (sx, sy)) > tol_mm):
                        continue
                    ecke = [round(sx, 1), round(sy, 1)]
                    # Und niemals eine Wand auf null ziehen -- bei zwei
                    # gleich weit entfernten Enden greift die Regel oben
                    # nicht.
                    gegen_a = a["end_mm" if schluessel_a == "start_mm" else "start_mm"]
                    gegen_b = b["end_mm" if schluessel_b == "start_mm" else "start_mm"]
                    if math.dist(ecke, gegen_a) < 1.0 or math.dist(ecke, gegen_b) < 1.0:
                        continue
                    a[schluessel_a] = ecke
                    b[schluessel_b] = ecke
    return walls


# --- Innenwand-Geometrie (plans/interior-wall-geometry-v1.md) --------------
#
# Gemessen am 2026-08-23 ueber alle 94 baubaren Simplifier-Projekte, 582
# Innenwaende. 67 davon sind nicht achsparallel. Die Abweichungen von der
# naechsten Achse verteilen sich so:
#
#   5.56 .. 10.43 Grad   17 Waende   Zittern einer Handzeichnung
#   -------------------  MESSBAR LEER  -------------------
#   21.58 .. 39.28 Grad  16 Waende   echte Schraegen
#   40.62 .. 44.98 Grad  34 Waende   die klassische 45-Grad-Ecke
#
# Unter 5.56 Grad liegt nichts, weil _regularize_outline_points die
# Raumpolygone schon mit 6 Grad Toleranz geradezieht. Was danach uebrig
# bleibt, ist genau das Band 6..12 -- deshalb muss diese Toleranz GROESSER
# als 6 sein, um ueberhaupt zu wirken, und sie darf die echten Schraegen
# nicht anfassen. 12.0 liegt mitten in der gemessenen leeren Bandluecke
# zwischen 10.43 und 21.58 Grad; auf diesem Korpus gibt es damit keinen
# einzigen Grenzfall.
INTERIOR_ANGLE_SNAP_TOLERANCE_DEG = 12.0

# Wie weit ein Innenwand-Ende hoechstens verlaengert wird, um die Wand zu
# treffen, auf die es zulaeuft. Gemessen: die groesste echte Luecke im Korpus
# ist 184.8mm (bungalow_040_66), die haeufigste exakt 120.0mm -- eine halbe
# Aussenwandstaerke, weil Innenwaende aus den Raum-INNENKANTEN entstehen und
# Aussenwaende um eine halbe Staerke nach aussen geschoben werden. 400mm ist
# dasselbe "das ist noch dieselbe Wand"-Mass, das MAX_PARTITION_GAP_MM und
# OUTLINE_WELD_DISTANCE_MM schon benutzen.
T_JUNCTION_GAP_MM = 400.0
# Flacher als das ist kein T-Stoss, sondern zwei fast parallele Waende.
# Gleicher Wert wie in _close_exterior_corners.
T_JUNCTION_MIN_ANGLE_DEG = 30.0
# Der Fusspunkt darf bis hierhin ueber das Ende der Zielwand hinausliegen
# (eine L-Ecke trifft die Zielwand genau an deren Ende), aber nicht weiter --
# sonst dockt eine Wand an der unendlichen Verlaengerung einer ganz anderen
# Wand an.
T_JUNCTION_TARGET_OVERRUN_MM = 300.0


def _orthogonalize_interior_walls(walls, tolerance_deg=INTERIOR_ANGLE_SNAP_TOLERANCE_DEG):
    """Fast-achsparallele INNENwaende exakt achsparallel machen.

    _regularize_outline_points zieht die Raumpolygone gerade, aber nur mit 6
    Grad Toleranz und nur pro Polygon. Eine Innenwand entsteht aus der
    UEBERLAPPUNG zweier Kanten aus zwei verschiedenen Raeumen und erbt die
    Richtung der einen Kante -- war die 9 Grad schief, ist die Wand 9 Grad
    schief. Genau das war onehalfstorey_029s Obergeschoss: wall-4 lief auf
    170.58 Grad quer durch die Grenze Flur/Kind, waehrend jede andere
    Innenwand desselben Geschosses exakt war (Rainer, 2026-08-23, Screenshot
    aus dem Moebel-Editor).

    Gedreht wird um den MITTELPUNKT: bei einer fast waagerechten Wand bekommen
    beide Enden das mittlere y, bei einer fast senkrechten das mittlere x. Ein
    Anlegen an einen der beiden Endpunkte wuerde die Wand um bis zu ihre volle
    Schiefe in einen der beiden Raeume schieben und die Tuer darauf mitnehmen.

    Beweisbar wirkungslos auf sauberer Geometrie: haben beide Enden schon
    dasselbe y, ist deren Mittelwert genau dieses y, und die Werte kommen
    unveraendert zurueck. Aussenwaende und Waende ausserhalb der Toleranz
    werden gar nicht erst betrachtet.
    """
    # An end that ALREADY touches another wall's end anchors the snap axis
    # instead of the plain midpoint -- otherwise snapping both ends to their
    # mean can pull an end straight off a neighbour it was touching before
    # this function ran. Measured on twostorey_046: HWR/HTR's near-vertical
    # boundary against Diele (8.85 degrees off vertical) starts exactly on
    # the neighbouring wall's end at x=5719.9, but the mean-of-both-ends
    # snap moved that end to x=5904.6, opening a 184.7mm gap where there had
    # been none (Rainer, 2026-09-15: "the wall to the htr still has a whole
    # in it"). Anchor tolerance is small on purpose -- this is for ends that
    # are already touching, not the 400mm T-junction gap-closer's job.
    ANCHOR_TOL_MM = 5.0
    # (wall_index, point) for every endpoint, so a wall's own two ends can be
    # excluded by IDENTITY of their owning wall -- not by value, which would
    # wrongly exclude a NEIGHBOUR's end too whenever it coincides with one of
    # this wall's own ends (exactly the case this function needs to find).
    other_ends = [(i, p) for i, w in enumerate(walls)
                 for p in (w["start_mm"], w["end_mm"])]

    def _anchor(point, self_index):
        hits = [p for i, p in other_ends
                if i != self_index and math.dist(point, p) <= ANCHOR_TOL_MM]
        return hits[0] if hits else None

    tolerance = abs(tolerance_deg)
    for index, wall in enumerate(walls):
        if wall.get("wall_type") != "interior":
            continue
        (ax, ay), (bx, by) = wall["start_mm"], wall["end_mm"]
        dx, dy = bx - ax, by - ay
        if math.hypot(dx, dy) < 1e-6:
            continue
        angle = math.degrees(math.atan2(dy, dx)) % 180.0
        off_horizontal = min(angle, 180.0 - angle)
        off_vertical = abs(angle - 90.0)
        start_anchor = _anchor(wall["start_mm"], index)
        end_anchor = _anchor(wall["end_mm"], index)
        if off_horizontal <= tolerance and off_horizontal <= off_vertical:
            axis = (start_anchor[1] if start_anchor else
                    end_anchor[1] if end_anchor else (ay + by) / 2.0)
            wall["start_mm"] = [ax, axis]
            wall["end_mm"] = [bx, axis]
        elif off_vertical <= tolerance:
            axis = (start_anchor[0] if start_anchor else
                    end_anchor[0] if end_anchor else (ax + bx) / 2.0)
            wall["start_mm"] = [axis, ay]
            wall["end_mm"] = [axis, by]
    return walls


def _close_interior_t_junctions(walls, gap_mm=T_JUNCTION_GAP_MM,
                                min_angle_deg=T_JUNCTION_MIN_ANGLE_DEG,
                                overrun_mm=T_JUNCTION_TARGET_OVERRUN_MM):
    """Offene T-Stoesse schliessen: ein Innenwand-Ende bis auf die Mittellinie
    der Wand verlaengern, auf die es erkennbar zulaeuft.

    Warum die Luecken systematisch sind und nicht zufaellig: Innenwaende
    werden aus den INNENKANTEN der Raeume gebaut, Aussenwaende um eine halbe
    Wandstaerke nach AUSSEN geschoben. Jede Innenwand endet damit exakt
    120mm (halbe 240er Aussenwand) vor der Aussenwand-Mittellinie. Gemessen an
    onehalfstorey_029s Obergeschoss: neun offene Enden, 26.6 bis 120.0mm, und
    die 120.0er kamen sechsmal vor. In der Draufsicht sieht das aus wie eine
    Wand, die kurz vor der Wand aufhoert -- Rainers "not clean".

    Verlaengert wird NUR, nie gekuerzt und nie seitlich verschoben:

    * Der Schnittpunkt muss in Verlaengerungsrichtung liegen (t > 1mm). Ein
      Ende, das schon auf der Zielachse sitzt, hat t = 0 und faellt durch.
      Ein Ende, das ueber die Zielwand hinaussteht, hat t < 0 und faellt
      ebenfalls durch (Kuerzen ist eine eigene Entscheidung und ausdruecklich
      nicht Teil dieses Plans).
    * Die Zielwand muss deutlich gegen die eigene stehen (>= min_angle_deg),
      sonst waere es keine Ecke, sondern eine Flucht -- und eine kollineare
      Nachbarwand mit einer Tuer dazwischen wuerde zugeschweisst.
    * Der Fusspunkt muss innerhalb der Zielwand liegen (+- overrun_mm). Die
      Mittellinie ist unendlich, die Wand ist es nicht.
    * Die eigene Wand muss eine Innenwand sein. Aussenwand-Ecken macht
      _close_exterior_corners, und zwar vorher.

    Gerechnet wird gegen eine EINGEFRORENE Kopie der Wandliste und erst danach
    geschrieben, damit das Ergebnis nicht von der Reihenfolge der Liste
    abhaengt. Zwei Runden, weil eine verlaengerte Wand fuer eine zweite Wand
    erst dadurch zum erreichbaren Ziel werden kann.
    """
    for _ in range(2):
        frozen = [(list(w["start_mm"]), list(w["end_mm"])) for w in walls]
        updates = []
        for index, wall in enumerate(walls):
            if wall.get("wall_type") != "interior":
                continue
            (ax, ay), (bx, by) = frozen[index]
            length = math.dist((ax, ay), (bx, by))
            if length < 1e-6:
                continue
            ux, uy = (bx - ax) / length, (by - ay) / length
            for key, point, sign in (("start_mm", (ax, ay), -1.0),
                                     ("end_mm", (bx, by), 1.0)):
                dx, dy = ux * sign, uy * sign
                best = None
                for other_index, other in enumerate(walls):
                    if other_index == index:
                        continue
                    (ox1, oy1), (ox2, oy2) = frozen[other_index]
                    odx, ody = ox2 - ox1, oy2 - oy1
                    other_length = math.hypot(odx, ody)
                    if other_length < 1e-6:
                        continue
                    denominator = dx * ody - dy * odx
                    if abs(denominator) < 1e-9:
                        continue                      # parallel: kein T-Stoss
                    theta = abs(math.degrees(math.atan2(abs(denominator),
                                                        dx * odx + dy * ody)))
                    if theta < min_angle_deg:
                        continue
                    t = ((ox1 - point[0]) * ody - (oy1 - point[1]) * odx) / denominator
                    if t <= 1.0 or t > gap_mm:
                        continue                      # schon dran, oder zu weit
                    hit = (point[0] + dx * t, point[1] + dy * t)
                    s = ((hit[0] - ox1) * odx + (hit[1] - oy1) * ody) / other_length
                    if s < -overrun_mm or s > other_length + overrun_mm:
                        continue                      # neben der Zielwand
                    if best is None or t < best[0]:
                        best = (t, [round(hit[0], 1), round(hit[1], 1)])
                if best is not None:
                    updates.append((index, key, best[1]))
        if not updates:
            break
        for index, key, point in updates:
            walls[index][key] = point
    return walls


def _distance_to_polygon(point, polygon):
    """Shortest distance from `point` to any EDGE of `polygon` (mm).

    Point-to-segment, minimized over every edge -- not point-to-vertex,
    which would overstate the distance for a point that sits squarely
    against the middle of a long polygon edge (exactly the outline's long
    exterior runs).
    """
    px, py = point
    best = math.inf
    for i in range(len(polygon)):
        ax, ay = polygon[i]
        bx, by = polygon[(i + 1) % len(polygon)]
        dx, dy = bx - ax, by - ay
        length_sq = dx * dx + dy * dy
        if length_sq < 1e-9:
            t = 0.0
        else:
            t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
        nearest_x, nearest_y = ax + t * dx, ay + t * dy
        best = min(best, math.hypot(px - nearest_x, py - nearest_y))
    return best


def partition_walls(annotations, level, frame):
    """Trennwaende: von Hand eingezeichnete Innenwaende (Element "partition").

    Rainer, 2026-09-20: "can we also add a new element? a trennwand?" -- volle
    Hoehe, zwei Klicks, 120 mm wenn im Rechtsklick-Menue nichts anderes gewaehlt
    wurde, und Tueren/Fenster duerfen darin sitzen wie in jeder Wand. Sie
    entstehen hier als ganz normale Innenwaende und laufen mit durch die
    gemeinsame Wandbereinigung (geradeziehen, zusammenfuehren, T-Stoesse).
    """
    walls = []
    for element in annotations.get("elements", []):
        if element.get("type") != "partition" or element.get("floor_level") != level:
            continue
        points = element.get("points") or []
        if len(points) < 2:
            continue
        start, end = frame.point(points[0]), frame.point(points[1])
        if math.dist(start, end) < 1.0:
            continue
        walls.append({
            "id": f"wall-partition-{len(walls)}",
            "start_mm": start,
            "end_mm": end,
            "thickness_mm": int(element.get("thickness_mm") or DEFAULT_PARTITION_THICKNESS_MM),
            "wall_type": "interior",
            "rooms": [],
        })
    return walls


def build_walls(rooms, outer_outline_mm=None,
                outline_reference=DEFAULT_OUTLINE_REFERENCE,
                outline_edge_tolerance_mm=None, extra_walls=None):
    """Interior walls from facing room boundaries, exterior from the rest.

    An interior wall is centred between the two room faces it separates. An
    exterior wall is pushed outward by half its thickness, because the room
    polygon is the inside face and a wall drawn centred on it would eat into
    the room.

    outer_outline_mm: optional single closed polygon (list of [x, y] mm
    points) marking the true exterior boundary, drawn once by Rainer. When
    given, exterior walls come straight from its edges instead of the
    "uncovered room-edge span" heuristic below -- reliable regardless of how
    the room polygons underneath happen to be drawn. Kept in sync with
    floorplan-simplifier/walls.py's derive_walls.
    """
    # Straighten the ROOM polygons too, not just the drawn outline.
    #
    # The outline got vertex-coordinate snapping earlier today; room polygons
    # did not, so every wall derived from them kept the hand tremor -- 029's
    # upper floor came out with 4 walls up to 8.8 degrees off axis while its
    # ground floor (built from the outline) was exact. Same job, two code
    # paths, one of them fixed: the shape of nearly every fault in this
    # pipeline. Snapping here uses the identical function, so a room edge that
    # is within tolerance of horizontal or vertical becomes exactly that.
    rooms = [dict(room, polygon_mm=_regularize_outline_points(room["polygon_mm"]))
             if room.get("polygon_mm") and len(room["polygon_mm"]) >= 3 else room
             for room in rooms]
    edges = _edges_of(rooms)
    # An edge may face SEVERAL rooms along its length (a long HWR wall with
    # DU-WC on one span and the Flur on another). Exclusive one-shot pairing
    # (`used[j]`) let the first room consume the whole edge; the second
    # room's edge then found no partner and fell through to the exterior
    # branch -- a 240mm 'exterior' wall dead-ending in the middle of the
    # flat, which is exactly the fat junction stub seen on render (task
    # #12). So: an edge may partner once per FACING PAIR; only an edge that
    # never partnered at all becomes exterior. Each room's own edge pulls
    # in its own span, so a shared long edge ends up correctly split into
    # one thin wall per neighbour.
    partnered = [False] * len(edges)
    paired = set()
    # Per-edge list of (t0, t1) intervals along the edge that a pairing
    # actually covered. One pairing used to consume the WHOLE edge, so the
    # stretch of a long edge beyond its partner's overlap silently got NO
    # wall at all — confirmed on bungalow_040_66: the Gast/office east
    # edge paired with the Wohnen west edge over a partial span and the
    # remainder (the missing 'Wand D' Rainer pointed at) vanished.
    covered = [[] for _ in edges]
    walls = []

    def _interval_on(edge, span):
        ax, ay = edge["a"]
        bx, by = edge["b"]
        length = math.dist((ax, ay), (bx, by)) or 1.0
        ux, uy = (bx - ax) / length, (by - ay) / length
        ts = sorted(((p[0] - ax) * ux + (p[1] - ay) * uy) for p in span)
        return (max(0.0, ts[0]), min(length, ts[1]))

    for i, edge in enumerate(edges):
        angle = math.atan2(edge["b"][1] - edge["a"][1], edge["b"][0] - edge["a"][0])
        partner = None
        for j, other in enumerate(edges):
            if j == i or other["room"] == edge["room"] or (i, j) in paired:
                continue
            other_angle = math.atan2(other["b"][1] - other["a"][1], other["b"][0] - other["a"][0])
            difference = abs((angle - other_angle + math.pi / 2) % math.pi - math.pi / 2)
            if difference > math.radians(PARALLEL_TOLERANCE_DEG):
                continue
            gap = _perpendicular_gap(edge, other)
            if gap > MAX_PARTITION_GAP_MM:
                continue
            span = _overlap(edge, other)
            if span is None:
                continue
            # Buendig gezeichnet heisst: eine Wand ohne eingezeichnete Staerke.
            # Sie bekommt die uebliche, statt zu verschwinden.
            buendig = gap < FLUSH_PARTITION_MM
            if buendig:
                gap = float(DEFAULT_PARTITION_THICKNESS_MM)
            if partner is None or gap < partner[0]:
                partner = (gap, j, span, buendig)

        if partner is not None:
            gap, j, span, buendig = partner
            partnered[i] = partnered[j] = True
            paired.add((i, j))
            paired.add((j, i))
            covered[i].append(_interval_on(edges[i], span))
            covered[j].append(_interval_on(edges[j], span))
            other = edges[j]
            # Centreline sits midway between the two faces.
            ax, ay = edge["a"]
            bx, by = edge["b"]
            length = math.dist((ax, ay), (bx, by))
            nx, ny = -(by - ay) / length, (bx - ax) / length
            towards = (other["a"][0] - ax) * nx + (other["a"][1] - ay) * ny
            # Bei einer gemeinsamen Kante gibt es kein "drueben": die Wand
            # sitzt MITTIG auf der gezeichneten Linie, je halbe Staerke in
            # beide Raeume. Ein Versatz haette sie ganz in einen der beiden
            # geschoben, und die Tuer darauf haette wieder daneben gelegen.
            shift = 0.0 if buendig else (gap / 2.0) * (1 if towards > 0 else -1)
            walls.append({
                "id": f"wall-{len(walls)}",
                "start_mm": [round(span[0][0] + nx * shift, 1), round(span[0][1] + ny * shift, 1)],
                "end_mm": [round(span[1][0] + nx * shift, 1), round(span[1][1] + ny * shift, 1)],
                "thickness_mm": round(gap),
                "wall_type": "interior",
                "rooms": sorted({edge["room"], other["room"]}),
            })

    if outer_outline_mm:
        walls.extend(_outline_to_walls(outer_outline_mm, outline_reference))

    # Uncovered edges: whole edge when it never paired, or the leftover
    # stretch when a partial pairing didn't consume it all. With no drawn
    # outline these become exterior walls (below). With an outline, every
    # REAL exterior wall already came from it -- but an edge can still go
    # uncovered for a completely different reason: a small "step" in an
    # L-shaped room (e.g. HWR/HTR stepping sideways to meet Diele) has no
    # facing partner because it's a jog, not a shared partition, and it
    # sits nowhere near the outline. Skipping the whole loop whenever an
    # outline exists (the previous behaviour) silently dropped that jog
    # entirely -- confirmed on twostorey_046: HWR/HTR right boundary had a
    # 184.7mm gap exactly at its step, Rainer, 2026-09-15: "the wall to the
    # htr still has a whole in it". So the loop always runs; only WHERE an
    # edge ends up (on the outline, or genuinely interior) decides its
    # wall_type/thickness.
    for i, edge in enumerate(edges):
        ax, ay = edge["a"]
        bx, by = edge["b"]
        length = math.dist((ax, ay), (bx, by))
        gaps = []
        cursor = 0.0
        for t0, t1 in sorted(covered[i]):
            if t0 - cursor > 300:
                gaps.append((cursor, t0))
            cursor = max(cursor, t1)
        if length - cursor > 300:
            gaps.append((cursor, length))
        if not gaps:
            continue
        ux, uy = (bx - ax) / length, (by - ay) / length
        nx, ny = -uy, ux
        # Push away from the room, so the wall sits outside its inner face.
        inward = (edge["centroid"][0] - ax) * nx + (edge["centroid"][1] - ay) * ny
        shift = (DEFAULT_WALL_THICKNESS_MM / 2.0) * (-1 if inward > 0 else 1)
        for t0, t1 in gaps:
            mid = ((ax + ux * (t0 + t1) / 2.0), (ay + uy * (t0 + t1) / 2.0))
            # Already on the drawn outline -- _outline_to_walls already
            # built the real exterior wall here, this uncovered stretch is
            # just that same boundary's inner-face edge. Skip it, don't
            # double it up.
            if outer_outline_mm and _distance_to_polygon(mid, outer_outline_mm) < (
                    outline_edge_tolerance_mm or DEFAULT_WALL_THICKNESS_MM):
                continue
            on_outline = not outer_outline_mm
            walls.append({
                "id": f"wall-{len(walls)}",
                "start_mm": [round(ax + ux * t0 + nx * shift, 1),
                             round(ay + uy * t0 + ny * shift, 1)],
                "end_mm": [round(ax + ux * t1 + nx * shift, 1),
                           round(ay + uy * t1 + ny * shift, 1)],
                "thickness_mm": (DEFAULT_WALL_THICKNESS_MM if on_outline
                                else DEFAULT_PARTITION_THICKNESS_MM),
                "wall_type": "exterior" if on_outline else "interior",
                "rooms": [edge["room"]],
            })

    walls.extend(extra_walls or [])

    # Reihenfolge zaehlt (plans/interior-wall-geometry-v1.md):
    #   1. Innenwaende geradeziehen -- VOR dem Merge, damit eine Trennwand,
    #      die als ein gerades und ein schiefes Stueck herauskam, danach auf
    #      einer Linie liegt und von selbst wieder EINE Wand wird. 029s
    #      Obergeschoss: wall-3 (y=6187.9) und wall-4 (9.42 Grad schief)
    #      gehoerten demselben Raumpaar und blieben getrennt, weil der
    #      Linien-Offset der schiefen Wand zu weit weg lag.
    #   2. Merge.
    #   3. Aussenecken schliessen (bestehend).
    #   4. Innen-T-Stoesse schliessen -- ZULETZT, damit sie auf die
    #      endgueltigen Aussenwand-Ecken zielen und nicht auf die, die
    #      Schritt 3 gleich noch verschiebt.
    #   2b. Doppelwaende zusammenfassen -- direkt nach dem Merge, damit die
    #       Eckenschliessung und die T-Stoesse schon auf die EINE Wand
    #       zielen und nicht auf zwei, die sich durchdringen.
    return _close_interior_t_junctions(
        _close_exterior_corners(
            _merge_overlapping_parallel_walls(
                _merge_collinear_walls(
                    _orthogonalize_interior_walls(walls)), rooms)))


def point_in_polygon(point, polygon, tolerance_mm=300):
    """Inside the polygon, or within tolerance of its boundary — openings sit
    ON a room's edge, so their midpoint can land just outside the polygon."""
    x, y = point
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    if inside:
        return True
    for i in range(len(polygon)):
        sx, sy = polygon[i]
        ex, ey = polygon[(i + 1) % len(polygon)]
        length_squared = (ex - sx) ** 2 + (ey - sy) ** 2
        if not length_squared:
            continue
        t = max(0.0, min(1.0, ((x - sx) * (ex - sx) + (y - sy) * (ey - sy)) / length_squared))
        if math.dist(point, (sx + t * (ex - sx), sy + t * (ey - sy))) <= tolerance_mm:
            return True
    return False


def nearest_wall(walls, a, b):
    """The wall an opening belongs to: closest by midpoint, and roughly parallel.

    Angle matters. A door drawn across a corner sits near two walls, and
    attaching it to the perpendicular one puts it through the return.
    """
    midpoint = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    angle = math.atan2(b[1] - a[1], b[0] - a[0])
    best = None
    for wall in walls:
        sx, sy = wall["start_mm"]
        ex, ey = wall["end_mm"]
        wall_angle = math.atan2(ey - sy, ex - sx)
        difference = abs((angle - wall_angle + math.pi / 2) % math.pi - math.pi / 2)
        if difference > math.radians(25):
            continue
        length_squared = (ex - sx) ** 2 + (ey - sy) ** 2
        if not length_squared:
            continue
        t = ((midpoint[0] - sx) * (ex - sx) + (midpoint[1] - sy) * (ey - sy)) / length_squared
        t = max(0.0, min(1.0, t))
        distance = math.dist(midpoint, (sx + t * (ex - sx), sy + t * (ey - sy)))
        if best is None or distance < best[0]:
            best = (distance, wall, t)
    return best


def door_pose_in_wall_frame(door_a, door_b, wall_start, wall_end,
                            hinge_side, swing_side):
    """Translate a door's annotated hinge/swing from the DOOR's own frame
    into its host WALL's frame.

    The annotator's swing preview (drawDoorSwing() in annotate.js) reads
    hinge_side ("start"/"end") and swing_side ("first_room"/"second_room")
    relative to the door element's own two drawn points -- that is what the
    user sees and chooses. add_door_leaf() reads the identical strings
    relative to the matched wall's start_mm -> end_mm order, a direction
    decided incidentally by which room's edge produced that wall segment.
    The two frames agree only when the door's point order happens to run
    the same way as its wall's; when opposite, every hand-set value renders
    backwards while previewing correctly (confirmed on bungalow_039,
    2026-08-22: exactly the 3 doors with opposite order -- Kueche,
    Buero/Gast, Eingang -- were the 3 Rainer named as wrong).

    SECOND BUG, found 2026-08-22 evening after Rainer reported "doors are
    still wrong" post-fix: the annotator's swing side is NOT defined
    relative to the door's raw point order -- drawDoorSwing() rotates the
    HINGE->FREE-END direction by +/-90deg, and that direction REVERSES when
    hinge_side is "end". The first fix flipped the two labels
    independently on point-order mismatch, which is only equivalent when
    hinge_side is "start": for every hinge="end" door the render stayed
    opposite to the preview (bungalow_039's Schlafzimmertuer, the one door
    with hinge="end" -- exactly the door still reported wrong). So no
    label-flipping algebra any more: compute the physical side the
    annotator actually drew, then express it in the wall's frame.

    Annotator geometry, mapped to y-up mm (canvas y is down, so its
    +90deg becomes -90deg here): the leaf opens to the side of
    Rot(sigma*90deg) applied to hinge->free, sigma=+1 for "first_room",
    -1 for "second_room". Renderer geometry (add_door_leaf): "first_room"
    means the +normal side, normal = Rot(+90deg) of wall start->end;
    hinge "start" means the jamb nearer the wall's start.

    Pure on purpose (points in, labels out; no wall matching, no element
    dicts): wall matching and pose normalization are separate failure
    domains, and this one is covered by metamorphic tests -- see
    plans/pose-contract-slice-1-v1.md. All four points must be in the SAME
    y-up mm space. Unset labels pass through untouched.
    """
    if not (hinge_side or swing_side):
        return hinge_side, swing_side
    wx, wy = wall_end[0] - wall_start[0], wall_end[1] - wall_start[1]
    hinge_pt = door_b if hinge_side == "end" else door_a
    free_pt = door_a if hinge_side == "end" else door_b
    fx, fy = free_pt[0] - hinge_pt[0], free_pt[1] - hinge_pt[1]

    out_hinge = hinge_side
    if hinge_side in ("start", "end"):
        out_hinge = "start" if (fx * wx + fy * wy) > 0 else "end"

    out_swing = swing_side
    if swing_side in ("first_room", "second_room"):
        sigma = 1.0 if swing_side == "first_room" else -1.0
        # The side the annotator drew: Rot(sigma*90deg) of hinge->free.
        vx, vy = -sigma * fy, sigma * fx
        # Renderer's first_room side: Rot(+90deg) of the wall = (-wy, wx).
        out_swing = "first_room" if (vx * -wy + vy * wx) > 0 else "second_room"
    return out_hinge, out_swing


def build_floor_walls_and_openings(rooms, excluded_polygons, annotations, level, frame, ground_level):
    """Walls and door/window/opening annotation elements matched onto them,
    for one floor.

    Extracted so geometry_only() (the furniture editor's plan view) and the
    full render-plan build share the ONE implementation instead of growing a
    second one that quietly drifts from it -- the exact failure class this
    file's own coordinate-system comments already warn about elsewhere.

    Returns (walls, openings, unmatched, skipped_excluded) in RAW form:
    build_walls()'s own keys (start_mm/end_mm/thickness_mm) and width_mm on
    openings. Callers translate to whatever schema their consumer expects.
    """
    # Rainer, 2026-09-19: "how else can i add notches and also get the sizes
    # and floor alignemtnt correct" -- was `if is_ground_level`, ground
    # only, because the legacy single outline could only ever be correctly
    # registered onto ONE floor. outline_points_for_level() now applies to
    # ANY level that has its own per-floor entry (a real notch is specific
    # to its floor); a legacy project with no outer_outlines key falls back
    # to that exact old ground-only behavior inside the helper itself.
    # The parameter used to be `is_ground_level` (bool). Callers that still
    # pass one keep working: True means this level IS the ground floor.
    if ground_level is True:
        ground_level = level
    elif ground_level is False:
        ground_level = None
    outer_outline_mm = None
    outline_points = outline_points_for_level(annotations, level, ground_level)
    if outline_points:
        if hasattr(frame, "outline_polygon"):
            outer_outline_mm = frame.outline_polygon(outline_points)
        else:
            outer_outline_mm = [frame.point(p) for p in outline_points]
    # A per-floor outline traces the OUTER face, while an upper storey's rooms
    # are drawn to the INNER face -- a full wall thickness (240 mm) inside it,
    # exactly on the default "already on the outline" cut-off. Hand-drawn
    # rooms scatter +-150 mm around that, so the edge of a room that IS the
    # exterior wall's inner face sometimes counted as a stray interior wall
    # and swallowed the real exterior wall (twostorey_050 upperfloor: 0
    # exterior walls). Only projects with per-floor outlines get the wider
    # cut-off; every other house builds exactly as before.
    wider = (OUTLINE_ROOM_EDGE_TOLERANCE_MM
             if annotations.get("outer_outlines") is not None else None)
    walls = build_walls(rooms, outer_outline_mm,
                        annotations.get("outer_outline_reference")
                        or DEFAULT_OUTLINE_REFERENCE,
                        outline_edge_tolerance_mm=wider,
                        extra_walls=partition_walls(annotations, level, frame))

    openings = []
    unmatched = []
    skipped_excluded = []
    for element in annotations.get("elements", []):
        if element.get("floor_level") != level:
            continue
        kind = element.get("type")
        if kind not in ("door", "window", "opening"):
            continue
        points = element.get("points") or []
        if len(points) < 2:
            continue
        a, b = frame.point(points[0]), frame.point(points[1])
        match = nearest_wall(walls, a, b)
        if match is None or match[0] > 1200:
            midpoint = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            host = next((label for label, poly in excluded_polygons
                         if point_in_polygon(midpoint, poly)), None)
            if host:
                skipped_excluded.append((element.get("id"), host))
            else:
                unmatched.append(element.get("id"))
            continue
        _, wall, t = match

        # Window type is annotated now, so the sill comes from the plan
        # instead of a blanket 900 mm. A bodentiefes Fenster starts at the
        # floor; a Brüstungsfenster does not.
        window_type = element.get("window_type")
        if kind == "window":
            sill = element.get("sill_height_mm")
            if sill is None:
                sill = 0 if window_type == "bodentief" else 900
            height = 2100 - sill if window_type == "bodentief" else 1350
        else:
            sill, height = 0, 2010

        # Normalized into the wall's frame here, once, so every downstream
        # reader gets wall-relative values matching what the annotator's
        # preview showed the user. The why lives on the function itself.
        swing_side = element.get("swing_side")
        hinge_side = element.get("hinge_side")
        if kind == "door":
            hinge_side, swing_side = door_pose_in_wall_frame(
                a, b, wall["start_mm"], wall["end_mm"], hinge_side, swing_side)

        openings.append({
            "id": element.get("id") or f"opening-{len(openings)}",
            "wall_id": wall["id"],
            "opening_type": kind,
            "position": round(t, 4),
            # Eine im Annotator gewaehlte Normbreite schlaegt die gezeichnete
            # Strichlaenge (Rainer, 2026-08-26: Auswahl 68/80/101/131/151/171/
            # 300 cm). Ohne Auswahl bleibt es bei der Zeichnung, damit sich an
            # bestehenden Annotationen nichts aendert. Die Oeffnung sitzt
            # weiter auf demselben `position`, wird also symmetrisch breiter.
            "width_mm": (float(element["width_mm"]) if element.get("width_mm")
                         else round(math.dist(a, b), 1)),
            "height_mm": height,
            "sill_height_mm": sill,
            "traversable": kind != "window",
            "window_type": window_type,
            "panes": element.get("panes"),
            "swing_side": swing_side,
            "hinge_side": hinge_side,
            "role": element.get("role"),
            "connects": wall.get("rooms", []),
        })
    return walls, openings, unmatched, skipped_excluded


def load_model_picks(style="modern"):
    """Resolved Hub models for each symbol key, with their scale divisor.

    Types come from the assets' own names and sizes were verified by
    scripts/resolve-hub-scales.py, so nothing here is inferred from a
    measurement — which is what went wrong every time today. The old
    size-match shortlist is deliberately NOT consulted: it ranked models
    against a library whose measurements the FBX conversion had corrupted.
    """
    if not os.path.exists(PICKS):
        return {}
    raw = load_json(PICKS).get("picks", {})
    resolved = {}
    for key, entry in raw.items():
        if not isinstance(entry, dict):
            continue
        chosen = entry.get(style) or entry.get("modern")
        if not isinstance(chosen, dict) or not chosen.get("path"):
            continue
        resolved[key] = {
            "path": chosen["path"],
            "divisor": chosen.get("divisor", 1.0),
            "size_mm": chosen.get("size_mm"),
            "label": chosen.get("label"),
            "source": "hub_resolved",
        }
    return resolved


GENERATED_CATALOG = os.path.join(REPO, "data", "furniture-assets", "full-catalog")

# Symbols whose spec type does not name the generated model that suits them.
# `garderobe` carries type "wardrobe" so the renderer finishes it like one,
# but the catalogue has a purpose-built coat_rack.
GENERATED_TYPE_OVERRIDE = {
    "garderobe": "coat_rack",
    # `lowboard` carries type "sideboard"; the catalogue calls the same piece
    # tv_unit. Same furniture, different word.
    "lowboard": "tv_unit",
    # Der Hub hat nur EINEN Doppelwaschtisch, und der ist 2269 mm breit --
    # fast das Doppelte unseres 1200er Symbols. Die Verzerrungssperre wirft
    # ihn darum zu Recht weg. Der erzeugte Katalog hat einen, der sich auf
    # jedes Mass normalisiert.
    "doppelwaschtisch": "bathroom_vanity",
}

# Which generated types are actually allowed to replace a box, checked by
# rendering them and LOOKING, not by trusting that a model beats a box.
#
# coat_rack: clear win. The 900x320x1900 box became a rack with hooks and a
# rail, and it reads as one at delivery distance.
#
# wardrobe: REGRESSION, measured 2026-09-03 on
# german_catalog_review_bungalow_3_4_2_b_120. The procedural box carries
# gap-cut children (kleiderschrank-17-gap-*) that draw a door seam; the
# generated model replaced it with a featureless slab -- the seam disappeared
# and nothing came back in its place. The model file is 519 KB, so the detail
# exists; the doors are simply not facing the camera. Its front axis is
# undeclared, which is the general gap: an imported asset carries no reliable
# statement of which local axis is its front. Until that is declared per
# asset, a generated wardrobe is worse than the box it replaces.
# wardrobe wieder aufgenommen 2026-09-03, nachdem derive_front_axis im
# Renderer die Vorderseite misst statt sie zu raten. Die Sperre bleibt als
# Mechanismus bestehen: ein Typ kommt hier erst rein, wenn sein Ergebnis
# angesehen wurde.
GENERATED_TYPES_VERIFIED = {"coat_rack", "wardrobe", "tv_unit", "bathroom_vanity"}


# Ab welchem Verhaeltnis Breite zu Tiefe ein Symbol keine Einzelmoebel mehr
# ist, sondern eine Zeile.
#
# Gemessen 2026-09-03 am Lowboard: 3500 x 300 mm, Verhaeltnis 11,7. Das
# erzeugte tv_unit wurde darauf gestreckt und verlor dabei jede Tuerfuge --
# aus fuenf Feldern wurde eine glatte 3,5-Meter-Planke, sichtbar schlechter
# als der prozedurale Quader mit seinen Fugenschnitten. Zum Vergleich:
# Kleiderschrank 1050 x 600 = 1,75 und Garderobe 900 x 320 = 2,8, beide
# gewonnen.
#
# Ein Katalogmodell ist EIN Moebelstueck. Ein langes Symbol ist eine Zeile aus
# mehreren, und die muss modular gebaut werden -- ein einzelnes Modell darauf
# zu ziehen ist immer falsch, egal wie gut das Modell ist. Der Wert trennt die
# gemessenen Faelle mit Abstand; er ist keine feine Justierung.
GENERATED_MAX_ASPECT = 4.0


def generated_catalog_model(key, spec_type, style, footprint=None):
    """A generated .glb for this symbol, or None.

    Second link in the model chain: Hub model if it fits -> generated
    catalogue model -> procedural box. It exists because a size-based search
    of the Hub has almost nothing to search. Measured 2026-09-03:
    tmp/hub-models-resolved.json holds 93 models and exactly ONE of type
    `wardrobe` (White Wardrobe, 3082 mm). All three Kleiderschraenke in
    german_catalog_review_bungalow_3_4_2_b_120 therefore got that one model;
    it fits the 3700 mm symbol and misses the two 1050 mm symbols by 2.7x, so
    the distortion gate correctly dropped it and built plain boxes.

    The generated catalogue is the other library, unused by this path until
    now: 16 types, each in a modern and a classic variant, authored per type
    rather than at one fixed real-world size. They carry no verified size on
    purpose -- `size_mm` stays None so the renderer normalises them to the
    annotated symbol instead of fitting them to a nominal size they do not
    have.
    """
    name = GENERATED_TYPE_OVERRIDE.get(key, spec_type)
    if name not in GENERATED_TYPES_VERIFIED:
        return None
    sides = sorted([(footprint or {}).get("width_mm") or 0,
                    (footprint or {}).get("depth_mm") or 0], reverse=True)
    if sides[1] > 0 and sides[0] / sides[1] > GENERATED_MAX_ASPECT:
        return None
    for want in (style, "modern"):
        path = os.path.join(GENERATED_CATALOG, "%s__%s.glb" % (name, want))
        if os.path.exists(path):
            return {
                "path": path,
                "divisor": 1.0,
                "size_mm": None,
                "label": "%s (%s, generated)" % (name, want),
                "source": "generated_catalog",
            }
    return None


# How far a model's real footprint may sit from the annotated one before a box
# serves better. A real model squeezed to a third of its size looks worse than
# a plain box at the right size — the stretched-sofa mistake in reverse.
#
# Crude on purpose. Nobody measures a marketing render; it only has to avoid
# looking obviously wrong.
# 0.45 was slightly too tight: a 400 mm basin against a 600 mm symbol misses by
# 49 % and got replaced by a box, when the real basin would have looked better.
# Nobody measures a marketing render, so err towards the real model.
FOOTPRINT_TOLERANCE = 0.6


def footprint_mismatch(model, footprint):
    """True when the model is too far off the drawn footprint to use."""
    size = model.get("size_mm")
    if not size or not footprint.get("width_mm"):
        return False
    want = sorted([footprint["width_mm"], footprint["depth_mm"]], reverse=True)
    got = sorted(size[:2], reverse=True)
    for a, b in zip(got, want):
        if b <= 0:
            continue
        if abs(a - b) / float(b) > FOOTPRINT_TOLERANCE:
            return True
    return False


def geometry_only(project_id, out_path):
    """The room polygons, walls and openings of this plan, in this plan's
    millimetres.

    The furniture editor needs to place things in the space the renderer
    actually builds. Re-deriving that space in TypeScript would mean a second
    implementation of Frame, image_size, floor_scale and the room exclusions —
    and a third coordinate system the first time one of them drifted. So the
    one implementation that already exists answers the question.

    Walls and openings come from the SAME build_floor_walls_and_openings()
    the full render-plan build uses, so a wall the renderer builds is a wall
    the furniture editor shows -- not a second, independently-derived guess.
    Their field names are translated to the short form the editor's SVG
    reads (start/end/thickness, width) -- the annotation-pipeline's own
    _mm-suffixed names are a different schema used only inside this script.
    """
    project_dir = os.path.join(SIMPLIFIER, "projects", project_id)
    annotations = load_annotations(project_dir)
    pixel_width, pixel_height = image_size(project_dir, annotations)
    floor_scale = annotations.get("floor_scale") or {}

    floors = []
    levels = sorted({item.get("floor_level") for item in annotations.get("annotations", [])
                     if item.get("floor_level")})
    ground_level = "groundfloor" if "groundfloor" in levels else (levels[0] if levels else None)
    for level in levels:
        scale = floor_scale.get(level)
        if not scale:
            raise SystemExit(f"{level} has no calibrated scale — set it in the Simplifier first")
        # Obergeschosse werden ueber die Ausrichtungsmarken auf das
        # Erdgeschoss registriert (RegisteredFrame); das Erdgeschoss selbst
        # bekommt den gewoehnlichen Frame.
        frame = frame_for_level(annotations, level, ground_level, pixel_width, pixel_height)
        rooms = []
        excluded_polygons = []
        for item in annotations.get("annotations", []):
            if item.get("floor_level") != level or len(item.get("points") or []) < 3:
                continue
            points = item["points"]
            if excluded(item.get("label")):
                excluded_polygons.append((item.get("label"), [frame.point(p) for p in points]))
                continue
            polygon_mm = [frame.point(point) for point in points]
            rooms.append({
                "id": item.get("id") or f"room-{len(rooms)}",
                "name": item.get("label"),
                "kind": room_kind(item.get("label")),
                "polygon_mm": polygon_mm,
                "area_m2": round(polygon_area(polygon_mm) / 1e6, 2),
            })
        walls, openings, _unmatched, _skipped_excluded = build_floor_walls_and_openings(
            rooms, excluded_polygons, annotations, level, frame, ground_level)
        # Frame rechnet y nach OBEN, der Bildschirm nach UNTEN. Gespiegelt
        # wird HIER, an der einen Stelle, an der die Geometrie den Renderer
        # verlaesst -- der Editor zeichnet dann roh und der Grundriss steht
        # wie im Annotator (Rainer, 2026-08-21: "why is the floorplan
        # rotated"). Zurueckgespiegelt wird beim Lesen der Moebel in
        # workbench_furniture, mit derselben Ausdehnung (level_room_extent).
        # Waende spiegeln sich mit denselben lo/hi wie die Raeume -- sonst
        # stuenden sie versetzt zu den (schon gespiegelten) Raumpolygonen.
        # Die Treppe kommt aus DERSELBEN Quelle wie der Render: der
        # GEZEICHNETEN stairs-Annotation (annotation_stair_core). Der
        # Moebel-Editor zeigte stattdessen shared_stair_core aus dem
        # Korrektur-Dokument -- GENERIERTE Geometrie mit eigener, anders
        # grosser, anders platzierter Treppe in einem anders normierten
        # Gebaeude (onehalfstorey_029, 2026-08-22: Annotator-Treppe 1599x1011
        # rechts in der Diele, Editor zeigte 2245x1584 in Gebaeudemitte;
        # Rainer: "the annotator has completely different stairs then the
        # Möbel"). Raeume aus der Zeichnung + Treppe aus dem Generator in
        # EINER Ansicht ist genau die Fehlerklasse dieses Tages.
        #
        # Codex-Review, 2026-09-18: annotation_stair_core() liest IMMER die
        # GROUNDFLOOR-eigenen Punkte (floor_level == ground_level), egal
        # welches `frame` uebergeben wird -- aber bis eben ging hier fuer ein
        # Obergeschoss dessen RegisteredFrame rein, nicht der Ground-Frame.
        # Ergebnis: Ground-Punkte durch die (anisotrope) Registrierungs-
        # Affinitaet gerechnet statt durch die Frame, die sie tatsaechlich
        # kalibriert hat -- gemessen 900mm (Bau, shared_stair_core) vs.
        # 1049mm (_047) / 1022mm (_049) in genau dieser Funktion. Die
        # Quelle bleibt jetzt IMMER der Ground-Frame + ground_level, exakt
        # wie der volle Bau am Ende dieser Datei ("shared_stair_core");
        # nur der anschliessende y-Flip bleibt pro Geschoss (unten), damit
        # dieselbe reale Treppe auf jedem Stockwerk an seiner eigenen
        # Raum-Ausdehnung gespiegelt korrekt angezeigt wird.
        ground_frame = frame if level == ground_level else Frame(
            floor_scale.get(ground_level) or 1.0, pixel_width, pixel_height)
        stair = annotation_stair_core(annotations, ground_frame, ground_level)
        # The furniture editor's own reference-photo overlay (Rainer,
        # 2026-09-17: "why are the uploaded floorplans not visible on the
        # möble tab", then "scale is off but it is all from the same data
        # how can it be off") -- it was fitting the photo to the ROOMS'
        # bounding box, which is only ever an approximation (rooms don't
        # reach the image edge, and a stretched fit ignores this floor's
        # own width/height ratio entirely). The real answer is the same
        # one every OTHER shape on this floor already gets: run the
        # image's own four corners through this SAME `frame`, so they
        # land in exactly the coordinate space the rooms/walls/stair
        # above are already in.
        image_corners_mm = [
            frame.point({"x": 0, "y": 0}), frame.point({"x": 1, "y": 0}),
            frame.point({"x": 1, "y": 1}), frame.point({"x": 0, "y": 1}),
        ]
        # Codex architecture review, 2026-09-18 ("i think there are many
        # flaws especially in the scaling between the different tabs i
        # think this has to be standardised and simplified"): this used to
        # flip against `lo, hi` computed FRESH from THIS geometry_only()
        # call's own room polygons -- a MOVING target. `workbench_furniture()`
        # (the reader, at furniture-read time) recomputed its OWN lo/hi the
        # same way, independently, via `level_room_extent()`. Two
        # independent recomputations of "the same" extent, from two
        # different call sites at two different times, is exactly the class
        # of bug that reflected twostorey_047's entire furniture set TWICE:
        # if a room is added/resized/excluded differently between the two
        # calls -- or, as measured on `_047`, if the SAME data is simply
        # re-saved through a code path that recomputes and reflips -- the
        # two flips stop being exact inverses of each other with no error,
        # just wrong furniture.
        #
        # `frame.height_mm` is not read from the rooms at all: it is
        # `scale_metres_per_x_unit * 1000 * (pixel_height/pixel_width)`,
        # fixed the moment the floor's scale and image are set and IDENTICAL
        # for every RegisteredFrame on this building (RegisteredFrame.__init__
        # copies `ground_frame.height_mm` verbatim). Flipping against it
        # instead of a room-derived lo/hi makes the flip a stateless,
        # per-floor CONSTANT that can never drift out of sync with itself --
        # redrawing, resizing or excluding a room no longer changes the
        # basis furniture (or anything else) is measured against.
        flip = frame.height_mm
        for r in rooms:
            r["polygon_mm"] = [[q[0], round(flip - q[1], 1)]
                               for q in r["polygon_mm"]]
        for w in walls:
            w["start_mm"] = [w["start_mm"][0], round(flip - w["start_mm"][1], 1)]
            w["end_mm"] = [w["end_mm"][0], round(flip - w["end_mm"][1], 1)]
        if stair:
            stair["polygon_mm"] = [[q[0], round(flip - q[1], 1)]
                                   for q in stair["polygon_mm"]]
            stair["path_mm"] = [[q[0], round(flip - q[1], 1)]
                                for q in stair["path_mm"]]
        image_corners_mm = [[q[0], round(flip - q[1], 1)] for q in image_corners_mm]
        # Kurzform, wie sie der Korrektur-Editor selbst schreibt
        # (correction-editor.mjs) -- dieselbe SVG-Zeichnung liest beide.
        walls_out = [{
            "id": w["id"], "start": w["start_mm"], "end": w["end_mm"],
            "thickness": w["thickness_mm"],
        } for w in walls]
        openings_out = [{
            "id": o["id"], "wall_id": o["wall_id"], "opening_type": o["opening_type"],
            "position": o["position"], "width": o["width_mm"], "role": o["role"],
        } for o in openings]
        floors.append({
            "floor_level": level,
            "width_mm": round(frame.width_mm, 1),
            "height_mm": round(frame.height_mm, 1),
            "rooms": rooms,
            "walls": walls_out,
            "openings": openings_out,
            "stair": ({"polygon": stair["polygon_mm"], "path": stair["path_mm"]}
                      if stair else None),
            "image_corners_mm": image_corners_mm,
            # Rainer, 2026-09-18, twostorey_047: 21 of 21 furniture items
            # found reflected into the wrong room. Root cause (Codex):
            # `saveFurniture()` recomputes this floor's identity FRESH at
            # save time and stamps whatever is current -- if the annotation
            # changed between the Moebel tab loading this geometry and the
            # user clicking Save, the save re-stamps the NEW identity onto
            # coordinates placed against the OLD layout, so the existing
            # staleness check (workbench_furniture(), which compares this
            # SAME level_geometry_identity()) can never catch it again.
            # Emitting it here lets the client capture the identity it is
            # ACTUALLY DISPLAYING and send that back on save, so the API can
            # refuse a save whose displayed geometry has since moved on
            # instead of silently re-stamping it as fresh.
            "geometry_identity": level_geometry_identity(project_id, level),
        })

    payload = {
        "project_id": project_id,
        "coordinate_space": RENDER_GEOMETRY_SPACE,
        "floors": floors,
    }
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    print(f"[geometry] wrote {out_path} ({len(floors)} floor(s))")


def approved_correction_revision(path):
    """An APPROVED correction revision, or a hard stop.

    Step 2 of plans/renderer-switch-execution-order.md: the renderer's source
    becomes explicit. `save_draft` is durable but not approved, and the
    corrections GET endpoint hands back the lexically newest revision whatever
    its status — so a rejected revision saved after an approved one would
    otherwise become the geometry a render is built from. AGENTS.md: nothing
    generates geometry without an approved corrected reference.
    """
    if not os.path.exists(path):
        raise SystemExit(f"{path}: no such correction revision")
    document = load_json(path)
    status = document.get("status") or document.get("approval_status")
    if status != "approved":
        raise SystemExit(
            f"{path}: revision status is {status!r}, not 'approved' — refusing to "
            f"render from it")
    return document



def corrected_placements(reference, floor_id, models):
    """Furniture placed in the workbench, for the corrected-document plan.

    Every stamp goes through the SAME hub-model resolution as the annotation
    path. Emitting geometry without `mesh_path`/`scale_divisor` produced a plan
    that looked complete and verified clean, while Blender reported
    "furniture 0 instances from 0 meshes" and rendered empty rooms — the
    failure is silent because a name with no model behind it is simply skipped.

    POSE IS TAKEN AS-IS from workbench_furniture(), which already converts
    editor space (y down) into render space: y-flipped positions/points,
    negated rotation, mirrored passed through uninverted. This function
    used to convert AGAIN (flip the position with the correction document's
    own extent, negate the rotation a second time, invert mirrored) — two
    flips and two negations cancel, so the --corrected path delivered poses
    still in the EDITOR's convention, plus a positional offset because the
    two flips used different extents. Found 2026-08-22, confirmed by Codex
    review, validated against Rainer's contact sheet; the regression test
    is test_corrected_path_agrees_with_the_workbench_path. Do not add a
    transform back here: workbench_furniture() is the ONE conversion.
    """
    symbols = workbench_furniture(reference, floor_id)
    if not symbols:
        return [], []
    placements, skipped = [], []
    for symbol in symbols:
        key = symbol.get("symbol")
        spec = SYMBOL_3D.get(key)
        if not spec:
            skipped.append({"symbol": key, "reason": "no 3D specification"})
            continue
        if symbol.get("points_mm"):
            points = symbol["points_mm"]
            # A run or rectangle whose points coincide has no size. It reaches
            # Blender as a degenerate mesh and shows up as a spike through
            # whatever stands nearby (Rainer, 2026-08-17: "something is sticking
            # through the dining table"). Two clicks on one spot is easy to do.
            span_x = max(pt[0] for pt in points) - min(pt[0] for pt in points)
            span_y = max(pt[1] for pt in points) - min(pt[1] for pt in points)
            if max(span_x, span_y) < 50:
                skipped.append({"symbol": key, "reason": "drawn with no size — re-draw it"})
                continue
            placements.append({
                "asset_id": key,
                "type": spec["type"],
                "build": "rect" if key in RECT_BUILD else "path",
                "points_mm": points,
                "depth_mm": symbol.get("depth_mm") or spec.get("depth", 600),
                "height_mm": spec["height"],
                "mesh_path": None,
                "model_source": "procedural",
                "scale_divisor": 1.0,
                "source": "workbench_furniture_corrected",
            })
            continue
        if not symbol.get("position_mm"):
            skipped.append({"symbol": key, "reason": "no position"})
            continue
        footprint = symbol.get("footprint_mm") or {}
        model = models.get(key)
        build = spec.get("build")
        if not model and not build:
            build = "box"
        # A footprint set by dragging the symbol's corners is a measurement of
        # THIS plan and outranks the model's nominal size, so the mismatch gate
        # must not fire against it — same rule as the annotation path.
        measured_here = bool(footprint.get("width_mm"))
        mismatch = (bool(model) and not measured_here
                    and footprint_mismatch(model, footprint))
        if mismatch and not build:
            build = "box"

        placements.append({
            "asset_id": key,
            "type": spec["type"],
            "mesh_path": model["path"] if model and not mismatch else None,
            "model_source": (model["source"] if model and not mismatch
                             else "procedural"),
            "model_label": model.get("label") if model else None,
            "scale_divisor": model.get("divisor", 1.0) if model else 1.0,
            "verified_size_mm": model.get("size_mm") if model else None,
            "size_mismatch": mismatch,
            "footprint_measured": measured_here,
            "build": build,
            # Already render-space (see the docstring): workbench_furniture()
            # performed the one editor->render conversion. The reflection
            # reasoning that used to live here ("the mirror flag inverts
            # too", 2026-08-17) was correct for a path that received RAW
            # editor coordinates — this path does not, and applying it here
            # double-transformed the pose.
            "position_mm": symbol["position_mm"],
            "rotation_deg": int(symbol.get("rotation_deg", 0)) % 360,
            "mirrored": bool(symbol.get("mirrored")),
            "target_bbox_mm": {
                "width_mm": footprint.get("width_mm"),
                "depth_mm": footprint.get("depth_mm"),
                "height_mm": spec["height"],
            },
            "height_mm": spec.get("mount", 0),
            # Same rule as the annotation path (see the long note at the other
            # placement site): `build` normally means "procedural, no mesh
            # imported", so claiming preserve_materials there would make the
            # plan lie. The sink is the one exception the renderer honours --
            # it imports its real model despite carrying build="hob".
            #
            # This branch was MISSING that exception while the annotation
            # branch had it, so the corrected path shipped
            # preserve_materials=false for `spuele`. The renderer then sent a
            # real 1000x500x506 library sink through normalise_to_bbox (the
            # Tripo axis-reorder path, which sorts axes by extent): the
            # model's 506mm height was matched to the 600mm target DEPTH and
            # its 500mm depth to the 200mm target HEIGHT, tipping the sink
            # onto its back and squashing it into a 600x600x200 slab, with
            # its materials cleared. That is the "Spuele sits proud of the
            # worktop" defect -- not a mounting-height bug.
            "preserve_materials": bool(model) and not mismatch and (
                not build or spec["type"] == "sink"),
            "source": "workbench_furniture_corrected",
        })
    return placements, skipped


def annotation_roof(project_id, key):
    """Roof choice from the annotation package. The corrected document carries
    geometry, not style, so the Dachform still lives with the annotations."""
    path = os.path.join(SIMPLIFIER, "projects", project_id, "annotations.json")
    if not os.path.exists(path):
        return None
    annotations = load_json(path)
    if key in ("modern", "classic"):
        return annotations.get(f"roof_type_{key}")
    return annotations.get("roof_overhang_mm")


def annotation_camera_style(project_id):
    """Interior-dollhouse camera choice ("classic" ortho or "realistic"
    perspective), set per-project in the Annotator. Lives with the
    annotations, same as the Dachform above -- it never travels into the
    corrected geometry document either."""
    path = os.path.join(SIMPLIFIER, "projects", project_id, "annotations.json")
    if not os.path.exists(path):
        return "realistic"
    return load_json(path).get("camera_style") or "realistic"


# Der Massstab und die Dachform stehen bei 119 Haeusern NICHT in der
# annotations.json, sondern in gebaeudemass.json daneben (load_annotations).
# Codex, 2026-08-20: "Massstab, Seitenverhaeltnis oder Dachform koennen
# geaendert werden, waehrend eine geometrisch alte Lieferung weiterhin als
# aktuell gilt." Genau so war es: der Provenance-Hash umfasste nur die
# Zeichnung. Wer danach 12,0 x 9,5 m in 11,4 x 8,2 m korrigierte, bekam ein
# Haus in alter Groesse mit gueltigem Zertifikat.
#
# Der Eingangshash umfasst deshalb BEIDE Dateien. Dieselben drei Zeilen stehen
# in scripts/batch-build.py (annotation_state) und in
# scripts/render-furnished-dollhouse.py (_refuse_stale_plan) -- die drei
# muessen zusammen geaendert werden, sonst baut die eine Seite, was die andere
# fuer alt haelt.
def sidecar_hash(project_dir):
    """sha256 der gebaeudemass.json, oder None wenn keine daneben liegt."""
    path = os.path.join(project_dir, "gebaeudemass.json")
    try:
        with open(path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()
    except OSError:
        return None


def input_hash(annotation_hash, side_hash):
    if not annotation_hash:
        return None
    return hashlib.sha256(("%s:%s" % (annotation_hash, side_hash or "-"))
                          .encode("utf-8")).hexdigest()


def source_provenance(project_id):
    """The annotation this plan is being compiled from, by hash.

    Half of the fail-closed boundary Codex asked for: the compiler stamps what
    it read, the renderer refuses anything that no longer matches. A stale plan
    then fails loudly instead of quietly rendering last week's house.
    """
    # Hash the annotation THIS COMPILER READ, not the one the annotator says it
    # wrote. Codex, 2026-08-19: "source_provenance() copies a hash from
    # source-state.json rather than hashing the actual annotations.json loaded
    # by the compiler ... a TOCTOU bug disguised as provenance." The two files
    # can diverge: the hook swallows its own failures, the writes are separate,
    # and a hand-edited annotation bypasses the hook entirely.
    project_dir = os.path.join(SIMPLIFIER, "projects", project_id)
    annotation_file = os.path.join(project_dir, "annotations.json")
    try:
        with open(annotation_file, encoding="utf-8-sig") as handle:
            annotations = json.load(handle)
        canonical = json.dumps(annotations, sort_keys=True, ensure_ascii=False,
                               separators=(",", ":")).encode("utf-8")
        annotation_hash = hashlib.sha256(canonical).hexdigest()
        # The scale merged in by load_annotations, per level -- not only what
        # the drawing itself says.
        merged = load_annotations(project_dir)
        scale = merged.get("floor_scale") or {}
        levels = sorted({a.get("floor_level") for a in (merged.get("annotations") or [])
                         if a.get("floor_level")})
        return {
            "annotation_hash": annotation_hash,
            "sidecar_hash": sidecar_hash(project_dir),
            "input_hash": input_hash(annotation_hash, sidecar_hash(project_dir)),
            "annotation_saved_at": annotations.get("updated_at"),
            "floors_without_scale": [lvl for lvl in levels if not scale.get(lvl)],
        }
    except Exception:
        # No source-state yet (annotator not saved since the hook landed).
        # Say so explicitly rather than inventing a hash.
        return {"annotation_hash": None, "sidecar_hash": None,
                "input_hash": None, "annotation_saved_at": None,
                "floors_without_scale": []}


# Codex: "the stair type must be explicit in the annotation, not inferred".
# Today the type is guessed from how many points the Lauflinie has -- 2 gerade,
# 3 viertelgewendelt, 4+ halbgewendelt. That guess cannot tell a WINDER from a
# LANDING: a Podesttreppe drawn with three points is called viertelgewendelt
# and built with tapered treads, which is a different stair. The docstring
# below records exactly that case on onehalfstorey_029 ("two properly drawn
# Podesttreppen").
#
# So a drawn stair may now SAY what it is. The value maps to whether this
# renderer can actually build it; declaring one it cannot build is refused
# rather than quietly rendered as something else.
STAIR_TYPES_BUILDABLE = ("gerade", "viertelgewendelt", "halbgewendelt", "podest")
STAIR_TYPES_NOT_YET = ("spindel",)
STAIR_TYPE_FROM_POINTS = {2: "gerade", 3: "viertelgewendelt"}

# The storey the stair has to climb, kept in step with the renderer, where it is
# `wall_height (2400) + FLOOR_SLAB_M (220)`. Before this the plan shipped a
# hard-coded `{"riseMm": 175, "risers": 16}` = 2800mm climb into a 2620mm storey:
# the flight overshot the floor it arrives on by 180mm on every house.
STOREY_HEIGHT_MM = 2620.0
# DIN 18065, notwendige Treppe in a dwelling: Steigung 140..200mm, Auftritt
# >= 260mm. 175/280 is the comfortable middle and stays the target.
TARGET_RISE_MM = 175.0
NOMINAL_GOING_MM = 280.0
MIN_GOING_MM = 260.0
MAX_GOING_MM = 350.0


def stair_risers_for_storey(storey_height_mm=STOREY_HEIGHT_MM,
                            target_rise_mm=TARGET_RISE_MM):
    """How many risers this storey needs, and the rise that divides it exactly."""
    risers = max(2, int(round(storey_height_mm / target_rise_mm)))
    return risers, storey_height_mm / risers


def stair_landing_zones(path_mm, width_mm, going_mm=NOMINAL_GOING_MM):
    """Where a Podesttreppe's landings would sit on the drawn Lauflinie.

    One zone per interior vertex, `width_mm` long and centred on the vertex --
    the square landing of Rainer's reference scripts (LANDING_SIZE =
    STAIR_WIDTH). Zones closer than one going apart are MERGED, because two
    90-degree vertices a short leg apart are one U-turn with one landing across
    both flights, not two landings with a stub of flight between them
    (simple_half_turn_stair_blender.py builds exactly that one landing).

    Returns [(start_mm, end_mm), ...] as distances along the Lauflinie, plus the
    total run.
    """
    half = width_mm / 2.0
    lengths = [math.hypot(path_mm[k + 1][0] - path_mm[k][0],
                          path_mm[k + 1][1] - path_mm[k][1])
               for k in range(len(path_mm) - 1)]
    total = sum(lengths)
    zones = []
    travelled = 0.0
    for k in range(len(lengths) - 1):           # interior vertices only
        travelled += lengths[k]
        start, end = max(0.0, travelled - half), min(total, travelled + half)
        if zones and start - zones[-1][1] < going_mm:
            zones[-1] = (zones[-1][0], end)
        else:
            zones.append((start, end))
    return zones, total


def stair_turn_style(path_mm, width_mm, risers, going_mm=NOMINAL_GOING_MM,
                     min_going_mm=MIN_GOING_MM, declared=None):
    """"straight" | "landing" | "winder" -- how the drawn turns get built.

    THE RULE (Rainer, 2026-08-23: "a 4-point U with a wide turn = landing type,
    a tight turn = winder"), read geometrically:

        A turn is built as a LANDING only if the drawn Lauflinie is still long
        enough to carry every riser on straight flights once the landing has
        taken its room. Otherwise the turn must be WOUND.

    A landing eats `width_mm` of Lauflinie and gives one riser back. A winder
    eats the same run but gives a riser for every wedge in it, which is why a
    tight well can only be wound. On onehalfstorey_029 the merged landing would
    take 2271.7 of 4789.9mm, leaving 2518mm for 15 risers = 168mm going -- not a
    stair. So that U is an echte halbgewendelte Treppe, and building it as a
    Podesttreppe would be a DIFFERENT stair, not a rougher one.

    An explicit `stair_type` in the drawing still wins over the measurement.
    """
    if len(path_mm) < 3:
        return "straight"
    if declared == "podest":
        return "landing"
    if declared in ("viertelgewendelt", "halbgewendelt"):
        return "winder"
    zones, total = stair_landing_zones(path_mm, width_mm, going_mm)
    if not zones:
        return "straight"
    landing_run = sum(end - start for start, end in zones)
    flight_run = total - landing_run
    # Each landing IS one of the risers (you step up onto it), so only the rest
    # have to fit on the flights.
    flight_treads = max(1, risers - len(zones))
    return "landing" if flight_run >= flight_treads * min_going_mm else "winder"


def declared_stair_type(element):
    """The stair type the annotation states, or None if it states none."""
    value = (element.get("stair_type") or element.get("treppentyp") or "").strip().lower()
    if not value:
        return None
    if value not in STAIR_TYPES_BUILDABLE + STAIR_TYPES_NOT_YET:
        raise SystemExit(
            "stair_type=%r ist unbekannt. Erlaubt: %s"
            % (value, ", ".join(STAIR_TYPES_BUILDABLE + STAIR_TYPES_NOT_YET)))
    return value


FLOOR_OVERHANG_THRESHOLD_MM = 250.0   # Handzeichnung + Marken: 100-200 mm Rauschen sind normal
_SIDE_NAMES_DE = {"north": "Norden", "south": "Sueden", "west": "Westen", "east": "Osten"}


def _exterior_face_box(walls):
    """Outer extent (x0, x1, y0, y1) of a floor's exterior walls, measured at
    their OUTER faces (centreline +- half thickness), or None."""
    boxes = []
    for wall in walls or []:
        if wall.get("wall_type") != "exterior":
            continue
        half = (wall.get("thickness_mm") or 240) / 2.0
        (ax, ay), (bx, by) = wall["start_mm"], wall["end_mm"]
        boxes.append((min(ax, bx) - half, max(ax, bx) + half,
                      min(ay, by) - half, max(ay, by) + half))
    if not boxes:
        return None
    return (min(b[0] for b in boxes), max(b[1] for b in boxes),
            min(b[2] for b in boxes), max(b[3] for b in boxes))


def floor_overhang(floors, threshold_mm=FLOOR_OVERHANG_THRESHOLD_MM):
    """Where an upper storey's outer faces miss the ground floor's.

    Rainer, 2026-09-21, twostorey_053: "the floors are not lined up." The upper
    floor's north wall stood 353 mm beyond the ground floor's. RegisteredFrame
    snaps outer faces onto the ground floor's within SNAP_MM (350 mm), so 353 mm
    was kept "as drawn (a real setback)" and nothing in the build said so; it
    was only visible in Blender. The builder cannot tell an intended overhang
    from a hand-drawing error -- so it reports, it never moves anything.

    Compares the bounding box of the exterior walls' OUTER faces per side
    (a notch inside the box is not seen -- accepted; the box catches the whole-
    side overhang that actually happened). delta_mm > 0: the upper floor reaches
    beyond the ground floor; < 0: it stands back. "north" is +y (plan space is
    y-up). Returns [{"level", "side", "delta_mm"}].
    """
    if not floors:
        return []
    ground = next((f for f in floors if f.get("level") == "groundfloor"), floors[0])
    base = _exterior_face_box(ground.get("walls"))
    if base is None:
        return []
    out = []
    for floor in floors:
        if floor is ground:
            continue
        box = _exterior_face_box(floor.get("walls"))
        if box is None:
            continue
        for side, delta in (("west", base[0] - box[0]), ("east", box[1] - base[1]),
                            ("south", base[2] - box[2]), ("north", box[3] - base[3])):
            if abs(delta) > threshold_mm:
                out.append({"level": floor.get("level"), "side": side, "delta_mm": delta})
    return out


def floor_overhang_message(entry):
    side = _SIDE_NAMES_DE.get(entry["side"], entry["side"])
    mm = round(abs(entry["delta_mm"]))
    if entry["delta_mm"] > 0:
        what = "ragt im %s %d mm ueber das Erdgeschoss hinaus" % (side, mm)
    else:
        what = "liegt im %s %d mm hinter dem Erdgeschoss zurueck" % (side, mm)
    return ("%s %s. Pruefen: gewollter Ueberstand/Ruecksprung? Sonst die Raumkanten "
            "dieses Geschosses auf die Innenseite der Aussenwand ziehen -- Raeume, die auf "
            "der Aussenseite enden, rasten ab etwa 350 mm Abstand nicht mehr ein."
            % (entry["level"], what))


STAIR_WALL_TOLERANCE_MM = 50.0     # Handzeichnung: ein paar Zentimeter sind kein Fehler


def stair_wall_overlap(stair_core, walls):
    """Wie weit das Treppenband in eine Aussenwand ragt, oder None.

    Rainer, 2026-09-21, twostorey_053: "stairs are not aligned why all of a
    sudden again?" Die gezeichnete Lauflinie lag 250 mm zu weit rechts. Der
    Bauer legt das Band symmetrisch um sie (annotation_stair_core: "the drawn
    polyline IS the Lauflinie"), also stand das 900-mm-Band 325 mm hinter der
    Innenseite der Aussenwand und 85 mm ausserhalb des Hauses -- und nichts
    sagte es. Das ist ein Zeichenfehler, keine Bauentscheidung; der Bauer
    verschiebt nichts, er sagt es.

    Gemessen wird entlang der Bandkanten (nicht nur an den Ecken: das Band kann
    die Wand durchqueren, ohne dass eine Ecke in ihr liegt).

    Rueckgabe: {"in_wand_mm": Tiefe hinter der Wand-Innenseite,
                "ausserhalb_mm": Ueberstand hinter der Aussenseite} oder None.
    """
    polygon = (stair_core or {}).get("polygon_mm") or []
    exterior = [w for w in (walls or []) if w.get("wall_type") == "exterior"]
    if len(polygon) < 3 or not exterior:
        return None
    xs = [c for w in exterior for c in (w["start_mm"][0], w["end_mm"][0])]
    ys = [c for w in exterior for c in (w["start_mm"][1], w["end_mm"][1])]
    cx, cy = (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0

    samples = []
    for index, start in enumerate(polygon):
        end = polygon[(index + 1) % len(polygon)]
        length = math.dist(start, end)
        steps = max(1, int(length // 25))
        for step in range(steps + 1):
            t = step / steps
            samples.append((start[0] + (end[0] - start[0]) * t,
                            start[1] + (end[1] - start[1]) * t))

    in_wand = ausserhalb = 0.0
    for wall in exterior:
        (ax, ay), (bx, by) = wall["start_mm"], wall["end_mm"]
        length = math.dist((ax, ay), (bx, by))
        if length < 1.0:
            continue
        ux, uy = (bx - ax) / length, (by - ay) / length
        nx, ny = -uy, ux
        if (cx - ax) * nx + (cy - ay) * ny < 0:      # Normale zeigt ins Haus
            nx, ny = -nx, -ny
        half = (wall.get("thickness_mm") or 240) / 2.0
        for px, py in samples:
            along = (px - ax) * ux + (py - ay) * uy
            if along < 0 or along > length:
                continue
            s_in = (px - ax) * nx + (py - ay) * ny   # > 0: im Haus
            if s_in < half:
                in_wand = max(in_wand, half - s_in)
                ausserhalb = max(ausserhalb, -half - s_in)
    if in_wand <= STAIR_WALL_TOLERANCE_MM:
        return None
    return {"in_wand_mm": round(in_wand), "ausserhalb_mm": round(ausserhalb)}


def annotation_stair_core(annotations, frame, ground_level):
    """A stair core from the DRAWN stairs, for the annotation-proof path.

    `shared_stair_core` used to come only from a correction document, so a house
    that had never been through the correction editor rendered with no stairs at
    all -- silently, with "stair none in plan" buried in a log. onehalfstorey_029
    hit exactly this: two properly drawn Podesttreppen, zero revisions, and a
    stairless render (Rainer, 2026-08-19).

    The drawn polyline IS the Lauflinie (ETA-06/0261, Anhang 1), so it is passed
    through as `path_mm` unchanged and the renderer sets the treads out along it.
    The point count names the type -- 2 gerade, 3 viertelgewendelt, 4+
    halbgewendelt -- matching floorplan.ts:912 rather than inventing a second
    rule. The polygon is the swept width around that line, which is what the
    Treppenloch is cut from.

    Returns None when nothing is drawn: no stair is a legitimate state for a
    bungalow, and guessing one would be worse than none.
    """
    drawn = [e for e in (annotations.get("elements") or [])
             if e.get("type") == "stairs"
             and (e.get("floor_level") == ground_level or not e.get("floor_level"))
             and len(e.get("points") or []) >= 2]
    if not drawn:
        return None
    stair = drawn[0]
    points = stair["points"]
    path_mm = [frame.point(p) for p in points]

    # Width: the annotator stores it in the same normalised x as the points.
    width_mm = None
    if stair.get("width"):
        width_mm = abs(frame.point({"x": stair["width"], "y": 0})[0]
                       - frame.point({"x": 0, "y": 0})[0])
    # DIN 18065: a notwendige Treppe in a dwelling needs 800mm clear running
    # width. onehalfstorey_029's drawn band came out at 660mm and was rendered
    # as-is -- too narrow to be a legal stair, and it looked wrong (Rainer,
    # 2026-08-19: "you have to widen it 660 is not enough"). The drawn line is
    # a Lauflinie, not a measurement of the flight, so a band narrower than the
    # minimum is treated as unmeasured rather than as a 660mm stair.
    DIN_18065_MIN_MM = 800.0
    if not width_mm or width_mm < DIN_18065_MIN_MM:
        width_mm = 1000.0           # comfortable domestic flight

    plan_type = ("straight" if len(points) == 2
                 else "quarter_turn" if len(points) == 3
                 else "half_or_multi_turn")

    # What the drawing SAYS, next to what its shape implies. Both travel into
    # the plan: the renderer needs the declared one to build the right stair,
    # and a disagreement between the two is worth surfacing rather than
    # silently resolving.
    declared = declared_stair_type(stair)
    inferred = STAIR_TYPE_FROM_POINTS.get(len(points), "halbgewendelt")
    if declared and declared in STAIR_TYPES_BUILDABLE and declared != inferred:
        print("[plan] Hinweis: stair_type=%s, die Lauflinie mit %d Punkten "
              "sieht aber nach %s aus" % (declared, len(points), inferred))

    # The polygon is the path swept by the flight width, so the Treppenloch is
    # cut from the shape the stair actually occupies -- including its turns.
    half = width_mm / 2

    # Hand-gezeichnete Lauflinien liegen nie exakt auf Achse; schon 2 Grad
    # Schraeglage machen das ganze Band sichtbar schief (Rainer, 2026-08-22,
    # onehalfstorey_029: "the stairs are kind of crooked"). Segmente nahe
    # der Achse werden deshalb orthogonalisiert -- echte Diagonallaeufe
    # (jenseits der Toleranz) bleiben, wie sie gezeichnet sind.
    ORTHO_TOL_DEG = 20.0
    snapped = [list(path_mm[0])]
    for x, y in path_mm[1:]:
        px, py = snapped[-1]
        dx, dy = x - px, y - py
        if dx == 0 and dy == 0:
            continue
        axis_angle = math.degrees(math.atan2(abs(dy), abs(dx)))
        if axis_angle <= ORTHO_TOL_DEG:
            snapped.append([x, py])
        elif axis_angle >= 90.0 - ORTHO_TOL_DEG:
            snapped.append([px, y])
        else:
            snapped.append([x, y])
    if len(snapped) >= 2:
        path_mm = snapped

    # Gehrungs-Offset statt gemitteltem Normalenvektor: der alte Code
    # offsetete Eckpunkte mit konstanter Laenge entlang der gemittelten
    # Normale, was jede 90-Grad-Ecke um den Faktor sqrt(2) EINZOG -- die
    # Kontur wirkte an jeder Wendung angefast und schief. Die Gehrung
    # skaliert den Eck-Offset auf half/cos(halber Knickwinkel), gedeckelt
    # bei 2x fuer sehr spitze Knicke.
    left, right = [], []
    count = len(path_mm)
    for index, (x, y) in enumerate(path_mm):
        if 0 < index < count - 1:
            d1x, d1y = x - path_mm[index - 1][0], y - path_mm[index - 1][1]
            d2x, d2y = path_mm[index + 1][0] - x, path_mm[index + 1][1] - y
            l1 = math.hypot(d1x, d1y) or 1.0
            l2 = math.hypot(d2x, d2y) or 1.0
            n1 = (-d1y / l1, d1x / l1)
            n2 = (-d2y / l2, d2x / l2)
            mx, my = n1[0] + n2[0], n1[1] + n2[1]
            ml = math.hypot(mx, my)
            if ml < 1e-6:
                mx, my, scale = n1[0], n1[1], 1.0
            else:
                mx, my = mx / ml, my / ml
                scale = 1.0 / max(mx * n1[0] + my * n1[1], 0.5)
        else:
            ax, ay = path_mm[max(index - 1, 0)]
            bx, by = path_mm[min(index + 1, count - 1)]
            dx, dy = bx - ax, by - ay
            length = math.hypot(dx, dy) or 1.0
            mx, my, scale = -dy / length, dx / length, 1.0
        left.append([round(x + mx * half * scale, 1), round(y + my * half * scale, 1)])
        right.append([round(x - mx * half * scale, 1), round(y - my * half * scale, 1)])
    polygon_mm = left + list(reversed(right))

    # Steigungen aus dem GESCHOSS, nicht aus einer Konstante: 16 x 175 = 2800mm
    # stand fest im Code, waehrend der Renderer 2400mm Wand + 220mm Decke =
    # 2620mm baut. Die Treppe schoss also auf jedem Haus 180mm ueber den Boden
    # hinaus, auf dem sie ankommt.
    risers, rise_mm = stair_risers_for_storey()
    turn_style = stair_turn_style(path_mm, width_mm, risers,
                                  going_mm=NOMINAL_GOING_MM, declared=declared)

    return {
        "id": stair.get("id") or "annotation-stair",
        "polygon_mm": polygon_mm,
        "path_mm": path_mm,
        "plan_type": plan_type,
        "declared_type": declared,
        "inferred_type": inferred,
        "turn_style": turn_style,
        "usable_width_mm": width_mm,
        "geometry": {"riseMm": round(rise_mm, 2), "goingMm": NOMINAL_GOING_MM,
                     "risers": risers},
        # An explicit choice from the Annotator's stair right-click menu still
        # wins over the wall-adjacency guess, same principle as stair_type
        # above: None means "the renderer decides for itself."
        "railing_sides": stair.get("railing_sides"),
    }


def exterior_area_ground_points(area, annotations, ground_level):
    """An exterior area's points in the GROUND floor's normalized frame.

    Returns (points, None), or (None, reason) when the area was drawn on
    another floor and no usable alignment exists.

    Rainer, 2026-09-21, twostorey_053: "why is the terasse going through the
    house." Every storey is drawn on its own image, so an area's coordinates
    mean a different place on each. The annotator now records the floor an
    area was drawn on (`floor_level`); the builder used to ignore it and put
    every area through the ground floor's Frame, which puts one drawn on the
    upper floor off by scale AND offset. No `floor_level` (all 219 areas so
    far) means ground -- what this builder always assumed.

    Site dressing, not walls: the same alignment affine the storeys use, but
    NOT RegisteredFrame.point(), which snaps to building faces. Points stay
    unclamped -- a driveway is meant to reach past the photographed image.
    A mirrored mapping (marks on different diagonals) counts as no alignment.
    """
    points = area.get("points") or []
    home = area.get("floor_level") or ground_level
    if home == ground_level:
        return points, None
    affine = _alignment_affine(annotations.get("floor_alignment") or {}, home, ground_level)
    if not affine or affine[0] <= 0 or affine[2] <= 0:
        return None, (f"auf {home} gezeichnet, aber die Ausrichtung {home} / {ground_level} "
                      f"fehlt oder ist unbrauchbar (zwei diagonal gegenueberliegende "
                      f"Aussenecken auf beiden Geschossen markieren)")
    ax, bx, ay, by = affine
    return [{"x": ax * p["x"] + bx, "y": ay * p["y"] + by} for p in points], None


def plan_exterior_areas(annotations, floor_scale, pixel_width, pixel_height):
    """Terrasse / Einfahrt / Gehweg / Garten as `points_mm` for the annotation
    plan. Exterior site data is building-wide, not per-floor: one roof, one set
    of site areas, expressed in the ground floor's millimetres (site
    coordinates are only meaningful against the ground floor's calibration)."""
    ground_level = "groundfloor" if "groundfloor" in floor_scale else next(iter(floor_scale), None)
    if not ground_level:
        return []
    frame = Frame(floor_scale[ground_level], pixel_width, pixel_height)
    out = []
    for area in annotations.get("exterior_areas") or []:
        if len(area.get("points") or []) < 3:
            continue
        points, reason = exterior_area_ground_points(area, annotations, ground_level)
        if points is None:
            print(f"[plan] Hinweis: Aussenflaeche {area.get('type')} ({area.get('id')}) "
                  f"ausgelassen: {reason}.")
            continue
        out.append({
            "id": area.get("id"),
            "type": area.get("type"),
            "points_mm": [frame.point(p) for p in points],
        })
    return out


def annotation_exterior_areas(project_id, corrected_rooms):
    """Terrasse / Einfahrt / Gehweg from the annotation package, mapped into
    the CORRECTED document's millimetre space.

    The corrected path shipped `"exterior_areas": []` hard-coded, so every
    render from an approved revision had a house standing on bare ground with
    no driveway, path or terrace (Rainer, 2026-08-17: "outside you still do
    not have any of the outside stuff like driveway garden").

    The two spaces do not share an origin: annotation millimetres come from
    the drawing's own scale calibration, corrected millimetres from the
    corrector. They DO share the building, so the ground floor's footprint
    bounding box gives the affine fit -- scale and offset per axis -- and the
    site areas ride through it. Fitting on the footprint rather than assuming
    a common origin is the whole point; assuming would put the driveway
    through the house.
    """
    path = os.path.join(SIMPLIFIER, "projects", project_id, "annotations.json")
    if not os.path.exists(path) or not corrected_rooms:
        return []
    annotations = load_json(path)
    areas = annotations.get("exterior_areas") or []
    if not areas:
        return []
    project_dir = os.path.join(SIMPLIFIER, "projects", project_id)
    pixel_width, pixel_height = image_size(project_dir, annotations)
    floor_scale = annotations.get("floor_scale") or {}
    level = "groundfloor" if "groundfloor" in floor_scale else next(iter(floor_scale), None)
    if not level:
        return []
    frame = Frame(floor_scale[level], pixel_width, pixel_height)

    source = []
    for item in annotations.get("annotations", []):
        if item.get("floor_level") != level or len(item.get("points") or []) < 3:
            continue
        if excluded(item.get("label")):
            continue
        source += [frame.point(p) for p in item["points"]]
    target = [p for room in corrected_rooms for p in room["polygon_mm"]]
    if len(source) < 3 or len(target) < 3:
        return []

    def fit(index):
        s_lo, s_hi = min(p[index] for p in source), max(p[index] for p in source)
        t_lo, t_hi = min(p[index] for p in target), max(p[index] for p in target)
        span = s_hi - s_lo
        scale = (t_hi - t_lo) / span if span > 1 else 1.0
        return scale, t_lo - s_lo * scale

    sx, ox = fit(0)
    sy, oy = fit(1)
    out = []
    for area in areas:
        if len(area.get("points") or []) < 3:
            continue
        points, reason = exterior_area_ground_points(area, annotations, level)
        if points is None:
            print(f"[plan] Hinweis: Aussenflaeche {area.get('type')} ({area.get('id')}) "
                  f"ausgelassen: {reason}.")
            continue
        mapped = []
        for p in points:
            x, y = frame.point(p)
            mapped.append([round(x * sx + ox, 1), round(y * sy + oy, 1)])
        out.append({"id": area.get("id"), "type": area.get("type"),
                    "points_mm": mapped})
    print(f"[plan] exterior areas: {len(out)} mapped onto the corrected footprint "
          f"(scale {sx:.3f}/{sy:.3f})")
    return out


def correction_plan(revision_path, style, out_path):
    """Build a render plan from the CORRECTED document instead of annotations.

    Step 3 of plans/renderer-switch-execution-order.md. The corrected document
    holds the geometry Rainer actually fixed: real walls with thickness and
    type, openings bound to a wall id at a position along it, a shared stair
    core. None of it is derived from room polygons here -- it is copied.

    Y is flipped exactly once, here. The correction document is SVG space (Y
    grows down); the Blender scripts want Y growing north. Every point on a
    floor goes through the same flip; opening `position` is a fraction along an
    already-flipped wall, so it is left alone.
    """
    document = load_json(revision_path)
    reference = document.get("source_reference_id") or "unknown"
    building = document.get("building") or {}
    models = load_model_picks(style)

    floors_out = []
    flips = {}
    for floor in document.get("floors", []):
        points = [p for room in floor.get("rooms", []) for p in room.get("polygon", [])]
        points += [p for wall in floor.get("walls", []) for p in (wall["start"], wall["end"])]
        if not points:
            continue
        max_y = max(p[1] for p in points)

        def flip(point, _max_y=max_y):
            return [round(float(point[0]), 1), round(_max_y - float(point[1]), 1)]

        rooms = [{
            "id": room.get("id"),
            "name": room.get("name"),
            "kind": room.get("kind") or room_kind(room.get("name")),
            "polygon_mm": [flip(p) for p in room.get("polygon", [])],
            "area_m2": room.get("area_m2"),
        } for room in floor.get("rooms", []) if not excluded(room.get("name"))]
        # Fuer R6_furniture_inside: dieselben Raeume, die oben herausgefiltert
        # wurden, weil sie Garage/Terrasse/Balkon/etc. sind. Codex, 2026-08-21:
        # "Der Korrektur-Weg filtert ausgeschlossene Raeume aus rooms, exportiert
        # sie aber nicht als excluded_areas ... betrifft genau Korrekturplaene
        # mit dort platzierten Moebeln." Ohne das faellt ein legitim in der
        # Garage stehendes Moebel durch den Verifier.
        excluded_areas = [{
            "label": room.get("name"),
            "polygon_mm": [flip(p) for p in room.get("polygon", [])],
        } for room in floor.get("rooms", []) if excluded(room.get("name"))]

        walls = [{
            "id": wall.get("id"),
            "start_mm": flip(wall["start"]),
            "end_mm": flip(wall["end"]),
            "thickness_mm": wall.get("thickness", DEFAULT_WALL_THICKNESS_MM),
            "wall_type": wall.get("wall_type", "interior"),
            "rooms": wall.get("room_ids", []),
        } for wall in floor.get("walls", [])]

        openings = [{
            "id": opening.get("id"),
            "wall_id": opening.get("wall_id"),
            "opening_type": opening.get("opening_type"),
            "position": opening.get("position"),
            "width_mm": opening.get("width"),
            "height_mm": opening.get("height_mm",
                                     1350 if opening.get("opening_type") == "window" else 2010),
            "sill_height_mm": opening.get("sill_height_mm", 0),
            "traversable": opening.get("traversable"),
            "role": opening.get("role"),
            "connects": opening.get("connects", []),
        } for opening in floor.get("openings", [])]

        flips[floor.get("id")] = flip
        placements, skipped = corrected_placements(reference, floor.get("id"), models)

        floors_out.append({
            "id": floor.get("id"),
            "name": floor.get("name"),
            "level": floor.get("level"),
            "rooms": rooms,
            "walls": walls,
            "openings": openings,
            "placements": placements,
            "unplaced": skipped,
            "skipped_rooms": [],
            "unmatched_openings": [],
            "openings_in_excluded_rooms": [],
            "excluded_areas": excluded_areas,
        })
        print(f"[plan] {floor.get('name')}: {len(rooms)} rooms, {len(walls)} walls, "
              f"{len(openings)} openings, {len(placements)} furniture")

    # The stair is a building-wide object in the correction document, so it is
    # mapped once, through the ground floor's flip (its polygon is in the same
    # space). Without this the house renders with no stairs at all.
    stair = document.get("shared_stair_core") or None
    stair_out = None
    if stair and stair.get("polygon") and floors_out:
        ground_flip = flips.get(floors_out[0]["id"])
        if ground_flip:
            stair_out = {
                "id": stair.get("id"),
                "polygon_mm": [ground_flip(point) for point in stair["polygon"]],
                "path_mm": [ground_flip(point) for point in (stair.get("path") or [])],
                "plan_type": stair.get("plan_type"),
                "declared_type": stair.get("declared_type"),
                "inferred_type": stair.get("inferred_type"),
                "turn_style": stair.get("turn_style"),
                "usable_width_mm": stair.get("usable_width_mm"),
                "geometry": stair.get("geometry"),
            }

    plan = {
        "schema": "dmh-furnished-render-plan-proof-v1",
        "plan_id": f"{reference}-{style}-corrected",
        "shared_stair_core": stair_out,
        "source_geometry_hash": document.get("geometry_hash"),
        "source_provenance": source_provenance(reference),
        "source": ("approved_correction_revision" if document.get("status") == "approved"
                   else "correction_revision_draft"),
        "correction_revision": os.path.abspath(revision_path),
        "correction_status": document.get("status"),
        "not_for_delivery": True,
        "style": style,
        # The Dachform is set in the annotator and does not travel into the
        # correction document, so fall back to the annotation package rather
        # than render a roofless house.
        "roof_type": building.get(f"roof_type_{style}") or annotation_roof(reference, style),
        "roof_overhang_mm": building.get("roof_overhang_mm")
                            or annotation_roof(reference, "overhang") or 500,
        "camera_style": annotation_camera_style(reference),
        "exterior_areas": annotation_exterior_areas(
            reference, floors_out[0]["rooms"] if floors_out else []),
        "floors": floors_out,
    }
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(plan, handle, indent=2)
    print(f"[plan] wrote {out_path} from {document.get('status')} revision "
          f"{document.get('revision')}")


def main():
    if len(sys.argv) >= 4 and sys.argv[1] == "--geometry-only":
        return geometry_only(sys.argv[2], sys.argv[3])
    # Die Identitaet der Raeume eines Geschosses, fuer den Moebel-Stempel.
    # EINE Implementierung: der Editor (beim Speichern) und der Bau (beim
    # Pruefen) fragen dieselbe Funktion, statt sie zweimal zu schreiben.
    if len(sys.argv) >= 4 and sys.argv[1] == "--geometrie-id":
        kennung = level_geometry_identity(sys.argv[2], sys.argv[3])
        print(kennung or "")
        return 0
    if len(sys.argv) >= 5 and sys.argv[1] == "--correction-revision":
        # Reserved for step 3 (the correction -> render adapter). It validates
        # and refuses today rather than silently falling back to annotations,
        # so the flag can never quietly mean "legacy" once it exists.
        # Hand-drawn work does not go through the approval gate -- that exists
        # for the automatic generator path (Rainer, 2026-08-16). A draft is a
        # real corrected document; the output records which it was.
        if not os.path.exists(sys.argv[2]):
            raise SystemExit(f"{sys.argv[2]}: no such correction revision")
        return correction_plan(sys.argv[2], sys.argv[3], sys.argv[4])
    if len(sys.argv) < 4:
        raise SystemExit(
            "usage: build-simplifier-render-plan.py <project_id> <style> <out.json>\n"
            "       build-simplifier-render-plan.py --geometry-only <project_id> <out.json>")
    project_id, style, out_path = sys.argv[1], sys.argv[2], sys.argv[3]

    project_dir = os.path.join(SIMPLIFIER, "projects", project_id)
    annotations = load_annotations(project_dir)
    pixel_width, pixel_height = image_size(project_dir, annotations)

    floor_scale = annotations.get("floor_scale") or {}
    floors_out = []
    models = load_model_picks(style)
    footprints = load_json(FOOTPRINTS)

    levels = sorted({item.get("floor_level") for item in annotations.get("annotations", [])
                     if item.get("floor_level")})
    # The drawn outer outline (Rainer, 2026-08-13) represents the ground-
    # level footprint -- same "groundfloor if present, else first level"
    # convention already used for exterior_areas below.
    ground_level = "groundfloor" if "groundfloor" in levels else (levels[0] if levels else None)
    for level in levels:
        scale = floor_scale.get(level)
        if not scale:
            raise SystemExit(f"{level} has no calibrated scale — set it in the Simplifier first")
        # Obergeschosse werden ueber die Ausrichtungsmarken auf das
        # Erdgeschoss registriert (RegisteredFrame); das Erdgeschoss selbst
        # bekommt den gewoehnlichen Frame.
        frame = frame_for_level(annotations, level, ground_level, pixel_width, pixel_height)

        rooms = []
        excluded_polygons = []
        for item in annotations.get("annotations", []):
            if item.get("floor_level") != level:
                continue
            points = item.get("points") or []
            if len(points) < 3:
                continue
            if excluded(item.get("label")):
                excluded_polygons.append((item.get("label"), [frame.point(p) for p in points]))
                continue
            polygon = [frame.point(p) for p in points]
            rooms.append({
                "id": item.get("id") or f"room-{len(rooms)}",
                "name": item.get("label") or "Raum",
                "kind": room_kind(item.get("label")),
                "polygon_mm": polygon,
                "area_m2": round(polygon_area(polygon) / 1e6, 2),
            })

        walls, openings, unmatched, skipped_excluded = build_floor_walls_and_openings(
            rooms, excluded_polygons, annotations, level, frame, ground_level)

        placements = []
        skipped = []
        # One source of furniture per floor, chosen once. Workbench furniture is
        # already in this plan's millimetres; annotation symbols are normalized
        # and go through `frame`. Everything downstream — SYMBOL_3D, measured
        # footprint precedence, model lookup, mismatch handling, procedural
        # fallback, derived chairs — is shared and untouched.
        workbench_symbols = workbench_furniture(project_id, level)
        from_workbench = workbench_symbols is not None
        if from_workbench:
            source_symbols = workbench_symbols
            furniture_source = "workbench_furniture_proof"
        else:
            source_symbols = [item for item in annotations.get("symbols", [])
                              if item.get("floor_level") == level]
            furniture_source = "simplifier_annotations_proof"

        for symbol in source_symbols:
            key = symbol.get("symbol")
            spec = SYMBOL_3D.get(key)
            if not spec:
                skipped.append({"symbol": key, "reason": "no 3D specification"})
                continue

            # Path and rectangle symbols carry BOTH `points` and a centre
            # `position`. The points are the real geometry — a kitchen run is
            # its path, not a dot — so they win. Testing `position` first sent
            # every Kuechenzeile down the stamp branch and lost it.
            if from_workbench:
                points = symbol.get("points_mm") or []
                position = None if points else symbol.get("position_mm")
                to_mm = lambda point: [round(float(point[0]), 1), round(float(point[1]), 1)]
            else:
                points = symbol.get("points") or []
                position = None if points else symbol.get("position")
                to_mm = frame.point
            if points:
                placements.append({
                    "asset_id": key,
                    "type": spec["type"],
                    # Eine Insel ist ein Rechteck, egal mit wie vielen Punkten
                    # sie gezeichnet wurde -- build_rect() nimmt ohnehin nur die
                    # Bounding Box. Die alte Bedingung `len(points) > 2` schickte
                    # genau den Normalfall in den falschen Zweig: das Werkzeug
                    # erzeugt ZWEI gegenueberliegende Ecken, also wurde daraus ein
                    # Kuechenzeilen-Lauf entlang der Diagonalen -- im Editor ein
                    # Rechteck, in der .blend ein schraeger Balken (Rainer,
                    # 2026-08-25: "the generated blender file always ends up at
                    # 45 degrees"). Zeile 2024 hatte die Bedingung nie.
                    "build": "rect" if key in RECT_BUILD else "path",
                    "points_mm": [to_mm(p) for p in points],
                    # The catalogue depth for this symbol. Falling back to a blanket
                    # 600 built every Vorwandinstallation four times too deep.
                    "depth_mm": symbol.get("depth_mm") or spec.get("depth", 600),
                    "height_mm": spec["height"],
                    "source": furniture_source,
                })
                continue
            if not position:
                skipped.append({"symbol": key, "reason": "no position"})
                continue

            # A footprint measured on the plan by dragging the symbol's
            # corners beats the catalogue's nominal size. The annotator was
            # looking at the actual drawing; the catalogue is a general figure
            # for that kind of furniture, and using it is what made every piece
            # come out undersized.
            measured = symbol.get("footprint_mm") or {}
            footprint = measured if measured.get("width_mm") else (footprints.get(key) or {})
            if not footprint.get("width_mm"):
                skipped.append({"symbol": key, "reason": "no footprint in the catalogue"})
                continue
            model = models.get(key)
            build = spec.get("build")
            if not model and not build:
                build = "box"

            # The gate exists to stop a wildly wrong model being squeezed into
            # a nominal catalogue footprint. It must never fire against a
            # footprint Rainer measured on the plan: that comparison is between
            # two things that are both correct, and rejecting the model turned
            # every carefully measured symbol into a plain box.
            measured_here = bool(measured.get("width_mm"))
            mismatch = (bool(model) and not measured_here
                        and footprint_mismatch(model, footprint))
            if mismatch and not build:
                # No model worth using and nothing procedural defined, so build
                # it as a plain box at the annotated size.
                build = "box"

            # Second link in the chain, before the box wins by default: a
            # generated catalogue model. Only for symbols whose spec defines
            # NO procedural builder of its own -- `kuechenzeile` (path) and
            # `stuff` (rect) are runs whose length comes from the drawing, and
            # one glb cannot stand in for those. Everything reaching here would
            # otherwise be a plain box.
            generated = (generated_catalog_model(key, spec["type"], style,
                                                 footprint)
                         if not spec.get("build") else None)
            if generated and (not model or mismatch):
                model, mismatch, build = generated, False, None
                generated = None

            placements.append({
                "asset_id": key,
                "type": spec["type"],
                "mesh_path": model["path"] if model and not mismatch else None,
                "model_source": (model["source"] if model and not mismatch
                                 else "procedural"),
                "model_label": model.get("label") if model else None,
                "scale_divisor": model.get("divisor", 1.0) if model else 1.0,
                # The model's own verified real-world size, from
                # resolve-hub-scales.py. The renderer scales to THIS rather than
                # to the catalogue footprint, so a real 2200 mm dining set stays
                # 2200 mm instead of being squeezed into a nominal 1800.
                "verified_size_mm": model.get("size_mm") if model else None,
                "size_mismatch": mismatch,
                # Measured by dragging the symbol's corners on the plan. When
                # present it OUTRANKS the model's own verified size: Rainer was
                # looking at this drawing, the model's dimensions describe some
                # other piece of furniture.
                "footprint_measured": bool(measured.get("width_mm")),
                "build": build,
                "position_mm": to_mm(position),
                "rotation_deg": symbol.get("rotation_deg", 0),
                "mirrored": bool(symbol.get("mirrored")),
                "target_bbox_mm": {
                    "width_mm": footprint.get("width_mm"),
                    "depth_mm": footprint.get("depth_mm"),
                    "height_mm": spec["height"],
                },
                "height_mm": spec.get("mount", 0),
                # Library models carry their own materials, which is the entire
                # reason to prefer them over generated meshes. Scale them to the
                # annotated footprint, but never overwrite what they came with.
                # An item with a `build` kind is routed through a procedural
                # builder by the renderer and its mesh is never imported, so
                # claiming preserve_materials there made the plan lie about
                # which path the item takes.
                #
                # Two corrections, 2026-09-03:
                # - The renderer no longer honours only the sink. Any item that
                #   still carries a mesh_path is imported (shower excepted), so
                #   `fernseher` takes the model path too despite build="tv".
                #   Its materials are still replaced from TYPE_FINISH, which is
                #   why "tv" needed an entry there.
                # - Generated catalogue models are untextured white shapes.
                #   Preserving their materials would render a white cupboard in
                #   every style, so they are explicitly excluded and get the
                #   style's finish like a procedural piece.
                "preserve_materials": bool(model)
                    and model.get("source") != "generated_catalog"
                    and (not build or spec["type"] == "sink"),
                # Third link, for the case this builder cannot decide: the
                # renderer runs its OWN distortion check and drops a model
                # that cannot meet the symbol. That check is why all three
                # Kleiderschraenke became boxes -- here the footprint was
                # measured, so `size_mismatch` stayed false and this builder
                # saw nothing wrong. Carry the generated alternative along so
                # the renderer has something better than a box to fall back
                # to. None when the symbol has its own procedural builder or
                # the catalogue holds no model of that type.
                "fallback_mesh_path": generated["path"] if generated else None,
                "fallback_model_label": generated["label"] if generated else None,
                "wall_snapped": bool(symbol.get("wall_snapped")),
                "source": furniture_source,
            })

        # A desk without a chair reads as unfinished (defect #4). If Rainer
        # annotated no schreibtischstuhl, derive one: offset from the desk
        # toward its room's centre (convention-free — no guess about which
        # local axis is 'front'), turned to face the desk. Presentation-only,
        # like all furnishing; never geometry.
        has_chair = any(p["asset_id"] == "schreibtischstuhl" for p in placements)
        chair_model = models.get("schreibtischstuhl")
        if not has_chair and chair_model:
            for desk in [p for p in placements if p["asset_id"].startswith("schreibtisch")]:
                dx, dy = desk["position_mm"]
                room = next((r for r in rooms if point_in_polygon((dx, dy), r["polygon_mm"], 0)), None)
                if not room:
                    continue
                pts = room["polygon_mm"]
                centroid = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
                vx, vy = centroid[0] - dx, centroid[1] - dy
                norm = math.hypot(vx, vy) or 1.0
                offset = (desk["target_bbox_mm"].get("depth_mm") or 800) / 2 + 350
                cx, cy = dx + vx / norm * offset, dy + vy / norm * offset
                facing = (math.degrees(math.atan2(-vx, vy)) + 180.0) % 360.0
                placements.append({
                    "asset_id": "schreibtischstuhl",
                    "type": "office_chair",
                    "mesh_path": chair_model["path"],
                    "model_source": chair_model["source"],
                    "model_label": chair_model.get("label"),
                    "scale_divisor": chair_model.get("divisor", 1.0),
                    "verified_size_mm": chair_model.get("size_mm"),
                    "size_mismatch": False,
                    "footprint_measured": False,
                    "build": None,
                    "position_mm": [round(cx, 1), round(cy, 1)],
                    "rotation_deg": round(facing, 1),
                    "mirrored": False,
                    "target_bbox_mm": {"width_mm": 650, "depth_mm": 650,
                                       "height_mm": 1200},
                    "height_mm": 0,
                    "preserve_materials": True,
                    "wall_snapped": False,
                    "derived_from": desk["asset_id"],
                    "source": furniture_source,
                })

        # The modern dining pick is a TABLE-ONLY model (the old set model was
        # a black blob and got swapped on Rainer's request); six chairs are
        # derived around it: two per long side, one per end, each turned to
        # face the table. Only when the resolved pick is a bare table —
        # a set model (classic) brings its own chairs.
        chair_model = models.get("essgruppe_stuhl")
        if chair_model:
            for table in [p for p in placements
                          if p["asset_id"] == "essgruppe_6"
                          and "table" in (p.get("model_label") or "").lower()
                          and "set" not in (p.get("model_label") or "").lower()]:
                tx, ty = table["position_mm"]
                theta = math.radians(table.get("rotation_deg", 0))
                cos_t, sin_t = math.cos(theta), math.sin(theta)
                half_w = (table["verified_size_mm"] or [1522, 914])[0] / 2
                half_d = (table["verified_size_mm"] or [1522, 914])[1] / 2
                chair_half = 297
                # Abstand von der Tischkante zur Stuhlmitte. War 40mm --
                # die Stuehle standen wie aufgereiht daneben statt am Tisch.
                # -60 schiebt die Sitzflaeche ein Stueck unter die Platte,
                # so wie ein zurueckgeschobener Stuhl wirklich steht
                # (Rainer, 2026-08-25: "alle Stuehle etwas naeher zum Tisch
                # ruecken, nicht zu viel").
                CHAIR_GAP_MM = -60
                side_y = half_d + CHAIR_GAP_MM + chair_half
                end_x = half_w + CHAIR_GAP_MM + chair_half
                locals_deg = [(-half_w / 2, side_y, 180), (half_w / 2, side_y, 180),
                              (-half_w / 2, -side_y, 0), (half_w / 2, -side_y, 0),
                              (end_x, 0, 90), (-end_x, 0, 270)]
                # Ein Stuhl steht schief. Sechs exakt ausgerichtete Stuehle
                # sehen gerendert aus wie ein Katalogfoto, nicht wie ein
                # bewohntes Haus ("damit es nicht ultra perfect aussieht").
                #
                # Deterministisch, nicht zufaellig: derselbe Grundriss ergibt
                # bei jedem Bau denselben Stuhl und denselben Winkel, sonst
                # aendert sich das Zertifikat bei jedem Lauf. Ueber den
                # Plannamen gestreut, damit nicht in jedem Haus derselbe Platz
                # schief steht.
                streu = int(hashlib.sha256(project_id.encode("utf-8")).hexdigest()[:8], 16)
                schief_index = streu % len(locals_deg)
                schief_grad = 15 if (streu >> 8) % 2 else -15
                for stuhl_nr, (lx, ly, face) in enumerate(locals_deg):
                    if stuhl_nr == schief_index:
                        face = (face + schief_grad) % 360
                    wx = tx + lx * cos_t - ly * sin_t
                    wy = ty + lx * sin_t + ly * cos_t
                    placements.append({
                        "asset_id": "essgruppe_stuhl",
                        "type": "dining_chair",
                        "mesh_path": chair_model["path"],
                        "model_source": chair_model["source"],
                        "model_label": chair_model.get("label"),
                        "scale_divisor": chair_model.get("divisor", 1.0),
                        "verified_size_mm": chair_model.get("size_mm"),
                        "size_mismatch": False,
                        "footprint_measured": False,
                        "build": None,
                        "position_mm": [round(wx, 1), round(wy, 1)],
                        "rotation_deg": (table.get("rotation_deg", 0) + face) % 360,
                        "mirrored": False,
                        "target_bbox_mm": {"width_mm": 563, "depth_mm": 593,
                                           "height_mm": 844},
                        "height_mm": 0,
                        "preserve_materials": True,
                        "wall_snapped": False,
                        "derived_from": "essgruppe_6",
                        "source": furniture_source,
                    })

        # Gezeichnete Balkone dieses Geschosses. Der Annotator kann sie seit
        # jeher zeichnen (type "balcony"), aber KEIN Skript hat den Typ je
        # gelesen -- der Balkon von onehalfstorey_029 (Obergeschoss West)
        # stand in der Zeichnung und fehlte in jedem .blend (Rainer,
        # 2026-08-22: "didnt create a balkony in the upperfloor westside").
        balconies = [{
            "id": e.get("id") or f"balcony-{level}",
            "polygon_mm": [frame.point(p) for p in e["points"]],
        } for e in annotations.get("elements", [])
            if e.get("type") == "balcony" and e.get("floor_level") == level
            and len(e.get("points") or []) >= 3]

        floors_out.append({
            "id": level,
            "name": level,
            "level": level,
            "scale_metres_per_x_unit": scale,
            "rooms": rooms,
            "walls": walls,
            "openings": openings,
            "placements": placements,
            "balconies": balconies,
            "unplaced": skipped,
            "skipped_rooms": [],
            "unmatched_openings": unmatched,
            "openings_in_excluded_rooms": [
                {"id": oid, "room": label} for oid, label in skipped_excluded],
            # Fuer R6_furniture_inside (verify_render.py): Moebel in einem
            # ausgeschlossenen Bereich (Garage, Terrasse, Balkon ...) stehen
            # legitim ausserhalb jedes RAUM-Polygons -- der Verifier braucht
            # diese Flaechen, um sie nicht faelschlich als "draussen" zu
            # meiden (Codex-Review, 2026-08-21).
            "excluded_areas": [{"label": label, "polygon_mm": poly}
                               for label, poly in excluded_polygons],
        })

    # Exterior site data is building-wide, not per-floor -- see
    # plan_exterior_areas() / exterior_area_ground_points().
    exterior_areas_out = plan_exterior_areas(annotations, floor_scale, pixel_width, pixel_height)

    # ROOF-RIDGE-PATH-TOOL-001, 2026-09-27: the drawn ridge path is
    # normalized 0-1 on whichever floor's image the Dach tab shows --
    # "das DACH sitzt auf dem OBERSTEN Geschoss" (render-exterior.py's own
    # convention, `floors[-1]`) -- `levels[-1]` here is the SAME floor,
    # built through the SAME `floors_out` loop just above, so converting
    # through its own `frame_for_level()` lands in the identical world-
    # metre frame `footprint` (traced from that floor's own walls) already
    # uses in render-exterior.py -- no separate registration step to get
    # wrong.
    # ROOF-RIDGE-MULTI-PATH-001, 2026-10-01: `roof_ridge_paths` (plural) is
    # the current field -- a LIST of independent, not-necessarily-connected
    # paths (Rainer: "we said we would build a 'countertop' line maker,
    # where i can also draw independent lines"). `roof_ridge_path`
    # (singular) is read as a one-path fallback for a project whose
    # annotations.json predates this and was never resaved.
    roof_ridge_paths_m = []
    _ridge_paths_norm = annotations.get("roof_ridge_paths")
    if not _ridge_paths_norm:
        _single = annotations.get("roof_ridge_path") or []
        _ridge_paths_norm = [_single] if len(_single) >= 2 else []
    if levels:
        _top_level = levels[-1]
        _top_frame = frame_for_level(annotations, _top_level, ground_level, pixel_width, pixel_height)
        if _top_frame:
            roof_ridge_paths_m = [
                [
                    {"x": _top_frame.point(p)[0] / 1000.0, "y": _top_frame.point(p)[1] / 1000.0}
                    for p in _path_norm
                ]
                for _path_norm in _ridge_paths_norm
                if len(_path_norm) >= 2
            ]

    out = {
        "schema": "dmh-furnished-render-plan-proof-v1",
        "plan_id": project_id,
        # No canonical document exists for this plan, so there is no geometry
        # hash to quote. Saying so explicitly is the point: an image built this
        # way is for review and cannot be delivered.
        "source_geometry_hash": None,
        "source": furniture_source,
        "source_provenance": source_provenance(project_id),
        "not_for_delivery": True,
        "style": style,
        "camera_style": annotations.get("camera_style") or "realistic",
        "roof_type": annotations.get(f"roof_type_{style}"),
        # Whether anybody ever CHOSE this roof. Measured 2026-08-20: all 234
        # annotations lack roof_type entirely, so the renderer's
        # `plan.get("roof_type") or "flachdach"` quietly gave every house a flat
        # roof -- including onehalfstorey_* houses, whose half storey exists
        # BECAUSE of a pitched roof. A delivery certified with an invented roof
        # is a certificate that means less than it looks like, so the plan now
        # says which it was and the manifest carries it forward.
        "roof_type_source": dach_herkunft(annotations, style),
        # Ein geschaetzter Massstab darf nicht wie ein gemessener aussehen.
        "floor_scale_geschaetzt": massstab_geschaetzt(annotations),
        "roof_overhang_mm": annotations.get("roof_overhang_mm"),
        # Side-view roof editor (Dach tab): exterior dressing like the overhang,
        # not geometry -- see roof_profile.py.
        "roof_profiles": annotations.get("roof_profiles"),
        # Which of pultdach / doppelpultdach is delivered as the 4th roof form.
        "roof_fourth": annotations.get("roof_fourth"),
        # Rainer, 2026-09-22: "also mybe have a possibility to rotate the
        # roof 90 degrees." null/"x"/"y" -- see roof_profile.py _axes().
        "roof_axis_override": annotations.get("roof_axis_override"),
        # Rainer, 2026-09-26: per-WING override for an L-shaped (two-wing)
        # house -- keyed "wingA"/"wingB", the same naming roof_wings.py's
        # own recognize_two_wings() returns (wingA = full x-extent, wingB =
        # full y-extent). Falls back to roof_axis_override (whole-house)
        # per wing when absent -- see render-exterior.py's own two-wing
        # branch. plans/PER-WING-AXIS-OVERRIDE-001.md.
        "roof_axis_overrides": annotations.get("roof_axis_overrides") or {},
        # ROOF-RIDGE-MULTI-PATH-001, 2026-10-01: the user-drawn ridge
        # path(s), already converted to WORLD METRES (see
        # roof_ridge_paths_m above) -- when present, render-exterior.py
        # derives wing rectangles from THESE instead of
        # roof_wings.recognize_two_wings() or roof_axis_override(s);
        # absent/empty leaves today's automatic behaviour unchanged.
        "roof_ridge_paths": roof_ridge_paths_m,
        "exterior_areas": exterior_areas_out,
        # Built from the drawn stairs, so an annotated house renders its stairs
        # without first passing through the correction editor.
        "shared_stair_core": annotation_stair_core(
            annotations, Frame(floor_scale.get(ground_level) or 1.0, pixel_width, pixel_height),
            ground_level),
        "floors": floors_out,
    }

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(out, handle, indent=1)

    for floor in floors_out:
        print(f"[plan] {floor['name']}: {len(floor['rooms'])} rooms, {len(floor['walls'])} walls "
              f"({sum(1 for w in floor['walls'] if w['wall_type'] == 'exterior')} exterior), "
              f"{len(floor['openings'])} openings, {len(floor['placements'])} furniture")
        if floor["unmatched_openings"]:
            print(f"[plan]   {len(floor['unmatched_openings'])} openings matched no wall")
        for entry in floor.get("openings_in_excluded_rooms", []):
            print(f"[plan]   opening {entry['id']} sits in excluded room "
                  f"'{entry['room']}' — intentionally not rendered")
        for item in floor["unplaced"]:
            print(f"[plan]   skipped {item['symbol']}: {item['reason']}")
        procedural = [p["asset_id"] for p in floor["placements"] if p.get("model_source") == "procedural"]
        if procedural:
            print(f"[plan]   built procedurally: {', '.join(sorted(set(procedural)))}")
    overlap = stair_wall_overlap(out.get("shared_stair_core"),
                                 floors_out[0]["walls"] if floors_out else [])
    if overlap:
        print("[plan] Hinweis: die Treppe ragt %d mm hinter die Innenseite der Aussenwand"
              "%s. Die Lauflinie im Annotator etwa %d mm nach innen ziehen -- das Band "
              "ist %d mm breit und liegt mittig auf ihr."
              % (overlap["in_wand_mm"],
                 (" (%d mm davon ausserhalb des Hauses)" % overlap["ausserhalb_mm"])
                 if overlap["ausserhalb_mm"] else "",
                 overlap["in_wand_mm"],
                 (out["shared_stair_core"] or {}).get("usable_width_mm") or 0))
    for entry in floor_overhang(floors_out):
        print("[plan] Hinweis: " + floor_overhang_message(entry))
    print(f"[plan] wrote {out_path}")


if __name__ == "__main__":
    main()

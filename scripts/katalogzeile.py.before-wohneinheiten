"""The kon_grundrisse row for a house -- the same rule the original import used.

Plan: plans/katalogzeile-automatisch-v1.md. Until 2026-10-20 every house drawn
after the one-time catalogue import in August needed an INSERT typed by hand in
WP Data Access (Rainer: "you have to get this fixed why all the extra work").
publish-renders.py now builds the row here and sends it to the INSERT-only
route b2t/v1/grundriss-anlegen.

The rule was reconstructed from the live list and is held to it by
katalogzeile.test.py (every dataset house that is in the catalogue):
haustyp from house_type, geschosse = drawn floors, keller = a basement floor,
raeume = drawn room areas, schlafzimmer = eltern, kinderzimmer = kind,
baeder = bad (a DU-WC does not count), ausstattung = the words below.
"""

import json
import os

HAUSTYPEN = {
    "bungalow": "Bungalow",
    "twostorey": "Zweigeschosser",
    "2-storey": "Zweigeschosser",
    "onehalfstorey": "1,5-Geschosser",
    "1.5-storey": "1,5-Geschosser",
    "twostorey_cellar": "Zweigeschosser mit Keller",
    "other": "Sonstige",
}

# room_id -> catalogue words. diele, flur, du_wc, luftraum, treppe ... add none.
RAUM_WORTE = {
    "eltern": ["Schlafzimmer"], "schlafen": ["Schlafzimmer"], "schlafzimmer": ["Schlafzimmer"],
    "bad": ["Bad"], "elternbad": ["Bad"], "kinderbad": ["Bad"],
    "kind": ["Kinderzimmer"],
    "wc": ["Gäste-WC"],
    "buero": ["Arbeitszimmer"],
    "hwr_htr": ["HWR"],
    "ankleide": ["Ankleide"],
    "gast": ["Gästezimmer"],
    "speisekammer": ["Speisekammer"],
    "kueche": ["Küche"], "kochen": ["Küche"],
    "wohnen": ["Wohnen"], "essen": ["Essen"],
    "wohnen_essen": ["Wohnen", "Essen"],
    "wohnen_essen_kochen": ["Wohnen", "Essen", "Küche"],
    "essen_kochen": ["Essen", "Küche"], "kueche_essen": ["Essen", "Küche"],
    "abstell": ["storage"],
    "garage": ["garage"], "carport": ["carport"], "garage_carport": ["garage", "carport"],
    "hobbyraum": ["hobby_room"],
}

# Fixed order for the text (the catalogue treats it as a set).
WORTE = ["Bad", "Schlafzimmer", "Kinderzimmer", "Ankleide", "Gästezimmer", "Arbeitszimmer",
         "Gäste-WC", "Wohnen", "Essen", "Küche", "Speisekammer", "HWR", "storage",
         "hobby_room", "garage", "carport", "balcony", "roof_terrace"]

# Drawn elements that are catalogue words as well.
ELEMENT_WORTE = {"balcony": "balcony", "roof_terrace": "roof_terrace"}


def _zeile(raeume, house_type, ebenen, sha, element_typen=(), du_wc_unten=False):
    """raeume: list of (room_id, room_ids) for every drawn room area.
    du_wc_unten: a DU-WC on the ground floor -- the import counted it as
    Gaeste-WC (112 of 114 such houses in the live list)."""
    worte = set()
    for room_id, room_ids in raeume:
        for rid in dict.fromkeys([room_id, *(room_ids or [])]):
            worte.update(RAUM_WORTE.get(rid, []))
    if du_wc_unten:
        worte.add("Gäste-WC")
    for typ in element_typen:
        if typ in ELEMENT_WORTE:
            worte.add(ELEMENT_WORTE[typ])
    return {
        "haustyp": HAUSTYPEN.get(house_type or "", "Sonstige"),
        "geschosse": len(ebenen),
        "keller": 1 if "basement" in ebenen else 0,
        "raeume": len(raeume),
        "qualitaet": "geprüft",
        "ausstattung": ", ".join(w for w in WORTE if w in worte),
        "schlafzimmer": sum(1 for rid, _ in raeume if rid in ("eltern", "schlafen", "schlafzimmer")),
        "kinderzimmer": sum(1 for rid, ids in raeume if rid == "kind" or "kind" in (ids or [])),
        "baeder": sum(1 for rid, _ in raeume if rid == "bad"),
        "hash": (sha or "")[:12] or None,
    }


def zeile_aus_dataset(record):
    """From a data/simplifier-v2/dataset.json project record."""
    raeume = [(rm.get("room_id"), rm.get("room_ids"))
              for f in record.get("floors") or [] for rm in f.get("rooms") or []]
    ebenen = [f.get("floor_level") for f in record.get("floors") or []]
    elemente = {e.get("type") for f in record.get("floors") or [] for e in f.get("elements") or []}
    du_wc_unten = any(rm.get("room_id") == "du_wc" for f in record.get("floors") or []
                      if f.get("floor_level") == "groundfloor" for rm in f.get("rooms") or [])
    return _zeile(raeume, record.get("house_type"), ebenen, record.get("annotation_sha256"),
                  elemente, du_wc_unten)


def ist_hang(ann):
    """Bauen am Hang: Aussenflaechen auf ZWEI Ebenen (unten Terrasse am UG,
    oben Zugang am EG) -- dieselbe Regel, nach der der Bau das Hanggelaende
    anlegt (build-simplifier-render-plan.gelaende_aus_flaechen)."""
    ebenen = {a.get("floor_level") for a in ann.get("exterior_areas") or [] if a.get("floor_level")}
    return len(ebenen) >= 2


def zeile_aus_projekt(ordner, blender_pfad=None):
    """From a floorplan-simplifier project folder (annotations.json + data.json)."""
    with open(os.path.join(ordner, "annotations.json"), encoding="utf-8-sig") as f:
        ann = json.load(f)
    try:
        with open(os.path.join(ordner, "data.json"), encoding="utf-8-sig") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    raeume = [(a.get("room_id"), a.get("room_ids")) for a in ann.get("annotations") or []
              if len(a.get("points") or []) >= 3]
    ebenen = sorted({a.get("floor_level") for a in ann.get("annotations") or [] if a.get("floor_level")})
    # house_type: the id prefix is what the import used (data.json says "2-storey" etc.)
    pid = ann.get("project_id") or os.path.basename(os.path.normpath(ordner))
    typ = next((t for t in ("twostorey_cellar", "twostorey", "onehalfstorey", "bungalow")
                if pid.startswith(t)), data.get("house_type") or "other")
    with open(os.path.join(ordner, "annotations.json"), "rb") as f:
        import hashlib
        sha = hashlib.sha256(f.read()).hexdigest()
    elemente = {e.get("type") for e in ann.get("elements") or []}
    du_wc_unten = any(a.get("room_id") == "du_wc" and a.get("floor_level") == "groundfloor"
                      for a in ann.get("annotations") or [])
    zeile = _zeile(raeume, typ, ebenen, sha, elemente, du_wc_unten)
    # Doppelhaushaelfte (doppelhaushaelfte-v1, Rainer 2026-10-23: "als haustyp
    # durchsuchbar"): eigener Haustyp; die Geschosse stehen in `geschosse`.
    if (ann.get("doppelhaus") or {}).get("trennwand") in ("north", "east", "south", "west"):
        zeile["haustyp"] = "Doppelhaushälfte"
    # Bauen am Hang (Rainer, 2026-10-25: als Kategorie im Katalog). Eine
    # Doppelhaushaelfte am Hang bleibt Doppelhaushaelfte.
    elif ist_hang(ann):
        zeile["haustyp"] = "Bauen am Hang"
    zeile["plan_id"] = pid
    zeile["blender_pfade"] = blender_pfad.replace("\\", "/") if blender_pfad else ""
    return zeile

"""Grundriss-Bilder fuer den Katalog (katalog-grundriss-bild-v1).

Rainer, 2026-11-07: "how about the icons swapping for the floorplans in the
grundriss katalog?" -- auf Karten ohne Render steht bisher ein Haus-Symbol.
Die Raumkonzept-PNGs des Simplifiers taugen dafuer nicht (kaputte Umlaute,
winzige Namen). Rainer: "Yes, draw them" -- also hier selbst gezeichnet, aus der
Annotation: Raeume farbig nach Art, Aussenumriss, Fenster, Tueren, Treppe, Name
mit Umlauten und m2, alle Geschosse im selben Massstab nebeneinander.

Ausgabe: <ziel>/<plan>-grundriss.png -- der Katalog ordnet ein Mediathek-Bild
ueber das Praefix "<plan>-" seinem Haus zu. Nur lesen in den Projekten; schreibt
nur in den Zielordner. Hochladen ist ein eigener Schritt (Regel 10, Rainers OK).

Aufruf: python katalog-grundriss-bilder.py <zielordner> <plan> [plan ...]
"""

import importlib.util
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("FLOORPLAN_WORKBENCH_DATA_DIR", os.path.join(HERE, ".."))
_spec = importlib.util.spec_from_file_location("kmatrix_bild", os.path.join(HERE, "konfigurator-matrix.py"))
km = importlib.util.module_from_spec(_spec)
_argv, sys.argv = sys.argv, ["x"]
_spec.loader.exec_module(km)
sys.argv = _argv

REIHENFOLGE = ["basement", "groundfloor", "upperfloor", "staffelgeschoss", "attic"]
NAMEN = {"basement": "Untergeschoss", "groundfloor": "Erdgeschoss", "upperfloor": "Obergeschoss",
         "staffelgeschoss": "Staffelgeschoss", "attic": "Dachgeschoss"}
PX_M = 70            # Pixel je Meter
RAND = 50
KOPF = 80
BREITE_MAX = 2400
DRAUSSEN = ("terrasse", "balkon", "loggia", "garten")

FARBEN = [  # (Stichwoerter, Fuellung)
    (("luftraum", "treppenöffnung", "treppenoeffnung"), (246, 246, 246)),
    (("bad", "wc", "dusch"), (214, 232, 244)),
    (("wohnen", "essen", "kochen", "küche", "kueche"), (218, 236, 220)),
    (("eltern", "schlafen"), (230, 224, 242)),
    (("kind",), (252, 240, 196)),
    (("büro", "buero", "arbeit", "gast", "zimmer", "hobby", "fitness"), (245, 228, 208)),
    (("ankleide",), (226, 220, 232)),
    (("flur", "diele", "galerie", "treppenhaus"), (238, 234, 226)),
    (("garage", "carport"), (225, 225, 225)),
]
GRUND = (236, 236, 232)
LINIE = (60, 60, 60)
FENSTER = (0, 142, 230)
TUER = (211, 47, 47)
TREPPE = (200, 186, 160)


def farbe(label):
    t = label.lower()
    for worte, f in FARBEN:
        if any(w in t for w in worte):
            return f
    return GRUND


def schrift(groesse, fett=False):
    for name in (("segoeuib.ttf", "arialbd.ttf") if fett else ("segoeui.ttf", "arial.ttf")) + ("DejaVuSans.ttf",):
        try:
            return ImageFont.truetype(name, groesse)
        except OSError:
            continue
    return ImageFont.load_default()


def im_polygon(x, y, pg):
    drin = False
    for i in range(len(pg)):
        x1, y1 = pg[i - 1]
        x2, y2 = pg[i]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            drin = not drin
    return drin


def abstand_rand(x, y, pg):
    best = float("inf")
    for i in range(len(pg)):
        (ax, ay), (bx, by) = pg[i - 1], pg[i]
        dx, dy = bx - ax, by - ay
        lq = dx * dx + dy * dy or 1e-9
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / lq))
        best = min(best, math.hypot(x - (ax + t * dx), y - (ay + t * dy)))
    return best


def beschriftungspunkt(pg):
    """Punkt im Raum mit dem groessten Abstand zum Rand (auch fuer L-Formen)."""
    xs, ys = [p[0] for p in pg], [p[1] for p in pg]
    best, bx, by = -1.0, sum(xs) / len(xs), sum(ys) / len(ys)
    for i in range(1, 24):
        for j in range(1, 24):
            x = min(xs) + (max(xs) - min(xs)) * i / 24
            y = min(ys) + (max(ys) - min(ys)) * j / 24
            if im_polygon(x, y, pg):
                d = abstand_rand(x, y, pg)
                if d > best:
                    best, bx, by = d, x, y
    return bx, by, max(best, 1.0)


def text_einpassen(stift, zeilen, max_b, max_h, start):
    groesse = start
    while groesse >= 11:
        f = schrift(groesse, fett=True)
        fk = schrift(max(10, int(groesse * 0.8)))
        b = max(stift.textlength(z, font=f if i == 0 else fk) for i, z in enumerate(zeilen))
        h = groesse * 1.25 * len(zeilen)
        if b <= max_b and h <= max_h:
            return f, fk, groesse
        groesse -= 2
    return schrift(11, True), schrift(10), 11


def geschoss_daten(plan):
    projekt = os.path.join(km.PROJECTS, plan)
    import json
    with open(os.path.join(projekt, "annotations.json"), encoding="utf-8") as f:
        d = json.load(f)
    gemischt = km.hausdaten.hausdaten(projekt)
    skalen = gemischt["floor_scale"] or {}
    d = dict(d, annotation_space=gemischt["annotation_space"])
    if not skalen:
        return []
    raeume = [a for a in d.get("annotations") or [] if len(a.get("points") or []) >= 3]
    ebenen = [e for e in REIHENFOLGE if any(a.get("floor_level") == e for a in raeume)]
    umrisse = d.get("outer_outlines") if isinstance(d.get("outer_outlines"), dict) else {}
    if not umrisse and len(d.get("outer_outline") or []) >= 3:
        umrisse = {d.get("outer_outline_floor") or "groundfloor": d["outer_outline"]}
    aus = []
    for e in ebenen:
        s = skalen.get(e) or next(iter(skalen.values()))
        v = km.bildverhaeltnis(projekt, e, d)
        if not v:
            continue
        m = lambda p: (p["x"] * s, p["y"] * s * v)  # noqa: E731 -- Meter, y nach unten
        aus.append({
            "ebene": e,
            "raeume": [(km.label_reparieren(a.get("label") or ""), [m(p) for p in a["points"]])
                       for a in raeume if a.get("floor_level") == e
                       and not any(w in (a.get("label") or "").lower() for w in DRAUSSEN)],
            "umriss": [m(p) for p in umrisse.get(e) or []] if len(umrisse.get(e) or []) >= 3 else None,
            "elemente": [(x.get("type"), [m(p) for p in x.get("points") or []], x.get("width_m"))
                         for x in d.get("elements") or [] if x.get("floor_level") == e],
        })
    return aus


def flaeche_m2(pg):
    return abs(sum(pg[i][0] * pg[(i + 1) % len(pg)][1] - pg[(i + 1) % len(pg)][0] * pg[i][1]
                   for i in range(len(pg)))) / 2


def geschoss_bild(g):
    punkte = [p for _, pg in g["raeume"] for p in pg] + (g["umriss"] or [])
    x0, y0 = min(p[0] for p in punkte), min(p[1] for p in punkte)
    x1, y1 = max(p[0] for p in punkte), max(p[1] for p in punkte)
    w, h = int((x1 - x0) * PX_M) + 2 * RAND, int((y1 - y0) * PX_M) + 2 * RAND
    bild = Image.new("RGB", (w, h), "white")
    st = ImageDraw.Draw(bild)
    px = lambda p: (RAND + (p[0] - x0) * PX_M, RAND + (p[1] - y0) * PX_M)  # noqa: E731
    for label, pg in g["raeume"]:
        st.polygon([px(p) for p in pg], fill=farbe(label), outline=(150, 150, 145))
    for typ, pts, breite in g["elemente"]:
        if typ == "stairs" and len(pts) >= 2:
            st.line([px(p) for p in pts], fill=TREPPE, width=int((breite or 0.9) * PX_M), joint="curve")
    if g["umriss"]:
        st.line([px(p) for p in g["umriss"] + g["umriss"][:1]], fill=LINIE, width=7, joint="curve")
    for typ, pts, _ in g["elemente"]:
        if len(pts) < 2:
            continue
        if typ == "window":
            st.line([px(pts[0]), px(pts[1])], fill=FENSTER, width=9)
        elif typ == "door":
            st.line([px(pts[0]), px(pts[1])], fill=TUER, width=7)
    for label, pg in g["raeume"]:
        if not label:
            continue
        cx, cy, r = beschriftungspunkt(pg)
        teile = [t.strip() for t in label.split("/")]
        zeilen = [label] if len(label) <= 14 else teile
        if "luftraum" not in label.lower() and "treppen" not in label.lower():
            zeilen = zeilen + [f"{flaeche_m2(pg):.0f} m²".replace(".", ",")]
        xs, ys = [p[0] for p in pg], [p[1] for p in pg]
        max_b = min(2 * r, max(xs) - min(xs)) * PX_M * 0.92
        max_h = min(2 * r, max(ys) - min(ys)) * PX_M * 0.9
        f, fk, groesse = text_einpassen(st, zeilen, max_b, max_h, 30)
        mx, my = px((cx, cy))
        y = my - groesse * 1.25 * len(zeilen) / 2
        for i, z in enumerate(zeilen):
            font = f if i == 0 or (len(zeilen) > 2 and i < len(zeilen) - 1) else fk
            st.text((mx, y), z, fill=(35, 35, 35) if i < len(zeilen) - 1 or len(zeilen) == 1 else (90, 90, 90),
                    font=font, anchor="ma")
            y += groesse * 1.25
    return bild


def bauen(plan, ziel):
    geschosse = geschoss_daten(plan)
    if not geschosse:
        return None
    teile = [(g["ebene"], geschoss_bild(g)) for g in geschosse]
    hoehe = max(t.height for _, t in teile)
    breite = sum(t.width for _, t in teile) + RAND * (len(teile) - 1)
    bild = Image.new("RGB", (breite, hoehe + KOPF), "white")
    st = ImageDraw.Draw(bild)
    font = schrift(44, fett=True)
    x = 0
    for ebene, teil in teile:
        st.text((x + RAND, 24), NAMEN.get(ebene, ebene), fill=(40, 40, 40), font=font)
        bild.paste(teil, (x, KOPF))
        x += teil.width + RAND
    if bild.width > BREITE_MAX:
        f = BREITE_MAX / bild.width
        bild = bild.resize((BREITE_MAX, round(bild.height * f)), Image.LANCZOS)
    os.makedirs(ziel, exist_ok=True)
    pfad = os.path.join(ziel, f"{plan}-grundriss.png")
    bild.save(pfad, optimize=True)
    return pfad


def main():
    if len(sys.argv) < 3:
        sys.exit("Aufruf: katalog-grundriss-bilder.py <zielordner> <plan> [plan ...]")
    ziel = sys.argv[1]
    for plan in sys.argv[2:]:
        try:
            print(plan, bauen(plan, ziel) or "nichts zu zeichnen")
        except (OSError, ValueError, KeyError) as fehler:
            print(plan, "FEHLER", fehler)


if __name__ == "__main__":
    main()

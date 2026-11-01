"""Staffelgeschoss: das kleinere oberste Geschoss und das Dach darunter.

STAFFELGESCHOSS-001, Rainer 2026-11-01, twostorey_xvit. Nur reine Geometrie,
damit Plan-Builder und beide Renderer dasselbe sehen. Die freie Decke des
Geschosses darunter ist Kies, die gezeichnete Dachterrasse hat einen Belag,
und rundherum laeuft eine Attika -- ausser dort, wo die Staffelwand buendig
auf der Aussenwand steht.
"""
import math

EBENE = "staffelgeschoss"
ATTIKA_HOEHE_M = 1.0    # absturzsichernd, wie BRUESTUNG_H in render-exterior.py
WAND_TOL_MM = 300.0     # Staffelwand und Aussenwand gelten als uebereinander
MIN_STUECK_MM = 200.0


def _aussen(waende):
    return [w for w in waende if w.get("wall_type") == "exterior"]


def umriss(waende, tol_mm=400.0):
    """Die Ecken des Wandzugs; ist er nicht geschlossen, die Huellbox."""
    rest = [(list(w["start_mm"]), list(w["end_mm"])) for w in waende]
    if not rest:
        return []
    a, b = rest.pop(0)
    zug = [a, b]
    while rest:
        kx, ky = zug[-1]
        besser = None
        for i, (p, q) in enumerate(rest):
            for naechster, ende in ((p, q), (q, p)):
                d = math.hypot(naechster[0] - kx, naechster[1] - ky)
                if d <= tol_mm and (besser is None or d < besser[0]):
                    besser = (d, i, ende)
        if besser is None:
            break
        rest.pop(besser[1])
        zug.append(besser[2])
    geschlossen = len(zug) >= 4 and math.hypot(zug[-1][0] - zug[0][0], zug[-1][1] - zug[0][1]) <= tol_mm
    if not geschlossen or rest:
        xs = [p[0] for w in waende for p in (w["start_mm"], w["end_mm"])]
        ys = [p[1] for w in waende for p in (w["start_mm"], w["end_mm"])]
        return [[min(xs), min(ys)], [max(xs), min(ys)], [max(xs), max(ys)], [min(xs), max(ys)]]
    return zug[:-1]


def _frei(wand, oben):
    """Die Abschnitte [t0, t1] der Wand (in mm ab Start) ohne Staffelwand darueber."""
    ax, ay = wand["start_mm"]
    bx, by = wand["end_mm"]
    laenge = math.hypot(bx - ax, by - ay)
    if laenge < 1:
        return laenge, []
    ux, uy = (bx - ax) / laenge, (by - ay) / laenge
    belegt = []
    for w in oben:
        px, py = w["start_mm"]
        qx, qy = w["end_mm"]
        lq = math.hypot(qx - px, qy - py)
        if lq < 1:
            continue
        if abs((qx - px) * uy - (qy - py) * ux) / lq > 0.02:      # nicht parallel
            continue
        if abs((px - ax) * uy - (py - ay) * ux) > WAND_TOL_MM:    # nicht uebereinander
            continue
        t = sorted(((px - ax) * ux + (py - ay) * uy, (qx - ax) * ux + (qy - ay) * uy))
        belegt.append((max(0.0, t[0]), min(laenge, t[1])))
    frei = []
    pos = 0.0
    for t0, t1 in sorted(belegt):
        if t0 > pos:
            frei.append((pos, t0))
        pos = max(pos, t1)
    if pos < laenge:
        frei.append((pos, laenge))
    return laenge, frei


def attika_stuecke(unten, oben):
    """Die Aussenwand-Abschnitte des Geschosses darunter, die eine Attika tragen."""
    stuecke = []
    for wand in unten:
        laenge, frei = _frei(wand, oben)
        ax, ay = wand["start_mm"]
        bx, by = wand["end_mm"]
        for t0, t1 in frei:
            if t1 - t0 < MIN_STUECK_MM:
                continue
            stuecke.append({
                "start_mm": [ax + (bx - ax) * t0 / laenge, ay + (by - ay) * t0 / laenge],
                "end_mm": [ax + (bx - ax) * t1 / laenge, ay + (by - ay) * t1 / laenge],
                "thickness_mm": wand.get("thickness_mm") or 240,
            })
    return stuecke


def _innen(punkt, poly):
    x, y = punkt
    drin = False
    for i, (ax, ay) in enumerate(poly):
        bx, by = poly[(i + 1) % len(poly)]
        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
            drin = not drin
    return drin


def kies_felder(unten, oben):
    """Rechtecke der freien Dachflaeche: im Umriss darunter, ausserhalb der Staffel.

    Im Geschossbild darf unter der Staffel kein Kies liegen, sonst schliesst er
    das Treppenloch (twostorey_xvit, 2026-11-01).
    """
    xs = sorted({p[0] for p in unten + oben})
    ys = sorted({p[1] for p in unten + oben})
    felder = []
    for x0, x1 in zip(xs, xs[1:]):
        for y0, y1 in zip(ys, ys[1:]):
            mitte = ((x0 + x1) / 2, (y0 + y1) / 2)
            if _innen(mitte, unten) and not _innen(mitte, oben):
                felder.append([[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
    return felder


def plan_feld(geschosse):
    """Das Plan-Feld `staffelgeschoss`, oder None ohne Staffelgeschoss obenauf."""
    if len(geschosse) < 2 or geschosse[-1].get("level") != EBENE:
        return None
    unten = _aussen(geschosse[-2].get("walls") or [])
    oben = _aussen(geschosse[-1].get("walls") or [])
    return {
        "umriss_unten_mm": umriss(unten),
        "kies_felder_mm": kies_felder(umriss(unten), umriss(oben)),
        "terrassen_mm": [p for p in geschosse[-1].get("dachterrassen") or [] if len(p) >= 3],
        "attika": attika_stuecke(unten, oben),
    }

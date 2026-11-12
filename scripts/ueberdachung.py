"""Ueberdachte Terrasse und Balkon: Das Haus laeuft weiter, es kommt keine Platte dazu.

Plan UEBERDACHUNG-001. Rainer, 2026-10-31: "it cant look like playwood it has
to be the floor above it extended or the roof above it extended", "anything
else looks like shit". Steht ueber der Flaeche ein Geschoss, laeuft dessen Decke
weiter; sonst laeuft das Hauptdach weiter. Kein bpy hier: render-exterior.py
baut aus diesen Zahlen die Geometrie.

Polygone in `flaechen()` und `bauteile()` in Millimetern, `vereinigt()` in Metern.
"""
import math

PFOSTEN_EINZUG_MM = 120
PFOSTEN_ABSTAND_MM = 8000
VERSATZ_MM = 300
FASSADE_ABSTAND_MM = 300
PFOSTEN_BREITE_M = 0.24
FANG_M = 0.35
RASTER_M = 0.15


def feld(quelle):
    """Nur True wird weitergereicht, damit Plaene ohne Haekchen gleich bleiben."""
    aus = {"ueberdacht": True} if quelle.get("ueberdacht") is True else {}
    if isinstance(quelle.get("gelaender_kanten"), list):
        aus["gelaender_kanten"] = quelle["gelaender_kanten"]
    return aus


def flaechen(plan, floors):
    """Alle ueberdachten Flaechen mit Geschossindex und dem, was sie deckt."""
    ebenen = [f.get("level") for f in floors]
    oben = len(floors) - 1
    aus = []
    for area in plan.get("exterior_areas") or []:
        if area.get("ueberdacht") and area.get("type") == "terrasse":
            ebene = ebenen.index(area["level"]) if area.get("level") in ebenen else 0
            aus.append({"id": area["id"], "art": "terrasse", "ebene": ebene, "poly": area["points_mm"],
                        "traeger": "dach" if ebene == oben else "decke"})
    for ebene, storey in enumerate(floors):
        for balkon in storey.get("balconies") or []:
            if balkon.get("ueberdacht") and len(balkon.get("polygon_mm") or []) >= 3:
                aus.append({"id": balkon["id"], "art": "balkon", "ebene": ebene, "poly": balkon["polygon_mm"],
                            "traeger": "dach" if ebene == oben else "decke"})
    return aus


def _abstand(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    span = dx * dx + dy * dy
    t = 0.0 if not span else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / span))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def _an_fassade(p, fassaden):
    return any(_abstand(p, a, b) < FASSADE_ABSTAND_MM for a, b in fassaden)


def _kreuz(a, b, c):
    return (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])


def _flaeche(punkte):
    return sum(punkte[i][0] * punkte[(i + 1) % len(punkte)][1]
               - punkte[(i + 1) % len(punkte)][0] * punkte[i][1] for i in range(len(punkte))) / 2


def _bereinigt(poly, eps=1.0):
    """Gegen den Uhrzeigersinn, ohne doppelte Punkte und ohne Punkte mitten in einer Kante."""
    punkte = [tuple(map(float, p)) for p in poly]
    if _flaeche(punkte) < 0:
        punkte.reverse()
    while True:
        n = len(punkte)
        weg = next((i for i in range(n)
                    if math.dist(punkte[i], punkte[(i + 1) % n]) < eps
                    or abs(_kreuz(punkte[i - 1], punkte[i], punkte[(i + 1) % n])) < eps), None)
        if weg is None or n <= 3:
            return punkte
        del punkte[weg]


def _innen(x, y, poly):
    drin = False
    for i in range(len(poly)):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % len(poly)]
        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
            drin = not drin
    return drin


def _raster(werte, fest):
    """Werte auf feste Linien fangen, nahe Werte zu einem zusammenziehen."""
    abbildung = {}
    linien = sorted(fest)
    for wert in sorted(werte):
        naechste = min(linien, key=lambda z: abs(z - wert), default=None)
        if naechste is not None and abs(naechste - wert) <= FANG_M:
            abbildung[wert] = naechste
    frei = [w for w in sorted(werte) if w not in abbildung]
    for wert in frei:
        nah = next((z for z in linien if abs(z - wert) <= RASTER_M), None)
        if nah is None:
            linien.append(wert)
            nah = wert
        abbildung[wert] = nah
    return abbildung


def vereinigt(fuss, zusatz):
    """Grundriss des Dachs: Hausumriss plus ueberdachte Flaechen, rechtwinklig, in Metern."""
    x_auf = _raster({p[0] for f in zusatz for p in f}, {p[0] for p in fuss})
    y_auf = _raster({p[1] for f in zusatz for p in f}, {p[1] for p in fuss})
    teile = [[tuple(p) for p in fuss]] + [[(x_auf[p[0]], y_auf[p[1]]) for p in f] for f in zusatz]
    xs = sorted({p[0] for t in teile for p in t})
    ys = sorted({p[1] for t in teile for p in t})
    voll = {(i, j) for i in range(len(xs) - 1) for j in range(len(ys) - 1)
            if any(_innen((xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2, t) for t in teile)}
    kanten = {}
    for i, j in voll:
        a, b, c, d = (xs[i], ys[j]), (xs[i + 1], ys[j]), (xs[i + 1], ys[j + 1]), (xs[i], ys[j + 1])
        if (i, j - 1) not in voll:
            kanten[a] = b
        if (i + 1, j) not in voll:
            kanten[b] = c
        if (i, j + 1) not in voll:
            kanten[c] = d
        if (i - 1, j) not in voll:
            kanten[d] = a
    schleifen = []
    while kanten:
        start = next(iter(kanten))
        schleife = [start]
        p = kanten.pop(start)
        while p != start and p in kanten:
            schleife.append(p)
            p = kanten.pop(p)
        schleifen.append(schleife)
    return _bereinigt(max(schleifen, key=lambda s: abs(_flaeche(s))), eps=1e-6)


def _versetzt(punkte, versatz):
    """Jede Kante i um versatz[i] nach aussen schieben, die Ecken neu schneiden."""
    n = len(punkte)
    neu = []
    for i in range(n):
        vor = (i - 1) % n
        a0, a1 = punkte[vor], punkte[i]
        b0, b1 = punkte[i], punkte[(i + 1) % n]
        la, lb = math.dist(a0, a1), math.dist(b0, b1)
        ua = ((a1[0] - a0[0]) / la, (a1[1] - a0[1]) / la)
        ub = ((b1[0] - b0[0]) / lb, (b1[1] - b0[1]) / lb)
        # Aussen liegt rechts der Laufrichtung: das Polygon laeuft gegen den Uhrzeigersinn.
        na, nb = (ua[1], -ua[0]), (ub[1], -ub[0])
        pa = (a1[0] + na[0] * versatz[vor], a1[1] + na[1] * versatz[vor])
        pb = (b0[0] + nb[0] * versatz[i], b0[1] + nb[1] * versatz[i])
        nenner = ua[0] * ub[1] - ua[1] * ub[0]
        t = ((pb[0] - pa[0]) * ub[1] - (pb[1] - pa[1]) * ub[0]) / nenner
        neu.append((pa[0] + ua[0] * t, pa[1] + ua[1] * t))
    return neu


def pfosten(poly, fassaden):
    """Stuetzen an den aeusseren Ecken, nie an der Fassade. `fassaden` sind Wandstrecken."""
    # Ein kleiner Versatz in der Zeichnung ist keine Ecke (Rainer: "too manyposts").
    punkte = _bereinigt(poly)
    punkte = _bereinigt([p for i, p in enumerate(punkte)
                         if len(punkte) <= 4 or math.dist(p, punkte[i - 1]) >= VERSATZ_MM])
    punkte = [p for i, p in enumerate(punkte)
              if len(punkte) <= 3 or abs(_kreuz(punkte[i - 1], p, punkte[(i + 1) % len(punkte)]))
              >= 0.1 * math.dist(punkte[i - 1], p) * math.dist(p, punkte[(i + 1) % len(punkte)])]
    n = len(punkte)
    frei = []
    for i in range(n):
        a, b = punkte[i], punkte[(i + 1) % n]
        frei.append(not _an_fassade(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), fassaden))
    innen = _versetzt(punkte, [-PFOSTEN_EINZUG_MM if f else 0 for f in frei])
    stuetzen = []
    for i in range(n):
        if not frei[i]:
            continue
        a, b = innen[i], innen[(i + 1) % n]
        felder = max(1, math.ceil(math.dist(a, b) / PFOSTEN_ABSTAND_MM))
        for k in range(felder + 1):
            ecke_a = k == 0 and _kreuz(punkte[i - 1], punkte[i], punkte[(i + 1) % n]) < 0
            ecke_b = k == felder and _kreuz(punkte[i], punkte[(i + 1) % n], punkte[(i + 2) % n]) < 0
            if ecke_a or ecke_b:
                continue                      # Innenecke einer L-Form: dort traegt nichts
            p = (a[0] + (b[0] - a[0]) * k / felder, a[1] + (b[1] - a[1]) * k / felder)
            if not _an_fassade(p, fassaden) and all(math.dist(p, q) > 10 for q in stuetzen):
                stuetzen.append(p)
    return stuetzen

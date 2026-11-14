"""Teppiche von den echten Waenden fernhalten.

Rainer, 2026-10-09: "and you still haven fixex the rugs going underneth the
walls". Der Fix vom 2026-09-07 hielt 200 mm Abstand zur RAUMKANTE und nahm an,
die Raumkante liege auf der Wandmitte. Bei bungalow_040_36 liegt sie auf der
AUSSENSEITE der Aussenwand (Wand-Mitte x = 14770 bei 240 mm Dicke, Raumkante
x = 14890): Innenkante 14650, Teppichkante 14690 -- 40 mm unter der Wand, im
Wohnbereich an drei Seiten.

Darum hier gegen die Waende selbst: jede achsparallele Wand ist ein Streifen
(halbe Dicke + Abstand zu jeder Seite). Schneidet der Teppich hinein, wird
die Kante gekuerzt, die am wenigsten Flaeche kostet. Schraege Waende werden
uebersprungen -- ihr Rechteck waere viel zu gross; dort bleibt die
bestehende Polygon-Pruefung.

Alles in METERN, wie im Renderer. Ohne bpy, damit es testbar ist.
"""

ABSTAND_M = 0.05


def wand_streifen(waende_mm, abstand_m=ABSTAND_M):
    """Achsparallele Waende als Rechtecke (x0, y0, x1, y1) in Metern."""
    streifen = []
    for wand in waende_mm:
        (sx, sy), (ex, ey) = wand["start_mm"], wand["end_mm"]
        if abs(sx - ex) > 1.0 and abs(sy - ey) > 1.0:
            continue  # schraeg
        halb = (wand.get("thickness_mm") or 0) / 2000.0 + abstand_m
        streifen.append((min(sx, ex) / 1000.0 - halb, min(sy, ey) / 1000.0 - halb,
                         max(sx, ex) / 1000.0 + halb, max(sy, ey) / 1000.0 + halb))
    return streifen


_EPS = 1e-6  # Rundung: eine Kante genau AUF dem Streifen ist kein Treffer


def _ueberlappt(a, b):
    return (a[0] < b[2] - _EPS and b[0] < a[2] - _EPS
            and a[1] < b[3] - _EPS and b[1] < a[3] - _EPS)


def von_waenden_weg(tx, ty, breite, tiefe, streifen):
    """Rechteck (Mitte, Breite, Tiefe) so kuerzen, dass es keinen Streifen beruehrt.

    Gibt (tx, ty, breite, tiefe) zurueck; kann auf 0 schrumpfen.
    """
    r = [tx - breite / 2, ty - tiefe / 2, tx + breite / 2, ty + tiefe / 2]
    for _ in range(4 * len(streifen) + 4):
        treffer = next((s for s in streifen if _ueberlappt(r, s)), None)
        if treffer is None:
            break
        b, t = r[2] - r[0], r[3] - r[1]
        moeglich = []
        # Jede Kante auf die Wandseite zurueckziehen; Kosten = verlorene Flaeche.
        if treffer[0] > r[0]:
            moeglich.append(((r[2] - treffer[0]) * t, 2, treffer[0]))   # rechts kuerzen
        if treffer[2] < r[2]:
            moeglich.append(((treffer[2] - r[0]) * t, 0, treffer[2]))   # links kuerzen
        if treffer[1] > r[1]:
            moeglich.append(((r[3] - treffer[1]) * b, 3, treffer[1]))   # unten kuerzen
        if treffer[3] < r[3]:
            moeglich.append(((treffer[3] - r[1]) * b, 1, treffer[3]))   # oben kuerzen
        if not moeglich:
            return tx, ty, 0.0, 0.0   # die Wand ueberdeckt den ganzen Teppich
        _, seite, wert = min(moeglich)
        r[seite] = wert
        if r[2] - r[0] <= 0 or r[3] - r[1] <= 0:
            return tx, ty, 0.0, 0.0
    return (r[0] + r[2]) / 2, (r[1] + r[3]) / 2, r[2] - r[0], r[3] - r[1]

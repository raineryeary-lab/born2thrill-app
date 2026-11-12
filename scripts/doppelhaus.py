"""Doppelhaushaelfte -- die reine Rechnung (doppelhaushaelfte-v1).

Rainer, 2026-10-23, onehalfstorey_046: "could we create a new class of house
this is a doppelhaushälfte". Keine neue Geschossklasse: eine Markierung auf
dem Haustyp, `doppelhaus: {"trennwand": "east"}` neben der Zeichnung. Die
Trennwand ist die Aussenwand dieser Seite -- zweischalige Haustrennwand,
365 mm, ohne Oeffnungen. Aussen steht die gespiegelte Nachbarhaelfte, das
Dach laeuft quer zur Trennwand ueber beide Haelften.

Plan-System: Millimeter, y nach oben (Nord = groesstes y), Ost = groesstes x.
Kein bpy hier.
"""

SEITEN = ("north", "east", "south", "west")
DICKE_MM = 365
TOL_MM = 300.0


def normalisieren(wert):
    """{"trennwand": <Seite>} oder None."""
    if isinstance(wert, dict) and wert.get("trennwand") in SEITEN:
        return {"trennwand": wert["trennwand"]}
    return None


def _bbox(waende):
    xs = [c for w in waende for c in (w["start_mm"][0], w["end_mm"][0])]
    ys = [c for w in waende for c in (w["start_mm"][1], w["end_mm"][1])]
    return min(xs), max(xs), min(ys), max(ys)


def _auf_seite(w, seite, bbox, tol=TOL_MM):
    x0, x1, y0, y1 = bbox
    (sx, sy), (ex, ey) = w["start_mm"], w["end_mm"]
    if seite in ("east", "west"):
        ziel = x1 if seite == "east" else x0
        return abs(sx - ex) < tol and abs((sx + ex) / 2 - ziel) < tol
    ziel = y1 if seite == "north" else y0
    return abs(sy - ey) < tol and abs((sy + ey) / 2 - ziel) < tol


def trennwand_markieren(waende, oeffnungen, seite):
    """Die Aussenwaende dieser Seite werden Trennwand (365 mm, Typ bleibt exterior).

    Zurueck: die Ids der Oeffnungen, die in einer Trennwand stehen -- eine
    Haustrennwand hat keine, gemeldet statt still entfernt.
    """
    aussen = [w for w in waende if w.get("wall_type") == "exterior"]
    if not aussen or seite not in SEITEN:
        return []
    bbox = _bbox(aussen)
    ids = set()
    for w in aussen:
        if _auf_seite(w, seite, bbox):
            w["trennwand"] = True
            w["thickness_mm"] = DICKE_MM
            ids.add(w.get("id"))
    return [o.get("id") for o in oeffnungen or [] if o.get("wall_id") in ids]


def ebene_mm(waende, seite):
    """Lage der Spiegelebene: Mitte der Trennwand (x fuer Ost/West, y fuer Nord/Sued)."""
    trenn = [w for w in waende if w.get("trennwand")]
    if not trenn:
        return None
    i = 0 if seite in ("east", "west") else 1
    werte = [c for w in trenn for c in (w["start_mm"][i], w["end_mm"][i])]
    return round(sum(werte) / len(werte), 1)


def dachachse(seite):
    """First quer zur Trennwand: das Dach laeuft ueber beide Haelften."""
    return "x" if seite in ("east", "west") else "y"


def kamera_seite(seite):
    """Die Seite der Trennwand in der Schreibweise der Aussenkamera."""
    return {"east": "+x", "west": "-x", "north": "+y", "south": "-y"}[seite]

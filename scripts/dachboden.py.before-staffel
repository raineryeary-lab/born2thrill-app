"""Bungalow mit Dachboden als Ausbaureserve -- die reine Rechnung.

Plan: plans/dachboden-ausbaureserve-v1.md. Rainer, 2026-10-23,
bungalow_generationat: "this one doesn't have a 2 geschoss but just an attic
with dachschraegen no walls as ausbaureserve".

Die gezeichnete Ebene `attic` ist KEIN Geschoss. Nichts darauf wird als Raum
oder Wand gebaut; ihre Fenster sitzen in den Giebeldreiecken des steilen
Satteldachs, das direkt auf dem Erdgeschoss sitzt (kein Kniestock).

Kein bpy hier: build-simplifier-render-plan.py und render-exterior.py rechnen
damit.
"""

import math

EBENE = "attic"
NEIGUNG_GRAD = 40.0     # wie der 1,5-Geschosser (anderthalb.NEIGUNG_GRAD)
RAND_M = 0.25           # Abstand Fensteroberkante -> Dachschraege
MIN_HOEHE_M = 0.5       # darunter ist es kein Fenster mehr


# DG-MIT-KNIESTOCK-001 (Rainer, 2026-10-24): ein Dachgeschoss MIT Wohnraeumen
# ist ein Geschoss (other_vito: Hobby; die 1,5-Geschosser aus dem Katalog:
# Kind/Eltern/Bad). Ausbaureserve ist es nur, wenn dort nichts Bewohnbares
# gezeichnet ist (GenerationAt: Luftraum, Abstellraum).
NICHT_WOHNRAUM = ("luftraum", "abstell", "dachboden", "speicher", "spitzboden",
                  "ausbau", "technik", "flur")
REIHE = {"basement": 0, "groundfloor": 1, "upperfloor": 2, "attic": 3}


def geschoss_reihenfolge(ebenen):
    """Ebenen von unten nach oben: KG, EG, OG, DG.

    Bis 2026-10-24 sortierte der Plan-Builder alphabetisch. EG/OG kamen
    zufaellig richtig heraus, `attic` aber VOR `groundfloor` -- die
    1,5-Geschosser mit DG standen kopfueber (DG als unterstes Geschoss).
    """
    return sorted({e for e in ebenen if e}, key=lambda e: (REIHE.get(e, 9), e))


def ist_ausbaureserve(raeume):
    """Nur Luftraum/Abstell/Speicher/... (und hoechstens ein Flur) -> Dachboden."""
    def text(r):
        return " ".join([str(x) for x in (r.get("room_ids") or [])] + [str(r.get("label") or "")]).lower()
    return all(any(k in text(r) for k in NICHT_WOHNRAUM) for r in raeume)


def abspalten(annotations):
    """Die Dachboden-Ebene aus der Zeichnung herausnehmen.

    Danach sieht alles Weitere einen Bungalow: keine Raeume, Fenster oder
    Treppen der Ebene `attic` in `annotations`/`elements`. Was gebraucht wird,
    steht unter `_dachboden`. Beide Stile bekommen das Satteldach -- ein
    Dachboden gibt es nur unter einem geneigten Dach.

    True, wenn abgespalten wurde. Ohne `attic` (oder nur `attic`) bleibt
    alles unveraendert.
    """
    raeume = annotations.get("annotations") or []
    elemente = annotations.get("elements") or []
    ebenen = {x.get("floor_level") for x in raeume + elemente if x.get("floor_level")}
    if EBENE not in ebenen or not (ebenen - {EBENE}):
        return False
    if not ist_ausbaureserve([x for x in raeume if x.get("floor_level") == EBENE]):
        return False
    annotations["_dachboden"] = {
        "level": EBENE,
        "raeume": [x for x in raeume if x.get("floor_level") == EBENE],
        "fenster": [e for e in elemente
                    if e.get("floor_level") == EBENE and e.get("type") == "window"],
    }
    annotations["annotations"] = [x for x in raeume if x.get("floor_level") != EBENE]
    annotations["elements"] = [e for e in elemente if e.get("floor_level") != EBENE]
    for stil in ("modern", "classic"):
        annotations["roof_type_%s" % stil] = "satteldach"
        annotations["roof_type_%s_herkunft" % stil] = "dachboden"
    return True


def geschoss_ebenen(ebenen, raeume=None):
    """Die Ebenen, die Geschosse sind: `attic` nicht, sobald es eine andere gibt.

    go.py zaehlte sonst den Dachboden mit und baute mit --floors 0,1
    (bungalow_generationat, 2026-10-23).
    """
    ebenen = {e for e in ebenen if e}
    wohn_dg = raeume is not None and not ist_ausbaureserve(
        [r for r in raeume if r.get("floor_level") == EBENE])
    if EBENE in ebenen and ebenen - {EBENE} and not wohn_dg:
        ebenen.discard(EBENE)
    return geschoss_reihenfolge(ebenen)


def fenster_mass(element):
    """(Bruestung, Hoehe) in mm -- dieselbe Regel wie fuer Erdgeschossfenster."""
    typ = element.get("window_type")
    bruestung = element.get("sill_height_mm")
    if bruestung is None:
        bruestung = 0 if typ == "bodentief" else 900
    hoehe = 2100 - bruestung if typ == "bodentief" else 1350
    return bruestung, hoehe


def fenster_hoehe(mitte, breite, c0, c1, neigung_grad, wunsch, rand=RAND_M):
    """Wie hoch ein Giebelfenster sein darf, in Metern ueber dem Dachboden.

    Der Giebel laeuft von c0 bis c1 (Meter entlang der Giebelwand), die
    Traufen liegen an beiden Enden. An der traufnaeheren Fensterkante bleibt
    unter der Dachschraege `rand` frei. None, wenn dort kein sinnvolles
    Fenster mehr passt.
    """
    abstand = min(mitte - breite / 2 - c0, c1 - (mitte + breite / 2))
    platz = abstand * math.tan(math.radians(neigung_grad)) - rand
    if platz < MIN_HOEHE_M:
        return None
    return min(wunsch, platz)

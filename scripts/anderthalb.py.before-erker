"""1,5-Geschosser: Kniestock, steiles Dach, Zwerch-/Quergiebel -- die reine Rechnung.

Plan: plans/anderthalbgeschosser-dach-v1.md (+ Nachtrag A1). Rainer, 2026-10-20:
"the 1,5 story we have to create with kniestock and quergiebel and stuff this
is just for 1,5 story houses" -- Werte: Kniestock 1,0 m, 40 Grad, Quergiebel
mittig ein Drittel der Fassade (mind. 2,5 m), Ziergiebel 2,0 m -- und
Variante A: wo im Obergeschoss Tueren oder Fenster in der niedrigen
Traufwand stehen, steht ein Zwerchgiebel ueber ihnen, so breit wie sie es
brauchen.

Kein bpy hier: render-exterior.py baut aus diesen Zahlen die Geometrie.
Koordinaten in Metern, Plan-System (y nach oben: Nord = groesstes y).
"""

import math

KNIESTOCK_M = 1.0
NEIGUNG_GRAD = 40.0
QUER_ANTEIL = 1.0 / 3.0
GIEBEL_MIN_M = 2.5
ZIER_BREITE_M = 2.0
RAND_M = 0.5            # links und rechts neben den Oeffnungen
LUECKE_M = 1.0          # naeher beieinander -> ein gemeinsamer Giebel

SEITEN = ("north", "east", "south", "west")


def ist_anderthalb(plan):
    """1,5-Geschosser? house_type aus dem Plan, sonst das Id-Praefix."""
    typ = str(plan.get("house_type") or "").lower()
    if typ in ("1.5-storey", "onehalfstorey", "1,5-geschosser"):
        return True
    return str(plan.get("plan_id") or "").startswith("onehalfstorey")


def traufhoehe(oberstes_geschoss_z, kniestock=KNIESTOCK_M):
    """Traufe = Fussboden des obersten Geschosses + Kniestock."""
    return oberstes_geschoss_z + kniestock


def traufseiten(bbox, roof_type, along_x=None):
    """Die Seiten, an denen das Dach bis zur Traufe herunterkommt.

    Satteldach: die beiden Seiten parallel zum First (First laengs der
    langen Seite, ausser along_x ist vorgegeben). Walmdach: alle vier.
    bbox = (x0, x1, y0, y1).
    """
    if roof_type == "walmdach":
        return list(SEITEN)
    x0, x1, y0, y1 = bbox
    if along_x is None:
        along_x = (x1 - x0) >= (y1 - y0)
    return ["north", "south"] if along_x else ["east", "west"]


def seite_von_wand(start, end, bbox, tol=0.3):
    """Welche Fassade eine (achsparallele) Aussenwand ist, oder None."""
    x0, x1, y0, y1 = bbox
    (sx, sy), (ex, ey) = start, end
    if abs(sy - ey) < tol:
        y = (sy + ey) / 2
        if abs(y - y1) < tol:
            return "north"
        if abs(y - y0) < tol:
            return "south"
    if abs(sx - ex) < tol:
        x = (sx + ex) / 2
        if abs(x - x1) < tol:
            return "east"
        if abs(x - x0) < tol:
            return "west"
    return None


def _cluster(intervalle):
    """Intervalle (lo, hi) zusammenfassen, die naeher als LUECKE_M liegen."""
    out = []
    for lo, hi in sorted(intervalle):
        if out and lo - out[-1][1] < LUECKE_M:
            out[-1][1] = max(out[-1][1], hi)
        else:
            out.append([lo, hi])
    return [tuple(i) for i in out]


def _auf_mindestbreite(lo, hi, breite, grenzen):
    """Mittig auf `breite` erweitern, innerhalb der Fassadengrenzen."""
    if hi - lo >= breite:
        return lo, hi
    mitte = (lo + hi) / 2
    lo, hi = mitte - breite / 2, mitte + breite / 2
    g0, g1 = grenzen
    if lo < g0:
        hi, lo = hi + (g0 - lo), g0
    if hi > g1:
        lo, hi = lo - (hi - g1), g1
    return max(lo, g0), min(hi, g1)


def gezogene_giebel(bbox, gezeichnet, tol=0.6):
    """Im Annotator gezogene Quergiebel -> [{"seite", "lo", "hi", "grund"}].

    gezeichnet: [((ax, ay), (bx, by))] in Metern, Plan-System. Breite und Lage
    genau wie gezogen -- kein Rand, keine Mindestbreite (quergiebel-ziehen-v1,
    Rainer 2026-10-21: "we will need to be able to adjust the width").
    """
    raus = []
    for a, b in gezeichnet or []:
        seite = seite_von_wand(a, b, bbox, tol)
        if not seite:
            continue
        i = 0 if seite in ("north", "south") else 1
        lo, hi = sorted((a[i], b[i]))
        raus.append({"seite": seite, "lo": lo, "hi": hi, "grund": "gezogen"})
    return raus


def giebel(bbox, roof_type, oeffnungen, merkmale, along_x=None, kniestock=KNIESTOCK_M,
           gezeichnet=None):
    """Die Zwerch-/Quergiebel eines 1,5-Geschossers.

    oeffnungen: [(seite, mitte_entlang_m, breite_m, oberkante_ueber_fussboden_m)]
    merkmale:   [(subtype, seite)] -- aus architectural_features (gable)
    Rueckgabe:  [{"seite", "lo", "hi", "grund"}] -- lo/hi entlang der Fassade.

    1. Jede Oeffnung in einer Traufwand, die ueber den Kniestock ragt, braucht
       Wand bis ueber ihre Oberkante: Oeffnungen naeher als 1 m werden ein
       Giebel, je 0,5 m Rand, mindestens 2,5 m breit.
    2. Ein gezeichneter Giebel auf einer Traufseite OHNE solche Oeffnungen:
       mittig -- Quergiebel ein Drittel der Fassade (mind. 2,5 m),
       Ziergiebel 2,0 m. Auf einer Giebelseite (Satteldach) gibt es nichts zu
       bauen: dort steht der Giebel schon.
    """
    # Gezogene Quergiebel ersetzen die Automatik ganz (quergiebel-ziehen-v1).
    if gezeichnet:
        return gezogene_giebel(bbox, gezeichnet)
    x0, x1, y0, y1 = bbox
    traufe = traufseiten(bbox, roof_type, along_x)
    grenzen = {"north": (x0, x1), "south": (x0, x1), "east": (y0, y1), "west": (y0, y1)}
    raus = []
    for seite in traufe:
        hoch = [(m - b / 2 - RAND_M, m + b / 2 + RAND_M)
                for s, m, b, oben in oeffnungen if s == seite and oben > kniestock + 1e-6]
        if hoch:
            for lo, hi in _cluster(hoch):
                lo, hi = _auf_mindestbreite(lo, hi, GIEBEL_MIN_M, grenzen[seite])
                raus.append({"seite": seite, "lo": lo, "hi": hi, "grund": "oeffnungen"})
            continue
        for subtype, s in merkmale:
            if s != seite:
                continue
            g0, g1 = grenzen[seite]
            breite = (ZIER_BREITE_M if subtype == "ziergiebel"
                      else max(GIEBEL_MIN_M, (g1 - g0) * QUER_ANTEIL))
            lo, hi = _auf_mindestbreite((g0 + g1) / 2, (g0 + g1) / 2, breite, (g0, g1))
            raus.append({"seite": seite, "lo": lo, "hi": hi, "grund": subtype})
            break
    return raus


def zwerch_masse(lo, hi, traufe_z, wand_oben_z, neigung_grad=NEIGUNG_GRAD):
    """Hoehen eines Zwerchgiebels gleicher Neigung.

    wand_oben_z: Oberkante seiner Frontwand (volle Geschosshoehe).
    first_z:     Firsthoehe des Zwerchdachs.
    tiefe_first: wie weit hinter der Fassade sein First auf das Hauptdach trifft.
    tiefe_traufe: wie weit hinter der Fassade seine Traufe aufs Hauptdach trifft.
    """
    t = math.tan(math.radians(neigung_grad))
    first_z = wand_oben_z + (hi - lo) / 2 * t
    return {"first_z": first_z,
            "tiefe_first": (first_z - traufe_z) / t,
            "tiefe_traufe": (wand_oben_z - traufe_z) / t}


# --- Zwerchkubus (moderne Variante) -----------------------------------------
# Plan anderthalb-zwerchkubus-modern-v1, Rainer 2026-10-21: "this would
# actually be a kind of a modern form for our 1,5 story houses" -- statt des
# spitzen Zwerchgiebels ein Kasten mit Flachdach, der durch die Traufe stoesst.

ATTIKA_M = 0.30     # Flachdachpaket/Attika ueber der Frontwand-Oberkante
KUBUS_SUFFIX = "-kubus"
KUBUS_VOR_M = 0.10   # der Kubus steht so weit vor der Fassade


def kubus_masse(lo, hi, traufe_z, wand_oben_z, neigung_grad=NEIGUNG_GRAD):
    """Hoehen und Tiefen eines Zwerchkubus.

    dach_z:     Oberkante des Flachdachs (Attika).
    tiefe_wand: wo die Unterkante des Flachdachs (= wand_oben_z) aufs Hauptdach trifft.
    tiefe_dach: wo die Oberkante (dach_z) aufs Hauptdach trifft -- so weit reicht die Platte.
    """
    t = math.tan(math.radians(neigung_grad))
    dach_z = wand_oben_z + ATTIKA_M
    return {"dach_z": dach_z,
            "tiefe_wand": (wand_oben_z - traufe_z) / t,
            "tiefe_dach": (dach_z - traufe_z) / t,
            "breite": hi - lo}


def dachform_und_zwerch(ext_roof_type):
    """EXT_ROOF_TYPE -> (Dachform, Zwerchform). "satteldach-kubus" -> ("satteldach", "kubus")."""
    roof = (ext_roof_type or "").strip().lower()
    if roof.endswith(KUBUS_SUFFIX):
        return roof[:-len(KUBUS_SUFFIX)], "kubus"
    return roof, "giebel"


def ueber_dach_profil(z0, tief, wand_oben_z, tan):
    """Querschnitt (s, z) des Koerpers, der alles UEBER einer Dachflaeche wegschneidet.

    s = Abstand nach innen von der Fassade; die Dachlinie steigt von z0 an der
    Wand mit `tan`. Die Oberkante muss ueber dem ENDE der Dachlinie liegen,
    sonst kreuzt sich der Umriss und der Boolesche Schnitt gelingt nur
    teilweise (onehalfstorey_045, 2026-10-21: Giebelwaende bis 8,7 m stehen
    geblieben).
    """
    ende = z0 + tief * tan
    oben = max(wand_oben_z, ende) + 5.0
    return [(-3.0, z0 - 3.0 * tan), (tief, ende), (tief, oben), (-3.0, oben)]

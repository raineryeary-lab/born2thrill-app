"""Fensterpruefer (fenster-pruefen-v1, REGELN 40; Rainer 2026-11-12).

Zwei Pruefungen je Haus, gerechnet in den Millimetern, die der Bau baut
(build-simplifier-render-plan.py --geometry-only, Obergeschosse ueber die
Ausrichtmarken auf das Erdgeschoss gelegt):

  1. Licht: Jeder Wohn- und Schlafraum braucht Fensterflaeche (Rohbaumass
     Breite x Hoehe, wie der Bau sie setzt) von mindestens 1/8 seiner
     Grundflaeche.
  2. Flucht: Fenster uebereinanderliegender Geschosse an derselben Fassade
     sollen links, rechts oder mittig fluchten. Gemeldet wird, was FAST
     fluchtet (mehr als 2 cm, hoechstens 30 cm daneben) -- das ist fast immer
     ein Zeichenfehler; was weiter weg liegt, ist Absicht.

Nur Bericht, aendert nichts.

  python fenster-pruefen.py <plan> [<plan> ...]     Bericht auf die Konsole
  python fenster-pruefen.py --alle                  alle Haeuser -> fenster-pruefen.json
"""
import importlib.util
import json
import math
import os
import sys
import tempfile
import contextlib
import io

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECTS = os.path.abspath(os.path.join(HERE, "..", "..", "floorplan-simplifier", "projects"))
DATA = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR") or r"E:\born2thrill-local-workbench-data"
AUSGABE = os.path.join(DATA, "fenster-pruefen.json")

LICHT_ANTEIL = 1 / 8
FLUCHT_OK_MM = 30        # so genau gilt es als fluchtend (Bau-Rauschen der Ausrichtung)
FLUCHT_FAST_MM = 300     # weiter daneben ist es Absicht
FASSADE_QUER_MM = 450    # so weit duerfen die Wandlinien zweier Geschosse auseinander liegen
FASSADE_WINKEL = math.radians(5)

# Wohn- und Schlafraeume (Aufenthaltsraeume). Alles andere braucht kein Licht nach 1/8.
WOHNRAUM = ("wohnen", "essen", "kochen", "küche", "kueche", "schlafen", "eltern", "kind",
            "büro", "buero", "arbeit", "gast", "zimmer", "spiel", "hobby", "studio", "lesen")
KEIN_WOHNRAUM = ("bad", "wc", "dusche", "flur", "diele", "hwr", "htr", "abstell", "ankleide",
                 "speise", "vorrat", "technik", "treppe", "luftraum", "galerie", "garage",
                 "carport", "terrasse", "balkon", "loggia", "keller", "windfang", "garderobe")


def ist_wohnraum(name):
    n = (name or "").lower()
    # "Wohnen / Essen / Kochen / Abstellraum" bleibt Wohnraum, "Kinderbad" nicht.
    if any(k in n for k in KEIN_WOHNRAUM) and not any(k in n for k in ("wohnen", "schlafen")):
        return False
    return any(k in n for k in WOHNRAUM)


def fensterhoehe(element):
    """Dieselbe Regel wie der Bau (build-simplifier-render-plan.py, Oeffnungen)."""
    typ = element.get("window_type")
    sill = element.get("sill_height_mm")
    if sill is None:
        sill = 0 if typ == "bodentief" else 900
    return 2100 - sill if typ == "bodentief" else 1350


def punkt_im_polygon(p, poly):
    x, y = p
    drin = False
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            drin = not drin
    return drin


def polygon_flaeche(poly):
    s = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2 / 1e6


def fenster_lage(opening, wall):
    """Endpunkte des Fensters auf seiner Wand, Mitte, Richtung, Normale."""
    sx, sy = wall["start"]
    ex, ey = wall["end"]
    laenge = math.hypot(ex - sx, ey - sy) or 1.0
    ux, uy = (ex - sx) / laenge, (ey - sy) / laenge
    t = opening["position"] * laenge
    halb = opening["width"] / 2
    mitte = (sx + ux * t, sy + uy * t)
    return {
        "a": (mitte[0] - ux * halb, mitte[1] - uy * halb),
        "b": (mitte[0] + ux * halb, mitte[1] + uy * halb),
        "mitte": mitte, "u": (ux, uy), "n": (-uy, ux), "breite": opening["width"],
    }


def pruefe(geo, annotations):
    elemente = {e.get("id"): e for e in annotations.get("elements") or []}
    licht, flucht = [], []
    fenster_je_geschoss = []
    for floor in geo["floors"]:
        waende = {w["id"]: w for w in floor["walls"]}
        raeume = [r for r in floor["rooms"] if len(r.get("polygon_mm") or []) >= 3]
        glas = {r["id"]: 0.0 for r in raeume}
        anzahl = {r["id"]: 0 for r in raeume}
        liste = []
        for o in floor["openings"]:
            if o.get("opening_type") != "window" or o.get("wall_id") not in waende:
                continue
            lage = fenster_lage(o, waende[o["wall_id"]])
            hoehe = fensterhoehe(elemente.get(o.get("id")) or {})
            # Welchem Raum leuchtet es? 30 cm neben der Wandmitte, beide Seiten.
            treffer = []
            for seite in (1, -1):
                p = (lage["mitte"][0] + lage["n"][0] * 300 * seite,
                     lage["mitte"][1] + lage["n"][1] * 300 * seite)
                treffer += [r for r in raeume if punkt_im_polygon(p, r["polygon_mm"])]
            for r in treffer[:1]:
                glas[r["id"]] += lage["breite"] * hoehe / 1e6
                anzahl[r["id"]] += 1
            lage.update(id=o.get("id"), aussen=len(treffer) < 2,
                        raum=treffer[0].get("name") if treffer else "")
            liste.append(lage)
        fenster_je_geschoss.append((floor["floor_level"], liste))
        for r in raeume:
            if not ist_wohnraum(r.get("name")):
                continue
            flaeche = r.get("area_m2") or polygon_flaeche(r["polygon_mm"])
            if flaeche < 4:
                continue
            soll = flaeche * LICHT_ANTEIL
            if glas[r["id"]] + 1e-6 < soll:
                licht.append({"geschoss": floor["floor_level"], "raum": r.get("name"),
                              "flaeche_m2": round(flaeche, 1), "fenster": anzahl[r["id"]],
                              "glas_m2": round(glas[r["id"]], 2), "soll_m2": round(soll, 2),
                              "anteil": f"1/{flaeche / glas[r['id']]:.1f}" if glas[r["id"]] else "kein Fenster"})
    # Flucht: Nachbargeschosse, nur Aussenfenster.
    for (unten_name, unten), (oben_name, oben) in zip(fenster_je_geschoss, fenster_je_geschoss[1:]):
        for fo in oben:
            if not fo["aussen"]:
                continue
            beste = None
            for fu in unten:
                if not fu["aussen"]:
                    continue
                winkel = abs(fo["u"][0] * fu["u"][1] - fo["u"][1] * fu["u"][0])
                if winkel > math.sin(FASSADE_WINKEL):
                    continue
                dx, dy = fo["mitte"][0] - fu["mitte"][0], fo["mitte"][1] - fu["mitte"][1]
                quer = abs(dx * fu["n"][0] + dy * fu["n"][1])
                if quer > FASSADE_QUER_MM:
                    continue
                # Entlang der Fassade, in der Richtung des unteren Fensters.
                lang = lambda p: (p[0] - fu["mitte"][0]) * fu["u"][0] + (p[1] - fu["mitte"][1]) * fu["u"][1]
                o_l, o_r = sorted((lang(fo["a"]), lang(fo["b"])))
                u_l, u_r = -fu["breite"] / 2, fu["breite"] / 2
                if o_r < u_l - FLUCHT_FAST_MM or o_l > u_r + FLUCHT_FAST_MM:
                    continue
                # "Kante" statt links/rechts: die Wandrichtung sagt nichts darueber,
                # wie man auf die Fassade schaut.
                abw = {"Kante": min(abs(o_l - u_l), abs(o_r - u_r)),
                       "Mitte": abs((o_l + o_r) / 2)}
                art, mm = min(abw.items(), key=lambda kv: kv[1])
                if beste is None or mm < beste[1]:
                    beste = (art, mm, fu)
            if beste and FLUCHT_OK_MM < beste[1] <= FLUCHT_FAST_MM:
                flucht.append({"oben": oben_name, "unten": unten_name, "fenster_oben": fo["id"],
                               "fenster_unten": beste[2]["id"], "raum_oben": fo["raum"],
                               "raum_unten": beste[2]["raum"], "naechste": beste[0],
                               "daneben_mm": round(beste[1])})
    return {"licht": licht, "flucht": flucht}


def _builder():
    spec = importlib.util.spec_from_file_location("bsrp", os.path.join(HERE, "build-simplifier-render-plan.py"))
    m = importlib.util.module_from_spec(spec)
    sys.argv = [sys.argv[0]]
    spec.loader.exec_module(m)
    return m


def haus(builder, plan):
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "g.json")
        with contextlib.redirect_stdout(io.StringIO()):
            builder.geometry_only(plan, out)
        with open(out, encoding="utf-8") as f:
            geo = json.load(f)
    with open(os.path.join(PROJECTS, plan, "annotations.json"), encoding="utf-8") as f:
        annotations = json.load(f)
    return pruefe(geo, annotations)


def main():
    args = sys.argv[1:]
    alle = "--alle" in args
    plaene = sorted(d for d in os.listdir(PROJECTS)
                    if os.path.exists(os.path.join(PROJECTS, d, "annotations.json"))
                    and not d.startswith("_")) if alle else [a for a in args if not a.startswith("--")]
    builder = _builder()
    ergebnis = {}
    for plan in plaene:
        try:
            r = haus(builder, plan)
        except (Exception, SystemExit) as fehler:
            ergebnis[plan] = {"fehler": str(fehler)[:200]}
            continue
        ergebnis[plan] = r
        if not alle:
            print(plan)
            for z in r["licht"]:
                print(f"  LICHT  {z['geschoss']:12s} {z['raum'][:26]:26s} {z['flaeche_m2']:5.1f} m²  "
                      f"Glas {z['glas_m2']:.2f} von {z['soll_m2']:.2f} m² ({z['anteil']})")
            for z in r["flucht"]:
                print(f"  FLUCHT {z['raum_oben']} ({z['oben']}) über {z['raum_unten']}: {z['daneben_mm']} mm neben {z['naechste']}")
            if not r["licht"] and not r["flucht"]:
                print("  ok")
    if alle:
        with open(AUSGABE, "w", encoding="utf-8") as f:
            json.dump({"schema": "fenster-pruefen-v1", "haeuser": ergebnis}, f, ensure_ascii=False, indent=1)
        treffer = sum(1 for v in ergebnis.values() if v.get("licht") or v.get("flucht"))
        print(f"{len(ergebnis)} Häuser, {treffer} mit Meldungen -> {AUSGABE}")


if __name__ == "__main__":
    main()

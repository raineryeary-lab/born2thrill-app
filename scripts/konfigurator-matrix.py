"""Konfigurator-Matrix: welche der 31 Grundriss-Felder haben wir, welche fehlen?

Rainer, 2026-10-16: "we basically check all the houses we got for biggest to
smallest and have some kind of variable in the backend that basically gives
the price per m2" -- und: "we use our annotated values". Die annotierten
Haeuser sind die Lehrbasis; spaeter werden daraus Grundrisse je Preisklasse
optimiert.

Quelle der 31 Felder: G:\\Meine Ablage\\_handoff\\Hausbauvarianten KS
Konfigurator.xlsx ("31 Grundrisse je Innen-Einrichtung M/K + 26 Ansichten").

    Budget bis 450   EFH 4/5/+   DHH 3/4/+     Bungalow 3/4/5/+
    Budget bis 600   EFH 4/5/+   DHH 3/4/5/+   Bungalow 3/4/+    ZFH 3/4/+
    Budget ueber 600 EFH 5/+                   Bungalow 3/4/+    ZFH 3/4/+

"+" ist die naechste Stufe und alles darueber (EFH 4/5/+ = 4, 5, 6+).

Je Haus:
  - Wohnflaeche aus den ANNOTIERTEN Raumpolygonen (ohne Garage, Carport,
    Terrasse, Balkon, Loggia, Keller) -- keine Korrektur auf Katalogwerte.
  - Preis = Wohnflaeche x Preis je m2 aus konfigurator.json (eine Zahl,
    im Backend aenderbar). Daraus die Budgetklasse.
  - Zimmerzahl wie in der Excel ("Kue, Bad, WC + 3R, 4R, 5R"): Wohn- und
    Schlafraeume; ein offenes Wohnen/Essen/Kochen zaehlt als 1. Kueche, Bad,
    WC, HWR, Diele, Flur, Abstell, Ankleide zaehlen nicht.
  - Haustyp: bungalow_* und *_bungalow_* -> bungalow; twostorey_*,
    onehalfstorey_* -> efh. DHH und ZFH kennt der Bestand nicht.

Ausgabe: konfigurator-matrix.csv (alle Haeuser) und konfigurator-fehlt.md
(die Felder und was fehlt) im Workbench-Datenordner.
"""

import csv
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECTS = os.path.abspath(os.path.join(HERE, "..", "..", "floorplan-simplifier", "projects"))
DATA = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR")
if not DATA:
    sys.exit("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt -- siehe .env.local.")

KONFIG = os.path.join(DATA, "konfigurator.json")
# Die Backend-Einstellungen. Fehlt ein Schluessel in konfigurator.json, gilt
# der Standard hier -- er folgt der ueblichen Zaehlung der Immobilienportale:
# Wohn-, Schlaf-, Kinder-, Arbeitszimmer zaehlen; Kueche, Bad, WC, Flur,
# Abstellraum nicht; eine Wohnkueche bzw. ein offenes Wohnen/Essen/Kochen ist
# EIN Zimmer; kleine Raeume zaehlen halb.
STANDARD = {
    "preis_pro_m2": 3000,
    "offener_wohnbereich_zaehlt": 1,     # Wohnen/Essen/Kochen in einem Raum
    "zimmer_mindestflaeche_m2": 6,       # darunter kein Zimmer
    "halbes_zimmer_unter_m2": 10,        # 6 bis unter 10 m2 = halbes Zimmer
    "halbe_zimmer_runden": "ab",         # "ab": 4,5 -> Stufe 4; "auf": 4,5 -> Stufe 5
    "_hinweis": "Werte aendern und konfigurator-matrix.py neu laufen lassen.",
}

BUDGETS = [("b450", "bis 450.000 EUR", 450_000), ("b600", "bis 600.000 EUR", 600_000),
           ("b600p", "ueber 600.000 EUR", None)]
# (budget, haustyp) -> Zimmerstufen; die letzte Stufe heisst "n+".
FELDER = {
    ("b450", "efh"): [4, 5, 6], ("b450", "dhh"): [3, 4, 5], ("b450", "bungalow"): [3, 4, 5, 6],
    ("b600", "efh"): [4, 5, 6], ("b600", "dhh"): [3, 4, 5, 6], ("b600", "bungalow"): [3, 4, 5],
    ("b600", "zfh"): [3, 4, 5],
    ("b600p", "efh"): [5, 6], ("b600p", "bungalow"): [3, 4, 5], ("b600p", "zfh"): [3, 4, 5],
}

NICHT_WOHNFLAECHE = ("garage", "carport", "terrasse", "balkon", "loggia", "keller")
KEIN_ZIMMER = ("bad", "wc", "dusch", "hwr", "htr", "hauswirtschaft", "diele", "flur",
               "abstell", "speis", "ankleide", "technik", "garage", "carport", "terrasse",
               "balkon", "loggia", "keller", "treppe", "luftraum", "galerie")
ZIMMER = ("wohnen", "wohnzimmer", "schlafen", "eltern", "kind", "buero", "büro", "arbeit",
          "gast", "zimmer", "essen")


def haustyp(plan):
    # Zuerst der Haustyp aus data.json -- die Projekt-ID kann luegen
    # (bungalow_040_185 ist ein Zweigeschosser, Rainer 2026-10-16).
    try:
        with open(os.path.join(PROJECTS, plan, "data.json"), encoding="utf-8") as f:
            typ = json.load(f).get("house_type")
        if typ == "bungalow":
            return "bungalow"
        if typ in ("twostorey", "onehalfstorey", "twostorey_cellar"):
            return "efh"
    except (OSError, ValueError):
        pass
    if plan.startswith("bungalow_") or "_bungalow_" in plan:
        return "bungalow"
    if plan.startswith(("twostorey_", "onehalfstorey_")) or "_onehalfstorey_" in plan or "_twostorey_" in plan:
        return "efh"
    return None


def ist_zimmer(label):
    text = (label or "").lower()
    if any(k in text for k in KEIN_ZIMMER) and not any(k in text for k in ("wohnen", "schlafen", "kind")):
        return False
    return any(k in text for k in ZIMMER)


def flaeche(punkte):
    return abs(sum(punkte[i]["x"] * punkte[(i + 1) % len(punkte)]["y"]
                   - punkte[(i + 1) % len(punkte)]["x"] * punkte[i]["y"]
                   for i in range(len(punkte)))) / 2


def bildverhaeltnis(projekt, ebene, annotationen):
    try:
        from PIL import Image
    except ImportError:
        Image = None
    for name in (f"{ebene}_original_preview.png", "original_preview.png"):
        pfad = os.path.join(projekt, name)
        if Image and os.path.exists(pfad):
            w, h = Image.open(pfad).size
            return h / w
    raum = (annotationen.get("annotation_space") or {}).get("aspect")
    return float(raum) if raum else None


def haus_werte(plan):
    projekt = os.path.join(PROJECTS, plan)
    pfad = os.path.join(projekt, "annotations.json")
    if not os.path.exists(pfad):
        return None
    with open(pfad, encoding="utf-8") as f:
        d = json.load(f)
    raeume = [a for a in d.get("annotations") or [] if (a.get("points") or []) and len(a["points"]) >= 3]
    if not raeume:
        return None
    skalen = d.get("floor_scale") or {}
    if not skalen:
        return {"plan": plan, "fehlt": "kein Massstab"}
    qm = 0.0
    luftraum = 0.0
    for a in raeume:
        ebene = a.get("floor_level")
        s = skalen.get(ebene) or next(iter(skalen.values()))
        if any(k in (a.get("label") or "").lower() for k in NICHT_WOHNFLAECHE):
            continue
        v = bildverhaeltnis(projekt, ebene, d)
        if not v:
            return {"plan": plan, "fehlt": "kein Seitenverhaeltnis"}
        stueck = flaeche(a["points"]) * s * s * v
        # Luftraum zaehlt voll mit -- er ist umbauter Raum und macht das Haus
        # groesser und teurer. Rainer, 2026-10-16: "just count it as if it
        # were quadratmeter, it is an umbauter Raum". Ausgewiesen wird er
        # trotzdem getrennt, damit man sieht, wieviel davon kein Boden ist.
        if "luftraum" in (a.get("label") or "").lower():
            luftraum += stueck
        qm += stueck
    # Ein Raum aus mehreren Polygonen (connected_room_id) ist EIN Zimmer --
    # seine Flaeche ist die Summe der Teile.
    flaechen = {}
    for a in raeume:
        if not ist_zimmer(a.get("label")):
            continue
        schluessel = a.get("connected_room_id") or a.get("id")
        ebene = a.get("floor_level")
        s = skalen.get(ebene) or next(iter(skalen.values()))
        eintrag = flaechen.setdefault(schluessel, {"m2": 0.0, "label": a.get("label") or ""})
        eintrag["m2"] += flaeche(a["points"]) * s * s * bildverhaeltnis(projekt, ebene, d)
    zimmer = 0.0
    for e in flaechen.values():
        offen = "wohnen" in e["label"].lower() and any(
            k in e["label"].lower() for k in ("essen", "kochen", "kueche", "küche"))
        if offen:
            zimmer += float(EINST["offener_wohnbereich_zaehlt"])
        elif e["m2"] < EINST["zimmer_mindestflaeche_m2"]:
            continue
        elif e["m2"] < EINST["halbes_zimmer_unter_m2"]:
            zimmer += 0.5
        else:
            zimmer += 1
    return {"plan": plan, "qm": round(qm), "luftraum": round(luftraum), "zimmer": zimmer,
            "haustyp": haustyp(plan)}


def budget_fuer(preis):
    for kennung, _, grenze in BUDGETS:
        if grenze is None or preis <= grenze:
            return kennung
    return BUDGETS[-1][0]


def stufe_fuer(zimmer, stufen):
    zimmer = (math.ceil(zimmer) if EINST["halbe_zimmer_runden"] == "auf" else math.floor(zimmer))
    if zimmer >= stufen[-1]:
        return stufen[-1]
    return zimmer if zimmer in stufen else None


def stufen_name(stufe, stufen):
    return f"{stufe}+" if stufe == stufen[-1] else str(stufe)


EINST = dict(STANDARD)


def main():
    konfig = {}
    if os.path.exists(KONFIG):
        with open(KONFIG, encoding="utf-8") as f:
            konfig = json.load(f)
    # Fehlende Schluessel mit dem Standard ergaenzen und zurueckschreiben, damit
    # alle Einstellungen in der Datei sichtbar sind.
    for k, v in STANDARD.items():
        konfig.setdefault(k, v)
    with open(KONFIG, "w", encoding="utf-8") as f:
        json.dump(konfig, f, indent=1)
    EINST.update(konfig)
    preis_m2 = float(EINST["preis_pro_m2"])

    fertig = set()
    ledger = os.path.join(DATA, "fertig-ledger.json")
    if os.path.exists(ledger):
        with open(ledger, encoding="utf-8") as f:
            l = json.load(f)
        fertig = set(l.get("plans", l).keys()) if isinstance(l, dict) else set()

    haeuser = []
    for plan in sorted(os.listdir(PROJECTS)):
        if plan.startswith("_") or not os.path.isdir(os.path.join(PROJECTS, plan)):
            continue
        w = haus_werte(plan)
        if not w or w.get("fehlt") or not w.get("haustyp"):
            continue
        w["preisflaeche"] = w["qm"]   # Luftraum steckt schon voll in qm
        w["preis"] = round(w["preisflaeche"] * preis_m2)
        w["budget"] = budget_fuer(w["preis"])
        stufen = FELDER.get((w["budget"], w["haustyp"]))
        stufe = stufe_fuer(w["zimmer"], stufen) if stufen else None
        w["feld"] = (f"{w['budget']}-{w['haustyp']}-{stufen_name(stufe, stufen)}"
                     if stufe is not None else "")
        w["fertig"] = plan in fertig
        haeuser.append(w)
    haeuser.sort(key=lambda h: -h["qm"])

    with open(os.path.join(DATA, "konfigurator-matrix.csv"), "w", newline="", encoding="utf-8") as f:
        schreiber = csv.writer(f, delimiter=";")
        schreiber.writerow(["plan", "haustyp", "wohnflaeche_m2", "luftraum_m2", "preisflaeche_m2",
                            "zimmer", "preis_eur", "budget", "konfigurator_feld", "fertig"])
        for h in haeuser:
            schreiber.writerow([h["plan"], h["haustyp"], h["qm"], h["luftraum"], h["preisflaeche"],
                                h["zimmer"], h["preis"], h["budget"], h["feld"],
                                "ja" if h["fertig"] else "nein"])

    zeilen = [f"# Konfigurator-Matrix ({int(preis_m2)} EUR/m2)", "",
              f"{len(haeuser)} Haeuser mit Massstab ausgewertet, davon {sum(h['fertig'] for h in haeuser)} fertig.", "",
              "| Feld | Status | fertig | offen |", "|---|---|---|---|"]
    fehlt = []
    for (budget, typ), stufen in FELDER.items():
        for stufe in stufen:
            name = f"{budget}-{typ}-{stufen_name(stufe, stufen)}"
            drin = [h for h in haeuser if h["feld"] == name]
            f_ = [h["plan"] for h in drin if h["fertig"]]
            o_ = [h["plan"] for h in drin if not h["fertig"]]
            status = "gruen" if f_ else ("gelb" if o_ else "ROT")
            if not f_ and not o_:
                fehlt.append(name)
            zeilen.append(f"| {name} | {status} | {', '.join(f_[:4])}{' ...' if len(f_) > 4 else ''} "
                          f"| {', '.join(o_[:4])}{' ...' if len(o_) > 4 else ''} |")
    zeilen += ["", f"## Es fehlen {len(fehlt)} Grundrisse", ""] + [f"- {n}" for n in fehlt]
    with open(os.path.join(DATA, "konfigurator-fehlt.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(zeilen) + "\n")
    print("\n".join(zeilen))


if __name__ == "__main__":
    main()

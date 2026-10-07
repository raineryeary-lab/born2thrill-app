# Map resolved Hub models onto Simplifier symbol keys.
#
# This replaces the size-match shortlist entirely. That approach ranked models
# by measured dimensions against a library whose measurements were wrong, and it
# put a vanity unit where a bath belonged. Here the type comes from the asset's
# own name and the size has already been verified by
# scripts/resolve-hub-scales.py, so nothing is being inferred.
#
# Each pick carries its scale divisor. The renderer must apply it on import —
# the library holds three different authoring scales and a model imported at the
# wrong one is worse than a missing model, because a missing model is visible
# and a wrong one merely looks odd.
#
# Where a symbol has several candidates, both a modern and a classic choice are
# recorded. That is how the four variants differ: same layout, same furniture
# positions, different finish set.
#
# Usage:
#   python scripts/build-symbol-picks.py

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RESOLVED = os.path.join(REPO, "tmp", "hub-models-resolved.json")
OUT = os.path.join(REPO, "data", "symbol-model-picks.json")

# Simplifier symbol key -> resolved type. Several symbols share a type: a
# Trockner is the same 600 x 600 x 850 box as a Waschmaschine, often stacked on
# it, so it reuses that model rather than needing its own.
# Symbole, die NICHT aus der Typtabelle kommen, sondern von Hand gepflegt
# sind, und die ein Neulauf darum nicht ueberschreiben darf.
#
# 2026-09-03 sind genau diese beiden bei einem Neulauf verschwunden. Sie
# standen nie in SYMBOL_TYPES -- sie wurden von Hand in die JSON geschrieben,
# und der Generator kannte sie nicht. `schreibtischstuhl` traegt
# divisor 3.5 mit der Notiz "measured 2236x2238x4340mm raw on 2026-08-10;
# divisor calibrated to 1240mm seat-back height": eine Messung, die der
# Generator mit seinem 2,54 zerstoert haette. Wiederhergestellt und hier
# eingetragen, damit es nicht noch einmal passiert.
HANDGEPFLEGT = {"essgruppe_stuhl", "schreibtischstuhl"}

SYMBOL_TYPES = {
    "badewanne": "bathtub",
    "eckbadewanne": "corner_bath",
    "dusche": "shower",
    "dusche_gross": "shower",
    "dusche_klein": "shower",
    "wand_wc": "wc",
    "waschtisch": "basin",
    "handwaschbecken": "basin",
    "doppelwaschtisch": "double_basin",
    "badheizkoerper": "towel_radiator",
    "spuele": "kitchen_sink",
    # Ergaenzt 2026-09-03. Diese drei hatten hier KEINEN Eintrag, weshalb der
    # Planbauer sie immer als `procedural` fuehrte -- ein Quader, obwohl die
    # Modelle auf der Platte lagen.
    "kuehlschrank": "fridge",
    "kochfeld": "hob",
    "hochschrank_herd": "oven",
    "waschmaschine": "washer",
    "trockner": "washer",
    "ecksofa": "corner_sofa",
    "sofa_3sitzer": "sofa_3",
    "sofa_2sitzer": "sofa_2",
    "sofa_1sitzer": "armchair",
    "hocker": "stool",
    "couchtisch": "coffee_table",
    "essgruppe_6": "dining_set",
    "fernseher": "tv",
    "doppelbett": "bed",
    "einzelbett": "bed",
    "kleiderschrank": "wardrobe",
    "schrank_60": "cupboard",
    "schrank_40": "cupboard",
    "abstellschrank": "cupboard",
    "schreibtisch": "desk",
    "schreibtisch_kind": "desk",
}

# Words that mark a model as leaning one way or the other. Used only to split
# candidates between the modern and classic variants; a symbol with a single
# candidate uses it for both.
# What the SYMBOL means, where the type alone is not specific enough. Ranking
# beds against a generic "bed" size put an 1120 mm single bed under Doppelbett;
# a Doppelbett is 1800 wide and an Einzelbett 900, and the library has both.
SYMBOL_EXPECTED_MM = {
    "doppelbett": (1800, 2000),
    "einzelbett": (900, 2000),
    "schrank_40": (400, 600),
    "schrank_60": (600, 600),
    "kleiderschrank": (2000, 600),
    "sofa_3sitzer": (2100, 900),
    "sofa_2sitzer": (1700, 900),
    "sofa_1sitzer": (900, 900),
    "ecksofa": (2800, 2000),
    "schreibtisch": (1600, 800),
    "schreibtisch_kind": (1200, 600),
    # A Waschtisch is a full basin; a Handwaschbecken is the small one. Ranked
    # against a generic "basin" the 400 x 280 hand basin won both, which is why
    # the Elternbad had a cloakroom sink in it.
    "waschtisch": (600, 550),
    "handwaschbecken": (450, 340),
    "badewanne": (1700, 750),
    "eckbadewanne": (1500, 1500),
    "dusche": (930, 1360),
    "dusche_gross": (990, 1200),
    "dusche_klein": (800, 800),
    "couchtisch": (1200, 600),
    "essgruppe_6": (1800, 900),
    "hocker": (600, 600),
    "fernseher": (1230, 80),
}


def footprint_error(size_mm, expected):
    got = sorted(size_mm[:2], reverse=True)
    want = sorted(expected, reverse=True)
    return sum(abs(a - b) / float(b) for a, b in zip(got, want)) / 2.0


CLASSIC_WORDS = ("classic", "leather", "wooden", "wood", "parsons", "rounded", "tufted")
MODERN_WORDS = ("modern", "grey", "graphite", "glass", "square", "light")


def leaning(label):
    lowered = label.lower()
    classic = sum(word in lowered for word in CLASSIC_WORDS)
    modern = sum(word in lowered for word in MODERN_WORDS)
    if classic > modern:
        return "classic"
    if modern > classic:
        return "modern"
    return "neutral"


# Farbwoerter, an denen sich ein Modell einem der drei modernen Stile
# zuordnen laesst. Sie stehen im Dateinamen der CGAxis- und Hub-Assets --
# "grey", "beige", "dark", "walnut" -- und das ist der einzige Hinweis, den
# ein Modell auf sein Aussehen gibt.
#
# Ergaenzt 2026-09-03. Vorher gab es genau ZWEI Modellsaetze, modern und
# classic; warm, dark und scandi teilten sich einen. Der Schwarzweiss-Test
# hat das sofort gezeigt: Warm gegen Scandi lag bei 5,2 Graustufen, weil
# beide dieselben Moebel benutzen und sich nur im Boden unterscheiden.
STIL_WOERTER = {
    "dark":   ("dark", "black", "graphite", "anthracite", "charcoal",
               "wenge", "grey", "gray"),
    "scandi": ("white", "light", "beige", "cream", "birch", "natural",
               "oak", "sand", "ivory"),
    # "leather", "wooden" und "brown" stehen bewusst NICHT hier: das sind die
    # Classic-Marker aus CLASSIC_WORDS. Als sie am 2026-09-03 in der
    # warm-Liste standen, griffen Warm und Classic nach denselben Modellen
    # und ihr Schwarzweiss-Abstand FIEL von 5,9 auf 3,5.
    "warm":   ("orange", "cognac", "terracotta", "amber", "honey", "walnut",
               "cherry", "caramel"),
}


def stil_neigung(label):
    """Zu welchem der drei modernen Stile ein Modell am ehesten passt."""
    gesenkt = label.lower()
    treffer = {stil: sum(w in gesenkt for w in woerter)
               for stil, woerter in STIL_WOERTER.items()}
    bester = max(treffer, key=lambda k: treffer[k])
    return bester if treffer[bester] else None


def waehle_je_stil(candidates, schon_vergeben):
    """Je einen Kandidaten fuer warm, dark und scandi -- moeglichst verschieden.

    Erst nimmt jeder Stil ein Modell, dessen Name zu ihm passt. Was schon
    vergeben ist, wird uebersprungen: zwei Stile mit demselben Sofa sind in
    Schwarzweiss dasselbe Zimmer, und genau das soll der Test finden.
    Reicht die Auswahl nicht, faellt ein Stil auf den besten freien
    Kandidaten zurueck und zuletzt auf den bestpassenden ueberhaupt -- die
    GROESSE schlaegt den Farbton, ein schlecht sitzendes Moebel ist schlimmer
    als ein doppeltes.
    """
    ergebnis = {}
    vergeben = set(schon_vergeben)
    for stil in ("dark", "scandi", "warm"):
        treffer = next((c for c in candidates
                        if stil_neigung(c["label"]) == stil
                        and c["path"] not in vergeben), None)
        if treffer is None:
            treffer = next((c for c in candidates if c["path"] not in vergeben), None)
        if treffer is None:
            treffer = candidates[0]
        ergebnis[stil] = treffer
        vergeben.add(treffer["path"])
    return ergebnis


def main():
    with open(RESOLVED, "r", encoding="utf-8") as handle:
        resolved = json.load(handle)["resolved"]

    by_type = {}
    for item in resolved:
        if not item.get("size_mm"):
            continue
        by_type.setdefault(item["type"], []).append(item)

    picks = {}
    missing = []
    for key, kind in sorted(SYMBOL_TYPES.items()):
        candidates = by_type.get(kind) or []
        if not candidates:
            missing.append((key, kind))
            continue

        # Closest fit to its nominal size first, so a symbol gets the most
        # typical example of its type rather than an outlier.
        # Rank against what THIS symbol is, not against its broad type.
        expected = SYMBOL_EXPECTED_MM.get(key)
        if expected:
            candidates = sorted(candidates,
                                key=lambda i: footprint_error(i["size_mm"], expected))
        else:
            candidates = sorted(candidates, key=lambda i: i.get("fit_error", 1.0))
        classic = next((c for c in candidates if leaning(c["label"]) == "classic"), candidates[0])
        modern = next((c for c in candidates if leaning(c["label"]) == "modern"), candidates[0])

        # Classic zuerst: sein Modell ist vergeben, bevor die drei modernen
        # Stile waehlen. Sonst greift Warm nach demselben Ledersofa.
        je_stil = waehle_je_stil(candidates, {classic["path"]})

        def eintrag(c):
            return {"path": c["path"], "divisor": c["divisor"],
                    "label": c["label"], "size_mm": c["size_mm"]}

        picks[key] = {
            "type": kind,
            "modern": eintrag(modern),
            "classic": eintrag(classic),
            # Die drei modernen Stile einzeln. `modern` bleibt als Rueckfall
            # stehen, damit aeltere Laeufe und Plaene weiter funktionieren.
            "warm": eintrag(je_stil["warm"]),
            "dark": eintrag(je_stil["dark"]),
            "scandi": eintrag(je_stil["scandi"]),
            "candidates": len(candidates),
        }

    # Handgepflegte Eintraege aus der bestehenden Datei uebernehmen, bevor
    # sie ueberschrieben wird. Ohne das loescht jeder Neulauf, was nicht aus
    # SYMBOL_TYPES kommt -- am 2026-09-03 waren das der Esszimmerstuhl und der
    # Schreibtischstuhl, letzterer mit einem von Hand kalibrierten Divisor.
    if os.path.exists(OUT):
        try:
            with open(OUT, encoding="utf-8") as vorher:
                bestand = json.load(vorher).get("picks", {})
        except (ValueError, OSError):
            bestand = {}
        for schluessel in HANDGEPFLEGT:
            if schluessel in bestand and schluessel not in picks:
                picks[schluessel] = bestand[schluessel]
                print("[picks] handgepflegt uebernommen: %s" % schluessel)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump({
            "schema": "dmh-symbol-model-picks-v2",
            "note": "Types come from the assets' own names; sizes verified by "
                    "resolve-hub-scales.py. Apply `divisor` on import — the "
                    "library holds three different authoring scales.",
            "picks": picks,
        }, handle, indent=1)

    print(f"[picks] {len(picks)} symbols mapped, {len(missing)} without a model")
    for key, item in sorted(picks.items()):
        # Handgepflegte Eintraege haben nicht zwingend beide Varianten.
        if "modern" not in item or "classic" not in item:
            print(f"[picks] {key:20} handgepflegt, unveraendert uebernommen")
            continue
        same = item["modern"]["label"] == item["classic"]["label"]
        note = "same for both" if same else f"classic: {item['classic']['label'][:28]}"
        print(f"[picks] {key:20} {item['modern']['label'][:32]:32} "
              f"/{item['modern']['divisor']:<5} {item['modern']['size_mm']}  {note}")
    for key, kind in missing:
        print(f"[picks] NO MODEL {key:20} (type {kind}) -> build as a box")


if __name__ == "__main__":
    main()

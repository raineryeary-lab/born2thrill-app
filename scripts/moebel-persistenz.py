#!/usr/bin/env python3
"""Ist jedes Moebel im gelieferten Bild noch da?

Rainer, 2026-09-01: "find out why stuff like that happens". Codex hat es
beantwortet -- jedes Innenbild ist eine eigene Stichprobe eines Bildmodells,
keine zweite Aufnahme derselben Szene. Objekte verschwinden dabei, und keine
Regel im Auftragstext kann das verhindern.

Was man dagegen tun kann, ist es MESSEN. Der Auftrag traegt seit dem
2026-09-01 je Moebel den projizierten Blender-Quader (`umriss_px`, acht
Ecken). Damit laesst sich fuer jedes Objekt einzeln fragen: steht an seiner
Stelle noch etwas?

Gemessen wird die KANTENDICHTE im Kasten, Lieferung gegen Baseline. Ein
Moebel hat Kanten -- Fugen, Beine, Kissen, Griffe. Verschwindet es, bleibt
Boden, und der ist glatt. Die Farbe taugt dafuer nicht: der Stilwechsel
aendert sie absichtlich, die Kanten bleiben.

    python moebel-persistenz.py <plan> <lieferordner>

NUR FUER BILDER, DIE ZUR BASELINE PASSEN -- also fuer einen
Low-Denoise-Pass ueber den Blender-Render, nicht fuer ein frei erzeugtes
Bild. Am 2026-09-01 an german_catalog_review_bungalow_3_4_2_b_120 gemessen:

    Baseline gegen sich selbst      43 Objekte, alle 1,00
    Dusche kuenstlich uebermalt     0,35, Nachbarn unveraendert 1,00
    freie Lieferung, dusche-3 FEHLT im Bild   1,16
    freie Lieferung, schreibtisch-20 FEHLT    1,06 und 1,26

Das Mass ist also richtig und der freie Input untauglich: wo die Dusche
fehlt, stehen Fliesen und eine Topfpflanze -- mehr Kanten als der graue
Rohbau, nicht weniger. Gegen frei erzeugte Bilder hilft nur das Auge; dieses
Werkzeug wird brauchbar, sobald der 0,22-Pass steht.

Die Zahlen sind ein Werkzeug fuer das Auge, kein Urteil. Codex, 2026-09-01,
zu dem, was auch mit Masken nicht garantiert bleibt: "exakte Stuhl-/
Kleinteilanzahl, unveraenderte Oeffnungen, keine subtilen
Wanddurchdringungen ... muessen visuell geprueft werden."
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_konfiguriert = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR", "").strip()
if not _konfiguriert:
    sys.exit("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt.")
DATA = os.path.abspath(_konfiguriert)


def kasten(umriss_px):
    """Das achsenparallele Rechteck um die acht projizierten Ecken.

    Der Quader steht in der Draufsicht schraeg; sein Umriss ist ein
    Sechseck. Fuer die Kantendichte genuegt das umschliessende Rechteck --
    es misst dieselbe Stelle in beiden Bildern, und mehr braucht der
    Vergleich nicht.
    """
    if not umriss_px:
        return None
    xs = [p[0] for p in umriss_px]
    ys = [p[1] for p in umriss_px]
    return (min(xs), min(ys), max(xs), max(ys))


def kantendichte(bild, rechteck, schwelle=28):
    """Anteil der Pixel im Rechteck, an denen eine Kante liegt.

    `bild` ist bereits ein Kantenbild in Graustufen. `schwelle` trennt
    Kante von Flaeche; 28 von 255 laesst das Rauschen des Renderers
    draussen und faengt eine Moebelfuge noch.
    """
    from PIL import Image
    links, oben, rechts, unten = [int(round(v)) for v in rechteck]
    links, oben = max(0, links), max(0, oben)
    rechts, unten = min(bild.width, rechts), min(bild.height, unten)
    if rechts - links < 4 or unten - oben < 4:
        return None
    aus = bild.crop((links, oben, rechts, unten))
    # `getdata` ist ab Pillow 14 weg; `tobytes` gibt dieselben Grauwerte.
    punkte = aus.tobytes()
    if not punkte:
        return None
    return sum(1 for p in punkte if p >= schwelle) / len(punkte)


def kantenbild(pfad):
    from PIL import Image, ImageFilter
    return Image.open(pfad).convert("L").filter(ImageFilter.FIND_EDGES)


def persistenz(baseline_png, lieferung_png, marker):
    """Je Marker: Kantendichte in Baseline und Lieferung, und ihr Verhaeltnis.

    Ein Verhaeltnis nahe 1 heisst "steht noch da". Nahe 0 heisst "die Stelle
    ist glatt geworden" -- dort war ein Moebel und ist keines mehr.
    """
    from PIL import Image
    basis = Image.open(baseline_png)
    liefer = Image.open(lieferung_png)
    if basis.size != liefer.size:
        return None
    kb = kantenbild(baseline_png)
    kl = kantenbild(lieferung_png)
    raus = {}
    for eintrag in marker:
        r = kasten(eintrag.get("umriss_px"))
        if not r:
            continue
        a = kantendichte(kb, r)
        b = kantendichte(kl, r)
        if a is None or b is None or a <= 0:
            continue
        raus[eintrag["name"]] = (round(a, 4), round(b, 4), round(b / a, 3))
    return raus


def lade(plan):
    pfad = os.path.join(DATA, "corrections", plan, "renders", "go-baseline",
                        "codex-job.json")
    with open(pfad, encoding="utf-8") as datei:
        return json.load(datei)


def main():
    zerleger = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    zerleger.add_argument("plan")
    zerleger.add_argument("ordner", help="Lieferordner unter renders/")
    zerleger.add_argument("--grenze", type=float, default=0.35,
                          help="ab welchem Verhaeltnis gemeldet wird")
    args = zerleger.parse_args()

    job = lade(args.plan)
    renders = os.path.join(DATA, "corrections", args.plan, "renders")
    ordner = args.ordner if os.path.isabs(args.ordner) else os.path.join(renders, args.ordner)
    karten = job.get("object_map") or []
    karten = karten if isinstance(karten, list) else [karten]
    if not karten:
        sys.exit("Der Auftrag hat keine Objektkarte.")
    marker = karten[0].get("markers") or []
    basis_name = (karten[0].get("file", "").replace("OBJEKTKARTE-", "")
                  .replace(".png", "") + ".png")
    baseline = os.path.join(renders, "go-baseline", basis_name)

    innen = [e["filename_hint"] for e in job.get("required_outputs", [])
             if e.get("kind") == "interior"]
    da = set(os.listdir(ordner))
    namen = []
    for hint in innen:
        stamm = os.path.splitext(hint)[0]
        treffer = [f for f in sorted(da) if f.startswith(stamm)]
        if treffer:
            namen.append(treffer[0])
    if not namen:
        sys.exit("Keine Innenbilder in %s" % ordner)
    for name in namen:
        raus = persistenz(baseline, os.path.join(ordner, name), marker)
        print(name)
        for objekt, (a, b, v) in sorted(raus.items(), key=lambda x: x[1][2]):
            if v <= args.grenze:
                print("   %-24s Baseline %.3f  Lieferung %.3f  -> %.2f"
                      % (objekt, a, b, v))


if __name__ == "__main__":
    main()

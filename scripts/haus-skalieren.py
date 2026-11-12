"""Haus als Vorlage duplizieren und etwas groesser/kleiner machen (haus-skalieren-v1).

Rainer, 2026-11-09: fehlende Baumfelder (REGELN 37) schnell fuellen -- aehnliche
Haeuser "nur etwas vergroessern oder verkleinern", "nach einer Vorschau ggf.
duplizieren". Erst ein Beispiel zeigen (REGELN 8).

Skaliert wird nur der Massstab (floor_scale je Geschoss): die normierte
Zeichnung bleibt, jede Strecke wird k-mal so lang, jede Flaeche k^2-mal so gross.
Elemente mit echter Breite (width_m: Tueren, Fenster, Treppe) behalten sie.

  python haus-skalieren.py <quelle> --flaeche 130          nur Vorschau-PNG, aendert nichts
  python haus-skalieren.py <quelle> --flaeche 130 --anlegen <neuer_plan>
                                                          legt den Projektordner neu an;
                                                          die Quelle bleibt unberuehrt
"""
import argparse
import copy
import importlib.util
import json
import math
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECTS = os.path.abspath(os.path.join(HERE, "..", "..", "floorplan-simplifier", "projects"))
DATA = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR") or r"E:\born2thrill-local-workbench-data"
VORSCHAU = os.path.join(DATA, "vorschau-skalieren")


def _lade(datei, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, datei))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def lies(pfad):
    with open(pfad, encoding="utf-8") as f:
        return json.load(f)


def skaliert(d, skalen, k):
    """Kopie der Zeichnung mit k-fachem Massstab."""
    neu = copy.deepcopy(d)
    neu["floor_scale"] = {e: s * k for e, s in skalen.items()}
    raum = neu.get("annotation_space")
    if isinstance(raum, dict):
        for feld in ("width_m", "depth_m"):
            if isinstance(raum.get(feld), (int, float)):
                raum[feld] = raum[feld] * k
    for e in neu.get("elements") or []:
        if e.get("type") != "stairs":
            continue
        # normierte Treppenbreite so, dass width_m gleich bleibt
        if isinstance(e.get("width"), (int, float)) and e.get("width_m"):
            e["width"] = e["width"] / k
        # Treppe in echter Laenge: eine kuerzere erreicht das Geschoss nicht
        # (R9_stair_access, onehalfstorey_efh120_s129). Anker = Wendelecke
        # (mittlerer Punkt), bei gerader Treppe der Antritt.
        pts = e.get("points") or []
        if len(pts) >= 2:
            a = pts[len(pts) // 2] if len(pts) >= 3 else pts[0]
            ax, ay = a["x"], a["y"]
            e["points"] = [dict(p, x=ax + (p["x"] - ax) / k, y=ay + (p["y"] - ay) / k) for p in pts]
    return neu


def faktor_fuer(matrix, plan, d, skalen, ziel):
    """k so, dass die Wohnflaeche (wie im Katalog gerechnet) ziel m2 ist."""
    alt = matrix.haus_werte(plan, dict(d, floor_scale=skalen))
    k = math.sqrt(ziel / alt["qm"])
    for _ in range(4):  # Rundung/Mindestflaechen: nachziehen
        w = matrix.haus_werte(plan, skaliert(d, skalen, k))
        if not w or not w.get("qm"):
            break
        k *= math.sqrt(ziel / max(w["qm"], 1))
    return alt, k, matrix.haus_werte(plan, skaliert(d, skalen, k))


def raumliste(matrix, plan, d, skalen):
    projekt = os.path.join(PROJECTS, plan)
    zeilen = []
    for a in d.get("annotations") or []:
        if len(a.get("points") or []) < 3:
            continue
        e = a.get("floor_level")
        s = skalen.get(e) or next(iter(skalen.values()))
        v = matrix.bildverhaeltnis(projekt, e, d) or 1
        zeilen.append((e, a.get("label") or "", matrix.flaeche(a["points"]) * s * s * v, a, s, v))
    return zeilen


def bild(matrix, plan, d, skalen, k, alt, neu, pfad):
    from PIL import Image, ImageDraw, ImageFont
    vorher = raumliste(matrix, plan, d, skalen)
    nachher = raumliste(matrix, plan, d, {e: s * k for e, s in skalen.items()})
    ebenen = sorted({z[0] for z in vorher}, key=lambda e: ["basement", "groundfloor", "upperfloor", "attic"].index(e)
                    if e in ("basement", "groundfloor", "upperfloor", "attic") else 9)
    PX = 38  # Pixel je Meter, links und rechts gleich: man sieht den Groessenunterschied
    try:
        f = ImageFont.truetype("arial.ttf", 13)
        fb = ImageFont.truetype("arialbd.ttf", 18)
    except OSError:
        f = fb = ImageFont.load_default()

    def rahmen(zeilen, e):
        xs = [p["x"] * s for z in zeilen if z[0] == e for s in [z[4]] for p in z[3]["points"]]
        ys = [p["y"] * s * v for z in zeilen if z[0] == e for s, v in [(z[4], z[5])] for p in z[3]["points"]]
        return min(xs), min(ys), max(xs), max(ys)

    spalte_b = max(rahmen(vorher, e)[2] - rahmen(vorher, e)[0] for e in ebenen) * max(k, 1) * PX + 60
    zeile_h = [max(rahmen(vorher, e)[3] - rahmen(vorher, e)[1], 1) * max(k, 1) * PX + 60 for e in ebenen]
    W, H = int(2 * spalte_b + 40), int(sum(zeile_h) + 110)
    img = Image.new("RGB", (W, H), "white")
    g = ImageDraw.Draw(img)
    g.text((20, 14), f"{plan}", fill="#201e1d", font=fb)
    g.text((20, 40), f"vorher {alt['qm']} m², {alt['zimmer']:g} Zimmer", fill="#555", font=f)
    g.text((20 + spalte_b, 40), f"nachher {neu['qm']} m², {neu['zimmer']:g} Zimmer  "
           f"(Maßstab ×{k:.3f}, Strecken {100 * (k - 1):+.1f} %)", fill="#b3261e", font=f)
    y0 = 80
    for i, e in enumerate(ebenen):
        for spalte, zeilen in ((0, vorher), (1, nachher)):
            x_min, y_min, _, _ = rahmen(zeilen, e)
            ox, oy = 20 + spalte * spalte_b, y0 + 20
            g.text((ox, y0), e, fill="#888", font=f)
            for z in zeilen:
                if z[0] != e:
                    continue
                _, label, m2, a, s, v = z
                pts = [(ox + (p["x"] * s - x_min) * PX, oy + (p["y"] * s * v - y_min) * PX) for p in a["points"]]
                g.polygon(pts, fill="#f4f1ea" if spalte == 0 else "#fdeeea", outline="#201e1d")
                cx = sum(p[0] for p in pts) / len(pts)
                cy = sum(p[1] for p in pts) / len(pts)
                text = f"{label}\n{m2:.1f} m²".replace(".", ",")
                g.multiline_text((cx, cy), text, fill="#201e1d", font=f, anchor="mm", align="center")
            # Massband: Breite des Geschosses
            x0, y_, x1, y1 = rahmen(zeilen, e)
            g.text((ox, oy + (y1 - y_) * PX + 6), f"{x1 - x0:.2f} × {y1 - y_:.2f} m".replace(".", ","),
                   fill="#555", font=f)
        y0 += zeile_h[i]
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    img.save(pfad)
    return [(z0[1], z0[2], z1[2]) for z0, z1 in zip(vorher, nachher)]


def anlegen(quelle, neu_plan, k, skalen):
    ziel = os.path.join(PROJECTS, neu_plan)
    if os.path.exists(ziel):
        sys.exit(f"{neu_plan} gibt es schon -- nichts geaendert")
    shutil.copytree(os.path.join(PROJECTS, quelle), ziel,
                    ignore=shutil.ignore_patterns("*.before-*", "*.vor-*", "*.blend*", "source-state.json"))
    pfad = os.path.join(ziel, "annotations.json")
    d = lies(pfad)
    d = skaliert(d, {e: s for e, s in (d.get("floor_scale") or skalen).items()}, k)
    d["project_id"] = neu_plan
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    gm = os.path.join(ziel, "gebaeudemass.json")
    if os.path.exists(gm):
        g = lies(gm)
        g["plan_id"] = neu_plan
        for feld in ("floor_scale",):
            if isinstance(g.get(feld), dict):
                g[feld] = {e: s * k for e, s in g[feld].items()}
        if isinstance(g.get("rahmen_m"), dict):
            g["rahmen_m"] = {e: [w * k for w in v] for e, v in g["rahmen_m"].items()}
        with open(gm, "w", encoding="utf-8") as f:
            json.dump(g, f, ensure_ascii=False, indent=1)
    with open(os.path.join(ziel, "abgeleitet.json"), "w", encoding="utf-8") as f:
        json.dump({"schema": "haus-skalieren-v1", "quelle": quelle, "faktor": k,
                   "angelegt": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "hinweis": "Rechte/Herkunft wie die Quelle; Moebel neu einrichten, Bau und Bilder neu."},
                  f, ensure_ascii=False, indent=1)
    return ziel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("quelle")
    ap.add_argument("--flaeche", type=float, required=True, help="Ziel-Wohnflaeche in m2")
    ap.add_argument("--anlegen", metavar="NEUER_PLAN")
    a = ap.parse_args()
    matrix = _lade("konfigurator-matrix.py", "konfigurator_matrix")
    hausdaten = _lade("hausdaten.py", "hausdaten")
    projekt = os.path.join(PROJECTS, a.quelle)
    d = lies(os.path.join(projekt, "annotations.json"))
    skalen = hausdaten.hausdaten(projekt)["floor_scale"]
    if not skalen:
        sys.exit("kein Massstab")
    alt, k, neu = faktor_fuer(matrix, a.quelle, d, skalen, a.flaeche)
    pfad = os.path.join(VORSCHAU, f"{a.quelle}__{int(a.flaeche)}m2.png")
    raeume = bild(matrix, a.quelle, d, skalen, k, alt, neu, pfad)
    print(f"{a.quelle}: {alt['qm']} m² {alt['zimmer']:g} Zi  ->  {neu['qm']} m² {neu['zimmer']:g} Zi   k={k:.4f}")
    for label, m_alt, m_neu in raeume:
        print(f"  {label[:28]:28s} {m_alt:6.1f} -> {m_neu:6.1f} m²")
    print("Vorschau:", pfad)
    if a.anlegen:
        print("angelegt:", anlegen(a.quelle, a.anlegen, k, skalen))


if __name__ == "__main__":
    main()

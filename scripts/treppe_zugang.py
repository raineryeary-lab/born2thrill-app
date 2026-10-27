"""Ob die Treppe an beiden Enden begehbar ist -- Pruefung VOR dem Bauen.

Rainer, 2026-10-17, twostorey_058: "you also have to set up a warning if a
staircase is not accessible please the last one had a wall blocking the
entrance".

Eigene Datei, nicht im Plan-Builder: der steht im Toolchain-Hash
(run_project.py), und jede Aenderung dort meldet ALLE Haeuser als veraltet.

    python treppe_zugang.py twostorey_058      -> JSON {"blockiert": [...]}

Baut den Plan in einen Temp-Ordner (der Plan-Builder ist schnell, kein
Blender) und prueft dessen Waende und Oeffnungen.
"""
import json
import math
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


STAIR_ACCESS_PROBE_MM = (-300, 700)   # vom Antritt/Austritt: 30 cm ins Band, 70 cm davor


def stair_access_blocked(stair_core, floors):
    """Ob eine Wand ohne Tuer den Antritt oder den Austritt der Treppe zusperrt.

    Rainer, 2026-10-17, twostorey_058: "you also have to set up a warning if a
    staircase is not accessible please the last one had a wall blocking the
    entrance". Eine Innenwand lief 52 mm vor der ersten Stufe quer ueber den
    Lauf, ohne Tuer -- gebaut, gerendert, und nichts sagte es.

    Geprueft wird ein Streifen in Laufrichtung: am Antritt (path_mm[0]) im
    untersten Geschoss, am Austritt (path_mm[-1]) im Geschoss darueber, je von
    30 cm im Band bis 70 cm davor. Gesperrt ist ein Ende erst, wenn auf einer
    Hoehe ALLE drei Spuren (Mitte und je 35 % der Breite links und rechts) in
    DERSELBEN Wand stehen, die dort keine begehbare Oeffnung hat -- eine Wand, die
    nur halb hineinragt, laesst einen Weg vorbei.

    Rueckgabe: Liste von {"ende", "level", "wall_id", "abstand_mm"}; leer,
    wenn beide Enden frei sind oder es keine Treppe gibt.
    """
    path = (stair_core or {}).get("path_mm") or []
    if len(path) < 2 or not floors:
        return []
    breite = (stair_core or {}).get("usable_width_mm") or 900.0

    def wand_an(floor, px, py):
        oeffnungen = {}
        for o in floor.get("openings") or []:
            if o.get("traversable") or o.get("opening_type") in ("door", "opening"):
                oeffnungen.setdefault(o.get("wall_id"), []).append(o)
        for w in floor.get("walls") or []:
            (ax, ay), (bx, by) = w["start_mm"], w["end_mm"]
            laenge = math.dist((ax, ay), (bx, by))
            if laenge < 1.0:
                continue
            ux, uy = (bx - ax) / laenge, (by - ay) / laenge
            entlang = (px - ax) * ux + (py - ay) * uy
            quer = abs((px - ax) * -uy + (py - ay) * ux)
            halb = (w.get("thickness_mm") or 120) / 2.0
            if quer > halb + 20 or entlang < -halb or entlang > laenge + halb:
                continue
            frei = any(abs(entlang - (o.get("position") or 0.5) * laenge) <= (o.get("width_mm") or 0) / 2.0
                       for o in oeffnungen.get(w.get("id"), []))
            if not frei:
                return w
        return None

    # Nach Hoehe ordnen, nicht nach Listenplatz: 1_5_1 hat [attic, groundfloor].
    reihe = {"basement": 0, "groundfloor": 1, "upperfloor": 2, "attic": 3}
    geordnet = sorted(floors, key=lambda f: reihe.get(f.get("level"), 9))
    if any(f.get("level") == "groundfloor" for f in geordnet):
        unten = next(i for i, f in enumerate(geordnet) if f.get("level") == "groundfloor")
    else:
        unten = 0

    befunde = []
    enden = [("antritt", unten, path[0], path[1]), ("austritt", unten + 1, path[-1], path[-2])]
    for ende, index, (ex, ey), (nx_, ny_) in enden:
        if index >= len(geordnet):
            continue
        floor = geordnet[index]
        laenge = math.dist((ex, ey), (nx_, ny_)) or 1.0
        ux, uy = (ex - nx_) / laenge, (ey - ny_) / laenge      # vom Lauf weg
        qx, qy = -uy, ux
        for d in range(STAIR_ACCESS_PROBE_MM[0], STAIR_ACCESS_PROBE_MM[1] + 1, 25):
            treffer = [wand_an(floor, ex + ux * d + qx * s, ey + uy * d + qy * s)
                       for s in (-0.35 * breite, 0.0, 0.35 * breite)]
            # Dieselbe Wand quer ueber alle drei Spuren. Drei VERSCHIEDENE
            # Waende sind meist eine Wandecke neben dem Austritt (1_1_2,
            # 1_6_1: Kind | Eltern, Tueren seitlich) -- kein Riegel.
            if all(treffer) and len({id(t) for t in treffer}) == 1:
                namen = {r.get("id"): r.get("name") for r in floor.get("rooms") or []}
                befunde.append({"ende": ende, "level": floor.get("level"),
                                "wall_id": treffer[1].get("id"), "abstand_mm": d,
                                "raeume": [namen[r] for r in treffer[1].get("rooms") or [] if namen.get(r)]})
                break
    return befunde


def stair_access_message(befund):
    wo = "Antritt (unten)" if befund["ende"] == "antritt" else "Austritt (oben)"
    geschoss = {"groundfloor": "EG", "upperfloor": "OG", "attic": "DG",
                "basement": "KG"}.get(befund["level"], befund["level"])
    zwischen = " und ".join(befund.get("raeume") or []) or befund["wall_id"]
    return ("Treppe nicht begehbar: am %s im %s steht eine Wand ohne Tuer quer davor "
            "(zwischen %s). Im Annotator die Raeume dort anpassen oder eine Tuer setzen."
            % (wo, geschoss, zwischen))


def pruefe_plan(plan):
    return stair_access_blocked(plan.get("shared_stair_core"), plan.get("floors") or [])


def pruefe_haus(name):
    with tempfile.TemporaryDirectory() as tmp:
        ziel = os.path.join(tmp, "plan.json")
        lauf = subprocess.run(
            [sys.executable, os.path.join(HERE, "build-simplifier-render-plan.py"), name, "modern", ziel],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        if lauf.returncode != 0 or not os.path.exists(ziel):
            return None
        with open(ziel, encoding="utf-8") as handle:
            return pruefe_plan(json.load(handle))


if __name__ == "__main__":
    befunde = pruefe_haus(sys.argv[1])
    print(json.dumps({"blockiert": [dict(b, text=stair_access_message(b)) for b in (befunde or [])],
                      "geprueft": befunde is not None}, ensure_ascii=False))

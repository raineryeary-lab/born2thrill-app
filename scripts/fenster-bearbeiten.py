"""Ein Fenster aus der 3D-Vorschau aendern (fenster-3d-v1, Rainer 2026-11-12:
"click on the 3d windows to move them horizontally ... rightclick and change
the size, Bruestung or full height and the number of glass panes").

Schreibt in die Zeichnung (annotations.json) -- dieselbe Datei, die der
Annotator speichert -- und zieht source-state.json nach, damit der naechste
Bau den neuen Stand als aktuell erkennt. Sicherung je Haus und Tag:
annotations.json.before-fenster-3d-<datum>.

  python fenster-bearbeiten.py <plan> <fenster-id> [--verschieben DX,DY]
         [--breite MM] [--typ bodentief|bruestungsfenster] [--felder N|auto]

DX,DY: Verschiebung in Plan-Millimetern (Bau-Koordinaten). Es zaehlt nur der
Anteil entlang des Fensters -- es bleibt auf seiner Wand.
Letzte Zeile der Ausgabe: JSON.
"""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import math
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECTS = os.path.abspath(os.path.join(HERE, "..", "..", "floorplan-simplifier", "projects"))


def _builder():
    spec = importlib.util.spec_from_file_location("bsrp", os.path.join(HERE, "build-simplifier-render-plan.py"))
    m = importlib.util.module_from_spec(spec)
    argv = sys.argv
    sys.argv = [argv[0]]
    try:
        spec.loader.exec_module(m)
    finally:
        sys.argv = argv
    return m


def source_state_schreiben(projekt, plan, d):
    """Wie floorplan-simplifier/app.py write_source_state()."""
    digest = hashlib.sha256(json.dumps(d, sort_keys=True, ensure_ascii=False,
                                       separators=(",", ":")).encode("utf-8")).hexdigest()
    scale = d.get("floor_scale") or {}
    levels = sorted({a.get("floor_level") for a in (d.get("annotations") or []) if a.get("floor_level")})
    state = {"schema": "zf-source-state-v1", "project_id": plan, "annotation_hash": digest,
             "saved_at": d.get("updated_at"), "floors": levels,
             "floors_without_scale": [l for l in levels if not scale.get(l)],
             "exterior_area_count": len(d.get("exterior_areas") or [])}
    pfad = os.path.join(projekt, "source-state.json")
    with open(pfad + ".tmp", "w", encoding="utf-8") as f:
        f.write(json.dumps(state, indent=2, ensure_ascii=False) + "\n")
    os.replace(pfad + ".tmp", pfad)


def bearbeiten(plan, fid, verschieben=None, breite=None, typ=None, felder=None):
    projekt = os.path.join(PROJECTS, plan)
    pfad = os.path.join(projekt, "annotations.json")
    with open(pfad, encoding="utf-8") as f:
        d = json.load(f)
    el = next((e for e in d.get("elements") or [] if e.get("id") == fid), None)
    if el is None or el.get("type") != "window":
        raise SystemExit(f"Kein Fenster {fid} in {plan}")
    pts = el.get("points") or []
    if len(pts) < 2:
        raise SystemExit("Fenster ohne zwei Punkte")

    b = _builder()
    with contextlib.redirect_stdout(io.StringIO()):
        ann = b.load_annotations(projekt)
        pw, ph = b.image_size(projekt, ann)
        levels = sorted({a.get("floor_level") for a in ann.get("annotations", []) if a.get("floor_level")})
        ground = ann.get("render_reference_level") or ("groundfloor" if "groundfloor" in levels else levels[0])
        frame = b.frame_for_level(ann, el.get("floor_level"), ground, pw, ph)
    a_n, b_n = pts[0], pts[-1]
    A, B = frame.point(a_n), frame.point(b_n)
    L = math.dist(A, B)
    if L < 1:
        raise SystemExit("Fenster zu kurz")
    ux, uy = (B[0] - A[0]) / L, (B[1] - A[1]) / L
    vorher = {"breite_mm": round(L), "typ": el.get("window_type"), "felder": el.get("panes")}

    # Verschieben: Anteil entlang des Fensters, in Bruchteilen seiner Laenge.
    if verschieben:
        dx, dy = verschieben
        s = (dx * ux + dy * uy) / L
        el["points"] = [dict(p, x=p["x"] + (b_n["x"] - a_n["x"]) * s,
                             y=p["y"] + (b_n["y"] - a_n["y"]) * s) for p in pts]
        pts = el["points"]
        a_n, b_n = pts[0], pts[-1]
    # Breite: um die Mitte, die Lage bleibt.
    if breite:
        k = float(breite) / L
        mx = (a_n["x"] + b_n["x"]) / 2
        my = (a_n["y"] + b_n["y"]) / 2
        el["points"] = [dict(p, x=mx + (p["x"] - mx) * k, y=my + (p["y"] - my) * k) for p in pts]
        el["width_m"] = round(float(breite) / 1000, 3)
        if "width_mm" in el:
            el["width_mm"] = float(breite)
    if typ:
        if typ not in ("bodentief", "bruestungsfenster"):
            raise SystemExit("Typ: bodentief oder bruestungsfenster")
        el["window_type"] = typ
        el.pop("sill_height_mm", None)       # Bau nimmt dann 0 bzw. 900 mm
    if felder is not None:
        if felder == "auto":
            el.pop("panes", None)
        else:
            n = int(felder)
            if not 1 <= n <= 6:
                raise SystemExit("Felder: 1 bis 6")
            el["panes"] = n

    tag = time.strftime("%Y%m%d")
    sicherung = f"{pfad}.before-fenster-3d-{tag}"
    if not os.path.exists(sicherung):
        shutil.copy2(pfad, sicherung)
    d["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    with open(pfad + ".tmp", "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    os.replace(pfad + ".tmp", pfad)
    source_state_schreiben(projekt, plan, d)
    return {"ok": True, "plan": plan, "id": fid, "vorher": vorher,
            "nachher": {"breite_mm": breite or vorher["breite_mm"], "typ": el.get("window_type"),
                        "felder": el.get("panes")}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("id")
    ap.add_argument("--verschieben")
    ap.add_argument("--breite", type=float)
    ap.add_argument("--typ")
    ap.add_argument("--felder")
    a = ap.parse_args()
    v = tuple(float(x) for x in a.verschieben.split(",")) if a.verschieben else None
    print(json.dumps(bearbeiten(a.plan, a.id, v, a.breite, a.typ, a.felder), ensure_ascii=True))


if __name__ == "__main__":
    main()

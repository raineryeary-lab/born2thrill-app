"""3D-Vorschau des Hauses von aussen, vor dem eigentlichen Bau (vorschau-3d-v1).

Rainer, 2026-11-03: "WOULD IT BE SUPER HARD TO DO A 3D PREVIEW OF SOME SORT
of the outside before we really go into the build?" -- gewaehlt: Weg 2, der
echte Bau ohne Render. Derselbe Plan (build-simplifier-render-plan.py) und
dieselbe Aussenszene (render-exterior.py) wie beim Bau; render-exterior.py
schreibt mit EXT_GLTF_OUT nur eine GLB-Datei und hoert vor dem Render auf.
Darum gibt es keinen zweiten Dach-Code, und die Vorschau kann vom Bau nicht
abweichen.

Usage:
  python scripts/vorschau-3d.py <project_id> <out_dir> [--dach <dachform>]

Schreibt <out_dir>/plan.json, <out_dir>/<dach>.glb und <out_dir>/vorschau.json
(Daecher dieses Hauses, gebaute Dateien). Rendert kein Bild, schreibt keine
.blend und beruehrt keinen Lieferordner. Letzte Zeile der Ausgabe: JSON.
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def dach_waehlen(gewuenscht, daecher):
    """Die gewuenschte Dachform, wenn das Haus sie hat, sonst die erste."""
    if not daecher:
        return None
    return gewuenscht if gewuenscht in daecher else daecher[0]


def main():
    import run_project   # BLENDER, BLENDER_PY, PLAN_ENV, roof_types_for_plan

    parser = argparse.ArgumentParser()
    parser.add_argument("project_id")
    parser.add_argument("out_dir")
    parser.add_argument("--dach", default="")
    args = parser.parse_args()
    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    plan_path = os.path.join(out_dir, "plan.json")
    start = time.time()

    # Fuer die Huelle reicht ein Stil: Waende, Oeffnungen und Dach haengen
    # nicht am Stil (run_project.py baut die Aussenbilder auch nur aus dem
    # Plan des ersten Stils).
    plan = subprocess.run(
        [sys.executable, os.path.join(HERE, "build-simplifier-render-plan.py"),
         args.project_id, "modern", plan_path],
        capture_output=True, text=True, env=run_project.PLAN_ENV)
    if plan.returncode != 0:
        print((plan.stdout + plan.stderr)[-2000:])
        print(json.dumps({"ok": False, "schritt": "plan"}))
        return 1

    daecher = list(run_project.roof_types_for_plan(plan_path))
    dach = dach_waehlen(args.dach, daecher)
    glb = os.path.join(out_dir, f"{dach}.glb")
    env = dict(os.environ, EXT_GLTF_OUT=glb, EXT_ROOF_TYPE=dach)
    # Der PNG-Pfad wird nie geschrieben (Abbruch vor dem Render), muss aber
    # ausserhalb von go-baseline liegen, damit keine Handkamera gerettet wird.
    bau = subprocess.run(
        [run_project.BLENDER, *run_project.BLENDER_PY,
         os.path.join(HERE, "render-exterior.py"), "--",
         plan_path, os.path.join(out_dir, f"{dach}.png")],
        capture_output=True, text=True, env=env)
    if bau.returncode != 0 or not os.path.exists(glb):
        print((bau.stdout + bau.stderr)[-3000:])
        print(json.dumps({"ok": False, "schritt": "blender", "dach": dach}))
        return 1

    info_pfad = os.path.join(out_dir, "vorschau.json")
    try:
        with open(info_pfad, encoding="utf-8") as handle:
            info = json.load(handle)
    except (OSError, ValueError):
        info = {}
    gebaut = {d: t for d, t in (info.get("gebaut") or {}).items() if d in daecher}
    gebaut[dach] = time.strftime("%Y-%m-%dT%H:%M:%S")
    info = {"projekt": args.project_id, "daecher": daecher, "gebaut": gebaut}
    with open(info_pfad, "w", encoding="utf-8") as handle:
        json.dump(info, handle, indent=1)
    print(json.dumps({"ok": True, "dach": dach, "daecher": daecher,
                      "sekunden": round(time.time() - start, 1)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

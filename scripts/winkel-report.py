#!/usr/bin/env python3
"""Show the walls that failed wall_angles, so the call takes a minute not an hour.

13 houses are blocked on angles between 6 and 37 degrees. A log line saying
"wall-20 is 25.049 deg off-axis" is not something anyone can judge; the same
wall drawn in red on the floorplan is. This writes one HTML page with every
blocked house, its walls in grey and the flagged ones in red with the angle on
them, so you can flick through and say which are real angled wings and which are
drawing slips.

Reads the built plan-*.json (the same geometry the verifier judged) and the
build log (for which walls it named). Writes nothing into any project and never
touches annotations.json.

    python winkel-report.py
    python winkel-report.py --out C:\\somewhere\\winkel.html
"""

import argparse
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SUITE = os.path.dirname(os.path.dirname(HERE))
# Nicht raten. 2026-08-21: der Datenordner zog von C: nach E:; ein Skript,
# das ohne gesetzte Variable still auf den alten C:-Nachbarordner
# zurueckfiele, wuerde unbemerkt gegen veraltete Daten arbeiten -- exakt
# der root-merge-Fehler vom 18.08., nur seitenverkehrt. Gleiches Muster wie
# build-simplifier-render-plan.py.workbench_data_root().
_konfiguriert = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR", "").strip()
if not _konfiguriert:
    sys.exit("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt -- verweigere, "
            "den Datenordner zu erraten. Siehe .env.local.")
DATA = os.path.abspath(_konfiguriert)
CORRECTIONS = os.path.join(DATA, "corrections")


def read_json(path):
    try:
        with open(path, encoding="utf-8-sig") as handle:
            return json.load(handle)
    except Exception:
        return None


def flagged_walls(log_path):
    """Wall ids the verifier named, mapped to the angle it reported."""
    try:
        with open(log_path, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    except Exception:
        return {}
    found = {}
    for block in re.findall(r"walls off-axis \(expected at most 1[^)]*\): \{([^}]*)\}", text):
        for wid, ang in re.findall(r"'([^']+)':\s*([0-9.]+)", block):
            found[wid] = float(ang)
    for wid, ang in re.findall(r"wall ([\w-]+) is ([0-9.]+) deg off-axis", text):
        found[wid] = float(ang)
    return found


def svg_for(plan, flagged, size=460):
    """Floorplan as SVG: exterior walls grey, flagged ones red and labelled."""
    walls = []
    for floor in plan.get("floors", []):
        for wall in floor.get("walls", []):
            if wall.get("wall_type") == "exterior":
                walls.append(wall)
    if not walls:
        return "<p>keine Aussenwaende im Plan</p>"

    xs = [c for w in walls for c in (w["start_mm"][0], w["end_mm"][0])]
    ys = [c for w in walls for c in (w["start_mm"][1], w["end_mm"][1])]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    span = max(maxx - minx, maxy - miny) or 1.0
    pad = 30.0
    scale = (size - 2 * pad) / span

    def px(x, y):
        return (pad + (x - minx) * scale,
                size - pad - (y - miny) * scale)   # y up

    parts = ['<svg viewBox="0 0 %d %d" width="100%%" xmlns="http://www.w3.org/2000/svg">'
             % (size, size)]
    labels = []
    for wall in walls:
        x1, y1 = px(*wall["start_mm"])
        x2, y2 = px(*wall["end_mm"])
        bad = wall["id"] in flagged
        parts.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                     'stroke="%s" stroke-width="%s" stroke-linecap="round"/>'
                     % (x1, y1, x2, y2,
                        "#c0392b" if bad else "#9aa4ad", "4.5" if bad else "2.5"))
        if bad:
            labels.append('<text x="%.1f" y="%.1f" font-family="ui-monospace,monospace" '
                          'font-size="12" fill="#c0392b" text-anchor="middle">%.1f&#176;</text>'
                          % ((x1 + x2) / 2, (y1 + y2) / 2 - 6, flagged[wall["id"]]))
    parts.extend(labels)
    parts.append("</svg>")
    return "".join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=os.path.join(
        SUITE, "floorplan-simplifier", "plans", "winkel-report.html"))
    args = parser.parse_args()

    cards = []
    for name in sorted(os.listdir(CORRECTIONS)):
        folder = os.path.join(CORRECTIONS, name, "renders", "go-baseline")
        log = os.path.join(folder, "batch-build.log")
        if not os.path.exists(log):
            continue
        flagged = flagged_walls(log)
        if not flagged:
            continue
        # Only houses that are actually still failing -- a certified delivery
        # means the log is history.
        if os.path.exists(os.path.join(folder, "delivery-manifest.json")):
            continue
        plan = read_json(os.path.join(folder, "plan-modern.json"))
        if not plan:
            continue
        angles = " ".join("%.1f&#176;" % a for a in sorted(flagged.values(), reverse=True))
        cards.append(
            '<figure><h2>%s</h2><div class="a">%s</div>%s'
            '<figcaption>%d beanstandete Wand/Waende</figcaption></figure>'
            % (name, angles, svg_for(plan, flagged), len(flagged)))

    html = """<title>Blockierte Winkel</title>
<style>
 :root{--bg:#f7f5f2;--fg:#22282d;--muted:#6b7680;--card:#fff;--line:#e2ddd6;--bad:#c0392b}
 :root:not([data-theme=light]) @media (prefers-color-scheme:dark){}
 body{margin:0;background:var(--bg);color:var(--fg);
      font:15px/1.55 ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}
 header{padding:28px 24px 8px;max-width:1200px;margin:0 auto}
 h1{font-size:22px;margin:0 0 6px} header p{margin:0;color:var(--muted);max-width:60ch}
 .grid{display:grid;gap:18px;padding:18px 24px 48px;max-width:1200px;margin:0 auto;
       grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}
 figure{margin:0;background:var(--card);border:1px solid var(--line);border-radius:10px;
        padding:14px}
 h2{font-size:12px;font-family:ui-monospace,monospace;margin:0 0 4px;word-break:break-all;
    color:var(--muted);font-weight:600}
 .a{font-family:ui-monospace,monospace;font-size:13px;color:var(--bad);margin-bottom:6px}
 figcaption{color:var(--muted);font-size:12px;margin-top:6px}
</style>
<header><h1>Blockierte Winkel &mdash; %d Haeuser</h1>
<p>Rot = die Wand, an der <code>wall_angles</code> haengt, mit ihrer Abweichung
von der Achse. 45&#176; gilt inzwischen als Diagonale und wird zugelassen; diese
hier liegen dazwischen. Frage je Haus: <b>gewollter Winkel</b> oder
<b>verzeichnet</b>?</p></header>
<div class="grid">%s</div>""" % (len(cards), "".join(cards))

    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(html)
    print("%d Haeuser gezeichnet -> %s" % (len(cards), args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())

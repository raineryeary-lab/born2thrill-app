"""Moebel einer Vorlage auf ein skaliertes Duplikat uebertragen (haus-skalieren-v1).

Rainer, 2026-11-09: onehalfstorey_efh120_s129 aus german_catalog_review_
onehalfstorey_1_1_2_efh_120. "Alle Raeume einrichten" lieferte dort doppelte
Kuechenteile und kein Sofa; die Vorlage ist von Rainer eingerichtet (inkl. seiner
Kuechenzeile, REGELN 16). Also: dieselben Moebel, gleiche Groesse (REGELN 14),
Raum fuer Raum versetzt. Achse fuer Achse: steht ein Moebel an einer Wand
(Abstand < 400 mm), bleibt der Abstand zu dieser Wand; sonst liegt es
anteilig im Raum. Raeume werden ueber ihre id zugeordnet (gleiche Zeichnung).

  python moebel-uebertragen.py <geo-quelle.json> <geo-ziel.json> <quelle> <ziel> [--schreiben]
geo-*.json: build-simplifier-render-plan.py --geometry-only <plan> <out>.
Ohne --schreiben nur Bericht.
"""
import copy
import json
import os
import sys
import time

DATA = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR") or r"E:\born2thrill-local-workbench-data"
AN_WAND_MM = 400


def bbox(pg):
    xs = [p[0] for p in pg]
    ys = [p[1] for p in pg]
    return min(xs), min(ys), max(xs), max(ys)


def drin(p, pg):
    x, y = p
    innen = False
    for i in range(len(pg)):
        (x1, y1), (x2, y2) = pg[i], pg[(i + 1) % len(pg)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            innen = not innen
    return innen


def halbe(item):
    """Halbe Ausdehnung in x und y (mm), nach Drehung."""
    if item.get("points_mm"):
        t = item.get("depth_mm", 600) / 2
        return t, t
    fp = item.get("footprint_mm") or {}
    w, d = fp.get("width_mm", 0) / 2, fp.get("depth_mm", 0) / 2
    return (d, w) if round(item.get("rotation_deg", 0)) % 180 == 90 else (w, d)


def achse(v, lo, hi, LO, HI, h):
    d0, d1 = v - lo, hi - v
    if d0 <= d1 and d0 - h < AN_WAND_MM:
        return LO + d0
    if d1 < d0 and d1 - h < AN_WAND_MM:
        return HI - d1
    return LO + (v - lo) * (HI - LO) / max(hi - lo, 1)


def uebertragen(geo_q, geo_z, symbole, ebene, k):
    rq = {r["id"]: r for f in geo_q["floors"] if f["floor_level"] == ebene for r in f["rooms"]}
    rz = {r["id"]: r for f in geo_z["floors"] if f["floor_level"] == ebene for r in f["rooms"]}
    neu, bericht = [], []
    for item in symbole:
        it = copy.deepcopy(item)
        pkt = it["points_mm"] if it.get("points_mm") else [it["position_mm"]]
        mitte = [sum(p[0] for p in pkt) / len(pkt), sum(p[1] for p in pkt) / len(pkt)]
        raum = next((r for r in rq.values() if drin(mitte, r["polygon_mm"])), None)
        hx, hy = halbe(it)
        if raum and raum["id"] in rz:
            x0, y0, x1, y1 = bbox(raum["polygon_mm"])
            X0, Y0, X1, Y1 = bbox(rz[raum["id"]]["polygon_mm"])
            neue = [[round(achse(p[0], x0, x1, X0, X1, hx), 1), round(achse(p[1], y0, y1, Y0, Y1, hy), 1)] for p in pkt]
            name = raum["name"]
        else:
            neue = [[round(p[0] * k, 1), round(p[1] * k, 1)] for p in pkt]
            name = "(kein Raum)"
        if it.get("points_mm"):
            it["points_mm"] = neue
        else:
            it["position_mm"] = neue[0]
        neu.append(it)
        bericht.append(f"  {name[:22]:22s} {it['symbol']:18s} {pkt} -> {neue}")
    return neu, bericht


def main():
    geo_q, geo_z = (json.load(open(p, encoding="utf-8")) for p in sys.argv[1:3])
    quelle, ziel = sys.argv[3], sys.argv[4]
    k = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "floorplan-simplifier",
                                    "projects", ziel, "abgeleitet.json"), encoding="utf-8"))["faktor"]
    ebenen = [f["floor_level"] for f in geo_q["floors"]]
    for i, ebene in enumerate(ebenen):
        pq = os.path.join(DATA, "corrections", quelle, "furniture", f"floor-{i}.json")
        pz = os.path.join(DATA, "corrections", ziel, "furniture", f"floor-{i}.json")
        dq, dz = json.load(open(pq, encoding="utf-8")), json.load(open(pz, encoding="utf-8"))
        assert dq["floor_id"] == dz["floor_id"], (dq["floor_id"], dz["floor_id"])
        symbole, bericht = uebertragen(geo_q, geo_z, dq["symbols"], ebene, k)
        print(ebene, len(symbole), "Moebel")
        print("\n".join(bericht))
        if "--schreiben" in sys.argv:
            os.replace(pz, pz + ".before-uebertragen") if not os.path.exists(pz + ".before-uebertragen") else None
            dz["symbols"] = symbole
            dz["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            with open(pz, "w", encoding="utf-8") as f:
                json.dump(dz, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()

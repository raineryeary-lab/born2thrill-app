"""Von Hand gezeichnete Gelaender und die automatischen am Treppenloch.

Plan: plans/gelaender-element-v1.md. Rainer, 2026-11-07: "i need to have a
railing element like the trennwand, the treppenloch combine with the should
work" -- entschieden: ein gezeichnetes Gelaender auf einer Treppenloch- oder
Luftraumkante ERSETZT dort das automatische (kein doppeltes), und ein Ende
nahe einer Lochecke rastet auf die Ecke ein, damit beide sich treffen.

Reines Python ohne bpy: render-furnished-dollhouse.py importiert es, die
Tests auch. Alle Masse in mm.
"""

import math

ABSTAND_MM = 150.0     # so nah muss ein gezeichnetes Gelaender an der Kante liegen
MAX_GRAD = 10.0        # und so parallel
EINRASTEN_MM = 150.0   # Ende so nah an einer Lochecke -> auf die Ecke


def abdeckung(a_mm, b_mm, segmente, abstand_mm=ABSTAND_MM, max_grad=MAX_GRAD):
    """Die Stuecke der Kante a->b, die ein gezeichnetes Gelaender schon traegt.

    Liste von (t0, t1) in 0..1 entlang a->b, sortiert und zusammengefasst.
    Ein Segment zaehlt, wenn es fast parallel (max_grad) und nah (abstand_mm,
    beide Enden) liegt; abgedeckt ist seine Projektion auf die Kante.
    """
    ax, ay = a_mm
    bx, by = b_mm
    dx, dy = bx - ax, by - ay
    laenge = math.hypot(dx, dy)
    if laenge < 1.0:
        return []
    ux, uy = dx / laenge, dy / laenge
    stuecke = []
    for seg in segmente or []:
        (sx, sy), (ex, ey) = seg["start_mm"], seg["end_mm"]
        sl = math.hypot(ex - sx, ey - sy)
        if sl < 1.0:
            continue
        cos = abs(((ex - sx) * ux + (ey - sy) * uy) / sl)
        if cos < math.cos(math.radians(max_grad)):
            continue
        quer = [abs((px - ax) * -uy + (py - ay) * ux) for px, py in ((sx, sy), (ex, ey))]
        if max(quer) > abstand_mm:
            continue
        t = sorted(((px - ax) * ux + (py - ay) * uy) / laenge for px, py in ((sx, sy), (ex, ey)))
        t0, t1 = max(0.0, t[0]), min(1.0, t[1])
        if t1 - t0 > 1e-6:
            stuecke.append((t0, t1))
    stuecke.sort()
    zusammen = []
    for t0, t1 in stuecke:
        if zusammen and t0 <= zusammen[-1][1]:
            zusammen[-1] = (zusammen[-1][0], max(zusammen[-1][1], t1))
        else:
            zusammen.append((t0, t1))
    return zusammen


def ohne_intervalle(stuecke, weg):
    """`stuecke` (t0, t1) ohne die Intervalle aus `weg`."""
    rest = list(stuecke)
    for w0, w1 in weg:
        neu = []
        for t0, t1 in rest:
            if w1 <= t0 or w0 >= t1:
                neu.append((t0, t1))
                continue
            if w0 > t0:
                neu.append((t0, w0))
            if w1 < t1:
                neu.append((w1, t1))
        rest = neu
    return [(t0, t1) for t0, t1 in rest if t1 - t0 > 1e-6]


def einrasten(segmente, ecken, grenze_mm=EINRASTEN_MM):
    """Enden nahe einer Lochecke auf die Ecke setzen. Neue Liste."""
    aus = []
    for seg in segmente or []:
        neu = dict(seg)
        for feld in ("start_mm", "end_mm"):
            px, py = seg[feld]
            beste = None
            for ecke in ecken or []:
                d = math.hypot(ecke[0] - px, ecke[1] - py)
                if d <= grenze_mm and (beste is None or d < beste[0]):
                    beste = (d, tuple(ecke))
            if beste:
                neu[feld] = beste[1]
        aus.append(neu)
    return aus

"""Recognizing a T- or Z/S-shaped footprint as three (or, for one Z/S
sub-family, two) overlapping roof wings -- the two-reflex-vertex
generalisation of `roof_wings.recognize_two_wings()` (one reflex vertex,
a simple L).

Rainer, 2026-09-26: after `PER-WING-AXIS-OVERRIDE-001` (per-wing ridge
override for L-shapes, design-reviewed, not yet built) he confirmed T-shape
support is wanted NOW, not deferred -- "doesnt work i need to make the
first b< han and even add a new one if needed" -> confirmed via question
("Yes, need T-shape now too"). A Codex read-only design review
(`plans/TZ-WING-RECOGNITION-001-codex-review.md`) was run BEFORE any of
this was written; its findings shaped the approach below directly:

  - "Two reflex vertices" does not mean one shape family. A classic T (one
    long bar, one stem through its middle) and a Z/S (two rectangles
    joined by a connector) need DIFFERENT construction rules, and Codex
    found a further wrinkle THIS module discovered empirically while
    building it: some two-reflex "Z-like" shapes decompose into just TWO
    overlapping rectangles (a diagonally-offset L, no separate connector
    needed), while others genuinely need THREE (a narrow bridging
    connector between two rectangles that do not themselves overlap).
    Both are legitimate, common shapes; this module tries the simpler
    (two-wing) decomposition FIRST and only falls back to the three-wing
    connector construction if that does not exactly reproduce the input
    polygon.
  - A classic T's "three roof wings" (left arm, right arm, stem) are
    DELIBERATELY NOT the shape's own inclusion-maximal rectangles -- the
    stem is extended the FULL bbox height (through the bar's own
    territory too), and each arm is extended THROUGH the stem's own width
    to its far side. "Find the maximal rectangles" does not produce the
    right answer; the construction below is driven directly by the two
    reflex points and which bounding-box corners are missing, not by a
    generic rectangle search.
  - Codex's strongest recommendation, followed literally here: verify
    every candidate decomposition by EXACT coverage against the real
    input polygon (not the sampled-grid check `roof_wings.py`'s own
    `_grid_coverage_matches()` uses, which can miss thin discrepancies --
    an axis-aligned polygon's own vertex coordinates fully define every
    relevant grid line, so an EXACT cell-by-cell check is possible and
    cheap, see `_arrangement_coverage_matches()` below). A construction
    that does not verify exactly is treated as wrong, never guessed at.

Deliberately kept in its OWN file, separate from `roof_wings.py` (which
stays exactly as `recognize_two_wings()` already is, unmodified, still the
only thing any renderer code calls) -- per the Codex review's explicit
recommendation: recognition is built and tested standalone first, NOT
wired into `render-exterior.py` yet, since doing so would immediately hit
several genuine, separate, not-yet-solved pairwise assumptions elsewhere
(the two-wing-only dominance rule, wall-exposure-trimming, valley/ridge
clipping for a single reflex point, the doppelpultdach hand-built-box
branch) -- see `plans/TZ-WING-RECOGNITION-001.md`'s own "Explicitly out of
scope" section. Nothing in this file is imported by render-exterior.py.
"""
import roof_wings as rw

DEFAULT_TOL_M = rw.DEFAULT_TOL_M


def _bbox(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), max(xs), min(ys), max(ys)


def _missing_corners(poly, x0, x1, y0, y1, tol):
    """Which of the bounding box's four corners are NOT part of the
    polygon (probed slightly inward, like `roof_wings.recognize_two_
    wings()`'s own single-corner check -- a corner exactly on the boundary
    is not well-defined for point-in-polygon, so never probe exactly on
    it)."""
    inset = tol / 2
    probes = {
        "bl": (x0 + inset, y0 + inset),
        "br": (x1 - inset, y0 + inset),
        "tl": (x0 + inset, y1 - inset),
        "tr": (x1 - inset, y1 - inset),
    }
    return {name for name, (px, py) in probes.items() if not rw.point_in_polygon(px, py, poly)}


def _arrangement_coverage_matches(poly, wings, tol):
    """EXACT coverage check (Codex's own recommendation, stronger than
    `roof_wings._grid_coverage_matches()`'s sampled grid): for an
    axis-aligned simple polygon, every point where the TRUE inside/outside
    classification can change lies exactly on one of the polygon's own
    vertex coordinates -- and every point where the CANDIDATE coverage can
    change lies on one of the WINGS' own edge coordinates. Building the
    arrangement from only the polygon's own vertices is not enough: a
    wing edge that falls strictly between two polygon vertices (e.g. a
    wrong construction that under-covers by stopping short partway across
    a straight run of the true polygon) would never get its own grid line,
    and the resulting cell -- straddling the real mismatch -- would sample
    on the wrong side of it. Caught by this module's own test suite, not
    by reasoning about the check in the abstract."""
    x0, x1, y0, y1 = _bbox(poly)
    wing_xs = {c for w in wings for c in (w[0], w[1])}
    wing_ys = {c for w in wings for c in (w[2], w[3])}
    xs = sorted({p[0] for p in poly} | {x0, x1} | wing_xs)
    ys = sorted({p[1] for p in poly} | {y0, y1} | wing_ys)

    def in_any_wing(x, y):
        return any(wx0 - 1e-9 <= x <= wx1 + 1e-9 and wy0 - 1e-9 <= y <= wy1 + 1e-9
                   for wx0, wx1, wy0, wy1 in wings)

    for i in range(len(xs) - 1):
        if xs[i + 1] - xs[i] < 1e-9:
            continue
        cx = (xs[i] + xs[i + 1]) / 2
        for j in range(len(ys) - 1):
            if ys[j + 1] - ys[j] < 1e-9:
                continue
            cy = (ys[j] + ys[j + 1]) / 2
            if rw.point_in_polygon(cx, cy, poly) != in_any_wing(cx, cy):
                return False
    return True


def _normalize(poly):
    if rw._signed_area(poly) < 0:
        poly = list(reversed(poly))
    return poly


def _reflex_ok(poly, x0, x1, y0, y1, reflex_points, tol):
    """Same degenerate-input guard as `recognize_two_wings()`: a reflex
    point too close to the bbox edge is rejected outright, never rounded
    into a hairline wing."""
    for rx, ry in reflex_points:
        if not (x0 + tol < rx < x1 - tol and y0 + tol < ry < y1 - tol):
            return False
    return True


def _try_two_wing_diagonal(poly, p_lo, p_hi, x0, x1, y0, y1, missing, tol):
    """The simpler of the two "reflex points don't share a coordinate"
    families: a diagonally-offset pair of overlapping rectangles, no
    separate connector needed (found empirically -- `roof_wings.test.py`'s
    own existing `Z_SHAPE` fixture, already used to assert the EXISTING
    one-reflex-only `recognize_two_wings()` correctly rejects it, turns
    out to be exactly this case once you allow two wings that don't each
    span a FULL bbox axis)."""
    if missing == {"br", "tl"}:
        rect_1 = (x0, p_lo[0], y0, p_hi[1])
        rect_2 = (p_hi[0], x1, p_lo[1], y1)
    elif missing == {"bl", "tr"}:
        rect_1 = (p_lo[0], x1, y0, p_hi[1])
        rect_2 = (x0, p_hi[0], p_lo[1], y1)
    else:
        return None
    wings = (rect_1, rect_2)
    if not _arrangement_coverage_matches(poly, wings, tol):
        return None
    return {
        "shape": "Z",
        "wings": wings,
        "roles": ("rect_1", "rect_2"),
        "reflex_points": (p_lo, p_hi),
        "junctions": (("rect_1", "rect_2"),),
    }


def _connector_y_banded(x0, x1, y0, y1, p_lo, p_hi, missing):
    """Construction assuming the CONNECTOR spans the full y-range (narrow
    in x), with `p_lo`/`p_hi` the two reflex points sorted by y (`p_lo`
    the smaller). `arm_lo` sits near `y0`, `arm_hi` near `y1` -- each
    extended sideways through the connector's OWN far edge, matching the
    T-shape's "arms extend through the stem's far side" convention.
    Returns `None` if `missing` isn't one of the two diagonal patterns
    this construction handles."""
    connector_lo, connector_hi = sorted((p_lo[0], p_hi[0]))
    if missing == {"bl", "tr"}:
        arm_lo = (connector_lo, x1, y0, p_lo[1])
        arm_hi = (x0, connector_hi, p_hi[1], y1)
    elif missing == {"br", "tl"}:
        arm_lo = (x0, connector_hi, y0, p_lo[1])
        arm_hi = (connector_lo, x1, p_hi[1], y1)
    else:
        return None
    connector = (connector_lo, connector_hi, y0, y1)
    return connector, arm_lo, arm_hi


def _transpose_rect(rect):
    x0, x1, y0, y1 = rect
    return (y0, y1, x0, x1)


def _transpose_point(pt):
    return (pt[1], pt[0])


_TRANSPOSE_CORNER = {"bl": "bl", "tr": "tr", "br": "tl", "tl": "br"}


def _try_three_wing_connector(poly, p_lo, p_hi, x0, x1, y0, y1, missing, tol):
    """The narrow-bridging-connector Z/S family (Codex's own illustrative
    example): two arms that do NOT themselves overlap, joined by a third,
    narrower rectangle. Tried only after the simpler two-wing diagonal
    construction has already failed to reproduce the polygon exactly.

    Tries the y-banded construction first (connector spans full y); if
    that doesn't reproduce the polygon exactly, tries the x-banded case
    NOT via a second, separately hand-derived mirror formula (the first
    attempt at that, for this exact function, produced a real bug --
    `arm_lo`/`arm_hi` swapped against the wrong reflex point -- caught
    only by the exact-coverage check, not by eyeballing the algebra) but
    by TRANSPOSING the whole problem (swap x and y everywhere), reusing
    the identical, now-verified y-banded formula, then transposing the
    result back. Reusing one proven formula via a coordinate swap is
    safer than maintaining two independently-derived mirror-image ones."""
    got = _connector_y_banded(x0, x1, y0, y1, p_lo, p_hi, missing)
    if got and _arrangement_coverage_matches(poly, got, tol):
        connector, arm_lo, arm_hi = got
        return {
            "shape": "Z",
            "wings": (connector, arm_lo, arm_hi),
            "roles": ("connector", "arm_lo", "arm_hi"),
            "reflex_points": (p_lo, p_hi),
            "junctions": (("connector", "arm_lo"), ("connector", "arm_hi")),
        }

    t_p_lo, t_p_hi = sorted((_transpose_point(p_lo), _transpose_point(p_hi)), key=lambda p: p[1])
    t_missing = {_TRANSPOSE_CORNER[m] for m in missing}
    got = _connector_y_banded(y0, y1, x0, x1, t_p_lo, t_p_hi, t_missing)
    if not got:
        return None
    t_connector, t_arm_lo, t_arm_hi = got
    wings = (_transpose_rect(t_connector), _transpose_rect(t_arm_lo), _transpose_rect(t_arm_hi))
    if not _arrangement_coverage_matches(poly, wings, tol):
        return None
    return {
        "shape": "Z",
        "wings": wings,
        "roles": ("connector", "arm_lo", "arm_hi"),
        "reflex_points": (p_lo, p_hi),
        "junctions": (("connector", "arm_lo"), ("connector", "arm_hi")),
    }


def _try_t_shape(poly, r1, r2, x0, x1, y0, y1, missing, tol):
    """A classic T: the two reflex points share ONE coordinate (the
    "waist" level where the stem meets the bar), and exactly one bbox
    edge's both corners are missing (the stem's own, narrower, far side)."""
    shared_y = abs(r1[1] - r2[1]) < tol
    shared_x = abs(r1[0] - r2[0]) < tol
    if shared_y == shared_x:      # neither or both -- not a clean T
        return None
    if shared_y:
        waist = (r1[1] + r2[1]) / 2
        stem_lo, stem_hi = sorted((r1[0], r2[0]))
        if missing == {"bl", "br"}:
            bar_lo, bar_hi = waist, y1
        elif missing == {"tl", "tr"}:
            bar_lo, bar_hi = y0, waist
        else:
            return None
        stem = (stem_lo, stem_hi, y0, y1)
        arm_1 = (x0, stem_hi, bar_lo, bar_hi)
        arm_2 = (stem_lo, x1, bar_lo, bar_hi)
    else:
        waist = (r1[0] + r2[0]) / 2
        stem_lo, stem_hi = sorted((r1[1], r2[1]))
        if missing == {"bl", "tl"}:
            bar_lo, bar_hi = waist, x1
        elif missing == {"br", "tr"}:
            bar_lo, bar_hi = x0, waist
        else:
            return None
        stem = (x0, x1, stem_lo, stem_hi)
        arm_1 = (bar_lo, bar_hi, y0, stem_hi)
        arm_2 = (bar_lo, bar_hi, stem_lo, y1)
    wings = (stem, arm_1, arm_2)
    if not _arrangement_coverage_matches(poly, wings, tol):
        return None
    return {
        "shape": "T",
        "wings": wings,
        "roles": ("stem", "arm_1", "arm_2"),
        "reflex_points": (r1, r2),
        "junctions": (("stem", "arm_1"), ("stem", "arm_2"), ("arm_1", "arm_2")),
    }


def recognize_multi_wing(poly, tol=DEFAULT_TOL_M):
    """Try to read `poly` as a T or Z/S shape (exactly two reflex
    vertices) -- the two-reflex generalisation of `roof_wings.recognize_
    two_wings()`. Returns `None` for anything that doesn't match one of
    the explicit, verified constructions (including shapes that merely
    HAVE two reflex vertices without being a genuine T/Z, e.g. a U-shaped
    notch or an unsupported staircase -- see this module's own tests for
    worked rejection cases), exactly like `recognize_two_wings()` returns
    `None` for anything that isn't a genuine simple L.

    Returns a dict with keys `shape` ("T" or "Z"), `wings` (a tuple of
    2 or 3 `(x0,x1,y0,y1)` rectangles), `roles` (parallel names), `
    reflex_points`, and `junctions` (which named wings share a real
    overlap) -- or `None`.
    """
    if len(poly) < 3:
        return None
    poly = _normalize(poly)
    reflex = rw._reflex_vertices(poly)
    if len(reflex) != 2:
        return None
    r1, r2 = poly[reflex[0]], poly[reflex[1]]
    x0, x1, y0, y1 = _bbox(poly)
    if not _reflex_ok(poly, x0, x1, y0, y1, (r1, r2), tol):
        return None
    missing = _missing_corners(poly, x0, x1, y0, y1, tol)
    if len(missing) != 2:
        return None

    adjacent_pairs = ({"bl", "br"}, {"tl", "tr"}, {"bl", "tl"}, {"br", "tr"})
    diagonal_pairs = ({"bl", "tr"}, {"br", "tl"})

    if missing in adjacent_pairs:
        return _try_t_shape(poly, r1, r2, x0, x1, y0, y1, missing, tol)
    if missing in diagonal_pairs:
        p_lo, p_hi = sorted((r1, r2), key=lambda p: p[1])
        got = _try_two_wing_diagonal(poly, p_lo, p_hi, x0, x1, y0, y1, missing, tol)
        if got:
            return got
        return _try_three_wing_connector(poly, p_lo, p_hi, x0, x1, y0, y1, missing, tol)
    return None

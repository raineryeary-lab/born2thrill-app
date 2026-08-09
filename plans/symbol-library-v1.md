# Symbol library — canonical type list

Status: IMPLEMENTED in the Simplifier as of 2026-08-09.

The vocabulary below is built: 39 symbols in `static/symbol-catalog.js`, the
stamp/path/rectangle tools, and one SVG per symbol in `static/symbols/` split
out of Rainer's own drawings. What is NOT built is downstream — no renderer
reads `symbols`, and the style packs that map key -> model + finish do not
exist yet.

Source: `Möbel3svg.svg` (referred to below as the authoritative file), drawn by
Rainer. Two earlier exports (`möbel 1.svg`, `Möbel copy.svg`) are superseded —
they carried embedded PNGs overhanging the linework, which broke measurement.

## Decided 2026-08-08

1. **Keys are German**, matching the drawings.
2. **Assemblies place as one unit** — `essgruppe_6` and `playstation_gruppe`
   are placed with a single symbol, not piece by piece.
3. **The renderer resolves collisions.** The annotator places a footprint; the
   3D pass arranges models inside it so nothing intersects a wall, a fixture,
   or another piece.
4. **Dimensions are measured from the drawings**, not invented. See below.

## How the dimensions were obtained

The drawings are to a single consistent scale. Calibrated against the one
dimension Rainer confirmed directly — Doppelbett 1800 × 2000 — the sheet is
**33.5 mm per SVG unit**: 2000/59.7 = 33.5 and 1800/53.5 = 33.6, the same
figure from both axes independently.

Two further confirmations, neither used for calibration:

- `Badewanne` measures 1710 × 760 against the German standard 1700 × 750.
- `Abseitenbereich` measures 1910 × **200** against Rainer's stated 150 deep.

Measurement is via the browser's `getBBox()`, which resolves transforms and the
full SVG path grammar. Two hand-written parsers were tried first and both gave
answers wrong by an order of magnitude, because path data uses relative
commands (`m 10,10 l 5,0` are deltas, not points).

**gemessen** is the measured value. **Norm** is the standard product size where
one exists, for reference — the measured value is authoritative unless Rainer
says otherwise.

## Sanitär

| Key | Quelle | gemessen (B × T) | Norm | Anmerkung |
|---|---|---|---|---|
| `vorwandinstallation` | Abseitenbereich, ~1, ~2 | 1910×200 · 3840×190 · 1940×190 | × 1500 hoch ✔ | Not furniture. WC and Waschtisch mount onto it. Three run lengths |
| `wand_wc` | WC, WC1, toilette, wc | 340×480 · 350×500 | 360 × 540 | Four names, one object |
| `waschtisch` | einzelwaschbecken | 570 × 450 | 600 × 550 | |
| `handwaschbecken` | waschbecken_klein | 430 × 340 | 450 | The small guest-WC basin |
| `doppelwaschtisch` | doppelwachtisch | 1090 × 450 | 1200 × 550 | Source name typo |
| `badewanne` | Badewanne | 1710 × 760 | 1700 × 750 | |
| `eckbadewanne` | Badewanne_Eckig | 760 × 1710 | — | Drawn rotated; same footprint as `badewanne` |
| `dusche` | Dusche | 930 × 1360 | 900 × 1350 | Rectangular, not square |
| `dusche_112` | Dusche_112 | 990 × 1200 | — | Larger variant |
| `badheizkoerper` | Badheizkörper | 100 × 550 | — | Plan view: depth × width |

## Küche

German carcass norm: 720 mm carcass, 600 deep, widths on a 100 grid; working
height 850–900 with plinth and worktop. Wall units 350 deep.

| Key | Quelle | gemessen (B × T) | Norm | Anmerkung |
|---|---|---|---|---|
| `kuechenzeile` | theke | — | **600 tief** | **Path tool** — drawn along walls, 90° corners |
| `kuecheninsel` | insel | (960 × 1520 drawn) | — | **Rectangle tool** — dragged to fit the room |
| `kochfeld` | herd | 470 × 740 | 600 × 520 | **Surface-mounted** — placed onto a Küchenzeile or Insel |
| `spuele` | sink | 530 × 950 | 600 × 600 | **Surface-mounted.** Distinct from the bathroom basin |
| `hochschrank_herd` | Hochherd | 570 × 600 | 600 × 600 | Floor-standing |
| `kuehlschrank` | Kühlschrank | 570 × 600 | 600 × 600 | Floor-standing |

## Wohnen

| Key | Quelle | gemessen (B × T) | Norm | Anmerkung |
|---|---|---|---|---|
| `ecksofa` | L-couch | 1670 × 2380 | 2800 × 1800 | Still carries 3 raster elements, but measures sensibly |
| `sofa_1sitzer` | _x31__sitzer | 1010 × 1030 | 900 × 900 | |
| `sofa_2sitzer` | _x32_-sitzer | 820 × 1600 | 1600 × 900 | Drawn rotated |
| `sofa_3sitzer` | _x33_-sitzer | 2270 × 820 | 2100 × 900 | |
| `hocker` | sessel, sessl | 500 × 500 | — | **Stool**, not an armchair — kids' room / Playstation seating per Rainer. Two spellings, one object |
| `couchtisch` | coffeetable, coffeetable1 | 520×850 · 760×570 | 1100 × 600 | Two different tables |
| `lowboard` | lowboard, lowboard1–3, lowboard_TV | 320 × 2110 | 2100 × 350 | |
| `fernseher` | TV, TV1, Fernseher, Fernseher1 | 180 × 1140 | — | |
| `sideboard` | sideboard, sideboard1 | 760×220 · 1880×320 | — | Two sizes |
| `playstation_gruppe` | Playstation_gruppe | 1230 × 1700 | — | **Assembly**, one unit |

## Schlafen und Stauraum

| Key | Quelle | gemessen (B × T) | Norm | Anmerkung |
|---|---|---|---|---|
| `doppelbett` | Doppelbett | 2000 × 1790 | **1800 × 2000** ✔ | Calibration reference |
| `einzelbett` | Einzelbett | 950 × 1930 | 900 × 2000 | |
| `kleiderschrank` | schrank, Schrank | 1050×550 · 740×1370 | — | Two variants |
| `schrank_40` | schrank_40 | 1070 × **370** | 400 tief | **The number is the depth**, not the width |
| `schrank_60` | Schrank_60 | 1070 × **590** | 600 tief | |
| `abstellschrank` | abstellschränke | 2530 × 380 | — | A run of cupboards |
| `garderobe` | garderobe | 900 × 320 | — | |

## Essen, Büro, Hauswirtschaft

| Key | Quelle | gemessen (B × T) | Norm | Anmerkung |
|---|---|---|---|---|
| `essgruppe_6` | dning_6 | 1710 × 1600 | — | **Assembly** — table + 6 chairs. Typo `dning` |
| `schreibtisch` | schreibtisch | 970 × 1140 | 1600 × 800 | Adult desk |
| `schreibtisch_kind` | schreibtisch1 | 660 × 1140 | — | Child's desk — the two drawn sizes are the two desks |
| `schreibtischstuhl` | Schreibtischstuhl | 610 × 610 | 600 × 600 | |
| `waschmaschine` | washer | 570 × 570 | 600 × 600 | |
| `trockner` | dryer | 570 × 570 | 600 × 600 | Stackable with the washer |

## Excluded

**Container groups, not symbols:** `Layer_3`, `Livingroom_1`, `Livingroom_2`,
`kitchen`, `wc`, `wascher_dryer`, `Fernsehen_lowboard`.

**Heights** are not in the drawings — a plan symbol has only a footprint. They
come from the norm column or from the 3D model the style pack selects.

## Four kinds of symbol

Not everything on the palette behaves the same way, and conflating them is why
the first auto-placement attempt produced a sofa against a wall and an empty
room.

**1. Fixed footprint.** Real dimensions that must be respected — a WC is 360
wide or it is wrong. Collision checks use the measured box.
Most sanitary, appliances, beds, `schrank_40`/`_60`.

**2. Indicative footprint.** The drawn size is a placeholder; the style pack
decides the real one. A `couchtisch` comes in every size there is, so the
symbol marks *where a coffee table goes*, not how big it is. Collision checks
use whatever the chosen model actually measures, not the drawn box.
`couchtisch`, `sideboard`, sofas, `lowboard`, `hocker`.

**3. Path tools.** Drawn along walls rather than dropped as a block, exactly
like the existing stairs tool — which already stores a path plus a width, so
the pattern and most of the code exist.

- `kuechenzeile`: **600 mm deep, corners constrained to 90°**, any length.
  One tool draws a straight run, an L or a U.
- `vorwandinstallation`: **150 mm deep, 1500 high**, any length, same 90°
  constraint. The three drawn `Abseitenbereich` variants (1910, 1940 and 3840
  long at the same 190 depth) are not three symbols — they are one tool at
  three lengths.

A path tool needs no fixed footprint in the catalogue, only its depth
constraint. That answers the "stretchable length" question from the earlier
draft: it isn't stretchable, it's drawn.

**4. Rectangle tool.** Dragged out as a box, free-standing rather than run
along a wall. Both dimensions are chosen by the annotator, so the catalogue
stores no footprint at all — only what the thing is.

- `kuecheninsel`: an island's size follows the room, not a product norm.

Likely to serve more than the island once it exists — built-in wardrobe runs,
niches, `abstellschrank` runs and any custom joinery are the same shape of
problem. Worth building as a general tool that takes a type, not as an
island-specific one.

## What a placement stores

```json
{
  "id": "…",
  "floor_level": "groundfloor",
  "symbol": "eckbadewanne",
  "room_id": "bad",
  "position": { "x": 0.42, "y": 0.31 },
  "rotation_deg": 90,
  "mirrored": true
}
```

**Rotation** snaps to 90° by default, since almost everything aligns to a wall,
with free rotation available for the exceptions. The renderer applies the same
angle to the 3D model, so one annotation drives both the 2D glyph and the mesh.

**Mirror** is not cosmetic — several symbols are handed and would otherwise
need drawing twice:

- `eckbadewanne`, `dusche` in a corner — left- or right-handed
- `ecksofa` — the chaise on the left or the right
- `kuechenzeile` as an L — which leg runs along which wall
- `schreibtisch` — return on either side

One drawing plus a mirror flag covers both hands.

Render-side consequence worth recording now: mirroring a mesh is a negative
scale on one axis, which inverts its normals. They have to be recalculated or
the model renders inside-out — lit from within, black at grazing angles. Cheap
to do at import, easy to forget, and the symptom looks like a material bug
rather than a transform bug.

Path and rectangle tools need neither flag: a path already carries its own
direction and corners, and a dragged rectangle is defined by where it was
dragged.

### Height: three cases, none of them guessed

- **Floor-standing** — the default. Base at floor level.
- **Wall-mounted** — `wand_wc`, `waschtisch`, `badheizkoerper`, mirrors and
  art. Base at a mount height. The existing `MOUNT_HEIGHT_MM` in
  `furniture-catalog.mjs` already does this, though note the bug found on
  2026-08-08: mount height is the item's *centre*, not its base, and treating
  it as the base put a 1600 mm mirror's top 600 mm above a 2400 mm wall.
- **Surface-mounted** — `kochfeld` and `spuele` only. Placed onto a
  `kuechenzeile` or `kuecheninsel`, so their height is the worktop, 900 mm.

The renderer should take the surface height from whatever the symbol was
placed on rather than assuming 900, so a raised bar counter or a lowered
baking station still works. If nothing is underneath, that is an annotation
error worth reporting — a hob floating in mid-air is exactly the kind of thing
that should fail loudly rather than render wrong.

## Collision avoidance

Three checks, cheapest first, all now possible because the footprints above are
real:

- **Footprint inside room.** The rotated box must lie within the room polygon.
  Today only the centre point is tested, which is why the 2026-08-08 render put
  a floor lamp outside its room in the notch of an L-shaped polygon — centre
  inside, footprint not.
- **Footprint against walls**, accounting for wall thickness.
- **Footprint against other symbols**, pairwise within a room.

Assemblies are one box for collision purposes; contents lay out relative to
that box, so the six chairs of an `essgruppe_6` cannot collide or drift apart.

## Open

- `kochfeld` measures 470 × 740 against a 600 × 520 norm hob. Possibly drawn as
  a range rather than a built-in hob. It also sits *in* a `kuechenzeile` rather
  than on the floor, so it may belong to that path tool as a fitting rather
  than as a standalone symbol — same question for `spuele`.
- `kleiderschrank` is drawn at two sizes (1050×550 and 740×1370). Fixed or
  indicative?

## Sources

Kitchen norms: [lieblingskuechen.de](https://www.lieblingskuechen.de/standard-kuechenschrank-masse/),
[der küchenmacher](https://www.derkuechenmacher.de/lp/kuechenmasse.html).
Sofas: [porta](https://porta.de/inspiration/ratgeber/sofamasse).
Sanitary: [BauNetz Wissen](https://www.baunetzwissen.de/bad-und-sanitaer/fachwissen/planungsgrundlagen/abmessungen-von-sanitaerobjekten-172702).

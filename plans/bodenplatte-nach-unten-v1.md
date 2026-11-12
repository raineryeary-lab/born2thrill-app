# Bodenplatte wächst nach unten — Möbel stehen auf dem Boden, nicht darin

Status: APPROVED (Rainer, 2026-08-25: "the bed bathtub and shower were about
20cm too far into the ground so they vanish in the floor" → "ok")

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Die Bodenplatte wächst nach OBEN. Die begehbare Oberfläche liegt dadurch
220 mm über z = 0, während jedes Möbelstück auf z = 0 gesetzt wird. Alles,
was auf dem Boden steht, versinkt exakt eine Plattendicke tief.

## Current evidence and behavior

Gemessen in Blender an der gebauten `bungalow_039/interior-modern-baseline.blend`
(Welt-Koordinaten, mm):

```
floor-…            unten    0.0   oben  220.0     <- Platte waechst nach oben
badewanne-6        unten    0.0   oben  580.0
doppelbett-13      unten    0.0   oben  500.0
dusche_gross-tray  unten    0.0   oben  120.0     <- vollstaendig begraben
essgruppe_stuhl    unten    0.0   oben  844.0     <- Sitz auf Knoechelhoehe
```

`polygon_object` (render-furnished-dollhouse.py) extrudiert mit
`solidify.offset = -1`, also **gegen** die Flächennormale — und die folgt der
Umlaufrichtung des Polygons. Die Raumpolygone von `bungalow_039` laufen alle
im Uhrzeigersinn (negative Fläche), also zeigt die Normale nach -Z und die
Platte wächst nach +Z.

**Und es ist nicht einmal einheitlich.** Dieselbe Messung an
`onehalfstorey_029/interior-modern-baseline.blend`:

```
floor-   5 Objekte   z-Bereiche: [(-220, 0), (0, 220)]
```

In EINEM Geschoss liegen manche Raumböden bei -220..0 und andere bei 0..220 —
je nachdem, wie der Raum gezeichnet wurde. Das ist der Roadmap-Punkt
"floor-slab z depending on polygon winding", jetzt mit Zahlen.

## Exact scope

1. Helfer `_winding_nach_unten(points_mm)` in `render-furnished-dollhouse.py`:
   dreht die Punktreihenfolge, wenn die vorzeichenbehaftete Fläche negativ ist.
   Ergebnis: die Normale zeigt immer nach +Z, `offset = -1` extrudiert immer
   nach unten.
2. Nur die **Raum-Bodenplatten** (`floor-<room id>`) gehen durch den Helfer.
   Die Platte belegt dann -220..0 statt 0..220; die begehbare Fläche liegt auf
   z = 0, wo alle Möbel, Montagehöhen und Schnitthöhen sie ohnehin erwarten.

## Files in scope

- `scripts/render-furnished-dollhouse.py`
- `scripts/render-furnished-dollhouse.test.py`

## Explicitly out of scope

- `slab-under-wall-*`: die Streifen unter den Wänden haben ihre Umlaufrichtung
  ausdrücklich von Hand gesetzt, um den Spalt zwischen den Geschossen zu
  füllen. Sie bleiben, wie sie sind.
- Treppenstufen und Podeste (`stair-step-*`, `stair-podest-*`) laufen durch
  dieselbe Funktion und könnten denselben Fehler haben. Nicht angefasst,
  eigener Punkt für die Roadmap.
- Möbel-Z-Positionen. Es wird der Boden korrigiert, nicht jedes Möbelstück.

## API, schema, and data-contract effects

Keine. Nur Geometrie im Bau.

## Acceptance criteria

1. Bodenplatten liegen bei -220..0 (Oberfläche auf z = 0), in jedem Raum
   dieselbe Richtung.
2. `bungalow_039`: Badewanne, Bett, Duschwanne und Stühle stehen mit ihrer
   Unterkante auf der Bodenoberfläche, nicht 220 mm darunter.
3. `onehalfstorey_029` (zwei Geschosse): kein neuer Spalt zwischen den
   Geschossen — die Streifen unter den Wänden füllen weiter, was sie vorher
   füllten. **Vor und nach der Änderung gemessen, nicht abgeschätzt.**
4. Kein bestehender Test wird geändert.

## Tests and verification commands

```
python scripts/render-furnished-dollhouse.test.py
python scripts/build-simplifier-render-plan.test.py
```

Dazu die Blender-Messung an beiden Häusern (Kriterien 1-3), da die
Geometrie nur im gebauten .blend beobachtbar ist.

## Protected and risky paths

Der Geschossspalt ist der bekannte Rückfall (Rainer hat ihn im August
fotografiert). Kriterium 3 ist deshalb eine Messung an einem echten
Zweigeschosser, kein Argument.

## Rollback

Den Helferaufruf an der einen Stelle entfernen.

# Möbel: Ecke ziehen verankert die Gegenecke, statt symmetrisch zur Mitte

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Beim Ziehen eines Eckgriffs im Möbel-Editor soll die **gegenüberliegende Ecke
stehenbleiben** und nur die gezogene Seite wandern. Heute wächst das Möbel
symmetrisch um seinen Mittelpunkt: zieht man eine Ecke 200 mm nach außen,
wandert die Gegenecke 200 mm in die andere Richtung, und ein an der Wand
stehendes Sofa löst sich beim Vergrößern von der Wand.

## Current evidence and behavior

`src/app/floorplan-workbench/page.tsx:491-503`:

```
// Symmetric about the centre: the handle is a corner, so the pointer
// describes half-extents.
const local = worldDeltaToLocalMm(x - sizing.centre[0], y - sizing.centre[1], sizing.rotationDeg);
onFurnitureResize(sizing.id, Math.abs(local.x) * 2, Math.abs(local.y) * 2);
```

Der Mittelpunkt (`position_mm`) bleibt unverändert; nur `footprint_mm` wächst.
`furnitureResize.current` (Zeile 615) merkt sich `{ id, centre, rotationDeg }` --
**welche** Ecke gegriffen wurde, wird gar nicht gespeichert (`furniture.tsx:544-551`
übergibt den Index nicht).

Zusätzlich: die Griffe liegen innerhalb der Gruppe mit
`scale(${item.mirrored ? -1 : 1} 1)` (`furniture.tsx:533`), die x-Vorzeichen sind
bei gespiegelten Möbeln also getauscht.

## Repository baselines

Repo: `born2thrill-local-workbench` (kein Git-Repo im Arbeitsverzeichnis laut
Umgebung -- Baseline ist der Dateistand vom 2026-08-25). Dev-Server läuft auf
:3000, Annotator auf :8765.

## Exact scope

1. Neue reine Funktion `anchoredResizeMm({ centreMm, rotationDeg, mirrored,
   widthMm, depthMm, cornerX, cornerY, pointerMm })` in
   `src/lib/generator/furniture-document.mjs`.
   - Ankerpunkt = Weltposition der Gegenecke, **einmal beim Greifen** bestimmt
     (nicht laufend neu), inklusive Spiegelung: `cornerXEff = mirrored ? -cornerX : cornerX`.
   - `delta = worldDeltaToLocalMm(pointer - anker, rotationDeg)`
   - `width = max(50, |delta.x|)`, `depth = max(50, |delta.y|)`
   - neue Mitte = Anker + Rückdrehung von `(sign(delta.x) * width/2, sign(delta.y) * depth/2)`
2. `furniture.tsx`: `onResizeGrab(event, item, cornerX, cornerY)` -- die schon
   vorhandenen `[sx, sy]` mitgeben.
3. `page.tsx`: `furnitureResize.current` merkt sich zusätzlich Anker,
   Ausgangsmaße und Spiegelung; im PointerMove `anchoredResizeMm` aufrufen und
   **beides** setzen: `onFurnitureResize(id, width, depth)` und
   `onFurnitureMove(id, neueMitte)`.

Keine Änderung am Dateiformat: `position_mm` und `footprint_mm` existieren
bereits und werden nur anders berechnet.

## Files in scope

- `src/lib/generator/furniture-document.mjs`
- `src/lib/generator/furniture-document.test.mjs` (neu oder erweitert)
- `src/app/floorplan-workbench/furniture.tsx`
- `src/app/floorplan-workbench/page.tsx`

## Explicitly out of scope

- Kanten-Griffe (nur eine Achse) -- heute gibt es nur die vier Eckgriffe.
- Seitenverhältnis-Sperre / Shift-Taste.
- Rechteck-Möbel mit `points_mm` (`onRectCornerGrab`), die haben schon eigene
  Eckenlogik.
- Der Annotator (`floorplan-simplifier`), Renderer und Zertifikate.

## API, schema, and data-contract effects

Keine. `furniture.json` behält Feldnamen und Einheiten (mm).

## Acceptance criteria

1. Sofa unrotiert, Griff unten rechts nach außen gezogen: obere linke Ecke
   bleibt millimetergenau stehen.
2. Dasselbe bei `rotation_deg` 90 und 270 -- Breite/Tiefe werden nicht getauscht.
3. Dasselbe bei `mirrored: true` -- es bleibt die optisch gegenüberliegende Ecke
   stehen, nicht die gespiegelte.
4. Über den Anker hinausziehen ergibt 50 mm Mindestmaß, kein negatives Maß und
   kein Springen der Mitte.
5. Im laufenden Editor an einem echten Haus nachgemessen (Werte aus
   `furniture.json` vorher/nachher), nicht nur im Unit-Test.

## Tests and verification commands

Neu in `src/lib/generator/furniture-document.test.mjs`: vier Fälle
(0°, 90°, gespiegelt, Mindestmaß), die die Ankerecke vorher/nachher vergleichen.

```
node --test src/lib/generator/furniture-document.test.mjs
npx tsc --noEmit
```

Bestehende Tests werden nicht geändert.

## Protected and risky paths

Der Möbel-Editor schreibt in `furniture.json` des jeweiligen Hauses. Risiko:
ein Vorzeichenfehler verschiebt beim Ziehen die Mitte -- deshalb Anker beim
Greifen einfrieren und Acceptance-Kriterium 5 am echten Haus prüfen.

## Rollback

Die drei Dateien zurücksetzen; die Funktion ist additiv, der alte
symmetrische Zweig kann in einer Zeile wiederhergestellt werden.

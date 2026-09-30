# Kücheninsel: Rechteck bleibt Rechteck (und lässt sich ziehen)

Status: APPROVED (Rainer, 2026-08-25: "please check your code on the
kuecheninsel … when finished it looked correct but the generated blender file
always ends up at 45 degrees")

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Zwei Fehler an derselben Stelle:

1. **Die Insel landet schräg im Blender.** Im Editor sieht sie richtig aus, in
   der .blend steht sie diagonal.
2. **Sie lässt sich kaum zeichnen.** Zwei Klicks ohne jede Vorschau; wer zu eng
   klickt, bekommt eine winzige Insel und muss sie hinterher an einem kleinen
   Griff aufziehen.

## Current evidence and behavior

**Zu 1 — gemessen an `bungalow_039`, `furniture/floor-0.json`:**

```
kuecheninsel  points_mm [[6600, 8850], [8450, 8150]]   (2 Punkte)
```

Zwei gegenüberliegende Ecken — genau das, was das Werkzeug erzeugt
(`page.tsx:455`: "A rectangle IS two opposite corners — the second click
finishes it").

`scripts/build-simplifier-render-plan.py:2758` entscheidet aber:

```python
"build": "rect" if len(points) > 2 and key == "kuecheninsel" else "path",
```

Bei 2 Punkten ist `len(points) > 2` falsch → `build: "path"` → der Renderer
baut einen Küchenzeilen-Lauf **entlang der Diagonalen**. Aus dx 1850 / dy -700
wird ein Balken unter rund 21°; bei einer quadratischen Insel sind es 45°.

Die zweite, korrigierte Fassung derselben Zeile hat die Bedingung nicht:
`build-simplifier-render-plan.py:2024` → `"rect" if key == "kuecheninsel"`.
Zwei Zweige, zwei Meinungen — dieselbe Krankheit wie bei der Dachform.

**Zu 2 —** `furniture.tsx:519` zeichnet die Vorschau nur für Nicht-Rechtecke:

```tsx
{draft && draft.length > 0 && getSymbol(draftKey || "")?.placement !== "rect" && <polyline …
```

Für die Insel gibt es also zwischen erstem und zweitem Klick **nichts zu sehen**.

## Repository baselines

Dateistand 2026-08-25. `bungalow_039` ist veröffentlicht
(`veroeffentlicht_build_alt`) — die falsche Insel steckt in den ausgelieferten
Bildern.

## Exact scope

1. `build-simplifier-render-plan.py:2758`: die Bedingung `len(points) > 2`
   entfällt, damit beide Zweige dieselbe Regel haben. Eine Insel ist ein
   Rechteck, egal mit wie vielen Punkten sie gezeichnet wurde —
   `build_rect()` nimmt ohnehin nur die Bounding Box.
2. `furniture.tsx`: Vorschau-Rechteck zwischen erstem Klick und Zeigerposition.
3. `page.tsx`: Ziehen als zweiter Weg — Zeiger drücken, ziehen, loslassen
   erzeugt dasselbe Zwei-Punkte-Rechteck. Die zwei Klicks bleiben, wer sie mag.

## Files in scope

- `scripts/build-simplifier-render-plan.py`
- `scripts/build-simplifier-render-plan.test.py` (neuer Test)
- `src/app/floorplan-workbench/furniture.tsx`
- `src/app/floorplan-workbench/page.tsx`

## Explicitly out of scope

- `build_rect()` im Renderer — es ist korrekt (achsparallel, Rotation 0).
- Andere Rechteck-Symbole als die Insel (`abstellschrank` läuft heute
  bewusst als `path`).
- Neu bauen von `bungalow_039` — eigener Schritt, nach dem Fix.

## API, schema, and data-contract effects

Keine. `points_mm` behält Form und Bedeutung.

## Acceptance criteria

1. Eine Insel mit 2 Punkten ergibt `build: "rect"` im Bauplan.
2. Eine Insel mit 4 Punkten ebenso.
3. Eine Küchenzeile mit 2 Punkten bleibt `path`.
4. Am echten Haus `bungalow_039` nachgemessen: der erzeugte Bauplan sagt
   `rect`, und die gebaute Insel steht achsparallel — nicht nur im Test.
5. Im Editor: während des Zeichnens ist das Rechteck sichtbar, und Ziehen
   erzeugt dieselbe Insel wie zwei Klicks.

## Tests and verification commands

```
python scripts/build-simplifier-render-plan.test.py
npx tsc --noEmit
```

## Protected and risky paths

Zeile 2758 liegt im Hauptpfad für ALLE Möbel. Die Änderung betrifft nur den
Zweig `key == "kuecheninsel"`; Kriterium 3 hält das fest.

## Rollback

Bedingung wieder einsetzen, die zwei UI-Stellen zurücknehmen. Keine Daten
betroffen.

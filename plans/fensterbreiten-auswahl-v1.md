# Normbreiten für Fenster im Annotator

Status: APPROVED (Rainer, 2026-08-26: "we have to add window widths at the
dropdown editing window 68, 80, 101, 131, 151, 171, 300")

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Ein Fenster ist heute genau so breit, wie der Strich lang war, den man
gezogen hat. Es soll eine Auswahl echter Normbreiten geben.

## Current evidence and behavior

- `floorplan-simplifier/static/annotate.html:82-99` hat für Fenster nur zwei
  Auswahlfelder: Lage (`windowContext`) und Typ (`windowType`). **Keine Breite.**
- `annotations.json`, Element eines Fensters: `id`, `type`, `floor_level`,
  `points` (zwei Endpunkte), `review_status`. Kein Breitenfeld.
- `build-simplifier-render-plan.py:1790` nimmt die gezeichnete Länge:
  `"width_mm": round(math.dist(a, b), 1)`.

## Exact scope

1. `static/annotate.html`: neues Feld „Fensterbreite" in den Fenster-Steuerungen.
   Erster Eintrag „aus der Zeichnung" (leer, heutiges Verhalten), danach
   68, 80, 101, 131, 151, 171 und 300 cm.
2. `static/annotate.js`: `windowWidthMetadata()` schreibt `width_mm` in
   Millimetern (680 … 3000) oder `null`; beim Öffnen eines Fensters wird das
   Feld aus `width_mm` gesetzt; beim Werkzeugwechsel zurückgesetzt.
3. `build-simplifier-render-plan.py:1790`: eine gesetzte `width_mm` schlägt die
   gezeichnete Länge. Die Öffnung sitzt weiter auf demselben Mittelpunkt
   (`position`), wird also symmetrisch breiter oder schmaler.

Ohne Punkt 3 wäre die Auswahl eine Attrappe: sichtbar im Editor, wirkungslos
im Bau.

## Files in scope

- `floorplan-simplifier/static/annotate.html`
- `floorplan-simplifier/static/annotate.js`
- `born2thrill-local-workbench/scripts/build-simplifier-render-plan.py`
- `born2thrill-local-workbench/scripts/build-simplifier-render-plan.test.py`

## Explicitly out of scope

- Türbreiten. Dieselbe Mechanik wäre möglich, ist aber nicht verlangt.
- Bestehende Fenster nachträglich auf Normmaße ziehen. Ohne Auswahl bleibt
  alles, wie es ist.
- Prüfen, ob die gewählte Breite in die Wand passt.

## API, schema, and data-contract effects

Ein neues, optionales Feld `width_mm` an Fenster-Elementen in
`annotations.json`. Alte Dateien ohne das Feld verhalten sich unverändert.

## Acceptance criteria

1. Die Auswahl steht im Fenster-Werkzeug und hat die sieben Breiten.
2. Ein Fenster mit gewählter Breite trägt `width_mm` in `annotations.json`.
3. Der Bauplan übernimmt diese Breite statt der Strichlänge.
4. Ohne Auswahl bleibt es exakt beim heutigen Verhalten (Strichlänge).
5. Im laufenden Annotator sichtbar geprüft, nicht nur im Code.

## Tests and verification commands

```
python scripts/build-simplifier-render-plan.test.py
```

Neuer Test: Fenster mit und ohne `width_mm` durch die Öffnungsberechnung.

## Protected and risky paths

`build_floor_walls_and_openings()` wird von BEIDEN Wegen benutzt — Möbel-Editor
und Bau. Kriterium 4 hält fest, dass ohne Auswahl nichts anders wird.

## Rollback

Das Auswahlfeld entfernen und die eine Zeile im Compiler zurücksetzen. Das
Feld in bestehenden Annotationen wird dann ignoriert.

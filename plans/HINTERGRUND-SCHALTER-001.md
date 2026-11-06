# HINTERGRUND-SCHALTER-001: Hintergrund ein- und ausblenden

Status: DONE

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-30: "can we add an option on the tabs with the background show hide background?" Überall, wo die hochgeladene Vorlage hinter dem Grundriss liegt, gibt es einen Knopf zum Aus- und Einblenden. Der Knopf ändert nur die Ansicht.

## Current evidence and behavior

Die Vorlage liegt an zwei Stellen, in zwei Programmen:

- Annotator (8765), Tabs Architektur und Exterior: `<img id="floorImage">` in `static/annotate.html:395`, Quelle `annotate.js:3726`.
- Workbench (3020), Tab Möbel: `ReferenzBild` in `src/app/floorplan-workbench/page.tsx:1015`, eingebunden bei `page.tsx:765`.

Der Tab Dach hat keinen Hintergrund: `dach-editor.js:155-166` lädt das Bild nur, um Maße zu lesen. Dort kommt kein Knopf hin.

Zwei Fallen:

- Annotator: `syncCanvasSize` misst die Zeichenfläche am Bild (`annotate.js:2399-2413`). `display:none` würde die Zeichenfläche auf 0 setzen und die Zeichnung verschieben. Deshalb nur `visibility:hidden`.
- Möbel: Die Raumfläche multipliziert nur, solange ein Bild dahinter liegt (`page.tsx:796`). Ohne Bild muss sie normal gefüllt sein. Der Sichtbereich (`page.tsx:365-374`) bleibt gleich, damit der Plan beim Umschalten nicht springt.

## Repository baselines

- `floorplan-simplifier`: Branch `agent/annotation-window-type-door-swing`, HEAD 8a08d19; `annotate.html`, `annotate.js`, `styles.css` und weitere sind schon geändert (M). Stände bleiben erhalten, Sicherungen `.before-hintergrund`.
- `born2thrill-local-workbench`: Branch `agent/furnished-render-and-annotation-schema`, HEAD 5be1a4e; `page.tsx` ist schon geändert (M), zuletzt durch MOEBEL-EIN-SPEICHERN-001. Sicherung `.before-hintergrund`.

## Exact scope

1. Annotator: Knopf "Hintergrund ausblenden" / "Hintergrund einblenden" in der Zoom-Leiste (`annotate.html:378`), gilt in Architektur und Exterior. Im Dach-Tab wird er versteckt.
2. Ausgeblendet heißt im Annotator `visibility:hidden` am Bild. Zeichnung, Zoom und Klicks bleiben gleich.
3. "Crop image" blendet den Hintergrund wieder ein, weil man sonst blind zuschneidet.
4. Möbel: gleicher Knopf neben dem Zoom (`page.tsx:1609`). Ausgeblendet wird `ReferenzBild` nicht gezeichnet und die Räume haben ihre normale Farbe.
5. Die Wahl gilt für alle Geschosse, solange die Seite offen ist. Nach dem Neuladen oder Tabwechsel in /haus ist der Hintergrund wieder da. So kann niemand später versehentlich ohne Vorlage abzeichnen.

## Files in scope

- `floorplan-simplifier/static/hintergrund-schalter.js` (neu)
- `floorplan-simplifier/static/annotate.html` (Knopf, Skript mit `?v=`)
- `floorplan-simplifier/tests/test_hintergrund_schalter.py` (neu)
- `born2thrill-local-workbench/src/app/floorplan-workbench/page.tsx`
- `born2thrill-local-workbench/scripts/hintergrund-schalter.test.mjs` (neu)
- `born2thrill-app-repo/plans/ROADMAP.md`

## Explicitly out of scope

- Regler für die Deckkraft.
- Merken der Wahl über das Neuladen hinaus.
- Tab Dach, Punkte-Ausrichten-Dialog.
- Gespeicherte Annotationen, Möbel, Bilddateien.

## API, schema, and data-contract effects

Keine. Nur Anzeigezustand im Browser.

## Acceptance criteria

- Architektur und Exterior: Knopf blendet das Bild aus und wieder ein. Bildschirmposition und Größe der Zeichenfläche sind in beiden Zuständen gleich, gemessen mit `getBoundingClientRect`.
- Zeichnen, Zoom und Geschosswechsel funktionieren ausgeblendet; der Zustand bleibt beim Geschosswechsel.
- "Crop image" zeigt den Hintergrund wieder.
- Möbel: Knopf blendet aus und ein, Sichtbereich unverändert, Räume in normaler Farbe, Möbel bleiben klickbar.
- Der Knopf löst kein Speichern aus und gilt nicht als ungespeicherte Änderung.

## Tests and verification commands

Keine bestehenden Tests werden geändert.

```bash
python -m unittest tests.test_hintergrund_schalter tests.test_annotation_viewport
```

```bash
node --test scripts/hintergrund-schalter.test.mjs scripts/furniture-document.test.mjs
```

Danach Prüfung im Browser auf beiden Oberflächen, ohne zu speichern.

## Protected and risky paths

`page.tsx` und `annotate.js` werden auch von anderen Sitzungen bearbeitet: vor dem Ändern Stand prüfen. `annotate.js` selbst wird nicht geändert.

## Rights, provenance, privacy, and security impact

Keine.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference? **No.** Die Änderung setzt nur Anzeigezustand im Browser und schreibt nichts.

## Customer, email, database, deployment, and external effects

Keine.

## Failed-hypothesis log

Keine.

## Rollback

`hintergrund-schalter.js` und die beiden neuen Tests entfernen, `.before-hintergrund`-Sicherungen zurückspielen.

## Unresolved questions

Keine. Entschieden: Knopf statt Deckkraft-Regler, Wahl wird nicht gemerkt.

## Approval record

Rainer, 2026-10-30: "komm schon bauen nicht dann gleich wieder vergessen".

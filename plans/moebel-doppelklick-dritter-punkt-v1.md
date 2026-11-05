# Möbel-Lauf: Doppelklick setzt keinen dritten Punkt mehr

Status: IMPLEMENTED (nachträglich dokumentiert — Änderung wurde vor diesem Plan gemacht)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-09: "mein doppelklick zum abschliessen von der Küchenzeile und
anderen linien endet immer in einen zusätzlichen punkt also eine gerade zeile
mit 2 punkten endet immer in 3 punkte davon sind 2 fast aufeinander".

Ein Doppelklick, der einen gezeichneten Lauf (Küchenzeile,
Vorwandinstallation) abschließt, darf keinen zusätzlichen Punkt erzeugen.

## Current evidence and behavior

- `page.tsx` `onPointerDown` hängt bei jedem Druck einen Punkt an
  `furnitureDraft`. Ein Doppelklick liefert zwei `pointerdown`, also zwei
  Punkte am Ende, danach `onDoubleClick` → `onFurniturePlaceDrawn`.
- `furniture.tsx` `entdoppelt()` zieht Punkte unter `DOPPELT_MM = 60` mm
  zusammen. Herausgezoomt sind ~12 mm/px; ein Wackler von 5+ px liegt über
  60 mm und überlebt — das ist der gemeldete dritte Punkt.

## Repository baselines

- born2thrill-local-workbench, Branch `agent/furnished-render-and-annotation-schema`,
  HEAD `5be1a4e`.
- Arbeitsbaum vorher schon schmutzig: 286 Einträge in `git status --short`,
  `page.tsx` hatte bereits +855/−36 nicht committete Änderungen. Diese gehören
  Rainer und werden nicht angefasst.

## Exact scope

Im Zeichenzweig von `onPointerDown`: für `placement === "path"` wird ein Druck
verworfen, wenn der vorherige Druck < 500 ms her ist und < 10 Bildschirm-Pixel
entfernt liegt (`event.clientX/Y`, `event.timeStamp`). Neue Ref
`letzterDruck`. Etwa 14 Zeilen.

## Files in scope

- `src/app/floorplan-workbench/page.tsx`
- `src/app/floorplan-workbench/furniture.tsx` (neue Funktion `istDoppelklickDruck`)
- `scripts/moebel-punkte.test.mjs` (vier Tests angehängt)

## Explicitly out of scope

- `entdoppelt()` und seine 60-mm-Toleranz bleiben als zweite Absicherung.
- Rechteck-Werkzeuge (Kücheninsel, Abstellschrank) — der zweite Klick schließt
  dort ohnehin ab.
- Annotator (`floorplan-simplifier/static/annotate.js`): dort überspringt der
  click-Handler `event.detail > 1` bereits; kein Befund. Offen, ob Rainer mit
  "anderen linien" dort etwas meint — siehe Unresolved questions.
- Bereinigung schon gespeicherter Läufe (`scripts/moebel-doppelpunkte.py`
  existiert dafür).

## API, schema, and data-contract effects

Keine. `points_mm` behält Form und Bedeutung.

## Acceptance criteria

1. Klick A, Doppelklick B → Lauf mit genau 2 Punkten.
2. Dasselbe mit 7 px Versatz zwischen den zwei Drücken des Doppelklicks
   (~90 mm bei Standardzoom) → genau 2 Punkte.
3. Zwei bewusst gesetzte Punkte im Abstand > 10 px bleiben erhalten.

## Tests and verification commands

Durchgeführt im Browser auf `http://localhost:3020/floorplan-workbench`,
Haus onehalfstorey_020, nicht gespeichert, danach neu geladen:

- Kriterium 1: echter Maus-Doppelklick → 2 Griffe. Bestanden.
- Kriterium 2: synthetische pointerdown/up + dblclick mit 7 px/2 px Versatz → 2
  Griffe. Bestanden.

Nachtrag 2026-10-09 (Rainer: "ja"): Bedingung als `istDoppelklickDruck()` in
`furniture.tsx` exportiert, `page.tsx` ruft sie auf. Vier Tests in
`scripts/moebel-punkte.test.mjs` angehängt (gleiche Konvention wie dort:
Logik gespiegelt, weil die .tsx-Datei ein DOM bräuchte):

    node --test --test-isolation=none scripts/moebel-punkte.test.mjs
    → 33 pass, 0 fail

Danach Kriterium 2 im Browser erneut geprüft: 2 Griffe. Keine bestehenden
Tests geändert.

## Protected and risky paths

Keine. Nur Eingabeverhalten im Editor.

## Rights, provenance, privacy, and security impact

Keine.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an
approved corrected corpus reference?

No. Die Änderung verwirft nur einen Eingabepunkt im ungespeicherten Entwurf;
Speichern, Freigabe, Render und Versand laufen unverändert über dieselben Pfade.

## Customer, email, database, deployment, and external effects

Keine.

## Failed-hypothesis log

Keine — erste Hypothese (60-mm-Toleranz in mm statt Pixel) bestätigt.

## Rollback

Die Ref `letzterDruck` (mit Kommentar) und die fünf Zeilen ab
`const druck = ...` im `onPointerDown`-Zweig aus `page.tsx` entfernen.

## Unresolved questions

- Meint "andere linien" auch Linien im Annotator? Dort bisher kein Befund.

## Approval record

Nicht vorab freigegeben — Änderung wurde vor dem Plan gemacht (Abweichung vom
Ablauf, Rainer am 2026-10-09 mitgeteilt). Rainer: "ok mach" (2026-10-09) als
Auftrag, den Plan nachzuholen.

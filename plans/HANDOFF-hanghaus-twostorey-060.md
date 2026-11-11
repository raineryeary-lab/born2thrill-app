# Handoff: twostorey_060 als Hanghaus bauen (Bauen am Hang)

Stand 2026-10-20. Für Codex oder die nächste Sitzung.

## Zuerst lesen

- `born2thrill-local-workbench/AGENTS.md` + `CLAUDE.md`, `floorplan-simplifier/AGENTS.md` + `CLAUDE.md`
- **Der Plan:** `born2thrill-local-workbench/plans/twostorey-060-hanghaus-geschosse-v1.md`
  - Status PROPOSED: erst nach Rainers Freigabe umsetzen.
- Roadmap: `born2thrill-app-repo/plans/ROADMAP.md`, Abschnitt "twostorey_060 ist ein Hanghaus"

## Sachlage (Rainer, 2026-10-20)

- Das gezeichnete "Erdgeschoss" ist in Wahrheit das **Untergeschoss**, das gezeichnete "Obergeschoss" das **Erdgeschoss**.
- Das Haus steht am Hang:
  - Straßenseite: Gehweg, Einfahrt und Haustür auf **EG-Höhe**;
  - Gartenseite: Terrasse auf **UG-Höhe**.
  - Die Zeichnung sagt das schon: Terrasse auf der unteren Zeichnung, Gehweg/Einfahrt/Haustür auf der oberen.
- Daten: `floorplan-simplifier/projects/twostorey_060`

## Teil A: Geschosse umbenennen (nur twostorey_060, vorher Backup)

- Umbenennen in dieser Reihenfolge, damit nichts kollidiert: erst `groundfloor` -> `basement`, dann `upperfloor` -> `groundfloor`.
- Betroffen:
  - `floor_level` in annotations, elements, exterior_areas
  - die Schlüssel `floor_scale`, `floor_alignment`, `outer_outlines`, `floor_concepts`, `outer_outline_floor`
  - Dateinamen sowie Erwähnungen in data.json, training-data.json, source-state.json, review-notes.txt
- `build-simplifier-render-plan.py`, `annotation_stair_core()`:
  - die Treppe aus dem **untersten Geschoss mit echter Treppe** lesen (role != "opening");
  - heute wird `ground_level` gelesen, das wäre nach dem Umbenennen nur die Kopie.

## Teil B: Hang (Plan-Builder + `render-exterior.py`)

- **Außenflächen:** jede auf der Höhe ihres Geschosses. Heute flach, die Höhe kommt nur aus `AREA_STACK_Z`.
- **`gelaende` im Plan:**
  - "hang", wenn Außenflächen auf zwei Geschossen liegen, sonst "eben" (dann alles exakt wie heute);
  - Richtung: von den EG-Flächen samt Haustür zu den UG-Flächen.
- **Rasen als Gitter-Mesh** (~0,5 m, kein Boolean):
  - straßenseitig auf EG-Höhe, gartenseitig auf UG-Höhe;
  - zwischen den beiden Fassadenlinien linear fallend;
  - Zellen im Hausumriss weglassen.
  - Ergebnis: Erde an der UG-Straßenseite, schräge Erdlinie an den Seitenfassaden.
- **Warnungen:**
  - UG-Fenster/-Tür mehr als 0,1 m unter Gelände;
  - Außenfläche im Hang (> 0,15 m neben dem Gelände).
- **Innenansichten:** bleiben ohne Gelände (Folgeaufgabe).

## Regeln

- Tests zuerst: `gelaende_aus_flaechen`, `gelaende_hoehe`, Treppe aus dem untersten Geschoss.
- Bestehende Tests nicht anfassen.
- Nichts committen, nichts hochladen.

## Abnahme

- `go.py twostorey_060` baut beide Geschosse.
- In der .blend:
  - Gelände 0,3 m vor der Straßenfassade = EG-Fußbodenhöhe (±0,05 m);
  - Gelände 0,3 m vor der Gartenfassade = 0 (±0,05 m);
  - Gehweg auf EG-Höhe, Terrasse auf UG-Höhe.
- Andere Häuser (z. B. bungalow_007, twostorey_059) außen unverändert.

## Bekannt, nicht Teil der Aufgabe

- **Letzter Bau von twostorey_060 (13:54):** keine Innen-.blend.
  - `gebaeudemass.json` wurde 1 s nach `plan-modern.json` geschrieben, darum "STALE PLAN".
  - Ein erneuter Bau sollte durchgehen. Wer die Datei in dem Moment schrieb, ist nicht geklärt.
- **`go.py`-Meldung:** zeigt als Fehlerzeile die erste Log-Zeile (z. B. das Blender-Banner) statt des Grunds.
- **Offene Frage an Rainer:** Läuft der Hang gerade von vorn (Gehweg) nach hinten (Terrasse)? Die Richtung wird aus den gezeichneten Flächen abgeleitet.
- **Katalog:** Neue Häuser bekommen ihre Katalogzeile seit 2026-10-20 automatisch beim ersten Upload. `twostorey_060` braucht dafür nichts von Hand.

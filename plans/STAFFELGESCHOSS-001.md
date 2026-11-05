# Staffelgeschoss

Status: DONE

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-01: "can we add a staffelgeschoss to the annotator?", Beispiel `twostorey_xvit`, Antwort "1 ja 2 ja 3 bauen". Das dritte Blatt von `twostorey_xvit` liegt als Keller vor und wird Staffelgeschoss. Lieferung: nur Flachdach, 4 Stile je Geschoss, 13 Bilder.

## Current evidence and behavior

- Ebenen: basement, groundfloor, upperfloor, attic, garage (`app.py:263`). `attic` ist im Bau kein Geschoss oder ein Kniestock-DG (`dachboden.py`, `anderthalb.py:37`), taugt also nicht.
- `render-exterior.py` baut einen kleineren obersten Stock schon: Dach auf dessen Umriss (`:1214`), `storey-cap` auf dem Stock darunter (`:1409`).
- Werkzeug `roof_terrace` gibt es im Annotator, kein Bau liest es.
- Dollhouse kennt weder Balkon noch Terrasse, die Kamera rahmt nur die Räume des Geschosses (`render-furnished-dollhouse.py:7316`).
- Treppe: ein `shared_stair_core` für das ganze Haus.

## Exact scope

- Annotator: neue Ebene `staffelgeschoss` in Upload, Anzeige, Reihenfolge, Dateinamen-Erkennung.
- `twostorey_xvit`: Blatt Keller auf Staffelgeschoss, mit Rainers OK (Regel 15).
- Neues Modul `scripts/staffel.py`: Umriss des Geschosses darunter, Attika-Stücke, Plan-Feld.
- Plan-Builder: `roof_terrace` der Ebene und Feld `staffelgeschoss`.
- `render-exterior.py` und `render-furnished-dollhouse.py`: Kies auf dem ganzen Dach darunter, Belag auf der Dachterrasse, 1 m Attika überall, wo keine Staffelwand steht.
- `run_project.py`: nur Flachdach. Kürzel `sg` im Codex-Auftrag, Namen im Editor.
- Regel 19.

## Abweichung vom Vorschlag im Chat

Kies wird nicht gezeichnet: Alles auf dem Dach außer Dachterrasse ist Kies, wie außen alles außer Einfahrt, Gehweg und Terrasse Rasen ist (Regel 17). Das spart ein neues Werkzeug.

## Explicitly out of scope

Möbelsymbole auf der Dachterrasse (Codex stattet nach Regel 26 aus), Upload, Rechte, angenommene Bilder, Häuser außer `twostorey_xvit`.

## Tests

- `scripts/staffel.test.py`, Ergänzungen in `dachboden.test.py`-Nähe über `staffel.test.py`.
- `floorplan-simplifier/tests/test_staffelgeschoss.py`.
- Bestehende Suiten: `make-codex-job.test.py`, `render-furnished-dollhouse.test.py`, `dachboden.test.py`, `anderthalb.test.py`, `unittest discover` im Annotator.
- Echter Bau von `twostorey_xvit`, sobald gezeichnet; davor Probe im Temp-Ordner.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

Answer: no. Geometrie kommt nur aus Rainers Zeichnung; der Bau schreibt nur in den Hausordner, Upload und E-Mail sind nicht betroffen.

## Rollback

Alle `.before-staffel`-Dateien zurückkopieren, `scripts/staffel.py` und `tests/test_staffelgeschoss.py` entfernen, Regel 19 zurück, `.before-staffel` in `twostorey_xvit` zurück, `staffelgeschoss_original_preview.png` wieder `basement_original_preview.png`.

## Approval record

Rainers "bauen" vom 2026-11-01 im Chat.

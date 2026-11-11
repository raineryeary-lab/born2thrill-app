# katalog-automatisch-v1

Rainer, 2026-11-07: "i just built a bungalow 3 zimmer over 600k why doesn't it show in the
grundrisscatalog" -> "Yes, go live" -> "this has to go automatically".

## Was
scripts/katalog-aktualisieren.py: Matrix neu; jedes Matrix-Haus ohne Katalogzeile bekommt Zeile
(grundriss-anlegen, nur INSERT) + Grundrissbild (Mediathek); Snippets 10/11/12 neu erzeugt und nur bei
echter Aenderung (Zeitstempel zaehlt nicht) ueber /wp-json/code-snippets/v1/snippets/<id> ersetzt.
Nie approved, nie Freigabe, nie Mail. CubiCasa-Plaene nie.

Annotator (app.py): nach jedem Save 90 s Ruhe, dann im Hintergrund; nie zwei Laeufe zugleich;
nur der laufende Server (main), nie Tests. Log: <Datenordner>/katalog-aktualisieren.log.
Aus: KATALOG_AUTO=0.

## Tests
scripts/katalog_aktualisieren.test.py (4), floorplan-simplifier/tests/test_katalog_auto.py (2), Suite 412 OK.

## Offen
Erster Lauf des Skripts durch Claude wurde vom Auto-Mode-Klassifizierer gestoppt; Snippets fuer
bungalow_3_600 wurden per Browser ersetzt. Erster echter Lauf geschieht beim naechsten Save.

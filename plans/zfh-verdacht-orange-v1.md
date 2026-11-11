# zfh-verdacht-orange-v1

Rainer, 2026-11-08: "die verdächtigen 2 Familienhäuser bitte im annotator markieren orange" -> "Ja, alle 6".

## Umfang
- Neue Datei `floorplan-simplifier/zfh-verdacht.json` {plan: Grund} mit den 6 Häusern aus dem Scan
  (zwei Küchen auf einem Geschoss oder Wohnen auf zwei Geschossen).
- app.py: `zfh_verdacht()` liest die Datei; ein Haus fällt automatisch heraus, sobald es
  `wohneinheiten >= 2` hat (= als ZFH gesetzt). `/api/hauszustand` liefert `zfh_verdacht`
  auch, wenn die Workbench nicht antwortet.
- static/app.js + styles.css: Projektliste färbt diese Häuser orange, Text "ZFH? <Grund>".
- Nichts an annotations.json, Haustyp oder Katalog wird geändert.

## Tests (zuerst)
`tests/test_zfh_verdacht.py`: Datei gelesen; Haus mit wohneinheiten 2 fällt raus; fehlende
Datei -> {}; hauszustand liefert den Schlüssel auch bei Workbench-Fehler.

## Rückweg
Backups `.before-zfh-verdacht`; Datei löschen = keine Markierung.

## Sicherheitsfrage
Geometrie erzeugen/veröffentlichen/mailen? Nein, nur Anzeige.

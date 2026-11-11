# einliegerwohnung-v1

Rainer, 2026-11-08: "could you add another house type EFH with Einliegerwohnung".
Antworten: passt noch nicht in den Fragebogen, später als Zusatzoption wie
"Gäste-WC mit Dusche"; Zimmer = nur Hauptwohnung, ELW-Zimmer in Klammern.

## Umfang
1. Annotator, Dach-Tab neben "Wohneinheiten": Häkchen **Einliegerwohnung** (Feld
   `einliegerwohnung: true` in annotations.json; überlebt Speichern).
2. Annotator, Rechtsklick auf einen Raum: oben **"Gehört zur Einliegerwohnung"**
   an/aus (Feld `einlieger: true` am Raum; überlebt normalize_annotation). Der Raum
   wird im Plan mit "ELW" gekennzeichnet. Raumname und Bau bleiben unverändert.
3. konfigurator-matrix.py: Zimmer zählt nur Räume ohne `einlieger`; neue Spalten
   `elw` (0/1) und `elw_zimmer`. Hausart bleibt EFH/Bungalow/DHH (kein neues Feld,
   REGELN 37 unverändert). Fläche und Preis zählen die ELW mit (sie wird gebaut).
4. Preisfenster im Annotator: "4 Zimmer (+ ELW 2)".
5. Katalog-Karte (Snippet 9) nur, wenn Rainer es danach will -- nicht in v1.

## Nicht im Umfang
Fragebogen, Katalogfilter, neue Hausart, Builds/Bilder.

## Tests (zuerst)
- floorplan-simplifier: `einliegerwohnung` und `einlieger` überleben Speichern.
- Matrix: Haus mit 2 ELW-Zimmern -> zimmer ohne sie, elw_zimmer = 2; ohne Flag
  unverändert (Vergleich gegen Stand vorher für alle Häuser).

## Rückweg
Backups `.before-einlieger`.

## Sicherheitsfrage
Geometrie erzeugen/veröffentlichen/mailen? Nein.

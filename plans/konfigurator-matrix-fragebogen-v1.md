# konfigurator-matrix-fragebogen-v1

Rainer, 2026-11-03: "this is the newest checklist according to what we have to
finish for our startup" -- der Fragebogen "Hausbau-Konfigurator – Fragen &
Ablauf" (Kopie: docs/Hausbau-Konfigurator-Fragen-Ablauf.pdf) ersetzt die
31 Felder aus der Excel.

## Neue Felder (30)

Budget 300-450 / 450-600 / ueber 600 Tsd. EUR, je
EFH 4/5, DHH 4/5, Bungalow 3/4/5, ZFH 3/4/5 Zimmer (zusaetzlich zu Kueche
und Bad). Baustil und Dachform sind Bildvarianten, keine Felder.
Frage 8 "Gaeste-WC mit Dusche": je Haus Spalte gaeste_wc_dusche (Raum mit
Label DU-WC oder "dusch" + "wc").

## Aenderung

Nur `scripts/konfigurator-matrix.py`: BUDGETS-Texte, FELDER, Spalte
gaeste_wc_dusche, Hinweis auf Haeuser unter 300 Tsd. (zaehlen in 300-450).
Die oberste Stufe heisst weiter "5+" (6-Zimmer-Haeuser zaehlen dort).
Keine Daten, kein Upload.

## Test

Skript laufen lassen; Ergebnis gleich der Probe-Rechnung vom 2026-11-03:
14 gruen, 1 gelb (b450-efh-4), 15 rot.

## Rueckweg

`konfigurator-matrix.py.before-fragebogen-2026-11` zurueckkopieren,
REGELN.md.before-fragebogen zurueckkopieren.

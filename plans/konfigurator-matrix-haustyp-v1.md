# konfigurator-matrix-haustyp-v1

Rainer, 2026-11-03: "check our questionair to make a table of what houses we
need and checkoff which houses we already have".

Live-Fragebogen born2thrill.de/test/ (Plugin hausklar-flug 0.5.2) hat dieselben
31 Felder wie `konfigurator-matrix.py` (BUDGETS/TYPES/ROOMS gelesen, gleich).

## Fehler in haustyp()

- data.json traegt heute "2-storey" / "1.5-storey"; das Skript kannte nur
  "twostorey"/"onehalfstorey" und fiel auf den Projektnamen zurueck:
  bungalow_xvv6 (Zweigeschosser) zaehlte als Bungalow.
- Doppelhaushaelften (`doppelhaus: {"trennwand": ...}` in annotations.json,
  onehalfstorey_046, other_vito, other_xvitv1, twostorey_xvit) zaehlten als EFH
  oder gar nicht -- alle DHH-Felder standen ROT.

## Aenderung

haustyp(): zuerst die doppelhaus-Markierung -> "dhh", dann house_type aus
annotations.json bzw. data.json mit beiden Schreibweisen, zuletzt der Name.
Nur `scripts/konfigurator-matrix.py`. Keine Daten, kein Upload.

## Test

Skript laufen lassen: DHH-Haeuser landen in dhh-Feldern, bungalow_xvv6 in efh.

## Rueckweg

`konfigurator-matrix.py.before-haustyp` zurueckkopieren.

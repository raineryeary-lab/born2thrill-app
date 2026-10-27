# LIEFERUNG-MARKER-GESCHOSS-001

Der Pruefer verlangt einen `marker_check` fuer JEDES Innenbild, sobald der
Auftrag eine Objektkarte enthaelt. Die Karte deckt aber nur ein Geschoss ab.

## Befund

`codex-onehalfstorey_020-2026-08-28-final` ist sachlich einwandfrei:

    10/10 Dateien unter den geforderten Namen
    10/10 Pixelmasse korrekt
    10/10 sha256 byte-identisch mit dem angenommenen Review-Satz
    state = final, oben und je Bild
    keine Zusatzdateien
    marker_check fuer 03--06 vollstaendig, 17 von 17, Farben stimmen

Trotzdem vier Beanstandungen:

    07..10-floorplan-*-og.png: marker_check fehlt

Die Objektkarte des Auftrags ist `OBJEKTKARTE-interior-modern-baseline.png`
und zeigt das Erdgeschoss. Die Bilder 07--10 stammen laut `source_blend` aus
`interior-modern-upper-baseline.blend` -- das Obergeschoss. Fuer sie gibt es
keine Karte, also auch nichts zu bestaetigen. Der Auftragstext hat Codex
ausdruecklich verboten, hier etwas zu erfinden; Codex hat sich daran gehalten
und faellt dafuer durch.

Der Fehler liegt im Pruefer, nicht in der Lieferung.

## Umfang

In Arbeit: `scripts/lieferung-pruefen.py`, `scripts/lieferung-pruefen.test.py`

Nicht in Arbeit: die Objektkarte fuers Obergeschoss (eigener Punkt, siehe
unten), `make-codex-job.py`, das Regelwerk, die Lieferdaten selbst.

## Aenderung

`pruefe()` reicht die Herkunft des Bildes an `_marker_beanstandungen()`
weiter. Ein `marker_check` wird nur verlangt, wenn die Objektkarte dieses
Bild ueberhaupt abdeckt:

    Karte `OBJEKTKARTE-<stamm>.png`  deckt  `source_blend == <stamm>.blend`

Faellt `source_blend`, laesst sich die Herkunft nicht bestimmen -- dann wird
weiterhin ein `marker_check` verlangt. Die Regel oeffnet nur dort, wo
nachweisbar keine Karte existiert.

Ein gelieferter `marker_check` wird weiterhin vollstaendig geprueft, auch fuer
ein Bild ausserhalb der Karte: unbekannte Marker, Doppelte, falsche Farben
bleiben Beanstandungen.

## Tests zuerst

1. Ein OG-Bild ohne `marker_check`, Karte fuers EG -- keine Beanstandung.
2. Ein EG-Bild ohne `marker_check`, Karte fuers EG -- Beanstandung wie bisher.
3. Ein Innenbild ohne `source_blend` -- Beanstandung (faellt geschlossen).
4. Ein OG-Bild MIT einem erfundenen Marker aus der EG-Karte -- Beanstandung.
5. Der ganze Ordner `-final` laeuft ohne Beanstandung durch.

## Abnahme

`python scripts/lieferung-pruefen.py onehalfstorey_020 codex-onehalfstorey_020-2026-08-28-final`
meldet 0 Beanstandungen, und die bestehenden 16 Tests bleiben gruen.

## Risiko

Ein Innenbild, fuer das es sehr wohl eine Karte gibt, koennte durchrutschen,
wenn Codex ein falsches `source_blend` einsetzt. Dagegen steht, dass
`source_blend` gegen die `inputs` des Auftrags gehalten werden kann -- der
naechste Punkt, nicht dieser.

## Rechte

Keine. Kein Bild wird erzeugt, veroeffentlicht oder versendet.

## Rueckabwicklung

Die zwei Dateien zurueckdrehen; es haengt nichts anderes daran.

## Bleibt offen

CODEX-OBJEKTKARTE-OG-001: eine Objektkarte fuer
`interior-modern-upper-baseline.blend`. Genau im Obergeschoss liegt die
Eckbadewanne, die dreimal verschwand, ohne dass es jemandem auffiel. Solange
es dort keine Karte gibt, gibt es fuer vier von zehn Bildern keinen Beweis.

# Rückmeldung an Codex: versetztes Pultdach / Doppelpultdach – Anschlussgeometrie

Stand: 2026-10-24 · Auftrag: Rainer via Codex („Bitte korrigiere im Blender-Generator die Anschlussgeometrie …“)

## 1. Zuständige Generatorstelle

- `born2thrill-local-workbench/scripts/roof_profile.py` → `profile_mesh()` baut das Dachblech aus dem Querschnitt (Dach-Tab). Die senkrechte Stufenfläche war Teil dieses Blechs und lief der Länge nach von `a0` bis `a1`, also über die Dachkontur **inklusive Überstand** → senkrechte Blende zwischen den beiden Dachkanten im Überstandsbereich.
- Aufruf: `born2thrill-local-workbench/scripts/render-exterior.py`, Rechteck-Zweig (`elif is_rectangle:`), nur für `roof_type == "doppelpultdach"`.
- L-förmige Häuser (Zweig `VERSATZ-WHOLE-HOUSE-001`) waren bereits richtig (Versatzwand auf der Wandaußenkante, oberes Dach mit Überstand). Rainer: dort bleibt Putz, kein Zink.

## 2. Umgesetzte Korrektur

Neue Parameter in `profile_mesh()`, alle mit Vorgabe 0 (= byte-gleiche Ausgabe für jede andere Dachform und jeden anderen Aufrufer):

| Parameter | Wirkung | Wert beim Doppelpultdach |
|---|---|---|
| `step_wall_a_inset` | Stufenfläche endet an beiden Giebeln an der Außenwandebene | Überstand − halbe Wanddicke (056: 0,38 m) |
| `step_overhang` | oberes Pultdach läuft über die Stufe hinaus, in eigener Neigung | voller Dachüberstand (0,50 m) |
| `step_wall_top_inset` | Stufenfläche endet unter der Dachplatte (keine Kante über dem Dach) | Dachdicke 0,22 m, senkrecht gemessen |

- **Kein Überstand mit Blende:** Im Überstandsbereich gibt es keine senkrechte Verbindung mehr zwischen oberer und unterer Dachkante.
- **Zink-Stehfalz:** Die verbleibende Stufenfläche hat eine dezente Zink-Stehfalzverkleidung: Material `zink-stehfalz` (Titanzink vorbewittert, Blaugrau), Falze alle 50 cm (20 mm breit, 25 mm vorstehend), nur innerhalb der Stufenfläche. Bei twostorey_056 sind es 22 Falze.
- **Mitbehoben:** Die Stufenfläche ist seit dem Einzug ein eigenes Stück. Die Normalenberechnung drehte sie um, sodass Dicke und Falze auf der Seite des höheren Dachs lagen. Ihre Richtung kommt jetzt aus dem Profil.
- **Unverändert:** Dachneigungen, Dachhöhen, übrige Überstände, Hausgeometrie, Öffnungen, Kameras, andere Dachtypen.
- **Tests:** `roof_profile.test.py` (12 neue Fälle, u. a. „ohne Parameter identisch“, „Stufenwand bündig an den Giebeln“, „Überstand oben in eigener Neigung“, „Falze nur in der Fläche“), alle grün. `roof_wings.test.py` und `roof_wings_multi.test.py` sind ebenfalls grün.

## 3. Nachweis an twostorey_056

Neu gebaut und zertifiziert am 2026-10-24 (`go.py twostorey_056`):

- `twostorey_056-detail-dachversatz.png`: Detailansicht des Dachversatzes. Zusatzkamera, nur gerendert, die Liefer-.blend ist unverändert.
- `twostorey_056-aussenansicht.png`: normale Außenansicht, genau der Roh-Render der Lieferung (`exterior-doppelpultdach-baseline.png`).
- `twostorey_056-detail-vorher-nachher.jpg`: gleiche Kamera oben alter Code, unten neuer Code.
- Liefer-.blend: `E:\born2thrill-local-workbench-data\corrections\twostorey_056\renders\go-baseline\exterior-doppelpultdach-baseline.blend`

Ein heller Streifen auf der unteren Dachfläche ist auch im alten Code vorhanden und gehört nicht zu dieser Korrektur.

## 4. Hochgeladene Projekte mit betroffener Doppelpultdach-Ansicht

**26 Projekte, 28 Bilder**, Details in `betroffene-projekte.csv` (plan_id, Bildname, Media-ID, URL, neu gebaut ja/nein, Zink ja/nein).

- **bungalow:** 007, 039, 040_185, 040_200, 040_24, m
- **german_catalog_review_bungalow:**
  - 3_1_2_b_85
  - 3_2_1_b_100_1 (2 Bilder)
  - 3_2_2_b_100_1, 3_2_4_b_100_1
  - 3_3_1_b_100_2, 3_3_2_b_100_2
  - 3_4_2_b_120, 3_4_6_b_120, 3_4_7_b_120
- **twostorey:** 046, 048, 049, 051, 052, 053, 054, 055 (2 Bilder), 056, 059, 060

**Nicht betroffen:**
- german_catalog_review_bungalow_3_3_3_b_100_2: online nur ein normales Pultdach-Bild
- german_catalog_review_bungalow_3_2_5_b_100_1, german_catalog_review_bungalow_3_3_4_b_100_2, twostorey_030: kein Pultdach-Bild online

## 5. Was NICHT passiert ist

- Kein bestehendes Bild ersetzt, nichts hochgeladen.
- **Kein weiterer Neubau nach dem Auftrag.** Vor dem Eingang des Auftrags waren bereits 8 Häuser neu gebaut worden, mit neuer Stufengeometrie, aber **noch ohne Zink**: bungalow_007, bungalow_039, bungalow_040_185, bungalow_040_200, bungalow_040_24, bungalow_m, german_catalog_review_bungalow_3_1_2_b_85, german_catalog_review_bungalow_3_2_1_b_100_1. Sie brauchen für den Zink noch einen Bau.
- Danach gebaut: nur twostorey_056 (Nachweis), außerdem twostorey_053 und twostorey_058 als Testhäuser für einen separaten Plan (`CODEX-EXPORT-001`: saubere Fassaden, Möbelfronten, Auftrag nur aus aktuellem Bau).

## 6. Für die Bildkorrekturen

- `python scripts/make-codex-job.py <plan> --nur doppelpult --grund "..."` schreibt einen **Teilauftrag**: Bestellt wird nur die Doppelpultdach-Außenansicht, alle anderen Bilder gelten als fertig.
- **Voraussetzung:** ein frischer, zertifizierter Bau des Hauses. Aufträge entstehen jetzt nur noch aus einem zertifizierten, aktuellen Bau; die Blend-Prüfsummen müssen zum Zertifikat passen.
- **Fertig für einen Teilauftrag:** twostorey_056 (neu gebaut, mit Zink).

**Offen, zur Abstimmung mit Codex:** In welcher Reihenfolge werden die 26 Häuser neu gebaut und ihre Pultdach-Bilder ersetzt?

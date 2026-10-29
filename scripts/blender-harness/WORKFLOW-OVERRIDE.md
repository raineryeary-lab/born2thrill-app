# WORKFLOW-OVERRIDE — Blender-only

Gueltig ab 2026-09-02. Diese Datei steht **ueber** `CODEX-AUFTRAG.md` und
`CODEX-REGELN.md`. Wo sie einer aelteren Regel widerspricht, gilt sie.

## 1 — Was aufgehoben ist

Ersatzlos gestrichen, fuer die vier Innenbilder je Geschoss:

- ComfyUI.
- Jedes Bildmodell.
- Ganzbild-Neugenerierung.
- Ganzbild-Bearbeitung.
- Maskierte generative Bearbeitung.
- Frueher erzeugte Innenbilder als Ausgangspunkt oder Referenz.

Die Forderung *"fuer jeden Stil genau EIN Ganzbild-Durchgang im Bildmodell"*
ist ausdruecklich aufgehoben.

## 2 — Was stattdessen gilt

- Einzige Geometriequelle ist die neueste `interior-modern-baseline.blend`.
- Moebel werden deterministisch in Blender gestaltet oder durch Modelle aus
  `E:\_models_hub\_codex_catalog_assets` ersetzt.
- Architektur, Waende, Tueren, Fenster, Oeffnungen, Kamera und Schnittebene
  bleiben unveraendert.
- Mittelpunkt, Fussabdruck, Ausrichtung und Anzahl jedes Ausgangsobjekts
  bleiben verbindlich.
- Die 43 Marker, die Stueckzahlen und alle Objektregeln des Auftrags bleiben
  harte Regeln.
- Zwischenstaende gelangen niemals in den Lieferordner. Der Harness schreibt
  ausschliesslich nach `renders/harness/`.
- Die angenommenen Aussenbilder werden nicht angefasst.

## 3 — Dateistruktur

    born2thrill-local-workbench/scripts/blender-harness/
        WORKFLOW-OVERRIDE.md      diese Datei
        export_invariants.py      Phase 0
        verify_invariants.py      Phase 1, reine Python-Pruefung ohne Blender
        null_render.py            Phase 1, Nullrender

    <haus>/renders/harness/       ALLE Ausgaben des Harness, nie die Lieferung
        invariants.json           Grundwahrheit der aktuellen .blend
        invariants_vorher.json    vor dem Nullrender
        null-render.png           der Nullrender
        invariants_nachher.json   nach dem Nullrender

## 4 — Befehle unter Windows

Pfade mit `^` am Zeilenende umbrechen (cmd) oder in eine Zeile schreiben.

    set BL="C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
    set H=C:\dev\Floorplan-tools\born2thrill-local-workbench\scripts\blender-harness
    set G=E:\born2thrill-local-workbench-data\corrections\german_catalog_review_bungalow_3_4_2_b_120\renders\go-baseline
    set A=E:\born2thrill-local-workbench-data\corrections\german_catalog_review_bungalow_3_4_2_b_120\renders\harness

PHASE 0:

    %BL% --background "%G%\interior-modern-baseline.blend" ^
         --python "%H%\export_invariants.py" -- "%A%\invariants.json" "%G%\codex-job.json"

PHASE 1:

    %BL% --background "%G%\interior-modern-baseline.blend" ^
         --python "%H%\null_render.py" -- "%A%" "%G%\codex-job.json"

    python "%H%\verify_invariants.py" "%A%\invariants_vorher.json" "%A%\invariants_nachher.json"

## 5 — Pass/Fail

PHASE 0 bestanden, wenn:

1. `invariants.json` entsteht und `objekte` ist nicht leer.
2. Jeder der 43 Marker ist einem Blender-Objekt zugeordnet;
   `marker.ohne_blender_objekt` ist leer.
3. `stueckzahlen.abweichungen` ist leer.
4. `nachweis_mesh_objekte` aus dem Auftrag deckt sich mit der Zahl der
   MESH-Objekte.

Sonst: abbrechen und melden. Kein Objekt anfassen.

PHASE 1 bestanden, wenn:

1. `verify_invariants.py` endet mit Code 0 und gibt "OK" aus.
2. Kein Objekt entfernt, hinzugefuegt, verschoben (> 0,001 mm), gedreht,
   skaliert oder in seiner Sichtbarkeit veraendert.
3. Kein Mesh-Fingerabdruck weicht ab.
4. Kamera und Render-Einstellungen unveraendert.

Der Vergleich Nullrender gegen `interior-modern-baseline.png` ist **kein**
Pass/Fail-Kriterium, solange Abschnitt 6 offen ist -- siehe dort.

## 6 — Offener Befund aus dem ersten Lauf (2026-09-02)

Phase 0 und Phase 1 sind an
`german_catalog_review_bungalow_3_4_2_b_120` gelaufen:

    Objekte 223, MESH 221, davon Moebel 81, Architektur 140
    43 Marker zugeordnet, 0 ohne Blender-Objekt
    keine Stueckzahl-Abweichung
    verify_invariants: OK, Code 0

Der Harness veraendert also nichts. ABER: der Nullrender sieht anders aus als
der gelieferte `interior-modern-baseline.png`.

    identische Pixel        13 021 von 3 000 000  (0,43 %)
    mittlere Abweichung     26,9 / 28,2 / 32,7 je Kanal
    Helligkeit Baseline     164,8   Nullrender 183,1

Die Geometrie ist dabei identisch -- Raeume, Moebel und Kamera decken sich.
Der Unterschied ist Farbmanagement und Hintergrund.

URSACHE, gefunden in `render-furnished-dollhouse.py`: der Depth-Pass setzt

    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = 0.0
    scene.eevee.taa_render_samples = 8

und stellt davon **nichts** zurueck, bevor `DMH_SAVE_BLEND` die Szene
schreibt. Die ausgelieferte `.blend` traegt damit die Einstellungen des
DEPTH-Passes, nicht die des Schoenbilds. In `invariants.json` nachgelesen:

    "view_transform": "Standard", "samples": 8, "exposure": 0.0

FOLGE: Wer die gelieferte `.blend` oeffnet und rendert, bekommt NICHT das
gelieferte Bild. Fuer einen Blender-only-Workflow, in dem die `.blend` die
einzige Quelle ist, ist das ein Blocker -- er muss vor Phase 2 geschlossen
werden, entweder durch Zuruecksetzen der View-Settings vor dem Speichern oder
dadurch, dass der Harness sie explizit setzt.

## 7 — Was in den bestehenden Dateien ausser Kraft tritt

`CODEX-AUFTRAG.md` (Stand 2026-09-01 20:23):

- Zeile 25 — "den gespeicherten Dollhouse-Kamera-Render als Grundbild
  verwenden": kein Grundbild mehr, es wird gerendert statt bearbeitet.
- Zeile 26 — "kein frueheres Innenbild als Grundbild": bleibt gueltig, ist
  aber gegenstandslos, weil es gar kein Grundbild mehr gibt.
- Zeile 27 — "fuer jeden Stil genau EIN Ganzbild-Durchgang im Bildmodell,
  keine Maske": AUFGEHOBEN.
- Zeile 28 — "das Bildmodell darf nur Material, Farbe, Licht ... veraendern":
  ersetzt durch "in Blender werden nur Material, Farbe, Licht und Modellwahl
  veraendert".
- Zeile 148 — "ein angenommenes Bild nie neu rendern": bleibt, gilt jetzt fuer
  01 und 02.
- Abschnitt "Innenansichten" — der Satz zur Ganzbild-Bearbeitung entfaellt;
  die Trennung "was variieren darf / was nicht" bleibt unveraendert gueltig.

`CODEX-REGELN.md` (717 Zeilen):

- Zeile 55 — "ein Bildmodell erfindet Tuerblaetter": gegenstandslos.
- Zeile 437 — Referenzlieferung `onehalfstorey_020` mit `gpt-image`: gilt
  nicht mehr als Verfahrensvorbild, nur noch als Qualitaetsmasstab.
- Zeilen 440-443 — Grundbild und Ganzbild-Bearbeitung: AUFGEHOBEN.
- Zeile 450 — "ein reiner Blender-Neurender scheitert an Abschnitt 11":
  UMGEDREHT. Der Blender-Render ist ab jetzt der einzige zulaessige Weg.
- Zeile 452 — "Nachbessern heisst zweite Ganzbild-Bearbeitung": AUFGEHOBEN.
  Nachbessern heisst: Szene aendern und neu rendern.
- Zeile 459 — "eine Ganzbild-Bearbeitung wuerfelt das Geschoss neu":
  gegenstandslos, war die Begruendung fuer das alte Verfahren.
- Zeile 465 — "ein angenommenes Bild wird NIE neu erzeugt": bleibt.
- Zeilen 506, 514, 517 — Denoise, kleinere Ausgabegroesse, 0,5 %
  Seitenverhaeltnis-Toleranz: gegenstandslos. Blender liefert exakt
  2000 x 1500.
- Zeile 561 — Qualitaetsbeispiel mit "ein Ganzbild-Durchgang, keine Maske":
  historisch, nicht mehr Vorschrift.
- Zeile 621 — "das Bild ist ein reiner Blender-Neurender, daher abgelehnt":
  STREICHEN. Das war der Ablehnungsgrund, der jetzt das Verfahren ist.
- Abschnitt 8.1 "Aufbau des Prompts" (Zeilen 485-506): vollstaendig
  gegenstandslos, es gibt keinen Prompt mehr.
- Abschnitte 1 bis 3, 5, 7, 11 und 12 bleiben unveraendert gueltig:
  Architektur, Stueckzahlen, Stile, Aussenaufnahmen, Pruefliste, Lieferung.

## 8 — Was jetzt NICHT passiert

Kein Moebeltausch, keine Materialaenderung, kein Licht, kein Styling, keine
Datei im Lieferordner. Phase 2 beginnt erst, wenn Abschnitt 6 geschlossen ist.

## 9 — Abschnitt 6 geschlossen (2026-09-02)

`render-furnished-dollhouse.py` sichert und restauriert jetzt vor dem
Speichern alle vom Depth-Pass veraenderten Zustaende:

    view_transform, exposure, taa_render_samples, render.filepath,
    world.use_nodes und world.color

Die bestehende `interior-modern-baseline.blend` wurde ausschliesslich in
diesen Einstellungen repariert. Die kontaminierte Fassung liegt daneben als
`interior-modern-baseline.before-color-management-fix-2026-09-02.blend`.

Nachweis auf dem tatsaechlichen Baseline-Pfad:

    Objekte 223, MESH 221, davon Moebel 81, Architektur 140
    43 Marker zugeordnet, 0 ohne Blender-Objekt
    Kamera, Objekte, Mesh-Fingerabdruecke, Marker und Stueckzahlen identisch
    verify_invariants: OK, Code 0
    Nullrender: 76,10 % exakt gleiche Pixel statt 0,43 %
    mittlere RGB-Abweichung: 2,89 / 2,76 / 2,59 statt 26,9 / 28,2 / 32,7
    Helligkeit Baseline / Nullrender: 164,18 / 162,41

Ein separater End-to-End-Erzeugertest nach dem Depth-Pass speicherte:

    view_transform=AgX, exposure=0.2, taa_render_samples=64

Damit ist Abschnitt 6 geschlossen und die Sperre aus Abschnitt 8 fuer den
Beginn von Phase 2 aufgehoben. Lieferdateien bleiben bis zu einer bestandenen
Phase-2-Pruefung weiterhin unangetastet.

## 10 — Abschnitt 7 ist angewendet (2026-09-03)

Die Liste in Abschnitt 7 war bis heute nur eine Liste: sie sagte, welche
Stellen in `CODEX-REGELN.md` und `CODEX-AUFTRAG.md` ungueltig sind, und die
Stellen standen unveraendert in den Originalen. Ein Regelwerk mit einem
Override-Zettel daneben ist kein Regelwerk.

Jetzt sind sie IN den Dateien gestrichen -- zwoelf Stellen im Regelwerk, fuenf
im Auftrag. Nicht geloescht, sondern ersetzt durch den neuen Wortlaut plus
eine datierte Zeile, warum die alte weg ist. Das ist die Schreibweise, die
das Regelwerk ohnehin benutzt ("Ergaenzt 2026-08-27: ...").

Der vollstaendige alte Wortlaut liegt daneben:

    CODEX-REGELN.md.vor-bereinigung-2026-09-03
    CODEX-AUFTRAG.md.vor-bereinigung-2026-09-03

Zusaetzlich zu Abschnitt 7 gestrichen, nach Rainers Durchsicht des
Regelwerk-Audits am 2026-09-03:

- Abschnitt 4, eingeschaltete Leuchten mit sichtbarem Lichtkegel. Das
  Dollhouse ist ein Schnitt OHNE Decke; Tageslicht faellt von oben in jeden
  Raum. Eine brennende Pendelleuchte in einem Raum ohne Decke ergibt keinen
  Sinn.
- Abschnitt 5, "symmetrische Anordnungen" bei Classic. Ohne Urheber, nie
  gefordert, im Widerspruch zur Positionssperre 2.2.
- AUFTRAG Zeile 30, "keine Dekoration auf freier Bodenflaeche". Stand im
  Widerspruch zu Regelwerk 3.4, das Deko VERLANGT. Praezisiert: gemeint sind
  Moebelstuecke ohne Marker, nicht Ausstattung an einem Traegerobjekt.

Nicht gestrichen, weil weiterhin gueltig: Abschnitte 1 bis 3, 5, 6, 7, 11 und
12 -- Architektur, Stueckzahlen, Stile, Aussenaufnahmen, Pruefliste,
Lieferung.

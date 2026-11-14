# Überdachte Terrasse und überdachter Balkon

Status: DONE

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer kann eine Terrasse oder einen Balkon im Annotator als "überdacht" markieren. Der Bau setzt darüber ein flaches anthrazites Dach auf schlanken Pfosten. Rainer, 2026-10-31: Variante 1, nicht das Hauptdach verlängern.

## Current evidence and behavior

- Terrassen sind `exterior_areas` und werden in `render-exterior.py` nur als flache Fläche gebaut (`flat_polygon`, Zeile 4021 ff.).
- Balkone sind Elemente vom Typ `balcony` und bekommen Belag und Brüstung (`render-exterior.py:3871-3899`), aber kein Dach.
- Das Hauptdach folgt nur den Wänden (`render-exterior.py:1212-1218`), eine Terrasse als Einschnitt bleibt offen.
- `roof_terrace` wird im Bau nirgends gelesen.
- Kein Haus enthält bisher "Loggia" oder "überdacht" als Raumname.
- Zwei stille Filter liegen auf dem Weg: `normalize_element` (`floorplan-simplifier/app.py:5341`) und `normalize_exterior_area` (`app.py:5494`) lassen nur bekannte Felder durch.
- Abweichung im Code: `annotation_exterior_areas` (`build-simplifier-render-plan.py:3676`, korrigierter Weg) übernimmt nur `id`, `type`, `points_mm`. Dort muss das Feld ebenfalls durch. Balkone gibt es nur im Annotationsweg (`:4286`), der korrigierte Weg kennt sie gar nicht.

## Repository baselines

- `born2thrill-local-workbench`: Branch `agent/furnished-render-and-annotation-schema`, Stand `5be1a4e`, 604 Einträge in `git status`.
- `floorplan-simplifier`: Branch `agent/annotation-window-type-door-swing`, Stand `8a08d19`, 250 Einträge in `git status`.
- Fremde Änderungen bleiben unangetastet.

## Exact scope

1. **Annotator:** Häkchen "überdacht" in der Liste der Außenflächen bei jeder Terrasse und in der Elementliste bei jedem Balkon. Andere Typen bekommen kein Häkchen. Das Feld heißt `ueberdacht: true`.
2. **Speichern:** Das Feld übersteht `normalize_exterior_area` und `normalize_element`.
3. **Plan:** `plan_exterior_areas`, `annotation_exterior_areas` und die Balkonliste reichen das Feld weiter.
4. **Bau:** Eine neue Funktion in `render-exterior.py` baut für jede markierte Fläche:
   - Dachplatte in Flächenform, 120 mm dick, anthrazit
   - Unterkante auf `Geschossboden + max(2,50 m, Fenstersturz + 150 mm)`, damit Türen und Fenster frei bleiben
   - 150 mm Überstand an den freien Kanten, an der Fassade kein Überstand
   - Pfosten 100 x 100 mm, anthrazit, an jeder äußeren Ecke, dazwischen höchstens 3 m Abstand
   - Fassadenkanten erkennt dieselbe Regel wie beim Balkon (300 mm Abstand), dort stehen keine Pfosten
   - Steht die Fläche frei, bekommt sie an allen Ecken Pfosten
5. **Hausakte:** Das Bau-Log nennt jede Überdachung.

## Files in scope

- `floorplan-simplifier/static/annotate.js`
- `floorplan-simplifier/app.py`
- `floorplan-simplifier/tests/test_element_felder_ueberleben_speichern.py` (Ergänzung)
- `floorplan-simplifier/tests/test_exterior_floor_level.py` oder neue Datei für das Außenflächen-Feld
- `born2thrill-local-workbench/scripts/build-simplifier-render-plan.py`
- `born2thrill-local-workbench/scripts/render-exterior.py`
- Neu: `born2thrill-local-workbench/scripts/ueberdachung.py` (reine Geometrie ohne Blender, damit testbar)
- Neu: `born2thrill-local-workbench/scripts/ueberdachung.test.py`

## Explicitly out of scope

- `make-codex-job.py` und der Bildablauf (Regel 22)
- Hauptdach verlängern, Dachneigung, andere Dachformen über der Terrasse
- Dollhouse-Innenbilder: Sie zeigen keine Überdachung. Bleibt offen in der Roadmap
- Balkone im korrigierten Weg
- Das Dachterrassen-Werkzeug
- Neubau bestehender Häuser und jeder Upload

## API, schema, and data-contract effects

Neues optionales Feld `ueberdacht` in `exterior_areas[]`, `elements[]` und im Render-Plan. Fehlt es, gilt "nicht überdacht". Häuser ohne das Feld bleiben unverändert.

## Acceptance criteria

1. Häkchen setzen, speichern, neu laden: Es bleibt gesetzt, bei Terrasse und Balkon.
2. Bauen im echten Ablauf: Die `.blend` enthält Dachplatte und Pfosten an der gezeichneten Stelle.
3. Kein Pfosten steht in einer Tür, vor einer Terrassentür oder in einer Fassade.
4. Die Unterkante liegt über allen Fenstern und Türen der angrenzenden Fassade.
5. Sichtprüfung am ganzen Bild für alle 4 Dächer: Dach und Pfosten sehen sauber aus, nichts schwebt, keine Überschneidung mit der Traufe.
6. Ein Haus ohne Häkchen baut dieselben Objekte wie vorher.
7. Terrasse über Wand hinaus und L-förmige Terrasse funktionieren.

## Tests and verification commands

Neue Tests zuerst:
- Feld übersteht Speichern, bei Terrasse und Balkon; bei anderen Typen wird es verworfen
- Plan reicht das Feld auf beiden Wegen weiter
- Geometrie: Pfostenzahl, Pfostenabstand, keine Pfosten an Fassadenkanten, Unterkante über dem Sturz, L-Form, frei stehende Fläche

```
python scripts/ueberdachung.test.py
python -m pytest tests/test_element_felder_ueberleben_speichern.py tests/test_exterior_floor_level.py
```

Sichtprüfung: Testbau an der Kopie eines echten Hausplans im Scratchpad, alle 4 Dächer, Terrasse und Balkon. Keine echte Hausdatei wird dafür geändert. Danach am echten Editor Häkchen setzen und mit Rainer an einem von ihm gewählten Haus bauen.

Bestehende Tests werden nicht geändert.

## Protected and risky paths

- Balkon im obersten Geschoss: Die Überdachung kann mit Traufe oder Dachüberstand kollidieren, vor allem bei Satteldach, Walmdach und Kniestock. Tritt das im Testbau auf, stoppe ich und zeige es Rainer, statt das Maß zu raten.
- Die neue Geometrie kann die Schauseite teilweise verdecken. Die Kamera bleibt unverändert.
- Häuser, die schon bei Codex sind, bleiben unberührt, bis Rainer sie neu baut.

## Rights, provenance, privacy, and security impact

Keine Änderung an Rechten, Freigaben oder Quelldaten. Das Feld gehört zu den Annotationen und ändert keine Wand- oder Raumgeometrie.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

Answer: no. Die Änderung ergänzt nur Bauteile am Außenmodell eines bestehenden Hauses und nur, wenn Rainer das Häkchen setzt. Es gibt keinen neuen Weg zu Veröffentlichung oder E-Mail, Upload und `--send` bleiben unberührt. Beleg: Akzeptanz 6 und die unveränderten Upload-Dateien.

## Customer, email, database, deployment, and external effects

Keine.

## Failed-hypothesis log

Noch keine.

## Rollback

`.before-ueberdachung`-Sicherungen der geänderten Dateien zurückkopieren, die zwei neuen Dateien entfernen. Ein vorhandenes Feld `ueberdacht` in Annotationen stört danach nicht, es wird beim Speichern verworfen.

## Unresolved questions

Keine, die den Start blockieren. Nach dem Bau trage ich die Variante als Regel in `REGELN.md` ein.

## Approval record

Variante 1 gewählt am 2026-10-31. Umsetzung freigegeben am 2026-10-31 (Rainer: "bauen").

## Umsetzung und Abweichungen

- Testbau an einer Kopie von `twostorey_xvv2_2`, Terrasse und Balkon, alle 4 Dächer.
- Gefunden: Bei Satteldach und Walmdach lag die Traufe bei 5,28 m, die Balkonplatte reichte bis 5,37 m. Abweichung vom Plan: `ueberdachung.unter_traufe` legt die Platte unter die im Bau gemessene Traufe, nie unter den Fenstersturz. Passt beides nicht, schreibt der Bau eine Warnung ins Log. Danach keine Überschneidung mit dem Hauptdach bei allen 4 Dächern.
- Beim Flachdach berührt die Terrassenplatte `roof-deck` des Erdgeschoss-Vorsprungs. Beide liegen fast auf gleicher Höhe, im Bild sauber, deshalb belassen.
- Tür- und Fenstermessung: Der nächste Pfosten steht 2,06 m oder weiter von bodentiefen Fenstern und Türen entfernt.
- Ohne Häkchen: 125 Objekte wie vorher, kein Objekt verschoben. Nur der Name eines importierten Modells (`cgaxis_models_79_76_02_1/2`) unterscheidet sich.
- Naht geprüft: echtes `normalize_*` plus echtes Bauskript tragen das Feld bis in den Plan. Häkchen im Annotator bei Terrasse und Balkon im Browser gesehen, nichts gespeichert.
- Noch nicht geprüft: Bau über den Knopf an einem echten Haus und das Codex-Bild mit Überdachung.

## Revision 2026-10-31: keine Platte mehr

Rainer: "it cant look like playwood it has to be the floor above it extended or the roof above it extended", "anything else looks like shit". Variante 1 ist damit aufgehoben, die Abschnitte oben zu Platte, Anthrazit, Überstand und Traufe gelten nicht mehr.

- Oberstes Geschoss: Die Fläche gehört zum Dachgrundriss, das Hauptdach läuft mit gleicher Neigung und Traufe weiter.
- Flachdach: Decke und Attika laufen in gleicher Höhe weiter.
- Unter einem Geschoss: Dessen Decke läuft weiter, 350 mm dick, in Fassadenfarbe.
- Stützen 240 x 240 mm in Fassadenfarbe, sie reichen bis an die Unterseite von Dach oder Decke.
- Noch nicht unterstützt: Balkon im obersten Geschoss eines 1,5-Geschossers mit Sattel- oder Walmdach. Der Bau schreibt eine Warnung, es entsteht dort kein Dach.
- Geprüft an einer Kopie von `twostorey_xvv2_2`, alle 4 Dächer im ganzen Bild. Ohne Häkchen 125 Objekte wie vorher, keines verändert; nur die Namen zweier importierter Modelle wechseln von Lauf zu Lauf.
- Vorhandener Fehler, nicht geändert: `render-exterior.py` prüft die Brüstung gegen die Wände aller Geschosse. Ein Balkon auf einem Erdgeschoss-Vorsprung bekommt deshalb keine Brüstung (Log: "0 Bruestungsfeld").

Nachtrag 2026-10-31, Rainer: "too manyposts": Stützen nur an den äußeren Ecken, Zwischenstütze erst ab 8 m Spannweite. Kleine Versätze in der Zeichnung zählen nicht als Ecke. Testhaus: Terrasse 3, Balkon 2.

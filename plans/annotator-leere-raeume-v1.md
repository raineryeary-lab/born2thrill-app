# Kein Raum entsteht aus einem Klick

Status: APPROVED (Rainer, 2026-08-28)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-08-28: "that happens when i open the screen and want to select
something to edit it and instead it tries to draw a room -- the default is
draw area instead of select. but with a save those less than 1 qm rooms can
be deleted."

Gemessen in `onehalfstorey_020`: zwei Raeume "Abstellraum" mit 0,00 m2, am
16.08. um 17:03 entstanden -- einer 141 x 0 mm, einer ein Punkt. Der Renderer
baut fuer jeden Raum eine Bodenplatte, also stehen zwei entartete Platten im
Modell, und das Obergeschoss zaehlt sieben Raeume statt fuenf.

Dasselbe Muster wie die zwei 50 x 50 mm grossen `stuff`-Rechtecke in
`german_catalog_review_bungalow_3_2_3_b_100_1` (STUFF-LEERE-RECHTECKE-001).

## Exact scope

`floorplan-simplifier/static/annotate.js` und `static/annotate.html`:

1. Startwerkzeug ist **Auswaehlen**, nicht "Room area". Ein Klick zum
   Bearbeiten darf keinen Raum erzeugen.
2. Beim Speichern werden Raeume unter **1 m2** verworfen und im Statusband
   benannt. Ohne bekannten Massstab wird nur Entartetes verworfen (normierte
   Flaeche < 1e-6, also Punkt oder Linie) -- sonst raeumte ein noch nicht
   vermessenes Projekt seine echten Raeume ab.

Flaeche = `polygonArea(normierte Punkte) * floor_scale^2`. Gegengerechnet an
onehalfstorey_020: 47,49 / 12,14 / 4,54 m2 gegen 47,69 / 12,20 / 4,56 m2 aus
dem Bauplan.

## Files in scope

- `floorplan-simplifier/static/annotate.js`
- `floorplan-simplifier/static/annotate.html`

## Explicitly out of scope

- Symbole und Elemente (Tueren, Fenster, stuff) -- eigener Fall,
  STUFF-LEERE-RECHTECKE-001.
- Der Renderer, der Bauplan, bestehende Annotationen anderer Haeuser.
- Nachtraegliches Aufraeumen: die zwei Raeume in onehalfstorey_020 werden
  beim naechsten Speichern von selbst verworfen.

## API, schema, and data-contract effects

Keine. Es werden nur Eintraege NICHT gespeichert, die keine Flaeche haben.

## Acceptance criteria

- Nach dem Laden ist "Auswaehlen" aktiv; ein Klick auf die Zeichenflaeche
  erzeugt keinen Raum.
- Ein Raum unter 1 m2 verschwindet beim Speichern, und das Statusband sagt
  welcher.
- Ein Raum ueber 1 m2 bleibt.
- Ohne Massstab bleibt jeder nicht entartete Raum erhalten.

## Tests and verification commands

`node --test floorplan-simplifier/static/annotate-leere-raeume.test.mjs` (neu):
die reine Auswahlfunktion mit den echten Zahlen aus onehalfstorey_020.
Sichtprobe im Annotator: Werkzeug beim Laden, Speichern mit einem
Null-Flaechen-Raum.

Kein bestehender Test wird geloescht, uebersprungen, abgeschwaecht oder umgeschrieben.

## Protected and risky paths

Der Filter LOESCHT Zeichnung. Deshalb die Schwelle nur mit bekanntem
Massstab, sonst ausschliesslich Entartetes.

## Rights, provenance, privacy, and security impact

Keine.

## Floorplan-suite invariant

Kann ein geaenderter Pfad Geometrie erzeugen, veroeffentlichen oder mailen,
ohne zu einer freigegebenen korrigierten Korpusreferenz zu passen?

**Nein.** Die Aenderung entfernt flaechenlose Eintraege beim Speichern der
Annotation. Sie erzeugt keine Geometrie, veroeffentlicht nichts und beruehrt
weder Katalog noch Upload.

## Customer, email, database, deployment, and external effects

Keine.

## Failed-hypothesis log

(leer)

## Rollback

Die zwei Dateien aus der Scratchpad-Sicherung zurueckkopieren.

## Unresolved questions

Keine.

## Approval record

Rainer, 2026-08-28, mit der Beschreibung des Fehlers und dem Vorschlag
"with a save those less than 1 qm rooms can be deleted".

# Vorderseite messen statt deklarieren

Status: APPROVED (muendlich, 2026-09-03: "ok mach")

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Ein importiertes Moebelmodell soll selbst sagen, wo vorne ist, statt auf eine
handgepflegte Tabelle angewiesen zu sein. Konvention bleibt die bestehende:
0 Grad heisst Blick nach +Y.

## Current evidence and behavior

Die Konvention existiert, sie ist nur nicht durchgesetzt. Der Renderer haelt
`MODEL_FACING_DEG`, eine Tabelle pro Modell, jeder Eintrag von Hand am Bild
geprueft:

    "doppelbett": 0, "einzelbett": 270
    "wand_wc": 270          Spuelkasten zeigt nach -X
    "badewanne": 180        Armaturenseite zeigt nach -Y
    "essgruppe_stuhl": 180

Fuer die erzeugten .glb aus data/furniture-assets/full-catalog/ gibt es
keinen einzigen Eintrag. Sie laufen durch den else-Zweig
(normalise_to_bbox), in dem ueberhaupt keine Ausrichtung angewendet wird.

Gemessene Folge, 2026-09-03: wardrobe__modern.glb ersetzte den prozeduralen
Kleiderschrank durch eine merkmallose Platte. Die Datei ist 519 KB, das
Tuerdetail existiert -- es zeigte zur Wand. Deshalb steht die Kette derzeit
ueber GENERATED_TYPES_VERIFIED auf coat_rack begrenzt.

## Exact scope

Eine Funktion `derive_front_axis(obj)`, die die Vorderseite MISST:

1. Von den beiden waagerechten Achsen ist die kuerzere die Tiefenachse.
   Ein Schrank ist 1050 breit und 600 tief; Vorder- und Rueckseite liegen
   auf der kurzen Achse. Die beiden langen Seiten kommen gar nicht erst in
   die Auswahl -- sie sind bei einem Schrank genauso flach wie der Ruecken.
2. Fuer die beiden Kandidatenflaechen wird die Deckung gemessen: Anteil der
   Flaeche, die tatsaechlich in der aeussersten Ebene liegt, an der vollen
   Flaeche der Bounding Box in dieser Richtung. Ein glatter Ruecken deckt
   nahezu 1,0. Eine Front mit zurueckgesetzten Tuerfuellungen deckt weniger.
3. Die flachere Seite ist der Ruecken, die gegenueberliegende ist vorne.
4. Liegen beide Werte naeher als eine Schwelle beieinander, wird NICHT
   gedreht, sondern gemeldet. Raten ist ausdruecklich nicht erlaubt.

Angewendet nur im else-Zweig und nur auf Modelle mit
`model_source == "generated_catalog"`. Hub-Modelle behalten
MODEL_FACING_DEG unveraendert -- diese Eintraege sind am Bild verifiziert und
werden nicht durch eine Heuristik ersetzt.

## Files in scope

    scripts/render-furnished-dollhouse.py

## Explicitly out of scope

- MODEL_FACING_DEG, MODEL_ORIENT_BY_LABEL, MODEL_MIRROR_Y anfassen.
- Hub-Modelle.
- Position, Anzahl, Kamera, Architektur.
- Jede Datei in einem Lieferordner.

## Acceptance criteria

- Der Kleiderschrank zeigt seine Tuerfuge wieder, nachdem wardrobe in
  GENERATED_TYPES_VERIFIED zurueckgenommen wurde.
- Das Log nennt je Modell die gemessene Deckung beider Seiten und die
  gewaehlte Drehung.
- Ein mehrdeutiger Fall dreht nicht und sagt das.
- Pixelaenderungen bleiben auf die betroffenen Moebel begrenzt; keine
  Platzierung verschwindet, 38 bleiben 38.

## Tests and verification commands

Kein bestehender Test wird geloescht, uebersprungen oder abgeschwaecht.

    build-simplifier-render-plan.py ... <harness>/plan-modern-test.json
    render-furnished-dollhouse.py   ... <harness>/interior-test5.png
    Pixeldiff gegen interior-modern-baseline.png

## Protected and risky paths

Alle Ausgaben nach renders/harness/model-beats-build/. Lieferordner nur
lesend.

Risiko: die Heuristik dreht ein Modell falsch. Eingegrenzt dadurch, dass sie
nur erzeugte Katalogmodelle betrifft, dass mehrdeutige Faelle gar nicht
gedreht werden, und dass jede Entscheidung im Log steht.

## Rights, provenance, privacy, and security impact

Keine neuen Assets, keine Rechteaenderung.

## Floorplan-suite invariant

Kann ein geaenderter Pfad Geometrie erzeugen, veroeffentlichen oder mailen,
ohne zu einer freigegebenen korrigierten Korpus-Referenz zu passen?

Nein. Die Aenderung liegt allein im Renderer und wirkt erst, wenn ein Mensch
ihn mit einem Ausgabepfad aufruft. Kein Publish-, Mail- oder Datenbankpfad
beruehrt.

## Ergebnis (2026-09-03)

Die Messung funktioniert und hat beim ersten Lauf einen zweiten, aelteren
Fehler aufgedeckt.

Log:

    model swapped  kleiderschrank 3082x650x2384 misses symbol 1050x600x2100
                   by 2.7x -- wardrobe (modern, generated)
    front measured kleiderschrank +X 0.0 / -X 0.95 -- 90deg auf +Y
    front unclear  garderobe +Y 0.0 / -Y 0.0 -- nicht gedreht

-X deckt 0,95: der glatte Ruecken. +X deckt 0,0: dort sitzen die
zurueckgesetzten Tuerfuellungen. Also ist +X vorne, Drehung 90 Grad. Genau
die Regel, ohne Tabelle und ohne Auge.

Die Garderobe ist ein offenes Gestell und hat auf beiden Seiten 0,0 Deckung.
Der Zweifelsfall greift und dreht nicht, statt zu raten.

ZWEITER BEFUND, nicht geplant, aber notwendig:

Der Prototyp-Cache war auf asset_id allein geschluesselt
(`if asset_id not in prototypes`). Drei Kleiderschraenke teilen sich eine
asset_id, aber nicht ein Modell: der 3700-mm-Schrank behaelt das Hub-Modell,
die beiden 1050er werden getauscht. Der erste Treffer baute den Prototyp und
die beiden anderen benutzten ihn stillschweigend mit. Der Tausch wurde also
protokolliert, aenderte aber nichts -- das Hub-Modell wurde stattdessen um
das 2,7-fache gestaucht, was den merkmallosen Schieber ergab, den wir am
Vormittag fuer das erzeugte Modell gehalten haben. Der Cache ist jetzt auf
(asset_id, mesh_path) geschluesselt.

Das war ein stiller Fehler unabhaengig von dieser Aufgabe: jede asset_id mit
zwei verschiedenen Modellen war davon betroffen.

Endstand des Testrenders gegen interior-modern-baseline.png:

    21 885 von 3 000 000 Pixeln geaendert
    Fernseher              x 1420-1604, y 466-697
    Schraenke + Garderobe  x  613-1035, y 810-1109
    38 Platzierungen vorher wie nachher

Der Kleiderschrank zeigt wieder Tuerfuge, Griff und Deckplatte.

## Customer, email, database, deployment, and external effects

Keine.

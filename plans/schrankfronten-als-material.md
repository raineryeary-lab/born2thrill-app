# Schrankfronten als Material

Status: APPROVED (Rainer, 2026-09-03: "sure")

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Prozedurale Moebelkaesten sollen Felder, Fugen und einen Sockel zeigen, ohne
dass dafuer Geometrie gebaut wird.

## Current evidence and behavior

Nachgerechnet am Massstab des Dollhouse-Renders. Das Lowboard ist 3500 mm
breit und belegt im Bild 311 Pixel, also 11,3 mm je Pixel:

    Schrankfront    600 mm  =  53,3 px    sichtbar
    Kassettenrahmen  60 mm  =   5,3 px    sichtbar, als Muster
    Rueckversatz      5 mm  =   0,44 px   unsichtbar
    Fuge              4 mm  =   0,36 px   unsichtbar

Die Tiefe einer Kassette ist ein halbes Pixel. Geometrie kauft dort nichts;
sichtbar ist allein das Muster. Rainer hat das vor der Rechnung gesagt.

Heute bekommen alle prozeduralen Kaesten `furniture_material(type)`, eine
einzige flache Farbe ohne jede Gliederung. Betroffen in
german_catalog_review_bungalow_3_4_2_b_120: kuechenzeile (4 Segmente),
lowboard, stuff, hochschrank_herd, kuehlschrank, vorwandinstallation.

## Repository baselines

    Repo   born2thrill-local-workbench
    Branch agent/furnished-render-and-annotation-schema
    Base   5be1a4e18956b9fb2e158bee82aa159898356e89

## Exact scope

Eine Funktion `front_material(finish, felder, sockel_anteil, stil)` in
render-furnished-dollhouse.py, die ein Material mit Shader-Knoten baut:

- Texturkoordinate GENERATED, nicht Object. Die Kaesten entstehen als
  Einheitswuerfel mit `obj.dimensions`, ihre Objektkoordinaten sind daher
  -0,5..0,5 und NICHT in Metern -- eine Fuge alle 600 mm liesse sich darin
  nicht ausdruecken. Generated laeuft 0..1 ueber die Bounding Box; die Zahl
  der Felder wird beim Bauen aus der echten Laenge berechnet und in den
  Shader gebacken. Das entspricht auch der Wirklichkeit: eine Kuechenzeile hat
  gleich breite Felder je Zug, keine angeschnittenen.
- Senkrechte Fugen an den Feldgrenzen.
- Eine waagerechte Fuge auf Sockelhoehe.
- Bei `classic` zusaetzlich ein eingesetzter Rahmen je Feld -- das
  Kassettenmuster.
- Die Fugenfarbe ist die Grundfarbe deutlich abgedunkelt, kein Schwarz.

Angewendet in den prozeduralen Zweigen fuer die Typen counter, sideboard,
wardrobe, storage_shelving, oven_housing, fridge.

## Files in scope

    scripts/render-furnished-dollhouse.py

## Explicitly out of scope

- Geometrie. Es wird kein Feld, keine Fuge und kein Griff modelliert.
- Griffe. Erst wenn Felder und Sockel sitzen.
- Geladene Modelle. Die bringen ihre eigene Gliederung mit.
- vorwandinstallation: das ist eine geflieste Vorwand, kein Schrank.
- Position, Anzahl, Kamera, Architektur.

## Acceptance criteria

- Die Kuechenzeile zeigt in jedem der vier Segmente gleich breite Felder.
- Das Lowboard zeigt wieder Feldgrenzen, ohne dass ein Modell geladen wird.
- Ein Sockelstrich ist sichtbar.
- Pixelaenderungen bleiben auf die betroffenen Moebel begrenzt; 38
  Platzierungen bleiben 38, keine verschiebt sich.

## Tests and verification commands

Kein bestehender Test wird geloescht, uebersprungen oder abgeschwaecht.

    render-furnished-dollhouse.py -- <plan> <harness>/interior-fronten.png
    Pixeldiff gegen die Baseline, Regionen benennen

## Protected and risky paths

Ausgaben nur nach renders/harness/. Lieferordner nur lesend.

Risiko: ein zu feines Muster wird bei 11,3 mm je Pixel zu Rauschen. Deshalb
Feldbreite rund 600 mm (53 px) und Fugenbreite so, dass sie mindestens ein
Pixel trifft.

## Rights, provenance, privacy, and security impact

Keine. Kein Asset, keine Textur von aussen -- reine Shader-Knoten.

## Floorplan-suite invariant

Kann ein geaenderter Pfad Geometrie erzeugen, veroeffentlichen oder mailen,
ohne zu einer freigegebenen korrigierten Korpus-Referenz zu passen?

Nein. Es wird ausschliesslich ein Material erzeugt. Geometrie, Kamera und
Stueckzahlen bleiben unberuehrt, kein Publish- oder Mailpfad ist beteiligt.

## Customer, email, database, deployment, and external effects

Keine.

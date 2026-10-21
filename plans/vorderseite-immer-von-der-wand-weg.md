# Vorderseite immer von der Wand weg

Status: APPROVED (Rainer, 2026-09-03: "dann mach doch die preile bei allen
moebeln immer von der wand weg ausser esstisch und couchtisch")

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Ein an eine Wand gesetztes Moebel soll mit dem Ruecken zur Wand stehen, ohne
dass jemand es nachdrehen muss. Und der Pfeil, der die Vorderseite zeigt, soll
fuer alle Moebel gelten statt fuer neun.

## Current evidence and behavior

BEFUND 1 -- der Rechenfehler.

`snapStampToWalls` in src/app/floorplan-workbench/furniture.tsx bestimmt die
Wandnormale und dreht sie in den Raum:

    let nx = -Math.sin(angle);
    let ny =  Math.cos(angle);
    if ((point - projected) . n < 0) { nx = -nx; ny = -ny; }

Dieses korrigierte Vorzeichen geht in die POSITION ein. In die Drehung nicht:

    rotation_deg: (angle * 180 / PI) % 360

`angle` ist die Richtung der WAND. Zwei Raeume links und rechts derselben Wand
bekommen dieselbe Drehung, obwohl ihre Normalen entgegengesetzt sind. Die
Haelfte der Faelle steht damit falsch herum.

Das deckt sich mit der Messung, die in scripts/moebel-vorderseite.test.mjs
dokumentiert ist: von 62 platzierten Stuecken mit Vorderseite zeigten 36 in
den Raum und 26 in die Wand. Der Pfeil wurde damals eingebaut, um das
sichtbar zu machen; die Ursache wurde nicht gesucht.

BEFUND 2 -- die Pfeilliste.

`MIT_VORDERSEITE` zaehlt neun Symbole auf. Kleiderschrank, Garderobe und
Lowboard stehen genauso an der Wand, haben aber keinen Pfeil, obwohl ihre
Drehung genauso falsch sein kann.

## Repository baselines

    Repo   C:\dev\Floorplan-tools\born2thrill-local-workbench
    Branch agent/furnished-render-and-annotation-schema
    Base   5be1a4e18956b9fb2e158bee82aa159898356e89

Vorbestehende Worktree-Aenderungen bleiben unangetastet.

## Exact scope

1. `snapStampToWalls` gibt die Drehung aus der NORMALEN zurueck statt aus der
   Wandrichtung: `Math.atan2(-nx, ny)`. Bei nicht gespiegelter Normale ist das
   rechnerisch identisch mit dem alten `angle`; nur der gespiegelte Fall
   aendert sich, und genau der war falsch.
2. `MIT_VORDERSEITE` wird zu `OHNE_VORDERSEITE`. Der Pfeil gilt fuer alle
   Moebel; die Liste zaehlt die Ausnahmen: esstisch, couchtisch und die
   Essgruppen. Ein Tisch steht frei und wird von allen Seiten benutzt.
   Gezeichnete Zuege (kuechenzeile, stuff, vorwandinstallation) fallen von
   selbst heraus, weil sie points_mm statt Breite und Tiefe haben.

## Files in scope

    src/app/floorplan-workbench/furniture.tsx
    scripts/moebel-vorderseite.test.mjs

## Explicitly out of scope

- Bereits gespeicherte Moebeldateien. Die Korrektur wirkt beim naechsten
  Setzen oder Anschnappen, nicht rueckwirkend. Ein Korrekturlauf ueber die
  19 vorhandenen Dateien ist eine eigene Aufgabe -- siehe Roadmap.
- Der Renderer.
- Position, Anzahl, Kamera, Architektur.

## API, schema, and data-contract effects

Keine. `rotation_deg` behaelt Bedeutung und Wertebereich.

## Acceptance criteria

- Zwei Klicks auf dieselbe Wand, einer von jeder Seite, ergeben Drehungen, die
  sich um 180 Grad unterscheiden, und beide Vorderseiten zeigen vom Wandstueck
  weg.
- Fuer die vier Achsenrichtungen zeigt die gedrehte lokale +y-Richtung in den
  Raum.
- kleiderschrank, garderobe und lowboard bekommen einen Pfeil.
- esstisch und couchtisch bekommen keinen.

## Tests and verification commands

GEAENDERTER BESTEHENDER TEST, mit Begruendung, wie es die AGENTS.md verlangt:

`scripts/moebel-vorderseite.test.mjs`, Test "was von allen Seiten gleich
aussieht, bekommt keinen". Er behauptet heute, dass hocker, essgruppe_stuhl,
kochfeld, badewanne, dusche_gross und kuecheninsel keinen Pfeil bekommen. Das
war die Entscheidung vom 2026-08-28 und ist durch die Entscheidung vom
2026-09-03 ersetzt: der Pfeil gilt fuer alle ausser Tischen. Der Test wird
nicht geloescht und nicht abgeschwaecht, sondern auf die neue Regel gezogen
und behaelt seine Faelle -- couchtisch bleibt darin, die anderen wechseln die
Seite. Zusaetzlich kommt der bisher voellig ungetestete Teil dazu: die
Drehung aus der Normalen.

    node --test scripts/moebel-vorderseite.test.mjs

## Protected and risky paths

Nur der Editor. Kein Renderpfad, kein Lieferordner.

Risiko: bereits gespeicherte Moebel behalten ihre alte, teils falsche Drehung.
Der Pfeil zeigt sie jetzt fuer alle Stuecke an, also werden sie sichtbar.

## Rights, provenance, privacy, and security impact

Keine.

## Floorplan-suite invariant

Kann ein geaenderter Pfad Geometrie erzeugen, veroeffentlichen oder mailen,
ohne zu einer freigegebenen korrigierten Korpus-Referenz zu passen?

Nein. Die Aenderung betrifft die Ausrichtung eines Moebels im Editor. Waende,
Oeffnungen und Raumgeometrie werden nicht beruehrt, kein Publish- oder
Mailpfad ist im Spiel.

## Customer, email, database, deployment, and external effects

Keine.

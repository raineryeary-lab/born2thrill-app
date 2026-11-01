# Tuerblaetter auf die Objektkarte

Status: IMPLEMENTED (Rainer, 2026-08-27 -- Weg B, "die Karte einmal an einem Haus
beweisen"; zwei Runden Nachbesserung haben denselben Fehler nicht behoben)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Die Objektkarte markiert Garderobe, Stuff, Sanitaer und Kueche -- aber nicht
die Tuerblaetter. Genau die werden mit der Garderobe verwechselt.

## Current evidence and behavior

`interior-modern-baseline.blend` von
`german_catalog_review_bungalow_3_2_3_b_100_1` enthaelt vier Tuerblaetter:
`wall-1-door`, `wall-3-door`, `wall-6-door`, `wall-12-door`. `wall-12-door`
misst 898 x 898 x 2010 mm (aufgeschlagen) und projiziert auf Pixel 479, 699 --
190 px neben Marker 3 (`garderobe-25`, Pixel 488, 635).

Zwei Nachbesserungsrunden am 2026-08-27 (17:03 und 17:59) haben in
`05-floorplan-soft-scandinavian.png` und `06-floorplan-classic.png` dasselbe
Ergebnis geliefert: Garderobe auf Marker 3, Tuerblatt weg. Der Bilddiff im
Eingangsbereich zeigt 32 % bzw. 13 % geaenderte Pixel -- Codex hat gearbeitet,
nur ohne zu wissen, wo das Tuerblatt sitzt.

## Exact scope

`scripts/make-codex-job.py`:
- Neuer Helfer `_stamm(name)`: Objekte auf `-door` zaehlen als Rolle "tuer",
  alles andere wie bisher nach dem ersten Namenssegment.
- `NENNENSWERT` bekommt "tuer" -> "Tuer (bleibt, nicht ersetzen)".
- `_bauteil()` fasst Tuerblaetter NICHT zusammen: `wall-12-door` wuerde sonst
  ueber das erste numerische Segment zu `wall-12` und damit zur Wand.
- `objektkarte()` faerbt nach Rolle: rot = ersetzen, blau = bleibt. Die Karte
  soll auf einen Blick sagen, was angefasst werden darf.
- Der Markdown-Abschnitt erklaert die zwei Farben.

`docs/CODEX-REGELN-4PLUS2.md`: §1.2 nennt die Tuermarker.

## Files in scope

- `scripts/make-codex-job.py`
- `scripts/make-codex-job.test.py`
- `docs/CODEX-REGELN-4PLUS2.md`

## Explicitly out of scope

Renderer, Bauplan, Upload, WordPress, Rechte-Gate, Hausseite.

## API, schema, and data-contract effects

`object_map.markers` bekommt das Feld `farbe`. Additiv.

## Acceptance criteria

- Die vier Tuerblaetter tragen je einen eigenen blauen Marker.
- Kein Tuerblatt wird mit seiner Wand zusammengefasst.
- Garderobe und Stuff bleiben rot.

## Tests and verification commands

`python scripts/make-codex-job.test.py` -- neue Faelle:
- `_stamm("wall-12-door")` ist "tuer", `_stamm("garderobe-25")` ist "garderobe".
- `_bauteil("wall-12-door")` bleibt der volle Name, wird nicht zu `wall-12`.
- Ein Tuerblatt und seine Wand ergeben zwei getrennte Marker.
- Rollen mit "(ersetzen)" bekommen rot, alle anderen blau.

Kein bestehender Test wird geloescht, uebersprungen, abgeschwaecht oder umgeschrieben.

## Protected and risky paths

Wie v1: der Generator schreibt nur in den go-baseline-Ordner.

## Rights, provenance, privacy, and security impact

Keine.

## Floorplan-suite invariant

Kann ein geaenderter Pfad Geometrie erzeugen, veroeffentlichen oder mailen,
ohne zu einer freigegebenen korrigierten Korpusreferenz zu passen?

**Nein.** Es aendert sich nur, welche Objekte auf einer Auftragsgrafik einen
Marker bekommen. Kein Aufruf von `publish-renders.py` oder `approve-plan.py`,
keine Geometrie, kein Katalogeintrag.

## Customer, email, database, deployment, and external effects

Keine.

## Failed-hypothesis log

(keine)

## Verification

- `python scripts/make-codex-job.test.py` -- 14 -> 18 Tests, OK.
- Uebrige Python-Tests gruen: comfyui-polish-exterior-rule, go (4),
  hausdaten (37), rechte, render-furnished-dollhouse, verify_render.
- Vorbestehend rot und nicht angefasst: `build-simplifier-render-plan.test.py`
  `test_door_hinge_and_swing_are_normalized_into_the_walls_frame`
  (KUECHENINSEL-DOORTEST-001).
- Am echten Haus erzeugt: 18 Marker statt 14. Neu blau: `wall-1-door` (798,448),
  `wall-12-door` (479,699), `wall-3-door` (904,763), `wall-6-door` (576,503).
  Marker 14 liegt sichtbar neben Marker 3 (`garderobe-25`, 488,635) -- genau
  die Verwechslung, die zwei Lieferrunden gekostet hat.
- Regelwerk-Hash `ad50a9e09c2f78bd`.

## Rollback

`_stamm`, den NENNENSWERT-Eintrag "tuer", die Farbgebung und die neuen Tests
zuruecknehmen, Auftrag neu erzeugen.

## Unresolved questions

Keine.

## Approval record

Rainer waehlte Weg B ("die Karte an diesem Haus beweisen, bevor sie auf die
anderen geht"). Zwei Runden haben denselben Fehler nicht behoben; die Ursache
ist nachgewiesen ein fehlender Marker.

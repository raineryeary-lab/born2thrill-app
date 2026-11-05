# TREPPE-MEHR-STEIGUNGEN-001: Zu lange Lauflinie: Geschosshöhe auf alle gebauten Steigungen verteilen

Status: DONE 2026-10-30 (Rainer: "yes"; 31 Tests OK, go onehalfstorey_xvv1 fertig, R9 PASS)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

`go` bricht bei `onehalfstorey_xvv1` ab:

    Verifier R9_stair_access: top tread stair-step-16 finishes at 2795mm but this storey's floor is at 2620mm

Rainer, 2026-10-30, hat Option 1 gewählt: Der Bauer ändert sich, die Zeichnung bleibt. Die Treppe füllt weiter die gezeichnete Linie und endet genau auf dem Boden.

## Current evidence and behavior

- Plan: `riseMm` 174,67, `risers` 15, Podest, Lauflinie 6861,8 mm, Breite 900 mm.
- `render-furnished-dollhouse.py:4164-4165`: 15 Steigungen, Höhe je 174,67 mm.
- `laufplan_stufen`, Zeile 1265-1266: Fluglauf 5061,8 mm / 13 Stufen = 389 mm, also über `max_going` 350. Die Stufenzahl wird auf `round(5061,8 / 350)` = 14 erhöht.
- Ergebnis 14 Stufen + 2 Podeste = 16 Elemente. Nachgerechnet mit der echten Funktion: 16.
- Zeile 4507 `top = z_base + n * rise` nutzt weiter die alte Höhe: 16 x 174,67 = 2795 mm.
- `bau.log`: "16 Steigungen x 175mm, 362mm Auftritt, podest (2 Podeste)".
- Der Kommentar in `laufplan_stufen` beschreibt nur den Fall "zu wenig Platz". Der Fall "zu viel Platz" wird vom Aufrufer nicht behandelt.

## Repository baselines

- Repo `born2thrill-local-workbench`, Branch `agent/furnished-render-and-annotation-schema`, HEAD 5be1a4e.
- Vorher schon offen: `render-furnished-dollhouse.py` geändert (M), `render-furnished-dollhouse.test.py` ungetrackt. Beide bleiben erhalten, Sicherungen `.before-mehr-steigungen`.

## Exact scope

1. Neue Hilfsfunktion in `render-furnished-dollhouse.py`:
   `steigung_fuer_laufplan(geschoss_m, risers, elemente)` gibt `(risers, rise)` zurück.
   - `elemente > risers`: `(elemente, geschoss_m / elemente)`
   - sonst unverändert `(risers, geschoss_m / risers)`
2. Aufruf direkt nach `steps = len(laufplan)`, vor der Treppennotiz, vor `z_base` (Zeile 4418) und vor der Stufenschleife.
3. `laufplan_stufen` bleibt unverändert.
4. Der Fall "zu wenig Platz" bleibt unverändert: Dort ist `elemente < risers`, die Regel R9 meldet ihn weiter.

Für xvv1 ergibt das 16 Steigungen x 163,75 mm, 362 mm Auftritt, Austritt bei 2620 mm.

## Files in scope

- `scripts/render-furnished-dollhouse.py`
- `scripts/render-furnished-dollhouse.test.py` (nur neue Tests)
- `born2thrill-app-repo/plans/ROADMAP.md`

## Explicitly out of scope

- Annotation und Treppe von `onehalfstorey_xvv1`.
- `verify_render_blend.py`: Die Regel R9 bleibt unverändert streng.
- `build-simplifier-render-plan.py`: Der Plan schreibt weiter 15 Steigungen (Roadmap: Annotator und Plan zeigen dann eine andere Zahl als der Bau).
- 1_5_1 (Treppe zu kurz): anderer Fall, eigene offene Entscheidung.

## API, schema, and data-contract effects

Keine Änderung an Plan- oder Annotationsformat.

## Behaviour change to accept

- Der Skript-Fingerabdruck in `run_project.py:535` ändert sich. Alle Häuser gelten danach als "Renderer geändert", wie bei jeder Renderer-Änderung.
- Die Geometrie anderer Häuser ändert sich nur, wenn dort `elemente > risers` ist. So ein Haus liegt eine Steigung über dem Boden, und R9 lehnt es ab. Ein Haus, das R9 heute besteht, sieht also gleich aus.
- Die Steigung wird kleiner als geplant (hier 164 statt 175 mm). Ein Haus mit extrem langer Linie bekäme sehr flache Stufen. Unter 150 mm wird nicht gebaut: `SystemExit` mit klarer Meldung, Linie von Hand kürzen.

## Acceptance criteria

- `steigung_fuer_laufplan(2.62, 15, 16)` ergibt 16 und 0,16375 m. 16 x Höhe = 2,62.
- Bei `elemente` <= `risers` bleibt das Ergebnis wie heute.
- Unter 150 mm Steigung: Abbruch mit Meldung.
- `go` auf `onehalfstorey_xvv1`: R9 PASS, Austritt bei 2620 mm, `bau.log` zeigt "16 Steigungen x 164mm".

## Tests and verification commands

Neu in `scripts/render-furnished-dollhouse.test.py`:
- `test_xvv1_sechzehn_Steigungen_enden_auf_dem_Boden`
- `test_passender_Laufplan_bleibt_wie_er_war`
- `test_zu_kurze_Linie_aendert_die_Steigung_nicht`
- `test_zu_flache_Steigung_bricht_ab`

Keine bestehenden Tests werden geändert, übersprungen oder gelöscht.

```bash
python scripts/render-furnished-dollhouse.test.py
```

Danach ein echter Bau von `onehalfstorey_xvv1` mit der R9-Prüfung.

## Protected and risky paths

`render-furnished-dollhouse.py` ist der zentrale Bauer. Die Änderung ist drei Zeilen plus Hilfsfunktion.

## Rights, provenance, privacy, and security impact

Keine.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference? **No.** Nur die Stufenhöhe innerhalb der gezeichneten Treppe ändert sich. Lauflinie, Wände und Treppenloch bleiben, und `verify_render_blend.py` prüft weiter. Kein Upload, keine E-Mail.

## Customer, email, database, deployment, and external effects

Keine.

## Failed-hypothesis log

Keine.

## Rollback

Die zwei `.before-mehr-steigungen`-Sicherungen zurückspielen.

## Unresolved questions

- Grenze 150 mm ist meine Vorgabe.
- `pipeline.lock` von xvv1 (pid 36972) vor dem Bau prüfen: Der Bau meldet ihn sonst vielleicht als belegt.

## Approval record

Approved 2026-10-30.

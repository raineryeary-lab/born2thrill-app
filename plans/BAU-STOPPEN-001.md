# Bau stoppen

Status: DONE

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-01: "can we add a stop build button on the build tab, in case i made a mistake and want to change it?"

## Current evidence and behavior

- `pipeline/route.ts` startet `go.py` und merkt sich den Prozess nur innerhalb von `lauf`, von außen kommt niemand daran.
- `beenden()` kann den Prozessbaum schon beenden (taskkill /T /F), genutzt nur beim Zeitlimit.
- Die Sperren überstehen einen Abbruch: `pipeline.lock` ist eine Betriebssystem-Sperre, `build.lock` wird bei totem Prozess übernommen (`run_project.py`).

## Exact scope

- `lauf` und `beenden` ziehen nach `src/lib/floorplan-workbench/pipeline-lauf.mjs`, dazu ein Verzeichnis laufender Baus je Haus.
- Route: Schritt `stoppen`, `GET ?plan=` sagt, ob ein Bau läuft.
- `/haus`, Schritt Bauen: Knopf "Bau stoppen" mit Rückfrage, auch nach F5 sichtbar.

## Explicitly out of scope

Hochladen und Freigeben lassen sich nicht stoppen. Aufräumen halbfertiger Dateien: Der nächste Bau ersetzt sie.

## Tests

`src/lib/floorplan-workbench/pipeline-lauf.test.mjs`: echter Prozessbaum wird beendet, Code 130, Zeitlimit unverändert, Stoppen ohne Lauf ist kein Fehler. Knopf im echten Editor.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

Answer: no. Der Knopf beendet nur einen laufenden Bau.

## Rollback

`pipeline/route.ts.before-bau-stoppen` und `haus/page.tsx.before-bau-stoppen` zurückkopieren, `pipeline-lauf.mjs` und seinen Test entfernen.

## Approval record

Rainers Anweisung vom 2026-11-01 im Chat.

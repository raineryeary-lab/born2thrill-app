# go.py baut kein fertiges Haus neu

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-07: "look if a house is finished doesnt do it again" --
"Fertig ist Fertig".

Ich habe an diesem Tag `go.py german_catalog_review_bungalow_4_1_3_wb_105`
laufen lassen. Das Haus stand im Ledger als **fertig v1.2, seit 07:18**.
`go.py` hat es ohne Nachfrage neu gebaut.

## Current evidence and behavior

- `E:\born2thrill-local-workbench-data\fertig-ledger.json` fuehrt 33 Haeuser
  mit Version, Erst- und Letztdatum und Build-Hash.
- `scripts/go.py` erwaehnt das Ledger an keiner Stelle (`grep fertig-ledger`
  findet nichts). `haus_vorantreiben()` laeuft Massstab -> Dachform -> Bauen
  -> Pruefen -> Zertifikat, ohne vorher zu fragen, ob es etwas zu tun gibt.
- Das Ledger wird heute NUR von der Statusroute geschrieben
  (`src/app/api/floorplan-workbench/state/route.ts`), nie von `go.py` gelesen.
  Die Regel FERTIG-BLEIBT-FERTIG-001 existiert also in der Oberflaeche und
  fehlt im Werkzeug, das tatsaechlich baut.
- Folge: ein `--alle`-Lauf baut alle 33 fertigen Haeuser neu, verschiebt ihre
  zertifizierte Lieferung nach `superseded-<datum>` und setzt beim naechsten
  Statusabruf die Version hoch -- fuer nichts.

## Exact scope

1. `go.py` liest vor dem Bauen `fertig-ledger.json` aus
   `FLOORPLAN_WORKBENCH_DATA_DIR`.
2. Steht das Haus drin, wird NICHT gebaut. Der Satz am Ende lautet
   `fertig v<version> seit <datum> -- nicht neu gebaut (--trotzdem erzwingt es)`.
3. Neue Fahne `--trotzdem`: baut ein fertiges Haus auf ausdrueckliche Ansage
   doch. Ohne sie passiert nichts. Rainer, 2026-10-07: "if i want to redo it
   i can redo it" -- die Entscheidung bleibt bei ihm, das Werkzeug trifft sie nie.
4. `--alle` ueberspringt fertige Haeuser still und nennt am Ende ihre Zahl.
   `--alle --trotzdem` gibt es NICHT: 33 fertige Haeuser auf einen Schlag neu
   zu bauen ist keine Entscheidung, die eine Fahne tragen sollte.
5. Wird doch gebaut, geht das Haus VORWAERTS: Rainer, 2026-10-07: "if we
   correct it is to go forward". Es bleibt fertig und bekommt die naechste
   Version. Das leistet `naechsteFertigVersion()` in `house-state.mjs` schon
   -- neuer Build-Hash heisst Minor+1 (1.2 -> 1.3). Hier ist nichts zu bauen,
   nur nicht kaputtzumachen: `go.py` darf das Ledger nicht anruehren.

## Files in scope

- `born2thrill-local-workbench/scripts/go.py`
- `born2thrill-local-workbench/scripts/go.test.py` (neu oder Ergaenzung)

## Explicitly out of scope

- `state/route.ts` und wer das Ledger schreibt -- nur gelesen wird hier
- Die Zustandsmaschine `house-state.mjs`
- `run_project.py`, `render-exterior.py`, jede Dachform
- Die Knoepfe in der Hausakte (eigener Plan,
  `liefer-knoepfe-aus-wenn-nichts-zu-tun.md`)

## API, schema, and data-contract effects

Keine. `fertig-ledger.json` wird nur gelesen, nie geschrieben.

## Acceptance criteria

1. `go.py <fertiges haus>` baut nicht und sagt Version und Datum.
2. `go.py <fertiges haus> --trotzdem` baut.
3. `go.py <offenes haus>` verhaelt sich wie bisher.
4. `go.py --alle` ueberspringt die 33 und nennt die Zahl.
5. Fehlt das Ledger oder ist es unlesbar, baut `go.py` wie bisher -- ein
   kaputtes Ledger darf nicht die ganze Arbeit blockieren.

## Tests and verification commands

Neu:
- `test_fertiges_haus_wird_nicht_gebaut`
- `test_trotzdem_baut_doch`
- `test_offenes_haus_unveraendert`
- `test_fehlendes_ledger_blockiert_nicht`

Kein bestehender Test wird geloescht, uebersprungen, abgeschwaecht oder umgeschrieben.

## Protected and risky paths

`go.py` ist der Knopf "Bauen" in der Hausakte. Eine zu scharfe Sperre wuerde
Arbeit verhindern statt schuetzen -- deshalb Kriterium 5 und `--trotzdem`.

## Rights, provenance, privacy, and security impact

Keiner. Die Aenderung baut weniger, nie mehr.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an
approved corrected corpus reference?

Nein. Die Aenderung erzeugt nichts Neues, sie verhindert einen Bau.

## Customer, email, database, deployment, and external effects

Keine.

## Repository baselines

- `born2thrill-local-workbench`, Branch `agent/furnished-render-and-annotation-schema`, Base SHA `5be1a4e`
- `scripts/go.py` ist in diesem Arbeitsbaum UNTRACKED -- Rollback ueber eine
  Sicherung `go.py.before-fertig-ist-fertig`, nicht ueber git.

## Rollback

`cp scripts/go.py.before-fertig-ist-fertig scripts/go.py`

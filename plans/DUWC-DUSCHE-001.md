# DUWC-DUSCHE-001: DU-WC bekommt eine Dusche

Status: DONE

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-30: "when there is a DuWC why is hter no shower added". Ein DU-WC wird beim Einrichten wie ein Duschbad behandelt.

## Current evidence and behavior

- Der Annotator vergibt den Namen "DU-WC" (`floorplan-simplifier/static/annotate.js:195`); er steht 77-mal in den Annotationen.
- `raumtypAusName` (`src/lib/generator/moebel-vorschlag.mjs:48-52`) kennt nur `dusch|du/bad|du-bad`. Gemessen: "DU-WC", "Du/WC", "Du WC" ergeben `wc`, "DuWC" ergibt `null`.
- Das Rezept `wc` (Zeile 402) setzt nur Wand-WC und Handwaschbecken. `duschbad` (Zeile 397) setzt Dusche, Waschtisch und WC.

## Repository baselines

`born2thrill-local-workbench`, Branch `agent/furnished-render-and-annotation-schema`, HEAD 5be1a4e. `moebel-vorschlag.mjs` vor dem Ändern prüfen, Sicherung `.before-kueche-zeile`.

## Exact scope

`raumtypAusName` erkennt `du-wc`, `du/wc`, `du wc` und `duwc` als `duschbad`. "WC" und "Gäste-WC" bleiben `wc`.

## Files in scope

- `src/lib/generator/moebel-vorschlag.mjs`
- `scripts/moebel-vorschlag.test.mjs` (neuer Test, bestehende bleiben)
- `born2thrill-app-repo/plans/ROADMAP.md`

## Explicitly out of scope

Gespeicherte Möbel bestehender Häuser, Raumnamen, Rezepte, Annotator.

## API, schema, and data-contract effects

Keine.

## Acceptance criteria

- Alle vier Schreibweisen ergeben `duschbad`, und ein passender Raum bekommt Dusche, Waschtisch und WC.
- "WC", "Gäste-WC", "Bad" und "Du/Bad" ergeben dasselbe wie vorher.
- Passt die Dusche nicht, wird sie wie bisher als fehlend gemeldet.

## Tests and verification commands

```bash
node --test scripts/moebel-vorschlag.test.mjs
```

## Protected and risky paths

Keine. Der Vorschlag wirkt nur, wenn Rainer einrichten klickt.

## Rights, provenance, privacy, and security impact

Keine.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference? **No.** Die Änderung betrifft nur die Zuordnung Raumname zu Einrichtungsrezept im Editor.

## Customer, email, database, deployment, and external effects

Keine.

## Failed-hypothesis log

Keine.

## Rollback

`.before-kueche-zeile`-Sicherungen zurückspielen (gemeinsam mit dem Küchenplan gebaut).

## Unresolved questions

Keine.

## Approval record

Rainer, 2026-10-30: "komm schon bauen nicht dann gleich wieder vergessen".
